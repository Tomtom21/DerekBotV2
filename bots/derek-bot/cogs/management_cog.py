from discord.ext import commands
from discord import app_commands, Interaction
import logging

class ManagementGroupCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    group = app_commands.Group(name="management", description="Commands for managing the state of the bot")

    @group.command(name="shutdown", description="Shuts down the bot")
    async def shutdown(self, interaction: Interaction):
        """
        Checks if the user has permission (is_creator) to shut down the bot.
        If permitted, logs the shutdown and shuts down the bot.
        If not permitted, logs the denial and informs the user.
        """
        db_user = self.data_manager.get_item_by_key(
            table_name="users",
            key="user_id",
            value=interaction.user.id
        )
        if db_user and db_user.get("is_creator"):
            logging.warning(f"Shutdown initiated by user {interaction.user.id} ({interaction.user.name})")
            await interaction.response.send_message("Shutting down..", ephemeral=True)
            exit(0)
        else:
            logging.warning(f"Shutdown attempt denied for user {interaction.user.id} ({interaction.user.name})")
            await interaction.response.send_message("`You do not have permission to shut down the bot.`", ephemeral=True)
