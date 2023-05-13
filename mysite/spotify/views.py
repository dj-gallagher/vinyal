from django.shortcuts import render, redirect
from .credentials import REDIRECT_URI, CLIENT_ID, CLIENT_SECRET
from rest_framework.views import APIView
from requests import Request, post
from rest_framework import status
from rest_framework.response import Response

from .util import update_or_create_user_tokens, is_spotify_authenticated, get_user_album_names_and_start_playback_urls, queue_and_play_tracks

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
        
from .util import play_list_of_uris
def play_album(request):
    
    if request.method == "POST":
        
        #queue_and_play_tracks(request)
        
        request = play_list_of_uris(request)
        
        return redirect("spotify:albums")