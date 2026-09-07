import re
from typing import Dict, Any, Optional

from app.turitop_service import turitop
from app.templates_service import template_mgr
from app.gemini_service import gemini
from app.config import COMPANY_NAME


def _fuzzy_match_tour(text_lower, available_tours):
    best_match = None
    best_score = 0
    for tour in available_tours:
        t_name = tour["name"].lower()
        words = [w for w in re.split(r'\W+', t_name) if len(w) > 3]
        score = sum(1 for w in words if w in text_lower)
        if score > best_score:
            best_score = score
            best_match = tour
    return best_match if best_score >= 1 else None


class AssistantParser:
    """
    Interprets natural language instructions from the operator.
    Connects to Gemini AI to understand the intent and parameters,
    matches against live TuriTop CRM data, groups bookings by pickup stop,
    and prepares multilingual WhatsApp messages with audioguides.
    """

    def parse_instruction(self, text: str, target_date: Optional[str] = None) -> Dict[str, Any]:
        text_lower = text.lower().strip()
        available_tours = turitop.get_tours()
        intent = None
        matched_tour = None
        target_provider = None
        target_pickup = None
        new_time = None
        reason = "motivos logisticos"
        target_slots = []
        used_engine = "Reglas Locales"

        # 1. Ask Gemini AI first
        if gemini.is_configured():
            g = gemini.parse_with_gemini(text, available_tours)
            if g:
                used_engine = "Google Gemini AI"
                intent = g.get("intent")
                tid = g.get("tour_id")
                if tid:
                    matched_tour = next((t for t in available_tours if t["id"] == tid or t.get("short_id") == tid), None)
                target_provider = g.get("target_provider")
                target_pickup = g.get("target_pickup")
                new_time = g.get("new_time")
                reason = g.get("reason") or reason
                target_slots = g.get("target_slots") or []

        # Fallback pickup detection if not parsed by Gemini
        if not target_pickup or target_pickup == "null":
            if any(k in text_lower for k in ["museo", "darsena", "dársena", "la salle", "salle"]):
                target_pickup = "museo"
            elif any(k in text_lower for k in ["peregrino", "exe"]):
                target_pickup = "peregrino"
            elif any(k in text_lower for k in ["pilar", "capilla"]):
                target_pickup = "pilar"
            else:
                target_pickup = None

        # Fallback provider detection if not parsed by Gemini
        if not target_provider or target_provider == "null":
            if "civitatis" in text_lower:
                target_provider = "civitatis"
            elif "getyourguide" in text_lower or "gyg" in text_lower:
                target_provider = "getyourguide"
            elif "viator" in text_lower or "tripadvisor" in text_lower:
                target_provider = "viator"
            elif "guruwalk" in text_lower:
                target_provider = "guruwalk"
            elif "freetour" in text_lower:
                target_provider = "freetour"
            elif "directo" in text_lower or "web" in text_lower:
                target_provider = "direct"
            else:
                target_provider = None

        # 2. Local fallback intent detection
        if not intent:
            review_kw = ["reseña", "reseñas", "opinion", "opiniones", "valoracion", "valoraciones", "review", "reviews", "google", "recordatorio de opinion"]
            sched_kw = ["avisa", "cambia", "unifica", "informa", "notifica", "retraso", "adelanta", "salida a las", "punto de encuentro", "enviar"]
            info_kw = ["clientes", "pasajeros", "salidas", "cuantos", "quien viene", "reservas", "listado de", "localiza", "busca", "proveedor"]
            overview_kw = ["que tours", "todos los tours", "tours de hoy", "resumen general"]

            if any(kw in text_lower for kw in review_kw):
                intent = "review_campaign"
            elif any(kw in text_lower for kw in overview_kw) and not any(kw in text_lower for kw in sched_kw):
                intent = "overview_all"
            elif any(kw in text_lower for kw in sched_kw):
                intent = "schedule_change"
            elif any(kw in text_lower for kw in info_kw):
                intent = "info_query"
            else:
                intent = "schedule_change"

        # 3. Match tour if not matched yet
        if not matched_tour and intent != "overview_all":
            matched_tour = _fuzzy_match_tour(text_lower, available_tours)

        # 4. Extract time if mentioned
        if not new_time:
            m = re.search(r'\b([0-2]?\d)[:.h]([0-5]\d)\b', text_lower)
            if m:
                h, mn = m.groups()
                new_time = f"{int(h):02d}:{mn}"

        # 5. Extract reason if mentioned
        if "trafico" in text_lower:
            reason = "motivos de trafico"
        elif "lluvia" in text_lower or "meteorol" in text_lower:
            reason = "condiciones meteorologicas"
        elif "logistic" in text_lower:
            reason = "motivos logisticos"

        # Intent: REVIEW CAMPAIGN (Ask clients for reviews on Google / Civitatis / GYG)
        if intent == "review_campaign":
            from datetime import date, timedelta
            from app.templates_service import REVIEW_LINKS

            # Determine period (e.g. yesterday, today, or target_date)
            if "ayer" in text_lower:
                d_from = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
                d_to = d_from
                period_label = "de ayer"
            elif "3 dias" in text_lower or "tres dias" in text_lower:
                d_from = (date.today() - timedelta(days=3)).strftime("%Y-%m-%d")
                d_to = date.today().strftime("%Y-%m-%d")
                period_label = "de los últimos 3 días"
            elif "semana" in text_lower:
                d_from = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
                d_to = date.today().strftime("%Y-%m-%d")
                period_label = "de los últimos 7 días"
            elif target_date:
                d_from = target_date
                d_to = target_date
                period_label = f"del {target_date}"
            else:
                d_from = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
                d_to = d_from
                period_label = "de ayer (post-tour)"

            t_id = matched_tour["id"] if matched_tour else None
            review_bookings = turitop.get_bookings(
                tour_id=t_id,
                provider_filter=target_provider,
                date_from=d_from,
                date_to=d_to
            )

            if not review_bookings:
                # Fallback to today if yesterday had 0 in simulator/live
                review_bookings = turitop.get_bookings(tour_id=t_id, provider_filter=target_provider)
                period_label = "de hoy"

            prepared = []
            lang_breakdown = {}
            prov_breakdown = {}
            total_pax = 0

            for b in review_bookings:
                lc = b["language"]["code"]
                flag = b["language"]["flag"]
                ln = b["language"]["name"]
                pax = b.get("pax", 1)
                total_pax += pax
                p_info = b.get("provider", {})
                p_id = p_info.get("id", "otros")
                p_name = p_info.get("name", "Web")

                # Smart review destination
                if p_id == "civitatis":
                    dest_platform = "Civitatis"
                    dest_url = REVIEW_LINKS.get("civitatis")
                elif p_id == "getyourguide":
                    dest_platform = "GetYourGuide"
                    dest_url = REVIEW_LINKS.get("getyourguide")
                elif p_id == "viator":
                    dest_platform = "TripAdvisor / Viator"
                    dest_url = REVIEW_LINKS.get("viator")
                elif p_id == "guruwalk":
                    dest_platform = "GuruWalk"
                    dest_url = REVIEW_LINKS.get("guruwalk")
                elif p_id == "freetour":
                    dest_platform = "FreeTour.com"
                    dest_url = REVIEW_LINKS.get("freetour")
                else:
                    dest_platform = "Google Maps"
                    dest_url = REVIEW_LINKS.get("google")

                t_name = b.get("tour_name") or (matched_tour["name"] if matched_tour else "Excursión Tour Galicia")

                msg = template_mgr.render(
                    client_name=b["client_name"],
                    tour_name=t_name,
                    lang_code=lc,
                    company_name=COMPANY_NAME,
                    template_type="review_request",
                    review_link=dest_url,
                    platform_name=dest_platform
                )

                lang_breakdown.setdefault(ln, {"count": 0, "flag": flag})
                lang_breakdown[ln]["count"] += 1
                prov_breakdown[p_name] = prov_breakdown.get(p_name, 0) + 1

                prepared.append({
                    "booking_id": b["id"],
                    "client_name": b["client_name"],
                    "phone": b["phone"],
                    "language": b["language"],
                    "pax": pax,
                    "slot": b.get("slot", "-"),
                    "pickup_stop": b.get("pickup_stop", "-"),
                    "status": b.get("status", "Confirmado"),
                    "provider": p_info,
                    "platform_name": dest_platform,
                    "review_link": dest_url,
                    "message": msg
                })

            reply_lines = [
                f"⭐ **Campaña de Reseñas Post-Tour Preparada ({period_label})**",
                f"📊 **Total:** {len(prepared)} clientes ({total_pax} pasajeros)\n",
                f"🏢 **Desglose de Canales / Enlaces de Reseña:**"
            ]
            for prov, count in prov_breakdown.items():
                reply_lines.append(f"  • **{prov}**: {count} clientes (enlace inteligente a su plataforma)")

            reply_lines.append(f"\n🌍 **Idiomas de los mensajes:**")
            for lang, data in lang_breakdown.items():
                reply_lines.append(f"  • {data['flag']} {lang}: {data['count']} mensajes")

            reply_lines.append("\n👉 _Revisa los mensajes preparados abajo y pulsa **Enviar WhatsApp** para despacharlos masivamente._")
            reply = "\n".join(reply_lines)

            return {
                "success": True,
                "intent": "review_campaign",
                "engine": used_engine,
                "tour": matched_tour or {"name": "Todos los Tours"},
                "new_time": "-",
                "reason": "Campaña de Reseñas",
                "target_slots": [],
                "total_clients": len(prepared),
                "total_pax": total_pax,
                "languages_summary": lang_breakdown,
                "providers_summary": prov_breakdown,
                "assistant_reply": reply,
                "clients": prepared
            }

        # Intent: OVERVIEW ALL
        if intent == "overview_all":
            summary = turitop.get_all_tours_summary_message(target_date=target_date)
            return {"success": True, "intent": "overview_all", "is_summary": True,
                    "engine": "TuriTop Overview", "summary_text": summary,
                    "assistant_reply": summary, "total_clients": len(turitop.get_bookings(target_date=target_date)),
                    "target_slots": [], "tour": {"name": "Todos los Tours"}, "new_time": "-",
                    "reason": "Resumen General", "languages_summary": {}, "clients": []}

        # Intent: INFO QUERY BY PICKUP STOP (e.g. "cuántos pasajeros hay para el Pilar hoy", "clientes en el Peregrino", etc.)
        if intent == "info_query" and target_pickup and not matched_tour:
            pickup_bookings = turitop.get_bookings(target_date=target_date, pickup_filter=target_pickup, provider_filter=target_provider)
            p_stop_label = pickup_bookings[0]["pickup_stop"] if pickup_bookings else target_pickup.capitalize()
            p_stop_icon = pickup_bookings[0].get("pickup_icon", "📍") if pickup_bookings else "📍"
            date_label = f"para el {target_date}" if target_date else "hoy"

            if not pickup_bookings:
                reply = f"No hay reservas registradas con salida en **{p_stop_label}** {date_label} en TuriTop."
                total_pax = 0
            else:
                total_pax = sum(b.get("pax", 1) for b in pickup_bookings)
                # Group by tour
                by_tour = {}
                for b in pickup_bookings:
                    by_tour.setdefault(b["tour_name"], []).append(b)

                lines = [
                    f"{p_stop_icon} **CLIENTES CON SALIDA EN {p_stop_label.upper()}** ({date_label})",
                    f"📊 **Total:** {len(pickup_bookings)} reserva(s) | **{total_pax} pasajero(s)** en total\n"
                ]
                for t_name, clients in by_tour.items():
                    t_pax = sum(c.get("pax", 1) for c in clients)
                    lines.append(f"🚌 **{t_name}** ({len(clients)} reservas / **{t_pax} pax**):")
                    for c in clients:
                        flag = c["language"]["flag"]
                        pax_label = f"{c.get('pax', 1)} pax" if c.get('pax', 1) > 1 else "1 pax"
                        prov_tag = f" [{c['provider']['code']}]" if c.get('provider') else ""
                        lines.append(f"  • {c['client_name']} ({pax_label}) {flag}{prov_tag}  |  {c['phone']}  |  {c['slot']}")
                    lines.append("")
                reply = "\n".join(lines).strip()

            return {"success": True, "intent": "info_query", "engine": used_engine,
                    "assistant_reply": reply, "tour": {"name": f"Todos ({p_stop_label})"}, "new_time": None,
                    "reason": None, "target_slots": [], "total_clients": len(pickup_bookings),
                    "total_pax": total_pax,
                    "languages_summary": {}, "clients": []}

        # Intent: INFO QUERY BY PROVIDER (when user asks for e.g. "clientes de Civitatis" across all tours)
        if intent == "info_query" and target_provider and not matched_tour:
            prov_bookings = turitop.get_bookings(target_date=target_date, provider_filter=target_provider, pickup_filter=target_pickup)
            prov_name = target_provider.capitalize() if target_provider else "Proveedor"
            date_label = f"para el {target_date}" if target_date else "hoy"

            if not prov_bookings:
                reply = f"No hay reservas registradas de **{prov_name}** {date_label} en TuriTop."
                total_pax = 0
            else:
                total_pax = sum(b.get("pax", 1) for b in prov_bookings)
                prov_label = prov_bookings[0]["provider"]["name"] if prov_bookings else prov_name
                prov_icon = prov_bookings[0]["provider"].get("icon", "🏢") if prov_bookings else "🏢"
                
                # Group by tour
                by_tour = {}
                for b in prov_bookings:
                    by_tour.setdefault(b["tour_name"], []).append(b)

                lines = [
                    f"{prov_icon} **CLIENTES DE {prov_label.upper()}** ({date_label})",
                    f"📊 **Total:** {len(prov_bookings)} reserva(s) | **{total_pax} pasajero(s)** en total\n"
                ]
                for t_name, clients in by_tour.items():
                    t_pax = sum(c.get("pax", 1) for c in clients)
                    lines.append(f"📍 **{t_name}** ({len(clients)} reservas / **{t_pax} pax**):")
                    for c in clients:
                        flag = c["language"]["flag"]
                        pax_label = f"{c.get('pax', 1)} pax" if c.get('pax', 1) > 1 else "1 pax"
                        ref_str = f" [Ref: {c['provider'].get('reference')}]" if c['provider'].get('reference') else ""
                        lines.append(f"  • {c['client_name']} ({pax_label}) {flag}{ref_str}  |  {c['phone']}  |  {c['pickup_stop']}")
                    lines.append("")
                reply = "\n".join(lines).strip()

            return {"success": True, "intent": "info_query", "engine": used_engine,
                    "assistant_reply": reply, "tour": {"name": f"Todos ({prov_name})"}, "new_time": None,
                    "reason": None, "target_slots": [], "total_clients": len(prov_bookings),
                    "total_pax": total_pax,
                    "languages_summary": {}, "clients": []}

        # Tour not found (and not a global provider / pickup search)
        if not matched_tour:
            names = "\n".join(f"  • {t['name']}" for t in available_tours[:15])
            reply = f"No he encontrado ningún tour coincidente en TuriTop.\n\n**Tours disponibles:**\n{names}\n\nPrueba escribiendo por ejemplo: *'avisa a todos los clientes de Finisterre del punto de encuentro'*, *'cuántos pasajeros hay para el Pilar'* o *'localiza clientes de Civitatis hoy'*."
            return {"success": False, "intent": intent, "engine": used_engine,
                    "assistant_reply": reply, "tour": None, "new_time": new_time,
                    "reason": reason, "target_slots": [], "total_clients": 0,
                    "languages_summary": {}, "clients": []}

        # Intent: INFO QUERY FOR SPECIFIC TOUR (with optional provider / pickup filter)
        if intent == "info_query":
            bookings = turitop.get_bookings(tour_id=matched_tour["id"], target_date=target_date, provider_filter=target_provider, pickup_filter=target_pickup)
            date_label = f"para el {target_date}" if target_date else "hoy"
            prov_extra = f" de {target_provider.capitalize()}" if target_provider else ""
            pickup_extra = f" con salida en {target_pickup.capitalize()}" if target_pickup else ""
            if not bookings:
                reply = f"No hay reservas registradas{prov_extra}{pickup_extra} {date_label} para **{matched_tour['name']}**."
                total_pax = 0
            else:
                total_pax = sum(b.get("pax", 1) for b in bookings)
                by_stop = {}
                for b in bookings:
                    stop = b.get("pickup_stop") or "Capilla del Pilar"
                    by_stop.setdefault(stop, []).append(b)

                lines = [
                    f"**{matched_tour['name']}**{prov_extra}{pickup_extra}",
                    f"📊 **Total:** {len(bookings)} reserva(s) | **{total_pax} pasajero(s)** en total ({date_label})\n"
                ]
                for stop, clients in by_stop.items():
                    stop_pax = sum(c.get("pax", 1) for c in clients)
                    lines.append(f"📍 Punto de salida: **{stop}** ({len(clients)} reservas / **{stop_pax} pax**):")
                    for c in clients:
                        flag = c["language"]["flag"]
                        pax_label = f"{c.get('pax', 1)} pax" if c.get('pax', 1) > 1 else "1 pax"
                        prov_tag = f" [{c['provider']['code']}]" if c.get('provider') else ""
                        lines.append(f"  • {c['client_name']} ({pax_label}) {flag}{prov_tag}  |  {c['phone']}  |  {c['slot']}")
                    lines.append("")
                reply = "\n".join(lines).strip()

            return {"success": True, "intent": "info_query", "engine": used_engine,
                    "assistant_reply": reply, "tour": matched_tour, "new_time": None,
                    "reason": None, "target_slots": [], "total_clients": len(bookings) if bookings else 0,
                    "total_pax": total_pax,
                    "languages_summary": {}, "clients": []}

        # Intent: SCHEDULE CHANGE / BROADCAST NOTIFICATION (The main action)
        all_bookings = turitop.get_bookings(
            tour_id=matched_tour["id"],
            target_date=target_date,
            provider_filter=target_provider,
            pickup_filter=target_pickup
        )
        if target_slots:
            affected = [b for b in all_bookings if b["slot"] in target_slots]
        else:
            affected = all_bookings

        lang_breakdown = {}
        stops_breakdown = {}
        prepared = []
        total_pax = 0

        for booking in affected:
            lc = booking["language"]["code"]
            flag = booking["language"]["flag"]
            ln = booking["language"]["name"]
            stop = booking.get("pickup_stop") or "Punto de salida principal"
            pax = booking.get("pax", 1)
            total_pax += pax

            lang_breakdown.setdefault(ln, {"count": 0, "flag": flag})
            lang_breakdown[ln]["count"] += 1

            stops_breakdown.setdefault(stop, {"bookings": 0, "pax": 0})
            stops_breakdown[stop]["bookings"] += 1
            stops_breakdown[stop]["pax"] += pax

            msg_time = new_time if new_time else booking["slot"]
            
            # Use departure_pickup template with specific stop & audioguide
            msg = template_mgr.render(
                client_name=booking["client_name"],
                tour_name=matched_tour["name"],
                new_time=msg_time,
                pickup_stop=stop,
                reason=reason,
                lang_code=lc,
                company_name=COMPANY_NAME,
                template_type="departure_pickup" if not new_time or new_time == booking["slot"] else "schedule_change"
            )

            prepared.append({
                "booking_id": booking["id"],
                "client_name": booking["client_name"],
                "phone": booking["phone"],
                "language": booking["language"],
                "original_slot": booking["slot"],
                "slot": msg_time,
                "pickup_stop": stop,
                "pickup_short": booking.get("pickup_short", "Pilar"),
                "pickup_code": booking.get("pickup_code", "pilar"),
                "pickup_badge": booking.get("pickup_badge", "bg-amber-100 text-amber-800 border-amber-300"),
                "pickup_icon": booking.get("pickup_icon", "⛪"),
                "pax": pax,
                "status": booking.get("status", "Confirmado"),
                "provider": booking.get("provider", {}),
                "message": msg
            })

        reply_lines = [
            f"✅ **Mensajes preparados para {matched_tour['name']}**",
            f"📊 **Total:** {len(prepared)} reserva(s) ({total_pax} pasajeros)\n",
            f"📍 **Desglose por Punto de Recogida extraído de TuriTop:**"
        ]
        for stop, st in stops_breakdown.items():
            reply_lines.append(f"  • **{stop}**: {st['bookings']} reservas ({st['pax']} pax)")

        reply_lines.append(f"\n🌍 **Idiomas asignados automáticamente por prefijo:**")
        for lang, data in lang_breakdown.items():
            reply_lines.append(f"  • {data['flag']} {lang}: {data['count']} mensajes (con audioguía en su idioma)")

        reply_lines.append("\n👉 _Revisa la tabla a continuación y pulsa **Confirmar y Enviar** para despacharlos por WhatsApp._")

        reply = "\n".join(reply_lines)

        return {
            "success": True,
            "intent": "schedule_change",
            "engine": used_engine,
            "tour": matched_tour,
            "new_time": new_time,
            "reason": reason,
            "target_slots": target_slots,
            "total_clients": len(prepared),
            "total_pax": total_pax,
            "languages_summary": lang_breakdown,
            "stops_summary": stops_breakdown,
            "assistant_reply": reply,
            "clients": prepared
        }


assistant = AssistantParser()
