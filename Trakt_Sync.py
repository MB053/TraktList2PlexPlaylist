import requests
import webbrowser
from urllib.parse import urlencode
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CLIENT_ID = os.getenv("TRAKT_CLIENT_ID")
CLIENT_SECRET = os.getenv("TRAKT_CLIENT_SECRET")
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ Error: CLIENT_ID and CLIENT_SECRET must be set in the .env file.")
    exit(1)

# Step 1: Build the authorization URL to get the code
params = {
    "response_type": "code",
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI
}
authorize_url = f"https://trakt.tv/oauth/authorize?{urlencode(params)}"

print("🔗 Open the following URL in your browser to authorize your Trakt account:")
print(authorize_url)
try:
    webbrowser.open(authorize_url)
except:
    print("⚠️ Could not open browser. Please manually copy and paste the URL above.")

# Step 2: Ask user to paste the code from the browser
code = input("📋 Paste the code from the URL here: ").strip()

if not code:
    print("❌ Error: No code provided.")
    exit(1)

# Step 3: Exchange the code for an access token
token_url = "https://api.trakt.tv/oauth/token"
data = {
    "code": code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code"
}

try:
    response = requests.post(token_url, json=data)
    response.raise_for_status()
    token_info = response.json()

    print("✅ OAuth successful. Here is your token info:")
    print(token_info)

    # Optional: Automatically update .env file with access token
    with open(".env", "a") as f:
        f.write(f"\nTRAKT_ACCESS_TOKEN={token_info['access_token']}\n")
    print("✅ Access token added to .env file.")

except requests.exceptions.RequestException as e:
    print("❌ Error during token request:", str(e))
    if response is not None:
        try:
            print("Details:", response.json())
        except:
            pass
    exit(1)
