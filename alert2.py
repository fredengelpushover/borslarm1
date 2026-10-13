import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

OMXSPI_THRESHOLD = 1.50
FASTIGHET_THRESHOLD = 3.00

# Svensk tid
sweden_time = datetime.now(ZoneInfo("Europe/Stockholm"))

INDEXES = {
    "OMXSPI": "^OMXSPI",
    "FASTIGHETER": "^SX35PI"
}

changes = {}

try:

    for name, ticker in INDEXES.items():

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

        if not r.text.strip():
            raise Exception(f"Tomt svar från Yahoo för {ticker}")

        data = r.json()

        result = data["chart"]["result"][0]
        meta = result["meta"]

        current = meta["regularMarketPrice"]

        closes = result["indicators"]["quote"][0]["close"]
        closes = [x for x in closes if x is not None]

        print(f"{ticker} closes:")
        print(closes)

        if len(closes) < 3:
            raise Exception(
        f"För få historiska kurser för {ticker}"
            )

        two_days_ago_close = closes[-3]

        change = (
            current / two_days_ago_close - 1
        ) * 100

        changes[name] = change

        print(
            f"{name}: "
            f"Current={current} "
            f"2dClose={two_days_ago_close} "
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
fastighet_trigger = (
    changes["FASTIGHETER"] > FASTIGHET_THRESHOLD
)

if omx_trigger or fastighet_trigger:

    triggers = []

    if omx_trigger:
        triggers.append(
            f"OMXSPI 2d {changes['OMXSPI']:.2f}% "
            f">(gräns {OMXSPI_THRESHOLD:.2f}%)"
        )

    if fastighet_trigger:
        triggers.append(
            f"Fastigheter 2d "
            f"{changes['FASTIGHETER']:.2f}% "
            f">(gräns {FASTIGHET_THRESHOLD:.2f}%)"
        )

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Börslarm 2 dagar",
            "message": (
                f"{' | '.join(triggers)}\n\n"
                f"OMXSPI 2 dagar: "
                f"{changes['OMXSPI']:.2f}%\n"
                f"Fastigheter 2 dagar: "
                f"{changes['FASTIGHETER']:.2f}%\n\n"
                f"Kl {sweden_time.strftime('%H:%M')}"
            ),
        },
        timeout=20,
    )

    print("Notification sent")

else:
    print("No alert")
