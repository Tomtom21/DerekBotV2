import logging

from discord import Interaction, Member

from shared.track_downloader.song_downloader import SongDownloader, SongRequest
from shared.VCAudioManager import VCAudioManager

class NotInVoiceChannelError(Exception):
    """Raised when a user is not in a voice channel but tries to issue a music command."""

    async def handle_error(self, interaction: Interaction, requires_followup: bool = False):
        """
        Handles the error by sending a message to the user.
        :param interaction: The Discord interaction object
        :param requires_followup: Whether the response requires a follow-up message
        """
        logging.warning(f"User {interaction.user.name} tried to use a music command without being in a voice channel.")
        error_string = "`You must be in a voice channel to use this command.`"
        if requires_followup:
            await interaction.followup.send(error_string)
        else:
            await interaction.response.send_message(error_string)


class MusicService:
    def __init__(self, song_downloader: SongDownloader, audio_manager: VCAudioManager):
        self.song_downloader = song_downloader
        self.audio_manager = audio_manager

    async def download_and_queue_song(
            self,
            song_url: str,
            user: Member,
            high_priority: bool = None
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
        if high_priority is not None:
            await self.audio_manager.add_to_queue(
                song_request.file_path,
                user.voice.channel,
                high_priority=high_priority,
                audio_name=song_request.title,
                added_by=user.display_name
            )
        else:
            await self.audio_manager.add_to_queue(
                song_request.file_path,
                user.voice.channel,
                audio_name=song_request.title,
                added_by=user.display_name
            )
        logging.info(f"Added song to queue: {song_request.title}")

        return song_request
