# General imports
import os
import logging

from cogs.bot_management_cog import BotManagementGroupCog

# Discord imports
import discord
from discord.ext import commands, tasks
from discord import app_commands

# Setting the discord bot info
LUCA_TOKEN = os.environ.get("LUCA_DISCORD_TOKEN")

# Setting up intents for permissions
intents = discord.Intents.default()

# List of bot images to keep track of
bot_image_names = [
    "derek-bot-image",
    "luca-image"
]

class Luca(commands.bot):
    def __init__(self, bot_image_names):
        super().__init__(command_prefix=None, intents=intents, case_insensitive=True)
        
        self.bot_image_names = bot_image_names

        logging.info("Luca instance initialized.")

    async def setup_hook(self):
        """
        Called by discord.py to set up cogs and sync commands.
        """
        logging.info("Adding cogs...")
        # await self.add_cog(BotManagementGroupCog(self))
        logging.info("Synced commands and added all cogs")

    async def on_ready(self):
        """
        Called when the bot is ready and connected to Discord.
        """
        logging.info(f"Bot ready event triggered. Logged in as {self.user}")
        self.start_background_tasks()

    def start_background_tasks(self):
        """
        Starts background processes if they aren't already started
        """
        if not self.bot_state_refresh.is_running():
            self.bot_state_refresh.start()
            logging.info("Bot state refresh background process started")

    @tasks.loop(minutes=1)
    async def bot_state_refresh(self):
        """
        Refreshes information and restarts bot images that have failed
        """
        pass

# Starting the bot
if __name__ == '__main__':
    bot = Luca(bot_image_names)
    bot.run(LUCA_TOKEN, log_handler=None, root_logger=True)
