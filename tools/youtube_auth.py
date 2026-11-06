#!/usr/bin/env python3
"""One-time YouTube OAuth (device flow) -> YOUTUBE_REFRESH_TOKEN.

Setup:
1. Google Cloud Console -> new project -> enable "YouTube Data API v3".
2. OAuth consent screen -> External -> add yourself as a test user.
3. Credentials -> Create OAuth client ID -> type "TVs and Limited Input devices".
4. .env me YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET daalo.
5. python tools/youtube_auth.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from pipeline.config import env, load_env
from pipeline.youtube import DEVICE_CODE_URL, SCOPES, TOKEN_URL


def _post(url: str, body: dict) -> dict:
    data = urllib.parse.urlencode(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return json.loads(raw or "{}")
        except json.JSONDecodeError:
            return {"error": raw[:400]}


def main() -> int:
    parser = argparse.ArgumentParser(description="YouTube OAuth device flow -> refresh token")
    parser.add_argument(
        "--out",
        default=None,
        help="refresh token ko is file me bhi likho (GitHub Actions artifact ke liye)",
    )
    args = parser.parse_args()

    load_env()
    client_id = env("YOUTUBE_CLIENT_ID")
    client_secret = env("YOUTUBE_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET missing (.env ya repo secrets me daalo).")
        return 1

    start = _post(DEVICE_CODE_URL, {"client_id": client_id, "scope": SCOPES})
    if "device_code" not in start:
        print(json.dumps(start, indent=2, ensure_ascii=False))
        return 1

    print("APNE PHONE KE BROWSER ME YE KHOLO (kisi bhi device se):")
    print(f"   URL  : {start['verification_url']}")
    print(f"   CODE : {start['user_code']}")
    print("")
    print("Wahan Google account se sign in karo -> apna channel choose karo -> Allow dabao.")
    print("Ye job khud wait karegi. Allow karte hi 10-20 second me token mil jayega.\n")

    interval = max(5, int(start.get("interval", 5)))
    deadline = time.time() + int(start.get("expires_in", 1800))

    while time.time() < deadline:
        token = _post(
            TOKEN_URL,
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "device_code": start["device_code"],
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )
        refresh_token = token.get("refresh_token")
        if refresh_token:
            print("MIL GAYA. Ab ise YOUTUBE_REFRESH_TOKEN secret me daalo.\n")
            print(f"YOUTUBE_REFRESH_TOKEN={refresh_token}")
            if args.out:
                Path(args.out).write_text(refresh_token + "\n", encoding="utf-8")
                print(f"\n(token {args.out} me bhi likh diya — job ke baad artifact download kar lo)")
            return 0

        error = token.get("error")
        if error == "authorization_pending":
            time.sleep(interval)
            continue
        if error == "slow_down":
            interval += 5
            time.sleep(interval)
            continue
        print(json.dumps(token, indent=2, ensure_ascii=False))
        return 1

    print("Code expire ho gaya — job dobara chalao.")
    return 1



if __name__ == "__main__":
    sys.exit(main())
