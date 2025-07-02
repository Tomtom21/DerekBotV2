# General imports
import logging

# Discord imports
from discord.ext import commands
from discord import app_commands, Interaction

from shared.DiscordList import DiscordList

class BotManagementGroupCog(commands.Cog):
   def __init__(self, bot: commands.Bot):
       self.bot = bot
  
   group = app_commands.Group(name="management", description="Commands for managing the other bots.")

   @group.command(name="status", description="Shows the status of each of the bots.")
   async def status(self, interaction: Interaction):
       """
       Shows a list with the status of each bot.

       :param interaction: The Discord interaction object
       """
       def get_bot_status_data():
           pass

       # discord_list = DiscordList(
       #     get_items=
       # )
