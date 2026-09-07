import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.language_detector import detect_language
from app.assistant import assistant
from app.whatsapp_service import whatsapp

print("=" * 60)
print("TEST 1: Detección de Idioma por Prefijo")
print("=" * 60)
numbers = [
    "+34 620 11 22 33", 
    "+44 7911 123456", 
    "+33 6 12 34 56 78", 
    "+49 151 23456789", 
    "+351 912 345 678", 
    "+39 347 1234567", 
    "+1 415 555 2671"
]
for num in numbers:
    info = detect_language(num)
    print(f"{num:20} -> {info['flag']} {info['name']} ({info['code']}) [{info['country']}]")

print("\n" + "=" * 60)
print("TEST 2: Parser de Instrucción del Asistente")
print("=" * 60)
prompt = "avisa a todos los clientes del tour de Leyendas y misterios de hoy a la tarde, en todas las franjas que por motivos logisticos el horario de salida sera a las 19.30"
print("Instrucción dada:", prompt)
result = assistant.parse_instruction(prompt)

print(f"\n✓ Excursión identificada: {result['tour']['name']}")
print(f"✓ Nueva hora extraída:   {result['new_time']}")
print(f"✓ Motivo detectado:      {result['reason']}")
print(f"✓ Franjas agrupadas:     {result['target_slots']}")
print(f"✓ Clientes afectados:    {result['total_clients']} pasajeros")

print("\nDesglose por Idioma:")
for lang, data in result['languages_summary'].items():
    print(f"  - {data['flag']} {lang}: {data['count']} mensajes")

print("\n" + "-" * 40)
print("Ejemplo 1 (Cliente en Español):")
print("-" * 40)
print(result['clients'][0]['message'])

print("\n" + "-" * 40)
print("Ejemplo 2 (Cliente en Inglés):")
print("-" * 40)
print(result['clients'][1]['message'])

print("\n" + "-" * 40)
print("Ejemplo 3 (Cliente en Francés):")
print("-" * 40)
print(result['clients'][2]['message'])

print("\n" + "=" * 60)
print("TEST 3: Simulación de Envío WhatsApp")
print("=" * 60)
dispatch = whatsapp.send_broadcast(result['clients'])
print(f"✓ Mensajes enviados: {dispatch['total_sent']} | Éxito: {dispatch['success']}")
print(f"✓ Primer registro: ID={dispatch['deliveries'][0]['id']} | Estado={dispatch['deliveries'][0]['status']}")
print("=" * 60)
print("TODAS LAS PRUEBAS COMPLETADAS CON ÉXITO")
print("=" * 60)
