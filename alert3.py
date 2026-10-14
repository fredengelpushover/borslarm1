import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

FASTIGHET_THRESHOLD = 0.30
SMABOLAG_THRESHOLD = 0.20

FILE = "history.json"

sweden_time = datetime.now(ZoneInfo("Europe/Stockholm"))

if not (
    (sweden_time.hour == 9 and sweden_time.minute >= 5)
    or
    (sweden_time.hour == 10 and sweden_time.minute <= 15)
):
    print(f"Outside allowed time window: {sweden_time:%H:%M:%S} Sweden time")
    exit()
    
today = sweden_time.strftime("%Y-%m-%d")


def get_current_value(ticker):

    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )

    r.raise_for_status()

    data = r.json()

    return data["chart"]["result"][0]["meta"]["regularMarketPrice"]


try:

    # Fastighetsindex
    fast_current = get_current_value("%5ESX35GI")

    # Småbolagsproxy
    large = get_current_value("%5EOMXSLCGI")
    mid = get_current_value("%5EOMXSMCGI")
    small = get_current_value("%5EOMXSSCGI")

    small_proxy_current = (
        0.30 * large
        + 0.50 * mid
        + 0.20 * small
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

# Uppdatera dagens värde

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
        f"Behöver minst 3 dagar historik. Har {len(dates)}."
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

fast_trigger = (
    fast_change > FASTIGHET_THRESHOLD
)

small_trigger = (
    small_change > SMABOLAG_THRESHOLD
)

print(f"Fastigheter 2 dagar: {fast_change:.2f}%")
print(f"Småbolag 2 dagar: {small_change:.2f}%")
print(f"fast_trigger={fast_trigger}")
print(f"small_trigger={small_trigger}")

if fast_trigger or small_trigger:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Tvådagarsutveckling: (sälj kl10)",
            "message": (
                f"TRIGGER: {' | '.join(triggers)}\n\n"
                f"Fastigheter 2d: "
                f"{fast_change:.2f}% "
                f"(gräns {FASTIGHET_THRESHOLD:.2f}%)\n"
                f"Småbolag 2d: "
                f"{small_change:.2f}% "
                f"(gräns {SMABOLAG_THRESHOLD:.2f}%)\n\n"
            ),
        },
        timeout=20,
    )

    print("Notification sent")

else:
    print("No alert")
