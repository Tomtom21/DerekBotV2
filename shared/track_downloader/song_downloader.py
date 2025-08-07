from concurrent.futures import ProcessPoolExecutor
import os
from errors import (
    YouTubeSearchError,
    DownloadError,
)
from isodate import parse_duration
import urllib.parse
import urllib.request
import re
from shared.file_utils import get_random_file_id
import yt_dlp
import logging
import asyncio
from models import SongRequest
from audio_processing import normalize_audio_track
from shared.spotify_api import SpotifyAPI
from shared.youtube_api import YoutubeAPI
from title_scoring import TitleScore


class SongDownloader:
    def __init__(self, spotify_api: SpotifyAPI, youtube_api: YoutubeAPI, output_path=".", max_workers=5):
        self.output_path = output_path
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        self.spotify_api = spotify_api
        self.youtube_api = youtube_api

        # The length a video must be under (in seconds) before it is no longer normalized (To save on processing)
        self.NORMALIZE_DURATION_THRESHOLD = 900

    async def download_song_by_url(self, song_url):
        """
        User-callable function to download a song using a URL

        :param song_url: The song url
        :return: The file path to the downloaded song
        """
        # New song request
        song_request = SongRequest(song_url)

        # Send to router
        return await self._route_song_download(song_request)

    async def download_song_by_search(self, search_query):
        """
        User-callable function to download a song using a URL

        :param search_query: The search query
        :return: The file path to the downloaded song
        """
        return await self._download_song_from_query(search_query)

    async def _download_song_from_query(self, search_query):
        """
        Searches and downloads a video that matches the search query

        :param search_query: The search query
        :return: The file path to the downloaded song
        """
        # Searching, checking if we found anything
        youtube_video_ids = await self._search_youtube_videos(search_query)
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

        # Getting the relevance scores to better match each video
        for song_request in potential_song_requests:
            song_request.relevance_score = TitleScore.get_relevance_score(song_request)

        # Sorting the list
        potential_song_requests.sort(key=lambda obj: obj.relevance_score, reverse=True)

        # Downloading the best option from YouTube
        return await self._download_youtube_song(potential_song_requests[0])
    
    @staticmethod
    async def _search_youtube_videos(search_query) -> list:
        """
        Searches YouTube for videos and provides their urls

        :param search_query: The search query for YouTube
        :return: A list of YouTube video ids
        """
        try:
            search_input = urllib.parse.urlencode({'search_query': search_query})
            search_url = "https://www.youtube.com/results?" + search_input
            response = urllib.request.urlopen(search_url)
            video_ids = re.findall(r"watch\?v=(\S{11})", response.read().decode())
            return video_ids
        except Exception as e:
            logging.error(f"Failed to search YouTube: {e}")
            return []

    async def _route_song_download(self, song_request: SongRequest):
        """
        Route a song url to one of the song downloading methods

        :param song_request: The song request to route
        :return: The file path to the downloaded song
        """
        if song_request.source == "youtube":
            return await self._download_youtube_song(song_request)
        elif song_request.source == "spotify":
            return await self._download_spotify_song(song_request)

    async def _download_youtube_song(self, song_request):
        """
        Runs the YouTube video download task in another process

        :param song_request: The song request to process
        :return: The song request with the file path set
        :raise DownloadError: If the download fails
        """
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(self.executor, self._download_youtube_song_process, song_request)

        song_request = await future
        return song_request

    def _download_youtube_song_process(self, song_request):
        """
        Downloads a YouTube video provided url. This is our separate process

        :param song_request: The song request to process
        :return: The file path to the downloaded song
        """
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
            if song_request.content_duration <= self.NORMALIZE_DURATION_THRESHOLD:
                new_file_path = normalize_audio_track(new_file_path)

            # Setting the file path in the song request
            song_request.file_path = new_file_path

            return song_request
        except Exception as e:
            logging.warning(e)
            raise DownloadError("Failed to download Youtube video") from e

    async def _download_spotify_song(self, song_request):
        """
        Downloads a Spotify song

        :param song_request: The song request to process
        :return: The file path to the downloaded song
        """
        # Getting info about the song
        song_id = self.spotify_api.get_spotify_item_id(song_request.url)
        song_info = self.spotify_api.api_call(
            endpoint_template="tracks/{track_id}",
            placeholder_values={"track_id": song_id}
        )
        song_name = song_info['name']
        song_artists = ", ".join(artist['name'] for artist in song_info['artists'])

        search_string = f"{song_name} - {song_artists}"

        # Searching for the song
        return await self._download_song_from_query(search_string)
