import spotipy

class Stats():
    def __init__(self, access_token):
        self.sp = spotipy.Spotify(auth=access_token)

    def get_top_artists(self, limit, time_range):
        results = self.sp.current_user_top_artists(limit=limit, time_range=time_range)
        return [artist['name'] for artist in results['items']]

    def get_top_tracks(self, limit, time_range):
        results = self.sp.current_user_top_tracks(limit=limit, time_range=time_range)
        return [track['name'] for track in results['items']]