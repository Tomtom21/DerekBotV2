# General imports
import os
import logging
import re
import time
import io

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
from shared.ChatLLMManager import ChatLLMManager, ConversationCache
from ai_tools.memory_tools import MemoryTools
from ai_tools.color_tools import generate_color_swatch
from ai_tools.tool_configs import tool_definitions
from ai_tools.weather_tools import get_spc_outlook_text, get_spc_outlook_image, get_local_forecast

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

# Conversation cache for message caching
conversation_cache = ConversationCache()

# Getting GPT config info
gpt_system_prompt = db_manager.get_item_by_key(
    table_name="system_config",
    key="config_name",
    value="derek_gpt_system_prompt"
).get("config_value_text")
if not gpt_system_prompt:
    raise ValueError("gpt_system_prompt cannot be None. There was an issue pulling info from the DB.")

memory_tools = MemoryTools(db_manager=db_manager)
tool_references = {
    "save_memory": memory_tools.save_memory,
    "generate_color_swatch": generate_color_swatch,
    "get_spc_outlook_text": get_spc_outlook_text,
    "get_spc_outlook_image": get_spc_outlook_image,
    "get_local_forecast": get_local_forecast
}

# Setting up the GPT model
llm_manager = ChatLLMManager(
    api_key=OPEN_AI_KEY,
    system_prompt=gpt_system_prompt,
    tool_function_references=tool_references,
    tool_definitions=tool_definitions,
    get_memories=memory_tools.get_memories
)


# Setting up intents for permissions
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.reactions = True
intents.members = True
intents.voice_states = True
intents.message_content = True


