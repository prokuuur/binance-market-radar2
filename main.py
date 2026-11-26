
import requests

print("BINANCE RADAR TEST")
print("=" * 35)

tests = {
    "FUTURES PING": "https://fapi.binance.com/fapi/v1/ping",
    "FUTURES TIME": "https://fapi.binance.com/fapi/v1/time",
    "SPOT PING": "https://api.binance.com/api/v3/ping",
}

for name, url in tests.items():
    try:
        response = requests.get(url, timeout=15)
        print(f"\n{name}")
        print("HTTP:", response.status_code)
        print("RESPONSE:", response.text[:500])
    except Exception as error:
        print(f"\n{name} ERROR:", error)

print("\nTEST FINISHED")
