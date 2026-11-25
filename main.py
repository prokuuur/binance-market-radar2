import requests

BASE_URL = "https://fapi.binance.com"

def main():
print("=" * 35)
print("BINANCE MARKET RADAR 2.0")
print("=" * 35)

try:
    response = requests.get(
        BASE_URL + "/fapi/v1/ping",
        timeout=10
    )
    response.raise_for_status()

    server = requests.get(
        BASE_URL + "/fapi/v1/time",
        timeout=10
    )
    server.raise_for_status()

    print("BINANCE CONNECTION: OK")
    print("SERVER TIME:", server.json()["serverTime"])
    print("SYSTEM INITIALIZED SUCCESSFULLY")

except requests.RequestException as error:
    print("CONNECTION ERROR:", error)
if name == "main":
main()
