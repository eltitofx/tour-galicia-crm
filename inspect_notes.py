import urllib.request
import json
import time
import html
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

api_key = 'NBzHliwdT2GZutt9jhUHLA8gGzAHYK9L'
url = 'https://app.turitop.com/v1/booking/getbookings'
now = int(time.time())
payload = {'data': {'filter': {'event_date_from': now - (10 * 86400), 'event_date_to': now + (30 * 86400)}}}
req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'})

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode('utf-8'))
    bookings = data['data']['bookings']
    print(f'Total bookings: {len(bookings)}')
    for i, b in enumerate(bookings[:20]):
        client = b.get('client_data') or {}
        c_name = html.unescape(client.get('name', ''))
        c_comm = html.unescape(str(client.get('comments') or ''))
        b_notes = html.unescape(str(b.get('notes') or ''))
        pickup = html.unescape(str(b.get('pickup_point') or ''))
        hotel = html.unescape(str(b.get('hotel_name') or ''))
        print(f"[{b.get('short_id')}] Tour: {b.get('product_name')} | Client: {c_name} | Comments: '{c_comm}' | Notes: '{b_notes}' | Pickup: '{pickup}' | Hotel: '{hotel}'")
