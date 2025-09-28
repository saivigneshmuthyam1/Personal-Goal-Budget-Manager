# src/services/reporting_service.py
from typing import Dict, List
from src.dao.transaction_dao import TransactionDAO
from src.dao.category_dao import CategoryDAO

class ReportingService:
    """
    Service for generating financial reports.
    """
    def __init__(self, transaction_dao: TransactionDAO, category_dao: CategoryDAO):
        self.transaction_dao = transaction_dao
        self.category_dao = category_dao

    def generate_spending_summary(self, start_date: str, end_date: str) -> Dict:
        """
        Generates a summary of expenses by category for a given date range.
        """
        report_data = self.transaction_dao.get_spending_report(start_date, end_date)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "summary": report_data
        }