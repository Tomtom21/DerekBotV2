from discord.ext import commands
from discord import app_commands, Interaction

from shared.data_manager import DataManager
from shared.DiscordList import DiscordList

class MovieGroupCog(commands.Cog):
    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data_manager = data_manager

    group = app_commands.Group(name="movies", description="Commands for managing movie lists")

    @group.command(name="unwatched_movies", description="Show a list of unwatched movies")
    async def unwatched_movies(self, interaction: Interaction):
        def get_unwatched_movie_data():
            return self.data_manager.data.get("unwatched_movies", [])

        discord_list = DiscordList(get_unwatched_movie_data)

        await interaction.response.send_message(
            discord_list.get_page(),
            view=discord_list.create_view()
        )


    @group.command(name="watched_movies", description="Show a list of watched movies")
    async def watched_movies(self, interaction: Interaction):
        def get_watched_movie_data():
            return self.data_manager.data.get("watched_movies", [])

        discord_list = DiscordList(get_watched_movie_data)

        await interaction.response.send_message(
            discord_list.get_page(),
            view=discord_list.create_view()
        )
