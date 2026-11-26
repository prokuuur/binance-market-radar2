
import requests

print("BINANCE RADAR 2.0")
print("OFFICIAL API DIAGNOSTICS")
print("=" * 40)

tests = {
    "SPOT MARKET DATA ONLY":
        "https://data-api.binance.vision/api/v3/ping",

    "SPOT STANDARD":
        "https://api.binance.com/api/v3/ping",

    "FUTURES PING":
        "https://fapi.binance.com/fapi/v1/ping",

    "FUTURES TIME":
        "https://fapi.binance.com/fapi/v1/time",
}

for name, url in tests.items():
    print(f"\n{name}")

    try:
        response = requests.get(
            url,
            timeout=15,
            headers={"User-Agent": "BinanceMarketRadar/2.0"}
        )

        print("HTTP:", response.status_code)
        print("DATA:", response.text[:500])

    except Exception as error:
        print("ERROR:", str(error))

print("\nDIAGNOSTICS FINISHED")
