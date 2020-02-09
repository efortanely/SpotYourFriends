#!/usr/bin/env python3

from dotenv import load_dotenv
import os
import sys
import spotipy
import spotipy.util as util
from flask import Flask, render_template, url_for, request, redirect

#TODO add bootstrap styling
#TODO host on heroku

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
scope = 'user-library-read playlist-modify-public'

app = Flask(__name__)

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

@app.route('/', methods = ["GET", "POST"])
def home():
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
            #alert
            print('no playlist name')
            return render_template('spotYourFriends.html')

        try:
            image = request.form['image']
        except:
            image = '/static/hacklahoma.png'

        try:
            num_songs = request.form['quantity']
        except:
            #alert
            print('no quantity')
            return render_template('spotYourFriends.html')

        if len(usernames) >= 2:
            token = util.prompt_for_user_token(username=usernames[0], scope=scope, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri='http://127.0.0.1/callback')
            sp = spotipy.Spotify(auth=token)

            shared_songs = get_all_song_ids_for_current_user(sp)
            for user in usernames[1:]:
                try:
                    shared_songs &= get_all_song_ids_for_user(user, sp)
                except:
                    pass
            
            #TODO add random songs if less than threshold

            if not is_playlist_created(playlist_name, sp):
                print('created playlist')
                playlist_id = sp.user_playlist_create(usernames[0], playlist_name)['id']
                #TODO change image
                sp.user_playlist_add_tracks(usernames[0], playlist_id, shared_songs)
                return redirect('spotify:playlist:' + playlist_id, code=302)
            else:
                return render_template('spotYourFriends.html')
    else:
        return render_template('spotYourFriends.html')


if __name__ == '__main__':
    app.run(threaded=True, port=5000)