import os

import requests, spotipy, datetime, random
from flask.cli import load_dotenv
from datetime import date

load_dotenv()

class Recommendations():
    def __init__(self, stats_obj, access_token, last_fm_key):
        self.sp = spotipy.Spotify(auth=access_token)
        self.access_token = access_token
        self.last_fm_api_key = last_fm_key
        self.stats = stats_obj

    def add_to_playlist(self, playlist_name, track_uris):
        user_id = self.sp.current_user()['id']
        playlist = self.sp.user_playlist_create(
            user=user_id,
            name=playlist_name,
            public=True,
            description=None
        )
        print(f"[DEBUG] Created playlist {playlist['name']} - {playlist['external_urls']['spotify']}")

        for i in range(0, len(track_uris), 100):
            chunk = track_uris[i:i+100]
            self.sp.playlist_add_items(playlist_id=playlist['id'], items=chunk)

        print(f"[DEBUG] Added tracks to the playlist successfully")

    def user_top_recs(self,top_artist_limit, similar_artist_limit, total_tracks_limit,time_range):
        print("[DEBUG] Fetching user's top artists...")
        top_artists = self.sp.current_user_top_artists(limit=top_artist_limit, time_range=time_range)
        top_artist_names = [artist['name'] for artist in top_artists['items']]
        print(f"[DEBUG] Top artists: {top_artist_names}")

        similar_artists = set()
        for artist_name in top_artist_names:
            print(f"[DEBUG] Getting similar artists for {artist_name}")
            url = "http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist={}&api_key={}&format=json".format(
                artist_name, LAST_FM_KEY)
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    print(f"[ERROR] Failed to get similar artists for {artist_name}, Status code: {response.status_code}")
                    continue

                data = response.json()
                print(f"[DEBUG] Raw similar data: {data}")

                similar = data.get("similarartists", {}).get("artist", [])
                if similar:
                    for artist in similar[:int(similar_artist_limit)]:
                        similar_artists.add(artist["name"])
                else:
                    print("f[WARNING] No similar artists found for {artist_name}")
            except Exception as e:
                print(f"[ERROR] Exception while processing {artist_name}: {e}")

        print(f"[DEBUG] Found similar artists: {list(similar_artists)}")

        total_artists = len(similar_artists)
        if total_artists == 0:
            print("[ERROR] No similar artists found. Cannot proceed with recommendations.")
            return [], []

        tracks_per_artist = max(total_tracks_limit // total_artists, 1)

        recommended_tracks = []
        for artist_name in similar_artists:
            print(f"[DEBUG] Searching for artist on Spotify {artist_name}")
            search_results = self.sp.search(q=artist_name, type='artist', limit=1)
            print(f"[DEBUG] Spotify search result FOR {artist_name}: {search_results}")

            if search_results['artists']['items']:
                artist_id = search_results['artists']['items'][0]['id']
                print(f"[DEBUG] Artist ID for {artist_name}: {artist_id}")

                top_tracks = self.sp.artist_top_tracks(artist_id)['tracks']
                print(f"[DEBUG] Top tracks for {artist_name}: {top_tracks}")

                if top_tracks:
                    recommended_tracks.extend(top_tracks[:tracks_per_artist])
                else:
                    print(f"[WARNING] No top tracks found for artist: {artist_name}")
            else:
                print(f"[ERROR] No artist found for search query {artist_name}")

        recommended_tracks = recommended_tracks[:total_tracks_limit]
        print(f"[DEBUG] Tracks being added to recommendations: {recommended_tracks}")

        final_results = []
        final_results_uris = []
        for track in recommended_tracks:
            artist_names = ", ".join(artist['name'] for artist in track['artists'])
            final_results.append(f"{track['name']} by {artist_names}")
            final_results_uris.append(track['uri'])

        print(f"[DEBUG] Final recommended tracks: {final_results}")
        return final_results, final_results_uris

    def last_fm_genres(self, genre,limit):
        url = 'http://ws.audioscrobbler.com/2.0/'
        params = {
            'method': 'tag.gettoptracks',
            'tag': genre,
            'api_key': self.last_fm_api_key,
            'format' : 'json',
            'limit': limit
        }
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"[ERROR] Failed to get recommendations for {genre}")
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
            return []

        data = response.json()
        tracks = data.get('tracks', {}).get('track', [])
        recommendations = []
        uris = []
        for track in tracks:
            name = track.get('name')
            artist = track.get('artist', {}).get('name')
            recommendations.append(f"{name} by {artist}")
            query = f"{name} {artist}"

            result = self.sp.search(q=query, type='track', limit=limit)
            print(f"[DEBUG] Searching for track on spotify: {name} by {artist}")
            items = result['tracks']['items']
            if items:
                uri = items[0]['uri']
                uris.append(uri)
        return recommendations, uris

    def album_chooser(self):
        saved_albums = self.sp.current_user_saved_albums(limit=50)
        albums = saved_albums['items']
        if not albums:
            return None
        chosen  = random.choice(albums)['album']
        return chosen

    def seasonal_recs(self):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            tod = "morning"
        elif 12 <= hour < 18:
            tod = "afternoon"
        elif 18 <= hour < 21:
           tod = "evening"
        else:
            tod = "night"

        month = datetime.now().month
        today = date.today()

        if 3 <= month <= 5:
            season = "spring"
        elif 6 <= month <= 8:
            season = "summer"
        elif 9 <= month <= 11:
            season = "autumn"
        else:
            season = "winter"

        if today == date(today.year, 12, 25):
            #its christmas!
            genre = ["christmas"]
        if season == "spring":
            descrip = "spring-like"
            genre = ["indie-pop", "post-punk", "blues", "folk", "acoustic"]
        if season == "summer":
            descrip = "summery"
            genre = ["reggae", "jungle", "hiphop", "pop-punk", "surf rock", "house"]
        if season == "autumn":
            descrip = "autumnal"
            genre = ["grunge", "classic-rock", "emo", "indie-rock", "jazz", "neo-soul", "ambient", "lo-fi"]
        if season == "winter":
            descrip = "winterly"
            genre = ["classical", "trip-hop", "post-rock", "industrial", "death-metal"]

        random_genre = random.choice(genre)

        url = 'http://ws.audioscrobbler.com/2.0/'
        params = {
            'method': 'tag.gettoptracks',
            'tag': random_genre,
            'api_key': self.last_fm_api_key,
            'format' : 'json',
            'limit': 30
        }
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"[ERROR] Failed to get recommendations for {genre}")
            print(f"Status code: {response.status_code}")
            print(f"Response text: {response.text}")
            return []

        data = response.json()
        tracks = data.get('tracks', {}).get('track', [])
        recommendations = []
        uris = []
        for track in tracks:
            name = track.get('name')
            artist = track.get('artist', {}).get('name')
            recommendations.append(f"{name} by {artist}")
            query = f"{name} {artist}"

            result = self.sp.search(q=query, type='track', limit=30)
            print(f"[DEBUG] Searching for track on spotify: {name} by {artist}")
            items = result['tracks']['items']
            if items:
                uri = items[0]['uri']
                uris.append(uri)


        playlist_name = f"{random_genre} songs on a {descrip} {tod}"

        print(playlist_name)
        for track in recommendations:
            print(track)

        return recommendations, uris

    def weather_recs(self, OPEN_WEATHER_KEY, country_code="GB"):
        print(f"[DEBUG] Starting weather recommendations")
        city = "Wolverhampton"
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city},{country_code}&appid={OPEN_WEATHER_KEY}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"[ERROR] Failed to get weather data. Status code {response.status_code}")
            return [], []

        data = response.json()
        weather = data['weather'][0]['main'].lower()
        detailed_weather = data['weather'][0]['description'].lower()
        print(f"[DEBUG] The weather is {weather}")

        genre_mapping = {
        "thunderstorm": ['ambient', 'industrial', 'gothic', 'metal', 'alternative-rock'],
        "drizzle": ['lo-fi', 'jazz', 'indie-pop', 'soul', 'ambient'],
        "rain": ['blues', 'acoustic', 'classical', 'chillwave'],
        "snow": ['classical', 'folk', 'dream-pop', 'ambient'],
        "atmosphere": ['ambient', 'chillwave', 'synthwave', 'post-rock'],
        "clear": ['pop', 'reggae', 'house', 'funk', 'indie-rock'],
        "clouds": ['indie', 'soft-rock', 'jazz', 'dream-pop']
        }

        if detailed_weather == "tornado":
            genre = ['hard-rock', 'heavy-metal', 'industrial', 'dubstep', 'drum-and-bass']
        else:
            #defualt genre pop if not found
            genre = genre_mapping.get(weather, ['pop'])

        print(f"[DEBUG] Selected genres: {genre}")
        genre_string = ", ".join(genre)

        url = 'http://ws.audioscrobbler.com/2.0/'
        params = {
            'method': 'tag.gettoptracks',
            'api_key': self.last_fm_api_key,
            'format' : 'json',
        }

        recommendations = []
        uris = []
        tracks_per_genre = 30 // len(genre)

        for single_genre in genre:
            print(f"[DEBUG] Fetching tracks for genre: {single_genre}")
            params['tag'] = single_genre
            params['limit'] = tracks_per_genre
            response = requests.get(url, params=params)
            if response.status_code != 200:
                print(f"[ERROR] Failed to get tracks for genre {single_genre}")
                continue

            data = response.json()
            tracks = data.get('tracks', {}).get('track', [])
            if not tracks:
                print(f"[ERROR] No tracks found for genre: {single_genre}")
                continue

            count = 0

            for track in tracks:
                if count >= tracks_per_genre:
                    break

                name = track.get('name')
                artist = track.get('artist', {}).get('name')
                if not name or not artist:
                    print(f"[WARNING] Skipping track with missing name or artist.")
                recommendations.append(f"{name} by {artist}")
                query = f"{name} {artist}"
                print(f"[DEBUG] Searching for track on spotify: {name} by {artist}")
                result = self.sp.search(q=query, type='track', limit=5)
                items = result.get('tracks', {}).get('items', [])
                if items:
                    uri = items[0]['uri']
                    if uri not in uris:
                        uris.append(uri)
                        count += 1
                        if count >= tracks_per_genre:
                            break

        playlist_name = f"Songs for {weather}"
        recommendations = recommendations[:30]
        random.shuffle(recommendations)
        uris = uris[:30]
        print(f"[DEBUG] Final recommendations: {recommendations}")
        print(len(recommendations))

        return recommendations, uris, playlist_name

    def time_capsule(self):
        short_term = self.sp.current_user_top_tracks(limit=15, time_range='short_term')
        medium_term = self.sp.current_user_top_tracks(limit=15, time_range='medium_term')
        long_term = self.sp.current_user_top_tracks(limit=15, time_range='long_term')
        return short_term, medium_term, long_term

    def genre_fusion_recs(self):
        pass