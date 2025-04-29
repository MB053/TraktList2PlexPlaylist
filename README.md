
# 🎬 Trakt → Plex Playlist Sync

This Python tool automatically synchronizes your custom movie and show lists from [Trakt.tv](https://trakt.tv) to specific playlists in your [Plex Media Server](https://www.plex.tv/).


---

## 🚀 Features

- ✅ Add Movies: From Trakt movie list directly into Plex playlist
- ✅ Add Shows: Only add Season 1, Episode 1 to Plex show playlist
- ✅ Avoid Duplicates
- ✅ Auto-remove from Trakt after Plex import
- ✅ Handle Trakt Rate Limits automatically
- ✅ Configurable via config file or .env
- ✅ Full Debug options

---

## 📦 Repository Contents

```
TraktSyncConfFile/
├── Trakt_Sync_Conf.py
├── Trakt_OAuth_Setup.py
├── trakt_config.txt
├── trakt_access_token.txt
├── .env.example
├── requirements.txt
├── setup.sh
└── README.md
```

---

## 🧰 Requirements

- Ubuntu Server 22.04+ (or any Linux)
- Python 3.10+
- Git
- Plex Media Server
- Trakt.tv account with API app credentials
- Optional: Tautulli to automatically run script

---

## ⚙️ Configuration Options

### Option 1: trakt_config.txt
```
# Trakt Client ID
YOUR_TRAKT_CLIENT_ID
# Trakt Client Secret
YOUR_TRAKT_CLIENT_SECRET
# Trakt Username
YourTraktUsername
# Movie List Slug
your-movie-list
# Show List Slug
your-show-list
# Plex Base URL
http://your.plex.server:32400
# Plex Token
your-plex-token
# Plex Movie Playlist
Your Plex Movie Playlist
# Plex Show Playlist
Your Plex Show Playlist
```

### Option 2: .env
Copy `.env.example` and fill it with your credentials.

---

## 🚀 Setup

```bash
git clone https://github.com/your-user/trakt-plex-sync.git
cd trakt-plex-sync/TraktSyncConfFile
bash setup.sh
source venv/bin/activate
```

### Authenticate with Trakt:
```bash
python Trakt_OAuth_Setup.py
```

Paste the code when prompted. It saves your access token.

---

## ▶️ Usage

```bash
python Trakt_Sync_Conf.py
```

You can also integrate into Tautulli as a notification script.

---

## 🛟 Troubleshooting

- Ensure `trakt_config.txt` and `trakt_access_token.txt` are in the same directory.
- Ensure you use the correct working directory in Tautulli.
- If Trakt list is empty, check manually via their website.
- Plex connection issues usually relate to wrong Token or URL.

---

## ⚖️ License

MIT License




[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/MB053)
---

Happy syncing! 🎬
