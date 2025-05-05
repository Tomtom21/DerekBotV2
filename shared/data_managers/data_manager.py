import os
from supabase import create_client, Client
import logging
import time
from abc import abstractmethod


class DataManager:
    def __init__(self, db_table_names: [str], max_login_attempts=5, wait_time=30):
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

        # Setting up our local cache of table data
        self.data: dict[str, list[dict]] = {}
        for name in db_table_names:
            self.data[name] = []

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

    def fetch_table_data(self, table_name):
        # Getting the table data from the db
        response = (
            self.supabase.table(table_name)
            .select("*")
            .execute()
        )

        # Updating the data if it doesn't return an error
        if response.error:
            logging.error(f"Failed to retrieve data from table {table_name}. Defaulting to cache data.")
        else:
            self.data[table_name] = response.data

    def add_table_data(self, table_name, json_data):
        # Adding the item to the db
        response = (
            self.supabase.table(table_name)
            .insert(json_data)
            .execute()
        )
        if response.error:
            logging.error(f"Failed to add {json_data} to table {table_name}")

        # Fetching a new copy of the db
        self.fetch_table_data(table_name)

    def delete_table_data(self, table_name, idx):
        # Removing an item from the db based on an index
        response = (
            self.supabase.table(table_name)
            .delete()
            .eq("id", 1)
            .execute()
        )
        if response.error:
            logging.error(f"Failed to remove index {idx} from table {table_name}")

        # Fetching a new copy of the db
        self.fetch_table_data(table_name)
