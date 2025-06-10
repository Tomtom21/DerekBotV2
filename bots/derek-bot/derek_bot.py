# General imports
import os
import logging
from shared.data_manager import DataManager
from cogs.movie_cog import MovieGroupCog
from cogs.misc_cog import MiscGroupCog
from cogs.birthday_cog import BirthdayGroupCog
from cogs.ai_cog import AICog
import random
import datetime
import pytz
from shared.numeric_helpers import get_suffix

# Discord imports
import discord
from discord.ext import commands, tasks
from discord import app_commands

# Setting up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s'
)

# DB manager
db_manager = DataManager(
    {
        "unwatched_movies": {
            "select": "*, added_by(*)",
            "order_by": {"column": "movie_name", "ascending": True}
        },
        "watched_movies": {
            "select": "*, added_by(*)",
            "order_by": {"column": "movie_name", "ascending": True}
        },
        "movie_phrases": {
            "select": "*"
        },
        "eight_ball_phrases": {
            "select": "*"
        },
        "users": {
            "select": "*"
        },
        "birthdays": {
            "select": "*"
        },
        "birthday_tracks": {
            "select": "*"
        },
        "statuses": {
            "select": "*"
        },
        "chat_memories": {
            "select": "*, added_by(*)",
            "order_by": {"column": "created", "ascending": False}
        },
        "random_user_nicknames": {
            "select": "*, added_by(*)",
            "order_by": {"column": "created", "ascending": False}
        }
    }
)

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
    def __init__(self, data_manager: DataManager):
        super().__init__(command_prefix=None, intents=intents, case_insensitive=True)

        self.data_manager = data_manager

        self.guild = None
        self.MAIN_CHANNEL_ID = self.get_discord_id_from_env("MAIN_CHANNEL_ID")

    @staticmethod
    def get_discord_id_from_env(env_var_name):
        val = os.environ.get(env_var_name)
        return int(val) if val is not None else None

    async def setup_hook(self):
        await self.add_cog(MovieGroupCog(self, self.data_manager))
        await self.add_cog(MiscGroupCog(self, self.data_manager))
        await self.add_cog(BirthdayGroupCog(self, self.data_manager))
        await self.add_cog(AICog(self, self.data_manager))
        await self.tree.sync()
        logging.info("Synced commands")

    async def on_ready(self):
        logging.info(f"Logged in as {self.user}")
        self.guild = self.get_guild(self.get_discord_id_from_env("NICKNAME_SHUFFLE_GUILD_ID"))
        self.start_background_tasks()

    # Starts our TTS and data collection background tasks
    def start_background_tasks(self):
        """
        Starts background processes if they aren't already started
        """
        if not self.birthday_check.is_running():
            self.birthday_check.start()
            logging.info("Birthday check background process started")

        if not self.cycle_statuses.is_running():
            self.cycle_statuses.start()
            logging.info("Status cycling background process started")

        if not self.cycle_nicknames.is_running():
            self.cycle_nicknames.start()
            logging.info("Nickname cycling background process started")

        # self.update_cached_info.start()

    # Repeatedly checks to see if there is a new TTS item to say
    @tasks.loop(seconds=1)
    async def tts_check_loop(self):
        pass

    # Checks whether it is someone's birthday, sends a birthday message to the appropriate user
    @tasks.loop(minutes=30)
    async def birthday_check(self):
        date = datetime.datetime.now()
        for birthday in self.data_manager.data.get("birthdays"):
            # Getting the current date for the birthday's timezone
            timezone_date = date.astimezone(pytz.timezone(birthday["timezone"]))

            # If a birthday matches the timezone data
            if timezone_date.month == birthday["month"] and timezone_date.day == birthday["day"]:
                # If the birthday is not already marked for this year, say something and mark it
                if not any(
                        (birthday_track["birthday_id"] == birthday["id"]) and
                        (birthday_track["year"] == timezone_date.year)
                        for birthday_track in self.data_manager.data.get("birthday_tracks")
                ):
                    # Making sure that we have a channel id to send to
                    if self.MAIN_CHANNEL_ID:
                        # Updating the birthday tracking table
                        self.data_manager.add_table_data(
                            table_name="birthday_tracks",
                            json_data={"birthday_id": birthday["id"], "year": timezone_date.year}
                        )

                        # Sending a birthday message
                        birthday_string = f"<@{birthday['user_id']}> Happy"
                        if birthday["year"]:
                            age = timezone_date.year - birthday["year"]
                            suffix = get_suffix(age)
                            birthday_string += f" {age}{suffix}"
                        birthday_string += f" birthday!"

                        await self.get_channel(self.MAIN_CHANNEL_ID).send(birthday_string)

    # Changes the status of the bot
    @tasks.loop(minutes=45)
    async def cycle_statuses(self):
        statuses = self.data_manager.data.get("statuses")
        random_status_string = random.choice(statuses).get("status", "")

        # Setting the status based on the status type
        if random_status_string.startswith("$p "):
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.playing,
                    name=random_status_string[3:]
                )
            )
        elif random_status_string.startswith("$l "):
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.listening,
                    name=random_status_string[3:]
                )
            )
        elif random_status_string.startswith("$w "):
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=random_status_string[3:]
                )
            )

    # Pulls cached info from the database, and updated the local variables for up-to-date values
    @tasks.loop(hours=1)
    async def update_cached_info(self):
        self.data_manager.fetch_all_table_data()
        logging.info("Updated all table information")

    async def give_user_random_nickname(self, user_id):
        """
        Gives a user a random nickname given a user id

        :param user_id: The user id of the user whose nickname we want to change
        """
        nicknames = self.data_manager.data.get("random_user_nicknames")

        # Getting the member and updating their name if nicknames exist
        if nicknames:
            member = self.guild.get_member(user_id)
            await member.edit(nick=random.choice(nicknames)["nickname"])
        else:
            logging.warning(f"No nicknames found in database. Not updating nickname for user {user_id}")

    @tasks.loop(hours=24)
    async def cycle_nicknames(self):
        """
        Participating users will have their nickname set to a random nickname on a daily basis
        """
        # Getting participating users
        user_ids_to_update = [
            user["user_id"]
            for user in self.data_manager.data.get("users")
            if user["shuffle_nickname"] is True
        ]

        # Looping through users and giving them a random nickname
        for user_id in user_ids_to_update:
            await self.give_user_random_nickname(user_id)

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
    bot = DerekBot(db_manager)
    bot.run(DISCORD_TOKEN, log_handler=None, root_logger=True)
