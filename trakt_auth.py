import os
import json
import requests
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "trakt_token.json")
CONFIG_FILE = os.path.join(BASE_DIR, "trakt_config.txt")

def load_config():
    client_id, client_secret = "", ""
    with open(CONFIG_FILE, "r") as f:
        for line in f:
            if "CLIENT_ID" in line and "=" in line:
                client_id = line.strip().split("=", 1)[1].strip()
            if "CLIENT_SECRET" in line and "=" in line:
                client_secret = line.strip().split("=", 1)[1].strip()
    return client_id, client_secret

def save_token(token_data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)

def load_token():
    if not os.path.isfile(TOKEN_FILE):
        return None
    with open(TOKEN_FILE, "r") as f:
        return json.load(f)

def refresh_token(token_data, client_id, client_secret):
    url = "https://api.trakt.tv/oauth/token"
    data = {
        "refresh_token": token_data["refresh_token"],
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "grant_type": "refresh_token"
    }
    resp = requests.post(url, json=data)
    resp.raise_for_status()
    new_token = resp.json()
    new_token["created_at"] = int(time.time())
    save_token(new_token)
    return new_token

def get_token():
    token_data = load_token()
    if not token_data:
        print(f"DEBUG: Looking for token at {TOKEN_FILE}")
        raise Exception("No Trakt token found, run Trakt_OAuth_Setup.py first.")
    client_id, client_secret = load_config()
    expires_in = token_data.get("expires_in", 3600)
    created_at = token_data.get("created_at", 0)
    if time.time() > created_at + expires_in - 60:
        print("Access token expired, refreshing...")
        token_data = refresh_token(token_data, client_id, client_secret)
    return token_data["access_token"]
