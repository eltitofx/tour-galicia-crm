import os
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

TEMPLATES_FILE = Path(__file__).resolve().parent.parent / "custom_templates.json"

AUDIOGUIDE_LINKS = {
    "es": "https://audioguide.tourgalicia.es/es",
    "en": "https://audioguide.tourgalicia.es/en",
    "fr": "https://audioguide.tourgalicia.es/fr",
    "de": "https://audioguide.tourgalicia.es/de",
    "pt": "https://audioguide.tourgalicia.es/pt",
    "it": "https://audioguide.tourgalicia.es/it"
}

REVIEW_LINKS = {
    "google": "https://g.page/r/TourGalicia/review",
    "civitatis": "https://www.civitatis.com/es/santiago-de-compostela/",
    "getyourguide": "https://www.getyourguide.com/account/bookings",
    "viator": "https://www.tripadvisor.es/UserReviewEdit",
    "guruwalk": "https://www.guruwalk.com/es/santiago-de-compostela",
    "freetour": "https://www.freetour.com/es/santiago-de-compostela",
    "default": "https://g.page/r/TourGalicia/review"
}

DEFAULT_SYSTEM_TEMPLATES = {
    "departure_pickup": {
        "es": (
            "👋 Hola *{nombre}*,\n\n"
            "Te contactamos desde *{empresa}* para confirmarte los detalles de tu excursión *{tour}* de hoy:\n\n"
            "📍 *Punto de recogida / Salida:* {parada}\n"
            "⏰ *Hora de encuentro:* *{hora}*\n"
            "⚠️ _Rogamos estar presentes 10 minutos antes._\n\n"
            "🎧 *Audioguía en tu idioma:* {audioguia}\n\n"
            "Si tienes cualquier consulta, puedes responder a este mensaje.\n"
            "¡Que disfrutes de la experiencia! 🚌✨"
        ),
        "en": (
            "👋 Hello *{nombre}*,\n\n"
            "Greetings from *{empresa}*! Here are the departure details for your *{tour}* excursion today:\n\n"
            "📍 *Pick-up / Meeting Point:* {parada}\n"
            "⏰ *Meeting Time:* *{hora}*\n"
            "⚠️ _Please arrive 10 minutes prior to departure._\n\n"
            "🎧 *Audioguide in your language:* {audioguia}\n\n"
            "If you have any questions, feel free to reply directly to this WhatsApp message.\n"
            "Enjoy your tour! 🚌✨"
        ),
        "fr": (
            "👋 Bonjour *{nombre}*,\n\n"
            "De la part de *{empresa}* pour vous confirmer les détails de votre excursion *{tour}* d'aujourd'hui :\n\n"
            "📍 *Point de rendez-vous / Prise en charge :* {parada}\n"
            "⏰ *Heure de rendez-vous :* *{hora}*\n"
            "⚠️ _Merci de vous présenter 10 minutes avant._\n\n"
            "🎧 *Audioguide en français :* {audioguia}\n\n"
            "Bonne visite avec nous ! 🚌✨"
        ),
        "de": (
            "👋 Hallo *{nombre}*,\n\n"
            "hier ist *{empresa}* mit den Details für Ihren Ausflug *{tour}* heute:\n\n"
            "📍 *Treffpunkt / Abholung:* {parada}\n"
            "⏰ *Abfahrtszeit:* *{hora}* Uhr\n"
            "⚠️ _Bitte seien Sie 10 Minuten vor Abfahrt vor Ort._\n\n"
            "🎧 *Audioguide auf Deutsch:* {audioguia}\n\n"
            "Wir wünschen Ihnen ein tolles Erlebnis! 🚌✨"
        ),
        "pt": (
            "👋 Olá *{nombre}*,\n\n"
            "Contactamos da *{empresa}* para confirmar os detalhes da sua excursão *{tour}* de hoje:\n\n"
            "📍 *Ponto de encontro / Paragem:* {parada}\n"
            "⏰ *Horário de saída:* *{hora}*\n"
            "⚠️ _Pedimos o favor de estar presente com 10 minutos de antecedência._\n\n"
            "🎧 *Audioguia em português:* {audioguia}\n\n"
            "Tenha um excelente passeio! 🚌✨"
        ),
        "it": (
            "👋 Ciao *{nombre}*,\n\n"
            "Ti contattiamo da *{empresa}* per confermarti i dettagli dell'escursione *{tour}* di oggi:\n\n"
            "📍 *Punto di incontro / Fermata:* {parada}\n"
            "⏰ *Orario di partenza:* *{hora}*\n"
            "⚠️ _Si prega di presentarsi 10 minuti prima._\n\n"
            "🎧 *Audioguida in italiano:* {audioguia}\n\n"
            "Buona escursione con noi! 🚌✨"
        )
    },
    "schedule_change": {
        "es": (
            "👋 Hola *{nombre}*,\n\n"
            "Te contactamos desde *{empresa}* referente a tu reserva para la excursión *{tour}* de hoy.\n\n"
            "ℹ️ *Aviso de Horario:*\n"
            "Por {motivo}, el horario de salida será a las *{hora}*.\n\n"
            "📍 *Punto de encuentro:* {parada}\n"
            "⏰ *Nueva hora:* *{hora}* (estar 10 min antes).\n\n"
            "🎧 *Audioguía en tu idioma:* {audioguia}\n\n"
            "¡Muchas gracias y nos vemos pronto! 🚌✨\n"
            "— *Equipo de {empresa}*"
        ),
        "en": (
            "👋 Hello *{nombre}*,\n\n"
            "We are contacting you from *{empresa}* regarding your booking for the *{tour}* tour today.\n\n"
            "ℹ️ *Schedule Update:*\n"
            "Due to {motivo}, your updated departure time is now *{hora}*.\n\n"
            "📍 *Meeting Point:* {parada}\n"
            "⏰ *New time:* *{hora}* (please arrive 10 min early).\n\n"
            "🎧 *Audioguide in your language:* {audioguia}\n\n"
            "Thank you, see you soon! 🚌✨\n"
            "— *{empresa} Team*"
        ),
        "fr": (
            "👋 Bonjour *{nombre}*,\n\n"
            "De la part de *{empresa}* concernant votre réservation pour *{tour}* aujourd'hui.\n\n"
            "ℹ️ *Mise à jour horaire :*\n"
            "Pour {motivo}, votre nouvel horaire de départ est à *{hora}*.\n\n"
            "📍 *Point de rendez-vous :* {parada}\n"
            "⏰ *Nouvelle heure :* *{hora}* (merci d'arriver 10 min avant).\n\n"
            "🎧 *Audioguide :* {audioguia}\n\n"
            "Merci et à très bientôt ! 🚌✨\n"
            "— *L'équipe {empresa}*"
        ),
        "de": (
            "👋 Hallo *{nombre}*,\n\n"
            "wir kontaktieren Sie von *{empresa}* bezüglich Ihrer Buchung für *{tour}* heute.\n\n"
            "ℹ️ *Fahrplanänderung:*\n"
            "Aus {motivo} ist die neue Abfahrtszeit um *{hora}* Uhr.\n\n"
            "📍 *Treffpunkt:* {parada}\n"
            "⏰ *Neue Zeit:* *{hora}* Uhr (bitte 10 min vorher da sein).\n\n"
            "🎧 *Audioguide:* {audioguia}\n\n"
            "Vielen Dank! 🚌✨\n"
            "— *{empresa}*"
        ),
        "pt": (
            "👋 Olá *{nombre}*,\n\n"
            "Da *{empresa}* referente à sua reserva para *{tour}* hoje.\n\n"
            "ℹ️ *Aviso de Horário:*\n"
            "Por {motivo}, a hora de saída será às *{hora}*.\n\n"
            "📍 *Ponto de encontro:* {parada}\n"
            "⏰ *Nova hora:* *{hora}* (chegar 10 min antes).\n\n"
            "🎧 *Audioguia:* {audioguia}\n\n"
            "Muito obrigado! 🚌✨\n"
            "— *{empresa}*"
        ),
        "it": (
            "👋 Ciao *{nombre}*,\n\n"
            "Da *{empresa}* in merito all'escursione *{tour}* di oggi.\n\n"
            "ℹ️ *Avviso di orario:*\n"
            "Per {motivo}, l'orario di partenza sarà alle *{hora}*.\n\n"
            "📍 *Punto di incontro:* {parada}\n"
            "⏰ *Nuovo orario:* *{hora}* (presentarsi 10 min prima).\n\n"
            "🎧 *Audioguida:* {audioguia}\n\n"
            "Grazie e a presto! 🚌✨\n"
            "— *{empresa}*"
        )
    },
    "review_request": {
        "es": (
            "👋 ¡Hola *{nombre}*!\n\n"
            "Esperamos que hayas disfrutado al máximo de tu excursión *{tour}* con *{empresa}* ⭐.\n\n"
            "Tu opinión es fundamental para nosotros y ayuda a futuros viajeros. ¿Nos regalarías 1 minuto para valorar tu experiencia en *{plataforma}*?\n\n"
            "✍️ *Deja tu reseña aquí:* 👇\n"
            "👉 {enlace_resena}\n\n"
            "¡Muchísimas gracias por viajar con nosotros y esperamos verte pronto de nuevo en Galicia! 💙🚌✨\n"
            "— *Equipo de {empresa}*"
        ),
        "en": (
            "👋 Hello *{nombre}*!\n\n"
            "We hope you had a wonderful experience on your *{tour}* tour with *{empresa}* ⭐.\n\n"
            "Your feedback means a lot to our team and helps other travelers. Could you take 1 minute to rate your experience on *{plataforma}*?\n\n"
            "✍️ *Leave your review here:* 👇\n"
            "👉 {enlace_resena}\n\n"
            "Thank you so much for joining us and we hope to welcome you back to Galicia! 💙🚌✨\n"
            "— *{empresa} Team*"
        ),
        "fr": (
            "👋 Bonjour *{nombre}* !\n\n"
            "Nous espérons que vous avez passé un excellent moment lors de votre excursion *{tour}* avec *{empresa}* ⭐.\n\n"
            "Votre avis compte énormément pour nous. Pourriez-vous nous accorder 1 minute pour partager votre expérience sur *{plataforma}* ?\n\n"
            "✍️ *Laissez votre avis ici :* 👇\n"
            "👉 {enlace_resena}\n\n"
            "Merci beaucoup d'avoir voyagé avec nous et à bientôt en Galice ! 💙🚌✨\n"
            "— *L'équipe {empresa}*"
        ),
        "de": (
            "👋 Hallo *{nombre}*!\n\n"
            "Wir hoffen, Sie hatten ein fantastisches Erlebnis bei Ihrem Ausflug *{tour}* mit *{empresa}* ⭐.\n\n"
            "Ihre Meinung ist uns sehr wichtig. Dürfen wir Sie um 1 Minute für ein kurzes Feedback auf *{plataforma}* bitten?\n\n"
            "✍️ *Bewertung hier abgeben:* 👇\n"
            "👉 {enlace_resena}\n\n"
            "Vielen Dank und bis zum nächsten Mal in Galizien! 💙🚌✨\n"
            "— *{empresa}*"
        ),
        "pt": (
            "👋 Olá *{nombre}*!\n\n"
            "Esperamos que tenha desfrutado ao máximo do seu passeio *{tour}* com a *{empresa}* ⭐.\n\n"
            "A sua avaliação é muito importante para nós. Poderia dispensar 1 minuto para partilhar a sua experiência no *{plataforma}*?\n\n"
            "✍️ *Deixe a sua avaliação aqui:* 👇\n"
            "👉 {enlace_resena}\n\n"
            "Muito obrigado por viajar connosco e até breve na Galiza! 💙🚌✨\n"
            "— *{empresa}*"
        ),
        "it": (
            "👋 Ciao *{nombre}*!\n\n"
            "Speriamo che la tua escursione *{tour}* con *{empresa}* sia stata un'esperienza fantastica ⭐.\n\n"
            "La tua opinione è preziosa per noi e per altri viaggiatori. Ci dedicheresti 1 minuto per lasciare una recensione su *{plataforma}*?\n\n"
            "✍️ *Lascia la tua recensione qui:* 👇\n"
            "👉 {enlace_resena}\n\n"
            "Grazie di cuore per aver viaggiato con noi e a presto in Galizia! 💙🚌✨\n"
            "— *{empresa}*"
        )
    },
    "cancellation_notice": {
        "es": (
            "👋 Hola *{nombre}*,\n\n"
            "Te contactamos desde *{empresa}* respecto a tu reserva para la excursión *{tour}* de {fecha_salida}.\n\n"
            "ℹ️ *Aviso Importante:*\n"
            "Lamentamos comunicarte que, debido a *{motivo}*, no será posible operar esta salida.\n\n"
            "Por favor, responde directamente a este WhatsApp para gestionar tu alternativa preferida:\n"
            "1️⃣ *Reubicación* en otra de nuestras salidas disponibles.\n"
            "2️⃣ *Reembolso íntegro* inmediato del importe de tu reserva.\n\n"
            "Sentimos mucho las molestias y quedamos a tu entera disposición.\n\n"
            "— *Equipo de {empresa}*"
        ),
        "en": (
            "👋 Hello *{nombre}*,\n\n"
            "We are contacting you from *{empresa}* regarding your booking for the *{tour}* excursion on {fecha_salida}.\n\n"
            "ℹ️ *Important Notice:*\n"
            "We regret to inform you that, due to *{motivo}*, this tour departure cannot operate.\n\n"
            "Please reply directly to this WhatsApp message to choose your preferred option:\n"
            "1️⃣ *Reschedule* to another available tour date or route.\n"
            "2️⃣ *Full and immediate refund* of your booking.\n\n"
            "We sincerely apologize for any inconvenience caused.\n\n"
            "— *{empresa} Team*"
        ),
        "fr": (
            "👋 Bonjour *{nombre}*,\n\n"
            "Nous vous contactons de la part de *{empresa}* au sujet de votre réservation pour l'excursion *{tour}* du {fecha_salida}.\n\n"
            "ℹ️ *Avis Important :*\n"
            "Nous avons le regret de vous informer que, pour *{motivo}*, cette sortie ne pourra pas avoir lieu.\n\n"
            "Merci de répondre directement à ce message pour nous indiquer votre choix :\n"
            "1️⃣ *Report* sur une autre de nos excursions disponibles.\n"
            "2️⃣ *Remboursement intégral* et immédiat de votre réservation.\n\n"
            "Veuillez nous excuser pour ce désagrément.\n\n"
            "— *L'équipe {empresa}*"
        ),
        "de": (
            "👋 Hallo *{nombre}*,\n\n"
            "wir kontaktieren Sie von *{empresa}* bezüglich Ihrer Buchung für *{tour}* am {fecha_salida}.\n\n"
            "ℹ️ *Wichtige Mitteilung:*\n"
            "Leider müssen wir Ihnen mitteilen, dass diese Tour aufgrund von *{motivo}* nicht stattfinden kann.\n\n"
            "Bitte antworten Sie direkt auf diese Nachricht, um Ihre Option zu wählen:\n"
            "1️⃣ *Umbuchung* auf einen anderen verfügbaren Ausflug.\n"
            "2️⃣ *Vollständige Rückerstattung* Ihres Buchungsbetrags.\n\n"
            "Wir bitten die Unannehmlichkeiten vielmals zu entschuldigen.\n\n"
            "— *{empresa}*"
        ),
        "pt": (
            "👋 Olá *{nombre}*,\n\n"
            "Contactamos da *{empresa}* referente à sua reserva para a excursão *{tour}* de {fecha_salida}.\n\n"
            "ℹ️ *Aviso Importante:*\n"
            "Lamentamos informar que, devido a *{motivo}*, esta saída não poderá realizar-se.\n\n"
            "Por favor, responda diretamente a esta mensagem para indicar a sua preferência:\n"
            "1️⃣ *Reagendamento* para outra das nossas excursões disponíveis.\n"
            "2️⃣ *Reembolso integral* do valor da sua reserva.\n\n"
            "Pedimos sinceras desculpas pelo transtorno.\n\n"
            "— *{empresa}*"
        ),
        "it": (
            "👋 Ciao *{nombre}*,\n\n"
            "Ti contattiamo da *{empresa}* riguardo alla tua prenotazione per l'escursione *{tour}* del {fecha_salida}.\n\n"
            "ℹ️ *Avviso Importante:*\n"
            "Siamo spiacenti di comunicarti che, a causa di *{motivo}*, questa partenza non potrà essere effettuata.\n\n"
            "Ti preghiamo di rispondere direttamente a questo messaggio per gestire l'opzione che preferisci:\n"
            "1️⃣ *Riprogrammazione* su un'altra delle nostre escursioni.\n"
            "2️⃣ *Rimborso integrale* immediato della prenotazione.\n\n"
            "Ci scusiamo per il disagio.\n\n"
            "— *{empresa}*"
        )
    }
}


