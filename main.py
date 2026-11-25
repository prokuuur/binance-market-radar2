import requests

URL = "https://fapi.binance.com"

def main():
    print("BINANCE MARKET RADAR 2.0")

    try:
        r = requests.get(URL + "/fapi/v1/ping", timeout=10)
        r.raise_for_status()

        t = requests.get(URL + "/fapi/v1/time", timeout=10)
        t.raise_for_status()

        print("BINANCE: CONNECTED")
        print("SERVER TIME:", t.json()["serverTime"])

    except requests.RequestException as e:
        print("ERROR:", e)

if __name__ == "__main__":
    main()