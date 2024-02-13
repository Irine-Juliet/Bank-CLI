from decimal import Decimal
from datetime import datetime, timedelta
from transaction import Transaction

class Account:
    """
    A base class for different types of bank accounts.
    Attributes:
        account_number (int): Unique identifier for the account.
        balance (Decimal): The current balance of the account.
        transactions (list): A list of transactions associated with the account.
    """
    account_number_counter = 1

    def __init__(self):
        """
        Initializes a new Account instance with a unique account number, zero balance, and an empty list of transactions.
        """
        self.account_number = Account.account_number_counter
        Account.account_number_counter += 1
        self.balance = Decimal('0.00')
        self.transactions = []
    
    def add_transaction(self, amount, transaction_date, bypass_limits=False, is_interest=False):
        """
        Adds a new transaction to the account.
        Parameters:
            amount (Decimal): The amount of the transaction. A negative value indicates a withdrawal.
            transaction_date (str or datetime.date): The date of the transaction.
            bypass_limits (bool): If True, transaction limits/overdraft restriction are ignored.
            is_interest (bool): If True, marks the transaction as an interest transaction.
        Returns:
            bool: True if the transaction was successfully added, False otherwise.
        """
        if not bypass_limits:
            # For SavingsAccount, check transaction limits
            if isinstance(self, Savings) and not self.can_add_transaction(amount, transaction_date):
                return False
            # Check for overdraft
            if self.balance + Decimal(amount) < Decimal('0.00'):
                return False
        # Add the transaction
        self.transactions.append(Transaction(Decimal(amount), transaction_date, is_interest=is_interest))
        self.balance += Decimal(amount)
        return True

    def get_last_transaction_date(self):
        """
        Determines the last transaction date of the month based on existing transactions.
        Returns:
            datetime.date: The last day of the month for the latest transaction.
        """
        last_date = max(t.date for t in self.transactions)
        # Find the last day of the month
        next_month = last_date.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)
        
    #def get_details(self):
        #"""
        #Retrieves the details of the account.
        #Returns:
        #tuple: A tuple containing the account number, balance, and a list of transactions.
        #"""
        #return self.account_number, self.balance, self.transactions

class Savings(Account):
    """
    Represents a savings account, inheriting from Account.
    Savings accounts have transaction limits.
    """

    def can_add_transaction(self, amount, transaction_date):
        """
        Checks if a new transaction can be added to the account without exceeding transaction limits.
        Parameters:
            amount (Decimal): The amount of the proposed transaction.
            transaction_date (str or datetime.date): The date of the proposed transaction.
        Returns:
            bool: True if the transaction can be added, False otherwise.
        """
        # Convert input date to datetime.date for comparison
        transaction_date = datetime.strptime(transaction_date, "%Y-%m-%d").date()
        # Count transactions on the same day and in the same month
        same_day_transactions = sum(1 for t in self.transactions if t.date == transaction_date and not t.is_interest)
        same_month_transactions = sum(1 for t in self.transactions if t.date.month == transaction_date.month and t.date.year == transaction_date.year and not t.is_interest)
        # Check transaction limits
        if same_day_transactions >= 2 or same_month_transactions >= 5:
            return False
        return True

    def apply_interest_and_fees(self):
        """
        Applies interest to the account balance and bypasses transaction limits.
        """
        interest_rate = Decimal('0.0041')
        interest = self.balance * interest_rate
        self.add_transaction(interest, self.get_last_transaction_date(), bypass_limits=True, is_interest=True)

class Checking(Account):
    """
    Represents a checking account, inheriting from Account.
    Checking accounts may incur a fee if the balance is below a certain threshold.
    """
    def apply_interest_and_fees(self):
        """
        Applies interest to the account balance and charges a fee if the balance is below the threshold.
        """
        interest_rate = Decimal('0.0008')
        interest = self.balance * interest_rate
        self.add_transaction(interest, self.get_last_transaction_date(), bypass_limits=True)

        fee_threshold = Decimal('100.00')
        fee = Decimal('5.44')
        if self.balance < fee_threshold:
            self.add_transaction(-fee, self.get_last_transaction_date(), bypass_limits=True)