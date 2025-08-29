import logging

from discord.ext import commands
from discord import app_commands, Interaction, ButtonStyle, Member

from shared.track_downloader.playlist_downloader import PlaylistDownloader
from shared.track_downloader.song_downloader import SongDownloader
from shared.track_downloader.errors import (
    SpotifyAPIError,
    URLClassificationError,
    MediaTypeMismatchError,
)
from shared.music_service import MusicService, NotInVoiceChannelError
from shared.DiscordList import DiscordList

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

    async def ensure_in_voice_channel(self, interaction: Interaction):
        """
        Ensures that the user is in a voice channel before proceeding with a music command.
        :param interaction: The Discord interaction object
        :raises NotInVoiceChannelError: If the user is not in a voice channel
        """
        if not interaction.user.voice or not interaction.user.voice.channel:
            raise NotInVoiceChannelError

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
            await self.ensure_in_voice_channel(interaction)
        except NotInVoiceChannelError as error:
            await error.handle_error(interaction, requires_followup=True)
            return

        # Attempt to download the song using the song downloader
        try:
            song_request = await self.music_service.download_and_queue_song(
                song_url,
                interaction.user,
                high_priority=True
            )
            logging.info(f"User {interaction.user.name} requested to add song: {song_url}")
            await interaction.followup.send(f"Added **{song_request.title}** to the queue.")
        except SpotifyAPIError as e:
            logging.error(f"Spotify API error while downloading song: {e}")
            await interaction.followup.send("`Failed to download song from Spotify.`")
            return
        except (URLClassificationError, MediaTypeMismatchError) as e:
            logging.error(f"URL classification error while downloading song: {e}")
            await interaction.followup.send("`Invalid or unsupported song URL.`")
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

    @group.command(name="queue", description="Show the current music queue")
    async def queue(self, interaction: Interaction):
        """
        Displays the current music queue.

        :param interaction: The Discord interaction object
        """
        def get_queue_data():
            """
            Returns the current music queue.
            """
            def format_duration(seconds):
                if seconds is None:
                    return "??:??"
                minutes = int(seconds // 60)
                secs = int(seconds % 60)
                return f"{minutes:02d}:{secs:02d}"

            return [
                f"*{audio_item.audio_name}*, [{format_duration(audio_item.duration)}] • {audio_item.added_by}"
                for audio_item in self.music_service.audio_manager.queue
            ]

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
            title="Song Queue",
            have_pages=False,
            add_refresh_button=True
        )

        # Adding current metadata
        discord_list.add_metadata("🎶 **Cᴜʀʀᴇɴᴛ Sᴏɴɢ**", get_current_audio_name)
        discord_list.add_metadata("🔎 **Rᴇᴏ̨ᴜᴇsᴛᴇᴅ ʙʏ**", get_current_audio_added_by)
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
