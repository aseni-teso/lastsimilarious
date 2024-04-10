import os
import argparse
import requests
import subprocess
import configparser
import time
import hashlib
import pylast
import mpv
import json
import random

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from collections import OrderedDict

load_dotenv()
api_key = os.getenv("LASTFM_API_KEY")
api_secret = os.getenv("LASTFM_API_SECRET")
username = os.getenv("username")
password = os.getenv("password")

parser = argparse.ArgumentParser(description='Last.fm audio player')
parser.add_argument('-n', '--track', metavar='TRACK', help='Search by track')
parser.add_argument('-b', '--album', metavar='ALBUM', help='Search by album')
parser.add_argument('-a', '--artist', metavar='ARTIST', help='Search by artist')
parser.add_argument('-g', '--tag', metavar='TAG', help='Search by tag')
parser.add_argument('-u', '--user', metavar='USER', help='Search by user')
args = parser.parse_args()

played_tracks = OrderedDict()

INVIDIOUS_MIRRORS_URLS = [
        'https://invidious.privacyredirect.com',
        'https://inv.oikei.net',
        'https://inv.us.projectsegfau.lt',
        'https://yewtu.be',
        'https://inv.us.projectsegfau.lt'
        ]

def get_network():
    session_key = get_or_generate_session_key()
    network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret, session_key=session_key)
    return network

