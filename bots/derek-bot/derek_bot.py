# General imports
import os
import logging
import re
import time

from shared.data_manager import DataManager
from cogs.movie_cog import MovieGroupCog
from cogs.misc_cog import MiscGroupCog
from cogs.birthday_cog import BirthdayGroupCog
from cogs.ai_cog import AICog
import random
import datetime
import pytz
from shared.numeric_helpers import get_suffix
from shared.TTSManager import TTSManager
from shared.VCAudioManager import VCAudioManager
from shared.cred_utils import save_google_service_file

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
        },
        "system_config": {
            "select": "*"
        },
        "reactions": {
            "select": "*"
        },
        "leave_phrases": {
            "select": "*"
        }
    }
)

# Setting up the google credentials file
save_google_service_file()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-services.json'

# Setting up the TTS manager and VC Audio Manager
tts_manager = TTSManager(os.path.join("tts_files"))
audio_manager = VCAudioManager(tts_manager)

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
    def __init__(self, data_manager: DataManager, tts_manager: TTSManager, audio_manager: VCAudioManager):
        super().__init__(command_prefix=None, intents=intents, case_insensitive=True)

        self.data_manager = data_manager
        self.tts_manager = tts_manager
        self.audio_manager = audio_manager

        self.guild = None
        self.guild_id = None
        self.main_channel_id = None
        self.vc_activity_channel_id = None
        self.joins_leaves_channel_id = None
        self.vc_text_channel_id = None
        self.reactions_list = []

        # Limiting the number of times Derek warns a user that they aren't in a voice channel
        self.last_vc_text_warning_time = 0

        self.tts_enabled = True  # Default to enabled, will be set from DB
        self.last_tts_user_id = None # For not repeating the "___ says:" phrase

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

    def set_config_data_from_db_manager(self):
        """
        Updates variables for variable discord ids to ensure all id information is up to date. Also refreshes reactions
        """
        config_data = self.data_manager.data.get("system_config")

        # If we don't get the config data
        if not config_data:
            return

        # Helper functions to make things cleaner
        def get_config_int(config_name):
            return next((item["config_value_int"] for item in config_data if item["config_name"] == config_name), None)

        def get_config_str(config_name):
            return next((item["config_value_text"] for item in config_data if item["config_name"] == config_name), None)

        def get_config_bool(config_name):
            return next((item["config_value_bool"] for item in config_data if item["config_name"] == config_name), None)

        self.main_channel_id = get_config_int("main_channel_id")
        self.vc_activity_channel_id = get_config_int("vc_activity_channel_id")
        self.joins_leaves_channel_id = get_config_int("joins_leaves_channel_id")
        self.vc_text_channel_id = get_config_int("vc_text_channel_id")
        self.guild_id = get_config_int("guild_id")
        logging.info("Config data from DB set")

        # Updating our list of reactions
        self.reactions_list = self.data_manager.data.get("reactions")
        logging.info("Reactions_list from DB set")

        # Setting VC Audio Manager leave messages
        vc_leave_phrases = [phrase['phrase'] for phrase in self.data_manager.data.get("leave_phrases")]
        self.audio_manager.set_bot_leave_messages(vc_leave_phrases)

        # Set TTS enabled/disabled from system_config
        tts_enabled_config = get_config_bool("tts_enabled")
        if tts_enabled_config:
            self.tts_enabled = tts_enabled_config

    async def on_ready(self):
        logging.info(f"Logged in as {self.user}")
        self.set_config_data_from_db_manager()
        self.guild = self.get_guild(self.guild_id)
        self.start_background_tasks()

    # Starts our TTS and data collection background tasks
    def start_background_tasks(self):
        """
        Starts background processes if they aren't already started
        """
        if not self.refresh_cached_info.is_running():
            self.refresh_cached_info.start()
            logging.info("Local DB Cache refresh process started")

        if not self.birthday_check.is_running():
            self.birthday_check.start()
            logging.info("Birthday check background process started")

        if not self.cycle_statuses.is_running():
            self.cycle_statuses.start()
            logging.info("Status cycling background process started")

        if not self.cycle_nicknames.is_running():
            self.cycle_nicknames.start()
            logging.info("Nickname cycling background process started")

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
                    if self.main_channel_id:
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

                        logging.info(f"Wishing happy birthday to a user")
                        await self.get_channel(self.main_channel_id).send(birthday_string)

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
    async def refresh_cached_info(self):
        self.data_manager.fetch_all_table_data()
        logging.info("Refreshed/updated all table information")

        # Updating our config data periodically incase anything changes
        self.set_config_data_from_db_manager()

    async def give_user_random_nickname(self, user_id):
        """
        Gives a user a random nickname given a user id

        :param user_id: The user id of the user whose nickname we want to change
        """
        nicknames = self.data_manager.data.get("random_user_nicknames")

        # Getting the member and updating their name if nicknames exist
        if nicknames and self.guild:
            try:
                member = self.guild.get_member(user_id)
                nickname_string = random.choice(nicknames)["nickname"]
                await member.edit(nick=nickname_string)
                logging.info(f"Set nickname for user {user_id} to {nickname_string}")
            except Exception as e:
                logging.error(f"Failed to change nickname for user {user_id}: {e}")
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

    async def on_voice_state_update(self, member, before, after):
        """
        Prints a message in a dedicated voice activity channel when a member leaves, joins, or moves voice channels

        :param member: The member whose voice channel activity we're tracking
        :param before: The channel they were in before, None if they were not
        :param after: The channel they were in ebfore, None if they were not
        """
        vc_activity_channel = self.get_channel(self.vc_activity_channel_id)

        # If we have found the vc-activity channel
        if vc_activity_channel:
            # Determining whether someone joined, left, or moved voice channels
            if not before.channel and after.channel:
                await vc_activity_channel.send(
                    f"🟩 ***{member.display_name}** joined {after.channel.name}.*"
                )
            elif before.channel and not after.channel:
                await vc_activity_channel.send(
                    f"🟥 ***{member.display_name}** left {before.channel.name}.*"
                )
            elif before.channel and after.channel:
                if before.channel.id != after.channel.id:
                    await vc_activity_channel.send(
                        f"🔀 ***{member.display_name}** joined {after.channel.name} from {before.channel.name}.*"
                    )
        else:
            logging.warning("Unable to find vc-activity channel. Not sending voice activity.")

    async def on_member_join(self, member):
        """
        Called when a user joins the server, logs the occurrence

        :param member: The user who joined
        """
        logging.info(f"{member.name} has joined the server")

    async def on_member_remove(self, member):
        """
        Called when a member leaves the server, sends a message announcing who the user to leave was

        :param member: The user who left
        """
        logging.info(f"{member.name} has left the server")
        joins_leaves_channel = self.get_channel(self.joins_leaves_channel_id)
        if joins_leaves_channel:
            await joins_leaves_channel.send(f"<@{member.id}> has left the server")

    async def on_message(self, message):
        # Reacting to messages using the regex strings found in the DB
        for reaction in self.reactions_list:
            match = re.search(reaction["regex"], message.content)
            if match:
                try:
                    await message.add_reaction(reaction["emoji"])
                except Exception as e:
                    logging.error(f"Failed to add reaction to message '{message.content[:25]}': {e}")

        # TTS processing. Checking if messages are in the tts channel, are not from the bot, and tts is enabled
        if self.tts_enabled and message.channel.id == self.vc_text_channel_id and message.author != self.user:

            # Making sure that they are in a voice channel
            if message.author.voice and message.author.voice.channel:
                # Getting the user and checking if they have announce name enabled
                db_user = self.data_manager.get_item_by_key(
                    table_name="users",
                    key="user_id",
                    value=message.author.id
                )
                if db_user and db_user.get("vc_text_announce_name") and self.last_tts_user_id != message.author.id:
                    final_tts_message = f"{message.author.name} says: {message.content}"
                    self.last_tts_user_id = message.author.id
                else:
                    final_tts_message = message.content

                # Generating the audio file and adding it to the queue for VC
                file_path = self.tts_manager.process(final_tts_message)
                if file_path:
                    await self.audio_manager.add_to_queue(file_path, message.author.voice.channel)
            else:
                # If Derek hasn't warned a user of not being in the VC within the past 3 minutes, warn them
                if time.time() - self.last_vc_text_warning_time >= 180:
                    logging.info(f"Warning user {message.author.name} that they aren't in a voice channel")
                    await message.reply("No voice channel detected")
                    self.last_vc_text_warning_time = time.time()

# Starting the bot
if __name__ == '__main__':
    bot = DerekBot(db_manager, tts_manager, audio_manager)
    bot.run(DISCORD_TOKEN, log_handler=None, root_logger=True)
