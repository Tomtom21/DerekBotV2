import time
import requests
import os
import logging
import urllib.parse


class SpotifyAPIError(Exception):
    pass


class SpotifyAPI:
    def __init__(self, retry_count=2):
        self.access_token = None
        self.token_expiration = 0
        self.retry_count = retry_count
        self.AUTH_URL = 'https://accounts.spotify.com/api/token'
        self.BASE_URL= "https://api.spotify.com/v1/"

    def refresh_access_token(self):
        """
        Refreshes the access token
        """
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
        """
        Gets the access token if still valid, if not it is refreshed

        :return: The valid access token
        """
        if not self.access_token or time.time() >= self.token_expiration:
            self.refresh_access_token()
        return self.access_token

    def make_request(self, endpoint_url):
        """
        Makes a request to the Spotify API

        :param endpoint_url: The endpoint url for the API
        :return: The JSON response from the API
        """
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

    @staticmethod
    def get_spotify_item_id(spotify_url: str):
        """
        Gets the id of a Spotify item from the provided Spotify URL

        :param spotify_url: A Spotify item URL
        :return: The Spotify item URL
        """
        item_id = spotify_url.split("/")[-1].split("?")[0]
        return item_id

    def get_song_info(self, spotify_song_url: str):
        """
        Gets Spotify song details

        :param spotify_song_url: A Spotify song url
        :return: The Spotify song details, in JSON format
        """
        song_id = self._get_spotify_item_id(spotify_song_url)
        return self.make_request(f"https://api.spotify.com/v1/tracks/{song_id}")

    def get_playlist_info(self, spotify_playlist_url: str):
        """
        Gets Spotify playlist details (No tracks)

        :param spotify_playlist_url: A Spotify playlist url
        :return: The Spotify playlist details, in JSON format
        """
        playlist_id = self._get_spotify_item_id(spotify_playlist_url)
        return self.make_request(f"https://api.spotify.com/v1/playlists/{playlist_id}")

    def get_playlist_tracks(self, spotify_playlist_url: str):
        """
        Gets information on the tracks of a playlist

        :param spotify_playlist_url: A Spotify playlist url
        :return: The Spotify playlist track information, in JSON format
        """
        playlist_id = self._get_spotify_item_id(spotify_playlist_url)
        return self.make_request(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks")

    def api_call(self, endpoint_template: str, placeholder_values=None, **query_params):
        """
        Makes a Spotify API request using the provided endpoint template and values

        :param endpoint_template: The endpoint template with the placeholders to be filled in later
        :param placeholder_values: A dictionary of values to replace the placeholders with
        :param query_params: The query parameters to be used for the request
        :return: The Spotify API response, in JSON format
        """
        # Since keeping a dict in the function def would bring up mutable argument issues, we define it here
        placeholder_values = placeholder_values or {}

        # Populate the endpoint template
        populated_template = endpoint_template.format(**placeholder_values)
        full_url = f"{self.BASE_URL}{populated_template}"

        # Handling our query parameters
        if query_params:
            query_param_string = urllib.parse.urlencode(query_params)
            full_url += f"?{query_param_string}"

        # Finally making our request and handing it back
        return self.make_request(full_url)
