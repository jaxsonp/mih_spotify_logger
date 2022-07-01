import os
import time
import csv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import secrets

def main ():
  
  # auth
  print("Gaining Spotify authorization")
  os.environ["SPOTIPY_CLIENT_ID"] = secrets.CLIENT_ID
  os.environ["SPOTIPY_CLIENT_SECRET"] = secrets.CLIENT_SECRET
  os.environ["SPOTIPY_REDIRECT_URI"] = "http://127.0.0.1:9090"
  scope = "user-read-playback-state"
  spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
  print(f"Successfully connected as {spotify.me()['display_name']}")
  
  current_track_id = ""

  while True:
    playback_data = spotify.current_playback()

    #checking for new track
    if current_track_id != playback_data['item']['id']:
      print("Logging new track")
      current_track_id = playback_data['item']['id']
      print(f" - Track: {} - {}")
    print("Track ID:", current_track_id)


    time.sleep(10)

  return


if __name__ == '__main__':
  print('\n\n\n')
  main()