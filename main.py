import requests

urls = {
    "FUTURES": "https://fapi.binance.com/fapi/v1/ping",
    "SPOT": "https://api.binance.com/api/v3/ping"
}

for name, url in urls.items():
    try:
        r = requests.get(url, timeout=15)
        print(name, "HTTP", r.status_code, r.text)
    except Exception as e:
        print(name, "ERROR", str(e))