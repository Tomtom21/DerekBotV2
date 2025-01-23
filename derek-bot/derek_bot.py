# General imports
import os
import logging
import sys
from libs.numeric_helpers import get_suffix

# Discord imports
import discord
from discord.ext import commands, tasks
from discord import app_commands

# DB imports
from supabase import create_client, Client
from libs.supabase_utils import signin_attempt_loop

# Setting up logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# Adding a ha
log_handler = logging.StreamHandler()
logging_formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
log_handler.setFormatter(logging_formatter)
logger.addHandler(log_handler)

# Preventing double logs
logger.propagate = False

logging.root = logger

# Getting the supabase db info
supabase_url: str = os.environ.get('SUPABASE_URL')
supabase_key: str = os.environ.get('SUPABASE_KEY')
supabase_email: str = os.environ.get('SUPABASE_EMAIL')
supabase_password: str = os.environ.get('SUPABASE_PASSWORD')

# Connecting to the database
supabase: Client = create_client(supabase_url, supabase_key)
signin_attempt_loop(supabase, supabase_email, supabase_password)

# Getting the discord bot info
DISCORD_TOKEN = os.environ.get('MAIN_DISCORD_TOKEN')
OPEN_AI_KEY = os.environ.get('OPEN_AI_KEY')

# Setting up intents for permissions
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.reactions = True
intents.members = True
intents.voice_states = True
intents.message_content = True


# The main code for the bot
class IntentBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, intents=intents, case_insensitive=True)
        self.synced = False

    async def on_ready(self):
        if not self.synced:
            logging.info("Syncing commands...")
            await self.tree.sync()
            self.synced = True
        logging.info(f"Logged in as {self.user}")
        self.start_background_tasks()

    # Starts our TTS and data collection background tasks
    def start_background_tasks(self):
        pass

    # Repeatedly checks to see if there is a new TTS item to say
    @tasks.loop(seconds=1)
    async def tts_check_loop(self):
        pass

    # Checks whether it is someone's birthday, sends a birthday message to the appropriate user
    @tasks.loop(minutes=30)
    async def birthday_check(self):
        pass

    # Changes the status of the bot
    @tasks.loop(minutes=45)
    async def cycle_statuses(self):
        pass

    # Pulls cached info from the database, and updated the local variables for up-to-date values
    @tasks.loop(hours=1)
    async def update_cached_info(self):
        pass

    @app_commands.command(name="unwatchedmovies", description="Show a list of unwatched movies")
    async def unwatchedmovies(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name="watchedmovies", description="Show a list of watched movies")
    async def watchedmovies(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name="addmovie", description="Add a movie to the unwatched list")
    async def addmovie(self, interaction: discord.Interaction, movie_name: str):
        pass

    @app_commands.command(name="removemovie", description="Remove a movie from the unwatched list")
    async def removemovie(self, interaction: discord.Interaction, movie_index: int):
        pass


# Starting the bot
if __name__ == '__main__':
    bot = IntentBot()
    bot.run(DISCORD_TOKEN, log_handler=None)