class DerekBot(commands.Bot):
    def __init__(self, data_manager: DataManager,
                 tts_manager: TTSManager,
                 audio_manager: VCAudioManager,
                 conversation_cache: ConversationCache,
                 llm_manager: ChatLLMManager):
        """
        Initializes the DerekBot instance.

        :param data_manager: The DataManager instance for DB access
        :param tts_manager: The TTSManager instance for TTS features
        :param audio_manager: The VCAudioManager instance for VC audio
        :param conversation_cache: The ConversationCache instance for message caching
        :param llm_manager: The ChatLLMManager instance for LLM features
        """
        super().__init__(command_prefix=None, intents=intents, case_insensitive=True)

        self.data_manager = data_manager
        self.tts_manager = tts_manager
        self.audio_manager = audio_manager
        self.conversation_cache = conversation_cache
        self.llm_manager = llm_manager

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

        logging.info("DerekBot instance initialized")

    async def setup_hook(self):
        """
        Called by discord.py to set up cogs and sync commands.
        """
        logging.info("Adding cogs...")
        await self.add_cog(MovieGroupCog(self, self.data_manager))
        await self.add_cog(MiscGroupCog(self, self.data_manager))
        await self.add_cog(BirthdayGroupCog(self, self.data_manager))
        await self.add_cog(AICog(self, self.data_manager))
        await self.tree.sync()
        logging.info("Synced commands and added all cogs")

    def set_config_data_from_db_manager(self):
        """
        Updates variables for Discord IDs and other config data from the database.
        Also refreshes reactions, TTS, and LLM settings.
        """
        logging.info("Setting config data from DB manager")
        config_data = self.data_manager.data.get("system_config")

        # If we don't get the config data
        if not config_data:
            logging.warning("No config data found in DB")
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

        # Setting the GPT system prompt
        gpt_system_prompt = get_config_str("derek_gpt_system_prompt")
        self.llm_manager.set_system_prompt(gpt_system_prompt)

    async def on_ready(self):
        """
        Called when the bot is ready and connected to Discord.
        Sets up config data, guild, background tasks, and updates the conversation cache.
        """
        logging.info(f"Bot ready event triggered. Logged in as {self.user}")
        self.set_config_data_from_db_manager()
        self.guild = self.get_guild(self.guild_id)
        if self.guild:
            logging.info(f"Guild set: {self.guild.name} ({self.guild_id})")
        else:
            logging.warning(f"Guild with ID {self.guild_id} not found")
        self.start_background_tasks()
        self.conversation_cache.update_bot_user_id(self.user.id)

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

    # Checks whether it is someone's birthday, sends a birthday message to the appropriate user
    @tasks.loop(minutes=30)
    async def birthday_check(self):
        """
        Checks if it is any user's birthday and sends a birthday message if so.
        """
        date = datetime.datetime.now()
        logging.info("Running birthday check loop")

        # Making sure that we have a channel id to send to
        if self.main_channel_id:
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
        else:
            logging.warning("Main channel ID not set, cannot send birthday message")

    # Changes the status of the bot
    @tasks.loop(minutes=45)
    async def cycle_statuses(self):
        """
        Changes the bot's status message at regular intervals.
        """
        statuses = self.data_manager.data.get("statuses")
        random_status_string = random.choice(statuses).get("status", "")
        logging.info(f"Cycling status to: {random_status_string}")

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
        """
        Refreshes cached info from the database and updates config data.
        """
        logging.info("Refreshing cached info from DB")
        self.data_manager.fetch_all_table_data()
        logging.info("Refreshed/updated all table information")

        # Updating our config data periodically incase anything changes
        self.set_config_data_from_db_manager()

    async def give_user_random_nickname(self, user_id):
        """
        Gives a user a random nickname given a user id.

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
            logging.warning(f"No nicknames found in database or guild not set. Not updating nickname for user {user_id}")

    @tasks.loop(hours=24)
    async def cycle_nicknames(self):
        """
        Sets a random nickname for participating users on a daily basis.
        """
        logging.info("Cycling nicknames for users who opted in")
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
        Sends a message in the voice activity channel when a member joins, leaves, or moves voice channels.

        :param member: The member whose voice channel activity we're tracking
        :param before: The channel they were in before, None if they were not
        :param after: The channel they are in after, None if they are not
        """
        vc_activity_channel = self.get_channel(self.vc_activity_channel_id)

        # If we have found the vc-activity channel
        if vc_activity_channel:
            # Determining whether someone joined, left, or moved voice channels
            if not before.channel and after.channel:
                logging.info(f"{member.display_name} joined {after.channel.name}")
                await vc_activity_channel.send(
                    f"🟩 ***{member.display_name}** joined {after.channel.name}.*"
                )
            elif before.channel and not after.channel:
                logging.info(f"{member.display_name} left {before.channel.name}")
                await vc_activity_channel.send(
                    f"🟥 ***{member.display_name}** left {before.channel.name}.*"
                )
            elif before.channel and after.channel:
                if before.channel.id != after.channel.id:
                    logging.info(f"{member.display_name} moved from {before.channel.name} to {after.channel.name}")
                    await vc_activity_channel.send(
                        f"🔀 ***{member.display_name}** joined {after.channel.name} from {before.channel.name}.*"
                    )
        else:
            logging.warning("Unable to find vc-activity channel. Not sending voice activity.")

    async def on_member_join(self, member):
        """
        Called when a user joins the server, logs the occurrence.

        :param member: The user who joined
        """
        logging.info(f"{member.name} has joined the server (ID: {member.id})")

    async def on_member_remove(self, member):
        """
        Called when a member leaves the server, sends a message announcing who left.

        :param member: The user who left
        """
        logging.info(f"{member.name} has left the server (ID: {member.id})")
        joins_leaves_channel = self.get_channel(self.joins_leaves_channel_id)
        if joins_leaves_channel:
            await joins_leaves_channel.send(f"<@{member.id}> has left the server")
        else:
            logging.warning("Joins/leaves channel not found, cannot announce member leave.")

    async def on_message(self, message):
        """
        Handles message events for reactions, TTS, and AI chat.

        :param message: The Discord message object
        """
        # Reacting to messages using the regex strings found in the DB
        for reaction in self.reactions_list:
            match = re.search(reaction["regex"], message.content)
            if match:
                try:
                    await message.add_reaction(reaction["emoji"])
                    logging.info(f"Added reaction '{reaction['emoji']}' to message by {message.author.name}")
                except Exception as e:
                    logging.error(f"Failed to add reaction to message '{message.content[:25]}' by {message.author.name}: {e}")

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
                    logging.error(f"TTS processing failed for message by {message.author.name}")
            else:
                # If Derek hasn't warned a user of not being in the VC within the past 3 minutes, warn them
                if time.time() - self.last_vc_text_warning_time >= 180:
                    logging.info(f"Warning user {message.author.name} that they aren't in a voice channel")
                    await message.reply("No voice channel detected")
                    self.last_vc_text_warning_time = time.time()
        
        # Chat processing
        if self.user.mentioned_in(message) and message.author != self.user:
            logging.info(f"AI chat triggered by {message.author.name} in channel {message.channel.name}")
            # Letting the user know we're processing things
            async with message.channel.typing():
                # Keeping track of things in the cache
                await self.conversation_cache.add_message(message)
                message_chain = self.conversation_cache.get_message_chain(message)
                gpt_message_list = self.llm_manager.generate_gpt_messages_list(message_chain)

                # Getting the AI response
                gpt_message, images = await self.llm_manager.run_model_with_funcs(gpt_message_list)

                # Converting images to discord files
                discord_file_images = []
                for idx, image in enumerate(images):
                    buffer = io.BytesIO()
                    image.save(buffer, format="PNG")
                    buffer.seek(0)
                    discord_file_images.append(
                        discord.File(buffer, filename=f"image_{idx}.png")
                    )

                # Sending the message
                reply_message = await message.reply(
                    content=gpt_message.content[:2000],
                    files=discord_file_images[:10]
                )
                logging.info(f"AI response sent to {message.author.name} in channel {message.channel.name}")
                await self.conversation_cache.add_message(reply_message)


# Starting the bot
if __name__ == '__main__':
    bot = DerekBot(db_manager, tts_manager, audio_manager, conversation_cache, llm_manager)
    bot.run(DISCORD_TOKEN, log_handler=None, root_logger=True)
