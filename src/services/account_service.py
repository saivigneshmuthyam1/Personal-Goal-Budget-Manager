# src/services/account_service.py
from typing import List, Dict, Optional
from src.dao.account_dao import AccountDAO

class AccountService:
    """
    Handles business logic for financial accounts.
    """
    def __init__(self, account_dao: AccountDAO):
        self.account_dao = account_dao

    def create_account(self, name: str, initial_balance: float = 0.0) -> Optional[Dict]:
        """Creates a new account."""
        return self.account_dao.create_account(name, initial_balance)

    def list_accounts(self) -> List[Dict]:
        """Lists all available accounts."""
        return self.account_dao.list_accounts()