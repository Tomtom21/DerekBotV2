from concurrent.futures import ProcessPoolExecutor
from shared.SpotifyAPI import SpotifyAPI
import os
from googleapiclient.discovery import build
from errors import (
    YoutubeAPIError,
    MediaTypeMismatchError,
    MediaSourceMismatchError,
    YouTubeSearchError,
    AudioProcessingError,
    DownloadError
)
from difflib import SequenceMatcher
from .models import SongRequest, PlaylistItem, PlaylistRequest
from .utils import extract_yt_playlist_id
from isodate import parse_duration
from datetime import datetime, timedelta, timezone
import urllib.parse
import urllib.request
import re
from pathlib import Path
from pydub import AudioSegment
import logging
import asyncio
from ..file_utils import get_random_file_id
import yt_dlp


class SongDownloader:
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
        """
        Determines the percentage similarity between two strings

        :param a: The first string
        :param b: The second string
        :return: The percentage similarity of the two strings
        """
        return SequenceMatcher(None, a, b).ratio()

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

    async def download_playlist_by_url(self, playlist_url, callback=None):
        """
        User-callable function to download a playlist using a URL

        :param playlist_url: The playlist url
        :param callback: The callback function to call when each song is downloaded successfully
        :return:
        """
        # This might have to be where we pass the list to this function after we
        # do an initial playlist download of info
        # Call multiprocessing router here
        pass

    def _fetch_spotify_album_data(self, album_id, max_length, offset):
        """
        Fetches Spotify album information

        :param album_id: The id of the album
        :param max_length: The maximum number of items to return
        :param offset: The item number to start fetching information at
        :return: A tuple of json objects
            - The album information
            - The information on the individual album tracks
        """
        # Getting album info
        album_info = self.spotify_api.api_call(
            endpoint_template="albums/{album_id}",
            placeholder_values={"album_id": album_id}
        )

        # Separate api call for using offset/limit
        album_tracks = self.spotify_api.api_call(
            endpoint_template="albums/{album_id}/tracks",
            placeholder_values={"album_id": album_id},
            limit=max_length,
            offset=offset
        )
        return album_info, album_tracks

    def _fetch_spotify_playlist_data(self, playlist_id, max_length, offset):
        """
        Fetches Spotify playlist information

        :param playlist_id: The id of the playlist
        :param max_length: The maximum number of items to return
        :param offset: The item number to start fetching information at
        :return: A tuple of json objects
            - The playlist information
            - The information on the individual playlist tracks
        """
        # Getting playlist info
        playlist_info = self.spotify_api.api_call(
            endpoint_template="playlists/{playlist_id}",
            placeholder_values={"playlist_id": playlist_id}
        )

        # Separate api call for using offset/limit
        playlist_tracks = self.spotify_api.api_call(
            endpoint_template="playlists/{playlist_id}/tracks",
            placeholder_values={"playlist_id": playlist_id},
            limit=max_length,
            offset=offset
        )
        return playlist_info, playlist_tracks

    def _fetch_and_process_youtube_playlist_data(self, playlist_id, max_length, offset):
        """
        Fetches YouTube playlist information and processes it into a title and a list of PlaylistItems

        :param playlist_id: The id of the playlist
        :param max_length: The maximum number of items to return
        :param offset: The item number to start fetching information at
        :return: A tuple of information about the playlist
            - The playlist's title
            - A list of PlaylistItems
        """
        # Getting playlist title
        yt_playlist_info_call = self.youtube_api.playlist().list(
            part="snippet",
            id=playlist_id
        )
        yt_playlist_info_response = yt_playlist_info_call.execute()
        playlist_title = yt_playlist_info_response["items"][0]["snippet"]["title"]

        # Getting the videos in the playlist
        next_page_token = None
        videos_retrieved = 0
        return_tracks = []

        while True:
            # Either getting the max results for the YouTube API, or the max we need
            yt_playlist_videos_call = self.youtube_api.playlist().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=min(50, max_length + offset - videos_retrieved),
                pageToken=next_page_token
            )
            yt_playlist_videos_response = yt_playlist_videos_call.execute()

            # Processing the tracks and appending them if we are handling the desired set of videos from the playlist
            for item in yt_playlist_videos_response["items"]:
                if videos_retrieved >= offset:
                    video_title = item["snippet"]["title"]
                    video_id = item["snippet"]["resourceId"]["videoId"]
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    playlist_item = PlaylistItem(
                        url=video_url,
                        title=video_title
                    )
                    return_tracks.append(playlist_item)

                    if len(return_tracks) >= max_length:
                        return playlist_title, return_tracks

            # Keeping track of the next token, or stopping if we don't get one
            next_page_token = yt_playlist_videos_response.get("nextPageToken")
            if not next_page_token:
                break
        return playlist_title, return_tracks

    @staticmethod
    def _process_spotify_list_data(list_info, list_tracks):
        """
        Processes Spotify list info and list tracks into a title and a list of PlaylistItems

        :param list_info: A JSON object with information about the Spotify playlist. Directly from Spotify API.
        :param list_tracks: A JSON object with a list of tracks. Directly from Spotify API.
        :return: A tuple of information about the playlist
            - The playlist's title
            - A list of PlaylistItems
        """
        # Parsing the title of the list
        playlist_title = list_info["name"]

        # Generating a list of PlaylistItems for all desired tracks
        return_tracks = []
        for track in list_tracks["items"]:
            # Attempting to get the internal 'track' for any playlist items. Use original if handling an album item
            track = track.get("track", track)

            # Generating a new playlist item
            playlist_item_name = track["name"]
            playlist_item_artist = track["artists"][0]["name"] if track.get("artists") else track["show"]["name"]
            playlist_item = PlaylistItem(
                title=playlist_item_name,
                artist=playlist_item_artist
            )

            # Adding our new item to the return_tracks list
            return_tracks.append(playlist_item)

        return playlist_title, return_tracks

    async def get_playlist_request(self, playlist_url, max_length=25, offset=0) -> PlaylistRequest:
        """
        Gets a playlist request with information about the playlist. This is provided to download_playlist function
        This is a separate function to download_playlist so the user can view the songs in the playlist first

        :param playlist_url: The URL to get information for
        :return: A PlaylistRequest with information on the playlist and what songs are in the playlist
        """
        # Generating our playlist request to work out of
        playlist_request = PlaylistRequest(playlist_url)

        # Getting info on the playlist
        if playlist_request.source == "spotify":
            # Getting the Spotify playlist id for either an album or playlist
            item_id = self.spotify_api.get_spotify_item_id(playlist_request.url)

            # Getting information on either a playlist or an album
            if playlist_request.media_type == "album":
                list_info, list_tracks = self._fetch_spotify_album_data(item_id, max_length, offset)
            elif playlist_request.media_type == "playlist":
                list_info, list_tracks = self._fetch_spotify_playlist_data(item_id, max_length, offset)
            else:
                raise MediaTypeMismatchError("Unsupported media type found when getting PlaylistRequest")

            # Process the lists into usable data, set the values in the playlist_request
            playlist_title, return_tracks = self._process_spotify_list_data(list_info, list_tracks)

        elif playlist_request.source == "youtube":
            # Getting the url info again for the list
            playlist_id = extract_yt_playlist_id(playlist_request.url)

            # Fetching and processing the YouTube playlist data
            playlist_title, return_tracks = self._fetch_and_process_youtube_playlist_data(
                playlist_id,
                max_length=max_length,
                offset=offset
            )
        else:
            raise MediaSourceMismatchError("Unsupported source found when creating PlaylistRequest")

        # Setting the values for the playlist request
        playlist_request.title = playlist_title
        playlist_request.items = return_tracks
        return playlist_request

    async def _download_song_from_query(self, search_query):
        """
        Searches and downloads a video that matches the search query

        :param search_query: The search query
        :return: The file path to the downloaded song
        """
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
        """
        Generates a new relevance score for song request base on title contents

        :param song_request: The song request whos relevance score we want to tweak
        :return: The new relevance score
        """
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
        """
        Searches YouTube for videos and provides all discovered videos

        :param search_query: The search query for YouTube
        :return: A list of YouTube video ids
        """
        search_input = urllib.parse.urlencode({'search_query': search_query})
        search_url = "https://www.youtube.com/results?" + search_input
        response = urllib.request.urlopen(search_url)
        video_ids = re.findall(r"watch\?v=(\S{11})", response.read().decode())

        return video_ids

    @staticmethod
    def match_target_amplitude(sound, target_dbfs):
        """
        Change's a sound's dbfs to match the target_dbfs value

        :param sound: The sound to apply to this to
        :param target_dbfs: The target dbfs value
        :return: The new sound with the gain applied
        """
        change_in_dbfs = target_dbfs - sound.dBFS
        return sound.apply_gain(change_in_dbfs)

    def normalize_audio_track(self, audio_path):
        """
        Normalizes the audio track so that it isn't too loud or quiet

        :param audio_path: The audio path to normalize
        :return: The new path of the normalized audio file
        """
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
        :return: The file path to the downloaded song
        """
        loop = asyncio.get_event_loop()
        future = loop.run_in_executor(self.executor, self._download_youtube_song_process, song_request)

        song_file_path = await future
        return song_file_path

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
            if song_request.content_duration <= 900:
                new_file_path = self.normalize_audio_track(new_file_path)

            return new_file_path
        except Exception as e:
            logging.warning(e)
            raise DownloadError("Failed to download Youtube video") from e

    def _download_spotify_song(self, song_request):
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
        return self._download_song_from_query(search_string)

    def _route_playlist_download(self, playlist_url, callback):
        """
        Routes a playlist url to one of the playlist downloading methods, calls callback for each download

        :param playlist_url: The playlist url
        :param callback: The callback function to call when each song is downloaded successfully
        :return:
        """
        pass

    def _download_spotify_playlist(self, spotify_playlist_url, callback):
        """
        Downloads a Spotify playlist, calls callback

        :param spotify_playlist_url: The Spotify playlist url
        :param callback: The callback function to call when each song is downloaded successfully
        :return:
        """
        # Ensuring we're authed. We auth each call to

        # This needs to accept a list of song requests??
        # essentially we need the list of songs to be pulled first

        pass

    def _download_youtube_playlist(self, youtube_playlist_url, callback):
        """
        Downloads a YouTube playlist, calls callback

        :param youtube_playlist_url: The YouTube playlist url
        :param callback: The callback function to call when the song is downloaded
        :return:
        """
        pass