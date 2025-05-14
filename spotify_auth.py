import spotipy, urllib, time, webbrowser
from spotipy import SpotifyOAuth

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
            token_info = self.sp_oauth.get_access_token(code)
            if isinstance(token_info, dict) and 'access_token' in token_info:
                self.access_token = token_info.get('access_token')
                if not self.access_token:
                    raise Exception('[DEBUG] No access token found.')
            else:
                self.access_token = token_info
            self.token_info = token_info
            print(f"[DEBUG] Access token set: {self.access_token}")
            return self.access_token
        except Exception as e:
            print("[ERROR] Failed to retreive access token:", str(e))
        return None

    def get_valid_token(self):
        try:
            if self.token_info and not self.sp_oauth.is_token_expired(self.token_info):
                return self.token_info['access_token']
            elif self.token_info:
                self.token_info = self.sp_oauth.refresh_access_token(self.token_info['refresh_token'])
                return self.token_info['access_token']
            else:
                print("[ERROR] No token info available. Please reauthorize.")
            return None
        except Exception as e:
            print(f"[ERROR] Token refresh failed: {str(e)}")
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
                    if token_info:
                        print(f"[DEBUG] Access token: {token_info['access_token']}")
                    else:
                        print("[ERROR] Token retrieval failed.")
                    webview_window.destroy()
                break
            time.sleep(1)

    def start_oauth_flow(self):
        self.token_info = self.sp_oauth.get_access_token(as_dict=True)
        if not self.token_info:
            auth_url = self.sp_oauth.get_authorize_url()
            webbrowser.open(auth_url)
            print("Please log in and paste the full redirect URL here.")
            response = input("Redirect URL: ")
            code = self.sp_oauth.parse_response_code(response)
            self.token_info = self.sp_oauth.get_access_token(code)

    def start_local_server(self):
        self.app.run(host='localhost', port=8080, debug=True)