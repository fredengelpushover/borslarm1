import os
import requests

THRESHOLD = 1.5

# Temporärt testvärde
daily_change = 1.7

if daily_change > THRESHOLD:

    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.environ["PUSHOVER_TOKEN"],
            "user": os.environ["PUSHOVER_USER"],
            "title": "Börslarm",
            "message": (
                f"Svenska börsen är upp "
                f"{daily_change:.2f}% idag"
            )
        }
    )

    print("Notification sent")
else:
    print("No alert")
