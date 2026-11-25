import requests
import time

BASE_URL = "https://fapi.binance.com"

def check_connection():
try:
response = requests.get(
BASE_URL + "/fapi/v1/ping",
timeout=10
)
response.raise_for_status()
print("BINANCE CONNECTION: OK")
return True

except requests.RequestException as error:
    print("CONNECTION ERROR:", error)
    return False
def get_server_time():
response = requests.get(
BASE_URL + "/fapi/v1/time",
timeout=10
)
response.raise_for_status()
return response.json()["serverTime"]

if name == "main":
print("=" * 40)
print("BINANCE MARKET RADAR 2.0")
print("=" * 40)
if check_connection():
    print("Binance server time:", get_server_time())
    print("System initialized successfully.")
