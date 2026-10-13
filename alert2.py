import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

OMXSPI_THRESHOLD = 0.150
SMABOLAG_THRESHOLD = 0.1200

sweden_time = datetime.now(ZoneInfo("Europe/Stockholm"))

try:

    # ==========================
    # OMXSPI - 2 dagar
    # ==========================

    url = (
        "https://query1.finance.yahoo.com/"
        "v8/finance/chart/%5EOMXSPI?range=5d&interval=1d"
    )

    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )

    r.raise_for_status()

    data = r.json()

    result = data["chart"]["result"][0]

    current = result["meta"]["regularMarketPrice"]

    closes = result["indicators"]["quote"][0]["close"]
    closes = [x for x in closes if x is not None]

    if len(closes) < 3:
        raise Exception("För få historiska kurser för OMXSPI")

    omx_2d_close = closes[-3]

    omx_change = (
        current / omx_2d_close - 1
    ) * 100

    print(
        f"OMXSPI: Current={current} "
        f"2dClose={omx_2d_close} "
        f"Change={omx_change:.2f}%"
    )

    # ==========================
    # Småbolagsproxy - 2 dagar
    # ==========================

    small_indexes = {
        "^OMXSLCGI": 0.30,
        "^OMXSMCGI": 0.50,
        "^OMXSSCGI": 0.20,
    }

    proxy_change = 0

    for ticker, weight in small_indexes.items():

        url = (
            f"https://query1.finance.yahoo.com/"
            f"v8/finance/chart/{ticker}"
            f"?range=5d&interval=1d"
        )

        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )

        r.raise_for_status()

        data = r.json()

        result = data["chart"]["result"][0]

        current = result["meta"]["regularMarketPrice"]

        closes = result["indicators"]["quote"][0]["close"]
        closes = [x for x in closes if x is not None]

        if len(closes) < 3:
            raise Exception(
                f"För få historiska kurser för {ticker}"
            )

        two_days_ago_close = closes[-3]

        change = (
            current / two_days_ago_close - 1
        ) * 100

        proxy_change += weight * change

        print(
            f"{ticker}: "
            f"Current={current} "
            f"2dClose={two_days_ago_close} "
            f"Change={change:.2f}%"
        )

    print(
        f"Småbolagsproxy 2 dagar: "
        f"{proxy_change:.2f}%"
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

omx_trigger = omx_change > OMXSPI_THRESHOLD
small_trigger = proxy_change > SMABOLAG_THRESHOLD

if omx_trigger or small_trigger:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Börslarm 2 dagar",
            "message": (
                f"OMXSPI 2 dagar: "
                f"{omx_change:.2f}% "
                f"(gräns {OMXSPI_THRESHOLD:.2f}%)\n"
                f"Småbolag 2 dagar: "
                f"{proxy_change:.2f}% "
                f"(gräns {SMABOLAG_THRESHOLD:.2f}%)\n\n"
            ),
        },
        timeout=20,
    )

    print("Notification sent")

else:
    print("No alert")
