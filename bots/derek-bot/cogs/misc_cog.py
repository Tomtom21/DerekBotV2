from discord.ext import commands
from discord import app_commands, Interaction

from shared.data_manager import DataManager
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
