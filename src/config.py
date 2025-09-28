# src/config.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

class AppConfig:
    """
    Manages application configuration and shared resources like the database client.
    """
    _supabase_client: Client = None

    def __init__(self):
        load_dotenv()

    def get_supabase_client(self) -> Client:
        """
        Initializes and returns a singleton Supabase client instance.
        """
        if self._supabase_client is None:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            if not supabase_url or not supabase_key:
                raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")
            self._supabase_client = create_client(supabase_url, supabase_key)
        return self._supabase_client

# This line creates the object that other files import.
# It was likely missing from your file.
config = AppConfig()