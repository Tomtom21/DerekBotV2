"""
This is the Derpods Discord bot, which provides music playback for Discord servers.
"""

import os
import logging
from distutils.util import strtobool


import discord
from discord.ext import tasks
from discord import app_commands

from cogs.music_command_cog import MusicCommandCog
from shared.base_bot import BaseBot
from shared.ChatLLMManager import ChatLLMManager
from shared.spotify_api import SpotifyAPI
from shared.youtube_api import YoutubeAPI
from shared.track_downloader.song_downloader import SongDownloader
from shared.track_downloader.playlist_downloader import PlaylistDownloader
from shared.music_service import MusicService
from ai_tools.song_tools import SongTools
from ai_tools.tool_configs import tool_definitions

# DB manager config
db_manager_config = {
    "system_config": {
        "select": "*"
    }
}

# Getting the discord bot info
DISCORD_TOKEN = os.environ.get('MUSIC_DISCORD_TOKEN')
OPEN_AI_KEY = os.environ.get('OPEN_AI_KEY')

class Derpods(BaseBot):
    """
    Discord bot for music playback and management in Discord servers.

    Derpods extends BaseBot and commands.Bot, providing:
    - Music playback via Spotify and YouTube integration
    - Downloading individual songs and playlists
    - Custom GPT-based chat interactions
    - Command handling through Discord's app commands and cogs

    Initialization sets up APIs, downloaders, and Discord intents.
    """
    def __init__(
            self,
            db_config,
            open_ai_key,
            audio_file_directory="music_files",
            gpt_prompt_config_column_name="derpods_gpt_system_prompt"
    ):
        # Setup intents
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        intents.reactions = True
        intents.members = True
        intents.voice_states = True
        intents.message_content = True

        # Initialize BaseBot first (no cogs, no LLM/tools)
        super().__init__(
            db_manager_config=db_config,
            open_ai_key=open_ai_key,
            audio_file_directory=audio_file_directory,
            gpt_prompt_config_column_name=gpt_prompt_config_column_name,
            command_prefix=None,
            intents=intents,
            case_insensitive=True
        )

        # Setting the derpods leave message
        self.audio_manager.set_volume(0.25)
        self.audio_manager.set_bot_leave_messages(["Derpods is disconnecting."])

        # Now set up the APIs, downloaders, and music service
        self.spotify_api = SpotifyAPI()
        self.youtube_api = YoutubeAPI()
        self.song_downloader = SongDownloader(
            spotify_api=self.spotify_api,
            youtube_api=self.youtube_api,
            output_path=audio_file_directory
        )
        self.playlist_downloader = PlaylistDownloader(
            song_downloader=self.song_downloader
        )
        self.music_service = MusicService(
            song_downloader=self.song_downloader,
            playlist_downloader=self.playlist_downloader,
            audio_manager=self.audio_manager
        )

        # Setting up song tools
        self.song_tools = SongTools(self.music_service)
        tool_references = {
            "play_song_url": self.song_tools.play_song_url,
            "play_song_search": self.song_tools.play_song_search,
            "skip_song": self.song_tools.skip_song
        }

        # Updating the LLM manager with tools
        self.llm_manager.set_tool_function_references(tool_references)
        self.llm_manager.set_tool_definitions(tool_definitions)

        # Set metadata function for LLM manager
        self.llm_manager.set_get_metadata(self.get_current_audio_metadata)

        # Set up command cogs
        cogs = [
            MusicCommandCog(
                self,
                spotify_api=self.spotify_api,
                youtube_api=self.youtube_api,
                music_service=self.music_service
            )
        ]
        self.add_command_cogs(cogs)

        logging.info("Derpods instance initialized")

    def extract_config_values(self, config_data):
        self.guild_id = self._get_config_value(config_data, "guild_id", "int")

    async def on_ready(self):
        """
        Extending the on_ready event to set the song tools guild.
        """
        await super().on_ready()
        self.song_tools.set_guild(self.guild)

    def get_current_audio_metadata(self):
        """
        Returns metadata about the currently playing audio for the LLM.
        """
        current_audio = self.audio_manager.current_audio_item
        if current_audio:
            audio_name = current_audio.audio_name or "Unknown"
            added_by = current_audio.added_by or "Unknown"
            return f"Current Audio: '{audio_name}' (Recommended by: {added_by})"
        else:
            return "No audio is currently playing."

# Starting the bot
if __name__ == "__main__":
    bot = Derpods(db_manager_config, OPEN_AI_KEY)
    bot.run(DISCORD_TOKEN, log_handler=None, root_logger=True)
