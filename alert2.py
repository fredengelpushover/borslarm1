import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

THRESHOLD = 1.4

# Svensk tid
sweden_time = datetime.now(ZoneInfo("Europe/Stockholm"))

# Hämta OMXSPI med historik
url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EOMXSPI?range=5d&interval=1d"

try:
    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )

    r.raise_for_status()

    if not r.text.strip():
        raise Exception("Tomt svar från Yahoo")

    data = r.json()

    result = data["chart"]["result"][0]
    meta = result["meta"]

    current = meta["regularMarketPrice"]

    closes = result["indicators"]["quote"][0]["close"]
    closes = [x for x in closes if x is not None]

    if len(closes) < 3:
        raise Exception("För få historiska kurser")

    two_days_ago_close = closes[-3]

except Exception as e:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Börslarm fel",
            "message": f"Fel vid hämtning av OMXSPI: {str(e)}"
        },
        timeout=20,
    )

    raise

two_day_change = (current / two_days_ago_close - 1) * 100

print(f"Current: {current}")
print(f"Two days ago close: {two_days_ago_close}")
print(f"2-day change: {two_day_change:.2f}%")

if two_day_change > THRESHOLD:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Tvådagarsutveckling: (sälj kl10)",
            "message": (
                f"2d OMXSPI är upp {two_day_change:.2f}% "
                #f"sedan stängning för två handelsdagar sedan. "
                #f"Kl {sweden_time.strftime('%H:%M')}. "
                f"(gräns {THRESHOLD:.1f}%)"
            ),
        },
        timeout=20,
    )

    print("Notification sent")

else:
    print("No alert")
