import logging

from discord.ext import commands
from discord import app_commands, Interaction, ButtonStyle, Member

from shared.track_downloader.playlist_downloader import PlaylistDownloader
from shared.track_downloader.song_downloader import SongDownloader
from shared.spotify_api import SpotifyAPI
from shared.youtube_api import YoutubeAPI
from shared.track_downloader.models import PlaylistRequest, SongRequest
from shared.track_downloader.errors import (
    SpotifyAPIError,
    URLClassificationError,
    MediaTypeMismatchError,
    URLValidationError,
    DownloadError,
    YouTubeSearchError,
    YoutubePlaylistFetchError,
    SpotifyListFetchError,
    AgeRestrictedContentError,
    LiveContentError
)
from shared.music_service import MusicService
from shared.errors import NotInVoiceChannelError
from shared.discord_ui.DiscordList import DiscordList
from shared.discord_ui.confirmation_prompt import ConfirmationPrompt
from shared.discord_utils import ensure_in_voice_channel

class MusicCommandCog(commands.Cog):
    def __init__(
            self,
            bot: commands.Bot,
            spotify_api: SpotifyAPI,
            youtube_api: YoutubeAPI,
            music_service: MusicService
    ):
        self.bot = bot
        self.spotify_api = spotify_api
        self.youtube_api = youtube_api
        self.music_service = music_service

    group = app_commands.Group(
        name="music",
        description="Commands for managing tracks, playlists, and the queue"
    )

    async def _handle_common_errors(self, interaction, error):
        """
        Handles errors common to both song and playlist commands.

        :param interaction: The Discord interaction object
        :param error: The exception that was raised
        :return: True if the error was handled, False otherwise
        """
        if isinstance(error, MediaTypeMismatchError):
            logging.error(f"Media type mismatch: {error}")
            await interaction.followup.send(
                "`The command cannot process the provided URL. "
                "Did you provide a playlist URL instead of a song URL (or vice versa)?`"
            )
            return True
        elif isinstance(error, URLValidationError):
            logging.error(f"URL validation error: {error}")
            await interaction.followup.send(
                "`The provided URL is invalid. Ensure it is a supported URL.`"
            )
            return True
        elif isinstance(error, URLClassificationError):
            logging.error(f"URL classification error: {error}")
            await interaction.followup.send("`Unable to identify url type.`")
            return True
        return False

    async def _handle_song_errors(self, interaction, error):
        """
        Handles common errors for song-related commands.
        
        :param interaction: The Discord interaction object
        :param error: The exception that was raised
        """
        if await self._handle_common_errors(interaction, error):
            return
        elif isinstance(error, DownloadError):
            logging.error(f"Download error: {error}")
            await interaction.followup.send("`Failed to download song.`")
        elif isinstance(error, YouTubeSearchError):
            logging.error(f"YouTube search error: {error}")
            await interaction.followup.send("`Failed to search for song on YouTube.`")
        elif isinstance(error, SpotifyAPIError):
            logging.error(f"Spotify API error: {error}")
            await interaction.followup.send("`Failed to make Spotify API request.`")
        elif isinstance(error, AgeRestrictedContentError):
            logging.error(f"Age-restricted content error: {error}")
            await interaction.followup.send("`Song is age-restricted and cannot be downloaded.`")
        elif isinstance(error, LiveContentError):
            logging.error(f"Live content error: {error}")
            await interaction.followup.send("`Song is a live/premiere and cannot be downloaded.`")
        else:
            logging.error(f"Unhandled error: {error}")
            await interaction.followup.send("`An unexpected error occurred.`")

    async def _handle_playlist_errors(self, interaction, error):
        """
        Handles common errors for playlist-related commands.

        :param interaction: The Discord interaction object
        :param error: The exception that was raised
        """
        if await self._handle_common_errors(interaction, error):
            return
        elif isinstance(error, YoutubePlaylistFetchError):
            logging.error(f"YouTube playlist fetch error: {error}")
            await interaction.followup.send("`Failed to fetch playlist from YouTube.`")
        elif isinstance(error, SpotifyListFetchError):
            logging.error(f"Spotify list fetch error: {error}")
            await interaction.followup.send("`Failed to fetch list from Spotify. Is the playlist public?`")
        else:
            logging.error(f"Unhandled playlist error: {error}")
            await interaction.followup.send(
                "`An unexpected error occurred while processing the playlist.`"
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

        # Ensure the user is in a voice channel
        try:
            ensure_in_voice_channel(interaction)
        except NotInVoiceChannelError as error:
            await error.handle_error(interaction, requires_followup=True)
            return

        # Attempt to download the song using the song downloader
        try:
            song_request = await self.music_service.download_and_queue_song_from_url(
                song_url,
                interaction.user
            )
            logging.info(f"User {interaction.user.name} requested to add song: {song_url}")
            await interaction.followup.send(f"Added **{song_request.title}** to the queue.")
        except Exception as e:
            await self._handle_song_errors(interaction, e)
            return

    @group.command(name="searchsong", description="Search for a song and add to the queue")
    @app_commands.describe(search_query="The search query to find the song")
    async def search_song(self, interaction: Interaction, search_query: str):
        """
        Searches for a song using the provided search query.

        :param interaction: The Discord interaction object
        :param search_query: The search query to find the song
        """
        await interaction.response.defer()

        # Ensure the user is in a voice channel
        try:
            ensure_in_voice_channel(interaction)
        except NotInVoiceChannelError as error:
            await error.handle_error(interaction, requires_followup=True)
            return

        # Attempt to download the song using the search query
        try:
            song_request = await self.music_service.download_and_queue_song_from_query(
                search_query,
                interaction.user
            )
            logging.info(f"User {interaction.user.name} requested to search song: {search_query}")
            await interaction.followup.send(f"Added **{song_request.title}** to the queue.")
        except Exception as e:
            await self._handle_song_errors(interaction, e)
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

        # Ensure the user is in a voice channel
        try:
            ensure_in_voice_channel(interaction)
        except NotInVoiceChannelError as error:
            await error.handle_error(interaction, requires_followup=True)
            return

        # Getting information about our playlist
        try:
            playlist_request = PlaylistRequest(playlist_url)
            await playlist_request.fetch_items(self.spotify_api, self.youtube_api, amount, start_at)
        except Exception as e:
            await self._handle_playlist_errors(interaction, e)
            return

        # Defining a callback that runs to start the downloading process
        async def on_confirm_callback(interaction: Interaction):
            async def noop_callback(download_result: SongRequest):
                pass
            await self.music_service.download_and_queue_playlist(
                playlist_request=playlist_request,
                callback_func=noop_callback,
                user=interaction.user
            )

        # Showing a confirmation prompt on whether to load the playlist or not.
        confirmation_prompt = ConfirmationPrompt(
            title="Confirm Playlist Load",
            description=(
                f"Do you want to load the playlist **{playlist_request.title}**? "
                f"**{amount}** song(s) will be added to the queue, starting from "
                f"position **{start_at}**."
            ),
            on_confirm_callback=on_confirm_callback,
            status_confirmed_msg="✅ Confirmed. The playlist will start being loaded into the queue."
        )
        sent_message = await interaction.followup.send(
            confirmation_prompt.get_message(),
            view=confirmation_prompt.create_view()
        )
        confirmation_prompt.message = sent_message

    @group.command(name="queue", description="Show the current music queue")
    async def queue(self, interaction: Interaction):
        """
        Displays the current music queue.

        :param interaction: The Discord interaction object
        """
        def format_duration(seconds):
            if seconds is None:
                return "??:??"
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"
        
        def get_queue_data():
            """
            Returns the current music queue.
            """
            items = []
            for audio_item in self.music_service.audio_manager.queue:
                priority_icon = "🔴" if audio_item.high_priority else "⚫"
                items.append(f"{priority_icon} **{audio_item.audio_name}**, [{format_duration(audio_item.duration)}] • *{audio_item.added_by}*")
            return items

        def get_current_audio_name():
            """
            Returns the currently playing audio item.
            """
            current_audio_item = self.music_service.audio_manager.current_audio_item
            return f"{current_audio_item.audio_name}" if current_audio_item else "N/A"

        def get_current_audio_added_by():
            """
            Returns who added the currently playing audio item.
            """
            current_audio_item = self.music_service.audio_manager.current_audio_item
            return f"{current_audio_item.added_by}" if current_audio_item else "N/A"

        def get_current_audio_duration():
            """
            Returns the duration of the currently playing audio item.
            """
            current_audio_item = self.music_service.audio_manager.current_audio_item
            return format_duration(current_audio_item.duration) if current_audio_item else "??:??"

        def get_current_audio_state():
            """
            Returns the current state of the audio player.
            """
            return self.music_service.audio_manager.current_state.value

        async def play_button(interaction: Interaction):
            self.music_service.audio_manager.resume_current()

        async def pause_button(interaction: Interaction):
            self.music_service.audio_manager.pause_current()

        async def skip_button(interaction: Interaction):
            self.music_service.audio_manager.skip_current()

        await interaction.response.defer()

        # Defining our list
        discord_list = DiscordList(
            get_items=get_queue_data,
            title="🎧 Song Queue",
            have_pages=False,
            add_refresh_button=True
        )

        # Adding current metadata
        discord_list.add_metadata("🎶 **Cᴜʀʀᴇɴᴛ Sᴏɴɢ**", get_current_audio_name)
        discord_list.add_metadata("🔎 **Rᴇᴏ̨ᴜᴇsᴛᴇᴅ ʙʏ**", get_current_audio_added_by)
        discord_list.add_metadata("⏱️ **Dᴜʀᴀᴛɪᴏɴ**", get_current_audio_duration)
        discord_list.add_metadata("⏯️ **Sᴛᴀᴛᴜs**", get_current_audio_state)

        # Adding hints at the bottom of the queue
        discord_list.add_hint("❕ Usᴇ /ᴀᴅᴅsᴏɴɢ ᴏʀ /ᴀᴅᴅᴘʟᴀʏʟɪsᴛ ᴛᴏ ᴏ̨ᴜᴇᴜᴇ ᴀɴᴏᴛʜᴇʀ sᴏɴɢ!")

        # Adding custom buttons for controlling playback
        discord_list.add_custom_button(
            "⏵", 
            play_button,
            ButtonStyle.green
        )
        discord_list.add_custom_button(
            "⏸", 
            pause_button,
            ButtonStyle.blurple
        )
        discord_list.add_custom_button(
            "Skip", 
            skip_button,
            ButtonStyle.red
        )

        await interaction.followup.send(
            discord_list.get_page(),
            view=discord_list.create_view()
        )

    @group.command(name="skipall", description="Skip all songs in the queue and stop playback")
    async def skip_all(self, interaction: Interaction):
        """
        Skips all songs in the queue and stops the currently playing audio.
        """
        await interaction.response.defer()

        # Defining a callback that runs when we confirm to skip all
        async def on_confirm_callback(interaction: Interaction):
            # We don't need to capture the return value.
            # The confirmation prompt will just inform the user of the attempt.
            _ = self.music_service.audio_manager.skip_all()

        # Showing a confirmation prompt on whether to skip all songs or not.
        confirmation_prompt = ConfirmationPrompt(
            title="Skip All Songs?",
            description=(
                f"Are you sure you want to skip all songs in the queue? This also stops any "
                f"currently playing song."
            ),
            on_confirm_callback=on_confirm_callback,
            status_confirmed_msg="✅ Confirmed. Skipping all songs."
        )
        sent_message = await interaction.followup.send(
            confirmation_prompt.get_message(),
            view=confirmation_prompt.create_view()
        )
        confirmation_prompt.message = sent_message
