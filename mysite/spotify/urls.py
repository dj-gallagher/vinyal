from django.urls import path

from . import views

app_name = 'spotify'
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path('get-auth-url/', views.AuthURL.as_view(), name='get-auth-url'),
    path("redirect/", views.spotify_callback, name="redirect"),
    path("is-authenticated/", views.IsAuthenticated.as_view(), name="is-authenticated"),
    path("albums/", views.AlbumsView.as_view(), name="albums"),
    path("albums/play_album", views.play_album, name="play_album"),
]