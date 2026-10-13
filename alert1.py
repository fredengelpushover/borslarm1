import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

OMXSPI_THRESHOLD = 0.15
FASTIGHET_THRESHOLD = 0.22

# Svensk tid
sweden_time = datetime.now(ZoneInfo("Europe/Stockholm"))

INDEXES = {
    "OMXSPI": "^OMXSPI",
    "FASTIGHETER": "^SX35GI"
}

changes = {}

try:

    for name, ticker in INDEXES.items():

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )

        r.raise_for_status()

        if not r.text.strip():
            raise Exception(f"Tomt svar från Yahoo för {ticker}")

        data = r.json()

        result = data["chart"]["result"][0]
        meta = result["meta"]

        current = meta["regularMarketPrice"]
        previous_close = meta["previousClose"]

        change = (current / previous_close - 1) * 100

        changes[name] = change

        print(
            f"{name}: "
            f"Current={current} "
            f"Previous={previous_close} "
            f"Change={change:.2f}%"
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

omx_trigger = changes["OMXSPI"] > OMXSPI_THRESHOLD
fastighet_trigger = changes["FASTIGHETER"] > FASTIGHET_THRESHOLD

if omx_trigger or fastighet_trigger:

    triggers = []

    if omx_trigger:
        triggers.append(
            f"OMXSPI {changes['OMXSPI']:.2f}% "
            f">(gräns {OMXSPI_THRESHOLD:.2f}%)"
        )

    if fastighet_trigger:
        triggers.append(
            f"Fastigheter {changes['FASTIGHETER']:.2f}% "
            f">(gräns {FASTIGHET_THRESHOLD:.2f}%)"
        )

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Börslarm",
            "message": (
                f"{' | '.join(triggers)}\n\n"
                f"OMXSPI: {changes['OMXSPI']:.2f}%\n"
                f"Fastigheter: {changes['FASTIGHETER']:.2f}%\n\n"
                f"Kl {sweden_time.strftime('%H:%M')}"
            ),
        },
        timeout=20,
    )

    print("Notification sent")

else:
    print("No alert")
