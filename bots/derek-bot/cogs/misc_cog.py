from discord.ext import commands
from discord import app_commands, Interaction
import logging

from shared.data_manager import DataManager, ListIndexOutOfBounds
from shared.DiscordList import DiscordList
from shared.time_utils import get_est_iso_date
import random


class MiscGroupCog(commands.Cog):
    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data_manager = data_manager

    group = app_commands.Group(name="misc", description="Miscellaneous commands")

    @group.command(name="magic8ball")
    async def magic8ball(self, interaction: Interaction, question: str):
        ball_phrase = random.choice(self.data_manager.data.get("eight_ball_phrases"))

        output_string = (f"{interaction.user.name} said: *{question}*\n"
                         f"🎱: **{ball_phrase.get('phrase')}**")

        await interaction.response.send_message(output_string)

    @group.command(name="simon_says")
    @app_commands.describe(text="The text to mimic")
    async def simon_says(self, interaction: Interaction, text: str):
        await interaction.channel.send(text)
        await interaction.response.send_message("Sent the simonsays message.", ephemeral=True)

    @group.command(name="random_nicknames")
    async def random_nicknames(self, interaction: Interaction):
        """
        Command to show the list of random nicknames for users who opt-in

        :param interaction: The interaction for the command
        """
        def get_random_nickname_data():
            return [
                f"{random_nickname['nickname']} - {random_nickname['added_by']['user_name']}"
                for random_nickname in self.data_manager.data.get("random_user_nicknames")
            ]

        discord_list = DiscordList(
            get_items=get_random_nickname_data,
            title="Random Nicknames"
        )

        await interaction.response.send_message(
            discord_list.get_page(),
            view=discord_list.create_view()
        )

    @group.command(name="add_nickname")
    async def add_nickname(self, interaction: Interaction, nickname: str):
        """
        Command to add a random nickname to the random nickname table in the DB

        :param interaction: The interaction for the command
        :param nickname: The nickname string to save
        """
        self.data_manager.ensure_user_exists(interaction.user)

        successfully_added = self.data_manager.add_table_data(
            table_name="random_user_nicknames",
            json_data={"nickname": nickname, "created": get_est_iso_date(), "added_by": interaction.user.id}
        )

        if successfully_added:
            logging.info(f"Saved new random nickname: {nickname}")
            await interaction.response.send_message(f"Saved random nickname **{nickname}**")
        else:
            await interaction.response.send_message("`Failed to save random nickname`")

    @group.command(name="remove_nickname")
    async def remove_nickname(self, interaction: Interaction, nickname_index: int):
        """
        Command to remove a random nickname from the random nickname table in the DB

        :param interaction: The interaction for the command
        :param nickname_index: The index of the nickname in the local db cache
        """
        try:
            nickname_item = self.data_manager.get_db_item_with_index(
                table_name="random_user_nicknames",
                item_index=nickname_index
            )

            nickname_string = nickname_item["nickname"]
            added_by_user_id = nickname_item["added_by"]["user_id"]

            # Removing the item
            successfully_removed = self.data_manager.delete_table_data(
                table_name="random_user_nicknames",
                match_json={"nickname": nickname_string, "added_by": added_by_user_id}
            )

            if successfully_removed:
                logging.info(f"Removed random nickname: {nickname_string}")
                await interaction.response.send_message(f"Removed random nickname **{nickname_string}**")
            else:
                await interaction.response.send_message(f"`Failed to remove random nickname`")

        except ListIndexOutOfBounds as error:
            await error.handle_index_error(interaction)
