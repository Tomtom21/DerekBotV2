from discord.ext import commands
from discord import app_commands, Interaction
import logging

from shared.data_manager import DataManager, ListIndexOutOfBounds
from shared.DiscordList import DiscordList
import random


class MiscGroupCog(commands.Cog):
    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data_manager = data_manager

    group = app_commands.Group(name="misc", description="Miscellaneous commands")

    @group.command(name="magic8ball", description="Ask the Magic 8 Ball a question.")
    @app_commands.describe(question="The question you want to ask the Magic 8 Ball")
    async def magic8ball(self, interaction: Interaction, question: str):
        """
        Responds to a user's question with a random Magic 8 Ball phrase.

        :param interaction: The Discord interaction object
        :param question: The user's question to the Magic 8 Ball
        """
        ball_phrase = random.choice(self.data_manager.data.get("eight_ball_phrases"))
        question = question[:200]
        
        output_string = (f"{interaction.user.name} said: *{question}*\n"
                         f"🎱: **{ball_phrase.get('phrase')}**")

        logging.info(f"Magic8Ball: {interaction.user.name} asked '{question}' -> '{ball_phrase.get('phrase')}'")
        await interaction.response.send_message(output_string)

    @group.command(name="simonsays", description="Make the bot repeat your message in the text channel.")
    @app_commands.describe(text="The text to mimic")
    async def simon_says(self, interaction: Interaction, text: str):
        """
        Sends the provided text to the channel as if the bot said it.

        :param interaction: The Discord interaction object
        :param text: The text to send to the channel
        """
        await interaction.channel.send(text[:2000])
        logging.info(f"SimonSays: {interaction.user.name} made bot say '{text[:50]}'")
        await interaction.response.send_message("Sent the simonsays message.", ephemeral=True)

    @group.command(name="nicknames", description="Show the list of random nicknames for nickname cycling.")
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

    @group.command(name="addnickname", description="Save a new random nickname to cycle through.")
    @app_commands.describe(nickname="The nickname to save")
    async def add_nickname(self, interaction: Interaction, nickname: str):
        """
        Adds a new random nickname to the database.

        :param interaction: The Discord interaction object
        :param nickname: The nickname string to save
        """
        await interaction.response.defer(ephemeral=True)
        if len(nickname) > 32:
            logging.warning(f"{interaction.user.name} attempted to submit a nickname that was too long")
            await interaction.followup.send("`Nickname is too long. Please use 32 characters or fewer.`")
            return

        self.data_manager.ensure_user_exists(interaction.user)

        successfully_added = self.data_manager.add_table_data(
            table_name="random_user_nicknames",
            json_data={"nickname": nickname, "added_by": interaction.user.id}
        )

        if successfully_added:
            logging.info(f"User {interaction.user.name} saved new random nickname: {nickname}")
            await interaction.followup.send(f"Saved random nickname **{nickname}**")
        else:
            logging.error(f"Failed to save random nickname for user {interaction.user.name}: {nickname}")
            await interaction.followup.send("`Failed to save random nickname`")

    @group.command(name="removenickname", description="Remove a random nickname by index.")
    @app_commands.describe(nickname_index="The index of the nickname in the random nicknames list.")
    async def remove_nickname(self, interaction: Interaction, nickname_index: int):
        """
        Removes a random nickname from the database by index.

        :param interaction: The Discord interaction object
        :param nickname_index: The index of the nickname in the user-facing list (local db index + 1)
        """
        await interaction.response.defer(ephemeral=True)
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
                await interaction.followup.send(f"Removed random nickname **{nickname_string}**")
            else:
                logging.error(f"Failed to remove random nickname for user {interaction.user.name}: {nickname_string}")
                await interaction.followup.send(f"`Failed to remove random nickname`")

        except ListIndexOutOfBounds as error:
            logging.warning(f"User {interaction.user.name} tried to remove nickname at invalid index {nickname_index}")
            await error.handle_index_error(interaction, requires_followup=True)

    @group.command(name="shufflenickname", description="Set whether to shuffle your nickname daily")
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
                f"`Derek is unable to shuffle nicknames for users who are of equal role level or higher.`",
                ephemeral=True
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
            logging.error(f"Failed to update nickname shuffling state for {interaction.user.name}")
            await interaction.response.send_message(f"`Failed to update nickname shuffling state`", ephemeral=True)
