# src/dao/debt_dao.py
from typing import List, Dict, Optional
from supabase import Client

class DebtDAO:
    """
    Data Access Object for handling 'debts' table operations.
    """
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table = "debts"

    def create_debt(self, name: str, total_amount: float, monthly_emi: Optional[float]) -> Optional[Dict]:
        """Creates a new debt record."""
        payload = {
            "name": name,
            "total_amount": total_amount,
            "remaining_amount": total_amount,
            "monthly_emi": monthly_emi
        }
        resp = self.db.table(self.table).insert(payload).execute()
        return resp.data[0] if resp.data else None

    def list_debts(self) -> List[Dict]:
        """Lists all debts."""
        resp = self.db.table(self.table).select("*").order("created_at").execute()
        return resp.data or []

    def update_debt_balance(self, debt_id: int, new_remaining_amount: float) -> Optional[Dict]:
        """Updates the remaining balance of a debt."""
        resp = self.db.table(self.table).update({"remaining_amount": new_remaining_amount}).eq("debt_id", debt_id).execute()
        return resp.data[0] if resp.data else None

    # NEW METHOD: To get a specific debt for editing
    def get_debt_by_id(self, debt_id: int) -> Optional[Dict]:
        """Retrieves a single debt by its ID."""
        resp = self.db.table(self.table).select("*").eq("debt_id", debt_id).limit(1).execute()
        return resp.data[0] if resp.data else None

    # NEW METHOD: To update any part of a debt record
    def update_debt(self, debt_id: int, updates: Dict) -> Optional[Dict]:
        """Updates a debt's details."""
        resp = self.db.table(self.table).update(updates).eq("debt_id", debt_id).execute()
        return resp.data[0] if resp.data else None