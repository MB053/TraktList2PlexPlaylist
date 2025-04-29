#!/usr/bin/env python3
"""
Trakt OAuth Setup Script
"""
import requests, webbrowser, os, sys
from urllib.parse import urlencode

USE_ENV=False

if USE_ENV:
    from dotenv import load_dotenv
    load_dotenv()
    CLIENT_ID=os.getenv("TRAKT_CLIENT_ID")
    CLIENT_SECRET=os.getenv("TRAKT_CLIENT_SECRET")
else:
    if not os.path.exists("trakt_config.txt"):
        print("Error: missing trakt_config.txt"); sys.exit(1)
    with open("trakt_config.txt") as f:
        lines=[l.strip() for l in f if l.strip() and not l.startswith("#")]
    CLIENT_ID,CLIENT_SECRET=lines[:2]

if not CLIENT_ID or not CLIENT_SECRET: sys.exit("Client ID/Secret missing")

REDIRECT="urn:ietf:wg:oauth:2.0:oob"
url="https://trakt.tv/oauth/authorize?"+urlencode({"response_type":"code","client_id":CLIENT_ID,"redirect_uri":REDIRECT})
print("Open URL:",url)
webbrowser.open(url)

code=input("Code: ").strip()
if not code: sys.exit("No code")

resp=requests.post("https://api.trakt.tv/oauth/token",json={
    "code":code,"client_id":CLIENT_ID,"client_secret":CLIENT_SECRET,
    "redirect_uri":REDIRECT,"grant_type":"authorization_code"
})
if resp.status_code!=200: sys.exit("OAuth failed: "+resp.text)
token=resp.json().get("access_token")
with open("trakt_access_token.txt","w") as f: f.write(token)
print("Saved token")
