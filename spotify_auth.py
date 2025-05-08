from spotipy import SpotifyOAuth
import spotipy, time, urllib.parse, webbrowser, socketserver, http.server
from dotenv import load_dotenv

load_dotenv()

class SpotifyAuth():
    def __init__(self, client_id, client_secret, redirect_uri, scope):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope

        self.sp_oauth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        )
        self.token_info = None

    def get_auth_url(self):
        return self.sp_oauth.get_authorize_url()

    def get_access_token(self, code):
        try:
            token_info = self.sp_oauth.get_access_token(code, as_dict=True)
            if isinstance(token_info, dict):
                self.access_token = token_info.get('access_token')
            else:
                self.access_token = token_info

            self.token_info = token_info
            print(f"[DEBUG] Returning access_token from get_access_token: {self.access_token}")
            return self.access_token
        except spotipy.exceptions.SpotifyOAuthError as e:
            print("[ERROR] Failed to get access token:", str(e))
            return None

    def get_valid_token(self):
        if self.token_info and not self.sp_oauth.is_token_expired(self.token_info):
            return self.token_info['access_token']
        elif self.token_info:
            self.token_info = self.sp_oauth.refresh_access_token(self.token_info['refresh_token'])
            return self.token_info['access_token']
        return None

    def handle_redirect(self, webview_window):
        while True:
            current_url = webview_window.get_current_url()
            if self.redirect_uri in current_url:
                parsed_url = urllib.parse.urlparse(current_url)
                auth_code = urllib.parse.parse_qs(parsed_url.query).get("code")
                if auth_code:
                    print(f"Authorization code: {auth_code[0]}")
                    token_info = self.get_access_token(auth_code[0])
                    print(f"Access token: {token_info['access_token']}")
                    webview_window.destroy()
                break
            time.sleep(1)

    def start_oauth_flow(self):
        self.token_info = self.sp_oauth.get_cached_token()
        if not self.token_info:
            auth_url = self.sp_oauth.get_authorize_url()
            webbrowser.open(auth_url)
            print("Please log in and paste the full redirect URL here.")
            response = input("Redirect URL: ")
            code = self.sp_oauth.parse_response_code(response)
            self.token_info = self.sp_oauth.get_access_token(code)

    def start_local_server(self):
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("localhost", 8888), handler) as httpd:
            print("Server started at http://localhost:8888")
            httpd.serve_forever()