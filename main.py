import os
import argparse
import requests
import subprocess
import configparser
import time
import hashlib
import pylast

from bs4 import BeautifulSoup
from dotenv import load_dotenv

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

played_tracks = {}

def search_track(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=track.search"
    params = {
            "api_key": api_key,
            "track": query,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    track = response['results']['trackmatches']['track'][0]
    return track

def search_album(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=album.search"
    params = {
            "api_key": api_key,
            "album": query,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    album = response['results']['albummatches']['album'][0]
    print(album)
    return album

def search_artist(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=artist.search"
    params = {
            "api_key": api_key,
            "artist": query,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    artist = response['results']['artistmatches']['artist'][0]
    return artist

def search_tag(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=tag.search"
    params = {
            "api_key": api_key,
            "tag": query,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    tag = response['results']['tagmatches']['tag'][0]
    return tag

def add_to_played_tracks(artist, track):
    key = f"{artist} - {track}"
    if key in played_tracks:
        played_tracks[key] += 1
    else:
        played_tracks[key] = 1

def scrobble_track(artist, track, session_key):
    network = pylast.LastFMNetwork(api_key=api_key, api_secret=api_secret, session_key=session_key)
    try:
        network.scrobble(artist=artist, title=track, timestamp=int(time.time()))
    except pylast.WSError as e:
        print(f"Ошибка: {e}")
        return None
    return "Success"

def play_track(track):
    track_url = get_track_url(track)
    if isinstance(track.get('artist'), dict):
        artist_name = track['artist'].get('name', '')
    else:
        artist_name = track.get('artist', '')
    print("Artist: ", artist_name)
    print("Track: ", track['name'])
    subprocess.run(['mpv', '--no-video', '--no-sub', track_url])
    add_to_played_tracks(artist_name, track['name'])
    session_key = get_or_generate_session_key()
    scrobble_track(artist_name, track['name'], session_key)
    similar_track = search_similar_track(track)
    play_track(similar_track)

def get_track_url(track):
    track_name = track.get('name', '')

    if isinstance(track.get('artist'), dict):
        artist_name = track['artist'].get('name', '')
    else:
        artist_name = track.get('artist', '')

    search_query = f'{track_name} {artist_name}'
    search_query = '+'.join(search_query.split())
    search_url = f'https://inv.oikei.net/search?q={search_query}'
    response = requests.get(search_url)

    soup = BeautifulSoup(response.text, 'html.parser')
    video_link = soup.find('a', href=lambda href: href.startswith('/watch?v='))
    if video_link:
        video_url = f'https://www.youtube.com{video_link["href"]}'
        return video_url
    else:
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
        scrobble_track(artist_name, track['name'], session_key)

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
        scrobble_track(artist_name, track['name'], session_key)

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
        scrobble_track(artist_name, track['name'], session_key)

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
        scrobble_track(artist_name, track['name'], session_key)

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
    response = requests.get(url, params=params).json()
    similar_tracks = response['similartracks']['track']

    for similar_track in similar_tracks:
        key = f"{similar_track['artist']['name']} - {similar_track['name']}"
        if key not in played_tracks:
            return similar_track

def get_request_token(api_key, api_secret):
    url = "http://ws.audioscrobbler.com/2.0/?method=auth.getToken"
    api_sig = hashlib.md5((f"api_key{api_key}methodauth.getToken{api_secret}").encode()).hexdigest()
    params = {
            "api_key": api_key,
            "api_sig": api_sig,
            "format": "json"
            }
    response = requests.post(url, data=params).json()
    print("response: ", response)
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
    print(api_key, api_sig, token)
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

if __name__ == "__main__":
    main()

