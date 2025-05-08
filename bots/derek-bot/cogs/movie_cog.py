from discord.ext import commands
from discord import app_commands, Interaction
import random

from shared.data_manager import DataManager, ListIndexOutOfBounds
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

    def search_unwatched_by_keyword(self, keyword: str):
        lowercase_keyword = keyword.lower()
        movies = [
            movie for movie in self.data_manager.data.get("unwatched_movies")
            if lowercase_keyword in movie.get("movie_name", "").lower()
        ]
        return movies

    @group.command(name="unwatched_movies", description="Show a list of unwatched movies")
    async def unwatched_movies(self, interaction: Interaction):
        def get_unwatched_movie_data():
            return self.process_movie_data(
                self.data_manager.data.get("unwatched_movies", [])
            )

        discord_list = DiscordList(
            get_items=get_unwatched_movie_data,
            title="Unwatched Movies"
        )

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

        discord_list = DiscordList(
            get_items=get_watched_movie_data,
            title="Watched Movies"
        )

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
        try:
            movie_item = self.data_manager.get_db_item_with_index(
                table_name="unwatched_movies",
                item_index=movie_index
            )

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

        except ListIndexOutOfBounds as error:
            await error.handle_index_error(interaction)

    @group.command(name="mark_watched", description="Marks a movie in the unwatched list as watched")
    @app_commands.describe(movie_index="Index number associated with each movie in the movie list")
    async def mark_watched(self, interaction: Interaction, movie_index: int):
        try:
            unwatched_item = self.data_manager.get_db_item_with_index(
                table_name="unwatched_movies",
                item_index=movie_index
            )
            unwatched_name = unwatched_item["movie_name"]
            unwatched_user_id = unwatched_item["added_by"]["user_id"]

            # Removing the item from the unwatched list
            successfully_removed = self.data_manager.delete_table_data(
                table_name="unwatched_movies",
                match_json={"movie_name": unwatched_name, "added_by": unwatched_user_id}
            )
            if not successfully_removed:
                await interaction.response.send_message("`Failed to remove movie from unwatched list during marking`")
                return

            # Adding it to the watched list
            successfully_added = self.data_manager.add_table_data(
                table_name="watched_movies",
                json_data={"movie_name": unwatched_name, "added_by": unwatched_user_id}
            )
            if successfully_added:
                await interaction.response.send_message("Marked **" + unwatched_name + "** as watched")
            else:
                await interaction.response.send_message("`Failed to add movie to the watched list`")
        except ListIndexOutOfBounds as error:
            await error.handle_index_error(interaction)

    @group.command(name="search_movie",
                   description="List all movies that contain the keyword (from unwatched list)")
    @app_commands.describe(keyword="Keyword movie name")
    async def search_movie(self, interaction: Interaction, keyword: str):
        def get_search_movies():
            movies = self.search_unwatched_by_keyword(keyword)
            return self.process_movie_data(movies)

        discord_list = DiscordList(
            get_items=get_search_movies,
            title="Unwatched Movie Search",
            have_pages=False,
            items_per_page=15
        )

        await interaction.response.send_message(
            discord_list.get_page(),
            view=discord_list.create_view()
        )

    @group.command(name="random_movie", description="Choose a random movie to watch (from unwatched list)")
    @app_commands.describe(keyword="[OPTIONAL] Keyword movie name")
    async def random_movie(self, interaction: Interaction, keyword: str = ""):
        # Getting a list of movies to choose a random selection from
        if keyword:
            possible_movies = self.search_unwatched_by_keyword(keyword)
        else:
            possible_movies = self.data_manager.data.get("unwatched_movies")

        # Checking if we have any movies avaiable
        if possible_movies:
            # Getting a random movie and a random movie phrase
            movie = random.choice(possible_movies)
            phrase = random.choice(self.data_manager.data.get("movie_phrases"))

            # Generating the output string. Determining if we should return the added_by user
            output_string = f"**{movie.get('movie_name', '')}** {phrase.get('phrase')}"

            added_by = movie.get("added_by")
            if added_by.get("user_id") != 0:
                output_string += f" It was recommended by **{added_by.get('user_name')}**."

            await interaction.response.send_message(output_string)
        else:
            await interaction.response.send_message(
                f"`No movies found with keyword '{keyword}'`",
                ephemeral=True
            )

