"""
The BaseBot module provides a foundational class for Discord bots with
database management, TTS, audio management, and GPT integration already set up.
"""

import os
import logging
import io
from abc import ABC, abstractmethod
from distutils.util import strtobool
from discord.ext import commands, tasks
from discord import File
import json

from shared.ChatLLMManager import ConversationCache, ChatLLMManager
from shared.data_manager import DataManager
from shared.cred_utils import save_google_service_file
from shared.TTSManager import TTSManager
from shared.VCAudioManager import VCAudioManager

class BaseBot(commands.Bot, ABC):
    """
    Base class for Discord bots. Sets up support for:
    - Database management via DataManager
    - Text-to-Speech (TTS) and voice channel audio management
    - Conversation caching
    - GPT-based chat and tool integration

    Initialization sets up all required managers and services.
    """
    def __init__(self,
                 *,
                 db_manager_config: dict,
                 open_ai_key: str,
                 audio_file_directory: str,
                 gpt_prompt_config_column_name: str,
                 gpt_function_references=None,
                 gpt_tool_definitions=None,
                 gpt_get_memories=None,
                 **kwargs):
        super().__init__(**kwargs)

        # Setting up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s]: %(message)s'
        )

        # Setting up the database manager
        self.db_manager = DataManager(db_manager_config)

        # Setting up the google credentials file
        save_google_service_file()
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-services.json'

        # Setting up the TTS manager and VC Audio Manager
        if audio_file_directory:
            self.tts_manager = TTSManager(audio_file_directory)
            self.audio_manager = VCAudioManager(self.tts_manager)

        # Conversation cache for message caching
        self.conversation_cache = ConversationCache()

        # Getting GPT config info
        gpt_system_prompt = self.db_manager.get_item_by_key(
            table_name="system_config",
            key="config_name",
            value=gpt_prompt_config_column_name
        ).get("config_value_text")
        if not gpt_system_prompt:
            raise ValueError("gpt_system_prompt cannot be None. There was an issue pulling info from the DB.")

        # NOTE: Tools and memory functions must be updated in ChatLLMManager

        # Setting up the GPT model
        self.llm_manager = ChatLLMManager(
            api_key=open_ai_key,
            system_prompt=gpt_system_prompt
        )

        # Keeping track of the guild and the guild ID of the bot
        self.guild_id = None
        self.guild = None

        # Keeping track of known bot IDs to ignore messages from
        self.known_bot_ids = []

        # Cogs to add
        self.command_cogs = []

    def _get_config_value(self, config_data, config_name, config_type):
        """
        Universal helper for fetching config values from DB or environment.
        """
        if (value := os.environ.get(config_name)):
            logging.info("TEST VAR USAGE: Using an environment variable in place of a DB config value")
            if config_type == "int":
                return int(value)
            elif config_type == "bool":
                return bool(strtobool(value))
            else:
                return value
        full_column_name = f"config_value_{config_type}"
        return next((item[full_column_name] for item in config_data if item["config_name"] == config_name), None)

    def set_config_data_from_db_manager(self):
        """
        Updates variables for Discord IDs and other config data from the database.
        Calls extract_config_values for bot-specific config extraction.
        """
        logging.info("Setting config data from DB manager")
        config_data = self.db_manager.data.get("system_config")

        # If we don't get the config data
        if not config_data:
            logging.warning("No config data found in DB")
            return
        
        # Setting the guild ID for any tools that need them
        self.guild_id = self._get_config_value(config_data, "guild_id", "int")

        # Known bot IDs to ignore messages from
        self.known_bot_ids = json.loads(self._get_config_value(config_data, "known_bot_ids", "text"))

        # Calling the abstract method to get the specific configs we need
        self.extract_config_values(config_data)

    @abstractmethod
    def extract_config_values(self, config_data):
        """
        Abstract method for extracting config values. Must be overridden in subclasses.
        """
        pass

    async def on_ready(self):
        """
        Called when the bot is ready and connected to Discord.
        """
        self.set_config_data_from_db_manager()
        self.guild = self.get_guild(self.guild_id)
        if self.guild:
            logging.info(f"Guild set: {self.guild.name} ({self.guild_id})")
        else:
            logging.warning(f"Guild with ID {self.guild_id} not found")
        self.start_background_tasks()
        logging.info("BaseBot ready event triggered. Logged in as %s", self.user)

    async def setup_hook(self):
        """
        Adds cogs from self.command_cogs and logs the process.
        """
        logging.info("Adding cogs...")
        for cog in self.command_cogs:
            await self.add_cog(cog)
            logging.info(f"Added cog: {cog.__class__.__name__}")
        await self.tree.sync()
        logging.info("Synced commands and added all cogs")

    def add_command_cogs(self, cogs):
        """
        Adds command cogs to the bot after initialization.
        """
        self.command_cogs.extend(cogs)
        logging.info(f"Added {len(cogs)} cogs to command_cogs list.")

    # Pulls cached info from the database, and updates the local variables for up-to-date values
    @tasks.loop(hours=1)
    async def refresh_cached_info(self):
        """
        Refreshes cached info from the database and updates config data.
        """
        logging.info("Refreshing cached info from DB")
        self.db_manager.fetch_all_table_data()
        logging.info("Refreshed/updated all table information")

        # Updating our config data periodically incase anything changes
        self.set_config_data_from_db_manager()

    def start_background_tasks(self):
        """
        Starts background processes if they aren't already started
        """
        if not self.refresh_cached_info.is_running():
            self.refresh_cached_info.start()
            logging.info("Started background task: refresh_cached_info")

    async def on_message(self, message):
        """
        Handles message events for AI chat functionality.
        
        :param message: The Discord message object
        """
        # Returning if we are responding/speaking the bot's message
        if message.author.id in self.known_bot_ids:
            return

        # Chat processing. First ignoring DMs, then continuing processing
        if not hasattr(message.channel, "name"):
            logging.warning(f"Received a dm from user {message.author.name}. Ignoring.")
            return

        if self.user.mentioned_in(message):
            logging.info(f"AI chat triggered by {message.author.name} in channel {message.channel.name}")
            # Letting the user know we're processing things
            async with message.channel.typing():
                # Keeping track of things in the cache
                await self.conversation_cache.add_message(message)
                message_chain = self.conversation_cache.get_message_chain(message)

                # Executing the model
                gpt_message, images = await self.llm_manager.process_with_history(message_chain)

                # Converting images to discord files
                discord_file_images = []
                for idx, image in enumerate(images):
                    buffer = io.BytesIO()
                    image.save(buffer, format="PNG")
                    buffer.seek(0)
                    discord_file_images.append(
                        File(buffer, filename=f"image_{idx}.png")
                    )

                # Sending the message if things are valid
                if gpt_message and gpt_message.content:
                    reply_message = await message.reply(
                        content=gpt_message.content[:2000],
                        files=discord_file_images[:10]
                    )
                    logging.info(f"AI response sent to {message.author.name} in channel {message.channel.name}")
                    await self.conversation_cache.add_message(reply_message)
                else:
                    logging.error("GPT message was None or missing content. Sending fallback error message.")
                    await message.reply("`Sorry, something went wrong with your request. Please try again later.`")
