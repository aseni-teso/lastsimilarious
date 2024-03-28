import argparse
import requests
import subprocess

from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description='Last.fm audio player')
parser.add_argument('-n', '--track', metavar='TRACK', help='Search by track')
parser.add_argument('-b', '--album', metavar='ALBUM', help='Search by album')
parser.add_argument('-a', '--artist', metavar='ARTIST', help='Search by artist')
parser.add_argument('-g', '--tag', metavar='TAG', help='Search by tag')
args = parser.parse_args()

def search_track(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=track.search"
    params = {
            "api_key": "YOUR_API_KEI",
            "track": query,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    track = response['results']['trackmatches']['track'][0]
    return track

def search_album(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=album.search"
    params = {
            "api_key": "YOUR_API_KEI",
            "album": query,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    album = response['results']['albummatches']['album'][0]
    return album

def search_artist(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=artist.search"
    params = {
            "api_key": "YOUR_API_KEI",
            "artist": query,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    artist = response['results']['artistmatches']['artist'][0]
    return artist

def search_tag(query):
    url = "http://ws.audioscrobbler.com/2.0/?method=tag.search"
    params = {
            "api_key": "YOUR_API_KEI",
            "tag": query,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    tag = response['results']['tagmatches']['tag'][0]
    return tag

def play_track(track):
    track_url = get_track_url(track)
    subprocess.run(['mpv', track_url])

def get_track_url(track):
    search_query = f'{track["name"]} {track["artist"]}'
    search_url = f'https://www.youtube.com/results?search_query={search_query}'
    response = requests.get(search_url)

    soup = BeautifulSoup(response.text, 'html.parser')
    video_link = soup.find('a', {'class': 'yt-uix-tile-link'})['href']
    video_url = f'https://www.youtube.com{video_link}'
    return video_url

def play_album(album):
    track_list = get_album_tracks(album)
    for track in track_list:
        play_track(track)

def get_album_tracks(album):
    url = "http://ws.audioscrobbler.com/2.0/?method=album.search"
    params = {
            "api_key": "YOUR_API_KEI",
            "artist": album['artist'],
            "album": album['name'],
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    album_info = response['album'][0]
    track_list = album_info['tracks']['track']

    return track_list

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
            "api_key": "YOUR_API_KEI",
            "album": artist['name'],
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    track_list = response['toptracks']['track']
    return track_list

def get_artist_albums(artist):
    url = "http://ws.audioscrobbler.com/2.0/?method=artist.gettopalbums"
    params = {
            "api_key": "YOUR_API_KEI",
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
            "api_key": "YOUR_API_KEI",
            "tag": tag,
            "format": "json"
            }
    response = requests.get(url, params=params).json()
    artist_list = response['topartists']['artist'][0]
    return artist_list


def search_similar_track(track):
    url = "http://ws.audioscrobbler.com/2.0/?method=track.getsimilar"
    params = {
            "api_key": "YOUR_API_KEI",
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
            "api_key": "YOUR_API_KEI",
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

