# src/dao/recurring_transaction_dao.py
from typing import List, Dict, Optional
from supabase import Client
import datetime

class RecurringTransactionDAO:
    """
    Data Access Object for handling 'recurring_transactions' table operations.
    """
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table = "recurring_transactions"

    def create_recurring_transaction(self, **kwargs) -> Optional[Dict]:
        """Creates a new recurring transaction."""
        resp = self.db.table(self.table).insert(kwargs).execute()
        return resp.data[0] if resp.data else None

    def get_due_transactions(self) -> List[Dict]:
        """Fetches all recurring transactions that are due to be processed."""
        today = datetime.date.today().isoformat()
        resp = self.db.table(self.table).select("*").lte("next_due_date", today).execute()
        return resp.data or []

    def update_next_due_date(self, recurring_id: int, new_due_date: datetime.date) -> Optional[Dict]:
        """Updates the next_due_date for a recurring transaction."""
        updates = {"next_due_date": new_due_date.isoformat()}
        resp = self.db.table(self.table).update(updates).eq("recurring_transaction_id", recurring_id).execute()
        return resp.data[0] if resp.data else None