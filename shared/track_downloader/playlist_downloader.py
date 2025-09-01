import asyncio
import logging

from shared.spotify_api import SpotifyAPI
from shared.youtube_api import YoutubeAPI
from shared.track_downloader.song_downloader import SongDownloader
from shared.track_downloader.models import PlaylistRequest

class PlaylistDownloader:
    def __init__(self, spotify_api: SpotifyAPI, youtube_api: YoutubeAPI, song_downloader: SongDownloader):
        self.song_downloader = song_downloader

    async def download_playlist_by_request(self, playlist_request: PlaylistRequest, callback_func, **kwargs):
        """
        User-callable function that downloads a playlist using a URL
        
        :param playlist_url: The playlist url
        :param callback_func: The callback function to call when each song is downloaded successfully
        :param kwargs: Additional keyword arguments
        """
        # Calling the callback to update the user-facing message and add it to the queue
        async def download_and_callback(song):
            result = await self.song_downloader.download_song_by_url(song.url)
            await callback_func(result)

        # Queueing up the downloads
        download_tasks = [
            asyncio.create_task(download_and_callback(song))
            for song in playlist_request.items
        ]

        # Waiting for all downloads to complete
        await asyncio.gather(*download_tasks)
