# General imports
import os
import logging

# Discord imports
import discord
from discord.ext import commands
from discord import app_commands

# DB imports
from supabase import create_client, Client
from libs.supabase_utils import signin_attempt_loop

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

# Setting up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

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


# Starting the bot
bot = IntentBot()
bot.run(DISCORD_TOKEN, log_handler=None)
