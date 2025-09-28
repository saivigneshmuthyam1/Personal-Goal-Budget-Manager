# src/services/recurring_transaction_service.py
from src.dao.recurring_transaction_dao import RecurringTransactionDAO
from src.services.transaction_service import TransactionService
from src.services.debt_service import DebtService, DebtError # Import DebtService
from datetime import date
from dateutil.relativedelta import relativedelta

class RecurringTransactionService:
    # UPDATED: Add DebtService
    def __init__(self, recurring_dao: RecurringTransactionDAO, transaction_service: TransactionService, debt_service: DebtService):
        self.recurring_dao = recurring_dao
        self.transaction_service = transaction_service
        self.debt_service = debt_service

    # UPDATED: This method now also handles paying down debt
    def process_due_transactions(self):
        """
        Checks for and processes all recurring transactions that are due.
        If a transaction is linked to a debt, it also pays down the debt.
        """
        due_transactions = self.recurring_dao.get_due_transactions()
        if not due_transactions:
            return

        print(f"\nProcessing {len(due_transactions)} due recurring transaction(s)...")
        for rt in due_transactions:
            try:
                # Step 1: Log the transaction as a general income/expense
                if rt['type'] == 'Income':
                    self.transaction_service.add_income(rt['amount'], rt['account_id'], rt['description'])
                elif rt['type'] == 'Expense':
                    self.transaction_service.add_expense(rt['amount'], rt['description'], rt['account_id'], rt['description'])

                # Step 2: NEW - If linked to a debt, reduce the debt balance
                if rt.get('debt_id'):
                    self.debt_service.make_payment(rt['debt_id'], rt['amount'])
                    print(f"  -> Applied EMI payment to debt ID {rt['debt_id']}.")

                # Step 3: Update the next_due_date
                current_due_date = date.fromisoformat(rt['next_due_date'])
                if rt['frequency'] == 'monthly':
                    new_due_date = current_due_date + relativedelta(months=1)
                else:
                    new_due_date = current_due_date + relativedelta(months=1)
                
                self.recurring_dao.update_next_due_date(rt['recurring_transaction_id'], new_due_date)
                print(f"  -> Processed '{rt['description']}'")
            except (DebtError, Exception) as e:
                print(f"  -> Failed to process '{rt['description']}': {e}")
        print("...Done.\n")