from discord.ext import commands
from discord import app_commands, Interaction
import random
import logging

from shared.data_manager import DataManager, ListIndexOutOfBounds
from shared.discord_ui.DiscordList import DiscordList


class MovieGroupCog(commands.Cog):
    def __init__(self, bot: commands.Bot, data_manager: DataManager):
        self.bot = bot
        self.data_manager = data_manager

    group = app_commands.Group(name="movies", description="Commands for managing movie lists")

    @staticmethod
    def process_movie_data(db_data):
        """
        Processes raw movie data from the DB to a list of data that can be shown in a list.

        :param db_data: The raw movie data from the database
        :return: A list of formatted movie strings
        """
        output_list = []
        for item in db_data:
            output_string = f"{item['movie_name']} - {item['added_by']['user_name']}"
            output_list.append(output_string)
        return output_list

    def search_unwatched_by_keyword(self, keyword: str):
        """
        Searches the unwatched movies for those containing the keyword.

        :param keyword: The keyword to search for in movie names
        :return: A list of matching movie dicts
        """
        lowercase_keyword = keyword.lower()
        movies = [
            movie for movie in self.data_manager.data.get("unwatched_movies")
            if lowercase_keyword in movie.get("movie_name", "").lower()
        ]
        return movies

    @group.command(name="unwatchedmovies", description="Show a list of unwatched movies")
    async def unwatched_movies(self, interaction: Interaction):
        """
        Shows a paginated list of unwatched movies.

        :param interaction: The Discord interaction object
        """
        def get_unwatched_movie_data():
            return self.process_movie_data(
                self.data_manager.data.get("unwatched_movies", [])
            )

        discord_list = DiscordList(
            get_items=get_unwatched_movie_data,
            title="Unwatched Movies"
        )

        logging.info(f"User {interaction.user.name} requested unwatched movie list")
        await interaction.response.send_message(
            discord_list.get_page(),
            view=discord_list.create_view()
        )

    @group.command(name="watchedmovies", description="Show a list of watched movies")
    async def watched_movies(self, interaction: Interaction):
        """
        Shows a paginated list of watched movies.

        :param interaction: The Discord interaction object
        """
        def get_watched_movie_data():
            return self.process_movie_data(
                self.data_manager.data.get("watched_movies", [])
            )

        discord_list = DiscordList(
            get_items=get_watched_movie_data,
            title="Watched Movies"
        )

        logging.info(f"User {interaction.user.name} requested watched movie list")
        await interaction.response.send_message(
            discord_list.get_page(),
            view=discord_list.create_view()
        )

    @group.command(name="addmovie", description="Add a movie to the unwatched list")
    @app_commands.describe(movie_name="The name of the movie to add to the list")
    async def add_movie(self, interaction: Interaction, movie_name: str):
        """
        Adds a movie to the unwatched movies list.

        :param interaction: The Discord interaction object
        :param movie_name: The name of the movie to add
        """
        await interaction.response.defer()
        self.data_manager.ensure_user_exists(interaction.user)

        logging.info(f"User {interaction.user.name} is adding movie: {movie_name}")
        successfully_added = self.data_manager.add_table_data(
            table_name="unwatched_movies",
            json_data={"movie_name": movie_name, "added_by": interaction.user.id}
        )

        if successfully_added:
            logging.info(f"Successfully added movie '{movie_name}' to unwatched list.")
            await interaction.followup.send("Added **" + movie_name + "** to unwatched list")
        else:
            logging.error(f"Failed to add movie '{movie_name}' to unwatched list.")
            await interaction.followup.send("`Failed to add movie to unwatched list`")

    @group.command(name="removemovie", description="Remove a movie from the unwatched list")
    @app_commands.describe(movie_index="The item number associated with each movie in the movie list")
    async def remove_movie(self, interaction: Interaction, movie_index: int):
        """
        Removes a movie from the unwatched movies list by index.

        :param interaction: The Discord interaction object
        :param movie_index: The index of the movie in the user-facing list (local db index + 1)
        """
        await interaction.response.defer()
        logging.info(f"User {interaction.user.name} is removing movie at index: {movie_index}")
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
                logging.info(f"Successfully removed movie '{movie_name}' from unwatched list.")
                await interaction.followup.send("Removed **" + movie_name + "** from unwatched list")
            else:
                logging.error(f"Failed to remove movie '{movie_name}' from unwatched list.")
                await interaction.followup.send("`Failed to remove movie from unwatched list`")

        except ListIndexOutOfBounds as error:
            logging.warning(f"ListIndexOutOfBounds error for user {interaction.user.name} at index {movie_index}: {error}")
            await error.handle_index_error(interaction, requires_followup=True)

    @group.command(name="markwatched", description="Marks a movie in the unwatched list as watched")
    @app_commands.describe(movie_index="Index number associated with each movie in the movie list")
    async def mark_watched(self, interaction: Interaction, movie_index: int):
        """
        Marks a movie as watched by moving it from the unwatched to the watched list.

        :param interaction: The Discord interaction object
        :param movie_index: The index of the movie in the user-facing list (local db index + 1)
        """
        await interaction.response.defer()
        logging.info(f"User {interaction.user.name} is marking movie at index {movie_index} as watched.")
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
                logging.error(f"Failed to remove movie '{unwatched_name}' from unwatched list during marking.")
                await interaction.followup.send("`Failed to remove movie from unwatched list during marking`")
                return

            # Adding it to the watched list
            successfully_added = self.data_manager.add_table_data(
                table_name="watched_movies",
                json_data={"movie_name": unwatched_name, "added_by": unwatched_user_id}
            )
            if successfully_added:
                logging.info(f"Marked movie '{unwatched_name}' as watched.")
                await interaction.followup.send("Marked **" + unwatched_name + "** as watched")
            else:
                logging.error(f"Failed to add movie '{unwatched_name}' to the watched list.")
                await interaction.followup.send("`Failed to add movie to the watched list`")
        except ListIndexOutOfBounds as error:
            logging.warning(f"ListIndexOutOfBounds error for user {interaction.user.name} at index {movie_index}: {error}")
            await error.handle_index_error(interaction, requires_followup=True)

    @group.command(name="searchmovie",
                   description="List all unwatched movies that contain the keyword")
    @app_commands.describe(keyword="Keyword movie name")
    async def search_movie(self, interaction: Interaction, keyword: str):
        """
        Lists all unwatched movies that contain the given keyword.

        :param interaction: The Discord interaction object
        :param keyword: The keyword to search for in movie names
        """
        logging.info(f"User {interaction.user.name} is searching for movies with keyword: '{keyword}'")

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

    @group.command(name="randommovie", description="Choose a random movie to watch (from unwatched list)")
    @app_commands.describe(keyword="[OPTIONAL] Keyword movie name")
    async def random_movie(self, interaction: Interaction, keyword: str = ""):
        """
        Chooses a random unwatched movie, optionally filtered by a keyword.

        :param interaction: The Discord interaction object
        :param keyword: Optional keyword to filter movies by name
        """
        logging.info(f"User {interaction.user.name} is requesting a random movie with keyword: '{keyword}'")
        # Getting a list of movies to choose a random selection from
        if keyword:
            possible_movies = self.search_unwatched_by_keyword(keyword)
        else:
            possible_movies = self.data_manager.data.get("unwatched_movies")

        # Checking if we have any movies available
        if possible_movies:
            # Getting a random movie and a random movie phrase
            movie = random.choice(possible_movies)
            phrase = random.choice(self.data_manager.data.get("movie_phrases"))

            # Generating the output string. Determining if we should return the added_by user
            output_string = f"**{movie.get('movie_name', '')}** {phrase.get('phrase')}"

            added_by = movie.get("added_by")
            if added_by.get("user_id") != 0:
                output_string += f" It was recommended by **{added_by.get('user_name')}**."

            logging.info(f"Randomly selected movie: '{movie.get('movie_name', '')}' for user {interaction.user.name}")

            await interaction.response.send_message(output_string)
        else:
            logging.info(f"No movies found with keyword '{keyword}' for user {interaction.user.name}")
            await interaction.response.send_message(
                f"`No movies found with keyword '{keyword}'`",
                ephemeral=True
            )

