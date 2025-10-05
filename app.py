# app.py
import streamlit as st
from datetime import date

# Import all DAO and Service classes from your project
from src.config import config
from src.dao.goal_dao import GoalDAO
from src.dao.step_dao import StepDAO
from src.dao.transaction_dao import TransactionDAO
from src.dao.category_dao import CategoryDAO
from src.dao.account_dao import AccountDAO
from src.dao.debt_dao import DebtDAO
from src.dao.recurring_transaction_dao import RecurringTransactionDAO
from src.services.goal_service import GoalService
from src.services.step_service import StepService
from src.services.transaction_service import TransactionService
from src.services.account_service import AccountService
from src.services.debt_service import DebtService
from src.services.recurring_transaction_service import RecurringTransactionService
from src.services.reporting_service import ReportingService

# --- INITIALIZATION ---
@st.cache_resource
def initialize_services():
    """Initializes all DAOs and Services."""
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
    account_service = AccountService(account_dao)
    transaction_service = TransactionService(transaction_dao, goal_dao, category_dao, account_dao)
    debt_service = DebtService(debt_dao, account_dao, transaction_service)
    step_service = StepService(step_dao, goal_dao)
    goal_service = GoalService(goal_dao, step_dao, transaction_dao)
    reporting_service = ReportingService(transaction_dao, category_dao)
    recurring_service = RecurringTransactionService(recurring_dao, transaction_service, debt_service)
    
    # Process recurring transactions on startup
    recurring_service.process_due_transactions()
    
    return account_service, debt_service, goal_service, step_service, transaction_service, reporting_service

# Load all our services
account_service, debt_service, goal_service, step_service, transaction_service, reporting_service = initialize_services()

st.set_page_config(layout="wide")
st.title("🎯 Personal Finance & Goal Manager")

# --- UI NAVIGATION ---
menu = ["Dashboard", "Manage Goals", "Manage Finances", "Manage Accounts", "Manage Debts", "Reports"]
choice = st.sidebar.selectbox("Menu", menu)


# --- UI PAGES ---

if choice == "Dashboard":
    st.subheader("Dashboard")
    col1, col2, col3 = st.columns(3)
    
    accounts = account_service.list_accounts()
    total_balance = sum(acc['balance'] for acc in accounts)
    col1.metric("Total Account Balance", f"₹{total_balance:,.2f}")

    debts = debt_service.list_debts()
    total_debt = sum(d['remaining_amount'] for d in debts)
    col2.metric("Total Remaining Debt", f"₹{total_debt:,.2f}")

    goals = goal_service.list_all_goals()
    active_goals = [g for g in goals if g['status'] == 'Active']
    col3.metric("Active Goals", len(active_goals))
    
    st.write("---")
    st.write("### Active Goals Overview")
    for goal in active_goals:
        with st.expander(f"{goal['name']} (Budget: ₹{goal.get('budget', 0):,.2f})"):
            details = goal_service.get_goal_details(goal['goal_id'])
            summary = details.get('financial_summary', {})
            
            # UPDATED LOGIC: Convert string percentage to float for progress bar
            progress_str = summary.get('progress_percentage', '0.0%')
            progress_float = float(progress_str.strip('%'))
            st.progress(progress_float / 100.0)
            
            st.write(f"**Saved:** ₹{summary.get('amount_saved', 0):,.2f} / **Budget:** ₹{summary.get('budget', 0):,.2f}")

elif choice == "Manage Goals":
    st.subheader("Manage Goals")

    with st.form("create_goal_form", clear_on_submit=True):
        st.write("### Create a New Goal")
        goal_name = st.text_input("Goal Name")
        goal_budget = st.number_input("Budget (₹)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Create Goal")
        if submitted and goal_name:
            goal_service.create_new_goal(goal_name, goal_budget)
            st.success(f"Goal '{goal_name}' created!")
            st.rerun()

    st.write("---")
    st.write("### All Goals")
    all_goals = goal_service.list_all_goals()
    if not all_goals:
        st.info("No goals found. Create one above!")
    else:
        for goal in all_goals:
            with st.expander(f"**{goal['name']}** - Status: {goal['status']}"):
                details = goal_service.get_goal_details(goal['goal_id'])
                summary = details.get('financial_summary', {})
                
                # Display financial summary
                st.write(f"**Budget:** ₹{summary.get('budget', 0):,.2f}")
                st.write(f"**Amount Saved:** ₹{summary.get('amount_saved', 0):,.2f}")
                st.write(f"**Progress:** {summary.get('progress_percentage', '0.00%')}")

                # UPDATED LOGIC: Convert string percentage to float for progress bar
                progress_str = summary.get('progress_percentage', '0.0%')
                progress_float = float(progress_str.strip('%'))
                st.progress(progress_float / 100.0)
                
                # Display steps
                st.write("**Steps:**")
                for step in details.get('steps', []):
                    st.checkbox(step['description'], value=(step['status']=='Completed'), key=f"step_{step['step_id']}")
                
                # Add a step
                with st.form(f"add_step_{goal['goal_id']}", clear_on_submit=True):
                    new_step_desc = st.text_input("New Step Description")
                    if st.form_submit_button("Add Step"):
                        if new_step_desc:
                            step_service.add_step_to_goal(goal['goal_id'], new_step_desc)
                            st.rerun()

