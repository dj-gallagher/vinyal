from django.shortcuts import render, redirect
from .credentials import REDIRECT_URI, CLIENT_ID, CLIENT_SECRET
from rest_framework.views import APIView
from requests import Request, post
from rest_framework import status
from rest_framework.response import Response

from .util import update_or_create_user_tokens, is_spotify_authenticated, get_user_album_names_and_start_playback_urls

from .models import SpotifyToken

# Create your views here.
from django.views import View

import requests

class IndexView(View):

    def get(self, request):
        
        template_name = 'spotify/index.html'
        
        return render(request,
                      template_name)

class AuthURL(APIView):
    def get(self, request, format=None):
        #scopes = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
        scopes = "user-library-read user-top-read user-read-playback-position app-remote-control streaming user-read-playback-state user-modify-playback-state user-read-currently-playing"
        
        url = Request("GET", "https://accounts.spotify.com/authorize", params={ # we send a request to this url
            "scope": scopes,
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID
        }).prepare().url

        #return Response({"url": url}, status=status.HTTP_200_OK)
        return redirect(url)
    

def spotify_callback(request, format=None):
    '''
    This function handles the info returned from the GET request in AuthURL above and uses
    that info to sent a POST request which returns a response with all the info we want
    '''
    code = request.GET.get("code")
    error = request.GET.get("error")
    
    response = post("https://accounts.spotify.com/api/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret":CLIENT_SECRET
        }).json()
    
    access_token = response.get("access_token")
    token_type = response.get("access_token")
    refresh_token = response.get("refresh_token")
    expires_in = response.get("expires_in")
    error = response.get("error")
    
    #if not request.session.exists(request.session.session_key):
    #    request.session.create()
    
    #update_or_create_user_tokens(request.session.session_key,
    update_or_create_user_tokens(request.user,
                                 access_token,
                                 token_type,
                                 expires_in,
                                 refresh_token)
    
    return redirect("http://127.0.0.1:8000/spotify/")

class IsAuthenticated(APIView):
    def get(self, request, format=None):
        is_authenticated = is_spotify_authenticated(self.request.user)
        return Response({"status": is_authenticated}, status=status.HTTP_200_OK)
    
class AlbumsView(View):
    
    def get(self, request):
        
        user_albums = get_user_album_names_and_start_playback_urls(request)
        
        #print(user_albums)
            
        return render(request, 
                      "spotify/albums.html",
                      {
                          "user_albums" : user_albums
                      })

def play_album(request):
    
    if request.method == "POST":
        
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
        