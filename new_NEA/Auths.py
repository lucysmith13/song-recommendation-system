import os
from abc import ABC, abstractmethod
from flask.cli import load_dotenv

load_dotenv()

class AuthBase(ABC):
    def __init__(self):
        self.access_token = None

    @abstractmethod
    def authenticate(self):
        pass

    @abstractmethod
    def get_credentials(self):
        pass

class SpotifyAuth(AuthBase):
    def __init__(self):
        super().__init__()
        self.client_id = os.getenv("spotify_client_id")
        self.client_secret = os.getenv("spotify_client_secret")
        self.redirect_uri = os.getenv("redirect_uri")

        self.scope = "user-read-private user-library-read user-top-read playlist-modify-public playlist-modify-private"

    def authenticate(self, code=None):
        if not self.client_id or not self.client_secret or not self.redirect_uri:
            raise ValueError("Spotify credentials are missing")

        if code is None:
            from urllib.parse import urlencode

            params = {
                "client_id": self.client_id,
                "response_type": "code",
                "redirect_uri": self.redirect_uri,
                "scope": self.scope,
            }
            auth_url = "https://accounts.spotify.com/authorize?" + urlencode(params)
            return auth_url
        else:
            import requests
            token_url = "https://accounts.spotify.com/api/token"
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            token_info = response.json()
            self.access_token = token_info['access_token']
            return self.access_token

    def get_credentials(self):
        return self.client_id, self.client_secret, self.access_token

class YouTubeAuth(AuthBase):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("youtube_api_key")

    def authenticate(self, **kwargs):
        if not self.api_key:
            raise ValueError("YouTube API key is missing")
        self.access_token = self.api_key
        return self.access_token

    def get_credentials(self):
        return self.api_key, self.access_token

class LastFMAuth(AuthBase):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("lastfm_api_key")

    def authenticate(self, **kwargs):
        if not self.api_key:
            raise ValueError("LastFM API key is missing")
        self.access_token = self.api_key
        return self.access_token

    def get_credentials(self):
        return self.api_key

class WeatherAPI(AuthBase):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("open_weather_api_key")

    def authenticate(self, **kwargs):
        if not self.api_key:
            raise ValueError("Open Weather API key is missing")
        self.access_token = self.api_key
        return self.access_token

    def get_credentials(self):
        return self.api_key