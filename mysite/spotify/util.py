from .models import SpotifyToken
from django.utils import timezone
from datetime import timedelta
from requests import post
from .credentials import CLIENT_ID, CLIENT_SECRET
import requests

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