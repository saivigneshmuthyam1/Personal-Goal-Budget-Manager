# src/dao/account_dao.py
from typing import List, Dict, Optional
from supabase import Client

class AccountDAO:
    """
    Data Access Object for handling 'accounts' table operations.
    """
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table = "accounts"

    def create_account(self, name: str, initial_balance: float = 0.0) -> Optional[Dict]:
        """Creates a new account."""
        payload = {"name": name, "balance": initial_balance}
        resp = self.db.table(self.table).insert(payload).execute()
        return resp.data[0] if resp.data else None

    def get_account_by_id(self, account_id: int) -> Optional[Dict]:
        """Retrieves a single account by its ID."""
        resp = self.db.table(self.table).select("*").eq("account_id", account_id).limit(1).execute()
        return resp.data[0] if resp.data else None

    def list_accounts(self) -> List[Dict]:
        """Lists all accounts."""
        resp = self.db.table(self.table).select("*").order("name").execute()
        return resp.data or []

    def update_account_balance(self, account_id: int, new_balance: float) -> Optional[Dict]:
        """Updates the balance of a specific account."""
        resp = self.db.table(self.table).update({"balance": new_balance}).eq("account_id", account_id).execute()
        return resp.data[0] if resp.data else None