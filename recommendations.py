import spotipy, random, requests, datetime
from dotenv import load_dotenv
from datetime import date
from collections import defaultdict

load_dotenv(dotenv_path='.env')


class Recommendations():
    def __init__(self,access_token, last_fm_key):
        self.sp = spotipy.Spotify(auth=access_token)
        self.access_token = access_token
        self.last_fm_api_key = last_fm_key

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

        weighted_similar_artists = defaultdict(int)
        artist_to_similars = {}

        for rank, top_artist in enumerate(top_artist_names):
            weight = top_artist_limit - rank #higher rank = more weight
            url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist={top_artist}&api_key={self.last_fm_api_key}&format=json"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                similars = data.get("similarartists", {}).get("artist", [])
                sim_names = [sim['name'] for sim in similars]
                artist_to_similars[top_artist] = sim_names
                for name in sim_names:
                    weighted_similar_artists[name] += weight
            else:
                print(f"[WARNING] Failed to get simialr artists for {top_artist}")

        sorted_similars = sorted(weighted_similar_artists.items(), key=lambda x: x[1], reverse=True)
        similar_artists = [name for name, _ in sorted_similars]

        must_include_artists = set()
        for sim_list in artist_to_similars.values():
            if sim_list:
                must_include_artists.add(sim_list[0])

        final_similar_artists = list(must_include_artists)
        for artist in similar_artists:
            if artist not in final_similar_artists:
                final_similar_artists.append(artist)
            if len(final_similar_artists) >= top_artist_limit * 2:
                break

        print(f"[DEBUG] Final similar artists: {final_similar_artists}")


        recommended_tracks = []
        seen_track_uris = set()
        tracks_per_artist = max(total_tracks_limit // len(final_similar_artists), 1)

        for artist_name in final_similar_artists:
            print(f"[DEBUG] Searching for artist on Spotify {artist_name}")
            search_results = self.sp.search(q=artist_name, type='artist', limit=1)
            print(f"[DEBUG] Spotify search result FOR {artist_name}: {search_results}")

            if search_results['artists']['items']:
                artist_id = search_results['artists']['items'][0]['id']
                print(f"[DEBUG] Artist ID for {artist_name}: {artist_id}")

                top_tracks = self.sp.artist_top_tracks(artist_id)['tracks']
                print(f"[DEBUG] Top tracks for {artist_name}: {top_tracks}")

                selected = 0
                for track in top_tracks:
                    if track['uri'] not in seen_track_uris and selected < tracks_per_artist:
                        recommended_tracks.append(track)
                        seen_track_uris.add(track['uri'])
                        selected += 1
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

    def last_fm_genres(self, genre, limit):
        def get_similar_genres(main_genre):
            url = 'http://ws.audioscrobbler.com/2.0/'
            params = {
                'method': 'tag.getSimilar',
                'tag': main_genre,
                'api_key': self.last_fm_api_key,
                'format': 'json'
            }

            try:
                response = requests.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    similar = data.get('similartags', {}).get("tag", [])
                    if similar:
                        return [tag['name'] for tag in similar]
            except Exception as e:
                print(f"[ERROR] Exception while getting last fm genres: {e}")

            fallback_similar = {
                "metal": ["death metal", "heavy metal", "thrash metal", "metalcore", "black metal", "emo"],
                "punk": ["anarcho punk", "punk rock", "hardcore punk", "crust", "hardcore"],
                "rock": ["alternative", "hard rock", "classic rock"],
                "hardcore": ["post-hardcore", "melodic hardcore", "hardcore punk", "beatdown hardcore"],
                "emo": ["post-hardcore", "screamo", "pop-punk"],
                "indie": ["indie rock", "indie pop", "alternative", "folk", "pop", "britpop"],
                "house": ["electronic", "dance", "deep house", "techno", "electro", "progressive house"],
                "jazz": ["instrumental", "piano", "smooth jazz", "swing", "saxophone"],
                "blues": ["blues rock", "rock", "jazz", "guitar", "soul", "classic rock"]

            }



            print(f"[DEBUG] Using fallback for genre {main_genre}")
            return fallback_similar.get(main_genre.lower(), [])


        similar_genres = get_similar_genres(genre)
        random.shuffle(similar_genres)
        similar_genres = similar_genres[:2]
        print(f"[DEBUG] Similar genres to '{genre}': {similar_genres}")
        genres = [genre] + similar_genres
        print(f"[DEBUG] Genres: {genres}")

        genre_string = ", ".join(genres)

        top_tracks = []
        uris = []
        seen_tracks = set()
        seen_artists = set()
        all_artists = []
        url = 'http://ws.audioscrobbler.com/2.0/'

        for genre in genres:
            params = {
                'method': 'tag.getTopArtists',
                'tag': genre,
                'api_key': self.last_fm_api_key,
                'format' : 'json',
                'limit': limit
            }

            print("[DEBUG] Calling Last.fm API for top artists...")
            top_artists_response = requests.get(url, params=params)

            print(f"[DEBUG] Full request URL: {top_artists_response.url}")
            print(f"[DEBUG] Status code: {top_artists_response.status_code}")
            print(f"[DEBUG] Response text: {top_artists_response.text}")

            if top_artists_response.status_code != 200:
                print(f"[ERROR] Failed to get top artists for {genre}")
                return [], [], ""

            try:
                artists_data = top_artists_response.json()
                artist_objs = artists_data.get('topartists', {}).get('artist', [])
                for a in artist_objs:
                    name = a.get('name')
                    if name and name not in seen_artists:
                        all_artists.append(name)
                        seen_artists.add(name)
            except Exception as e:
                print(f"[ERROR] Parsing artist response failed: {e}")
                continue

            print(f"[DEBUG] Total unique artists: {len(all_artists)}")

        random.shuffle(all_artists)
        for artist_name in all_artists:
            print(f"[DEBUG] Getting top track for {artist_name}")

            track_params = {
                'method': 'artist.getTopTracks',
                'artist': artist_name,
                'api_key': self.last_fm_api_key,
                'format': 'json',
                'limit': 5
            }

            try:
                track_response = requests.get(url, params=track_params)
                if track_response.status_code != 200:
                    print(f"[ERROR] Failed to get top track for {artist_name}")
                    continue

                track_data = track_response.json()
                tracks = track_data.get('toptracks', {}).get('track', [])
                if isinstance(tracks, dict):
                    tracks = [tracks]

                if tracks:
                    chosen_track = random.choice(tracks)
                    track_name = chosen_track.get('name')
                    if not track_name:
                        continue

                    track_id = f"{track_name.lower()} by {artist_name.lower()}"
                    if track_id in seen_tracks:
                        continue

                    seen_tracks.add(track_id)
                    top_tracks.append(f"{track_name} by {artist_name}")

                    query = f"{track_name} {artist_name}"
                    print(f"[DEBUG] Query: {query}")
                    result = self.sp.search(q=query, type='track', limit=5)
                    items = result['tracks']['items']
                    if items:
                        items.sort(key=lambda x: x['popularity'], reverse=True)
                        uri = items[0]['uri']
                        uris.append(uri)

            except Exception as e:
                print(f"[ERROR] Exception while getting top tracks for {artist_name}")
                continue

            if len(top_tracks) >= limit:
                return top_tracks[:limit], uris[:limit], genre_string

        return top_tracks[:limit], uris[:limit], genre_string

    def album_chooser(self):
        saved_albums = self.sp.current_user_saved_albums(limit=50)
        albums = saved_albums['items']
        if not albums:
            return None
        chosen  = random.choice(albums)['album']
        return chosen

    def seasonal_recs(self):
        hour = datetime.datetime.now().hour
        if 5 <= hour < 12:
            tod = "morning"
        elif 12 <= hour < 18:
            tod = "afternoon"
        elif 18 <= hour < 21:
           tod = "evening"
        else:
            tod = "night"

        month = datetime.datetime.now().month
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

        return recommendations, uris, playlist_name

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
        genre_string = ", ".join(genre)

        return recommendations, uris, playlist_name, genre_string

    def time_capsule(self):
        short_term = self.sp.current_user_top_tracks(limit=15, time_range='short_term')
        medium_term = self.sp.current_user_top_tracks(limit=15, time_range='medium_term')
        long_term = self.sp.current_user_top_tracks(limit=15, time_range='long_term')
        return short_term, medium_term, long_term