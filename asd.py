#!/usr/bin/python

from datetime import datetime, timezone
import requests as req
import json
import sys

CLIENT_ID = "QH0sodO4QzbRjYm1f4FpCtEJvOB3PbaU"

DEBUG = True

HEADERS = { "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0" }

def to_sc_ts(dt: datetime):
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def now_ts():
    now = datetime.now(timezone.utc)
    return to_sc_ts(now)

def get_sc_version():
    try:
        if DEBUG:
            print("[!] getting soundcloud version...")

        res = req.get("https://soundcloud.com/versions.json")
        parsed = json.loads(res.text)
        ver = parsed["app"]

        if DEBUG:
            print(f"[+] soundcloud version: {ver}")

        return ver
    except Exception as e:
        if DEBUG:
            print("[-] failed to get soundcloud version")

        print(e)
        sys.exit(-1)

def get_sc_userid(username: str):
    try:
        if DEBUG:
            print(f"[!] getting soundcloud userid for {username}")

        res = req.get(f"https://api-v2.soundcloud.com/resolve?url=https://soundcloud.com/{username}&client_id={CLIENT_ID}", headers=HEADERS)
        parsed = json.loads(res.text)
        userid = parsed["id"]

        if DEBUG:
            print(f"[+] {username} is {userid}")

        return userid
    except Exception as e:
        if DEBUG:
            print(f"[!] failed to get userid for {username}")

        print(e)
        sys.exit(-1)

def get_user_tracks(username: str, limit: int):
    try:
        if DEBUG:
            print(f"[!] trying to get {username}'s tracks")

        ts = now_ts()
        ver = get_sc_version()
        userid = get_sc_userid(username)
        url = f"https://api-v2.soundcloud.com/users/{userid}/tracks?offset={ts},tracks,00000000000000000000&limit={limit}&representation=&client_id={CLIENT_ID}&app_version={ver}&app_locale=en"

        res = req.get(url, headers=HEADERS)
        parsed = json.loads(res.text)
        collection = parsed["collection"]

        if DEBUG:
            print(f"[+] found {len(collection)} tracks for {username}")

        return collection

    except Exception as e:
        if DEBUG:
            print("f[-] failed to get tracks for {username}")

        print(e)
        sys.exit(-1)

def get_track_playlist_url(track_url: str):
    try:
        if DEBUG:
            print(f"[!] getting {track_url} playlist url")

        url = f"https://api-v2.soundcloud.com/resolve?url={track_url}&client_id={CLIENT_ID}"
        res = req.get(url, headers=HEADERS)
        parsed = json.loads(res.text)

        pl_url = parsed["media"]["transcodings"][0]["url"]
        pl_url += "?"
        pl_url += f"client_id={CLIENT_ID}"
        pl_url += "&"
        pl_url += f"track_authorization={parsed['track_authorization']}"

        res = req.get(pl_url, headers=HEADERS)
        parsed = json.loads(res.text)

        if DEBUG:
            print(f"[+] found playlist url {parsed['url']} for {track_url}")

        return parsed["url"]

    except Exception as e:
        if DEBUG:
            print(f"[-] failed to get {track_url} playlist url")

        print(e)
        sys.exit(-1)

def parse_playlist(playlist_url: str):
    try:
        if DEBUG:
            print("[!] parsing playlist")



    except Exception as e:
        if DEBUG:
            print("[-] failed to parse playlist")

        print(e)
        sys.exit(-1)

tracks = get_user_tracks("drewthearchitect", 20000)

get_track_playlist_url(tracks[0]["permalink_url"])
