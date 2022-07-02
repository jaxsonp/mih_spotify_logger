import os
import time
import csv
from datetime import datetime
import requests
from icalendar import vDatetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import secrets

bypass_device_filter = True

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
  scope = "user-read-playback-state"
  spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
  print(f"Successfully connected as {spotify.me()['display_name']}")
  
  current_track_id = ""

  print("Polling for new playback data...")
  while True:
    try:
      playback_data = spotify.current_playback()
    except Exception as e:
      print(f" {colors.fg.red}! Encountered error while polling for spotify api data:{colors.reset}")
      print(e)
      continue

    #checking for new track
    if playback_data != None and current_track_id != playback_data['item']['id']:

      print(f"{colors.fg.lightgreen} > Detected new track <{colors.reset}\nVerifying device...")
      current_track_id = playback_data['item']['id']

      if (playback_data['device']['name'] == 'Cafe TV' and playback_data['device']['type'] == 'TV') or bypass_device_filter:
        print(f" - Device: {colors.fg.cyan}{playback_data['device']['name']} ({playback_data['device']['type']}){colors.reset}")


        print ("Gathering Made in Hope schedule data")
        try:
          mih_cal = str(requests.get(secrets.SCHEDULE_LINK).content)
        except Exception as e:
          print(f"{colors.fg.red} ! Encountered error while collecting MIH schedule data:{colors.reset}")
          print(e)
          current_track_id = ""
          continue
        
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
        track = spotify.track(current_track_id)
        track_artists = ", ".join([artist['name'] for artist in track['artists']])
        print(f" - {colors.fg.cyan}Track: {track['name']} - {track_artists} [{current_track_id}]{colors.reset}")
        
        playlist = spotify.playlist(playback_data['context']['uri'].split(":")[2])
        print(f" - {colors.fg.cyan}Playlist: {playlist['name']} - {playlist['owner']['display_name']} [{playlist['id']}]{colors.reset}")
        
        print("Aggregating data")
        entry = []
        with open('track_log.csv', 'r') as f:
          entry.append(len(f.readlines()))

        entry.append(", ".join(current_employees))
        entry.append(track['name'])
        entry.append(current_track_id)
        entry.append(track_artists)

        print("Logging collected data")
        with open('track_log.csv', 'a', newline='\n') as f:
          writer = csv.writer(f)
          writer.writerow(entry)

        print("Uploading data to cloud")
        credentials = ServiceAccountCredentials.from_json_keyfile_name('google_client_secret.json', ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets', "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(credentials)
        print("Authorized google sheets access\nWriting csv data to sheet")

        spreadsheet = client.open_by_key(secrets.SPREADSHEET_KEY)
        worksheet = spreadsheet.worksheet("Raw data")
        worksheet_rows = len(worksheet.col_values(1))
        for i in range(len(entry)):
          worksheet.update_cell(worksheet_rows + 1, i + 1, entry[i])
        
          
        #worksheet.update_title("Raw data")
        
        print("Polling for new playback data...")

      else:
        print(f" {colors.fg.red}! Listening on Invalid device: {playback_data['device']['name']} ({playback_data['device']['type']}){colors.reset}")
        print("Polling for new playback data...")


    time.sleep(15)

  return


if __name__ == '__main__':
  print('\n\n\n')
  main()



""" PLAYLIST
{
  'collaborative': False,
  'description': '',
  'external_urls': {
    'spotify': 'https://open.spotify.com/playlist/2hrD3KjuS1ekiDqboJNSVC'
  },
  'followers': {
    'href': None,
    'total': 0
  },
  'href': 'https://api.spotify.com/v1/playlists/2hrD3KjuS1ekiDqboJNSVC?additional_types=track',
  'id': '2hrD3KjuS1ekiDqboJNSVC',
  'images': [
    {
      'height': 640,
      'url': 'https://i.scdn.co/image/ab67616d0000b27353314c645406acd9ab15aaee',
      'width': 640
    }
  ],
  'name': 'Test playlist',
  'owner': {
    'display_name': 'Jaxson P',
    'external_urls': {
      'spotify': 'https://open.spotify.com/user/4jtq72to3phoh40qj10gghrrm'
    },
    'href': 'https://api.spotify.com/v1/users/4jtq72to3phoh40qj10gghrrm',
    'id': '4jtq72to3phoh40qj10gghrrm',
    'type': 'user',
    'uri': 'spotify:user:4jtq72to3phoh40qj10gghrrm'
  },
  'primary_color': None,
  'public': True,
  'snapshot_id': 'MixjYzdkNDg2Y2VlZDg2YjQyNDM4ZWNlODVmZGZmYmYxNGRkZDYwZTg3',
  'tracks': {
    'href': 'https://api.spotify.com/v1/playlists/2hrD3KjuS1ekiDqboJNSVC/tracks?offset=0&limit=100&additional_types=track',
    'items': [
      {
        'added_at': '2022-07-02T08:16:19Z',
        'added_by': {
          'external_urls': {
            'spotify': 'https://open.spotify.com/user/4jtq72to3phoh40qj10gghrrm'
          },
          'href': 'https://api.spotify.com/v1/users/4jtq72to3phoh40qj10gghrrm',
          'id': '4jtq72to3phoh40qj10gghrrm',
          'type': 'user',
          'uri': 'spotify:user:4jtq72to3phoh40qj10gghrrm'
        },
        'is_local': False,
        'primary_color': None,
        'track': {
          'album': {
            'album_type': 'single',
            'artists': [
              {
                'external_urls': {
                  'spotify': 'https://open.spotify.com/artist/2ahbiJn3gxyByrDXIMaACV'
                },
                'href': 'https://api.spotify.com/v1/artists/2ahbiJn3gxyByrDXIMaACV',
                'id': '2ahbiJn3gxyByrDXIMaACV',
                'name': 'Vaeo',
                'type': 'artist',
                'uri': 'spotify:artist:2ahbiJn3gxyByrDXIMaACV'
              }
            ],
            'available_markets': [
              'AD',
              'AE',
              'ZW'
            ],
            'external_urls': {
              'spotify': 'https://open.spotify.com/album/3Rjox1mLxaJLl0P5RwjLnP'
            },
            'href': 'https://api.spotify.com/v1/albums/3Rjox1mLxaJLl0P5RwjLnP',
            'id': '3Rjox1mLxaJLl0P5RwjLnP',
            'images': [
              {
                'height': 640,
                'url': 'https://i.scdn.co/image/ab67616d0000b27353314c645406acd9ab15aaee',
                'width': 640
              },
              {
                'height': 300,
                'url': 'https://i.scdn.co/image/ab67616d00001e0253314c645406acd9ab15aaee',
                'width': 300
              },
              {
                'height': 64,
                'url': 'https://i.scdn.co/image/ab67616d0000485153314c645406acd9ab15aaee',
                'width': 64
              }
            ],
            'name': 'junkie',
            'release_date': '2022-03-23',
            'release_date_precision': 'day',
            'total_tracks': 4,
            'type': 'album',
            'uri': 'spotify:album:3Rjox1mLxaJLl0P5RwjLnP'
          },
          'artists': [
            {
              'external_urls': {
                'spotify': 'https://open.spotify.com/artist/2ahbiJn3gxyByrDXIMaACV'
              },
              'href': 'https://api.spotify.com/v1/artists/2ahbiJn3gxyByrDXIMaACV',
              'id': '2ahbiJn3gxyByrDXIMaACV',
              'name': 'Vaeo',
              'type': 'artist',
              'uri': 'spotify:artist:2ahbiJn3gxyByrDXIMaACV'
            },
            {
              'external_urls': {
                'spotify': 'https://open.spotify.com/artist/6lQsMKSDG7XdirlE6YImHa'
              },
              'href': 'https://api.spotify.com/v1/artists/6lQsMKSDG7XdirlE6YImHa',
              'id': '6lQsMKSDG7XdirlE6YImHa',
              'name': 'rouri404',
              'type': 'artist',
              'uri': 'spotify:artist:6lQsMKSDG7XdirlE6YImHa'
            }
          ],
          'available_markets': [
            
          ],
          'disc_number': 1,
          'duration_ms': 117333,
          'episode': False,
          'explicit': True,
          'external_ids': {
            'isrc': 'QZDA72275129'
          },
          'external_urls': {
            'spotify': 'https://open.spotify.com/track/4E6RRv2D91G1P665WSBADB'
          },
          'href': 'https://api.spotify.com/v1/tracks/4E6RRv2D91G1P665WSBADB',
          'id': '4E6RRv2D91G1P665WSBADB',
          'is_local': False,
          'name': 'poison',
          'popularity': 41,
          'preview_url': 'https://p.scdn.co/mp3-preview/87d8b52cd66db0be1e447becfbb2c077d6c34717?cid=fe463969182142bdaac06fc2b96227c9',
          'track': True,
          'track_number': 4,
          'type': 'track',
          'uri': 'spotify:track:4E6RRv2D91G1P665WSBADB'
        },
        'video_thumbnail': {
          'url': None
        }
      }
    ],
    'limit': 100,
    'next': None,
    'offset': 0,
    'previous': None,
    'total': 1
  },
  'type': 'playlist',
  'uri': 'spotify:playlist:2hrD3KjuS1ekiDqboJNSVC'
}























TRACK

{
  'album': {
    'album_type': 'single',
    'artists': [
      {
        'external_urls': {
          'spotify': 'https://open.spotify.com/artist/7DMveApC7UnC2NPfPvlHSU'
        },
        'href': 'https://api.spotify.com/v1/artists/7DMveApC7UnC2NPfPvlHSU',
        'id': '7DMveApC7UnC2NPfPvlHSU',
        'name': 'Cheat Codes',
        'type': 'artist',
        'uri': 'spotify:artist:7DMveApC7UnC2NPfPvlHSU'
      },
      {
        'external_urls': {
          'spotify': 'https://open.spotify.com/artist/1VBflYyxBhnDc9uVib98rw'
        },
        'href': 'https://api.spotify.com/v1/artists/1VBflYyxBhnDc9uVib98rw',
        'id': '1VBflYyxBhnDc9uVib98rw',
        'name': 'Icona Pop',
        'type': 'artist',
        'uri': 'spotify:artist:1VBflYyxBhnDc9uVib98rw'
      }
    ],
    'available_markets': [
      'AD',

      'ZM',
      'ZW'
    ],
    'external_urls': {
      'spotify': 'https://open.spotify.com/album/7xerYbkUGD5BazNdP6OaZW'
    },
    'href': 'https://api.spotify.com/v1/albums/7xerYbkUGD5BazNdP6OaZW',
    'id': '7xerYbkUGD5BazNdP6OaZW',
    'images': [
      {
        'height': 640,
        'url': 'https://i.scdn.co/image/ab67616d0000b273dd22d7c43aa6aa2593829d48',
        'width': 640
      },
      {
        'height': 300,
        'url': 'https://i.scdn.co/image/ab67616d00001e02dd22d7c43aa6aa2593829d48',
        'width': 300
      },
      {
        'height': 64,
        'url': 'https://i.scdn.co/image/ab67616d00004851dd22d7c43aa6aa2593829d48',
        'width': 64
      }
    ],
    'name': 'Payback (feat. Icona Pop)',
    'release_date': '2022-03-04',
    'release_date_precision': 'day',
    'total_tracks': 1,
    'type': 'album',
    'uri': 'spotify:album:7xerYbkUGD5BazNdP6OaZW'
  },
  'artists': [
    {
      'external_urls': {
        'spotify': 'https://open.spotify.com/artist/7DMveApC7UnC2NPfPvlHSU'
      },
      'href': 'https://api.spotify.com/v1/artists/7DMveApC7UnC2NPfPvlHSU',
      'id': '7DMveApC7UnC2NPfPvlHSU',
      'name': 'Cheat Codes',
      'type': 'artist',
      'uri': 'spotify:artist:7DMveApC7UnC2NPfPvlHSU'
    },
    {
      'external_urls': {
        'spotify': 'https://open.spotify.com/artist/1VBflYyxBhnDc9uVib98rw'
      },
      'href': 'https://api.spotify.com/v1/artists/1VBflYyxBhnDc9uVib98rw',
      'id': '1VBflYyxBhnDc9uVib98rw',
      'name': 'Icona Pop',
      'type': 'artist',
      'uri': 'spotify:artist:1VBflYyxBhnDc9uVib98rw'
    }
  ],
  'available_markets': [
    'AD',
    'AE',
    'AL',
 
  ],
  'disc_number': 1,
  'duration_ms': 203411,
  'explicit': False,
  'external_ids': {
    'isrc': 'US3DF2214226'
  },
  'external_urls': {
    'spotify': 'https://open.spotify.com/track/6VcpaoEQRxc9wrAtYBqKwz'
  },
  'href': 'https://api.spotify.com/v1/tracks/6VcpaoEQRxc9wrAtYBqKwz',
  'id': '6VcpaoEQRxc9wrAtYBqKwz',
  'is_local': False,
  'name': 'Payback (feat. Icona Pop)',
  'popularity': 59,
  'preview_url': 'https://p.scdn.co/mp3-preview/53d8447de086c4500fa110414dccb7d44ffda7b4?cid=fe463969182142bdaac06fc2b96227c9',
  'track_number': 1,
  'type': 'track',
  'uri': 'spotify:track:6VcpaoEQRxc9wrAtYBqKwz'
}
"""