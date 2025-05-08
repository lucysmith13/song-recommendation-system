import os
from NEA.ui import SpotifyApp
import tkinter
from tkinter import Tk
from dotenv import load_dotenv

load_dotenv()

def main():
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = 'http://127.0.0.1:8888/callback'
    SCOPE = "user-library-read user-top-read playlist-modify-public playlist-modify-private"
    LAST_FM_KEY = os.getenv('LAST_FM_KEY')
    OPEN_WEATHER_KEY = os.getenv('OPEN_WEATHER_KEY')

    if os.path.exists(".cache"):
        os.remove(".cache")


    master = Tk()
    master.geometry("800x600")
    master.configure(background="white")

    app = SpotifyApp(master, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE, LAST_FM_KEY)
    master.mainloop()


if __name__ == "__main__":
    main()
