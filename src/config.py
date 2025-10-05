'''# src/config.py
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
'''
# src/config.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables from .env file for local development
load_dotenv()

# This logic attempts to get secrets from Streamlit Cloud first,
# then falls back to the local .env file.
try:
    import streamlit as st
    SUPABASE_URL = st.secrets.get("SUPABASE_URL")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
except ImportError:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
except Exception: # Handles cases where st.secrets is not available
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")


class AppConfig:
    """
    Manages application configuration and shared resources like the database client.
    """
    _supabase_client: Client = None

    def get_supabase_client(self) -> Client:
        """
        Initializes and returns a singleton Supabase client instance using
        the globally defined URL and Key.
        """
        if self._supabase_client is None:
            if not SUPABASE_URL or not SUPABASE_KEY:
                raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be set in your .env file or Streamlit secrets.")
            self._supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return self._supabase_client

# Creates a single, reusable instance of the AppConfig class
config = AppConfig()