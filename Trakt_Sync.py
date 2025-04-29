#!/usr/bin/env python3
"""
Trakt ➔ Plex Playlist Sync Tool
Supports both trakt_config.txt and .env for configuration.

This version resolves all config/token paths relative to the script's location,
so it works when Tautulli invokes it from any CWD.
"""
import os
import re
import requests
import xml.etree.ElementTree as ET
import time

# === CONFIGURATION SWITCH ===
USE_ENV = False  # Set True to use .env, False to use trakt_config.txt

# Base dir of this script (so paths are always correct, even under Tautulli)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if USE_ENV:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))
    TRAKT_CLIENT_ID      = os.getenv("TRAKT_CLIENT_ID")
    TRAKT_USERNAME       = os.getenv("TRAKT_USERNAME")
    TRAKT_MOVIE_LIST     = os.getenv("TRAKT_MOVIE_LIST")
    TRAKT_SHOW_LIST      = os.getenv("TRAKT_SHOW_LIST")
    PLEX_URL             = os.getenv("PLEX_URL")
    PLEX_TOKEN           = os.getenv("PLEX_TOKEN")
    PLEX_PLAYLIST_MOVIES = os.getenv("PLEX_PLAYLIST_MOVIES")
    PLEX_PLAYLIST_SHOWS  = os.getenv("PLEX_PLAYLIST_SHOWS")
