import os
import time
import csv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import secrets

bypass_device_filter = True

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

  print("Polling for new playback data...")
  while True:
    playback_data = spotify.current_playback()

    #checking for new track
    if playback_data != None and current_track_id != playback_data['item']['id']:

      print("Detected new track")
      current_track_id = playback_data['item']['id']

      if (playback_data['device']['name'] == 'Cafe TV' and playback_data['device']['type'] == 'TV') or bypass_device_filter:
        
        print ("Confirmed Cafe TV\nLogging track...")

        track_name = playback_data['item']['name']
        track_artists = str([artist['name'] for artist in playback_data['item']['artists']])
        print(f" - Track: {track_name} - {track_artists} ({current_track_id})")
        print("Track ID:", current_track_id)

        print("Polling for new playback data...")

      else:
        print(f" ! Listening on Invalid device: {playback_data['device']['name']} ({playback_data['device']['type']})")
        print("Polling for new playback data...")


    time.sleep(10)

  return


if __name__ == '__main__':
  print('\n\n\n')
  main()



"""

"""