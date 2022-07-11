import os


configuration = {
    "genius": {
        "client_id": os.environ["GENIUS_CLIENT_ID"],
        "client_secret": os.environ["GENIUS_CLIENT_SECRET"],
        "client_access_token": os.environ["GENIUS_ACCESS_TOKEN"],
    },
    "telegram": {
        "bot_token": os.environ["TELEGRAM_BOT_TOKEN"]
    },
    "searchers": {
        "amalgama": "AmalgamaLyricsWebLoader",
        "genius": "GeniusLyricsWebLoader"
    }
}
