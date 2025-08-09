from discord.ext import commands
from discord import app_commands, Interaction

from shared.track_downloader.playlist_downloader import PlaylistDownloader
from shared.track_downloader.song_downloader import SongDownloader
from shared.track_downloader.errors import (
    SpotifyAPIError,
)

import logging

class MusicCommandCog(commands.Cog):
    def __init__(self, bot: commands.Bot, song_downloader: SongDownloader, playlist_downloader: PlaylistDownloader):
        self.bot = bot
        self.song_downloader = song_downloader
        self.playlist_downloader = playlist_downloader

    group = app_commands.Group(name="music", description="Commands for managing tracks, playlists, and the queue")

    @group.command(name="addsong", description="Add a song to the queue by URL (HIGH PRIORITY)")
    @app_commands.describe(track_url="Youtube or Spotify track URL")
    async def add_song(self, interaction: Interaction, track_url: str):
        """
        Adds a song to the queue using the provided track URL.

        :param interaction: The Discord interaction object
        :param track_url: The URL of the track to add
        """
        await interaction.response.defer()

        # Attempt to download the song using the song downloader
        try:
            song_request = await self.song_downloader.download_song_by_url(track_url)
            logging.info(f"User {interaction.user.name} requested to add song: {track_url}")
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
