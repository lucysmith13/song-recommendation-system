# Import Libraries
from abc import ABC, abstractmethod
import spotipy
import requests

# Import Files
from Auths import SpotifyAuth, YouTubeAuth, LastFMAuth

class APIBase(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def add_to_playlist(self, playlist_name,playlist_id, track_uris):
        pass

    @abstractmethod
    def get_user_info(self):
        pass

class SpotifyAPI(APIBase):
    def __init__(self):
        super().__init__("Spotify")
        self.SpotifyAuth = SpotifyAuth()
        self.scope = "user-read-private user-library-read user-top-read playlist-modify-public playlist-modify-private"
        self.client_id, self.client_secret, self.access_token = self.SpotifyAuth.get_credentials()
        self.spotify = spotipy.Spotify(auth=self.access_token)
        self.user_id = self.spotify.current_user()['id']

    def add_to_playlist(self, playlist_name, playlist_id, track_uris):
        if not track_uris:
            raise ValueError("trac")

        playlist = self.spotify.user_playlist_create(
            user = self.user_id,
            name = playlist_name,
            public = False,
            description = "Created by Lucy's song recommendation system."
        )

        self.spotify.playlist_add_items(playlist_id, track_uris)
        return playlist

    def get_user_info(self):
        user_id = self.spotify.current_user()['id']
        user_info = self.spotify.me()
        user_name = user_info.get('display_name', 'Unknown User')

        return user_id, user_info, user_name

class YoutubeAPI(APIBase):
    def __init__(self):
        super().__init__("Youtube")
        self.YoutubeAuth = YouTubeAuth()
        self.youtube = self.YoutubeAuth.get_credentials()
        self.video_id = None

    def set_video(self, video_id):
        self.video_id = video_id

    def add_to_playlist(self, playlist_name, playlist_id, *_):
        if not self.video_id:
            raise ValueError("No video selected, make sure to use set_video first.")

        request = self.youtube.playlistItems().insert(
            part="snippet",
            body={
                "snippet": {
                    "title": playlist_name,
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": self.video_id,
                    }
                }
            }
        )

        response = request.execute()
        return response

    def get_user_info(self):
        return "[WARNING] Youtube user info retrieval not implemented."

class LastFMAPI():
    def __init__(self):
        self.LastFMAuth = LastFMAuth()
        self.api_key = self.LastFMAuth.get_credentials()

    def find_similar_artists(self, artist):
        url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist={artist}&api_key={self.api_key}&format=json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            similars = data.get("similarartists", {}).get("artist", [])
            sim_names = [sim['name'] for sim in similars]
            return sim_names
