#!/usr/bin/env python3
"""
Trakt ➔ Plex Playlist Sync Tool
Supports old-school trakt_config.txt (values in order, no KEY=VALUE required).
Automatic Trakt token refresh via trakt_auth.py.
Telegram notifications supported!
"""

import os
import re
import requests
import xml.etree.ElementTree as ET
import time
import trakt_auth  # Automatic Trakt token management

# === CONFIGURATION SWITCH ===
USE_ENV = False  # Set True to use .env, False to use trakt_config.txt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config_env():
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(BASE_DIR, '.env'))
    config = {
        "TRAKT_CLIENT_ID": os.getenv("TRAKT_CLIENT_ID"),
        "TRAKT_CLIENT_SECRET": os.getenv("TRAKT_CLIENT_SECRET"),
        "TRAKT_USERNAME": os.getenv("TRAKT_USERNAME"),
        "TRAKT_MOVIE_LIST": os.getenv("TRAKT_MOVIE_LIST"),
        "TRAKT_SHOW_LIST": os.getenv("TRAKT_SHOW_LIST"),
        "PLEX_URL": os.getenv("PLEX_URL"),
        "PLEX_TOKEN": os.getenv("PLEX_TOKEN"),
        "PLEX_PLAYLIST_MOVIES": os.getenv("PLEX_PLAYLIST_MOVIES"),
        "PLEX_PLAYLIST_SHOWS": os.getenv("PLEX_PLAYLIST_SHOWS"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
    }
    return config

def load_config_txt():
    config_file = os.path.join(BASE_DIR, "trakt_config.txt")
    if not os.path.exists(config_file):
        print(f"❌ Configuration file not found: {config_file}")
        exit(1)
    config = {}
    key_order = [
        "TRAKT_CLIENT_ID", "TRAKT_CLIENT_SECRET", "TRAKT_USERNAME", "TRAKT_MOVIE_LIST",
        "TRAKT_SHOW_LIST", "PLEX_URL", "PLEX_TOKEN", "PLEX_PLAYLIST_MOVIES",
        "PLEX_PLAYLIST_SHOWS", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"
    ]
    idx = 0
    with open(config_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if idx < len(key_order):
                config[key_order[idx]] = line
                idx += 1
    # Fill missing keys with empty string
    for key in ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]:
        if key not in config:
            config[key] = ""
    return config

config = load_config_env() if USE_ENV else load_config_txt()
TRAKT_CLIENT_ID       = config["TRAKT_CLIENT_ID"]
TRAKT_CLIENT_SECRET   = config["TRAKT_CLIENT_SECRET"]
TRAKT_USERNAME        = config["TRAKT_USERNAME"]
TRAKT_MOVIE_LIST      = config["TRAKT_MOVIE_LIST"]
TRAKT_SHOW_LIST       = config["TRAKT_SHOW_LIST"]
PLEX_URL              = config["PLEX_URL"]
PLEX_TOKEN            = config["PLEX_TOKEN"]
PLEX_PLAYLIST_MOVIES  = config["PLEX_PLAYLIST_MOVIES"]
PLEX_PLAYLIST_SHOWS   = config["PLEX_PLAYLIST_SHOWS"]
TELEGRAM_BOT_TOKEN    = config.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID      = config.get("TELEGRAM_CHAT_ID", "")

TRAKT_TOKEN = trakt_auth.get_token()

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

def send_telegram_message(bot_token, chat_id, message):
    if not bot_token or not chat_id:
        debug("Telegram not configured, skipping notification.")
        return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code == 200:
            debug("Telegram notification sent!")
        else:
            debug(f"Telegram error: {resp.status_code} {resp.text}")
    except Exception as e:
        debug(f"Telegram exception: {e}")

def sync_trakt_to_plex():
    removed_titles = []
    added_titles = []

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
                removed_titles.append(title)
                added_titles.append(title)

    # Telegram notification
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID and (removed_titles or added_titles):
        msg = ""
        if removed_titles:
            msg += "🗑️ <b>Removed from Trakt:</b>\n" + "\n".join(f"- {t}" for t in removed_titles) + "\n\n"
        if added_titles:
            msg += "➕ <b>Added to Plex playlist:</b>\n" + "\n".join(f"- {t}" for t in added_titles)
        send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, msg.strip())

if __name__ == "__main__":
    sync_trakt_to_plex()