else:
    # Read the first 9 non-comment lines from trakt_config.txt
    config_file = os.path.join(BASE_DIR, "trakt_config.txt")
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        exit(1)
    with open(config_file, "r") as f:
        lines = [
            line.strip() for line in f.readlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    if len(lines) < 9:
        print("❌ trakt_config.txt must contain 9 values (see README).")
        exit(1)
    (
        TRAKT_CLIENT_ID,
        TRAKT_CLIENT_SECRET,
        TRAKT_USERNAME,
        TRAKT_MOVIE_LIST,
        TRAKT_SHOW_LIST,
        PLEX_URL,
        PLEX_TOKEN,
        PLEX_PLAYLIST_MOVIES,
        PLEX_PLAYLIST_SHOWS
    ) = lines[:9]

# Load the OAuth token that was saved by Trakt_OAuth_Setup.py
token_file = os.path.join(BASE_DIR, "trakt_access_token.txt")
if not os.path.exists(token_file):
    print(f"❌ Trakt access token file missing: {token_file}")
    exit(1)
with open(token_file, "r") as f:
    TRAKT_TOKEN = f.read().strip()

HEADERS_TRAKT = {
    "Content-Type": "application/json",
    "trakt-api-version": "2",
    "Authorization": f"Bearer {TRAKT_TOKEN}",
    "trakt-api-key": TRAKT_CLIENT_ID
}

DEBUG = True
def debug(msg):
    if DEBUG:
        print(f"[DEBUG] {msg}")

def normalize_title(title):
    # Strip trailing (YEAR) and non-alphanumeric, lowercase
    title = re.sub(r"\(\d{4}\)$", "", title).strip()
    return re.sub(r"[^\w]", "", title).lower()

def trakt_list_items(listname, item_type):
    url = f"https://api.trakt.tv/users/{TRAKT_USERNAME}/lists/{listname}/items/{item_type}"
    resp = requests.get(url, headers=HEADERS_TRAKT)
    debug(f"Trakt {item_type} list {resp.status_code} → {url}")
    if resp.status_code != 200:
        return []
    return resp.json()

def search_movie_in_plex(title):
    url = f"{PLEX_URL}/search?query={title}&type=1&X-Plex-Token={PLEX_TOKEN}"
    debug(f"🔍 Plex movie search: {url}")
    resp = requests.get(url)
    tree = ET.fromstring(resp.content)
    results = []
    for vid in tree.findall(".//Video"):
        if vid.attrib.get("type") == "movie":
            results.append({
                "title": vid.attrib["title"],
                "ratingKey": vid.attrib["ratingKey"]
            })
    debug(f"Movie matches: {[m['title'] for m in results]}")
    return results

def search_show_in_plex(title):
    url = f"{PLEX_URL}/search?query={title}&type=2&X-Plex-Token={PLEX_TOKEN}"
    debug(f"🔍 Plex show search: {url}")
    resp = requests.get(url)
    tree = ET.fromstring(resp.content)
    target = normalize_title(title)
    for d in tree.findall(".//Directory"):
        if d.attrib.get("type") == "show":
            norm = normalize_title(d.attrib["title"])
            if norm == target or target in norm or norm in target:
                debug(f"Show match: '{d.attrib['title']}' key {d.attrib['ratingKey']}")
                return d.attrib["ratingKey"]
    debug("No show match")
    return None

def get_first_episode_of_show(show_key):
    url = f"{PLEX_URL}/library/metadata/{show_key}/children?X-Plex-Token={PLEX_TOKEN}"
    resp = requests.get(url)
    tree = ET.fromstring(resp.content)
    # find season 1
    for season in tree.findall(".//Directory"):
        if season.attrib.get("index") == "1":
            season_url = f"{PLEX_URL}{season.attrib['key']}?X-Plex-Token={PLEX_TOKEN}"
            resp2 = requests.get(season_url)
            tree2 = ET.fromstring(resp2.content)
            for ep in tree2.findall(".//Video"):
                if ep.attrib.get("index") == "1":
                    return ep.attrib["ratingKey"]
    return None

def get_machine_identifier():
    resp = requests.get(f"{PLEX_URL}/?X-Plex-Token={PLEX_TOKEN}")
    return ET.fromstring(resp.content).attrib.get("machineIdentifier")

def add_to_playlist(pl_name, rating_key):
    resp = requests.get(f"{PLEX_URL}/playlists?X-Plex-Token={PLEX_TOKEN}")
    tree = ET.fromstring(resp.content)
    for pl in tree.findall(".//Playlist"):
        if pl.attrib.get("title") == pl_name:
            pid = pl.attrib["ratingKey"]
            machine = get_machine_identifier()
            uri = f"server://{machine}/com.plexapp.plugins.library/library/metadata/{rating_key}"
            r2 = requests.put(f"{PLEX_URL}/playlists/{pid}/items?uri={uri}&X-Plex-Token={PLEX_TOKEN}")
            debug(f"➕ Added → HTTP {r2.status_code}")
            return r2.status_code == 200
    return False

def remove_from_trakt(kind, trakt_obj, listname):
    url = f"https://api.trakt.tv/users/{TRAKT_USERNAME}/lists/{listname}/items/remove"
    payload = {f"{kind}s":[{"ids": trakt_obj.get("ids") }]}
    while True:
        r = requests.post(url, headers=HEADERS_TRAKT, json=payload)
        debug(f"🗑️ Remove {kind} → {r.status_code}")
        if r.status_code == 200:
            break
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 1))
            debug(f"⏳ Rate limited, waiting {wait}s")
            time.sleep(wait)
            continue
        debug(f"⚠️ Trakt error: {r.text}")
        break

def sync_trakt_to_plex():
    for kind, listname, playlist in [
        ("movie", TRAKT_MOVIE_LIST, PLEX_PLAYLIST_MOVIES),
        ("show",  TRAKT_SHOW_LIST,  PLEX_PLAYLIST_SHOWS)
    ]:
        debug(f"=== Sync {kind}s ===")
        items = trakt_list_items(listname, kind)
        debug(f"ℹ️ Found {len(items)} item(s) in Trakt list '{listname}'")
        for item in items:
            title = item[kind]["title"]
            debug(f"[PROCESS] {kind}: {title}")
            rating_key = None
            if kind == "movie":
                matches = search_movie_in_plex(title)
                if matches:
                    rating_key = matches[0]["ratingKey"]
            else:
                show_key = search_show_in_plex(title)
                if show_key:
                    rating_key = get_first_episode_of_show(show_key)

            if not rating_key:
                debug(f"⚠️ No Plex match for '{title}'")
                continue

            if add_to_playlist(playlist, rating_key):
                remove_from_trakt(kind, item[kind], listname)

if __name__ == "__main__":
    sync_trakt_to_plex()
