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
        """
        Responds to a user's question with a random Magic 8 Ball phrase.

        :param interaction: The Discord interaction object
        :param question: The user's question to the Magic 8 Ball
        """
        ball_phrase = random.choice(self.data_manager.data.get("eight_ball_phrases"))

        output_string = (f"{interaction.user.name} said: *{question}*\n"
                         f"🎱: **{ball_phrase.get('phrase')}**")

        logging.info(f"Magic8Ball: {interaction.user.name} asked '{question}' -> '{ball_phrase.get('phrase')}'")
        await interaction.response.send_message(output_string)

    @group.command(name="simon_says")
    @app_commands.describe(text="The text to mimic")
    async def simon_says(self, interaction: Interaction, text: str):
        """
        Sends the provided text to the channel as if the bot said it.

        :param interaction: The Discord interaction object
        :param text: The text to send to the channel
        """
        await interaction.channel.send(text)
        logging.info(f"SimonSays: {interaction.user.name} made bot say '{text}'")
        await interaction.response.send_message("Sent the simonsays message.", ephemeral=True)

    @group.command(name="random_nicknames")
    async def random_nicknames(self, interaction: Interaction):
        """
        Shows the list of random nicknames for users who opt-in.

        :param interaction: The Discord interaction object
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

        logging.info(f"RandomNicknames: {interaction.user.name} requested random nicknames list")
        await interaction.response.send_message(
            discord_list.get_page(),
            view=discord_list.create_view()
        )

    @group.command(name="add_nickname")
    async def add_nickname(self, interaction: Interaction, nickname: str):
        """
        Adds a new random nickname to the database.

        :param interaction: The Discord interaction object
        :param nickname: The nickname string to save
        """
        self.data_manager.ensure_user_exists(interaction.user)

        successfully_added = self.data_manager.add_table_data(
            table_name="random_user_nicknames",
            json_data={"nickname": nickname, "created": get_est_iso_date(), "added_by": interaction.user.id}
        )

        if successfully_added:
            logging.info(f"User {interaction.user.name} saved new random nickname: {nickname}")
            await interaction.response.send_message(f"Saved random nickname **{nickname}**")
        else:
            logging.warning(f"Failed to save random nickname for user {interaction.user.name}: {nickname}")
            await interaction.response.send_message("`Failed to save random nickname`")

    @group.command(name="remove_nickname")
    async def remove_nickname(self, interaction: Interaction, nickname_index: int):
        """
        Removes a random nickname from the database by index.

        :param interaction: The Discord interaction object
        :param nickname_index: The index of the nickname in the user-facing list (local db index + 1)
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
                logging.info(f"User {interaction.user.name} removed random nickname: {nickname_string}")
                await interaction.response.send_message(f"Removed random nickname **{nickname_string}**")
            else:
                logging.warning(f"Failed to remove random nickname for user {interaction.user.name}: {nickname_string}")
                await interaction.response.send_message(f"`Failed to remove random nickname`")

        except ListIndexOutOfBounds as error:
            logging.warning(f"User {interaction.user.name} tried to remove nickname at invalid index {nickname_index}")
            await error.handle_index_error(interaction)

    @group.command(name="shuffle_nickname", description="Set whether to shuffle your nickname daily")
    @app_commands.describe(shuffle_nickname="Do you want to shuffle your nickname daily?")
    async def shuffle_nickname(self, interaction: Interaction, shuffle_nickname: bool):
        """
        Sets whether to shuffle a user's nickname on a daily basis.

        :param interaction: The Discord interaction object
        :param shuffle_nickname: Boolean value to enable or disable daily nickname shuffling
        """
        # Preventing higher or equal roles from enabling this feature
        bot_member_top_role = interaction.guild.me.top_role
        user_top_role = interaction.user.top_role

        if bot_member_top_role <= user_top_role and shuffle_nickname:
            logging.warning(
                f"User {interaction.user.id}({interaction.user.name}) failed to enable nickname shuffling. "
                f"Bot/User role levels were: {bot_member_top_role.position} > {user_top_role.position}"
            )
            await interaction.response.send_message(
                f"`Derek is unable to shuffle nicknames for users who are of equal role level or higher.`"
            )
            return

        # Otherwise updating the nickname shuffling state
        successfully_updated = self.data_manager.update_table_data(
            table_name="users",
            match_json={"user_id": interaction.user.id},
            update_json={"shuffle_nickname": shuffle_nickname}
        )

        if successfully_updated:
            logging.info(f"Successfully updated nickname shuffling state for {interaction.user.name} to {shuffle_nickname}")
            await interaction.response.send_message(
                f"Successfully updated nickname shuffling state to **{shuffle_nickname}**",
                ephemeral=True
            )
        else:
            logging.warning(f"Failed to update nickname shuffling state for {interaction.user.name}")
            await interaction.response.send_message(f"`Failed to update nickname shuffling state`")
