from PIL import ImageTk, Image
from io import BytesIO

from NEA.recommendations import Recommendations
from NEA.spotify_auth import SpotifyAuth
import threading, requests, time, spotipy, tkinter as tk, flask, webbrowser
from flask import request
from flask import Flask
from dotenv import load_dotenv
from tkinter import messagebox
from spotipy import SpotifyOAuth
import base64

load_dotenv()

class SpotifyApp():
        def __init__(self, master, client_id, client_secret, redirect_uri, scope, last_fm_key, open_weather_key):
            self.master = master
            self.client_id = client_id
            self.spotify_auth = SpotifyAuth(self.client_id, client_secret, redirect_uri, scope)
            self.token_received = threading.Event()
            self.access_token = None
            self.user_name = "User"
            self.recs = None
            self.last_fm_key = last_fm_key
            self.OPEN_WEATHER_KEY = open_weather_key


            self.master.title("Song recommendation system")

            self.recs_frame = tk.Frame(self.master, bg="white")
            self.recs_frame.place(relwidth=1, relheight=1)

            self.authorize_button = tk.Button(self.master, text="Authorize with Spotify", command=self.authorize, font=("",10), background="red")
            self.authorize_button.place(x=0, y=0)

            self.welcome_label = tk.Label(self.master, text=f"Welcome {self.user_name}!", font=("",16, "bold"), background="white")
            self.welcome_label.place(x=300, y=75)

            self.recs_button = tk.Button(self.master, text="Song\nRecommendations: ", background="darkgray", borderwidth=5)
            self.recs_button['command'] = self.recs_button_clicked
            self.recs_button.place(x=450, y=150, width="200", height="200")

            self.recs_label = tk.Label(self.recs_frame, text=f"{self.user_name}'s recommendations:", font=("",16, "bold"), background="white")
            self.recs_label.pack(pady=20)

            self.back_button2 = tk.Button(self.recs_frame, text="Back", command=self.show_main_frame, background="white")
            self.back_button2.place(x=0, y=0)

            self.recs_frame.place_forget()

            self.app = Flask(__name__)
            self.setup_routes()
            threading.Thread(target=self.run_flask, daemon=True).start()

            self.recs_frame.place_forget()
            self.show_main_frame()

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
            self.num_tracks_var = tk.StringVar()
            self.num_tracks_entry = tk.Entry(self.genre_recs_frame, textvariable=self.num_tracks_var)
            self.num_tracks_entry.pack()
            tk.Label(self.genre_recs_frame, text="Genre:").pack()
            self.genre_var = tk.StringVar()
            self.genre_entry = tk.Entry(self.genre_recs_frame, textvariable=self.genre_var)
            self.genre_entry.pack()
            generate_recommendations_button = tk.Button(self.genre_recs_frame, text="Generate Recommendations")
            generate_recommendations_button['command'] = self.generate_genre_recommendations
            generate_recommendations_button.pack(pady=10)
            self.genre_recs_genres = tk.Label(self.genre_recs_frame, text="", font=("", 12, "bold"), background="white")
            self.genre_recs_genres.pack(pady=10)
            self.results_listbox = tk.Listbox(self.genre_recs_frame, width=70, height=15)
            self.results_listbox.pack(pady=20)
            tk.Label(self.genre_recs_frame, text="Playlist Name:").pack()
            self.playlist_name_option2_var = tk.StringVar()
            self.playlist_name_option2 = tk.Entry(self.genre_recs_frame, textvariable=self.playlist_name_option2_var)
            self.playlist_name_option2.pack()
            self.add_to_playlist_button = tk.Button(self.genre_recs_frame, text="Add to Playlist", state="disabled")
            self.add_to_playlist_button['command'] = lambda: self.add_to_playlist(self.playlist_name_option.get())
            self.add_to_playlist_button.pack(pady=10)
            self.clear_button = tk.Button(self.genre_recs_frame, text="Clear")
            self.clear_button['command'] = self.clear_genre_recs_widgets
            self.clear_button.place(x=750, y=0)


            tk.Label(self.user_recs_frame, text="Time-Range:").pack()
            self.time_range_options = ["short_term", "medium_term", "long_term"]
            self.selected_time_range_option = tk.StringVar()
            self.time_range_dropdown = tk.OptionMenu(self.user_recs_frame, self.selected_time_range_option, *self.time_range_options)
            self.time_range_dropdown.pack()
            tk.Label(self.user_recs_frame, text="Number of tracks").pack()
            self.num_tracks_var2 = tk.StringVar()
            self.num_tracks = tk.Entry(self.user_recs_frame, textvariable=self.num_tracks_var2)
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
            self.add_to_playlist_button2['command'] = lambda: self.add_to_playlist(self.playlist_name_option2.get())
            self.clear_button2 = tk.Button(self.user_recs_frame, text="Clear")
            self.clear_button2['command'] = self.clear_user_recs_widgets
            self.clear_button2.place(x=750, y=0)

            self.weather_recs_button = tk.Button(self.recs_frame, text="Weather\nRecommendations", background="green")
            self.weather_recs_button['command'] = self.show_weather_recs_frame
            self.weather_recs_button.place(x=50, y=325, width=150, height=150)
            self.weather_recs_frame = tk.Frame(self.master, background="white")
            self.weather_recs_frame.place(relwidth=1, relheight=1)
            self.back_button6 = tk.Button(self.weather_recs_frame, text="Back", command=self.show_recs_frame, background="white")
            self.back_button6.place(x=0, y=0)
            self.weather_recs_label = tk.Label(self.weather_recs_frame, text="Weather Recommendations", font=("",16, "bold"), background="white")
            self.weather_recs_label.pack(pady=20)
            self.weather_recs_name = tk.Label(self.weather_recs_frame, text="", font=("", 14, "bold"), background="white")
            self.weather_recs_name.pack(pady=20)
            self.weather_recs_genres = tk.Label(self.weather_recs_frame, text="", font=("", 12, "bold"), background="white")
            self.weather_recs_genres.pack(pady=10)
            self.weather_recs_listbox = tk.Listbox(self.weather_recs_frame, width=70, height=15)
            self.weather_recs_listbox.pack(pady=20)
            self.generate_weather_button = tk.Button(self.weather_recs_frame, text="Generate Recommendations")
            self.generate_weather_button.pack()
            self.generate_weather_button['command'] = self.generate_weather_recs
            self.add_to_playlist_button3 = tk.Button(self.weather_recs_frame, text="Add to Playlist", state="disabled")
            self.add_to_playlist_button3.pack(pady=10)
            self.add_to_playlist_button3['command'] = self.add_to_playlist

            self.seasonal_recs_button = tk.Button(self.recs_frame, text="Seasonal Recs", background="green")
            self.seasonal_recs_button['command'] = self.show_seasonal_recs_frame
            self.seasonal_recs_button.place(x=300, y=325, width=150, height=150)
            self.seasonal_recs_frame = tk.Frame(self.master, background="white")
            self.seasonal_recs_frame.place(relwidth=1, relheight=1)
            self.seasonal_recs_back_button = tk.Button(self.seasonal_recs_frame, text="Back", command=self.show_recs_frame, background="white")
            self.seasonal_recs_back_button.place(x=0, y=0)
            tk.Label(self.seasonal_recs_frame, text="Seasonal Recommendations", font=("",16, "bold"), background="white").pack(pady=20)
            self.seasonal_recs_name = tk.Label(self.seasonal_recs_frame, text="", font=("", 14, "bold"), background="white")
            self.seasonal_recs_name.pack(pady=20)
            self.seasonal_recs_listbox = tk.Listbox(self.seasonal_recs_frame, width=70, height=15)
            self.seasonal_recs_listbox.pack(pady=20)
            self.generate_seasonal_button = tk.Button(self.seasonal_recs_frame, text="Generate Recommendations")
            self.generate_seasonal_button.pack()
            self.generate_seasonal_button['command'] = self.generate_seasonal_recs
            self.add_to_playlist_button4 = tk.Button(self.seasonal_recs_frame, text="Add to Playlist", state="disabled")
            self.add_to_playlist_button4.pack(pady=10)
            self.add_to_playlist_button4['command'] = self.add_to_playlist

            self.final_recs_button = tk.Button(self.recs_frame, text="BLANK", background="green")
            self.final_recs_button.place(x=550, y=325, width=150, height=150)

            self.seasonal_recs_frame.place_forget()
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
                try:
                    print("[DEBUG] Callback hit!")
                    code = request.args.get("code")

                    if code:
                        print(f"[DEBUG] Authorization code: {code}")
                        token_info = self.spotify_auth.get_access_token(code)
                        if not token_info:
                            token_info = self.spotify_auth.get_access_token(code)
                        if token_info:
                            print(f"[DEBUG] Access token: {token_info}")
                            return "Authentication successful, you can close the browser"
                    return f"[ERROR] No authentication code received", 400
                except Exception as e:
                    print("[ERROR] Callback error:", str(e))
                    return "[ERROR] An error occurred during authentication.", 500


        def run_flask(self):
            self.app.run(host='127.0.0.1', port=8080, debug=False)


        def authorize(self):
            auth_url = self.spotify_auth.get_auth_url()
            print(f"[DEBUG] Auth URL: {auth_url}")
            webbrowser.open_new_tab(auth_url)

            def wait_for_auth():
                timeout = 10
                interval = 0.5

                start_time = time.time()
                while time.time() - start_time < timeout:
                    self.access_token = self.spotify_auth.get_valid_token()
                    print(f"[DEBUG] access_token AFTER validation: {self.access_token}")

                    if self.access_token:
                        break
                    time.sleep(interval)

                if not self.access_token:
                    print("[ERROR] Access token is still None after waiting")
                    return

                sp = spotipy.Spotify(auth=self.access_token)
                user_info = sp.me()
                print(f"[DEBUG] User Info = {user_info}")

                self.user_name = user_info.get('display_name', 'Unknown User')
                print(f"[DEBUG] User name: {self.user_name}")

                self.welcome_label.config(text=f"Welcome {self.user_name}!", background="white")
                self.recs_label.config(text=f"{self.user_name}'s recommendations: ", font=("",16, "bold"), background="white")

                self.recs_button.config(state=tk.NORMAL)

                print(f"[ERROR] Access token in authorize: {self.access_token}")
                if self.access_token:
                    self.recs = Recommendations(self.access_token, self.last_fm_key)
                    print("[DEBUG] Recommendations object created:", self.recs)
                    self.authorize_button.config(state=tk.DISABLED, background="grey")
                else:
                    print("[ERROR] Access token is missing, recommendations cannot be created.")

            wait_for_auth()


        def generate_genre_recommendations(self):
            if not self.recs:
                messagebox.showerror("Error", "Recs not loaded, please authorize first.")
                return
            print(f"[DEBUG] Access token in recommendations: {self.access_token}")
            genre = self.genre_entry.get().strip().lower()
            limit = int(self.num_tracks_entry.get())
            recommendations, uris, genres = self.recs.last_fm_genres(genre, limit)
            print(f"[DEBUG] Recommendations returned: {recommendations}")
            print(f"[DEBUG] URIs returned: {uris}")

            self.current_track_uris = uris

            self.results_listbox.delete(0, tk.END)

            for idx, rec in enumerate(recommendations, start=1):
                self.results_listbox.insert(tk.END, f"{idx}. {rec}")

            self.add_to_playlist_button.config(state=tk.NORMAL)
            self.add_to_playlist_button2.config(state=tk.NORMAL)
            self.genre_recs_genres.config(text=genres)

        def generate_user_recs(self):
            if not self.recs:
                messagebox.showerror("Error", "Recommendations not loaded. Please authorize again.")
                return

            try:
                top_artist_limit = 10
                similar_artist_limit = 5
                total_tracks_limit = int(self.num_tracks.get())
                selected_time_range_option_value = self.selected_time_range_option.get()
                results, uris = self.recs.user_top_recs(top_artist_limit, similar_artist_limit, total_tracks_limit,selected_time_range_option_value)
                self.current_track_uris = uris

                if total_tracks_limit > 40:
                    messagebox.showerror("Error", "No more than 40 tracks can be generated at once.")
                    total_tracks_limit = 40


                self.results_listbox2.delete(0, tk.END)

                self.results_listbox2.config(yscrollcommand = self.scrollbar.set)
                self.scrollbar.config(command = self.results_listbox2.yview)

                for idx, rec in enumerate(results, start=1):
                    self.results_listbox2.insert(tk.END, f"{idx}. {rec}")

                self.add_to_playlist_button.config(state=tk.NORMAL)
                self.add_to_playlist_button2.config(state=tk.NORMAL)
            except AttributeError:
                print("[ERROR] No recommendations object has been created.")
                messagebox.showerror("Error", "Recommendations not loaded. Please authorize again.")


        def generate_weather_recs(self):
            recommendations, uris, weather_playlist_name, genre_string = self.recs.weather_recs(self.OPEN_WEATHER_KEY)
            self.current_track_uris = uris
            self.weather_playlist_name = weather_playlist_name
            self.genres = genre_string

            self.weather_recs_listbox.delete(0, tk.END)

            for idx, rec in enumerate(recommendations, start=1):
                self.weather_recs_listbox.insert(tk.END, f"{idx}. {rec}")

            self.add_to_playlist_button.config(state=tk.NORMAL)
            self.add_to_playlist_button2.config(state=tk.NORMAL)
            self.add_to_playlist_button3.config(state=tk.NORMAL)
            self.weather_recs_name.config(text=weather_playlist_name)
            self.weather_recs_genres.config(text=self.genres)

            return weather_playlist_name, genre_string

        def generate_seasonal_recs(self):
            recommendations, uris, playlist_name = self.recs.seasonal_recs()
            self.current_track_uris = uris
            self.seasonal_playlist_name = playlist_name

            self.seasonal_recs_listbox.delete(0, tk.END)

            for idx, rec in enumerate(recommendations, start=1):
                self.seasonal_recs_listbox.insert(tk.END, f"{idx}. {rec}")

            self.add_to_playlist_button4.config(state=tk.NORMAL)
            self.seasonal_recs_name.config(text=playlist_name)

            return self.seasonal_playlist_name


        def add_to_playlist(self, playlist_name):
            playlist_name1 = self.playlist_name_option.get().strip()
            playlist_name2 = self.playlist_name_option2.get().strip()
            playlist_name3 = "IDK" #MEANT TO BE SEASONAL PLAYLIST NAME
            # playlist_name3 = self.weather_playlist_name

            if playlist_name1:
                playlist_name = playlist_name1
            elif playlist_name2:
                playlist_name = playlist_name2
            elif playlist_name3:
                playlist_name = playlist_name3
            else:
                messagebox.showerror("Error", "Please enter a playlist name.")
                return

            print([f"[DEBUG] Playlist name: {playlist_name}"])

            sp = spotipy.Spotify(auth=self.access_token)
            user_id = sp.current_user()['id']

            playlist = sp.user_playlist_create(
                user=user_id,
                name=playlist_name,
                public=True,
                description="Created by Lucy's Song recommendation system"
            )

            print(f"[DEBUG] Created playlist: {playlist['name']}")

            for i in range(0, len(self.current_track_uris), 100):
                chunk = self.current_track_uris[i:i + 100]
                sp.playlist_add_items(playlist_id=playlist['id'], items=chunk)

            print(f"[DEBUG] Added tracks to playlist successfully")

            messagebox.showinfo(title="Playlist Creation", message=f"{playlist['name']} created successfully")

        def clear_genre_recs_widgets(self):
            self.results_listbox.delete(0, tk.END)
            self.num_tracks_var.set("")
            self.genre_var.set("")
            self.playlist_name_option2_var.set("")
            self.genre_recs_genres.config(text="")

        def clear_user_recs_widgets(self):
            self.results_listbox2.delete(0, tk.END)
            self.num_tracks_var2.set("")
            self.selected_time_range_option.set("")

        def recs_button_clicked(self):
            self.master.configure(bg="white")
            self.hide_main_frame()
            self.recs_frame.place(relwidth=1, relheight=1)

        def user_recs_button_clicked(self):
            self.master.configure(bg="white")
            self.hide_recs_frame()
            self.user_recs_frame.place(relwidth=1, relheight=1)

        def genre_button_clicked(self):
            self.master.configure(bg="white")
            self.hide_recs_frame()
            self.genre_recs_frame.place(relwidth=1, relheight=1)

        def albums_button_clicked(self):
            self.master.configure(bg="white")
            self.hide_recs_frame()
            self.albums_frame.place(relwidth=1, relheight=1)

            album = self.recs.album_chooser()

            name = album['name']
            artist = ", ".join(artist['name'] for artist in album['artists'])
            image_url = album['images'][0]['url'] if album['images'] else None

            self.album_name_label = tk.Label(self.albums_frame, text=f"{name} by\n{artist}", bg="white", font=("", 16, "bold"))
            self.album_name_label.place(x=270, y=100)

            img_data = requests.get(image_url).content
            img = Image.open(BytesIO(img_data)).resize((300, 300))
            photo = ImageTk.PhotoImage(img)

            image_label = tk.Label(self.albums_frame, image=photo, bg="white")
            image_label.image = photo
            image_label.place(x=250, y=170)

        def hide_main_frame(self):
            self.authorize_button.place_forget()
            self.welcome_label.place_forget()
            self.recs_button.place_forget()

        def hide_recs_frame(self):
            self.recs_frame.place_forget()

        def show_seasonal_recs_frame(self):
            self.master.configure(bg="white")
            self.hide_recs_frame()
            self.seasonal_recs_frame.place(relwidth=1, relheight=1)

        def show_recs_frame(self):
            self.weather_recs_frame.place_forget()
            self.genre_recs_frame.place_forget()
            self.albums_frame.place_forget()
            self.user_recs_frame.place_forget()
            self.seasonal_recs_frame.place_forget()
            self.authorize_button.place(x=0, y=0)
            self.recs_frame.place(relwidth=1, relheight=1)

        def show_weather_recs_frame(self):
            self.master.configure(bg="white")
            self.hide_recs_frame()
            self.weather_recs_frame.place(relwidth=1, relheight=1)

        def show_main_frame(self):
            self.recs_frame.place_forget()
            self.authorize_button.place(x=0, y=0)
            self.welcome_label.place(x=300, y=75)
            self.recs_button.place(x=450, y=150, width=200, height=200)

        def refresh_random_album(self):
            if self.recs is None:
                print("[ERROR] Recommendations not loaded yet, authorize first.")
                return None
            self.album_name_label.config(text="")
            self.albums_button_clicked()