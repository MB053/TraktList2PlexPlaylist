import requests
import time
import json
import os

CONFIG_FILE = "trakt_config.txt"
TOKEN_FILE = "trakt_token.json"

def load_config():
    # Past bij jouw config: ID = regel 1, Secret = regel 2
    with open(CONFIG_FILE, "r") as f:
        lines = [
            line.strip() for line in f.readlines()
            if line.strip() and not line.strip().startswith("#")
        ]
    if len(lines) < 2:
        print("❌ trakt_config.txt must contain at least Client ID and Secret.")
        exit(1)
    return lines[0], lines[1]

def main():
    client_id, client_secret = load_config()
    redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

    print(f"Open URL: https://trakt.tv/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri.replace(':','%3A')}")
    code = input("Code: ").strip()

    token_url = "https://api.trakt.tv/oauth/token"
    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    resp = requests.post(token_url, json=payload)
    if resp.status_code != 200:
        print(f"❌ Trakt auth failed: {resp.status_code} {resp.text}")
        exit(1)
    data = resp.json()
    # Voeg aanmaak-tijd toe zodat refresh werkt
    data["created_at"] = int(time.time())

    # Sla tokens op in JSON-bestand
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Token saved to {TOKEN_FILE}")

if __name__ == "__main__":
    main()
