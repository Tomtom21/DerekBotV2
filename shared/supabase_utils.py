import time
import logging
from supabase import Client


# max_attempts is how many times a signin attempt will be made
# wait_time is how long it will wait between attempts
def signin_attempt_loop(supabase_client: Client, supabase_username, supabase_password, max_attempts=5, wait_time=30):
    """
    Make repeated attempts to sign in to Supabase

    :param supabase_client: The Supabase client to use
    :param supabase_username: The Supabase username
    :param supabase_password: The Supabase password
    :param max_attempts: The max number of attempts to make during sign in
    :param wait_time: The time to wait between attempts to sign in
    """
    attempts = 0
    logging.info("Attempting database login")
    while attempts < max_attempts:
        try:
            supabase_client.auth.sign_in_with_password({"email": supabase_username, "password": supabase_password})
            logging.info("Database Login Successful")
            break
        except Exception as e:
            logging.error(f"Database signin attempt failed: {e}. Retrying in {wait_time} seconds")
            attempts += 1
            time.sleep(wait_time)
