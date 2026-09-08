import re
from datetime import date, timedelta
from typing import Dict, Any, Optional, List

from app.turitop_service import turitop
from app.templates_service import template_mgr, REVIEW_LINKS
from app.gemini_service import gemini
from app.config import COMPANY_NAME


def _fuzzy_match_tour(text_lower: str, available_tours: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    # Specific high-priority keyword mappings
    if "express" in text_lower or "expres" in text_lower:
        f_express = next((t for t in available_tours if "express" in t["name"].lower() or "finsiterre express" in t["name"].lower()), None)
        if f_express:
            return f_express

    if "premium" in text_lower:
        f_prem = next((t for t in available_tours if "premium" in t["name"].lower()), None)
        if f_prem:
            return f_prem

    if "vip" in text_lower:
        f_vip = next((t for t in available_tours if "vip" in t["name"].lower()), None)
        if f_vip:
            return f_vip

    if "autoguiado" in text_lower:
        f_auto = next((t for t in available_tours if "autoguiado" in t["name"].lower()), None)
        if f_auto:
            return f_auto

    if "atardecer" in text_lower:
        f_atar = next((t for t in available_tours if "atardecer" in t["name"].lower()), None)
        if f_atar:
            return f_atar

    if "meigas" in text_lower or "misterios" in text_lower or "teatralizado" in text_lower:
        meig = next((t for t in available_tours if "meigas" in t["name"].lower()), None)
        if meig:
            return meig

    if "catedrales" in text_lower or "playa" in text_lower or "ribadeo" in text_lower:
        cat = next((t for t in available_tours if "catedrales" in t["name"].lower() and "santiago" in t["name"].lower()), None)
        if cat:
            return cat

    if "rias" in text_lower or "rías" in text_lower or "baixas" in text_lower or "toxa" in text_lower:
        rias = next((t for t in available_tours if "rias baixas" in t["name"].lower() and "santiago" in t["name"].lower()), None)
        if rias:
            return rias

    if "ribeira" in text_lower or "sacra" in text_lower or "ourense" in text_lower:
        rib = next((t for t in available_tours if "ribeira sacra" in t["name"].lower() and "salida ourense" not in t["name"].lower()), None)
        if rib:
            return rib

    if "finisterre" in text_lower or "morte" in text_lower or "fisterra" in text_lower:
        finis = next((t for t in available_tours if t["id"] == "P1" or "finisterre y costa da morte desde santiago" in t["name"].lower()), None)
        if finis:
            return finis

    # Generic score match
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
    Connects to Gemini AI or local deterministic NLP rules to understand the intent and parameters,
    matches against live TuriTop CRM data, groups bookings by pickup stop,
    and prepares multilingual WhatsApp messages with audioguides (only for non-ES/EN).
    """

    def parse_instruction(self, text: str, target_date: Optional[str] = None) -> Dict[str, Any]:
        text_lower = text.lower().strip()
        available_tours = turitop.get_tours()
        intent = None
        matched_tour = None
        target_provider = None
        target_pickup = None
        new_time = None
        new_tour_name = None
        reason = "motivos de organización"
        target_slots = []
        used_engine = "Reglas Locales"

        # 1. Resolve date from natural language
        if "pasado mañana" in text_lower or "pasado manana" in text_lower:
            resolved_date = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")
            date_label = f"Pasado mañana ({(date.today() + timedelta(days=2)).strftime('%d/%m/%Y')})"
        elif "mañana" in text_lower or "manana" in text_lower:
            resolved_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
            date_label = f"Mañana ({(date.today() + timedelta(days=1)).strftime('%d/%m/%Y')})"
        elif "hoy" in text_lower:
            resolved_date = date.today().strftime("%Y-%m-%d")
            date_label = f"Hoy ({date.today().strftime('%d/%m/%Y')})"
        elif "ayer" in text_lower:
            resolved_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
            date_label = f"Ayer ({(date.today() - timedelta(days=1)).strftime('%d/%m/%Y')})"
        elif target_date:
            resolved_date = target_date
            date_label = target_date
        else:
            resolved_date = date.today().strftime("%Y-%m-%d")
            date_label = f"Hoy ({date.today().strftime('%d/%m/%Y')})"

        # 2. Ask Gemini AI first if configured
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

        # Fallback pickup detection
        if not target_pickup or target_pickup == "null":
            if any(k in text_lower for k in ["museo", "darsena", "dársena", "la salle", "salle"]):
                target_pickup = "museo"
            elif any(k in text_lower for k in ["peregrino", "exe"]):
                target_pickup = "peregrino"
            elif any(k in text_lower for k in ["pilar", "capilla"]):
                target_pickup = "pilar"
            else:
                target_pickup = None

        # Fallback provider detection
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

        # 3. Fallback intent detection
        relocation_kw = ["cambio del tour a", "cambio de tour a", "cambiar a regular", "unificar con", "reubicar en", "cambio al tour", "cambio de excursion a"]
        cancellation_kw = ["minimo", "mínimo", "no sale", "cancelar", "cancelación", "cancelacion", "cancelado", "cancelada", "suspender", "anular", "no se realiza", "no va a salir", "no hemos alcanzado"]
        review_kw = ["reseña", "reseñas", "opinion", "opiniones", "valoracion", "valoraciones", "review", "reviews", "google", "recordatorio de opinion"]
        sched_kw = ["avisa", "cambia", "unifica", "informa", "notifica", "retraso", "adelanta", "salida a las", "punto de encuentro", "enviar", "recuerda", "recordar"]
        info_kw = ["cuantos", "cuántos", "quien viene", "quién viene", "listado de", "localiza", "busca", "consultar"]
        overview_kw = ["que tours", "todos los tours", "tours de hoy", "resumen general"]

        if any(kw in text_lower for kw in relocation_kw):
            intent = "tour_relocation"
            new_tour_name = "Finisterre y Costa da Morte desde Santiago"
        elif any(kw in text_lower for kw in cancellation_kw):
            intent = "cancellation_notice"
        elif any(kw in text_lower for kw in review_kw):
            intent = "review_campaign"
        elif any(kw in text_lower for kw in overview_kw) and not any(kw in text_lower for kw in sched_kw):
            intent = "overview_all"
        elif any(kw in text_lower for kw in sched_kw):
            intent = "schedule_change"
        elif any(kw in text_lower for kw in info_kw):
            intent = "info_query"
        elif not intent:
            intent = "schedule_change"

        # 4. Match tour if not matched yet
        if not matched_tour and intent != "overview_all":
            matched_tour = _fuzzy_match_tour(text_lower, available_tours)

        # 5. Extract time if mentioned
        if not new_time:
            m = re.search(r'\b([0-2]?\d)[:.h]([0-5]\d)\b', text_lower)
            if m:
                h, mn = m.groups()
                new_time = f"{int(h):02d}:{mn}"
            else:
                m_single = re.search(r'\ba las?\s+([0-2]?\d)\b', text_lower)
                if m_single:
                    h = m_single.group(1)
                    new_time = f"{int(h):02d}:00"

        # 6. Extract reason if mentioned
        if any(kw in text_lower for kw in ["minimo", "mínimo", "no hemos alcanzado", "participantes"]):
            reason = "no haberse alcanzado el número mínimo de participantes requerido"
        elif "trafico" in text_lower or "tráfico" in text_lower:
            reason = "motivos de tráfico"
        elif "lluvia" in text_lower or "meteorol" in text_lower or "clima" in text_lower or "tiempo" in text_lower:
            reason = "condiciones meteorológicas"
        elif "logistic" in text_lower:
            reason = "motivos de organización"

        # Intent: REVIEW CAMPAIGN
        if intent == "review_campaign":
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
            else:
                d_from = resolved_date
                d_to = resolved_date
                period_label = date_label

            t_id = matched_tour["id"] if matched_tour else None
            bookings = turitop.get_bookings(tour_id=t_id, provider_filter=target_provider, date_from=d_from, date_to=d_to)
            tours_dict = {t["id"]: t["name"] for t in available_tours}

            prepared = []
            lang_breakdown = {}
            prov_breakdown = {}
            total_pax = 0

            for b in bookings:
                lc = b["language"]["code"]
                flag = b["language"]["flag"]
                ln = b["language"]["name"]
                pax = b.get("pax", 1)
                total_pax += pax
                p_info = b.get("provider", {})
                p_id = p_info.get("id", "otros")
                p_name = p_info.get("name", "Web")

                if p_id == "civitatis":
                    dest_platform = "Civitatis"
                    dest_url = REVIEW_LINKS.get("civitatis")
                elif p_id == "getyourguide":
                    dest_platform = "GetYourGuide"
                    dest_url = REVIEW_LINKS.get("getyourguide")
                elif p_id == "viator":
                    dest_platform = "TripAdvisor / Viator"
                    dest_url = REVIEW_LINKS.get("viator")
                else:
                    dest_platform = "Google Maps"
                    dest_url = REVIEW_LINKS.get("google")

                t_name = b.get("tour_name") or tours_dict.get(b.get("tour_id"), "Excursión Tour Galicia")

                msg = template_mgr.render(
                    client_name=b["client_name"],
                    tour_name=t_name,
                    tour_id=b.get("tour_id"),
                    lang_code=lc,
                    company_name=COMPANY_NAME,
                    template_type="review_request",
                    review_link=dest_url,
                    platform_name=dest_platform,
                    date_label=date_label
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
                f"🏢 **Desglose de Plataformas de Reseña:**"
            ]
            for prov, count in prov_breakdown.items():
                reply_lines.append(f"  • **{prov}**: {count} clientes (enlace a su plataforma)")

            reply_lines.append(f"\n🌍 **Idiomas:**")
            for lang, data in lang_breakdown.items():
                reply_lines.append(f"  • {data['flag']} {lang}: {data['count']} mensajes")

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
            summary = turitop.get_all_tours_summary_message(target_date=resolved_date)
            return {"success": True, "intent": "overview_all", "is_summary": True,
                    "engine": "TuriTop Overview", "summary_text": summary,
                    "assistant_reply": summary, "total_clients": len(turitop.get_bookings(target_date=resolved_date)),
                    "target_slots": [], "tour": {"name": "Todos los Tours"}, "new_time": "-",
                    "reason": "Resumen General", "languages_summary": {}, "clients": []}

        # Tour not found
        if not matched_tour:
            names = "\n".join(f"  • {t['name']}" for t in available_tours[:10])
            reply = f"No he encontrado ningún tour coincidente en TuriTop.\n\n**Tours principales:**\n{names}\n\nPrueba por ejemplo: *'Avisa a los clientes de Finisterre del día de mañana del punto de salida'* o *'Avisa a los clientes de Playa de las Catedrales de que mañana sale el tour a las 08:00'*."
            return {"success": False, "intent": intent, "engine": used_engine,
                    "assistant_reply": reply, "tour": None, "new_time": new_time,
                    "reason": reason, "target_slots": [], "total_clients": 0,
                    "languages_summary": {}, "clients": []}

        # Intent: CANCELLATION / TOUR RELOCATION / SCHEDULE CHANGE / DEPARTURE PICKUP NOTIFICATION
        all_bookings = turitop.get_bookings(
            tour_id=matched_tour["id"],
            target_date=resolved_date,
            provider_filter=target_provider,
            pickup_filter=target_pickup
        )

        # Smart slot exclusion for schedule changes (e.g. Meigas at 19:00: exclude clients ALREADY booked for 19:00)
        excluded_already_on_time = 0
        if intent == "schedule_change" and new_time and ("meigas" in text_lower or "cambio" in text_lower or "salida sera a las" in text_lower or "salida a las" in text_lower):
            affected = []
            for b in all_bookings:
                b_slot = b.get("slot", "")
                if b_slot == new_time:
                    excluded_already_on_time += b.get("pax", 1)
                else:
                    affected.append(b)
        elif target_slots:
            affected = [b for b in all_bookings if b["slot"] in target_slots]
        else:
            affected = all_bookings

        lang_breakdown = {}
        stops_breakdown = {}
        prepared = []
        total_pax = 0

        # Determine template category
        if intent == "tour_relocation":
            tpl_category = "tour_relocation"
        elif intent == "cancellation_notice":
            tpl_category = "cancellation_notice"
        elif new_time and any(b.get("slot") != new_time for b in affected):
            tpl_category = "schedule_change"
        else:
            tpl_category = "departure_pickup"

        for booking in affected:
            lc = booking["language"]["code"]
            flag = booking["language"]["flag"]
            ln = booking["language"]["name"]
            stop = booking.get("pickup_stop") or "Capilla del Pilar"
            pax = booking.get("pax", 1)
            total_pax += pax

            lang_breakdown.setdefault(ln, {"count": 0, "flag": flag})
            lang_breakdown[ln]["count"] += 1

            stops_breakdown.setdefault(stop, {"bookings": 0, "pax": 0, "icon": booking.get("pickup_icon", "📍")})
            stops_breakdown[stop]["bookings"] += 1
            stops_breakdown[stop]["pax"] += pax

            msg_time = new_time if new_time else (booking.get("slot") or "09:00")
            
            # Smart template rendering based on tour, language, reason, date and new tour
            msg = template_mgr.render(
                client_name=booking["client_name"],
                tour_name=matched_tour["name"],
                tour_id=matched_tour.get("id"),
                new_time=msg_time,
                pickup_stop=stop,
                reason=reason,
                lang_code=lc,
                company_name=COMPANY_NAME,
                template_type=tpl_category,
                date_label=date_label,
                new_tour_name=new_tour_name or "Finisterre y Costa da Morte desde Santiago"
            )

            prepared.append({
                "booking_id": booking["id"],
                "client_name": booking["client_name"],
                "phone": booking["phone"],
                "language": booking["language"],
                "original_slot": booking.get("slot", "09:00"),
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

        if intent == "tour_relocation":
            reply_lines = [
                f"🔄 **Cambio / Reubicación de Tour: {matched_tour['name']} ➔ {new_tour_name}**",
                f"📅 **Fecha:** {date_label}",
                f"📊 **Total:** {len(prepared)} reserva(s) ({total_pax} pasajeros)",
                f"💬 **Mensajes redactados en el idioma de cada cliente informando del cambio a la excursión regular completa.**"
            ]
        elif intent == "cancellation_notice":
            reply_lines = [
                f"⚠️ **Avisos de Cancelación / Alternativas — {matched_tour['name']}**",
                f"📅 **Fecha:** {date_label}",
                f"📊 **Total:** {len(prepared)} reserva(s) ({total_pax} pasajeros)",
                f"ℹ️ **Motivo:** {reason}\n",
                f"💬 **Mensajes redactados en el idioma nativo de cada cliente con opciones de reubicación y reembolso.**"
            ]
        else:
            reply_lines = [
                f"🚌 **{matched_tour['name']}** — {date_label}",
                f"📊 **Total:** {len(prepared)} reservas ({total_pax} pasajeros)\n",
                f"📍 **Puntos de Recogida Asignados:**"
            ]
            for stop, st in stops_breakdown.items():
                icon = st.get("icon", "📍")
                reply_lines.append(f"  {icon} **{stop}**: {st['bookings']} reservas ({st['pax']} pax)")

            if excluded_already_on_time > 0:
                reply_lines.append(f"\n💡 _Nota: Se han excluido automáticamente {excluded_already_on_time} pasajeros que ya tenían salida a las {new_time} para no duplicar avisos._")

        reply_lines.append(f"\n🌍 **Idiomas y Mensajes Preparados:**")
        for lang, data in lang_breakdown.items():
            audioguide_note = " (sin audioguía, guía presencial)" if lang in ["Español", "English"] else " (con enlace a audioguía)"
            reply_lines.append(f"  • {data['flag']} {lang}: {data['count']} mensajes{audioguide_note}")

        reply = "\n".join(reply_lines)

        return {
            "success": True,
            "intent": intent,
            "engine": used_engine,
            "tour": matched_tour,
            "target_date": resolved_date,
            "date_label": date_label,
            "new_time": new_time or (prepared[0]["slot"] if prepared else "09:00"),
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
