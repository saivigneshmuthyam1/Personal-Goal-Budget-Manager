# src/dao/category_dao.py
from typing import Dict, Optional
from supabase import Client

class CategoryDAO:
    """
    Data Access Object for handling 'categories' table operations.
    """
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table = "categories"

    def get_or_create_category(self, name: str) -> Optional[Dict]:
        """
        Fetches a category by name. If it doesn't exist, it creates it.
        This is useful to avoid creating duplicate categories.
        """
        # Check if category exists
        get_resp = self.db.table(self.table).select("*").eq("name", name).limit(1).execute()
        if get_resp.data:
            return get_resp.data[0]
        
        # If not, create it
        create_resp = self.db.table(self.table).insert({"name": name}).execute()
        return create_resp.data[0] if create_resp.data else None