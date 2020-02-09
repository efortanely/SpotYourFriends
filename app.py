#!/usr/bin/env python3

#from dotenv import load_dotenv
import os
import sys
import spotipy
import spotipy.util as util
from flask import Flask, render_template, url_for, request, redirect
import random
from boto.s3.connection import S3Connection
#import base64

#load_dotenv()

#CLIENT_ID = os.getenv("CLIENT_ID")
#CLIENT_SECRET = os.getenv("CLIENT_SECRET")
s3 = S3Connection(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])
CLIENT_ID = s3['CLIENT_ID']
CLIENT_SECRET = s3['CLIENT_SECRET']
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
            return render_template('spotYourFriends.html')

        
        image = request.form['image']
        if not image:
            image = 'static/hacklahoma.png'

        try:
            num_songs = int(request.form['quantity'])
        except:
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
            
            songs_needed = num_songs - len(shared_songs)
            if songs_needed > 0:
                all_songs = set()
                for user in usernames:
                    all_songs |= get_all_song_ids_for_user(user, sp)
                shared_songs |= set(random.sample(all_songs, songs_needed))
            else:
                shared_songs = list(shared_songs)[:num_songs]

            if not is_playlist_created(playlist_name, sp):
                playlist_id = sp.user_playlist_create(usernames[0], playlist_name)['id']
                '''
                with open(image, 'rb') as image_file:
                    encoded_string = base64.b64encode(image_file.read())
                    sp.playlist_upload_cover_image(playlist_id, encoded_string)
                '''
                sp.user_playlist_add_tracks(usernames[0], playlist_id, shared_songs)
                return redirect('spotify:playlist:' + playlist_id, code=302)
            else:
                return render_template('spotYourFriends.html')
    else:
        return render_template('spotYourFriends.html')


if __name__ == '__main__':
    app.run(threaded=True, port=5000)