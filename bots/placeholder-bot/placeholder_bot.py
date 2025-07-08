# General imports
import logging
import os

# Discord imports
import discord
from discord.ext import commands

# Setting up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

# Getting the discord bot info
DISCORD_TOKEN = os.environ.get('PLACEHOLDER_DISCORD_TOKEN')

# Setting up intents for permissions
intents = discord.Intents.default()

class PlaceholderBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=None, intents=intents, case_insensitive=True)

    async def setup_hook(self):
        logging.info("Syncing without cogs to remove commands")
        await self.tree.sync()

# Starting the bot
if __name__ == '__main__':
    bot = PlaceholderBot()
    bot.run(DISCORD_TOKEN)

