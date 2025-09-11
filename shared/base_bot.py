"""
The BaseBot module provides a foundational class for Discord bots with
database management, TTS, audio management, and GPT integration already set up.
"""

import os
import logging
from abc import ABC, abstractmethod
from distutils.util import strtobool
from discord.ext import commands, tasks

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
                 command_cogs=None,
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

        # NOTE: Tools and memory functions are provided to this class

        # Setting up the GPT model
        self.llm_manager = ChatLLMManager(
            api_key=open_ai_key,
            system_prompt=gpt_system_prompt,
            tool_function_references=gpt_function_references,
            tool_definitions=gpt_tool_definitions,
            get_memories=gpt_get_memories
        )

        # Keeping track of the guild and the guild ID of the bot
        self.guild_id = None
        self.guild = None

        # Cogs to add
        self.command_cogs = command_cogs or []

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
