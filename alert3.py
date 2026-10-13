import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

THRESHOLD = 3.0

FILE = "fastighet_history.json"

sweden_time = datetime.now(
    ZoneInfo("Europe/Stockholm")
)

today = sweden_time.strftime("%Y-%m-%d")

try:

    url = (
        "https://query1.finance.yahoo.com/"
        "v8/finance/chart/%5ESX35GI"
    )

    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )

    r.raise_for_status()

    data = r.json()

    meta = data["chart"]["result"][0]["meta"]

    current = meta["regularMarketPrice"]

except Exception as e:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Fastighetslarm fel",
            "message": str(e)
        },
        timeout=20,
    )

    raise

# Läs historik

if os.path.exists(FILE):

    with open(FILE, "r") as f:
        history = json.load(f)

else:

    history = {}

# Uppdatera dagens värde

history[today] = current

# Spara

with open(FILE, "w") as f:
    json.dump(
        history,
        f,
        indent=2
    )

dates = sorted(history.keys())

if len(dates) < 3:
    print("För få dagar sparade")
    raise SystemExit

two_days_ago = dates[-3]

two_days_ago_close = history[two_days_ago]

change = (
    current / two_days_ago_close - 1
) * 100

print(
    f"Current={current} "
    f"2dClose={two_days_ago_close} "
    f"Change={change:.2f}%"
)

if change > THRESHOLD:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Fastigheter 2 dagar",
            "message": (
                f"Fastighetsindex är upp "
                f"{change:.2f}% på två dagar.\n"
                f"Kl {sweden_time.strftime('%H:%M')}\n"
                f"Larmnivå {THRESHOLD:.1f}%"
            ),
        },
        timeout=20,
    )

    print("Notification sent")

else:
    print("No alert")
