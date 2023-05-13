from .models import SpotifyToken
from django.utils import timezone
from datetime import timedelta
from requests import post
from .credentials import CLIENT_ID, CLIENT_SECRET
import requests
from django.shortcuts import redirect

def get_user_tokens(user_object):
    
    user_tokens = SpotifyToken.objects.filter(user=user_object)
    if user_tokens.exists():
        return user_tokens[0]
    else:
        return None
    

def update_or_create_user_tokens(user_object, access_token, token_type, expires_in, refresh_token):
    
    tokens = get_user_tokens(user_object)
    expires_in = timezone.now() + timedelta(seconds=expires_in)
    
    if tokens:
        tokens.access_token = access_token
        tokens.refresh_token = refresh_token
        tokens.expires_in = expires_in
        tokens.token_type = token_type
        tokens.save(update_fields=["access_token", "refresh_token", "expires_in", "token_type"])
    else:
        tokens = SpotifyToken(user=user_object, 
                              access_token=access_token,
                              refresh_token=refresh_token, 
                              token_type=token_type, 
                              expires_in=expires_in)
        tokens.save()
        
def is_spotify_authenticated(user_object):
    tokens = get_user_tokens(user_object)
    if tokens:
        expiry = tokens.expires_in
        if expiry <= timezone.now():
            refresh_spotify_token(user_object)
        
        return True
    
    return False

def refresh_spotify_token(user_object):
    refresh_token = get_user_tokens(user_object).refresh_token
    
    response = post("https//accounts.spotify.com/api/token", data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }).json()
    
    access_token = response.get("access_token")
    token_type = response.get("token_type")
    expires_in = response.get("expires_in")
    refresh_token = response.get("refresh_token")
    
    update_or_create_user_tokens(user_object, access_token, token_type,
                                 expires_in, refresh_token)
        
    
def get_user_album_names_and_start_playback_urls(request):
    
    BASE_URL = "https://api.spotify.com/v1/me/"
        
    access_token = SpotifyToken.objects.filter(user=request.user)[0].access_token
    
    request_headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    request_params = {
        "limit": 3
    }

    API_ENDPOINT = "albums/"
    
    # response is a json object with ["items"] being all the albums returned (list of dicts)
    json_response = requests.get(BASE_URL + API_ENDPOINT, params=request_params, headers=request_headers).json()
    
    user_albums = []
    
    for item in json_response["items"]:
        
        album_name = item["album"]["name"]
        album_uri = item["album"]["uri"]
        album_id = item["album"]["id"]
        
        user_albums.append({
            "name" : album_name,
            "uri" : album_uri,
            "id" : album_id
        })
    
    return user_albums



def queue_and_play_tracks(request):
    
    # extract album id from post request
    data = request.POST
    album_id = data["album_id"]
    
    #print(data)
    
    # get users available device id using available token
    BASE_URL = "https://api.spotify.com/v1/me/"
    
    access_token = SpotifyToken.objects.filter(user=request.user)[0].access_token
    
    request_headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    API_ENDPOINT = "player/devices/"
    
    api_response = requests.get(BASE_URL + API_ENDPOINT, headers=request_headers).json()

    device_id = api_response["devices"][0]["id"]
    
    
    # get list of tracks from the album
    
    BASE_URL = "https://api.spotify.com/v1/"
    
    request_headers = {
        "Authorization": "Bearer " + access_token,
    }
    
    request_params = {
        "id": album_id
    }

    API_ENDPOINT = f"albums/{album_id}/tracks"
    
    api_response = requests.get(BASE_URL + API_ENDPOINT, params=request_params, headers=request_headers).json()

    album_track_items = api_response["items"]
    
    album_track_uris = []
    
    for track_item in album_track_items:
        album_track_uris.append(track_item['uri'])
    
    #print(album_track_uris)
    
    # add to queue
    BASE_URL = "https://api.spotify.com/v1/me/"
    
    for uri in album_track_uris:
        request_headers = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json"
        }

        request_params = {
            "uri": uri
        }

        API_ENDPOINT = "player/queue/"
        
        api_response = requests.post(BASE_URL + API_ENDPOINT, params=request_params, headers=request_headers)
    
    # use device id and start playing qeued tracks
    request_headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    request_params = {
        "device_id": device_id
    }

    API_ENDPOINT = "player/next/"
    
    api_response = requests.post(BASE_URL + API_ENDPOINT, params=request_params, headers=request_headers)
    
    return redirect("spotify:albums")


def play_list_of_uris(request):
    
    # extract album id from post request
    data = request.POST
    album_id = data["album_id"]
    
    #print(data)
    
    # get users available device id using available token
    BASE_URL = "https://api.spotify.com/v1/me/"
    
    access_token = SpotifyToken.objects.filter(user=request.user)[0].access_token
    
    request_headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    API_ENDPOINT = "player/devices/"
    
    api_response = requests.get(BASE_URL + API_ENDPOINT, headers=request_headers).json()

    device_id = api_response["devices"][0]["id"]
    
    
    # get list of tracks from the album
    
    BASE_URL = "https://api.spotify.com/v1/"
    
    request_headers = {
        "Authorization": "Bearer " + access_token,
    }
    
    request_params = {
        "id": album_id
    }

    API_ENDPOINT = f"albums/{album_id}/tracks"
    
    api_response = requests.get(BASE_URL + API_ENDPOINT, params=request_params, headers=request_headers).json()

    album_track_items = api_response["items"]
    
    album_track_uris = []
    
    for track_item in album_track_items:
        album_track_uris.append(track_item['uri'])
    
    #print(album_track_uris)
    
    # play tracks
    BASE_URL = "https://api.spotify.com/v1/me/"
    
    request_headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }
    
    request_params = {
        "device_id": device_id,
    }
    
    request_data = {
        "uris": album_track_uris
    }

    API_ENDPOINT = "player/play/"
    
    api_response = requests.put(BASE_URL + API_ENDPOINT, params=request_params, headers=request_headers, json=request_data)
    
    return request
    
    