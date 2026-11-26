import requests

print("BINANCE RADAR - NETWORK TEST")

try:
    ip = requests.get(
        "https://api.ipify.org?format=json",
        timeout=15
    )
    print("GITHUB SERVER IP:", ip.text)
except Exception as e:
    print("IP ERROR:", e)

urls = {
    "FUTURES": "https://fapi.binance.com/fapi/v1/ping",
    "SPOT": "https://api.binance.com/api/v3/ping"
}

for name, url in urls.items():
    try:
        r = requests.get(url, timeout=15)
        print(name, "HTTP:", r.status_code)
        print("RESPONSE:", r.text[:1000])
    except Exception as e:
        print(name, "ERROR:", e)

print("TEST FINISHED")