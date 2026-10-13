import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

THRESHOLD = -111.5

# Svensk tid
sweden_time = datetime.now(ZoneInfo("Europe/Stockholm"))

# Endast runt 11:30-11:40
#if sweden_time.hour != 11:
#    print("Inte 11-timmen")
#    raise SystemExit

# Hämta OMXSPI
url = "https://query1.finance.yahoo.com/v8/finance/chart/%5EOMXSPI"

r = requests.get(url, timeout=20)
data = r.json()

meta = data["chart"]["result"][0]["meta"]

current = meta["regularMarketPrice"]
previous_close = meta["previousClose"]

daily_change = (current / previous_close - 1) * 100

print(f"OMXSPI: {daily_change:.2f}%")

if daily_change > THRESHOLD:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Börslarm",
            "message": (
                f"OMXSPI är upp {daily_change:.2f}% "
                f"kl {sweden_time.strftime('%H:%M')}. "
                f"Larmnivå {THRESHOLD:.1f}% passerad."
            ),
        },
        timeout=20,
    )

    print("Notification sent")

else:
    print("No alert")