class TemplateManager:
    def __init__(self):
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        result = {
            "departure_pickup": DEFAULT_SYSTEM_TEMPLATES["departure_pickup"].copy(),
            "schedule_change": DEFAULT_SYSTEM_TEMPLATES["schedule_change"].copy(),
            "cancellation_notice": DEFAULT_SYSTEM_TEMPLATES["cancellation_notice"].copy(),
            "review_request": DEFAULT_SYSTEM_TEMPLATES["review_request"].copy(),
            "custom_templates": []
        }

        if TEMPLATES_FILE.exists():
            try:
                with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        # Merge departure_pickup / schedule_change / cancellation_notice / review_request
                        for key in ["departure_pickup", "schedule_change", "cancellation_notice", "review_request"]:
                            if key in loaded and isinstance(loaded[key], dict):
                                result[key].update(loaded[key])
                        if "custom_templates" in loaded and isinstance(loaded["custom_templates"], list):
                            result["custom_templates"] = loaded["custom_templates"]
            except Exception as e:
                print("Error loading custom_templates.json:", e)

        return result

    def _save_to_disk(self) -> bool:
        try:
            with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print("Error saving templates to disk:", e)
            return False

    def get_all(self) -> Dict[str, Any]:
        return self.data

    def save_base_templates(self, templates_dict: Dict[str, Any]) -> bool:
        for key in ["departure_pickup", "schedule_change", "review_request"]:
            if key in templates_dict:
                self.data[key] = templates_dict[key]
        return self._save_to_disk()

    # Custom dynamic templates CRUD
    def get_custom_templates(self) -> List[Dict[str, Any]]:
        return self.data.get("custom_templates", [])

    def add_custom_template(self, tpl: Dict[str, Any]) -> Dict[str, Any]:
        tpl_id = tpl.get("id") or f"tpl_{uuid.uuid4().hex[:8]}"
        new_entry = {
            "id": tpl_id,
            "title": tpl.get("title", "Plantilla Personalizada").strip(),
            "tour_id": tpl.get("tour_id", "all"),
            "tour_name": tpl.get("tour_name", "Todos los Tours"),
            "language": tpl.get("language", "es").lower(),
            "category": tpl.get("category", "departure_pickup"),
            "content": tpl.get("content", "").strip()
        }

        # Check if updating existing
        existing_idx = next((i for i, t in enumerate(self.data["custom_templates"]) if t.get("id") == tpl_id), None)
        if existing_idx is not None:
            self.data["custom_templates"][existing_idx] = new_entry
        else:
            self.data["custom_templates"].append(new_entry)

        self._save_to_disk()
        return new_entry

    def delete_custom_template(self, tpl_id: str) -> bool:
        initial_len = len(self.data.get("custom_templates", []))
        self.data["custom_templates"] = [t for t in self.data.get("custom_templates", []) if t.get("id") != tpl_id]
        if len(self.data["custom_templates"]) != initial_len:
            return self._save_to_disk()
        return False

    def find_best_template(
        self,
        tour_id: Optional[str] = None,
        tour_name: Optional[str] = None,
        lang_code: str = "es",
        category: str = "departure_pickup"
    ) -> Optional[str]:
        lang_code = lang_code.lower()
        customs = self.data.get("custom_templates", [])

        # 1. Exact tour_id + language + category
        if tour_id and tour_id != "all":
            for t in customs:
                if t.get("tour_id") == tour_id and t.get("language") == lang_code and t.get("category") == category:
                    return t.get("content")

        # 2. Fuzzy tour_name + language + category
        if tour_name and customs:
            t_name_lower = tour_name.lower()
            for t in customs:
                tpl_tour = (t.get("tour_name") or "").lower()
                if tpl_tour != "todos los tours" and tpl_tour in t_name_lower and t.get("language") == lang_code and t.get("category") == category:
                    return t.get("content")

        # 3. Global custom for language + category (tour_id == 'all')
        for t in customs:
            if t.get("tour_id") == "all" and t.get("language") == lang_code and t.get("category") == category:
                return t.get("content")

        # 4. Fallback to default base templates
        group = self.data.get(category) or self.data.get("departure_pickup", {})
        return group.get(lang_code, group.get("en", group.get("es", "")))

    def render(
        self,
        client_name: str,
        tour_name: str,
        tour_id: Optional[str] = None,
        new_time: str = "",
        pickup_stop: str = "",
        reason: str = "",
        lang_code: str = "es",
        company_name: str = "Tour Galicia",
        template_type: str = "departure_pickup",
        review_link: str = "",
        platform_name: str = "Google",
        date_label: str = "mañana"
    ) -> str:
        template = self.find_best_template(
            tour_id=tour_id,
            tour_name=tour_name,
            lang_code=lang_code,
            category=template_type
        )

        if not template:
            template = (
                "👋 Hola *{nombre}*,\n\n"
                "Confirmamos tu excursión *{tour}* con salida a las *{hora}* en *{parada}*.\n"
                "🎧 Audioguía: {audioguia}\n\n"
                "— *{empresa}*"
            )

        audioguide = AUDIOGUIDE_LINKS.get(lang_code, AUDIOGUIDE_LINKS.get("en", "https://audioguide.tourgalicia.es/es"))
        rev_link = review_link or REVIEW_LINKS.get("default")

        rendered = template
        replacements = {
            "{nombre}": client_name or "Estimado/a cliente",
            "{client_name}": client_name or "Estimado/a cliente",
            "{hora}": new_time or "09:00",
            "{new_time}": new_time or "09:00",
            "{parada}": pickup_stop or "Punto de salida habitual",
            "{pickup_stop}": pickup_stop or "Punto de salida habitual",
            "{tour}": tour_name,
            "{tour_name}": tour_name,
            "{motivo}": reason or "motivos de organización",
            "{reason}": reason or "motivos de organización",
            "{empresa}": company_name,
            "{company_name}": company_name,
            "{audioguia}": audioguide,
            "{audioguide}": audioguide,
            "{enlace_resena}": rev_link,
            "{review_link}": rev_link,
            "{plataforma}": platform_name or "Google",
            "{platform}": platform_name or "Google",
            "{fecha_salida}": date_label or "mañana",
            "{date_label}": date_label or "mañana"
        }

        for var, val in replacements.items():
            rendered = rendered.replace(var, str(val))

        return rendered


template_mgr = TemplateManager()
