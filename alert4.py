import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

THRESHOLD = 3.0

# Svensk tid
sweden_time = datetime.now(ZoneInfo("Europe/Stockholm"))

INDEXES = {
    "large": ("^OMXSLCGI", 0.30),
    "mid": ("^OMXSMCGI", 0.50),
    "small": ("^OMXSSCGI", 0.20),
}

try:

    proxy_change = 0

    for name, (ticker, weight) in INDEXES.items():

        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/"
            f"{ticker}?range=5d&interval=1d"
        )

        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )

        r.raise_for_status()

        data = r.json()

        result = data["chart"]["result"][0]
        meta = result["meta"]

        current = meta["regularMarketPrice"]

        closes = result["indicators"]["quote"][0]["close"]
        closes = [x for x in closes if x is not None]

        if len(closes) < 3:
            raise Exception(f"För få historiska kurser för {ticker}")

        two_days_ago_close = closes[-3]

        change = (current / two_days_ago_close - 1) * 100

        proxy_change += weight * change

        print(
            f"{name}: "
            f"current={current}, "
            f"2d_close={two_days_ago_close}, "
            f"change={change:.2f}%"
        )

except Exception as e:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Börslarm fel",
            "message": f"Fel vid hämtning av indexdata: {str(e)}"
        },
        timeout=20,
    )

    raise

print(f"2-dagars småbolagsproxy: {proxy_change:.2f}%")

if proxy_change > THRESHOLD:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Småbolag 2-dagarslarm",
            "message": (
                f"PLUS Småbolag-proxy är upp "
                f"{proxy_change:.2f}% "
                f"sedan stängningen för två handelsdagar sedan. "
                f"Kl {sweden_time.strftime('%H:%M')}. "
                f"\nLarmnivå {THRESHOLD:.1f}% passerad."
            ),
        },
        timeout=20,
    )

    print("Notification sent")

else:
    print("No alert")
