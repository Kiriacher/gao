import steam_web_api as swa, os
KEY = os.environ.get("STEAM_API_KEY")
steam = swa.Steam(KEY)

steam.users.search_user("the12thchairman")