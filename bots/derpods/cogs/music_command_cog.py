import logging

from discord.ext import commands
from discord import app_commands, Interaction

from shared.track_downloader.playlist_downloader import PlaylistDownloader
from shared.track_downloader.song_downloader import SongDownloader
from shared.track_downloader.errors import (
    SpotifyAPIError,
)
from shared.music_service import MusicService, NotInVoiceChannelError

class MusicCommandCog(commands.Cog):
    def __init__(
            self,
            bot: commands.Bot,
            music_service: MusicService
    ):
        self.bot = bot
        self.music_service = music_service

    group = app_commands.Group(
        name="music",
        description="Commands for managing tracks, playlists, and the queue"
    )

    @group.command(name="addsong", description="Add a song to the queue by URL (HIGH PRIORITY)")
    @app_commands.describe(song_url="Youtube or Spotify track URL")
    async def add_song(self, interaction: Interaction, song_url: str):
        """
        Adds a song to the queue using the provided track URL.

        :param interaction: The Discord interaction object
        :param song_url: The URL of the track to add
        """
        await interaction.response.defer()

        # Checking if the user is in a voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            logging.warning(f"User {interaction.user.name} tried to add a song without being in a voice channel.")
            await interaction.followup.send("`You must be in a voice channel to use this command.`")
            return

        # Attempt to download the song using the song downloader
        try:
            song_request = await self.music_service.download_and_queue_song(
                song_url,
                interaction.user.voice.channel,
                high_priority=True
            )
            logging.info(f"User {interaction.user.name} requested to add song: {song_url}")
            await interaction.followup.send(f"Added **{song_request.title}** to the queue.")
        except SpotifyAPIError as e:
            logging.error(f"Spotify API error while downloading song: {e}")
            await interaction.followup.send("`Failed to download song from Spotify.`")
            return
        except Exception as e:
            logging.error(f"Error while downloading song: {e}")
            await interaction.followup.send("`Failed to download song.`")
            return


    @group.command(name="addplaylist", description="Youtube or Spotify playlist URL")
    @app_commands.describe(
        playlist_url="The URL of the playlist to add tracks from",
        start_at="The starting index in the playlist (default: 0)",
        amount="Number of tracks to add (default: 25, max: 50)"
    )
    async def add_playlist(
        self,
        interaction: Interaction,
        playlist_url: str,
        start_at: app_commands.Range[int, 0, 1000] = 0,
        amount: app_commands.Range[int, 1, 50] = 25
    ):
        """
        Adds tracks from a playlist to the queue.

        :param interaction: The Discord interaction object
        :param playlist_url: The URL of the playlist
        :param start_at: The starting index in the playlist
        :param amount: Number of tracks to add (max 50)
        """
        await interaction.response.defer()
        # TODO: Implement logic to add tracks from the playlist
        logging.info(
            f"User {interaction.user.name} requested to add playlist: {playlist_url} "
            f"starting at {start_at} with {amount} tracks"
        )
        await interaction.followup.send(
            f"Added {amount} tracks from playlist: {playlist_url} (starting at {start_at})"
        )
