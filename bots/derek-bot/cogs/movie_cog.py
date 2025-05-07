from discord.ext import commands
from discord import app_commands, Interaction

from shared.data_manager import DataManager
from shared.DiscordList import DiscordList

class MovieGroupCog(commands.Cog):
    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data_manager = data_manager

    group = app_commands.Group(name="movies", description="Commands for managing movie lists")

    @staticmethod
    def process_movie_data(db_data):
        """
        Processes raw movie data from the DB to a list of data that can be shown in a list
        :param db_data:
        :return:
        """
        output_list = []
        for item in db_data:
            output_string = f"{item['movie_name']} - {item['added_by']['user_name']}"
            output_list.append(output_string)
        return output_list

    @group.command(name="unwatched_movies", description="Show a list of unwatched movies")
    async def unwatched_movies(self, interaction: Interaction):
        def get_unwatched_movie_data():
            return self.process_movie_data(
                self.data_manager.data.get("unwatched_movies", [])
            )

        discord_list = DiscordList(get_unwatched_movie_data)

        await interaction.response.send_message(
            discord_list.get_page(),
            view=discord_list.create_view()
        )


    @group.command(name="watched_movies", description="Show a list of watched movies")
    async def watched_movies(self, interaction: Interaction):
        def get_watched_movie_data():
            return self.process_movie_data(
                self.data_manager.data.get("watched_movies", [])
            )

        discord_list = DiscordList(get_watched_movie_data)

        await interaction.response.send_message(
            discord_list.get_page(),
            view=discord_list.create_view()
        )

    @group.command(name="add_movie", description="Add a movie to the unwatched list")
    @app_commands.describe(movie_name="The name of the movie to add to the list")
    async def add_movie(self, interaction: Interaction, movie_name: str):
        successfully_added = self.data_manager.add_table_data(
            table_name="unwatched_movies",
            json_data={"movie_name": movie_name, "added_by": interaction.user.id}
        )

        if successfully_added:
            await interaction.response.send_message("Added **" + movie_name + "** to unwatched list")
        else:
            await interaction.response.send_message("`Failed to add movie to unwatched list`")
