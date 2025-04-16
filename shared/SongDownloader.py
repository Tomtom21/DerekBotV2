import urllib.parse
import urllib.request
from difflib import SequenceMatcher
import re
import os
import random
import logging
from typing import List

from bs4 import BeautifulSoup
import json
from concurrent.futures import ProcessPoolExecutor
from googleapiclient.discovery import build
import yt_dlp
from shared.SpotifyAPI import SpotifyAPI
from shared.file_utils import get_random_file_id
from datetime import datetime, timedelta, timezone
from isodate import parse_duration
from pathlib import Path
from pydub import AudioSegment
import asyncio


class YoutubeAPIError(Exception):
    pass


class URLValidationError(Exception):
    pass


class URLSanitizationError(Exception):
    pass


class SongRouterError(Exception):
    pass


class DownloadError(Exception):
    pass


class YouTubeSearchError(Exception):
    pass


class AudioProcessingError(Exception):
    pass


class SongRequest:
    def __init__(self, song_url):
        self.url = song_url
        self.title = None
        self.source = None

        # These are for scoring of the request when necessary
        self.relevance_score = None
        self.source_publish_date = None
        self.content_duration = None

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

    def __init__(self, output_path=".", max_workers=5):
        self.output_path = output_path
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        self.spotify_api = SpotifyAPI()

        self.TITLE_SCORE_TWEAKS = {"live": -0.15,
                                   "concert": -0.1,
                                   "official": 0.1,
                                   "karaoke": -0.1,
                                   "react": -0.15,
                                   "lyric": 0.35,
                                   "Behind the scenes": -0.1,
                                   "Clean": -0.1,
                                   "vocals only": -0.5,
                                   "cover": -0.2,
                                   "#shorts": -0.2}

        # Logging into the YouTube api
        if (youtube_api_key := os.getenv("YOUTUBE_API_KEY")) is not None:
            self.youtube_api = build("youtube", "v3", developerKey=youtube_api_key)
        else:
            raise YoutubeAPIError("Failed to load/build youtube api")

        # Need to set up the spotify api here

    @staticmethod
    def get_text_similarity(a, b):
        """Determines the percentage similarity between two strings"""
        return SequenceMatcher(None, a, b).ratio()

    async def download_song_by_url(self, song_url):
        """"""
        # New song request
        song_request = SongRequest(song_url)

        # Send to router
        return await self._route_song_download(song_request)

    async def download_song_by_search(self, search_query):
        """"""
        return await self._download_song_from_query(search_query)

    async def download_playlist_by_url(self, playlist_url, callback=None):
        """"""

        # This might have to be where we pass the list to this function after we
        # do an initial playlist download of info
        # Call multiprocessing router here
        pass

    async def _download_song_from_query(self, search_query):
        """Searches and downloads a video that matches the search query"""
        # Searching, checking if we found anything
        youtube_video_ids = await self._get_yt_video_ids_from_query(search_query)
        if not youtube_video_ids:
            raise YouTubeSearchError("Failed to find results for the YouTube query.")
        youtube_video_ids = youtube_video_ids[:50]

        # doing YouTube search to get info on video ids
        youtube_search_results = self.youtube_api.videos().list(
            part="snippet,contentDetails",
            id=",".join(youtube_video_ids)
        ).execute()

        # Generating a series of requests to filter
        potential_song_requests = [
            SongRequest(f"https://www.youtube.com/watch?v={video_id}")
            for video_id in youtube_video_ids
        ]

        # Setting song request info generating an similarity score, avg if possible
        for (idx, item) in enumerate(youtube_search_results["items"]):
            potential_song_requests[idx].title = item["snippet"]["title"]
            potential_song_requests[idx].source_publish_date = item["snippet"]["publishedAt"]
            potential_song_requests[idx].content_duration = parse_duration(
                item['contentDetails']['duration']).total_seconds()

            # Determining the relevance score
            potential_song_requests[idx].relevance_score = self.get_text_similarity(
                potential_song_requests[idx].title,
                search_query
            )

            # If we have a normalized search query, check the query against title in reverse order, then average
            if " - " in search_query:
                split_query = search_query.split(" - ")
                reversed_query = f"{split_query[1]} - {split_query[0]}"
                reverse_score = self.get_text_similarity(
                    potential_song_requests[idx].title,
                    reversed_query
                )
                potential_song_requests[idx].relevance_score = (
                    (potential_song_requests[idx].relevance_score + reverse_score) / 2
                )

        # Tweaking the relevance scores to better match each video
        for song_request in potential_song_requests:
            song_request.relevance_score = self._tweak_relevance_score(song_request)

        # Sorting the list
        potential_song_requests.sort(key=lambda obj: obj.relevance_score, reverse=True)

        # Downloading the best option from YouTube
        return await self._download_youtube_song(potential_song_requests[0])

    def _tweak_relevance_score(self, song_request: SongRequest):
        """Generates a new relevance score for a song request based on title contents"""
        score = song_request.relevance_score

        # Checking the title for good or bad keywords
        for phrase, score_change in self.TITLE_SCORE_TWEAKS.items():
            if phrase.lower() in song_request.title.lower():
                score += score_change

        # Penalizing very new songs
        upload_date = datetime.fromisoformat(
            song_request.source_publish_date.replace("Z", "+00:00")
        )
        if upload_date > (datetime.now(timezone.utc) - timedelta(weeks=5)):
            score += -0.2

        # Penalizing short videos
        if song_request.content_duration < 40:
            score += -0.4
        elif song_request.content_duration < 80:
            score += -0.2

        return score

    @staticmethod
    async def _get_yt_video_ids_from_query(search_query) -> list:
        """Searches YouTube, returns a list of YouTube video urls and titles"""
        search_input = urllib.parse.urlencode({'search_query': search_query})
        search_url = "https://www.youtube.com/results?" + search_input
        response = urllib.request.urlopen(search_url)
        video_ids = re.findall(r"watch\?v=(\S{11})", response.read().decode())

        return video_ids

    @staticmethod
    def match_target_amplitude(sound, target_dbfs):
        change_in_dbfs = target_dbfs - sound.dBFS
        return sound.apply_gain(change_in_dbfs)

    def normalize_audio_track(self, audio_path):
        """Normalizes the audio track so that it isn't too loud or quiet"""
        try:
            new_path = Path(audio_path).with_suffix(".wav")
            sound = AudioSegment.from_file(audio_path)
            normalized_sound = self.match_target_amplitude(sound, -15.0)
            normalized_sound.export(new_path, format="wav")
            os.remove(audio_path)
            logging.info(f"Deleted {audio_path} after normalization, new filename is {new_path}")
            return new_path
        except Exception as e:
            logging.warning(e)
            raise AudioProcessingError("Failed to normalize audio") from e

    async def _route_song_download(self, song_request: SongRequest):
        """Routes a song url to one of the song downloading methods"""
        # if
        pass

    async def _download_youtube_song(self, song_request):
        """Runs the YouTube video download task in another process"""
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(self.executor, self._download_youtube_song_process, song_request)

        song_file_path = await future
        return song_file_path

    def _download_youtube_song_process(self, song_request):
        """Downloads a YouTube video provided url. This is our separate process"""
        try:
            # Generating a new filename
            new_file_id = get_random_file_id(self.output_path)
            new_file_path = os.path.join(self.output_path, new_file_id + ".m4a")

            # Downloading the song
            ydl_opts = {
                'quiet': True,
                'format': 'bestaudio/best',
                'audio-format': 'm4a',
                'audio-quality': 192,
                'noplaylist': True,
                'outtmpl': new_file_path,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([song_request.url])

            # Normalizing the audio
            if song_request.content_duration <= 900:
                new_file_path = self.normalize_audio_track(new_file_path)

            return new_file_path
        except Exception as e:
            logging.warning(e)
            raise DownloadError("Failed to download Youtube video") from e

    def _download_spotify_song(self, song_request):
        """Downloads a Spotify video provided url"""
        # Getting info about the song
        song_info = self.spotify_api.get_song_info(song_request.url)
        song_name = song_info['name']
        song_artists = ", ".join(artist['name'] for artist in song_info['artists'])

        search_string = f"{song_name} - {song_artists}"

        # Searching for the song
        return self._download_song_from_query(search_string)

    def _route_playlist_download(self, playlist_url, callback):
        """Routes a playlist url to one of the playlist downloading methods"""
        pass

    def _download_spotify_playlist(self, spotify_playlist_url, callback):
        """Downloads a Spotify playlist provided url, calls callback"""
        # Ensuring we're authed. We auth each call to

        # This needs to accept a list of song requests??
        # essentially we need the list of songs to be pulled first

        pass

    def _download_youtube_playlist(self, youtube_playlist_url, callback):
        """Downloads a YouTube playlist provided url, calls callback"""
        pass



