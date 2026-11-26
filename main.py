
import requests

BASE = "https://data-api.binance.vision"

print("BINANCE RADAR 2.0")
print("MARKET DATA TEST")

def check_price(symbol):
    url = BASE + "/api/v3/ticker/price"
    r = requests.get(
        url,
        params={"symbol": symbol},
        timeout=15
    )
    print(symbol, "HTTP:", r.status_code)
    print(r.text[:300])

def check_klines():
    url = BASE + "/api/v3/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "5m",
        "limit": 5
    }

    r = requests.get(url, params=params, timeout=15)
    print("\nBTCUSDT CANDLES")
    print("HTTP:", r.status_code)
    print(r.text[:1500])

for symbol in ["BTCUSDT", "ETHUSDT", "BNBUSDT"]:
    try:
        check_price(symbol)
    except Exception as e:
        print(symbol, "ERROR:", e)

try:
    check_klines()
except Exception as e:
    print("KLINES ERROR:", e)

print("\nTEST FINISHED")
