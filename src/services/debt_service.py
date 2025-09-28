# src/services/debt_service.py
from typing import List, Dict, Optional
from src.dao.debt_dao import DebtDAO
from src.dao.account_dao import AccountDAO
from src.services.transaction_service import TransactionService, TransactionError

class DebtError(Exception):
    pass

class DebtService:
    """
    Handles business logic for debts and loans.
    """
    # UPDATED: Now depends on other components
    def __init__(self, debt_dao: DebtDAO, account_dao: AccountDAO, transaction_service: TransactionService):
        self.debt_dao = debt_dao
        self.account_dao = account_dao
        self.transaction_service = transaction_service

    def add_debt(self, name: str, total_amount: float, monthly_emi: Optional[float] = None) -> Optional[Dict]:
        """Creates a new debt record."""
        return self.debt_dao.create_debt(name, total_amount, monthly_emi)

    def list_debts(self) -> List[Dict]:
        """Lists all current debts."""
        return self.debt_dao.list_debts()

    # UPDATED: This method is now used by the recurring transaction service
    def make_payment(self, debt_id: int, amount: float) -> Optional[Dict]:
        """Internal method to reduce debt balance."""
        debt = self.debt_dao.get_debt_by_id(debt_id)
        if not debt:
            raise DebtError(f"Debt with ID {debt_id} not found.")
        new_remaining_amount = debt['remaining_amount'] - amount
        return self.debt_dao.update_debt_balance(debt_id, new_remaining_amount)

    # NEW METHOD: For handling manual payments from the user
    def make_manual_payment(self, debt_id: int, account_id: int, amount: float) -> Dict:
        """
        Processes a manual payment for a debt.
        1. Logs an expense transaction from the specified account.
        2. Reduces the remaining balance of the debt.
        """
        # The transaction service already checks for sufficient funds and updates the account balance.
        # We will log this payment under a specific category.
        payment_description = f"Payment for debt ID {debt_id}"
        self.transaction_service.add_expense(amount, "Debt Payment", account_id, payment_description)

        # Now, reduce the debt's remaining amount
        updated_debt = self.make_payment(debt_id, amount)
        return updated_debt

    def update_debt_details(self, debt_id: int, **kwargs) -> Optional[Dict]:
        """Updates a debt's details."""
        current_debt = self.debt_dao.get_debt_by_id(debt_id)
        if not current_debt:
            raise DebtError(f"Debt with ID {debt_id} not found.")
        updates = {}
        new_total_amount = kwargs.get("total_amount")
        if new_total_amount is not None:
            old_total_amount = current_debt.get("total_amount", 0.0)
            difference = new_total_amount - old_total_amount
            new_remaining_amount = current_debt.get("remaining_amount", 0.0) + difference
            updates["total_amount"] = new_total_amount
            updates["remaining_amount"] = new_remaining_amount
        if kwargs.get("name") is not None and kwargs.get("name"):
            updates["name"] = kwargs["name"]
        if kwargs.get("monthly_emi") is not None:
            updates["monthly_emi"] = kwargs["monthly_emi"]
        if not updates:
            return current_debt
        return self.debt_dao.update_debt(debt_id, updates)  