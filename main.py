import os
import argparse
import requests
import subprocess

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()
api_key = os.getenv("LASTFM_API_KEY")

parser = argparse.ArgumentParser(description='Last.fm audio player')
parser.add_argument('-n', '--track', metavar='TRACK', help='Search by track')
parser.add_argument('-b', '--album', metavar='ALBUM', help='Search by album')
parser.add_argument('-a', '--artist', metavar='ARTIST', help='Search by artist')
parser.add_argument('-g', '--tag', metavar='TAG', help='Search by tag')
args = parser.parse_args()

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

def play_track(track):
    track_url = get_track_url(track)
    subprocess.run(['mpv', '--no-video', track_url])

def get_track_url(track):
    print(track)
    track_name = track.get('name', '')
    artist_name = track.get('artist', {}).get('name', '')
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
        play_track(track)

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
        play_track(track)

def play_artist_albums(artist):
    album_list = get_artist_albums(artist)
    for album in album_list:
            play_album(album)

def get_artist_tracks(artist):
    url = "http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks"
    params = {
            "api_key": api_key,
            "album": artist['name'],
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    track_list = response['toptracks']['track']
    return track_list

def get_artist_albums(artist):
    url = "http://ws.audioscrobbler.com/2.0/?method=artist.gettopalbums"
    params = {
            "api_key": api_key,
            "album": artist['name'],
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    album_list = response['topalbums']['album']
    return album_list

def play_tag(tag):
    artist_list = get_popular_artists_by_tag(tag)
    print("Popular artists by tag '{}':".format(tag))
    for i, artist in enumerate(artist_list):
        print("{}. {}".format(i+1, artist["name"]))

    selection = int(input("Input artist number: "))
    selected_artist = artist_list[selection-1]

    play_artist_tracks(selected_artist)

def get_popular_artists_by_tag(tag):
    url = "http://ws.audioscrobbler.com/2.0/?method=tag.gettopartists"
    params = {
            "api_key": api_key,
            "tag": tag,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    artist_list = response['topartists']['artist'][0]
    return artist_list


def search_similar_track(track):
    url = "http://ws.audioscrobbler.com/2.0/?method=track.getsimilar"
    params = {
            "api_key": api_key,
            "artist": track['artist'],
            "track": track['name'],
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    similar_track = response['similartracks']['track'][0]
    return similar_track

def search_similar_album(album):
    url = "http://ws.audioscrobbler.com/2.0/?method=album.getsimilar"
    params = {
            "api_key": api_key,
            "artist": album['artist'],
            "track": album['name'],
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    similar_album = response['similars']['album'][0]
    return similar_album

def main():
    if args.track:
        track = search_track(args.track)
        play_track(track)
        similar_track = search_similar_track(track)
        play_track(similar_track)

    elif args.album:
        album = search_album(args.album)
        play_album(album)
        similar_album = search_similar_album(album)
        play_album(similar_album)

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

if __name__ == "__main__":
    main()

