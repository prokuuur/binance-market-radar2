
import requests

BASE = "https://data-api.binance.vision"

# Stablecoins, fiat and tokenized stock tickers
EXCLUDED_BASES = {
    "USDT", "USDC", "BUSD", "TUSD", "FDUSD",
    "USDP", "DAI", "USDE", "USD1", "PYUSD",
    "EUR", "GBP", "AUD", "BRL", "TRY",
    "PLN", "UAH", "RUB", "ZAR", "NGN",
    "BIDR", "IDRT", "USTC", "UST",
    "AAPL", "TSLA", "NVDA", "MSFT",
    "AMZN", "GOOGL", "META", "COIN",
    "MSTR", "CRCL", "HOOD", "INTC",
    "QQQ", "SPY", "MARA", "SOUN",
    "SOXLB", "NVDAB", "SPCXB", "MMT",
    "XAUT", "PAXG", "RLUSD","SOXSB"
}

def get_crypto_universe():
    print("Loading Binance markets...")

    info = requests.get(
        BASE + "/api/v3/exchangeInfo",
        timeout=20
    )
    info.raise_for_status()

    ticker = requests.get(
        BASE + "/api/v3/ticker/24hr",
        timeout=30
    )
    ticker.raise_for_status()

    volumes = {
        item["symbol"]: float(item["quoteVolume"])
        for item in ticker.json()
    }

    markets = []

    for item in info.json()["symbols"]:
        base = item["baseAsset"]
        symbol = item["symbol"]

        if item["status"] != "TRADING":
            continue

        if item["quoteAsset"] != "USDT":
            continue

        if not item.get("isSpotTradingAllowed", False):
            continue

        if base in EXCLUDED_BASES:
            continue

        if symbol not in volumes:
            continue

        markets.append({
            "symbol": symbol,
            "volume": volumes[symbol]
        })

    markets.sort(
        key=lambda x: x["volume"],
        reverse=True
    )

    return markets


def main():
    print("\nBINANCE MARKET RADAR 2.0")
    print("=" * 40)

    try:
        markets = get_crypto_universe()

        print("CRYPTO PAIRS:", len(markets))
        print("\nTOP 30 BY VOLUME")
        print("-" * 40)

        for market in markets[:30]:
            print(
                market["symbol"],
                f'{market["volume"]:,.0f} USDT'
            )

        print("\nUNIVERSE TEST FINISHED")

    except Exception as error:
        print("ERROR:", error)


if __name__ == "__main__":
    main()
