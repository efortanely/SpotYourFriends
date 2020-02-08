#!/usr/bin/env python3

from dotenv import load_dotenv
import os
import sys
import spotipy
import spotipy.util as util
from flask import Flask, render_template, url_for

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

#app = Flask(__name__)

#TODO
scope = 'user-library-read playlist-modify-public'
username = 'charlieissomine'
username2 = 'edolivares16'
playlist_name = username + ' and ' + username2 + "'s Mix"

#@app.route('/')
#def home():
token = util.prompt_for_user_token(username=username, scope=scope, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri='http://127.0.0.1/callback')
sp = spotipy.Spotify(auth=token)

#returns set of all songs across playlists
def get_all_song_ids(username: str):
    songs = set()
    playlists = sp.user_playlists(username)
    for playlist in playlists['items']:
        name = playlist['name']
        playlist_id = playlist['id']
        for item in sp.playlist_tracks(playlist_id)['items']:
            track = item['track']
            id = track['id']
            songs.add(id)
    return songs

def is_playlist_created(username: str):
    playlist_exists = False
    
    playlists = sp.user_playlists(username)
    for playlist in playlists['items']:
        name = playlist['name']
        if name == playlist_name:
            playlist_exists = True
    
    return playlist_exists

songs1 = get_all_song_ids(username)
songs2 = get_all_song_ids(username2)
shared_songs = songs1 & songs2

if not is_playlist_created(username):
    playlist_id = sp.user_playlist_create(username, playlist_name)['id']
    sp.user_playlist_add_tracks(username, playlist_id, shared_songs)


#if __name__ == '__main__':
#    app.run(threaded=True, port=5000)