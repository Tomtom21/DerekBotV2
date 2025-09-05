from concurrent.futures import ProcessPoolExecutor
import os
import re
import urllib.parse
import urllib.request
import logging
import asyncio

from isodate import parse_duration
import yt_dlp

from shared.file_utils import get_random_file_id
from shared.track_downloader.errors import (
    YouTubeSearchError,
    DownloadError,
)
from shared.track_downloader.models import SongRequest
from shared.track_downloader.audio_processing import normalize_audio_track
from shared.spotify_api import SpotifyAPI
from shared.youtube_api import YoutubeAPI
from shared.track_downloader.title_scoring import TitleScore
from shared.track_downloader.utils import get_text_similarity, extract_spotify_resource_info
from shared.constants import NORMALIZE_DURATION_THRESHOLD, YOUTUBE_VIDEO_URL_PREFIX


class SongDownloader:
    def __init__(self, spotify_api: SpotifyAPI, youtube_api: YoutubeAPI, output_path=".", max_workers=5):
        self.output_path = output_path
        self.executor = ProcessPoolExecutor(max_workers=max_workers)
        self.spotify_api = spotify_api
        self.youtube_api = youtube_api

    async def download_song_by_url(self, song_url):
        """
        User-callable function to download a song using a URL

        :param song_url: The song url
        :return: The song request of the downloaded song
        """
        # New song request
        song_request = SongRequest(song_url)

        # Send to router
        return await self._route_song_download(song_request)

    async def download_song_by_search(self, search_query):
        """
        User-callable function to download a song using a URL

        :param search_query: The search query
        :return: The song request of the downloaded song
        """
        return await self._download_song_from_query(search_query)

    async def _download_song_from_query(self, search_query):
        """
        Searches and downloads a video that matches the search query

        :param search_query: The search query
        :return: The song request of the downloaded song
        :raise YouTubeSearchError: If no results are found for the search query
        """
        # Searching, checking if we found anything
        logging.info(f"Searching YouTube for: {search_query}")
        youtube_video_ids = await self._search_youtube_videos(search_query)
        if not youtube_video_ids:
            raise YouTubeSearchError("Failed to find results for the YouTube query.")
        
        logging.info(f"Found {len(youtube_video_ids)} results on YouTube for query: {search_query}")
        youtube_video_ids = youtube_video_ids[:50]

        # doing YouTube search to get info on video ids
        logging.info(f"Retrieving YouTube video details for {len(youtube_video_ids)} videos")
        youtube_search_results = self.youtube_api.youtube_api.videos().list(
            part="snippet,contentDetails",
            id=",".join(youtube_video_ids)
        ).execute()

        # Generating a series of requests to filter
        potential_song_requests = [
            SongRequest(f"{YOUTUBE_VIDEO_URL_PREFIX}{video_id}")
            for video_id in youtube_video_ids
        ]

        # Setting song request info generating an similarity score, avg if possible
        logging.info(f"Scoring {len(potential_song_requests)} potential song matches")
        for (idx, item) in enumerate(youtube_search_results["items"]):
            potential_song_requests[idx].title = item["snippet"]["title"]
            potential_song_requests[idx].source_publish_date = item["snippet"]["publishedAt"]
            potential_song_requests[idx].content_duration = parse_duration(
                item['contentDetails']['duration']).total_seconds()

            # Determining the relevance score
            potential_song_requests[idx].relevance_score = get_text_similarity(
                potential_song_requests[idx].title,
                search_query
            )

            # If we have a normalized search query, check the query against title in reverse order, then average
            if " - " in search_query:
                split_query = search_query.split(" - ")
                reversed_query = f"{split_query[1]} - {split_query[0]}"
                reverse_score = get_text_similarity(
                    potential_song_requests[idx].title,
                    reversed_query
                )
                potential_song_requests[idx].relevance_score = (
                    (potential_song_requests[idx].relevance_score + reverse_score) / 2
                )

        # Getting the relevance scores to better match each video
        for song_request in potential_song_requests:
            song_request.relevance_score = TitleScore.get_relevance_score(song_request) #TODO: Make this update relevance score

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
            return [] #TODO: Raise error?

    async def _route_song_download(self, song_request: SongRequest):
        """
        Route a song url to one of the song downloading methods

        :param song_request: The song request to route
        :return: The song request of the downloaded song
        """
        if song_request.source == "youtube":
            # We aren't going to be running the query download, so we need to get the video info here
            try:
                with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
                    video_info = ydl.extract_info(song_request.url, download = False)

                # Checking if our video is live. We can't play those
                if video_info.get("is_live", False):
                    raise DownloadError("Cannot download live videos.")
                
                # Setting the song request info
                song_request.title = video_info.get('title', 'Unknown Title')
                song_request.content_duration = video_info.get('duration')
            except Exception as e:
                logging.warning(e)
                raise DownloadError("Failed to get video information") from e #TODO: Consider removing this try to ensure errors are passed correctly

            return await self._download_youtube_song(song_request)
        elif song_request.source == "spotify":
            return await self._download_spotify_song(song_request)

    async def _download_youtube_song(self, song_request):
        """
        Runs the YouTube video download task in another process

        :param song_request: The song request to process
        :return: The song request with the file path set
        """
        logging.info(f"Starting download attempt for URL: {song_request.url}")
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(
            self.executor, 
            self._download_youtube_song_process,
            self.output_path,
            song_request
        )

        song_request = await future
        return song_request

    @staticmethod
    def _download_youtube_song_process(output_path, song_request):
        """
        Downloads a YouTube video provided url. This is our separate process

        :param output_path: The directory to save the downloaded file
        :param song_request: The song request to process
        :return: The song request with the file path set
        :raise DownloadError: If the download fails
        """
        try:
            # Generating a new filename
            new_file_id = get_random_file_id(output_path)
            new_file_path = os.path.join(output_path, f"{new_file_id}.m4a")

            # Downloading the song
            logging.info(f"Starting audio download for url: {song_request.url}")
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
            if song_request.content_duration <= NORMALIZE_DURATION_THRESHOLD:
                logging.info(f"Normalizing audio for track: {song_request.title}")
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
        :return: The song request of the downloaded song
        """
        # Getting info about the song
        logging.info(f"Retrieving Spotify track information for URL: {song_request.url}")
        _, song_id = extract_spotify_resource_info(song_request.url)
        song_info = self.spotify_api.api_call(
            endpoint_template="tracks/{track_id}",
            placeholder_values={"track_id": song_id}
        )
        song_name = song_info['name']
        song_artists = ", ".join(artist['name'] for artist in song_info['artists'])

        search_string = f"{song_name} - {song_artists}"

        # Searching for the song
        return await self._download_song_from_query(search_string)
