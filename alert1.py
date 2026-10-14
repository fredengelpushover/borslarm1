import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

OMXSPI_THRESHOLD = 1.4
SMABOLAG_THRESHOLD = 1.4
FASTIGHET_THRESHOLD = 2.0

sweden_time = datetime.now(ZoneInfo("Europe/Stockholm"))
if not (
    (sweden_time.hour == 10 and sweden_time.minute >= 45)
    or
    (sweden_time.hour == 11 and sweden_time.minute <= 45)
):
    print(f"Outside allowed time window: {sweden_time:%H:%M:%S} Sweden time")
    exit()
    
try:

    # ---------- OMXSPI ----------

    r = requests.get(
        "https://query1.finance.yahoo.com/v8/finance/chart/%5EOMXSPI",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )

    r.raise_for_status()

    meta = r.json()["chart"]["result"][0]["meta"]

    omx_change = (
        meta["regularMarketPrice"]
        / meta["previousClose"]
        - 1
    ) * 100

    print(f"OMXSPI: {omx_change:.2f}%")

    # ---------- FASTIGHETER ----------

    r = requests.get(
        "https://query1.finance.yahoo.com/v8/finance/chart/%5ESX35GI",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )

    r.raise_for_status()

    meta = r.json()["chart"]["result"][0]["meta"]

    fast_change = (
        meta["regularMarketPrice"]
        / meta["previousClose"]
        - 1
    ) * 100

    print(f"Fastigheter: {fast_change:.2f}%")

    # ---------- SMÅBOLAGSPROXY ----------

    proxy_change = 0

    small_indexes = {
        "^OMXSLCGI": 0.30,
        "^OMXSMCGI": 0.50,
        "^OMXSSCGI": 0.20,
    }

    for ticker, weight in small_indexes.items():

        r = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )

        r.raise_for_status()

        meta = r.json()["chart"]["result"][0]["meta"]

        current = meta["regularMarketPrice"]
        previous = meta["previousClose"]

        change = (current / previous - 1) * 100

        proxy_change += weight * change

    print(f"Småbolagsproxy: {proxy_change:.2f}%")

except Exception as e:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Börslarm fel",
            "message": str(e),
        },
        timeout=20,
    )

    raise

omx_trigger = omx_change > OMXSPI_THRESHOLD
fast_trigger = fast_change > FASTIGHET_THRESHOLD
small_trigger = proxy_change > SMABOLAG_THRESHOLD

if omx_trigger or fast_trigger or small_trigger:


    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Dagens utveckling: (sälj kl 11.40)",
            "message": (
                f"1d OMXSPI: {omx_change:.2f}% "
                f"(gräns {OMXSPI_THRESHOLD:.2f}%)\n"
                f"1d Fastigheter: {fast_change:.2f}% "
                f"(gräns {FASTIGHET_THRESHOLD:.2f}%)\n"
                f"1d Småbolag: {proxy_change:.2f}% "
                f"(gräns {SMABOLAG_THRESHOLD:.2f}%)\n\n"
            ),
        },
        timeout=20,
    )

    print("Notification sent")

else:
    print("No alert")
