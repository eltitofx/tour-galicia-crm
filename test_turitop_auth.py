import urllib.request
import urllib.error
import json

short_id = "T955"
secret_key = "NBzHliwdT2GZutt9jhUHLA8gGzAHYK9L"

tests = [
    {
        "name": "Grant endpoint JSON body",
        "url": "https://app.turitop.com/v1/authorization/grant",
        "headers": {"Content-Type": "application/json"},
        "data": json.dumps({"short_id": short_id, "secret_key": secret_key}).encode("utf-8")
    },
    {
        "name": "Grant endpoint urlencoded",
        "url": "https://app.turitop.com/v1/authorization/grant",
        "headers": {"Content-Type": "application/x-www-form-urlencoded"},
        "data": f"short_id={short_id}&secret_key={secret_key}".encode("utf-8")
    },
    {
        "name": "Direct Bearer on /service/getservices",
        "url": "https://app.turitop.com/v1/service/getservices",
        "headers": {"Authorization": f"Bearer {secret_key}", "Content-Type": "application/json"},
        "data": b"{}"
    },
    {
        "name": "Direct Bearer short_id:secret_key on /service/getservices",
        "url": "https://app.turitop.com/v1/service/getservices",
        "headers": {"Authorization": f"Bearer {short_id}:{secret_key}", "Content-Type": "application/json"},
        "data": b"{}"
    }
]

for t in tests:
    print(f"Testing: {t['name']}")
    req = urllib.request.Request(t["url"], data=t["data"], headers=t["headers"])
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            print("  STATUS:", resp.status)
            print("  BODY:", resp.read().decode("utf-8")[:300])
    except urllib.error.HTTPError as e:
        print(f"  HTTP ERROR {e.code}: {e.read().decode('utf-8')[:300]}")
    except Exception as e:
        print(f"  ERROR: {e}")
