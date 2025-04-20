import time
import requests
import os
import logging


class SpotifyAPIError(Exception):
    pass


class SpotifyAPI:
    def __init__(self, retry_count=2):
        self.access_token = None
        self.token_expiration = 0
        self.retry_count = retry_count
        self.AUTH_URL = 'https://accounts.spotify.com/api/token'

    def refresh_access_token(self):
        """Refreshes the access token"""
        if "SPOTIFY_CLIENT_ID" in os.environ and "SPOTIFY_CLIENT_SECRET" in os.environ:
            data = {
                'grant_type': 'client_credentials',
                'client_id': os.getenv('SPOTIFY_CLIENT_ID'),
                'client_secret': os.getenv('SPOTIFY_CLIENT_SECRET'),
            }
            auth_response = requests.post(self.AUTH_URL, data=data)
            auth_response.raise_for_status()

            token_info = auth_response.json()
            self.access_token = token_info['access_token']
            self.token_expiration = time.time() + token_info.get("expires_in", 3600)
        else:
            logging.error("Spotify API credentials not set in environment variable file")
            raise Exception("Spotify credentials not set")

    def get_access_token(self):
        """Gets the access token if still valid, if not it is refreshed"""
        if not self.access_token or time.time() >= self.token_expiration:
            self.refresh_access_token()
        return self.access_token

    def make_request(self, endpoint_url):
        """Makes the request to the Spotify API"""
        for _ in range(self.retry_count):
            access_token = self.get_access_token()
            headers = {
                "Authorization": f"Bearer {access_token}"
            }
            api_response = requests.get(endpoint_url, headers=headers)

            # Making sure the request was successful, authorized. If not, retry
            if api_response.status_code == 401:
                self.refresh_access_token()
                continue

            api_response.raise_for_status()

            return api_response.json()

        raise SpotifyAPIError("Spotify API failed after retrying.")

    def get_song_info(self, spotify_song_url: str):
        """Gets spotify song details"""
        # Getting the spotify song id
        song_id = spotify_song_url.split("/")[-1].split("?")[0]

        return self.make_request(f"https://api.spotify.com/v1/tracks/{song_id}")

    def get_playlist_info(self, spotify_playlist_url: str):
        """Gets spotify playlist details"""
        # Getting the spotify playlist id
        playlist_id = spotify_playlist_url.split("/")[-1].split("?")[0]

        return self.make_request(f"https://api.spotify.com/v1/playlists/{playlist_id}")
