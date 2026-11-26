
import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# BINANCE MARKET RADAR 2.0
# ==========================================

BASE_URL = "https://data-api.binance.vision"

TIMEFRAME = "15m"
KLINE_LIMIT = 150
MAX_WORKERS = 10

MIN_QUOTE_VOLUME = 5_000_000
SCAN_INTERVAL = 60

EXCLUDED_BASES = {
    "USDT", "USDC", "BUSD", "FDUSD", "TUSD",
    "USDP", "DAI", "EUR", "TRY", "BRL",
    "GBP", "AUD", "BIDR", "IDRT"
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)


def get_json(endpoint, params=None):
    response = requests.get(
        BASE_URL + endpoint,
        params=params,
        timeout=15
    )
    response.raise_for_status()
    return response.json()


def get_symbols():
    data = get_json("/api/v3/exchangeInfo")

    symbols = []

    for item in data["symbols"]:
        if (
            item["status"] == "TRADING"
            and item["quoteAsset"] == "USDT"
            and item["baseAsset"] not in EXCLUDED_BASES
            and item["isSpotTradingAllowed"]
        ):
            symbols.append(item["symbol"])

    return symbols


def get_market_data():
    data = get_json("/api/v3/ticker/24hr")

    markets = {}

    for item in data:
        symbol = item["symbol"]

        if symbol.endswith("USDT"):
            markets[symbol] = {
                "price": float(item["lastPrice"]),
                "volume": float(item["quoteVolume"]),
                "change": float(item["priceChangePercent"])
            }

    return markets


def get_klines(symbol):
    data = get_json(
        "/api/v3/klines",
        {
            "symbol": symbol,
            "interval": TIMEFRAME,
            "limit": KLINE_LIMIT
        }
    )

    closes = [float(candle[4]) for candle in data]
    volumes = [float(candle[5]) for candle in data]

    return closes, volumes


def ema(values, period):
    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    result = sum(values[:period]) / period

    for value in values[period:]:
        result = (
            value * multiplier
            + result * (1 - multiplier)
        )

    return result


def calculate_rsi(values, period=14):
    if len(values) <= period:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):
        difference = values[i] - values[i - 1]
        gains.append(max(difference, 0))
        losses.append(max(-difference, 0))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (
            avg_gain * (period - 1) + gains[i]
        ) / period

        avg_loss = (
            avg_loss * (period - 1) + losses[i]
        ) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss

    return 100 - (100 / (1 + rs))


def calculate_macd(values):
    if len(values) < 35:
        return None, None

    fast = ema(values, 12)
    slow = ema(values, 26)

    if fast is None or slow is None:
        return None, None

    return fast - slow, "calculated"


def analyze_symbol(symbol, market):
    try:
        closes, volumes = get_klines(symbol)

        if len(closes) < 60:
            return None

        current_price = closes[-1]

        ema20 = ema(closes, 20)
        ema50 = ema(closes, 50)
        rsi = calculate_rsi(closes)

        macd, _ = calculate_macd(closes)

        if None in (ema20, ema50, rsi, macd):
            return None

        signal = None
        score = 0

        if (
            current_price > ema20 > ema50
            and 50 < rsi < 70
            and macd > 0
        ):
            signal = "LONG"
            score = 3

        elif (
            current_price < ema20 < ema50
            and 30 < rsi < 50
            and macd < 0
        ):
            signal = "SHORT"
            score = 3

        if signal is None:
            return None

        return {
            "symbol": symbol,
            "signal": signal,
            "price": current_price,
            "rsi": rsi,
            "ema20": ema20,
            "ema50": ema50,
            "macd": macd,
            "volume": market["volume"],
            "change": market["change"],
            "score": score
        }

    except Exception as error:
        logging.warning("%s: %s", symbol, error)
        return None


def main():
    print("=" * 50)
    print("       BINANCE MARKET RADAR 2.0")
    print("=" * 50)

    while True:
        try:
            print("\nLoading Binance market...")

            symbols = get_symbols()
            markets = get_market_data()

            symbols = [
                symbol for symbol in symbols
                if symbol in markets
                and markets[symbol]["volume"] >= MIN_QUOTE_VOLUME
            ]

            print("Pairs to scan:", len(symbols))

            results = []

            with ThreadPoolExecutor(
                max_workers=MAX_WORKERS
            ) as executor:

                futures = {
                    executor.submit(
                        analyze_symbol,
                        symbol,
                        markets[symbol]
                    ): symbol
                    for symbol in symbols
                }

                for future in as_completed(futures):
                    result = future.result()

                    if result:
                        results.append(result)

            results.sort(
                key=lambda x: x["score"],
                reverse=True
            )

            print("\n========== SIGNALS ==========")

            if not results:
                print("No signals found.")

            for item in results:
                print(
                    f"\n{item['symbol']} | {item['signal']}"
                    f"\nPrice: {item['price']}"
                    f"\nRSI: {item['rsi']:.2f}"
                    f"\nEMA20: {item['ema20']:.6f}"
                    f"\nEMA50: {item['ema50']:.6f}"
                    f"\nMACD: {item['macd']:.6f}"
                    f"\n24h volume: {item['volume']:,.0f} USDT"
                    f"\n24h change: {item['change']:.2f}%"
                    "\n-----------------------------"
                )

            print("\nScan completed.")

        except Exception as error:
            logging.error("Main error: %s", error)

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
