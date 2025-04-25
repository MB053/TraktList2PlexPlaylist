# Trakt to Plex Sync

This Python tool automatically synchronizes your custom movie and show lists from [Trakt.tv](https://trakt.tv) to specific playlists in your [Plex Media Server](https://www.plex.tv/).

🎯 **Goal**
- Add the first episode of new shows and new movies from Trakt to your Plex playlists.
- Once an item is successfully added to Plex, remove it from the Trakt list.

---

## 🚀 Features
- ✅ Sync Trakt custom lists to Plex playlists.
- ✅ Only adds Season 1 Episode 1 for TV shows.
- ✅ Avoids duplicates.
- ✅ Automatically removes synced items from Trakt.
- ✅ Robust rate-limit handling and debug logs.

---

## 🧰 Requirements
- Ubuntu Server (tested on 22.04 LTS)
- Python 3.10 or newer
- Access to a Plex Media Server
- A Trakt.tv account with API credentials

---

## 🛠️ Installation Guide

### Step 1: Clone the Project
```bash
sudo apt update && sudo apt install unzip git -y
git clone https://github.com/your-user/trakt2plex-sync.git
cd trakt2plex-sync
```

### Step 2: Create Python Environment
```bash
sudo apt install python3.10-venv -y
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Set Up Trakt OAuth
Edit `.env` with your Trakt credentials and playlist names.
Then run:
```bash
python Trakt_OAuth_Setup.py
```
This will walk you through authenticating your Trakt account and saving your access token.

### Step 4: Create `.env` File
Create a `.env` file with the following format:
```
TRAKT_CLIENT_ID=your_trakt_client_id
TRAKT_ACCESS_TOKEN=your_trakt_token
TRAKT_USERNAME=your_trakt_username
TRAKT_MOVIE_LIST=name_of_your_trakt_movie_list
TRAKT_SHOW_LIST=name_of_your_trakt_show_list

PLEX_URL=http://your.plex.server:32400
PLEX_TOKEN=your_plex_token
PLEX_PLAYLIST_MOVIES=Movie Playlist Name in Plex
PLEX_PLAYLIST_SHOWS=Show Playlist Name in Plex
```

### Step 5: Run the Sync Script
```bash
python Trakt_Sync.py
```

---

## 📂 Folder Structure
```
trakt2plex-sync/
│
├── Trakt_Sync.py               # Main sync logic
├── Trakt_OAuth_Setup.py        # One-time Trakt OAuth flow
├── .env                        # Your credentials & settings
├── README.md                   # This file
├── requirements.txt            # Python dependencies
└── venv/                       # Python virtual environment
```

---

## 🧪 Testing Tips
- Add test items to your Trakt list and watch them get added to Plex.
- Confirm `.env` values match exactly what is in Trakt and Plex.
- Check debug logs printed to console for step-by-step insight.

---

## 🛟 Troubleshooting
- ❗ **Trakt not removing items**: Make sure the item identifiers are correct and that the list is a **custom** list.
- ❗ **Rate Limit**: The script handles Trakt's 429 errors with a wait-and-retry.
- ❗ **Nothing is added**: Make sure Plex and Trakt titles match and your Plex token has access to the correct library.

---

MIT — Free to use, modify, and share. Attribution is appreciated 💛


[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/MB053)
---

Happy syncing! 🎬

