# src/dao/transaction_dao.py
from typing import List, Dict, Optional
from supabase import Client

class TransactionDAO:
    """
    Data Access Object for handling 'transactions' table operations.
    """
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table = "transactions"

    def create_transaction(
        self,
        amount: float,
        type: str,
        account_id: int, # UPDATED: account_id is now required
        goal_id: Optional[int] = None,
        category_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> Optional[Dict]:
        """Creates a new transaction, which must be linked to an account."""
        payload = {
            "account_id": account_id,
            "goal_id": goal_id,
            "category_id": category_id,
            "amount": amount,
            "type": type,
            "description": description
        }
        resp = self.db.table(self.table).insert(payload).execute()
        return resp.data[0] if resp.data else None

    def get_transactions_by_goal_id(self, goal_id: int) -> List[Dict]:
        """Retrieves all transactions associated with a single goal."""
        resp = self.db.table(self.table).select("*, categories(name)").eq("goal_id", goal_id).order("transaction_date").execute()
        return resp.data or []

    def get_spending_report(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Fetches aggregated spending data, grouped by category.
        This requires a PostgreSQL function in Supabase.
        """
        resp = self.db.rpc('spending_report_by_category', {'start_date': start_date, 'end_date': end_date}).execute()
        return resp.data or []