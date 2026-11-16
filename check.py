import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

USER = os.environ["TIKTOK_USER"].strip().lstrip("@")
TOPIC = os.environ["NTFY_TOPIC"].strip()
SEEN_FILE = Path("seen_ids.json")
URL = f"https://www.tiktok.com/@{USER}"


def latest_ids():
    out = subprocess.run(
        [sys.executable, "-m", "yt_dlp", "--flat-playlist",
         "--playlist-items", "1-6", "--print", "id", URL],
        capture_output=True, text=True, timeout=180,
    )
    if out.returncode != 0:
        print(out.stderr[-800:])
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def notify(message, title="New TikTok", click=None):
    headers = {"Title": title, "Priority": "high"}
    if click:
        headers["Click"] = click
    req = urllib.request.Request(
        f"https://ntfy.sh/{TOPIC}", data=message.encode(), headers=headers
    )
    urllib.request.urlopen(req, timeout=30)


def main():
    ids = latest_ids()
    if not ids:
        print("Could not read the profile (TikTok may be blocking this server).")
        sys.exit(1)

    if not SEEN_FILE.exists():
        SEEN_FILE.write_text(json.dumps(sorted(ids)))
        notify("Cloud checker is set up and working.", title="TikTok alerts")
        print("First run: saved current videos.")
        return

    seen = set(json.loads(SEEN_FILE.read_text()))
    new = [i for i in ids if i not in seen]
    for vid in new:
        notify(f"@{USER} just posted!", click=f"{URL}/video/{vid}")
        print("Notified:", vid)
    if new:
        SEEN_FILE.write_text(json.dumps(sorted(seen | set(new))))


if __name__ == "__main__":
    main()
