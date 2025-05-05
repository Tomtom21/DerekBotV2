# General imports
import os
import logging
import sys
from shared.numeric_helpers import get_suffix
from shared.data_managers.data_manager import DataManager

# Discord imports
import discord
from discord.ext import commands, tasks
from discord import app_commands

# Setting up logging
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

# Adding a ha
log_handler = logging.StreamHandler()
logging_formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
log_handler.setFormatter(logging_formatter)
logger.addHandler(log_handler)

# DB manager
data_manager = DataManager(
    db_table_names=[
        "unwatched_movies",
        "watched_movies"
    ]
)

# Preventing double logs
logger.propagate = False

logging.root = logger

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


class DerekBot(commands.Bot):
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
    @app_commands.describe(movie_name="Name of the movie to add to the list")
    async def addmovie(self, interaction: discord.Interaction, movie_name: str):
        pass

    @app_commands.command(name="removemovie", description="Remove a movie from the unwatched list")
    @app_commands.describe(movie_index="Index number associated with each movie in the movie list")
    async def removemovie(self, interaction: discord.Interaction, movie_index: int):
        pass

    @app_commands.command(name="markwatched", description="Marks a movie in the unwatched list as watched")
    @app_commands.describe(movie_index="Index number associated with each movie in the movie list")
    async def markwatched(self, interaction: discord.Interaction, movie_index: int):
        pass

    @app_commands.command(name="searchmovie", description="List all movies that contain the keyword (from unwatched list)")
    @app_commands.describe(keyword="Keyword movie name")
    async def searchmovie(self, interaction: discord.Interaction, keyword: str):
        pass

    @app_commands.command(name="randommovie", description="Choose a random movie to watch (from unwatched list)")
    @app_commands.describe(keyword="[OPTIONAL] Keyword movie name")
    async def randommovie(self, interaction: discord.Interaction, keyword: str = ""):
        pass

    @app_commands.command(name="toggletts", description="Enables/Disables TTS in TTS channels (admin only)")
    async def toggletts(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name="ttslang", description="Changes the language of tts (admin only)")
    @app_commands.choices(language=[
        app_commands.Choice(name='english (US)', value=0),
        app_commands.Choice(name='english (UK)', value=1),
        app_commands.Choice(name='english (AU)', value=2),
        app_commands.Choice(name='french', value=3),
        app_commands.Choice(name='german', value=4),
        app_commands.Choice(name='italian', value=5),
        app_commands.Choice(name='portuguese', value=6),
        app_commands.Choice(name='russian', value=7),
        app_commands.Choice(name='spanish', value=8),
        app_commands.Choice(name='moonbase', value=9),
    ])
    async def ttslang(self, interaction: discord.Interaction, language: app_commands.Choice[int]):
        pass

    @app_commands.command(name="vckick", description="Forcefully kick the bot from the VC")
    async def vckick(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name="vcskip", description="Skip to the next tts message")
    async def vcskip(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name="announcename", description="Announce the name of the user when they use vc-text")
    async def announcename(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name="simonsays", description="Repeats what the user says")
    async def simonsays(self, interaction: discord.Interaction, text: str):
        pass

    @app_commands.command(name="magic8ball", description="Replies with a magic 8-ball answer")
    async def magic8ball(self, interaction: discord.Interaction, question: str):
        pass

    @app_commands.command(name="addbirthday", description="Save a birthday for Derek to remember later")
    @app_commands.choices(timezone=[
        app_commands.Choice(name='EST', value="US/Eastern"),
        app_commands.Choice(name='CST', value="US/Central"),
        app_commands.Choice(name='MST', value="US/Mountain"),
        app_commands.Choice(name='PST', value="US/Pacific"),
        app_commands.Choice(name='AKT', value="US/Alaska"),
        app_commands.Choice(name='HAT', value="US/Hawaii"),
        app_commands.Choice(name='CET', value="Europe/Brussels"),
        app_commands.Choice(name='London', value="Europe/London")
    ])
    async def addbirthday(self,
                          interaction: discord.Interaction,
                          month: app_commands.Range[int, 1, 12],
                          day: app_commands.Range[int, 1, 31],
                          year: app_commands.Range[int, 1985, 2010] = -1,
                          timezone: app_commands.Choice[str] = "US/Eastern"):
        pass

    @app_commands.command(name="time", description="Shows the current time in various timezones")
    async def time(self, interaction: discord.Interaction):
        pass

    @app_commands.command(name="featurerq", description="Request a feature to be added in the future")
    async def featurerq(self, interaction: discord.Interaction, request_text: str):
        pass



# Starting the bot
if __name__ == '__main__':
    bot = DerekBot()
    bot.run(DISCORD_TOKEN, log_handler=None)
