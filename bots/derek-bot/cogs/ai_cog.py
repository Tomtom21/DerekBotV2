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

    @group.command(name="memories", description="Shows a list of Derek's memories")
    async def memories(self, interaction: Interaction):
        def get_memory_data():
            return [
                f"{memory['memory']} - {memory['added_by']['user_name']}"
                for memory in self.data_manager.data.get("chat_memories")
            ]

        discord_list = DiscordList(
            get_items=get_memory_data,
            title="Derek's Memories"
        )

        await interaction.response.send_message(
            discord_list.get_page(),
            view=discord_list.create_view()
        )

    @group.command(name="remove_memory", description="Deletes a memory from Derek")
    async def remove_memory(self, interaction: Interaction, memory_index: int):
        try:
            memory = self.data_manager.get_db_item_with_index(
                table_name="chat_memories",
                item_index=memory_index
            )

            memory_name = memory["memory"]
            added_by_user_id = memory["added_by"]["user_id"]

            # Removing the memory
            successfully_removed = self.data_manager.delete_table_data(
                table_name="chat_memories",
                match_json={"memory": memory_name, "added_by": added_by_user_id}
            )

            if successfully_removed:
                await interaction.response.send_message("Removed **" + memory_name + "** from Derek's memory")
            else:
                await interaction.response.send_message("`Failed to remove memory`")

        except ListIndexOutOfBounds as error:
            await error.handle_index_error(interaction)