def search_track(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=track.search"
    params = {
            "api_key": api_key,
            "track": query,
            "format": "json"
            }
    print("\nSearching track... ")
    response = requests.get(url, params=params).json()
    track = response['results']['trackmatches']['track'][0]
    print("OK")
    return track

def search_album(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=album.search"
    params = {
            "api_key": api_key,
            "album": query,
            "format": "json"
            }
    print("\nSearching album... ")
    response = requests.get(url, params=params).json()
    album = response['results']['albummatches']['album'][0]
    print("OK")
    return album

def search_artist(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=artist.search"
    params = {
            "api_key": api_key,
            "artist": query,
            "format": "json"
            }
    print("\nSearching artist... ")
    response = requests.get(url, params=params).json()
    artist = response['results']['artistmatches']['artist'][0]
    print("OK")
    return artist

def search_tag(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=tag.search"
    params = {
            "api_key": api_key,
            "tag": query,
            "format": "json"
            }
    print("\nSearching tag... ")
    response = requests.get(url, params=params).json()
    tag = response['results']['tagmatches']['tag'][0]
    print("OK")
    return tag

def add_to_played_tracks(artist, track, scrobbled):
    key = f"{artist} - {track}"
    if key in played_tracks:
        played_tracks[key] += 1
    else:
        played_tracks[key] = 1

    if not scrobbled:
        if key in played_tracks:
            played_tracks.move_to_end(key, last=False)
        else:
            played_tracks[key] = 1

def get_previous_track():
    if len(played_tracks):
        keys = list(played_tracks.keys())
        previous_key = keys[-1]
        previous_value = played_tracks[previous_key]
        artist, track = previous_key.split(" - ")

        data = {
                'name': track,
                'artist': artist
                }
        json_data = json.dumps(data)
        return json_data
    else:
        return None

def scrobble_track(artist, track):
    network = get_network()
    try:
        network.scrobble(artist=artist, title=track, timestamp=int(time.time()))
    except pylast.WSError as e:
        print(f"Ошибка: {e}")
        return None
    return "Success"

def update_now_playing(artist, track):
    network = get_network()
    try:
        network.update_now_playing(artist=artist, title=track) 
    except pylast.WSError as e:
        print(f"Ошибка: {e}")
        return None
    return "Success"

def add_to_loved_tracks(artist, track):
    network = get_network()
    try:
        track_object = network.get_track(artist=artist, title=track) 
        track_object.love()
    except pylast.WSError as e:
        print(f"Ошибка: {e}")
        return None
    return "Success"

def users_track_info(artist, track):
    network = get_network()
    track = pylast.Track(artist=artist, title=track, network=network, username=username)

    loved = track.get_userloved()
    assert loved is not None
    assert isinstance(loved, bool)
    assert not isinstance(loved, str)

    count = track.get_userplaycount()

    print(f"You listen this track {count} times.")
    if loved:
        print("You LOVE this track.")
        return
    return

def play_track(track):
    track_url = get_track_url(track)
    while True:
        if isinstance(track.get('artist'), dict):
            artist_name = track['artist'].get('name', '')
        else:
            artist_name = track.get('artist', '')
        print("Artist: ", artist_name)
        print("Track: ", track['name'])
        player = mpv.MPV(ytdl=True, video=False, terminal=True, input_default_bindings=True, input_terminal=True)

        @player.on_key_press('q')
        def my_q_binding():
            nonlocal track_finished
            track_finished = True
            print("\nTrack aborted. Next...")

        @player.on_key_press('Shift+q')
        def my_shift_q_binding():
            player.command('stop')
            player.command('quit')
            print("\nExiting...")
            time.sleep(0.1)
            os._exit(0)

        @player.on_key_press('l')
        def my_l_binding():
            response = input("\nAdd track to loved tracks? (y/n): ")
            if response.lower() == "y":
                add_to_loved_tracks(artist_name, track['name'])
                print("\nTrack added to loved tracks.")
            else:
                print("\nCanceled.")

        player.play(track_url)
        playing = True
        scrobbled = False
        track_finished = False
        users_track_info(artist_name, track['name'])

        add_to_played_tracks(artist_name, track['name'], scrobbled)
        print(played_tracks)
        if not scrobbled:
            previous_track = get_previous_track()
            similar_track = search_similar_track(previous_track)
        else:
            similar_track = search_similar_track(track)
        if similar_track:
            track_url = get_track_url(similar_track)

        while playing:
            update_now_playing(artist_name, track['name'])
            if track_finished:
                break
            if player.duration and player.duration != 'None':
                if player.time_pos >= float(player.duration) * 0.5 or player.time_pos >= 180:
                    if not scrobbled:
                        print("\nScrobbling... ")
                        scrobble_track(artist_name, track['name'])
                        print("OK")
                        scrobbled = True

                if player.time_pos >= float(player.duration) - 3:
                    if not track_finished:
                        track_finished = True
            
            if not player.metadata and player.eof_reached:
                print("Not metadata")
                player.terminate()
                break

            time.sleep(1)

        if track_finished:
            track = similar_track
        else:
            break

        player.terminate()

def is_video_available(url):
    try:
        output = subprocess.check_output(['yt-dlp', '--ignore-errors', '--skip-download', url], stderr=subprocess.DEVNULL)
        output = output.decode('utf-8')
        if 'Video unavailable' in output:
            return False
        return True
    except subprocess.CalledProcessError:
        return False

def get_track_url(track):
    track_name = track.get('name', '')
    if isinstance(track.get('artist'), dict):
        artist_name = track['artist'].get('name', '')
    else:
        artist_name = track.get('artist', '')

    search_query = f'{track_name} {artist_name}'
    search_query = '+'.join(search_query.split())
    for mirror_url in INVIDIOUS_MIRRORS_URLS:
        search_url = f'{mirror_url}/search?q={search_query}'
        print("\nSearching url... ")
        response = requests.get(search_url)
        print("OK")

        soup = BeautifulSoup(response.text, 'html.parser')
        video_link = soup.find('a', href=lambda href: href.startswith('/watch?v='))
        while video_link:
            video_url = f'https://www.youtube.com{video_link["href"]}'
            print("\nChecking url... ")
            if is_video_available(video_url):
                print("OK")
                return video_url
            print("Failed. Trying now... ")
            video_link = video_link.find_next('a', href=lambda href: href.startswith('/watch?v='))
    return None

def play_album(album):
    track_list = get_album_tracks(album)
    for track in track_list:
        track_url = get_track_url(track)
        if isinstance(track.get('artist'), dict):
            artist_name = track['artist'].get('name', '')
        else:
            artist_name = track.get('artist', '')
        print("Artist: ", artist_name)
        print("Track: ", track['name'])
        subprocess.run(['mpv', '--no-video', '--no-sub', track_url])
        session_key = get_or_generate_session_key()
        scrobble_track(artist_name, track['name'])

def get_album_tracks(album):
    album_search_url = "http://ws.audioscrobbler.com/2.0/?method=album.search"
    params = {
            "api_key": api_key,
            "artist": album['artist'],
            "album": album['name'],
            "format": "json"
            }
    search_response = requests.get(album_search_url, params=params).json()
    album_matches = search_response.get('results', {}).get('albummatches', {}).get('album', [])
    if album_matches:
        album_info = album_matches[0]
        album_info_url = "http://ws.audioscrobbler.com/2.0/?method=album.getInfo"
        album_params = {
                "api_key": api_key,
                "artist": album_info['artist'],
                "album": album_info['name'],
                "format": "json"
                }
        info_response = requests.get(album_info_url, params=album_params).json()
        track_list = info_response['album']['tracks']['track']

        return track_list
    else:
        return None

def play_artist_tracks(artist):
    track_list = get_artist_tracks(artist)
    for track in track_list:
        track_url = get_track_url(track)
        if isinstance(track.get('artist'), dict):
            artist_name = track['artist'].get('name', '')
        else:
            artist_name = track.get('artist', '')
        print("Artist: ", artist_name)
        print("Track: ", track['name'])
        subprocess.run(['mpv', '--no-video', '--no-sub', track_url])
        session_key = get_or_generate_session_key()
        scrobble_track(artist_name, track['name'])

def play_artist_albums(artist):
    album_list = get_artist_albums(artist)
    for album in album_list:
            play_album(album)

def get_artist_tracks(artist):
    url = "http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks"
    params = {
            "api_key": api_key,
            "artist": artist['name'],
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    track_list = response['toptracks']['track']
    return track_list

def get_artist_albums(artist):
    url = "http://ws.audioscrobbler.com/2.0/?method=artist.gettopalbums"
    params = {
            "api_key": api_key,
            "artist": artist['name'],
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    album_list = response['topalbums']['album']
    return album_list

def play_tag(tag):
    track_list = get_popular_tracks_by_tag(tag)
    for track in track_list:
        track_url = get_track_url(track)
        if isinstance(track.get('artist'), dict):
            artist_name = track['artist'].get('name', '')
        else:
            artist_name = track.get('artist', '')
        print("Artist: ", artist_name)
        print("Track: ", track['name'])
        subprocess.run(['mpv', '--no-video', '--no-sub', track_url])
        session_key = get_or_generate_session_key()
        scrobble_track(artist_name, track['name'])

def play_user(user):
    track_list = get_popular_tracks_by_user(user)
    for track in track_list:
        track_url = get_track_url(track)
        if isinstance(track.get('artist'), dict):
            artist_name = track['artist'].get('name', '')
        else:
            artist_name = track.get('artist', '')
        print("Artist: ", artist_name)
        print("Track: ", track['name'])
        subprocess.run(['mpv', '--no-video', '--no-sub', track_url])
        session_key = get_or_generate_session_key()
        scrobble_track(artist_name, track['name'])

def get_popular_tracks_by_tag(tag):
    url = "http://ws.audioscrobbler.com/2.0/?method=tag.gettoptracks"
    params = {
            "api_key": api_key,
            "tag": tag,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    track_list = response['tracks']['track']
    return track_list

def get_popular_tracks_by_user(user):
    url = "http://ws.audioscrobbler.com/2.0/?method=user.gettoptracks"
    params = {
            "api_key": api_key,
            "user": user,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    track_list = response['toptracks']['track']
    return track_list

def search_similar_track(track):
    url = "http://ws.audioscrobbler.com/2.0/?method=track.getsimilar"
    if isinstance(track, str):
        track = json.loads(track)
    if isinstance(track.get('artist'), dict):
        params = {
            "api_key": api_key,
            "artist": track['artist']['name'],
            "track": track['name'],
            "limit": 12,
            "format": "json"
            }
    else:
        params = {
            "api_key": api_key,
            "artist": track['artist'],
            "track": track['name'],
            "limit": 12,
            "format": "json"
            }
    print("\nSearching next track... ")
    response = requests.get(url, params=params).json()
    similar_tracks = response['similartracks']['track']

    if not similar_tracks:
        print("Fail.\nSearching similar artist... ")
        artist_params = {
                "api_key": api_key,
                "artist": params['artist'],
                "limit": 12,
                "format": "json"
                }
        similar_artist_response = requests.get("http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar", params=artist_params).json()
        similar_artists = similar_artist_response['similarartists']['artist']

        for artist in similar_artists:
            top_tracks_params = {
                "api_key": api_key,
                "artist": artist['name'],
                "limit": 6,
                "format": "json"
                }
            top_tracks_response = requests.get("http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks", params=top_tracks_params).json()
            top_tracks = top_tracks_response['toptracks']['track']

            for top_track in top_tracks:
                key = f"{top_track['artist']['name']} - {top_track['name']}"
                if key not in played_tracks:
                    print("OK")
                    return top_track

        if not similar_artists:
            random_track = get_random_loved_track()
            return random_track

    for similar_track in similar_tracks:
        key = f"{similar_track['artist']['name']} - {similar_track['name']}"
        if key not in played_tracks:
            print("OK")
            return similar_track

def get_random_loved_track():
    print("Searching random loved track... ")
    url = "http://ws.audioscrobbler.com/2.0/?method=user.getlovedtracks"
    user = username
    params = {
            "api_key": api_key,
            "user": user,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    total_pages = int(response['lovedtracks']['@attr']['totalPages'])
    random_page = random.randint(1, total_pages)
    params["page"] = random_page
    response = requests.get(url, params=params).json()
    track_list = response['lovedtracks']['track']
    random_track = random.choice(track_list)
    print("OK")
    return random_track

def get_request_token(api_key, api_secret):
    url = "http://ws.audioscrobbler.com/2.0/?method=auth.getToken"
    api_sig = hashlib.md5((f"api_key{api_key}methodauth.getToken{api_secret}").encode()).hexdigest()
    params = {
            "api_key": api_key,
            "api_sig": api_sig,
            "format": "json"
            }
    response = requests.post(url, data=params).json()
    token = response["token"]
    return token

def get_session_key(api_key, api_secret, token):
    url = "http://ws.audioscrobbler.com/2.0/?method=auth.getSession"
    api_sig = hashlib.md5((f"api_key{api_key}methodauth.getSessiontoken{token}{api_secret}").encode()).hexdigest()
    params = {
            "api_key": api_key,
            "api_sig": api_sig,
            "token": token,
            "format": "json"
            }
    response = requests.post(url, data=params).json()
    session_key = response['session']['key']
    return session_key

def get_or_generate_session_key():
    config = configparser.ConfigParser()
    config.read('config.ini')
    if config.has_option('AUTH', 'SESSION_KEY'):
        session_key = config.get('AUTH', 'SESSION_KEY')
        return session_key
    else:
        token = get_request_token(api_key, api_secret)
        auth_url = f"http://www.last.fm/api/auth?api_key={api_key}&token={token}"
        print(f"Please grant permission at: {auth_url}")
        input("Press Enter after granting permission...")
        session_key = get_session_key(api_key, api_secret, token)
        save_session_key(session_key)
        return session_key

def save_session_key(session_key):
    config = configparser.ConfigParser()
    config.read('config.ini')
    if not config.has_section('AUTH'):
        config.add_section('AUTH')
    config.set('AUTH', 'SESSION_KEY', session_key)
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def main():
    try:
        if args.track:
            track = search_track(args.track)
            play_track(track)

        elif args.album:
            album = search_album(args.album)
            play_album(album)

        elif args.artist:
            artist = search_artist(args.artist)
            display_choice = input("Play artist's tracks (1) or albums (2). Input 1 or 2: ")
            if display_choice == "1":
                play_artist_tracks(artist)
            elif display_choice == "2":
                play_artist_albums(artist)

        elif args.tag:
            tag = args.tag        
            play_tag(tag)

        elif args.user:
            user = args.user
            play_user(user)

        else:
            track = get_random_loved_track()
            play_track(track)
    except pylast.NetworkError as e:
        print("Network error:", str(e))

if __name__ == "__main__":
    main()

