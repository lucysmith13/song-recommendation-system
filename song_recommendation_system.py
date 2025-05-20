import os,tkinter as tk
from flask.cli import load_dotenv
from NEA.user_interface import SpotifyApp

def main():
    print("Current working directory:", os.getcwd())
    load_dotenv(r'C:/Users/lucya/OneDrive - King Edward VI College, Stourbridge/Computer Science/NEA/.env')
    CLIENT_ID = os.getenv("CLIENT_ID")
    print(f"[DEBUG] Client ID: {CLIENT_ID}")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    print(f"[DEBUG] Client secret: {CLIENT_SECRET}")
    REDIRECT_URI = 'http://127.0.0.1:8080/callback'
    SCOPE = "user-read-private user-library-read user-top-read playlist-modify-public playlist-modify-private"
    LAST_FM_KEY = os.getenv('LAST_FM_KEY')
    OPEN_WEATHER_KEY = os.getenv('OPEN_WEATHER_KEY')

    #clearing cache
    if os.path.exists(".cache"):
        os.remove(".cache")

    return CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, OPEN_WEATHER_KEY, SCOPE, LAST_FM_KEY


if __name__ == "__main__":
    CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, OPEN_WEATHER_KEY, SCOPE, LAST_FM_KEY = main()

    master = tk.Tk()
    master.geometry("800x600")
    master.configure(background="white")
    app = SpotifyApp(master, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE, LAST_FM_KEY, OPEN_WEATHER_KEY)
    master.mainloop()

