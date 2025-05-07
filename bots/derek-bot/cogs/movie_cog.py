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

    def get_unwatched_with_index(self, movie_index: int, movie_count: int):
        """
        Gets an unwatched movie using an index (1-length).

        :param movie_index: A 1 based indexing value.
        :param movie_count: The number of movies in the list
        :return: The unwatched movie item if it exists, otherwise None
        """
        if movie_count >= movie_index >= 1:
            # Pulling movie item information
            movie_item = self.data_manager.data.get("unwatched_movies")[movie_index - 1]
            return movie_item
        else:
            return None

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

    @group.command(name="remove_movie", description="Remove a movie from the unwatched list")
    @app_commands.describe(movie_index="The item number associated with each movie in the movie list")
    async def remove_movie(self, interaction: Interaction, movie_index: int):
        movie_count = len(self.data_manager.data.get("unwatched_movies"))

        movie_item = self.get_unwatched_with_index(movie_index, movie_count)
        if movie_item:
            movie_name = movie_item["movie_name"]
            added_by_user_id = movie_item["added_by"]["user_id"]

            # Removing the item
            successfully_removed = self.data_manager.delete_table_data(
                table_name="unwatched_movies",
                match_json={"movie_name": movie_name, "added_by": added_by_user_id}
            )

            if successfully_removed:
                await interaction.response.send_message("Removed **" + movie_name + "** from unwatched list")
            else:
                await interaction.response.send_message("`Failed to remove movie from unwatched list`")
        else:
            await interaction.response.send_message(
                "Movie index is outside of the valid range (1-" + str(movie_count) + ")",
                ephemeral=True
            )
