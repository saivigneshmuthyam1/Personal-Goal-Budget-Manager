# src/services/transaction_service.py
from typing import Dict, Optional
from src.dao.transaction_dao import TransactionDAO
from src.dao.goal_dao import GoalDAO
from src.dao.category_dao import CategoryDAO
from src.dao.account_dao import AccountDAO # Import AccountDAO

class TransactionError(Exception):
    """Custom exception for transaction-related business logic errors."""
    pass

class TransactionService:
    """
    Handles business logic for financial transactions, including updating account balances.
    """
    def __init__(
        self,
        transaction_dao: TransactionDAO,
        goal_dao: GoalDAO,
        category_dao: CategoryDAO,
        account_dao: AccountDAO # Add AccountDAO
    ):
        self.transaction_dao = transaction_dao
        self.goal_dao = goal_dao
        self.category_dao = category_dao
        self.account_dao = account_dao # Store AccountDAO

    def add_expense(
        self, amount: float, category_name: str, account_id: int, description: Optional[str]
    ) -> Dict:
        """Adds a general expense, assigning it to a category and deducting from an account."""
        # Step 1: Validate the account exists
        account = self.account_dao.get_account_by_id(account_id)
        if not account:
            raise TransactionError(f"Account with ID {account_id} not found.")

        # Step 2: Update the account balance
        new_balance = account['balance'] - amount
        self.account_dao.update_account_balance(account_id, new_balance)

        # Step 3: Create the transaction record
        category = self.category_dao.get_or_create_category(category_name)
        return self.transaction_dao.create_transaction(
            amount=amount,
            type='Expense',
            account_id=account_id,
            category_id=category['category_id'],
            description=description
        )

    def add_income(self, amount: float, account_id: int, description: Optional[str]) -> Dict:
        """Adds a general income record and adds it to an account."""
        # Step 1: Validate the account exists
        account = self.account_dao.get_account_by_id(account_id)
        if not account:
            raise TransactionError(f"Account with ID {account_id} not found.")

        # Step 2: Update the account balance
        new_balance = account['balance'] + amount
        self.account_dao.update_account_balance(account_id, new_balance)
        
        # Step 3: Create the transaction record
        return self.transaction_dao.create_transaction(
            amount=amount,
            type='Income',
            account_id=account_id,
            description=description
        )

    def allocate_to_goal(self, goal_id: int, amount: float, account_id: int, description: Optional[str]) -> Dict:
        """Allocates a saving amount from an account to a specific goal."""
        # Rule 1: Validate that the goal exists.
        if not self.goal_dao.get_goal_by_id(goal_id):
            raise TransactionError(f"Goal with ID {goal_id} not found.")

        # Rule 2: Validate that the account exists and has enough funds.
        account = self.account_dao.get_account_by_id(account_id)
        if not account:
            raise TransactionError(f"Account with ID {account_id} not found.")
        if account['balance'] < amount:
            raise TransactionError(f"Insufficient funds in '{account['name']}'. "
                                   f"Required: {amount}, Available: {account['balance']}.")

        # This action is effectively an expense from a general account that is marked as a 'Saving' for a goal.
        # Step 1: Deduct the amount from the account balance
        new_balance = account['balance'] - amount
        self.account_dao.update_account_balance(account_id, new_balance)

        # Step 2: Create the 'Saving' transaction linked to the goal
        return self.transaction_dao.create_transaction(
            amount=amount,
            type='Saving',
            account_id=account_id,
            goal_id=goal_id,
            description=description
        )