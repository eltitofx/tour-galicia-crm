from typing import Dict, Any

TEMPLATES = {
    "schedule_change": {
        "es": (
            "👋 Hola *{client_name}*,\n\n"
            "Te contactamos desde *{company_name}* referente a tu reserva para la excursión *{tour_name}* programada para hoy.\n\n"
            "ℹ️ *Aviso Importante de Horario:*\n"
            "Por {reason}, hemos unificado la salida del grupo. Tu nuevo horario de salida será a las *{new_time}*.\n\n"
            "📍 *Punto de encuentro / Parada:* {pickup_stop}\n"
            "⏰ *Nueva hora de encuentro:* *{new_time}*\n"
            "⚠️ _Rogamos estar presentes con 10 minutos de antelación._\n\n"
            "Si tienes cualquier duda, puedes responder directamente a este mensaje.\n\n"
            "¡Muchas gracias por tu colaboración y nos vemos pronto! 🚌✨\n"
            "— *Equipo de {company_name}*"
        ),
        "en": (
            "👋 Hello *{client_name}*,\n\n"
            "We are contacting you from *{company_name}* regarding your booking for the *{tour_name}* excursion scheduled for today.\n\n"
            "ℹ️ *Important Schedule Update:*\n"
            "Due to {reason_en}, departures have been consolidated. Your updated departure time is now *{new_time}*.\n\n"
            "📍 *Meeting / Pick-up Point:* {pickup_stop}\n"
            "⏰ *New departure time:* *{new_time}*\n"
            "⚠️ _Please arrive 10 minutes prior to departure._\n\n"
            "If you have any questions, feel free to reply directly to this WhatsApp message.\n\n"
            "Thank you very much for your understanding, see you soon! 🚌✨\n"
            "— *{company_name} Team*"
        ),
        "fr": (
            "👋 Bonjour *{client_name}*,\n\n"
            "Nous vous contactons de la part de *{company_name}* concernant votre réservation pour l'excursion *{tour_name}* prévue aujourd'hui.\n\n"
            "ℹ️ *Mise à jour importante de l'horaire :*\n"
            "Pour {reason_fr}, nous avons regroupé les départs. Votre nouvel horaire de départ est fixé à *{new_time}*.\n\n"
            "📍 *Point de rendez-vous / Prise en charge :* {pickup_stop}\n"
            "⏰ *Nouvelle heure de départ :* *{new_time}*\n"
            "⚠️ _Merci de vous présenter 10 minutes avant._\n\n"
            "Pour toute question, vous pouvez répondre directement à ce message.\n\n"
            "Merci pour votre compréhension et à très bientôt ! 🚌✨\n"
            "— *L'équipe {company_name}*"
        ),
        "de": (
            "👋 Hallo *{client_name}*,\n\n"
            "wir kontaktieren Sie von *{company_name}* bezüglich Ihrer Buchung für den Ausflug *{tour_name}* am heutigen Tag.\n\n"
            "ℹ️ *Wichtige Fahrplanänderung:*\n"
            "Aus {reason_de} haben wir die Abfahrten zusammengelegt. Ihre neue Abfahrtszeit ist um *{new_time}* Uhr.\n\n"
            "📍 *Treffpunkt / Abholung:* {pickup_stop}\n"
            "⏰ *Neue Abfahrtszeit:* *{new_time}* Uhr\n"
            "⚠️ _Bitte seien Sie 10 Minuten vor Abfahrt vor Ort._\n\n"
            "Bei Fragen können Sie direkt auf diese Nachricht antworten.\n\n"
            "Vielen Dank für Ihr Verständnis und bis gleich! 🚌✨\n"
            "— *Ihr Team von {company_name}*"
        ),
        "pt": (
            "👋 Olá *{client_name}*,\n\n"
            "Entramos em contacto da *{company_name}* referente à sua reserva para a excursão *{tour_name}* marcada para hoje.\n\n"
            "ℹ️ *Aviso Importante de Horário:*\n"
            "Por {reason_pt}, unificámos a partida do grupo. O seu novo horário de saída será às *{new_time}*.\n\n"
            "📍 *Ponto de encontro / Paragem:* {pickup_stop}\n"
            "⏰ *Novo horário de encontro:* *{new_time}*\n"
            "⚠️ _Pedimos o favor de estar presente com 10 minutos de antecedência._\n\n"
            "Se tiver qualquer dúvida, pode responder diretamente a esta mensagem.\n\n"
            "Muito obrigado pela compreensão e até já! 🚌✨\n"
            "— *Equipa {company_name}*"
        ),
        "it": (
            "👋 Ciao *{client_name}*,\n\n"
            "Ti contattiamo da *{company_name}* in merito alla tua prenotazione per l'escursione *{tour_name}* prevista per oggi.\n\n"
            "ℹ️ *Avviso importante di orario:*\n"
            "Per {reason_it}, abbiamo accorpato le partenze del gruppo. Il nuovo orario di partenza sarà alle *{new_time}*.\n\n"
            "📍 *Punto di incontro / Fermata:* {pickup_stop}\n"
            "⏰ *Nuovo orario di partenza:* *{new_time}*\n"
            "⚠️ _Si prega di presentarsi 10 minuti prima._\n\n"
            "Per qualsiasi dubbio puoi rispondere direttamente a questo messaggio.\n\n"
            "Grazie mille per la comprensione, a presto! 🚌✨\n"
            "— *Il team di {company_name}*"
        )
    },
    "departure_reminder": {
        "es": (
            "👋 Hola *{client_name}*,\n\n"
            "Te recordamos los detalles de tu excursión *{tour_name}* con *{company_name}*:\n\n"
            "📅 *Fecha:* {date}\n"
            "📍 *Punto de recogida / Salida:* {pickup_stop}\n"
            "⏰ *Hora de recogida:* *{pickup_time}*\n"
            "⚠️ _Por favor, preséntate 10 minutos antes en el punto indicado._\n\n"
            "¡Te deseamos una maravillosa experiencia con nosotros! 🚌 Galicia te espera."
        ),
        "en": (
            "👋 Hello *{client_name}*,\n\n"
            "Here is a reminder for your upcoming *{tour_name}* excursion with *{company_name}*:\n\n"
            "📅 *Date:* {date}\n"
            "📍 *Pick-up / Meeting Point:* {pickup_stop}\n"
            "⏰ *Pick-up Time:* *{pickup_time}*\n"
            "⚠️ _Please arrive 10 minutes prior at the designated location._\n\n"
            "We wish you a fantastic experience! 🚌 Galicia awaits you."
        )
    }
}

