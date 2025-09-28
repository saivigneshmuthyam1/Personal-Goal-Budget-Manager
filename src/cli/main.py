'''
# src/cli/main.py
import questionary
import json
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta

from src.config import config
# DAO Imports
from src.dao.goal_dao import GoalDAO
from src.dao.step_dao import StepDAO
from src.dao.transaction_dao import TransactionDAO
from src.dao.category_dao import CategoryDAO
from src.dao.account_dao import AccountDAO
from src.dao.debt_dao import DebtDAO
from src.dao.recurring_transaction_dao import RecurringTransactionDAO
# Service Imports
from src.services.goal_service import GoalService, GoalError
from src.services.step_service import StepService, StepError
from src.services.transaction_service import TransactionService, TransactionError
from src.services.account_service import AccountService
from src.services.debt_service import DebtService, DebtError
from src.services.reporting_service import ReportingService
from src.services.recurring_transaction_service import RecurringTransactionService

class GoalManagerCLI:
    def __init__(self):
        db_client = config.get_supabase_client()
        # DAOs
        goal_dao = GoalDAO(db_client)
        step_dao = StepDAO(db_client)
        transaction_dao = TransactionDAO(db_client)
        category_dao = CategoryDAO(db_client)
        account_dao = AccountDAO(db_client)
        debt_dao = DebtDAO(db_client)
        recurring_dao = RecurringTransactionDAO(db_client)
        # Services
        self.account_service = AccountService(account_dao)
        self.debt_service = DebtService(debt_dao)
        self.transaction_service = TransactionService(transaction_dao, goal_dao, category_dao, account_dao)
        self.step_service = StepService(step_dao, goal_dao)
        self.goal_service = GoalService(goal_dao, step_dao, transaction_dao)
        self.reporting_service = ReportingService(transaction_dao, category_dao)
        self.recurring_service = RecurringTransactionService(recurring_dao, self.transaction_service, self.debt_service)

    def run(self):
        """Main application loop to display the main menu."""
        print("Welcome to your Personal Finance & Goal Manager!")
        self.recurring_service.process_due_transactions()
        while True:
            choice = questionary.select(
                "What would you like to do?",
                choices=["Manage Goals", "Manage Finances", "Manage Accounts", "Manage Debts", "View Reports", "Exit"]
            ).ask()

            if choice == "Manage Goals": self._goals_menu()
            elif choice == "Manage Finances": self._finances_menu()
            elif choice == "Manage Accounts": self._accounts_menu()
            elif choice == "Manage Debts": self._debts_menu()
            elif choice == "View Reports": self._reports_menu()
            elif choice == "Exit" or choice is None:
                print("Goodbye!"); break
    
    # --- Menu Functions ---
    def _accounts_menu(self):
        while True:
            choice = questionary.select("What would you like to do with Accounts?",
                choices=["Create New Account", "List All Accounts", "Back to Main Menu"]).ask()
            if choice == "Create New Account": self._handle_create_account()
            elif choice == "List All Accounts": self._handle_list_accounts()
            elif choice == "Back to Main Menu" or choice is None: break

    def _debts_menu(self):
        while True:
            choice = questionary.select("What would you like to do with Debts?",
                choices=["Add New Debt", "List All Debts", "Edit a Debt", "Back to Main Menu"]).ask()
            if choice == "Add New Debt": self._handle_add_debt()
            elif choice == "List All Debts": self._handle_list_debts()
            elif choice == "Edit a Debt": self._handle_edit_debt()
            elif choice == "Back to Main Menu" or choice is None: break

    def _goals_menu(self):
        while True:
            choice = questionary.select("What would you like to do with Goals?",
                choices=["Create New Goal", "List All Goals", "View/Manage a Specific Goal", "Back to Main Menu"]).ask()
            if choice == "Create New Goal": self._handle_create_goal()
            elif choice == "List All Goals": self._handle_list_goals()
            elif choice == "View/Manage a Specific Goal": self._handle_manage_specific_goal()
            elif choice == "Back to Main Menu" or choice is None: break
    
    def _finances_menu(self):
        while True:
            choice = questionary.select("What would you like to do with Finances?",
                choices=["Add General Expense", "Add General Income", "Allocate Saving to Goal", "Set Up Recurring Transaction", "Back to Main Menu"]).ask()
            if choice == "Add General Expense": self._handle_add_expense()
            elif choice == "Add General Income": self._handle_add_income()
            elif choice == "Allocate Saving to Goal": self._handle_allocate_to_goal()
            elif choice == "Set Up Recurring Transaction": self._handle_setup_recurring_transaction()
            elif choice == "Back to Main Menu" or choice is None: break

    def _reports_menu(self):
        while True:
            choice = questionary.select("Which report would you like to see?",
                choices=["Monthly Spending Summary", "Back to Main Menu"]).ask()
            if choice == "Monthly Spending Summary": self._handle_spending_report()
            elif choice == "Back to Main Menu" or choice is None: break

    def _specific_goal_menu(self, goal_id):
        while True:
            try:
                goal_details = self.goal_service.get_goal_details(goal_id)
                print("\n--- Goal Details ---"); print(json.dumps(goal_details, indent=2, default=str)); print("--------------------\n")
                choice = questionary.select(f"What do you want to do with '{goal_details['name']}'?",
                    choices=["Add a Step", "Mark a Step as Completed", "Edit Goal", "Mark Goal as Completed", "Back to Goals Menu"]).ask()
                if choice == "Add a Step":
                    desc = questionary.text("Enter step description:").ask()
                    if desc: self.step_service.add_step_to_goal(goal_id, desc)
                elif choice == "Mark a Step as Completed":
                    steps = goal_details.get('steps', []); pending_steps = [s for s in steps if s['status'] == 'Pending']
                    if not pending_steps: print("No pending steps to complete."); continue
                    step_to_complete = questionary.select("Which step do you want to complete?", choices=[f"{s['step_id']}: {s['description']}" for s in pending_steps]).ask()
                    if step_to_complete:
                        step_id = int(step_to_complete.split(':')[0])
                        self.step_service.mark_step_as_completed(step_id)
                elif choice == "Edit Goal": self._handle_edit_goal(goal_id)
                elif choice == "Mark Goal as Completed":
                    if questionary.confirm(f"Are you sure you want to complete this goal?").ask():
                        self.goal_service.mark_goal_as_complete(goal_id); print("✅ Goal marked as completed!"); break
                elif choice == "Back to Goals Menu" or choice is None: break
            except (StepError, GoalError) as e:
                print(f"❌ Error: {e}")
                
    # --- Utility function to select an account ---
    def _select_account(self, prompt_message):
        accounts = self.account_service.list_accounts()
        if not accounts:
            print("❌ Error: No accounts found. Please create an account first.")
            return None
        account_choice = questionary.select(prompt_message,
            choices=[f"{acc['account_id']}: {acc['name']} (Balance: {acc['balance']})" for acc in accounts]).ask()
        if not account_choice: return None
        return int(account_choice.split(':')[0])

    # --- Handler Functions ---
    def _handle_create_account(self):
        name = questionary.text("Enter account name (e.g., Savings Account):").ask()
        if not name: return
        balance_str = questionary.text("Enter initial balance (e.g., 200000):").ask()
        balance = float(balance_str) if balance_str else 0.0
        try:
            acc = self.account_service.create_account(name, balance)
            print("✅ Account created successfully:"); print(json.dumps(acc, indent=2, default=str))
        except Exception as e: print(f"❌ Error: {e}")

    def _handle_list_accounts(self):
        accounts = self.account_service.list_accounts()
        print("\n--- All Accounts ---"); print(json.dumps(accounts, indent=2, default=str)); print("--------------------\n")

    def _handle_add_debt(self):
        name = questionary.text("Enter debt name (e.g., Laptop Loan):").ask()
        if not name: return
        amount_str = questionary.text("Enter total loan amount:").ask()
        emi_str = questionary.text("Enter monthly EMI (optional):").ask()
        try:
            debt = self.debt_service.add_debt(name, float(amount_str) if amount_str else 0.0, float(emi_str) if emi_str else None)
            print("✅ Debt added successfully:"); print(json.dumps(debt, indent=2, default=str))
        except Exception as e: print(f"❌ Error: {e}")

    def _handle_list_debts(self):
        debts = self.debt_service.list_debts()
        print("\n--- All Debts ---"); print(json.dumps(debts, indent=2, default=str)); print("-----------------\n")
    
    def _handle_edit_debt(self):
        debts = self.debt_service.list_debts()
        if not debts: print("No debts found to edit."); return
        debt_choice = questionary.select("Which debt do you want to edit?", choices=[f"{d['debt_id']}: {d['name']}" for d in debts]).ask()
        if not debt_choice: return
        debt_id = int(debt_choice.split(':')[0])
        current_debt = self.debt_service.debt_dao.get_debt_by_id(debt_id)
        print("Leave a field blank to keep its current value.")
        new_name = questionary.text("Enter new name:", default=current_debt['name']).ask()
        new_total_str = questionary.text("Enter new total amount:", default=str(current_debt['total_amount'])).ask()
        new_emi_str = questionary.text("Enter new monthly EMI:", default=str(current_debt['monthly_emi'])).ask()
        try:
            updated_debt = self.debt_service.update_debt_details(
                debt_id=debt_id, name=new_name,
                total_amount=float(new_total_str) if new_total_str else None,
                monthly_emi=float(new_emi_str) if new_emi_str else None
            )
            print("✅ Debt updated successfully:"); print(json.dumps(updated_debt, indent=2, default=str))
        except (DebtError, Exception) as e: print(f"❌ Error: {e}")

    def _handle_create_goal(self):
        name = questionary.text("What is the name of your goal?").ask()
        if not name: return
        budget_str = questionary.text("What is the budget? (optional)").ask()
        budget = float(budget_str) if budget_str else None
        try:
            goal = self.goal_service.create_new_goal(name, budget)
            print("✅ Goal created successfully:"); print(json.dumps(goal, indent=2, default=str))
        except GoalError as e: print(f"❌ Error: {e}")

    def _handle_list_goals(self):
        goals = self.goal_service.list_all_goals()
        print("\n--- All Goals ---"); print(json.dumps(goals, indent=2, default=str)); print("-----------------\n")

    def _handle_manage_specific_goal(self):
        goals = self.goal_service.list_all_goals()
        if not goals: print("No goals found. Please create one first."); return
        goal_choice = questionary.select("Which goal do you want to manage?",
            choices=[f"{g['goal_id']}: {g['name']}" for g in goals]).ask()
        if goal_choice:
            goal_id = int(goal_choice.split(':')[0])
            self._specific_goal_menu(goal_id)
            
    def _handle_edit_goal(self, goal_id: int):
        print("Leave a field blank to keep its current value.")
        current_goal = self.goal_service.get_goal_details(goal_id)
        new_name = questionary.text("Enter new goal name:", default=current_goal['name']).ask()
        new_budget_str = questionary.text("Enter new budget:", default=str(current_goal['budget'])).ask()
        new_name = new_name if new_name else None
        new_budget = float(new_budget_str) if new_budget_str else None
        try:
            updated_goal = self.goal_service.update_goal_details(goal_id, new_name, new_budget)
            print("✅ Goal updated successfully:"); print(json.dumps(updated_goal, indent=2, default=str))
        except GoalError as e: print(f"❌ Error: {e}")

    def _handle_add_expense(self):
        account_id = self._select_account("Which account to use for this expense?")
        if not account_id: return
        categories = ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Shopping", "EMI", "Other (create new)"]
        amount_str = questionary.text("Enter expense amount:").ask()
        if not amount_str: return
        category_choice = questionary.select("Select a category:", choices=categories).ask()
        if not category_choice: return
        if category_choice == "Other (create new)":
            category_name = questionary.text("Enter the new category name:").ask()
            if not category_name: return
        else: category_name = category_choice
        desc = questionary.text("Enter description (optional):").ask()
        try:
            trx = self.transaction_service.add_expense(float(amount_str), category_name, account_id, desc)
            print("✅ Expense added successfully:"); print(json.dumps(trx, indent=2, default=str))
        except TransactionError as e: print(f"❌ Error: {e}")

    def _handle_add_income(self):
        account_id = self._select_account("Which account will this income go into?")
        if not account_id: return
        amount_str = questionary.text("Enter income amount:").ask()
        if not amount_str: return
        desc = questionary.text("Enter description (optional):").ask()
        try:
            trx = self.transaction_service.add_income(float(amount_str), account_id, desc)
            print("✅ Income added successfully:"); print(json.dumps(trx, indent=2, default=str))
        except TransactionError as e: print(f"❌ Error: {e}")

    def _handle_allocate_to_goal(self):
        account_id = self._select_account("Which account are you allocating savings FROM?")
        if not account_id: return
        goals = self.goal_service.list_all_goals()
        if not goals: print("No goals found to allocate to."); return
        goal_choice = questionary.select("Which goal do you want to allocate savings TO?", choices=[f"{g['goal_id']}: {g['name']}" for g in goals]).ask()
        if not goal_choice: return
        goal_id = int(goal_choice.split(':')[0])
        amount_str = questionary.text(f"Enter amount to allocate from your account to '{goal_choice.split(': ')[1]}':").ask()
        desc = questionary.text("Enter description (optional):").ask()
        try:
            trx = self.transaction_service.allocate_to_goal(goal_id, float(amount_str), account_id, desc)
            print("✅ Amount allocated successfully:"); print(json.dumps(trx, indent=2, default=str))
        except TransactionError as e: print(f"❌ Error: {e}")
            
    def _handle_setup_recurring_transaction(self):
        account_id = self._select_account("Which account is this transaction for?")
        if not account_id: return
        ttype = questionary.select("Is this recurring income or expense?", choices=["Income", "Expense"]).ask()
        if not ttype: return
        amount = float(questionary.text("Enter the monthly amount:").ask())
        desc = questionary.text("Enter a description (e.g., Monthly Salary, Rent EMI):").ask()
        start_date = questionary.text("Enter the first payment date (YYYY-MM-DD):").ask()
        debt_id = None
        if ttype == 'Expense' and questionary.confirm("Is this an EMI for a specific debt?").ask():
            debts = self.debt_service.list_debts()
            if debts:
                debt_choice = questionary.select("Which debt is this EMI for?", 
                    choices=[f"{d['debt_id']}: {d['name']}" for d in debts]).ask()
                if debt_choice: debt_id = int(debt_choice.split(':')[0])
            else: print("No debts found to link this to.")
        try:
            recurring_dao = self.recurring_service.recurring_dao
            recurring_dao.create_recurring_transaction(
                account_id=account_id, description=desc, amount=amount, type=ttype, 
                frequency='monthly', start_date=start_date, next_due_date=start_date, debt_id=debt_id
            )
            print("✅ Recurring transaction set up successfully!")
        except Exception as e: print(f"❌ Error setting up recurring transaction: {e}")

    def _handle_spending_report(self):
        month_str = questionary.text("Enter the month for the report (e.g., YYYY-MM):",
            validate=lambda text: True if len(text) == 7 and text[4] == '-' else "Please use YYYY-MM format.").ask()
        if not month_str: return
        try:
            year = int(month_str[:4]); month = int(month_str[5:])
            _, last_day = calendar.monthrange(year, month)
            start_date = f"{year}-{month:02d}-01"; end_date = f"{year}-{month:02d}-{last_day}"
            report = self.reporting_service.generate_spending_summary(start_date, end_date)
            print("\n--- Monthly Spending Summary ---"); print(json.dumps(report, indent=2, default=str)); print("--------------------------------\n")
        except Exception as e: print(f"❌ Error generating report: {e}")

def main():
    cli = GoalManagerCLI()
    cli.run()

if __name__ == "__main__":
    main()
'''

