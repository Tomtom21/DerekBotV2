import os
import logging
from shared.base_bot import BaseBot
from shared.ChatLLMManager import ChatLLMManager

# Discord imports
import discord
from discord.ext import commands, tasks
from discord import app_commands

# Cogs
from cogs.music_command_cog import MusicCommandCog

# DB manager config
db_manager_config = {
    "system_config": {
        "select": "*"
    }
}

# Getting the discord bot info
DISCORD_TOKEN = os.environ.get('MUSIC_DISCORD_TOKEN')
OPEN_AI_KEY = os.environ.get('OPEN_AI_KEY')

class Derpods(BaseBot, commands.Bot):
    def __init__(self, 
                 db_manager_config, 
                 audio_file_directory, 
                 OPEN_AI_KEY,
                 gpt_prompt_config_column_name="derek_gpt_system_prompt"):
        BaseBot.__init__(
            self,
            db_manager_config=db_manager_config,
            audio_file_directory=audio_file_directory,
            OPEN_AI_KEY=OPEN_AI_KEY,
            gpt_prompt_config_column_name=gpt_prompt_config_column_name
        )
        commands.Bot.__init__(command_prefix=None, intents=self.intents, case_insensitive=True)

# Starting the bot
if __name__ == "__main__":
    bot = Derpods(db_manager_config, "music_files", OPEN_AI_KEY)
    bot.run(DISCORD_TOKEN, log_handler=None, root_logger=True)