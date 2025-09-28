# src/dao/step_dao.py
from typing import List, Dict, Optional
from supabase import Client

class StepDAO:
    """
    Data Access Object for handling 'steps' (tasks) table operations.
    """
    def __init__(self, db_client: Client):
        self.db = db_client
        self.table = "steps"

    def create_step(self, goal_id: int, description: str) -> Optional[Dict]:
        """Creates a new step for a given goal."""
        payload = {"goal_id": goal_id, "description": description}
        resp = self.db.table(self.table).insert(payload).execute()
        return resp.data[0] if resp.data else None

    def get_steps_by_goal_id(self, goal_id: int) -> List[Dict]:
        """Retrieves all steps associated with a single goal."""
        resp = self.db.table(self.table).select("*").eq("goal_id", goal_id).order("created_at").execute()
        return resp.data or []

    def update_step(self, step_id: int, updates: Dict) -> Optional[Dict]:
        """Updates a step's details (e.g., description, status)."""
        resp = self.db.table(self.table).update(updates).eq("step_id", step_id).execute()
        return resp.data[0] if resp.data else None