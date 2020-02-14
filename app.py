#!/usr/bin/env python3

import os
import sys
import spotipy
import spotipy.util as util
from flask import Flask, render_template, url_for, request, redirect
import random
from urllib.parse import quote
import requests
import json

app = Flask(__name__)

#Client Keys
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

#Spotify URLs
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

#Server-side Parameters
CLIENT_SIDE_URL = "http://spotyourfriends.herokuapp"
PORT = 5000
REDIRECT_URI = "{}/callback/q".format(CLIENT_SIDE_URL)
SCOPE = 'user-library-read playlist-modify-public'
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()
global token

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "client_id": CLIENT_ID
}

def get_all_song_ids_for_user(username: str, sp):
    playlists = sp.user_playlists(username)
    return get_all_songs(playlists, sp)

def get_all_song_ids_for_current_user(sp):
    playlists = sp.current_user_playlists()
    return get_all_songs(playlists, sp)

def get_all_songs(playlists, sp):
    songs = set()

    for playlist in playlists['items']:
        name = playlist['name']
        playlist_id = playlist['id']
        for item in sp.playlist_tracks(playlist_id)['items']:
            track = item['track']
            id = track['id']
            songs.add(id)
    return songs

def is_playlist_created(playlist_name, sp):
    playlist_exists = False

    playlists = sp.current_user_playlists()
    for playlist in playlists['items']:
        name = playlist['name']
        if name == playlist_name:
            playlist_exists = True
    
    return playlist_exists

@app.route("/")
def home():
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route("/callback/q", methods = ["GET", "POST"])
def callback():
    global token

    if request.method == 'POST':
        usernames = []
        try:
            usernames.append(request.form['input0'])
            usernames.append(request.form['input1'])
            usernames.append(request.form['input2'])
            usernames.append(request.form['input3'])
            usernames.append(request.form['input4'])
        except:
            pass
        
        try:
            playlist_name = request.form['playlist_name']
        except:
            return render_template('spotYourFriends.html')

        try:
            num_songs = int(request.form['quantity'])
        except:
            return render_template('spotYourFriends.html')

        if len(usernames) >= 1:            
            sp = spotipy.Spotify(auth=token)

            shared_songs = get_all_song_ids_for_current_user(sp)
            for user in usernames:
                try:
                    shared_songs &= get_all_song_ids_for_user(user, sp)
                except:
                    pass
            
            songs_needed = num_songs - len(shared_songs)
            if songs_needed > 0:
                all_songs = get_all_song_ids_for_current_user(sp)
                for user in usernames:
                    all_songs |= get_all_song_ids_for_user(user, sp)
                shared_songs |= set(random.sample(all_songs, songs_needed))
            else:
                shared_songs = list(shared_songs)[:num_songs]

            if not is_playlist_created(playlist_name, sp):
                playlist_id = sp.user_playlist_create(sp.me()['id'], playlist_name)['id']
                sp.user_playlist_add_tracks(sp.me()['id'], playlist_id, shared_songs)
                return redirect('spotify:playlist:' + playlist_id, code=302)
            else:
                return render_template('spotYourFriends.html')
    else:
        auth_token = request.args['code']
        
        code_payload = {
            "grant_type": "authorization_code",
            "code": str(auth_token),
            "redirect_uri": REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }

        post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)
        response_data = json.loads(post_request.text)
        token = response_data["access_token"]

        return render_template('spotYourFriends.html')


if __name__ == '__main__':
    app.run(threaded=True, port=PORT)