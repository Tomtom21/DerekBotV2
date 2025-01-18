import time
from supabase import Client

# max_attempts is how many times a signin attempt will be made
# wait_time is how long it will wait between attempts
def signin_attempt_loop(supabase_client: Client, supabase_username, supabase_password, max_attempts=5, wait_time=30):
    attempts = 0
    while attempts < max_attempts:
        try:
            supabase_client.auth.sign_in_with_password({"email": supabase_username, "password": supabase_password})
            print("Database Login Successful")
            break
        except Exception as e:
            print(f"Database signin attempt failed. Retrying in {wait_time} seconds")
            attempts += 1
            time.sleep(wait_time)
