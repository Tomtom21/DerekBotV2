import os
from supabase import create_client, Client
from libs.supabase_utils import signin_attempt_loop

# Setting up the supabase connection
supabase_url: str = os.environ.get('SUPABASE_URL')
supabase_key: str = os.environ.get('SUPABASE_KEY')
supabase_email: str = os.environ.get('SUPABASE_EMAIL')
supabase_password: str = os.environ.get('SUPABASE_PASSWORD')

# Connecting to the database
supabase: Client = create_client(supabase_url, supabase_key)
signin_attempt_loop(supabase, supabase_email, supabase_password)

response = supabase.table("birthdays").select("*").execute()
print(response.data)
