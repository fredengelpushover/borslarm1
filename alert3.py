
if fast_trigger or small_trigger:

    triggers = []

    if fast_trigger:
        triggers.append("Fastigheter")

    if small_trigger:
        triggers.append("Småbolag")

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
