import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

THRESHOLD = 1.5

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

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )

        r.raise_for_status()

        data = r.json()

        meta = data["chart"]["result"][0]["meta"]

        current = meta["regularMarketPrice"]
        previous_close = meta["previousClose"]

        change = (current / previous_close - 1) * 100

        proxy_change += weight * change

        print(
            f"{name}: "
            f"current={current}, "
            f"previous={previous_close}, "
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

print(f"Proxy för PLUS Småbolag: {proxy_change:.2f}%")

if proxy_change > THRESHOLD:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Småbolagslarm",
            "message": (
                f"PLUS Småbolag-proxy är upp "
                f"{proxy_change:.2f}% "
                f"kl {sweden_time.strftime('%H:%M')}. "
                f"\nLarmnivå {THRESHOLD:.1f}% passerad."
            ),
        },
        timeout=20,
    )

    print("Notification sent")

else:
    print("No alert")
