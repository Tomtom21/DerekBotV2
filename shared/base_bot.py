from shared.ChatLLMManager import ConversationCache, ChatLLMManager
from shared.data_manager import DataManager
import logging
from shared.cred_utils import save_google_service_file
import os
from shared.TTSManager import TTSManager
from shared.VCAudioManager import VCAudioManager
from discord import Intents

class BaseBot:
    def __init__(self, 
                 db_manager_config: dict, 
                 OPEN_AI_KEY: str,
                 audio_file_directory: str, 
                 gpt_prompt_config_column_name: str,
                 gpt_function_references=None, 
                 gpt_tool_definitions=None, 
                 gpt_get_memories=None):
        
        # Setting up the database manager
        self.db_manager = DataManager(db_manager_config)

        # Setting up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s]: %(message)s'
        )

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
            api_key=OPEN_AI_KEY,
            system_prompt=gpt_system_prompt,
            tool_function_references=gpt_function_references,
            tool_definitions=gpt_tool_definitions,
            get_memories=gpt_get_memories
        )

        # Setting up intents for permissions
        self.intents = Intents.default()
        self.intents.guilds = True
        self.intents.guild_messages = True
        self.intents.reactions = True
        self.intents.members = True
        self.intents.voice_states = True
        self.intents.message_content = True

