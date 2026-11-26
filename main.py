
import requests
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# BINANCE MARKET RADAR 2.0
# SIGNAL ENGINE 2.0
# ==========================================

BASE_URL = "https://data-api.binance.vision"

TIMEFRAME = "15m"
KLINE_LIMIT = 150
MAX_WORKERS = 10
TOP_SIGNALS = 10

MIN_QUOTE_VOLUME = 5_000_000
MIN_SCORE = 65
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

    return [
        item["symbol"]
        for item in data["symbols"]
        if item["status"] == "TRADING"
        and item["quoteAsset"] == "USDT"
        and item["baseAsset"] not in EXCLUDED_BASES
        and item["isSpotTradingAllowed"]
    ]


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

    # Используем только закрытые свечи
    data = data[:-1]

    highs = [float(x[2]) for x in data]
    lows = [float(x[3]) for x in data]
    closes = [float(x[4]) for x in data]
    volumes = [float(x[5]) for x in data]

    return highs, lows, closes, volumes


def ema_series(values, period):
    if len(values) < period:
        return []

    multiplier = 2 / (period + 1)

    result = [
        None
    ] * (period - 1)

    current = sum(values[:period]) / period
    result.append(current)

    for value in values[period:]:
        current = (
            value * multiplier
            + current * (1 - multiplier)
        )
        result.append(current)

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
    fast = ema_series(values, 12)
    slow = ema_series(values, 26)

    if not fast or not slow:
        return None, None

    macd_values = []

    for f, s in zip(fast, slow):
        if f is not None and s is not None:
            macd_values.append(f - s)

    signal_values = ema_series(macd_values, 9)

    if not signal_values or signal_values[-1] is None:
        return None, None

    macd = macd_values[-1]
    signal = signal_values[-1]

    return macd, macd - signal


def calculate_atr(highs, lows, closes, period=14):
    if len(closes) <= period:
        return None

    true_ranges = []

    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        )
        true_ranges.append(tr)

    atr = sum(true_ranges[:period]) / period

    for value in true_ranges[period:]:
        atr = (
            atr * (period - 1) + value
        ) / period

    return atr


def analyze_symbol(symbol, market):
    try:
        highs, lows, closes, volumes = get_klines(symbol)

        if len(closes) < 60:
            return None

        price = closes[-1]

        ema20_values = ema_series(closes, 20)
        ema50_values = ema_series(closes, 50)

        ema20 = ema20_values[-1]
        ema50 = ema50_values[-1]

        rsi = calculate_rsi(closes)
        macd, histogram = calculate_macd(closes)
        atr = calculate_atr(highs, lows, closes)

        if any(
            x is None
            for x in (ema20, ema50, rsi, macd, histogram, atr)
        ):
            return None

        if price <= 0:
            return None

        atr_percent = atr / price * 100

        avg_volume = sum(volumes[-21:-1]) / 20

        if avg_volume <= 0:
            return None

        volume_ratio = volumes[-1] / avg_volume

        ema_slope = (
            ema20_values[-1] - ema20_values[-6]
        ) / ema20_values[-6] * 100

        directions = []

        if price > ema20 > ema50:
            directions.append("LONG")

        if price < ema20 < ema50:
            directions.append("SHORT")

        for direction in directions:
            score = 0
            reasons = []

            if direction == "LONG":
                if price > ema20 > ema50:
                    score += 25
                    reasons.append("EMA trend bullish")

                if 50 < rsi < 70:
                    score += 20
                    reasons.append("RSI bullish")

                if macd > 0 and histogram > 0:
                    score += 20
                    reasons.append("MACD bullish")

                if price > ema20:
                    score += 10
                    reasons.append("Price above EMA20")

                if ema_slope > 0:
                    score += 10
                    reasons.append("EMA20 rising")

            else:
                if price < ema20 < ema50:
                    score += 25
                    reasons.append("EMA trend bearish")

                if 30 < rsi < 50:
                    score += 20
                    reasons.append("RSI bearish")

                if macd < 0 and histogram < 0:
                    score += 20
                    reasons.append("MACD bearish")

                if price < ema20:
                    score += 10
                    reasons.append("Price below EMA20")

                if ema_slope < 0:
                    score += 10
                    reasons.append("EMA20 falling")

            if volume_ratio >= 1.2:
                score += 15
                reasons.append("Volume confirmed")

            if score < MIN_SCORE:
                continue

            rating = (
                "STRONG" if score >= 80
                else "CANDIDATE"
            )

            return {
                "symbol": symbol,
                "signal": direction,
                "rating": rating,
                "score": score,
                "price": price,
                "rsi": rsi,
                "ema20": ema20,
                "ema50": ema50,
                "macd": macd,
                "histogram": histogram,
                "atr": atr,
                "atr_percent": atr_percent,
                "volume_ratio": volume_ratio,
                "volume": market["volume"],
                "change": market["change"],
                "reasons": reasons
            }

        return None

    except Exception as error:
        logging.warning("%s: %s", symbol, error)
        return None


def print_signal(item):
    print(
        f"\n{item['symbol']} | {item['signal']}"
        f"\nRating: {item['rating']}"
        f"\nScore: {item['score']}/100"
        f"\nPrice: {item['price']}"
        f"\nRSI: {item['rsi']:.2f}"
        f"\nEMA20: {item['ema20']:.8f}"
        f"\nEMA50: {item['ema50']:.8f}"
        f"\nMACD: {item['macd']:.8f}"
        f"\nMACD histogram: {item['histogram']:.8f}"
        f"\nATR: {item['atr_percent']:.2f}%"
        f"\nVolume ratio: {item['volume_ratio']:.2f}x"
        f"\n24h volume: {item['volume']:,.0f} USDT"
        f"\n24h change: {item['change']:.2f}%"
        f"\nReasons: {', '.join(item['reasons'])}"
        "\n--------------------------------"
    )


def main():
    print("=" * 50)
    print("       BINANCE MARKET RADAR 2.0")
    print("       SIGNAL ENGINE 2.0")
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

            print("\n========== TOP SIGNALS ==========")

            if not results:
                print("No qualified signals found.")

            for item in results[:TOP_SIGNALS]:
                print_signal(item)

            print(
                f"\nScan completed. "
                f"Qualified signals: {len(results)}"
            )

        except Exception as error:
            logging.error("Main error: %s", error)

        time.sleep(SCAN_INTERVAL)


if __name__ == "__main__":
    main()
