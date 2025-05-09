from NEA.spotify_auth  import SpotifyAuth
from NEA.recommendations import Recommendations

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
from dotenv import load_dotenv

load_dotenv()

class SpotifyApp():
    def __init__(self, master, client_id, client_secret, redirect_uri, scope, last_fm_key, open_weather_key):
        self.LAST_FM_KEY = last_fm_key
        self.OPEN_WEATHER_KEY = open_weather_key

        self.master = master
        self.master.title("Song Recommendation System")

        self.spotify_auth = SpotifyAuth(client_id, client_secret, redirect_uri, scope)
        self.access_token = None
        self.user_name = "User"
        self.recs = None

        self.main_ui_setup()

        self.app = Flask(__name__)
        self.setup_routes()
        threading.Thread(target=self.run_flask, daemon=True)

    def main_ui_setup(self):
        self.main_frame = tk.Frame(self.master, bg="lightgray")
        self.main_frame.place(relwidth=1, relheight=1)

        self.authorize_button = tk.Button(self.main_frame, text="Authorize", command=self.authorize, font=("",10), bg="red")
        self.authorize_button.pack(pady=10)

        self.welcome_label = tk.Label(self.main_frame, text=f"Welcome {self.user_name}!", font=("", 16, "bold"), background="lightgray")
        self.welcome_label.place(x=250, y=200)

        tk.Button(self.main_frame, text="Genre Recommendations", command=lambda: self.show_frame(self.genre_recs_frame)).place(width=200, height=100,x=25, y=25)
        tk.Button(self.main_frame, text="User Recommendations", command=lambda: self.show_frame(self.user_recs_frame)).place(width=200, height=100, x=300, y=25)
        tk.Button(self.main_frame, text="Weather Recommendations", command=lambda: self.show_frame(self.weather_recs_frame)).place(width=200, height=100,x=575, y=25)

        self.create_genre_recs_frame()
        self.create_user_recs_frame()
        self.create_weather_recs_frame()

        self.show_frame(self.main_frame)

    def create_genre_recs_frame(self):
        self.genre_recs_frame = tk.Frame(self.master, bg="white")
        tk.Label(self.genre_recs_frame, text="Genre Recommendations", font=("", 16, "bold"), background="lightgray" ).pack(pady=5)

        tk.Button(self.genre_recs_frame, text="Back", command=lambda: self.show_frame(self.main_frame)).place(x=0, y=0)

        tk.Label(self.genre_recs_frame, text="Genre:").pack()
        self.genre_entry = tk.Entry(self.genre_recs_frame)
        self.genre_entry.pack()

        tk.Button(self.genre_recs_frame, text="Generate", command=self.generate_genre_recs).pack()

        self.genre_results_listbox = tk.Listbox(self.genre_recs_frame, width=70, height=15)
        self.genre_results_listbox.pack(pady=10)

    def create_user_recs_frame(self):
        self.user_recs_frame = tk.Frame(self.master, bg="white")
        tk.Label(self.user_recs_frame, text="User-Based Recommendations", font=("", 16, "bold"), background="lightgray" ).pack(pady=5)

        tk.Button(self.user_recs_frame, text="Back", command=lambda: self.show_frame(self.main_frame)).place(x=0,y=0)

        tk.Label(self.user_recs_frame, text="Number of Tracks:").pack()
        self.num_tracks_entry = tk.Entry(self.user_recs_frame)
        self.num_tracks_entry.pack()

        tk.Button(self.user_recs_frame, text="Generate", command=self.generate_user_recs).pack()

        self.user_results_listbox = tk.Listbox(self.user_recs_frame, width=70, height=15)
        self.user_results_listbox.pack(pady=10)

    def create_weather_recs_frame(self):
        self.weather_recs_frame = tk.Frame(self.master, bg="white")
        tk.Label(self.user_recs_frame, text="Weather Recommendations", font=("", 16, "bold"), background="lightgray" ).pack(pady=5)

        tk.Button(self.weather_recs_frame, text="Back", command=lambda: self.show_frame(self.main_frame)).place(x=0,y=0)

        tk.Button(self.weather_recs_frame, text="Generate", command=self.generate_weather_recs).pack()

        self.weather_results_listbox = tk.Listbox(self.weather_recs_frame, width=70, height=15)
        self.weather_results_listbox.pack(pady=10)

    def show_frame(self, frame):
        for widget in self.master.winfo_children():
            widget.place_forget()
        frame.place(relwidth=1, relheight=1)

    def authorize(self):
        auth_url = self.spotify_auth.get_auth_url()
        webbrowser.open_new(auth_url)

    def setup_routes(self):
        print("[DEBUG] Starting Flask server...")
        @self.app.route('/callback')
        def callback():
            code = requests.args.get("code")
            if code:
                self.access_token = self.spotify_auth.get_access_token(code)
                self.master.after(0, self.on_authorized)
            return "Authorization complete."

    def run_flask(self):
        self.app.run(host='127.0.0.1', port=8888, debug=False)

    def on_authorized(self):
        if self.access_token:
            sp = spotipy.Spotify(auth=self.access_token)
            user_info = sp.me()
            self.user_name = user_info['display_name']
            self.welcome_label.config(text=f"Welcome {self.user_name}!")

        self.recs = Recommendations(self.access_token, self.LAST_FM_KEY)

    def generate_genre_recs(self):
        genre = self.genre_entry.get().strip().lower()
        recommendations, uris = self.recs.last_fm_genres(genre, 30)
        self.current_track_uris = uris

        self.genre_results_listbox.delete(0, tk.END)

        for idx, rec in enumerate(recommendations, start=1):
            self.genre_results_listbox.insert(tk.END, f"{idx}. {rec}")

    def generate_user_recs(self):
        top_artist_limit = 10
        similar_artist_limit = 5
        total_tracks_limit = int(self.num_tracks_entry.get())
        # hard-coded option for now, but needs changing to a drop-down menu
        selected_time_range_option_value = "medium_term"
        results, uris = self.recs.user_top_recs(top_artist_limit, similar_artist_limit, total_tracks_limit,selected_time_range_option_value)
        self.current_track_uris = uris

        self.user_results_listbox.delete(0, tk.END)

        for idx, rec in enumerate(results, start=1):
            self.user_results_listbox.insert(tk.END, f"{idx}. {rec}")

    def generate_weather_recs(self):
        recommendations, uris, playlist_name = self.recs.weather_recs(self.OPEN_WEATHER_KEY)
        self.current_track_uris = uris

        self.weather_results_listbox.delete(0, tk.END)

        for idx, rec in enumerate(recommendations, start=1):
            self.weather_results_listbox.insert(tk.END, f"{idx}. {rec}")


    # def authorize(self):
    #     auth_url = self.spotify_auth.get_auth_url()
    #     print(f"[DEBUG] Auth URL: {auth_url}")
    #     webbrowser.open_new_tab(auth_url)
    #     print(f"[DEBUG] Access token: {self.access_token}")
    #
    #     def wait_for_auth():
    #         self.token_received.wait()
    #         print("[DEBUG] Token received event triggered")
    #
    #         print(f"[DEBUG] access_token BEFORE validation: {self.access_token}")
    #         self.access_token = self.spotify_auth.get_valid_token()
    #         print(f"[DEBUG] access_token AFTER validation: {self.access_token}")
    #
    #         if not self.access_token:
    #             print("[ERROR] Access token is still None after validation!")
    #             return
    #
    #         sp = spotipy.Spotify(auth=self.access_token)
    #         user_info = sp.me()
    #         self.user_name = user_info['display_name']
    #
    #
    #         self.welcome_label.config(text=f"Welcome {self.user_name}!", background="white")
    #         self.recs = Recommendations(self.access_token, self.LAST_FM_KEY)
    #
    #     threading.Thread(target=wait_for_auth, daemon=True).start()
    #
    #
    # def add_to_playlist(self):
    #     playlist_name = self.playlist_name_option.get().strip()
    #     if not playlist_name:
    #         messagebox.showerror("Error", "Please enter a playlist name.")
    #         return
    #
    #     sp = spotipy.Spotify(auth=self.access_token)
    #     user_id = sp.current_user()['id']
    #
    #     playlist = sp.user_playlist_create(
    #         user = user_id,
    #         name = playlist_name,
    #         public = True,
    #         description = "Created by Lucy's Song recommendation system"
    #     )
    #
    #     print(f"[DEBUG] Created playlist: {playlist['name']}")
    #
    #     for i in range(0, len(self.current_track_uris), 100):
    #         chunk = self.current_track_uris[i:i+100]
    #         sp.playlist_add_items(playlist_id=playlist['id'], items=chunk)
    #
    #     print(f"[DEBUG] Added tracks to playlist successfully")
    #
    #     messagebox.showinfo(title="Playlist Creation", message=f"{playlist['name']} created successfully")
    #
    # def generate_weather_recs(self):
    #     recommendations, uris, playlist_name = self.recs.weather_recs(OPEN_WEATHER_KEY)
    #     self.current_track_uris = uris
    #
    #     self.weather_recs_listbox.delete(0, tk.END)
    #     self.results_listbox2.config(yscrollcommand = self.scrollbar3.set)
    #     self.scrollbar3.config(command = self.weather_recs_listbox.yview)
    #
    #     for idx, rec in enumerate(recommendations, start=1):
    #         self.weather_recs_listbox.insert(tk.END, f"{idx}. {rec}")
    #
    #     self.add_to_playlist_button.config(state=tk.NORMAL)
    #     self.add_to_playlist_button2.config(state=tk.NORMAL)
    #     self.add_to_playlist_button3.config(state=tk.NORMAL)
    #
    #
    #     self.master.configure(bg="white")
    #
    # def user_recs_button_clicked(self):
    #     self.master.configure(bg="white")
    #     self.user_recs_frame.place(relwidth=1, relheight=1)
    #
    # def genre_button_clicked(self):
    #     self.master.configure(bg="white")
    #     self.genre_recs_frame.place(relwidth=1, relheight=1)
    #
    # def albums_button_clicked(self):
    #     self.master.configure(bg="white")
    #     self.albums_frame.place(relwidth=1, relheight=1)
    #
    #     album = self.recs.album_chooser()
    #
    #     name = album['name']
    #     artist = ", ".join(artist['name'] for artist in album['artists'])
    #     image_url = album['images'][0]['url'] if album['images'] else None
    #
    #     label = tk.Label(self.albums_frame, text=f"{name} by\n{artist}", bg="white", font=("", 16, "bold"))
    #     label.place(x=270, y=100)
    #
    #     img_data = requests.get(image_url).content
    #     img = Image.open(BytesIO(img_data)).resize((300,300))
    #     photo = ImageTk.PhotoImage(img)
    #
    #     image_label = tk.Label(self.albums_frame, image=photo, bg="white")
    #     image_label.image = photo
    #     image_label.place(x=250, y=170)
    #
    # def hide_main_frame(self):
    #     self.authorize_button.place_forget()
    #     self.welcome_label.place_forget()
    #
    # def show_weather_recs_frame(self):
    #     self.master.configure(bg="white")
    #     self.weather_recs_frame.place(relwidth=1, relheight=1)
    #
    # def show_main_frame(self):
    #     self.authorize_button.place(x=325, y=400)
    #     self.welcome_label.place()
    #
    # def refresh_random_album(self):
    #     if self.recs is None:
    #         print("[ERROR] Recommendations not loaded yet, authorize first.")
    #         return None
    #     self.albums_button_clicked()