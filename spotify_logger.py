import os
from shutil import ExecError
import time
import csv
from datetime import datetime
import requests
from icalendar import vDatetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import gspread
from gspread import utils
from oauth2client.service_account import ServiceAccountCredentials

import secrets

bypass_device_filter = False

class colors:
    reset='\033[0m'
    bold='\033[01m'
    disable='\033[02m'
    underline='\033[04m'
    reverse='\033[07m'
    strikethrough='\033[09m'
    invisible='\033[08m'
    class fg:
        black='\033[30m'
        red='\033[31m'
        green='\033[32m'
        orange='\033[33m'
        blue='\033[34m'
        purple='\033[35m'
        cyan='\033[36m'
        lightgrey='\033[37m'
        darkgrey='\033[90m'
        lightred='\033[91m'
        lightgreen='\033[92m'
        yellow='\033[93m'
        lightblue='\033[94m'
        pink='\033[95m'
        lightcyan='\033[96m'
    class bg:
        black='\033[40m'
        red='\033[41m'
        green='\033[42m'
        orange='\033[43m'
        blue='\033[44m'
        purple='\033[45m'
        cyan='\033[46m'
        lightgrey='\033[47m'

def main ():
  
  # auth
  os.system("cls")
  print("Gaining Spotify authorization")
  os.environ["SPOTIPY_CLIENT_ID"] = secrets.CLIENT_ID
  os.environ["SPOTIPY_CLIENT_SECRET"] = secrets.CLIENT_SECRET
  os.environ["SPOTIPY_REDIRECT_URI"] = "http://127.0.0.1:9090"
  spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-playback-state"))
  print(f"Successfully connected as {spotify.me()['display_name']}")
  

  while True:

    try:
      spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope="user-read-playback-state"))
    except Exception as e:
      print(f" {colors.fg.red}\n ! Encountered error while authorizing spotify:{colors.reset}")
      print(e)
      continue

    current_track_id = ""
    print("Polling for new song...")

    while True:

      try:
        playback_data = spotify.current_playback()
      except Exception as e:
        print(f" {colors.fg.red}\n ! Encountered error while polling for spotify playback data:{colors.reset}")
        print(e)
        break

      #checking for new track
      try:
        if playback_data != None and current_track_id != playback_data['item']['id']:

          print(f"{colors.fg.lightgreen} > Detected new track <{colors.reset}\nVerifying device...")
          current_track_id = playback_data['item']['id']

          if (playback_data['device']['name'] == 'Cafe TV' and playback_data['device']['type'] == 'TV') or bypass_device_filter:
            print(f" - Device: {colors.fg.cyan}{playback_data['device']['name']} ({playback_data['device']['type']}){colors.reset}")


            print ("Gathering Made in Hope schedule data")
            try:
              mih_cal = str(requests.get(secrets.SCHEDULE_LINK).content)
            except Exception as e:
              print(f"{colors.fg.red} \n ! Encountered error while collecting MIH schedule data:{colors.reset}")
              print(e)
              current_track_id = ""
              break
            
            print("Parsing shifts...")
            shifts = mih_cal.split("BEGIN:VEVENT")
            current_employees = []
            for shift in shifts:
              if "SUMMARY" not in shift:
                continue
              raw_start = shift.split("DTSTART:")[1].split("\\")[0]
              start = vDatetime.from_ical(raw_start).replace(tzinfo=None)
              raw_end = shift.split("DTEND:")[1].split("\\")[0][:-1]
              end = vDatetime.from_ical(raw_end).replace(tzinfo=None)
              
              now = datetime.utcnow()#datetime(2022, 7, 1, 2, 30, 0, )
              
              if now > start and now < end:
                employee = " ".join(shift.split("SUMMARY:")[1].split(" ")[:2])
                current_employees.append(employee)

            print(f"{len(current_employees)} employee(s) currently on shift:")
            [print(f" - {colors.fg.cyan}{employee}{colors.reset}") for employee in current_employees]


            print('Gathering track data...')
            try:
              track = spotify.track(current_track_id)
            except Exception as e:
              print(f"{colors.fg.red}\n ! Encountered error while collecting Spotify track data:{colors.reset}")
              print(e)
            
            print('Gathering track features...')
            try:
              track_features = spotify.audio_features(current_track_id)[0]
            except Exception as e:
              print(f"{colors.fg.red} ! Encountered error while collecting Spotify track features:{colors.reset}")
              print(e)
            
            print(f" - Track: {colors.fg.cyan}{track['name']} - {', '.join([artist['name'] for artist in track['artists']])} [{current_track_id}]{colors.reset}")
            
            print('Gathering artist genres')
            all_genres = []
            try:
              for artist in track['artists']:
                all_genres += spotify.artist(artist['id'])['genres']
            except Exception as e:
              print(f"{colors.fg.red} ! Encountered error while collecting artist genres:{colors.reset}")
              print(e)
              break

            genres = []
            for i in all_genres:
                if i not in genres:
                    genres.append(i)
            
            print('Gathering context data...')
            try:
              type = playback_data['context']['type']
              print(f" - Type: {colors.fg.cyan}{type}{colors.reset}")
              context_uri = playback_data['context']['uri'].split(":")[2]
              if type == 'artist':
                print('Gathering artist radio data')
                context = spotify.artist(context_uri)
                print(f" - Artist playlist: {colors.fg.cyan}{context['name']} [{context['id']}]{colors.reset}")
              elif type == 'playlist':
                print('Gathering playlist data')
                context = spotify.playlist(context_uri)
                print(f" - Playlist: {colors.fg.cyan}{context['name']} - {context['owner']['display_name']} [{context['id']}]{colors.reset}")
              elif type == 'album':
                print('Gathering album data')
                context = spotify.playlist(context_uri)
                print(f" - Album: {colors.fg.cyan}{context['name']} [{context['id']}]{colors.reset}")

            except Exception as e:
              print(f"{colors.fg.red}\n ! Encountered error while collecting Spotify context data:{colors.reset}")
              print(e)
              
              current_track_id = ""
              break
            
            print("Aggregating data")
            new_entry = []
            with open('track_log.csv', 'r', encoding='utf-16') as f:
              reader = csv.reader(f)
              tracks = -1
              for row in reader:
                tracks += 1
              new_entry.append(tracks)
            
            new_entry.append(str(datetime.utcnow()))
            new_entry.append(", ".join(current_employees).replace("\\xca\\xbb", "\'"))
            new_entry.append(track['name'])
            new_entry.append(current_track_id)
            new_entry.append(",".join([artist['name'] for artist in track['artists']]))
            new_entry.append(playback_data['device']['volume_percent'])
            new_entry.append(track['popularity'])
            new_entry.append(track['explicit'])
            new_entry.append(track_features['tempo'])
            new_entry.append(track_features['duration_ms'])
            new_entry.append(track_features['valence'])
            new_entry.append(track_features['loudness'])
            new_entry.append(track_features['energy'])
            new_entry.append(track_features['liveness'])
            new_entry.append(context['name'])
            new_entry.append(context['id'])
            new_entry.append(context['type'])
            new_entry.append(",".join(genres))

            print("Logging collected data")
            with open('track_log.csv', 'a', newline='\n', encoding='utf-16') as f:
              writer = csv.writer(f)
              writer.writerow(new_entry)

            print("Uploading data to cloud")
            credentials = ServiceAccountCredentials.from_json_keyfile_name('google_client_secret.json', ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"])
            client = gspread.authorize(credentials)
            print("Authorized google sheets access\nWriting csv data to sheet")

            upload_complete = False
            while upload_complete != True:

              try:
                spreadsheet = client.open_by_key(secrets.SPREADSHEET_KEY)
                print("Found spreadsheet")
                worksheet = spreadsheet.worksheet("raw_data")
                print("Found worksheet")
                worksheet_rows = len(worksheet.col_values(1))
                
                range = utils.rowcol_to_a1(worksheet_rows + 1, 1) + ":" + utils.rowcol_to_a1(worksheet_rows + 1, len(new_entry))
                print(f' - Range: {colors.fg.cyan}{range}{colors.reset}')
                cell_list = worksheet.range(range)
                for cell in cell_list:
                  cell.value = new_entry[cell.col - 1]
                  print(f' - Uploading {colors.fg.cyan}{round(100 * (cell.col - 1) / len(new_entry), 2)}%{colors.reset}', end="\r")
                  time.sleep(0.1)
                worksheet.update_cells(cell_list)

                print(f' - Uploading {colors.fg.cyan}100.00%{colors.reset}')

                upload_complete = True

              except Exception as e:
                print(f"\n{colors.fg.red}\n ! Encountered error while writing data to Google sheets:{colors.reset}")
                print(e)
                print('\nTrying again...')
            
            print("Done!\nPolling for new playback data...")
            time.sleep(15)

          
          else:
            print(f"{colors.fg.red}Listening on Invalid device: {playback_data['device']['name']} ({playback_data['device']['type']}){colors.reset}")
            print("Polling for new playback data...")

      except Exception as e:
        print(f"\n{colors.fg.red}\n ! Encountered unhandled error during excecution:{colors.reset}")
        print(e)
        break

      time.sleep(30)
    print("Refreshing program loop")

  print("!!!!Broke program") 
  return

if __name__ == '__main__':
  print('\n\n\n')
  main()









