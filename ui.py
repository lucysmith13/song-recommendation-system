from NEA.spotify_auth  import SpotifyAuth
from NEA.other_features import Stats
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
    def __init__(self, master, client_id, client_secret, redirect_uri, scope, last_fm_key):
        self.LAST_FM_KEY = last_fm_key
        self.master = master
        self.spotify_auth = SpotifyAuth(client_id, client_secret, redirect_uri, scope)
        self.token_received = threading.Event()
        self.access_token = None
        self.stats = None
        self.user_name = "User"
        self.recs = None

        self.master.title("Song recommendation system")

        self.authorize_button = tk.Button(self.master, text="Authorize with Spotify", command=self.authorize, font=("",10), background="red")
        self.authorize_button.pack(pady=20)
        self.authorize_button.place(x=0, y=0)

        self.welcome_label = tk.Label(self.master, text=f"Welcome {self.user_name}!", font=("",16, "bold"), background="white")
        self.welcome_label.place(x=300, y=75)

        self.stats_button = tk.Button(self.master, text=f"{self.user_name}'s Spotify\nStatistics:", background="darkgray", borderwidth=5)
        self.stats_button['command'] = self.stats_button_clicked
        self.stats_button.place(x=100, y=150, width="200", height="200")

        self.recs_button = tk.Button(self.master, text="Song\nRecommendations: ", background="darkgray", borderwidth=5)
        self.recs_button['command'] = self.recs_button_clicked
        self.recs_button.place(x=450, y=150, width="200", height="200")

        self.stats_button.config(state=tk.DISABLED)
        self.recs_button.config(state=tk.DISABLED)

        self.stats_frame = tk.Frame(self.master, bg="white")
        self.stats_frame.place(relwidth=1, relheight=1)

        self.stats_label = tk.Label(self.stats_frame, text=f"{self.user_name}'s Spotify Stats: ", font=("",16, "bold"), background="white")
        self.stats_label.pack(pady=20)

        self.back_button1 = tk.Button(self.stats_frame, text="Back", command=self.show_main_frame, background="white")
        self.back_button1.place(x=0,y=0)

        self.recs_frame = tk.Frame(self.master, bg="white")
        self.recs_frame.place(relwidth=1, relheight=1)

        self.recs_label = tk.Label(self.recs_frame, text=f"{self.user_name}'s recommendations:", font=("",16, "bold"), background="white")
        self.recs_label.pack(pady=20)

        self.back_button2 = tk.Button(self.recs_frame, text="Back", command=self.show_main_frame, background="white")
        self.back_button2.place(x=0, y=0)

        self.recs_frame.place_forget()

        self.app = Flask(__name__)
        self.setup_routes()
        threading.Thread(target=self.run_flask, daemon=True).start()

        self.stats_frame.place_forget()
        self.recs_frame.place_forget()
        self.show_main_frame()

        self.all_time_stats_label = tk.Label(self.stats_frame, text="All time stats: ", font=("",14, "bold"), background="darkgray", bd=5, anchor="n")
        self.all_time_stats_label.place(x=550, y=150, width=250, height=450)

        self.user_recs_button = tk.Button(self.recs_frame, text="User-Based\nRecommendations", background="green")
        self.user_recs_button['command'] = self.user_recs_button_clicked
        self.user_recs_button.place(x=50, y=100, width=150, height=150)

        self.albums_button = tk.Button(self.recs_frame, text="Random Album Picker", background="green")
        self.albums_button['command'] = self.albums_button_clicked
        self.albums_button.place(x=300, y=100, width=150, height=150)

        self.albums_frame = tk.Frame(self.master, bg="white")
        self.albums_frame.place(relwidth=1, relheight=1)

        self.albums_label = tk.Label(self.albums_frame, text="Random Album Picker", font=("",14, "bold"), background="white")
        self.albums_label.pack(pady=20)

        self.back_button4 = tk.Button(self.albums_frame, text="Back", command=self.show_recs_frame, background="white")
        self.back_button4.place(x=0,y=0)

        self.refresh_album_button = tk.Button(self.albums_frame, text="Refresh", background="white")
        self.refresh_album_button.place(x=750, y=0)
        self.refresh_album_button['command'] = self.refresh_random_album

        self.genre_recs_button = tk.Button(self.recs_frame, text="Genre Recommendations", background="green")
        self.genre_recs_button['command'] = self.genre_button_clicked
        self.genre_recs_button.place(x=550, y=100, width=150, height=150)

        self.user_recs_frame = tk.Frame(self.master, bg="white")
        self.user_recs_frame.place(relwidth=1, relheight=1)

        self.genre_recs_frame = tk.Frame(self.master, bg="white")
        self.user_recs_frame.place(relwidth=1, relheight=1)

        self.back_button5 = tk.Button(self.genre_recs_frame, text="Back", command=self.show_recs_frame, background="white")
        self.back_button5.place(x=0,y=0)

        self.user_recs_label = tk.Label(self.user_recs_frame, text="User-based Recommendations", font=("",16, "bold"), background="white")
        self.user_recs_label.pack(pady=20)

        self.genre_recs_label = tk.Label(self.genre_recs_frame, text="Genre Recommendations", font=("", 16, "bold"), background="white")
        self.genre_recs_label.pack(pady=20)

        self.back_button3 = tk.Button(self.user_recs_frame, text="Back", command=self.show_recs_frame, background="white")
        self.back_button3.place(x=0, y=0)

        tk.Label(self.genre_recs_frame, text="Number of Tracks:").pack()
        self.num_tracks_entry = tk.Entry(self.genre_recs_frame)
        self.num_tracks_entry.pack()
        tk.Label(self.genre_recs_frame, text="Genre:").pack()
        self.genre_entry = tk.Entry(self.genre_recs_frame)
        self.genre_entry.pack()
        generate_recommendations_button = tk.Button(self.genre_recs_frame, text="Generate Recommendations")
        generate_recommendations_button['command'] = self.generate_genre_recommendations
        generate_recommendations_button.pack(pady=10)
        self.results_listbox = tk.Listbox(self.genre_recs_frame, width=70, height=15)
        self.results_listbox.pack(pady=20)
        tk.Label(self.genre_recs_frame, text="Playlist Name:").pack()
        self.playlist_name_option = tk.Entry(self.genre_recs_frame)
        self.playlist_name_option.pack()
        self.add_to_playlist_button = tk.Button(self.genre_recs_frame, text="Add to Playlist", state="disabled")
        self.add_to_playlist_button['command'] = self.add_to_playlist
        self.add_to_playlist_button.pack(pady=10)

        tk.Label(self.user_recs_frame, text="Time-Range:").pack()
        self.time_range_options = ["short_term", "medium_term", "long_term"]
        self.selected_time_range_option = tk.StringVar()
        self.time_range_dropdown = tk.OptionMenu(self.user_recs_frame, self.selected_time_range_option, *self.time_range_options)
        self.time_range_dropdown.pack()
        tk.Label(self.user_recs_frame, text="Number of tracks").pack()
        self.num_tracks = tk.Entry(self.user_recs_frame)
        self.num_tracks.pack()
        generate_user_recs_button = tk.Button(self.user_recs_frame, text="Generate Recommendations")
        generate_user_recs_button['command'] = self.generate_user_recs
        generate_user_recs_button.pack(pady=10)
        self.results_listbox2 = tk.Listbox(self.user_recs_frame, width=70, height=15)
        self.results_listbox2.pack(pady=20)
        self.scrollbar = tk.Scrollbar(self.user_recs_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill= tk.BOTH)
        tk.Label(self.user_recs_frame, text="Playlist Name: ").pack()
        self.playlist_name_option = tk.Entry(self.user_recs_frame)
        self.playlist_name_option.pack()
        self.add_to_playlist_button2 = tk.Button(self.user_recs_frame, text="Add to Playlist", state="disabled")
        self.add_to_playlist_button2.pack(pady=10)
        self.add_to_playlist_button2['command'] = self.add_to_playlist

        self.weather_recs_button = tk.Button(self.recs_frame, text="Weather\nRecommendations", background="green")
        self.weather_recs_button['command'] = self.show_weather_recs_frame
        self.weather_recs_button.place(x=50, y=325, width=150, height=150)
        self.weather_recs_frame = tk.Frame(self.master, background="white")
        self.weather_recs_frame.place(relwidth=1, relheight=1)
        self.back_button6 = tk.Button(self.weather_recs_frame, text="Back", command=self.show_recs_frame, background="white")
        self.back_button6.place(x=0, y=0)
        self.weather_recs_label = tk.Label(self.weather_recs_frame, text="Weather Recommendations", font=("",16, "bold"), background="white")
        self.weather_recs_label.pack(pady=20)
        self.weather_recs_name = tk.Label(self.weather_recs_frame, text="[PLAYLIST NAME HERE]", font=("", 14, "bold"), background="white")
        self.weather_recs_name.pack(pady=20)
        self.weather_recs_listbox = tk.Listbox(self.weather_recs_frame, width=70, height=15)
        self.weather_recs_listbox.pack(pady=20)
        self.scrollbar3 = tk.Scrollbar(self.weather_recs_frame)
        self.scrollbar3.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.generate_weather_button = tk.Button(self.weather_recs_frame, text="Generate Recommendations")
        self.generate_weather_button.pack()
        self.generate_weather_button['command'] = self.generate_weather_recs
        self.add_to_playlist_button3 = tk.Button(self.weather_recs_frame, text="Add to Playlist", state="disabled")
        self.add_to_playlist_button3.pack(pady=10)
        self.add_to_playlist_button3['command'] = self.add_to_playlist

        self.another_recs_button = tk.Button(self.recs_frame, text="BLANK", background="green")
        self.another_recs_button.place(x=300, y=325, width=150, height=150)

        self.final_recs_button = tk.Button(self.recs_frame, text="BLANK", background="green")
        self.final_recs_button.place(x=550, y=325, width=150, height=150)

        self.weather_recs_frame.place_forget()
        self.user_recs_frame.place_forget()
        self.genre_recs_frame.place_forget()
        self.albums_frame.place_forget()
        self.refresh_random_album()
        self.show_main_frame()

        auth_url = self.spotify_auth.get_auth_url()
        print(f"[DEBUG] Full auth URL: {auth_url}")

    def setup_routes(self):
        @self.app.route('/callback')
        def callback():
            print("[DEBUG] Callback hit!")
            code = request.args.get("code")
            print(f"[DEBUG] Code: {code}")

            if code:
                self.access_token = self.spotify_auth.get_access_token(code)
                print(f"[DEBUG] Final access_token: {self.access_token}")

                if not self.access_token:
                    print("[ERROR] Access token is still None after get_access_token")
                else:
                    print("[DEBUG] Access token is valid")

                self.token_received.set()
                return """
                    <script>
                        window.close()
                    </script>
                    <p>You can now return to the app.</p>
                """

            return "No code found"

    def run_flask(self):
        self.app.run(host='127.0.0.1', port=8888, debug=False)


    def authorize(self):
        auth_url = self.spotify_auth.get_auth_url()
        print(f"[DEBUG] Auth URL: {auth_url}")
        webbrowser.open_new_tab(auth_url)
        print(f"[DEBUG] Access token: {self.access_token}")

        def wait_for_auth():
            self.token_received.wait()
            print("[DEBUG] Token received event triggered")

            print(f"[DEBUG] access_token BEFORE validation: {self.access_token}")
            self.access_token = self.spotify_auth.get_valid_token()
            print(f"[DEBUG] access_token AFTER validation: {self.access_token}")

            if not self.access_token:
                print("[ERROR] Access token is still None after validation!")
                return
            self.stats = Stats(self.access_token)

            sp = spotipy.Spotify(auth=self.access_token)
            user_info = sp.me()
            self.user_name = user_info['display_name']


            self.welcome_label.config(text=f"Welcome {self.user_name}!", background="white")
            self.stats_label.config(text=f"{self.user_name}'s Spotify Stats: ", font=("",16, "bold"), background="white")
            self.recs_label.config(text=f"{self.user_name}'s recommendations: ", font=("",16, "bold"), background="white")

            self.stats_button.config(state=tk.NORMAL)
            self.recs_button.config(state=tk.NORMAL)

            self.recs = Recommendations(self.stats, self.access_token, self.LAST_FM_KEY)

        threading.Thread(target=wait_for_auth, daemon=True).start()


    def add_to_playlist(self):
        playlist_name = self.playlist_name_option.get().strip()
        if not playlist_name:
            messagebox.showerror("Error", "Please enter a playlist name.")
            return

        sp = spotipy.Spotify(auth=self.access_token)
        user_id = sp.current_user()['id']

        playlist = sp.user_playlist_create(
            user = user_id,
            name = playlist_name,
            public = True,
            description = "Created by Lucy's Song recommendation system"
        )

        print(f"[DEBUG] Created playlist: {playlist['name']}")

        for i in range(0, len(self.current_track_uris), 100):
            chunk = self.current_track_uris[i:i+100]
            sp.playlist_add_items(playlist_id=playlist['id'], items=chunk)

        print(f"[DEBUG] Added tracks to playlist successfully")

        messagebox.showinfo(title="Playlist Creation", message=f"{playlist['name']} created successfully")

    def generate_genre_recommendations(self):
        genre = self.genre_entry.get().strip().lower()
        limit = int(self.num_tracks_entry.get())
        recommendations, uris = self.recs.last_fm_genres(genre, limit)
        self.current_track_uris = uris

        self.results_listbox.delete(0, tk.END)

        for idx, rec in enumerate(recommendations, start=1):
            self.results_listbox.insert(tk.END, f"{idx}. {rec}")

        self.add_to_playlist_button.config(state=tk.NORMAL)
        self.add_to_playlist_button2.config(state=tk.NORMAL)

    def generate_user_recs(self):
        top_artist_limit = 10
        similar_artist_limit = 5
        total_tracks_limit = int(self.num_tracks.get())
        selected_time_range_option_value = self.selected_time_range_option.get()
        results, uris = self.recs.user_top_recs(top_artist_limit, similar_artist_limit, total_tracks_limit,selected_time_range_option_value)
        self.current_track_uris = uris

        self.results_listbox2.delete(0, tk.END)

        self.results_listbox2.config(yscrollcommand = self.scrollbar.set)
        self.scrollbar.config(command = self.results_listbox2.yview)

        for idx, rec in enumerate(results, start=1):
            self.results_listbox2.insert(tk.END, f"{idx}. {rec}")

        self.add_to_playlist_button.config(state=tk.NORMAL)
        self.add_to_playlist_button2.config(state=tk.NORMAL)

    def generate_weather_recs(self):
        recommendations, uris, playlist_name = self.recs.weather_recs(OPEN_WEATHER_KEY)
        self.current_track_uris = uris

        self.weather_recs_listbox.delete(0, tk.END)
        self.results_listbox2.config(yscrollcommand = self.scrollbar3.set)
        self.scrollbar3.config(command = self.weather_recs_listbox.yview)

        for idx, rec in enumerate(recommendations, start=1):
            self.weather_recs_listbox.insert(tk.END, f"{idx}. {rec}")

        self.add_to_playlist_button.config(state=tk.NORMAL)
        self.add_to_playlist_button2.config(state=tk.NORMAL)
        self.add_to_playlist_button3.config(state=tk.NORMAL)

    def stats_button_clicked(self):
        if self.stats is None:
            messagebox.showerror("Error", "Spotify data not loaded yet. Please wait or reauthorize.")
            return

        self.master.configure(bg="white")
        self.hide_main_frame()
        self.stats_frame.place(relwidth=1, relheight=1)

        all_time_artists = self.stats.get_top_artists(limit=3, time_range="long_term")
        all_time_tracks = self.stats.get_top_tracks(limit=3, time_range="long_term")

        self.all_time_stats_label.config(text="Top Artists (All Time):\n" + "\n".join(all_time_artists) + "\n\nTop Tracks (All Time):\n" + "\n".join(all_time_tracks))

    def recs_button_clicked(self):
        self.master.configure(bg="white")
        self.hide_main_frame()
        self.recs_frame.place(relwidth=1, relheight=1)

    def user_recs_button_clicked(self):
        self.master.configure(bg="white")
        self.hide_stats_frame()
        self.hide_recs_frame()
        self.user_recs_frame.place(relwidth=1, relheight=1)

    def genre_button_clicked(self):
        self.master.configure(bg="white")
        self.hide_stats_frame()
        self.hide_recs_frame()
        self.genre_recs_frame.place(relwidth=1, relheight=1)

    def albums_button_clicked(self):
        self.master.configure(bg="white")
        self.hide_stats_frame()
        self.hide_recs_frame()
        self.albums_frame.place(relwidth=1, relheight=1)

        album = self.recs.album_chooser()

        name = album['name']
        artist = ", ".join(artist['name'] for artist in album['artists'])
        image_url = album['images'][0]['url'] if album['images'] else None

        label = tk.Label(self.albums_frame, text=f"{name} by\n{artist}", bg="white", font=("", 16, "bold"))
        label.place(x=270, y=100)

        img_data = requests.get(image_url).content
        img = Image.open(BytesIO(img_data)).resize((300,300))
        photo = ImageTk.PhotoImage(img)

        image_label = tk.Label(self.albums_frame, image=photo, bg="white")
        image_label.image = photo
        image_label.place(x=250, y=170)

    def hide_main_frame(self):
        self.authorize_button.place_forget()
        self.welcome_label.place_forget()
        self.recs_button.place_forget()
        self.stats_button.place_forget()

    def hide_stats_frame(self):
        self.stats_frame.place_forget()

    def hide_recs_frame(self):
        self.recs_frame.place_forget()

    def show_stats_frame(self):
        self.genre_recs_frame.place_forget()
        self.all_time_stats_label.place(x=550, y=150, width=250, height=450)

    def show_recs_frame(self):
        self.genre_recs_frame.place_forget()
        self.albums_frame.place_forget()
        self.user_recs_frame.place_forget()
        self.recs_frame.place(relwidth=1, relheight=1)

    def show_weather_recs_frame(self):
        self.master.configure(bg="white")
        self.hide_recs_frame()
        self.hide_stats_frame()
        self.weather_recs_frame.place(relwidth=1, relheight=1)

    def show_main_frame(self):
        self.stats_frame.place_forget()
        self.recs_frame.place_forget()
        self.authorize_button.place(x=0, y=0)
        self.welcome_label.place(x=300, y=75)
        self.stats_button.place(x=100, y=150, width=200, height=200)
        self.recs_button.place(x=450, y=150, width=200, height=200)


    def refresh_random_album(self):
        if self.recs is None:
            print("[ERROR] Recommendations not loaded yet, authorize first.")
            return None
        self.albums_button_clicked()