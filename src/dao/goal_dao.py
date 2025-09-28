# src/dao/goal_dao.py
from typing import List, Dict, Optional
from supabase import Client

class GoalDAO:
    """
    Data Access Object for handling 'goals' table operations.
    """
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table = "goals"

    def create_goal(self, name: str, budget: Optional[float] = None) -> Optional[Dict]:
        """Creates a new goal."""
        payload = {"name": name, "budget": budget}
        resp = self.db.table(self.table).insert(payload).execute()
        return resp.data[0] if resp.data else None

    def get_goal_by_id(self, goal_id: int) -> Optional[Dict]:
        """Retrieves a single goal by its primary key."""
        resp = self.db.table(self.table).select("*").eq("goal_id", goal_id).limit(1).execute()
        return resp.data[0] if resp.data else None

    def list_goals(self) -> List[Dict]:
        """Lists all goals."""
        resp = self.db.table(self.table).select("*").order("created_at").execute()
        return resp.data or []

    def update_goal(self, goal_id: int, updates: Dict) -> Optional[Dict]:
        """Updates a goal's details (e.g., name, status, budget)."""
        resp = self.db.table(self.table).update(updates).eq("goal_id", goal_id).execute()
        return resp.data[0] if resp.data else None