# src/cli/main.py
import questionary
import json
import calendar
from datetime import date
from dateutil.relativedelta import relativedelta

from src.config import config
# DAO Imports
from src.dao.goal_dao import GoalDAO
from src.dao.step_dao import StepDAO
from src.dao.transaction_dao import TransactionDAO
from src.dao.category_dao import CategoryDAO
from src.dao.account_dao import AccountDAO
from src.dao.debt_dao import DebtDAO
from src.dao.recurring_transaction_dao import RecurringTransactionDAO
# Service Imports
from src.services.goal_service import GoalService, GoalError
from src.services.step_service import StepService, StepError
from src.services.transaction_service import TransactionService, TransactionError
from src.services.account_service import AccountService
from src.services.debt_service import DebtService, DebtError
from src.services.reporting_service import ReportingService
from src.services.recurring_transaction_service import RecurringTransactionService

class GoalManagerCLI:
    def __init__(self):
        db_client = config.get_supabase_client()
        # DAOs
        goal_dao = GoalDAO(db_client)
        step_dao = StepDAO(db_client)
        transaction_dao = TransactionDAO(db_client)
        category_dao = CategoryDAO(db_client)
        account_dao = AccountDAO(db_client)
        debt_dao = DebtDAO(db_client)
        recurring_dao = RecurringTransactionDAO(db_client)
        # Services
        self.account_service = AccountService(account_dao)
        self.transaction_service = TransactionService(transaction_dao, goal_dao, category_dao, account_dao)
        self.debt_service = DebtService(debt_dao, account_dao, self.transaction_service)
        self.step_service = StepService(step_dao, goal_dao)
        self.goal_service = GoalService(goal_dao, step_dao, transaction_dao)
        self.reporting_service = ReportingService(transaction_dao, category_dao)
        self.recurring_service = RecurringTransactionService(recurring_dao, self.transaction_service, self.debt_service)

    def run(self):
        """Main application loop to display the main menu."""
        print("Welcome to your Personal Finance & Goal Manager!")
        self.recurring_service.process_due_transactions()
        while True:
            choice = questionary.select(
                "What would you like to do?",
                choices=["Manage Goals", "Manage Finances", "Manage Accounts", "Manage Debts", "View Reports", "Exit"]
            ).ask()

            if choice == "Manage Goals": self._goals_menu()
            elif choice == "Manage Finances": self._finances_menu()
            elif choice == "Manage Accounts": self._accounts_menu()
            elif choice == "Manage Debts": self._debts_menu()
            elif choice == "View Reports": self._reports_menu()
            elif choice == "Exit" or choice is None:
                print("Goodbye!"); break
    
    # --- Menu Functions ---
    def _accounts_menu(self):
        while True:
            choice = questionary.select("What would you like to do with Accounts?",
                choices=["Create New Account", "List All Accounts", "Back to Main Menu"]).ask()
            if choice == "Create New Account": self._handle_create_account()
            elif choice == "List All Accounts": self._handle_list_accounts()
            elif choice == "Back to Main Menu" or choice is None: break

    def _debts_menu(self):
        while True:
            choice = questionary.select("What would you like to do with Debts?",
                choices=["Add New Debt", "List All Debts", "Edit a Debt", "Make a Payment", "Back to Main Menu"]).ask()
            if choice == "Add New Debt": self._handle_add_debt()
            elif choice == "List All Debts": self._handle_list_debts()
            elif choice == "Edit a Debt": self._handle_edit_debt()
            elif choice == "Make a Payment": self._handle_make_debt_payment()
            elif choice == "Back to Main Menu" or choice is None: break

    def _goals_menu(self):
        while True:
            choice = questionary.select("What would you like to do with Goals?",
                choices=["Create New Goal", "List All Goals", "View/Manage a Specific Goal", "Back to Main Menu"]).ask()
            if choice == "Create New Goal": self._handle_create_goal()
            elif choice == "List All Goals": self._handle_list_goals()
            elif choice == "View/Manage a Specific Goal": self._handle_manage_specific_goal()
            elif choice == "Back to Main Menu" or choice is None: break
    
    def _finances_menu(self):
        while True:
            choice = questionary.select("What would you like to do with Finances?",
                choices=["Add General Expense", "Add General Income", "Allocate Saving to Goal", "Set Up Recurring Transaction", "Back to Main Menu"]).ask()
            if choice == "Add General Expense": self._handle_add_expense()
            elif choice == "Add General Income": self._handle_add_income()
            elif choice == "Allocate Saving to Goal": self._handle_allocate_to_goal()
            elif choice == "Set Up Recurring Transaction": self._handle_setup_recurring_transaction()
            elif choice == "Back to Main Menu" or choice is None: break

    def _reports_menu(self):
        while True:
            choice = questionary.select("Which report would you like to see?",
                choices=["Monthly Spending Summary", "Back to Main Menu"]).ask()
            if choice == "Monthly Spending Summary": self._handle_spending_report()
            elif choice == "Back to Main Menu" or choice is None: break

    def _specific_goal_menu(self, goal_id):
        while True:
            try:
                goal_details = self.goal_service.get_goal_details(goal_id)
                print("\n--- Goal Details ---"); print(json.dumps(goal_details, indent=2, default=str)); print("--------------------\n")
                choice = questionary.select(f"What do you want to do with '{goal_details['name']}'?",
                    choices=["Add a Step", "Mark a Step as Completed", "Edit Goal", "Mark Goal as Completed", "Back to Goals Menu"]).ask()
                if choice == "Add a Step":
                    desc = questionary.text("Enter step description:").ask()
                    if desc: self.step_service.add_step_to_goal(goal_id, desc)
                elif choice == "Mark a Step as Completed":
                    steps = goal_details.get('steps', []); pending_steps = [s for s in steps if s['status'] == 'Pending']
                    if not pending_steps: print("No pending steps to complete."); continue
                    step_to_complete = questionary.select("Which step do you want to complete?", choices=[f"{s['step_id']}: {s['description']}" for s in pending_steps]).ask()
                    if step_to_complete:
                        step_id = int(step_to_complete.split(':')[0])
                        self.step_service.mark_step_as_completed(step_id)
                elif choice == "Edit Goal": self._handle_edit_goal(goal_id)
                elif choice == "Mark Goal as Completed":
                    if questionary.confirm(f"Are you sure you want to complete this goal?").ask():
                        self.goal_service.mark_goal_as_complete(goal_id); print("✅ Goal marked as completed!"); break
                elif choice == "Back to Goals Menu" or choice is None: break
            except (StepError, GoalError) as e:
                print(f"❌ Error: {e}")
                
    # --- Utility function to select an account ---
    def _select_account(self, prompt_message):
        accounts = self.account_service.list_accounts()
        if not accounts:
            print("❌ Error: No accounts found. Please create an account first.")
            return None
        account_choice = questionary.select(prompt_message,
            choices=[f"{acc['account_id']}: {acc['name']} (Balance: {acc['balance']})" for acc in accounts]).ask()
        if not account_choice: return None
        return int(account_choice.split(':')[0])

    # --- Handler Functions ---
    def _handle_create_account(self):
        name = questionary.text("Enter account name (e.g., Savings Account):").ask()
        if not name: return
        balance_str = questionary.text("Enter initial balance (e.g., 200000):").ask()
        balance = float(balance_str) if balance_str else 0.0
        try:
            acc = self.account_service.create_account(name, balance)
            print("✅ Account created successfully:"); print(json.dumps(acc, indent=2, default=str))
        except Exception as e: print(f"❌ Error: {e}")

    def _handle_list_accounts(self):
        accounts = self.account_service.list_accounts()
        print("\n--- All Accounts ---"); print(json.dumps(accounts, indent=2, default=str)); print("--------------------\n")

    def _handle_add_debt(self):
        name = questionary.text("Enter debt name (e.g., Laptop Loan):").ask()
        if not name: return
        amount_str = questionary.text("Enter total loan amount:").ask()
        emi_str = questionary.text("Enter monthly EMI (optional):").ask()
        try:
            debt = self.debt_service.add_debt(name, float(amount_str) if amount_str else 0.0, float(emi_str) if emi_str else None)
            print("✅ Debt added successfully:"); print(json.dumps(debt, indent=2, default=str))
        except Exception as e: print(f"❌ Error: {e}")

    def _handle_list_debts(self):
        debts = self.debt_service.list_debts()
        print("\n--- All Debts ---"); print(json.dumps(debts, indent=2, default=str)); print("-----------------\n")
    
    def _handle_edit_debt(self):
        debts = self.debt_service.list_debts()
        if not debts: print("No debts found to edit."); return
        debt_choice = questionary.select("Which debt do you want to edit?", choices=[f"{d['debt_id']}: {d['name']}" for d in debts]).ask()
        if not debt_choice: return
        debt_id = int(debt_choice.split(':')[0])
        current_debt = self.debt_service.debt_dao.get_debt_by_id(debt_id)
        print("Leave a field blank to keep its current value.")
        new_name = questionary.text("Enter new name:", default=current_debt['name']).ask()
        new_total_str = questionary.text("Enter new total amount:", default=str(current_debt['total_amount'])).ask()
        new_emi_str = questionary.text("Enter new monthly EMI:", default=str(current_debt.get('monthly_emi') or '')).ask()
        try:
            updated_debt = self.debt_service.update_debt_details(
                debt_id=debt_id, name=new_name,
                total_amount=float(new_total_str) if new_total_str else None,
                monthly_emi=float(new_emi_str) if new_emi_str else None
            )
            print("✅ Debt updated successfully:"); print(json.dumps(updated_debt, indent=2, default=str))
        except (DebtError, Exception) as e: print(f"❌ Error: {e}")

    def _handle_make_debt_payment(self):
        debts = self.debt_service.list_debts()
        if not debts: print("No debts found to make a payment on."); return
        debt_choice = questionary.select("Which debt are you paying?",
            choices=[f"{d['debt_id']}: {d['name']} (Remaining: {d['remaining_amount']})" for d in debts]).ask()
        if not debt_choice: return
        debt_id = int(debt_choice.split(':')[0])
        account_id = self._select_account("Which account are you paying FROM?")
        if not account_id: return
        amount_str = questionary.text("Enter payment amount:").ask()
        if not amount_str: return
        try:
            amount = float(amount_str)
            updated_debt = self.debt_service.make_manual_payment(debt_id, account_id, amount)
            print("✅ Payment successful! Debt updated:"); print(json.dumps(updated_debt, indent=2, default=str))
        except (DebtError, TransactionError, Exception) as e: print(f"❌ Error: {e}")

    def _handle_create_goal(self):
        name = questionary.text("What is the name of your goal?").ask()
        if not name: return
        budget_str = questionary.text("What is the budget? (optional)").ask()
        budget = float(budget_str) if budget_str else None
        try:
            goal = self.goal_service.create_new_goal(name, budget)
            print("✅ Goal created successfully:"); print(json.dumps(goal, indent=2, default=str))
        except GoalError as e: print(f"❌ Error: {e}")

    def _handle_list_goals(self):
        goals = self.goal_service.list_all_goals()
        print("\n--- All Goals ---"); print(json.dumps(goals, indent=2, default=str)); print("-----------------\n")

    def _handle_manage_specific_goal(self):
        goals = self.goal_service.list_all_goals()
        if not goals: print("No goals found. Please create one first."); return
        goal_choice = questionary.select("Which goal do you want to manage?",
            choices=[f"{g['goal_id']}: {g['name']}" for g in goals]).ask()
        if goal_choice:
            goal_id = int(goal_choice.split(':')[0])
            self._specific_goal_menu(goal_id)
            
    def _handle_edit_goal(self, goal_id: int):
        print("Leave a field blank to keep its current value.")
        current_goal = self.goal_service.get_goal_details(goal_id)
        new_name = questionary.text("Enter new goal name:", default=current_goal['name']).ask()
        new_budget_str = questionary.text("Enter new budget:", default=str(current_goal['budget'])).ask()
        new_name = new_name if new_name else None
        new_budget = float(new_budget_str) if new_budget_str else None
        try:
            updated_goal = self.goal_service.update_goal_details(goal_id, new_name, new_budget)
            print("✅ Goal updated successfully:"); print(json.dumps(updated_goal, indent=2, default=str))
        except GoalError as e: print(f"❌ Error: {e}")

    def _handle_add_expense(self):
        account_id = self._select_account("Which account to use for this expense?")
        if not account_id: return
        categories = ["Food", "Transport", "Rent", "Utilities", "Entertainment", "Shopping", "EMI", "Other (create new)"]
        amount_str = questionary.text("Enter expense amount:").ask()
        if not amount_str: return
        category_choice = questionary.select("Select a category:", choices=categories).ask()
        if not category_choice: return
        if category_choice == "Other (create new)":
            category_name = questionary.text("Enter the new category name:").ask()
            if not category_name: return
        else: category_name = category_choice
        desc = questionary.text("Enter description (optional):").ask()
        try:
            trx = self.transaction_service.add_expense(float(amount_str), category_name, account_id, desc)
            print("✅ Expense added successfully:"); print(json.dumps(trx, indent=2, default=str))
        except TransactionError as e: print(f"❌ Error: {e}")

    def _handle_add_income(self):
        account_id = self._select_account("Which account will this income go into?")
        if not account_id: return
        amount_str = questionary.text("Enter income amount:").ask()
        if not amount_str: return
        desc = questionary.text("Enter description (optional):").ask()
        try:
            trx = self.transaction_service.add_income(float(amount_str), account_id, desc)
            print("✅ Income added successfully:"); print(json.dumps(trx, indent=2, default=str))
        except TransactionError as e: print(f"❌ Error: {e}")

    def _handle_allocate_to_goal(self):
        account_id = self._select_account("Which account are you allocating savings FROM?")
        if not account_id: return
        goals = self.goal_service.list_all_goals()
        if not goals: print("No goals found to allocate to."); return
        goal_choice = questionary.select("Which goal do you want to allocate savings TO?", choices=[f"{g['goal_id']}: {g['name']}" for g in goals]).ask()
        if not goal_choice: return
        goal_id = int(goal_choice.split(':')[0])
        amount_str = questionary.text(f"Enter amount to allocate from your account to '{goal_choice.split(': ')[1]}':").ask()
        desc = questionary.text("Enter description (optional):").ask()
        try:
            trx = self.transaction_service.allocate_to_goal(goal_id, float(amount_str), account_id, desc)
            print("✅ Amount allocated successfully:"); print(json.dumps(trx, indent=2, default=str))
        except TransactionError as e: print(f"❌ Error: {e}")
            
    def _handle_setup_recurring_transaction(self):
        account_id = self._select_account("Which account is this transaction for?")
        if not account_id: return
        ttype = questionary.select("Is this recurring income or expense?", choices=["Income", "Expense"]).ask()
        if not ttype: return
        amount = float(questionary.text("Enter the monthly amount:").ask())
        desc = questionary.text("Enter a description (e.g., Monthly Salary, Rent EMI):").ask()
        start_date = questionary.text("Enter the first payment date (YYYY-MM-DD):").ask()
        debt_id = None
        if ttype == 'Expense' and questionary.confirm("Is this an EMI for a specific debt?").ask():
            debts = self.debt_service.list_debts()
            if debts:
                debt_choice = questionary.select("Which debt is this EMI for?", 
                    choices=[f"{d['debt_id']}: {d['name']}" for d in debts]).ask()
                if debt_choice: debt_id = int(debt_choice.split(':')[0])
            else: print("No debts found to link this to.")
        try:
            recurring_dao = self.recurring_service.recurring_dao
            recurring_dao.create_recurring_transaction(
                account_id=account_id, description=desc, amount=amount, type=ttype, 
                frequency='monthly', start_date=start_date, next_due_date=start_date, debt_id=debt_id
            )
            print("✅ Recurring transaction set up successfully!")
        except Exception as e: print(f"❌ Error setting up recurring transaction: {e}")

    def _handle_spending_report(self):
        month_str = questionary.text("Enter the month for the report (e.g., YYYY-MM):",
            validate=lambda text: True if len(text) == 7 and text[4] == '-' else "Please use YYYY-MM format.").ask()
        if not month_str: return
        try:
            year = int(month_str[:4]); month = int(month_str[5:])
            _, last_day = calendar.monthrange(year, month)
            start_date = f"{year}-{month:02d}-01"; end_date = f"{year}-{month:02d}-{last_day}"
            report = self.reporting_service.generate_spending_summary(start_date, end_date)
            print("\n--- Monthly Spending Summary ---"); print(json.dumps(report, indent=2, default=str)); print("--------------------------------\n")
        except Exception as e: print(f"❌ Error generating report: {e}")

def main():
    cli = GoalManagerCLI()
    cli.run()

if __name__ == "__main__":
    main()