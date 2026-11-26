
import requests

BASE = "https://data-api.binance.vision"

print("BINANCE RADAR 2.0")
print("MARKET UNIVERSE TEST")

try:
    info = requests.get(
        BASE + "/api/v3/exchangeInfo",
        timeout=20
    )
    info.raise_for_status()

    symbols = [
        s["symbol"]
        for s in info.json()["symbols"]
        if s.get("status") == "TRADING"
        and s.get("quoteAsset") == "USDT"
        and s.get("isSpotTradingAllowed", False)
    ]

    print("AVAILABLE USDT PAIRS:", len(symbols))

    ticker = requests.get(
        BASE + "/api/v3/ticker/24hr",
        timeout=20
    )
    ticker.raise_for_status()

    volumes = {
        item["symbol"]: float(item["quoteVolume"])
        for item in ticker.json()
    }

    ranked = sorted(
        [s for s in symbols if s in volumes],
        key=lambda s: volumes[s],
        reverse=True
    )

    print("\nTOP 20 BY VOLUME")

    for symbol in ranked[:20]:
        print(symbol, volumes[symbol], "USDT")

except Exception as error:
    print("ERROR:", error)

print("\nTEST FINISHED")
