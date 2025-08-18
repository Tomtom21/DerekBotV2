import os
import logging
from shared.base_bot import BaseBot
from shared.ChatLLMManager import ChatLLMManager
from shared.spotify_api import SpotifyAPI
from shared.youtube_api import YoutubeAPI
from shared.track_downloader.song_downloader import SongDownloader
from shared.track_downloader.playlist_downloader import PlaylistDownloader

# Discord imports
import discord
from discord.ext import commands, tasks
from discord import app_commands

# Cogs
from cogs.music_command_cog import MusicCommandCog

# DB manager config
db_manager_config = {
    "system_config": {
        "select": "*"
    }
}

# Getting the discord bot info
DISCORD_TOKEN = os.environ.get('MUSIC_DISCORD_TOKEN')
OPEN_AI_KEY = os.environ.get('OPEN_AI_KEY')

class Derpods(BaseBot, commands.Bot):
    def __init__(
            self, 
            db_manager_config, 
            OPEN_AI_KEY,
            audio_file_directory="music_files", 
            gpt_prompt_config_column_name="derek_gpt_system_prompt"
    ):
        # Setup intents
        intents = discord.Intents.default()
        intents.guilds = True
        intents.guild_messages = True
        intents.reactions = True
        intents.members = True
        intents.voice_states = True
        intents.message_content = True

        # Use super().__init__ for proper multiple inheritance
        super().__init__(
            db_manager_config=db_manager_config,
            OPEN_AI_KEY=OPEN_AI_KEY,
            audio_file_directory=audio_file_directory,
            gpt_prompt_config_column_name=gpt_prompt_config_column_name,
            command_prefix=None,
            intents=intents,
            case_insensitive=True
        )

        # Initializing track and playlist downloading
        self.spotify_api = SpotifyAPI()
        self.youtube_api = YoutubeAPI()
        self.song_downloader = SongDownloader(
            spotify_api=self.spotify_api,
            youtube_api=self.youtube_api,
            output_path=audio_file_directory
        )
        self.playlist_downloader = PlaylistDownloader(
            spotify_api=self.spotify_api,
            youtube_api=self.youtube_api,
            song_downloader=self.song_downloader
        )

        logging.info("Derpods instance initialized")

    async def setup_hook(self):
        """
        Called by discord.py to set up cogs and sync commands.
        """
        logging.info("Adding cogs...")
        await self.add_cog(MusicCommandCog(
            self,
            song_downloader=self.song_downloader,
            playlist_downloader=self.playlist_downloader
        ))
        await self.tree.sync()
        logging.info("Synced commands and added all cogs")

    async def on_ready(self):
        """
        Called when the bot is ready and connected to Discord.
        """
        logging.info(f"Bot ready event triggered. Logged in as {self.user}")

# Starting the bot
if __name__ == "__main__":
    bot = Derpods(db_manager_config, OPEN_AI_KEY)
    bot.run(DISCORD_TOKEN, log_handler=None, root_logger=True)
