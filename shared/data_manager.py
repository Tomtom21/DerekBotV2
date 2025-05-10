import os
from supabase import create_client, Client
import logging
import time
from discord import Interaction, Member
from abc import abstractmethod


class ListIndexOutOfBounds(Exception):
    def __init__(self, item_count: int):
        self.item_count = item_count

    async def handle_index_error(self, interaction: Interaction):
        await interaction.response.send_message(
            "`Item index is outside of the valid range (1-" + str(self.item_count) + ")`",
            ephemeral=True
        )


class DataManager:
    def __init__(self, db_table_fetch_config: dict, max_login_attempts=5, wait_time=30):
        # Getting the supabase db info. These are not maintained in memory
        supabase_url: str = os.environ.get('SUPABASE_URL')
        supabase_key: str = os.environ.get('SUPABASE_KEY')
        supabase_email: str = os.environ.get('SUPABASE_EMAIL')
        supabase_password: str = os.environ.get('SUPABASE_PASSWORD')

        # Setting up the database client, logging in
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.signin_attempt_loop(
            supabase_username=supabase_email,
            supabase_password=supabase_password,
            max_login_attempts=max_login_attempts,
            wait_time=wait_time
        )

        self.db_table_fetch_config = db_table_fetch_config

        # Setting up our local cache of table data
        self.data: dict[str, list[dict]] = {}
        for name in db_table_fetch_config.keys():
            self.data[name] = []

        # Fetching all data needed
        self.fetch_all_table_data()

    def signin_attempt_loop(self, supabase_username, supabase_password, max_login_attempts, wait_time):
        """
        Make repeated attempts to sign in to Supabase

        :param supabase_username: The Supabase username
        :param supabase_password: The Supabase password
        :param max_login_attempts: The max number of attempts to make during sign in
        :param wait_time: The time to wait between attempts to sign in
        """
        attempts = 0
        logging.info("Attempting database login")
        while attempts < max_login_attempts:
            try:
                self.supabase.auth.sign_in_with_password({"email": supabase_username, "password": supabase_password})
                logging.info("Database Login Successful")
                break
            except Exception as e:
                logging.error(f"Database signin attempt failed: {e}. Retrying in {wait_time} seconds")
                attempts += 1
                time.sleep(wait_time)

    @staticmethod
    def execute_db_query(query, table_name):
        try:
            response = query.execute()
            return response
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            logging.error(f"Failed to retrieve data from table {table_name}")
            return None

    def fetch_table_data(self, table_name):
        # Table fetch config
        config = self.db_table_fetch_config.get(table_name, {})
        query = self.supabase.table(table_name).select(config.get("select", "*"))

        # Doing orders
        order_by = config.get("order_by")
        if order_by:
            query = query.order(order_by["column"], desc=not order_by["ascending"])

        # Executing the query, saving the data
        response = self.execute_db_query(query, table_name)
        if response:
            self.data[table_name] = response.data

    def add_table_data(self, table_name, json_data):
        # Building our add item query
        query = self.supabase.table(table_name).insert(json_data)

        # Executing our insert query
        response = self.execute_db_query(query, table_name)

        # Fetching a new copy of the db
        self.fetch_table_data(table_name)

        # Returning to the user whether it was successful or not
        if response:
            return True
        else:
            logging.error(f"Failed to add {json_data} to table {table_name}")
            return False

    def delete_table_data(self, table_name, match_json):
        # Building the remove item query
        query = self.supabase.table(table_name).delete().match(match_json)

        # Executing the remove query
        response = self.execute_db_query(query, table_name)

        # Fetching a new copy of the db
        self.fetch_table_data(table_name)

        # Returning to the user whether it was successful or not
        if response:
            return True
        else:
            logging.error(f"Failed to remove items matching info {match_json} from table {table_name}")
            return False

    def fetch_all_table_data(self):
        for name in self.db_table_fetch_config.keys():
            self.fetch_table_data(name)

    def get_db_item_with_index(self, table_name: str, item_index: int):
        """
        Gets an item from a DB table using an index (1-length).
        This is made for processing user input referencing a DiscordList item index.

        :param table_name: The name of the table to get the item from
        :param item_index: The index of the item in the DB cache
        :return: The item from the table in the DB cache
        """
        item_count = len(self.data.get(table_name))
        if item_count >= item_index >= 1:
            # Pulling item information from the table
            item = self.data.get(table_name)[item_index - 1]
            return item
        else:
            raise ListIndexOutOfBounds(item_count)

    def ensure_user_exists(self, user: Member):
        """
        Ensures that a user exists in the users table

        :param user: The use to check for existence
        :return: True if they exist or have been added, False if an error occurred
        """
        # If the user is not in the users table
        if not any(db_user["user_id"] == user.id for db_user in self.data.get("users")):
            successfully_added = self.add_table_data(
                table_name="users",
                json_data={
                    "user_name": user.name,
                    "user_id": user.id,
                    "is_administrator": False,
                    "is_creator": False,
                    "shuffle_nickname": False
                }
            )
            if successfully_added:
                logging.info(f"User {user.name}({user.id}) has been added to the users list")
            else:
                logging.error(f"There was an issue adding user {user.name}({user.id})")
