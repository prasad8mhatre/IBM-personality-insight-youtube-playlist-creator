from __future__ import print_function 
from flask import Flask
import json
import urllib
import urllib2
from flask import jsonify
import argparse
import os

import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

import httplib2


from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run

import sys
app = Flask(__name__)

API_KEY="<your api key>"
Base_Url="https://www.googleapis.com/youtube/v3"
Max_Result=10
SCOPES = ['https://www.googleapis.com/auth/youtube']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'
CLIENT_SECRETS_FILE = "client_secret.json"

MISSING_CLIENT_SECRETS_MESSAGE = """
missing client_secrets.json file
found at:

%s


""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                            CLIENT_SECRETS_FILE))
                        

YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


@app.route("/getPreferenceMusic")
def getPreferenceMusic():
    print("getPreferenceMusic ", file=sys.stderr)
    items = readPreferences()
    return json.dumps(items)

@app.route("/createPlaylistFromPreferences")
def createPlaylistFromPreferences(): 
    print("In createPlaylistFromPreferences:", file=sys.stderr)
    items = readPreferences()
    for item in items:
        add_playlist(youtube, item)
    return 'playlist created'

@app.route("/getMyPreferencePlaylist")
def getMyPreferencePlaylist(): 
    print("In getMyPreferencePlaylist:", file=sys.stderr)
    playlists = playlists_list_mine(youtube)
    items = readPreferences()
    matchedPreferences = []
    for playlist in playlists['items']:
        title = playlist['snippet']['title']
        for item in items:
            if item['category'] == title:
                matchedPreferences.append(playlist)
    return json.dumps(matchedPreferences)

@app.route("/deleteMyPreferencePlaylist")
def deleteMyPreferencePlaylist(): 
    print("In deleteMyPreferencePlaylist:", file=sys.stderr)
    playlists = playlists_list_mine(youtube)
    items = readPreferences()
    for playlist in playlists['items']:
        title = playlist['snippet']['title']
        for item in items:
            if item['category'] == title:
                playlists_delete(youtube, playlist['id'])
    
    return 'Playlist deleted'


def readPreferences():
    with open('data.json', 'r') as f:
        datastore = json.load(f)

    items = []
    for preference in datastore["consumption_preferences"]:
        if preference["score"] > 0:
            category = preference["consumption_preference_id"].replace('consumption_preferences_music_', '') + " music"
            items.append(fetchMusic(category))
    
    return items

def fetchMusic(category):
    f = { 'q' : category}
    query = urllib.urlencode(f)
    url = Base_Url + "/search?" + query + "&maxResults=" + str(Max_Result) +"&part=snippet&key=" + API_KEY
    print("Url: "+ url, file=sys.stderr)
    content = urllib2.urlopen(url).read()
    
    data = {}
    data["url"] = url
    data["category"] = category
    data["result"] = json.loads(content)
    return data

 
  
def get_authenticated_service():
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run(flow, storage)

    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()))

youtube = get_authenticated_service()

def add_video_to_playlist(youtube,videoID,playlistID):
    add_video_request=youtube.playlistItems().insert(
    part="snippet",
    body={
        'snippet': {
            'playlistId': playlistID, 
            'resourceId': {
                    'kind': 'youtube#video',
                'videoId': videoID
            }
        }
    }
    ).execute()


def add_playlist(youtube, item):
  
    body = dict(
        snippet=dict(
            title=item['category'],
            description=item['category']
        ),
        status=dict(
            privacyStatus='private'
        ) 
    ) 

    playlists_insert_response = youtube.playlists().insert(
        part='snippet,status',
        body=body
    ).execute()

    print( 'New playlist ID: %s' % playlists_insert_response['id'],file=sys.stderr)

    videos = item['result']['items']
    for video in videos:
        if video['id']['kind'] == 'youtube#video':
            vi = video['id']['videoId']
            add_video_to_playlist(youtube,vi,playlists_insert_response['id'])



def playlists_delete(youtube, playlistId):
    playlist_delete_response = youtube.playlists().delete(
        id=playlistId
    ).execute()

    return playlist_delete_response

def playlists_list_mine(youtube):
 
  response = youtube.playlists().list(
    part='snippet,contentDetails',
    mine=True,
    maxResults=25,
  ).execute()

  return response


