import json
import time
from datetime import datetime
import requests
import csv

# List of Taiwan top 20 ETF stock codes (example codes)
ETF_CODES = [
    "0050", "0056", "006208", "00692", "00713", "006203", "00850", "0061", "006201", "006204",
    "00679B", "00720", "00752", "00878", "00646", "008201", "00757", "00757B", "00713L", "00715"
]

API_URL = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{}.tw"


def fetch_price(code):
    url = API_URL.format(code)
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        msg_array = data.get("msgArray", [])
        if msg_array:
            price = msg_array[0].get("z")
            timestamp = msg_array[0].get("tlong")
            return price, timestamp
    except Exception as e:
        print(f"Error fetching {code}: {e}")
    return None, None


def fetch_all():
    results = []
    for code in ETF_CODES:
        price, timestamp = fetch_price(code)
        if price:
            results.append({
                "code": code,
                "price": price,
                "timestamp": datetime.fromtimestamp(int(timestamp)/1000).isoformat() if timestamp else ''
            })
    return results


def save_csv(data, filename="etf_prices.csv"):
    fieldnames = ["code", "price", "timestamp"]
    with open(filename, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for row in data:
            writer.writerow(row)


def main(interval=60):
    while True:
        data = fetch_all()
        if data:
            save_csv(data)
            print(f"Fetched {len(data)} records at {datetime.now()}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
