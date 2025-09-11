import logging

from discord import Interaction, Member

from shared.track_downloader.song_downloader import SongDownloader
from shared.track_downloader.playlist_downloader import PlaylistDownloader
from shared.track_downloader.models import PlaylistRequest, SongRequest
from shared.VCAudioManager import VCAudioManager
from shared.discord_utils import is_in_voice_channel

class MusicService:
    def __init__(self, song_downloader: SongDownloader, playlist_downloader: PlaylistDownloader, audio_manager: VCAudioManager):
        self.song_downloader = song_downloader
        self.playlist_downloader = playlist_downloader
        self.audio_manager = audio_manager

    async def download_and_queue_song_from_url(
            self,
            song_url: str,
            user: Member
    ) -> SongRequest:
        """
        Downloads a song using the SongDownloader and adds it to the VCAudioManager's queue.

        :param song_url: The URL of the song to download and queue
        :param voice_channel: The voice channel to join for playback
        :param high_priority: Whether to add the song to the front of the queue
        :return: The SongRequest object if successful
        """
        # Download the song
        song_request: SongRequest = await self.song_downloader.download_song_by_url(song_url)
        logging.info(f"Downloaded song: {song_request.title}")

        # Add the downloaded song to the audio manager's queue
        await self.audio_manager.add_to_queue(
            song_request.file_path,
            song_request.content_duration,
            user.voice.channel,
            high_priority=True,
            audio_name=song_request.title,
            added_by=user.display_name
        )
        logging.info(f"Added song to queue: {song_request.title}")

        return song_request

    async def download_and_queue_song_from_query(
            self,
            search_query: str,
            user: Member
    ) -> SongRequest:
        """
        Downloads a song using a search query and adds it to the VCAudioManager's queue.

        :param search_query: The search query to find the song
        :param voice_channel: The voice channel to join for playback
        :param high_priority: Whether to add the song to the front of the queue
        :return: The SongRequest object if successful
        """
        # Download the song using the search query
        song_request: SongRequest = await self.song_downloader.download_song_by_search(search_query)
        logging.info(f"Downloaded song from query '{search_query}': {song_request.title}")

        # Add the downloaded song to the audio manager's queue
        await self.audio_manager.add_to_queue(
            song_request.file_path,
            song_request.content_duration,
            user.voice.channel,
            high_priority=True,
            audio_name=song_request.title,
            added_by=user.display_name
        )
        logging.info(f"Added song to queue: {song_request.title}")

        return song_request

    async def download_and_queue_playlist(
            self,
            playlist_request: PlaylistRequest,
            callback_func,
            user: Member
    ):
        """
        Downloads a playlist using the PlaylistRequest and adds it to the VCAudioManager's queue.

        :param playlist_request: The PlaylistRequest object containing playlist details. This isn't a url because we want to use the approval process.
        :param user: The Discord Member who requested the playlist
        """
        # Defining the callback to be executed once the song is downloaded
        async def add_to_queue_callback_wrapper(download_result: SongRequest):
            # Ensuring the user is still in a voice channel while downloading
            if not is_in_voice_channel(user):
                logging.error(
                    f"User {user.display_name} is no longer in a voice channel during"
                    f" playlist download. Skipping download."
                )
                return

            await self.audio_manager.add_to_queue(
                download_result.file_path,
                download_result.content_duration,
                user.voice.channel,
                audio_name=download_result.title,
                added_by=user.display_name,
                high_priority=False
            )
            await callback_func(download_result)

        # Starting the playlist download with our callback
        await self.playlist_downloader.download_playlist_by_request(
            playlist_request,
            add_to_queue_callback_wrapper
        )        