REASON_TRANSLATIONS = {
    "motivos logísticos": {
        "es": "motivos logísticos",
        "en": "logistical reasons",
        "fr": "raisons logistiques",
        "de": "logistischen Gründen",
        "pt": "motivos logísticos",
        "it": "motivi logistici"
    },
    "motivos de tráfico": {
        "es": "motivos de tráfico y circulación",
        "en": "traffic and transit delays",
        "fr": "raisons de circulation",
        "de": "verkehrsbedingten Gründen",
        "pt": "motivos de trânsito",
        "it": "motivi di traffico"
    },
    "condiciones meteorológicas": {
        "es": "condiciones meteorológicas",
        "en": "weather conditions",
        "fr": "conditions météorologiques",
        "de": "Wetterbedingungen",
        "pt": "condições meteorológicas",
        "it": "condizioni meteorologiche"
    }
}

def translate_reason(reason_es: str, target_lang: str) -> str:
    cleaned = reason_es.strip().lower()
    for key, trans in REASON_TRANSLATIONS.items():
        if key in cleaned:
            return trans.get(target_lang, reason_es)
    # Default fallback
    if target_lang == "en":
        return f"operational adjustments ({reason_es})"
    elif target_lang == "fr":
        return f"ajustements opérationnels ({reason_es})"
    elif target_lang == "de":
        return f"betrieblichen Gründen ({reason_es})"
    elif target_lang == "pt":
        return f"motivos operacionais ({reason_es})"
    elif target_lang == "it":
        return f"motivi operativi ({reason_es})"
    return reason_es

def render_schedule_change_message(
    client_name: str,
    tour_name: str,
    new_time: str,
    pickup_stop: str,
    reason: str,
    lang_code: str,
    company_name: str = "Tour Galicia"
) -> str:
    template_group = TEMPLATES.get("schedule_change", {})
    # Fallback to English if language not supported, or Spanish if requested
    template = template_group.get(lang_code, template_group.get("en", template_group["es"]))
    
    translated_reason = translate_reason(reason, lang_code)
    
    return template.format(
        client_name=client_name or "Estimado/a cliente",
        company_name=company_name,
        tour_name=tour_name,
        new_time=new_time,
        pickup_stop=pickup_stop or "Punto de salida principal",
        reason=reason,
        reason_en=translated_reason,
        reason_fr=translated_reason,
        reason_de=translated_reason,
        reason_pt=translated_reason,
        reason_it=translated_reason
    )
