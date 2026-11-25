import requests

URL = "https://fapi.binance.com"

def main():
    data = requests.get(URL + "/fapi/v1/ticker/24hr").json()
    coins = [x for x in data if x["symbol"].endswith("USDT")]

    coins.sort(key=lambda x: abs(float(x["priceChangePercent"])), reverse=True)

    print("BINANCE MARKET RADAR 2.0")
    for coin in coins[:20]:
        print(coin["symbol"], coin["priceChangePercent"] + "%")

if __name__ == "__main__":
    main()