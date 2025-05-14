# import os
# from NEA.ui import SpotifyApp
# import tkinter
# from tkinter import Tk
# from dotenv import load_dotenv
#
#
# def main():
#     CLIENT_ID = os.getenv("CLIENT_ID")
#     CLIENT_SECRET = os.getenv("CLIENT_SECRET")
#     REDIRECT_URI = 'http://127.0.0.1:8080/callback'
#     SCOPE = "user-library-read user-top-read playlist-modify-public playlist-modify-private"
#     LAST_FM_KEY = os.getenv('LAST_FM_KEY')
#     OPEN_WEATHER_KEY = os.getenv('OPEN_WEATHER_KEY')
#
#     if os.path.exists(".cache"):
#         os.remove(".cache")
#
#
#     master = Tk()
#     master.geometry("800x600")
#     master.configure(background="white")
#
#     app = SpotifyApp(master, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE, LAST_FM_KEY, OPEN_WEATHER_KEY)
#     master.mainloop()
#
#
# if __name__ == "__main__":
#     main()

import os, spotipy, tkinter as tk, requests, random, customtkinter as ctk, time
import dateutil.utils
from bottle import url
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image, ImageTk
from tkinter import ttk, PhotoImage
import webview
import urllib.parse
from flask import Flask, request
import threading
import webbrowser
import re
import http.server
import socketserver
from tkinter import font, messagebox
import json
from io import BytesIO
import datetime
import time
from datetime import datetime, date
from flask.cli import load_dotenv
from flask import Flask, request, redirect
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
    app = SpotifyApp(master, CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, SCOPE, LAST_FM_KEY)
    master.mainloop()