elif choice == "Manage Finances":
    st.subheader("Manage Finances")
    
    accounts = account_service.list_accounts()
    account_choices = {f"{acc['account_id']}: {acc['name']}": acc['account_id'] for acc in accounts}

    goals = goal_service.list_all_goals()
    goal_choices = {f"{g['goal_id']}: {g['name']}": g['goal_id'] for g in goals if g.get('status')=='Active'}
    
    tab1, tab2, tab3 = st.tabs(["Add Expense", "Add Income", "Allocate to Goal"])
    
    with tab1:
        with st.form("add_expense", clear_on_submit=True):
            st.write("### Log a New Expense")
            if not account_choices:
                st.warning("Please create an account first in 'Manage Accounts'.")
            else:
                acc_choice = st.selectbox("From Account", options=account_choices.keys())
                category = st.text_input("Category (e.g., Food, Transport)")
                amount = st.number_input("Amount (₹)", min_value=0.01, format="%.2f")
                desc = st.text_input("Description (Optional)")
                if st.form_submit_button("Add Expense"):
                    transaction_service.add_expense(amount, category, account_choices[acc_choice], desc)
                    st.success("Expense added!")
                    st.rerun()
    
    with tab2:
        with st.form("add_income", clear_on_submit=True):
            st.write("### Log New Income")
            if not account_choices:
                st.warning("Please create an account first in 'Manage Accounts'.")
            else:
                acc_choice = st.selectbox("To Account", options=account_choices.keys())
                amount = st.number_input("Amount (₹)", min_value=0.01, format="%.2f")
                desc = st.text_input("Description (Optional)")
                if st.form_submit_button("Add Income"):
                    transaction_service.add_income(amount, account_choices[acc_choice], desc)
                    st.success("Income added!")
                    st.rerun()

    with tab3:
        with st.form("allocate_goal", clear_on_submit=True):
            st.write("### Allocate Savings to a Goal")
            if not account_choices or not goal_choices:
                st.warning("Please create at least one account and one active goal first.")
            else:
                acc_choice = st.selectbox("From Account", options=account_choices.keys())
                goal_choice = st.selectbox("To Goal", options=goal_choices.keys())
                amount = st.number_input("Amount to Allocate (₹)", min_value=0.01, format="%.2f")
                desc = st.text_input("Description (Optional)")
                if st.form_submit_button("Allocate"):
                    transaction_service.allocate_to_goal(goal_choices[goal_choice], amount, account_choices[acc_choice], desc)
                    st.success("Allocation successful!")
                    st.rerun()

elif choice == "Manage Accounts":
    st.subheader("Manage Accounts")
    with st.form("create_account", clear_on_submit=True):
        st.write("### Create New Account")
        acc_name = st.text_input("Account Name (e.g., Savings Bank)")
        initial_balance = st.number_input("Initial Balance (₹)", min_value=0.0, format="%.2f")
        if st.form_submit_button("Create Account"):
            account_service.create_account(acc_name, initial_balance)
            st.success(f"Account '{acc_name}' created.")
            st.rerun()
    
    st.write("---")
    st.write("### Your Accounts")
    accounts_data = account_service.list_accounts()
    st.dataframe(accounts_data)

elif choice == "Manage Debts":
    st.subheader("Manage Debts")
    with st.form("create_debt", clear_on_submit=True):
        st.write("### Add New Debt")
        debt_name = st.text_input("Debt Name (e.g., Laptop Loan)")
        total_amount = st.number_input("Total Amount (₹)", min_value=0.0, format="%.2f")
        emi = st.number_input("Monthly EMI (Optional, ₹)", min_value=0.0, format="%.2f")
        if st.form_submit_button("Add Debt"):
            debt_service.add_debt(debt_name, total_amount, emi if emi > 0 else None)
            st.success(f"Debt '{debt_name}' added.")
            st.rerun()
            
    st.write("---")
    st.write("### Your Debts")
    debts_data = debt_service.list_debts()
    st.dataframe(debts_data)
    
elif choice == "Reports":
    st.subheader("Reports")
    st.write("### Monthly Spending Summary")
    
    today = date.today()
    month_str = st.text_input("Enter Month (YYYY-MM)", value=today.strftime("%Y-%m"))
    
    if st.button("Generate Report"):
        if len(month_str) == 7 and month_str[4] == '-':
            start_date = f"{month_str}-01"
            end_date = f"{month_str}-31" # A simple approximation
            report = reporting_service.generate_spending_summary(start_date, end_date)
            st.write(f"Spending for {month_str}:")
            st.dataframe(report.get('summary', []))
        else:
            st.error("Please use YYYY-MM format.")