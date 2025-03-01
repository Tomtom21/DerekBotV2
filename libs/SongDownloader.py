import urllib.parse
import urllib.request
from difflib import SequenceMatcher
import re
from bs4 import BeautifulSoup
import json
from concurrent.futures import ProcessPoolExecutor


class URLValidationError(Exception):
    pass


class URLSanitizationError(Exception):
    pass


class SongRouterError(Exception):
    pass


class SongRequest:
    def __init__(self, song_url):
        self.url = song_url
        self.title = None
        self.source = None
        
        self.VALID_DOMAINS = {"youtube.com": "youtube",
                              "youtu.be": "youtube",
                              "open.spotify.com": "spotify"}
        self.SANITIZATION_MAX_LENGTH = 120

        # Verifying the link, updating the source
        self._validate_url()

        # Sanitizing the link
        self._sanitize_url()

    def _validate_url(self):
        """Checks to ensure the user provided a real url"""
        def normalize_domain(domain):
            domain = domain.lower()
            if domain.startswith("www."):
                return domain[4:]
            return domain

        parsed = urllib.parse.urlparse(self.url)

        # Checking if we have a https link. No http here
        if parsed.scheme not in {"https"}:
            raise URLValidationError("The provided URL does not use HTTPS")

        # Normalizing and checking the url domains
        normalized_domain = normalize_domain(parsed.netloc)
        if normalized_domain not in self.VALID_DOMAINS.keys():
            raise URLValidationError("The URL domain is not valid")

        # It seems we have a valid domain, mark it
        self.source = self.VALID_DOMAINS[normalized_domain]

    def _sanitize_url(self):
        if len(self.url) > self.SANITIZATION_MAX_LENGTH:
            raise URLValidationError("The URl seems to be too long")


class SongDownloader:
    """
    General gameplan can be:
    For regular youtube videos, just download it without checking as long as its youtube
    For youtube playlists, up to 50 items per request but only 1 quota unit per request
    For spotify songs, search with regular request and then videos.list get all url info for 1 quota per 50 videos
    For spotify playlists, search with regular request, then videos.list for each song. 25 quota per playlist add sequence (or as many songs as added)
    """
    def __init__(self, output_dir=".", max_workers=5):
        self.output_dir = output_dir
        self.executor = ProcessPoolExecutor(max_workers=max_workers)

        self.BAD_TITLE_WORDS = {"live", "official", "karaoke"}


    @staticmethod
    def get_text_similarity(a, b):
        """Determines the percentage similarity between two strings"""
        return SequenceMatcher(None, a, b).ratio()

    async def download_song_by_url(self, song_url, callback=None):
        """"""
        # Prepare new song request
        song_request = SongRequest(song_url)

        # Send to router

        # Call multiprocessing router here
        pass

    async def download_song_by_search(self, search_query, callback=None):
        """"""
        pass

    async def download_playlist_by_url(self, playlist_url, callback=None):
        """"""

        # This might have to be where we pass the list to this function after we
        # do an initial playlist download of info
        # Call multiprocessing router here
        pass

    def _download_song_from_query(self, search_query, callback):
        """Searches and downloads a video that matches the search query"""
        pass

    def _filter_youtube_results(self, video_list):
        """Filters a list of urls/titles to remove non-desirable videos for audio streaming"""
        return [
            video
            for video in video_list
            if all(word not in video["title"].lower() for word in self.BAD_TITLE_WORDS)
        ]

    @staticmethod
    def _get_yt_video_ids_from_query(search_query) -> list:
        """Searches YouTube, returns a list of YouTube video urls and titles"""
        search_input = urllib.parse.urlencode({'search_query': search_query})
        search_url = "https://www.youtube.com/results?" + search_input
        response = urllib.request.urlopen(search_url)
        video_ids = re.findall(r"watch\?v=(\S{11})", response.read().decode())

        return video_ids

    def _route_song_download(self, song_url, callback):
        """Routes a song url to one of the song downloading methods"""
        # if
        pass

    def _download_youtube_song(self, youtube_song_url, callback):
        """Downloads a YouTube video provided url, calls callback. This is our separate process"""
        pass

    def _download_spotify_song(self, spotify_song_url, callback):
        """Downloads a Spotify video provided url, calls callback"""
        pass

    def _route_playlist_download(self, playlist_url, callback):
        """Routes a playlist url to one of the playlist downloading methods"""
        pass

    def _download_spotify_playlist(self, spotify_playlist_url, callback):
        """Downloads a Spotify playlist provided url, calls callback"""
        pass

    def _download_youtube_playlist(self, youtube_playlist_url, callback):
        """Downloads a YouTube playlist provided url, calls callback"""
        pass



