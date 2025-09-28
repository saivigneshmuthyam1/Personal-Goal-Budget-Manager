# src/services/step_service.py
from typing import Dict
from src.dao.step_dao import StepDAO
from src.dao.goal_dao import GoalDAO

class StepError(Exception):
    """Custom exception for step-related business logic errors."""
    pass

class StepService:
    """
    Handles business logic for steps (tasks) within a goal.
    """
    def __init__(self, step_dao: StepDAO, goal_dao: GoalDAO):
        self.step_dao = step_dao
        self.goal_dao = goal_dao

    def add_step_to_goal(self, goal_id: int, description: str) -> Dict:
        """Adds a new step to a goal, after checking for duplicates."""
        # Rule 1: A step can only be added to a goal that exists.
        if not self.goal_dao.get_goal_by_id(goal_id):
            raise StepError(f"Goal with ID {goal_id} not found.")
        
        # NEW: Rule 2: Check for duplicate step descriptions.
        existing_steps = self.step_dao.get_steps_by_goal_id(goal_id)
        for step in existing_steps:
            if step['description'].lower() == description.lower():
                raise StepError(f'Step "{description}" already exists for this goal.')
        
        # If all checks pass, create the new step.
        return self.step_dao.create_step(goal_id, description)

    def mark_step_as_completed(self, step_id: int) -> Dict:
        """Updates a step's status to 'Completed'."""
        return self.step_dao.update_step(step_id, {"status": "Completed"})