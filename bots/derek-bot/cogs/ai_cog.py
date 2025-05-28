from discord.ext import commands
from discord import app_commands, Interaction
import random
import logging
from shared.time_utils import get_est_iso_date

from shared.data_manager import DataManager, ListIndexOutOfBounds
from shared.DiscordList import DiscordList


class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data_manager = data_manager

    group = app_commands.Group(name="ai", description="Commands for managing Derek's AI functionality")

    @group.command(name="add_memory", description="Adds a memory for Derek to remember")
    async def add_memory(self, interaction: Interaction, memory: str):
        if len(memory) > 100:
            logging.warning(f"{interaction.user.name} tried to save a memory with more than 100 characters: {memory}")
            await interaction.response.send_message(
                "`Memory is too long. Must be at most 100 characters`",
                ephemeral=True
            )
        else:
            self.data_manager.ensure_user_exists(interaction.user)
            successfully_added = self.data_manager.add_table_data(
                table_name="chat_memories",
                json_data={"memory": memory, "created": get_est_iso_date(), "added_by": interaction.user.id}
            )
            logging.info(f"User {interaction.user.name} saved memory: {memory}")
            if successfully_added:
                await interaction.response.send_message("Memory successfully saved")
            else:
                await interaction.response.send_message("`Failed to save memory`")
