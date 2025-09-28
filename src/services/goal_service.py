'''
# src/services/goal_service.py
from typing import Dict, List, Optional
from src.dao.goal_dao import GoalDAO
from src.dao.step_dao import StepDAO
from src.dao.transaction_dao import TransactionDAO

class GoalError(Exception):
    """Custom exception for goal-related business logic errors."""
    pass

class GoalService:
    """
    Handles the main business logic for managing goals
    and calculating their progress.
    """
    def __init__(
        self, goal_dao: GoalDAO, step_dao: StepDAO, transaction_dao: TransactionDAO
    ):
        self.goal_dao = goal_dao
        self.step_dao = step_dao
        self.transaction_dao = transaction_dao

    def create_new_goal(self, name: str, budget: Optional[float] = None) -> Dict:
        """Creates a new goal."""
        return self.goal_dao.create_goal(name, budget)

    def get_goal_details(self, goal_id: int) -> Dict:
        """
        Fetches all details for a goal, including its steps and a
        calculated financial summary. This is the core feature.
        """
        # Step 1: Get the main goal record from its DAO.
        goal = self.goal_dao.get_goal_by_id(goal_id)
        if not goal:
            raise GoalError(f"Goal with ID {goal_id} not found.")

        # Step 2: Get all related data from other DAOs.
        steps = self.step_dao.get_steps_by_goal_id(goal_id)
        transactions = self.transaction_dao.get_transactions_by_goal_id(goal_id)

        # Step 3: Perform the business logic - the calculation.
        budget = goal.get("budget") or 0.0
        amount_saved = sum(t["amount"] for t in transactions if t["type"] == 'Saving')
        amount_spent = sum(t["amount"] for t in transactions if t["type"] == 'Expense')
        
        remaining_to_save = budget - amount_saved
        progress_percentage = (amount_saved / budget * 100) if budget > 0 else 0

        # Step 4: Assemble everything into a single, clean package to return to the user.
        goal["steps"] = steps
        goal["financial_summary"] = {
            "budget": budget,
            "amount_saved": amount_saved,
            "amount_spent_on_goal": amount_spent,
            "remaining_to_save": remaining_to_save,
            "progress_percentage": f"{progress_percentage:.2f}%"
        }
        
        return goal

    def list_all_goals(self) -> List[Dict]:
        """Returns a simple list of all goals."""
        return self.goal_dao.list_goals()

    def mark_goal_as_complete(self, goal_id: int) -> Dict:
        """Updates a goal's status to 'Completed'."""
        return self.goal_dao.update_goal(goal_id, {"status": "Completed"})
'''
# src/services/goal_service.py
from typing import Dict, List, Optional
from src.dao.goal_dao import GoalDAO
from src.dao.step_dao import StepDAO
from src.dao.transaction_dao import TransactionDAO

class GoalError(Exception):
    """Custom exception for goal-related business logic errors."""
    pass

class GoalService:
    """
    Handles the main business logic for managing goals
    and calculating their progress.
    """
    def __init__(
        self, goal_dao: GoalDAO, step_dao: StepDAO, transaction_dao: TransactionDAO
    ):
        self.goal_dao = goal_dao
        self.step_dao = step_dao
        self.transaction_dao = transaction_dao

    def create_new_goal(self, name: str, budget: Optional[float] = None) -> Dict:
        """Creates a new goal."""
        return self.goal_dao.create_goal(name, budget)

    def get_goal_details(self, goal_id: int) -> Dict:
        """
        Fetches all details for a goal, including its steps and a
        calculated financial summary.
        """
        goal = self.goal_dao.get_goal_by_id(goal_id)
        if not goal:
            raise GoalError(f"Goal with ID {goal_id} not found.")

        steps = self.step_dao.get_steps_by_goal_id(goal_id)
        transactions = self.transaction_dao.get_transactions_by_goal_id(goal_id)

        budget = goal.get("budget") or 0.0
        amount_saved = sum(t["amount"] for t in transactions if t["type"] == 'Saving')
        amount_spent_on_goal = sum(t["amount"] for t in transactions if t["type"] == 'Expense')
        
        remaining_to_save = budget - amount_saved
        progress_percentage = (amount_saved / budget * 100) if budget > 0 else 0

        goal["steps"] = steps
        goal["financial_summary"] = {
            "budget": budget,
            "amount_saved": amount_saved,
            "amount_spent_on_goal": amount_spent_on_goal,
            "remaining_to_save": remaining_to_save,
            "progress_percentage": f"{progress_percentage:.2f}%"
        }
        
        return goal

    def list_all_goals(self) -> List[Dict]:
        """Returns a simple list of all goals."""
        return self.goal_dao.list_goals()

    def mark_goal_as_complete(self, goal_id: int) -> Dict:
        """Updates a goal's status to 'Completed'."""
        if not self.goal_dao.get_goal_by_id(goal_id):
            raise GoalError(f"Goal with ID {goal_id} not found.")
        return self.goal_dao.update_goal(goal_id, {"status": "Completed"})

    def update_goal_details(self, goal_id: int, new_name: Optional[str] = None, new_budget: Optional[float] = None) -> Dict:
        """Updates a goal's name and/or budget."""
        if not self.goal_dao.get_goal_by_id(goal_id):
            raise GoalError(f"Goal with ID {goal_id} not found.")

        updates = {}
        if new_name:
            updates["name"] = new_name
        if new_budget is not None:
            updates["budget"] = new_budget
        
        if not updates:
            return self.goal_dao.get_goal_by_id(goal_id)
            
        return self.goal_dao.update_goal(goal_id, updates)