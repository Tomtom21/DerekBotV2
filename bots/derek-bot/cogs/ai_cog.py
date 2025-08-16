from discord.ext import commands
from discord import app_commands, Interaction
import random
import logging

from shared.data_manager import DataManager, ListIndexOutOfBounds
from shared.DiscordList import DiscordList


class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data_manager = data_manager

    group = app_commands.Group(name="ai", description="Commands for managing Derek's AI functionality")

    @group.command(name="addmemory", description="Adds a memory for Derek to remember")
    @app_commands.describe(memory="The information you'd like Derek to remember")
    async def add_memory(self, interaction: Interaction, memory: str):
        """
        Command to add a memory to the chat_memories table in the DB

        :param interaction: The interaction for the command
        :param memory: The memory string to save
        """
        await interaction.response.defer()
        if len(memory) > 100:
            logging.warning(f"{interaction.user.name} tried to save a memory with more than 100 characters: {memory}")
            await interaction.followup.send("`Memory is too long. Must be at most 100 characters`")
        else:
            self.data_manager.ensure_user_exists(interaction.user)
            successfully_added = self.data_manager.add_table_data(
                table_name="chat_memories",
                json_data={"memory": memory, "added_by": interaction.user.id}
            )

            if successfully_added:
                logging.info(f"User {interaction.user.name} saved memory: {memory}")
                await interaction.followup.send("Memory successfully saved")
            else:
                logging.error(f"Failed to save memory for user {interaction.user.name}: {memory}")
                await interaction.followup.send("`Failed to save memory`")

    @group.command(name="memories", description="Shows a list of Derek's memories")
    async def memories(self, interaction: Interaction):
        """
        Command to show a list of Derek's current memories to the

        :param interaction: The interaction for the command
        """
        def get_memory_data():
            return [
                f"{memory['memory']} - {memory['added_by']['user_name']}"
                if memory.get("added_by") and memory["added_by"].get("user_name")
                else memory["memory"]
                for memory in self.data_manager.data.get("chat_memories", [])
            ]

        discord_list = DiscordList(
            get_items=get_memory_data,
            title="Derek's Memories"
        )

        logging.info(f"User {interaction.user.name} requested Derek's memory list")
        await interaction.response.send_message(
            discord_list.get_page(),
            view=discord_list.create_view()
        )

    @group.command(name="removememory", description="Deletes a memory from Derek")
    @app_commands.describe(memory_index="The number in the memory list corresponding to the memory you want to remove")
    async def remove_memory(self, interaction: Interaction, memory_index: int):
        """
        Command to remove a memory from the chat_memories table in the DB

        :param interaction: The interaction for the command
        :param memory_index: The index of the memory in the user-facing list (local db index + 1)
        """
        await interaction.response.defer()
        logging.info(f"User {interaction.user.name} is removing movie at index: {memory_index}")
        try:
            memory = self.data_manager.get_db_item_with_index(
                table_name="chat_memories",
                item_index=memory_index
            )

            memory_text = memory["memory"]
            added_by_user_id = memory["added_by"]["user_id"]

            # Removing the memory
            successfully_removed = self.data_manager.delete_table_data(
                table_name="chat_memories",
                match_json={"memory": memory_text, "added_by": added_by_user_id}
            )

            if successfully_removed:
                logging.info(f"User {interaction.user.name} removed memory: {memory_text}")
                await interaction.followup.send("Removed **" + memory_text + "** from Derek's memory")
            else:
                logging.error(f"Failed to remove memory for user {interaction.user.name}: {memory_text}")
                await interaction.followup.send("`Failed to remove memory`")

        except ListIndexOutOfBounds as error:
            logging.warning(f"User {interaction.user.name} tried to remove memory at invalid index {memory_index}")
            await error.handle_index_error(interaction, requires_followup=True)
