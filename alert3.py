import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

FASTIGHET_THRESHOLD = 3.0
SMABOLAG_THRESHOLD = 2.0

FILE = "history.json"

sweden_time = datetime.now(
    ZoneInfo("Europe/Stockholm")
)

today = sweden_time.strftime("%Y-%m-%d")


def get_change_today(ticker):

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

    return current, previous_close


try:

    # Fastigheter

    fast_current, _ = get_change_today("%5ESX35GI")

    # Småbolagsproxy

    large_current, _ = get_change_today("%5EOMXSLCGI")
    mid_current, _ = get_change_today("%5EOMXSMCGI")
    small_current, _ = get_change_today("%5EOMXSSCGI")

    small_proxy_current = (
        0.30 * large_current
        + 0.50 * mid_current
        + 0.20 * small_current
    )

except Exception as e:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Börslarm fel",
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


# Uppdatera dagens värden

history[today] = {
    "fastighet": fast_current,
    "smabolag": small_proxy_current
}


# Spara historik

with open(FILE, "w") as f:
    json.dump(
        history,
        f,
        indent=2
    )


dates = sorted(history.keys())

if len(dates) < 3:

    print(
        f"Behöver minst 3 dagar historik. "
        f"Har {len(dates)}."
    )

    raise SystemExit


two_days_ago = dates[-3]

fast_two_days_ago = history[two_days_ago]["fastighet"]

small_two_days_ago = history[two_days_ago]["smabolag"]

fast_change = (
    fast_current / fast_two_days_ago - 1
) * 100

small_change = (
    small_proxy_current / small_two_days_ago - 1
) * 100

print(
    f"Fastigheter: "
    f"{fast_change:.2f}%"
)

print(
    f"Småbolag: "
    f"{small_change:.2f}%"
)

