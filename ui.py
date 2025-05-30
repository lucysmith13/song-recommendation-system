from NEA.recommendations import Recommendations
from NEA.spotify_auth import SpotifyAuth
import threading, requests, time, spotipy, tkinter as tk, flask, webbrowser
from flask import request
from flask import Flask
from dotenv import load_dotenv
from tkinter import messagebox
from spotipy import SpotifyOAuth

load_dotenv()

class UserInterface():
    def __init__(self, master, client_id, client_secret, redirect_uri, scope, last_fm_key, open_weather_key):
        self.master = master
        self.client_id = client_id
        self.spotify_auth = SpotifyAuth(self.client_id, client_secret, redirect_uri, scope)
        self.token_received = threading.Event()
        self.access_token = None
        self.user_name = "User"
        self.recs = None
        self.last_fm_key = last_fm_key
        self.open_weather_key = open_weather_key

    def create_frame(self, frame):
