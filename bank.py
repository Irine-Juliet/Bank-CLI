from decimal import Decimal
from account import Account, Checking, Savings

class Bank:
    """
    A class representing a bank that manages multiple accounts.
    Attributes:
        accounts (dict): A dictionary mapping account numbers to account objects.
    """
    def __init__(self):
        """
        Initializes a new Bank instance with an empty accounts dictionary.
        """
        self.accounts = {} 

    def open_account(self, account_type):
        """
        Opens a new account of the specified type.
        Parameters:
            account_type (str): The type of account to open, either 'checking' or 'savings'.
        Returns:
            Account: The newly created account object.
        """
        if account_type == "checking":
            account = Checking()
        elif account_type == "savings":
            account = Savings()
        self.accounts[account.account_number] = account
        return account

    def summary(self):
        """
        Prints a summary of all accounts in the bank.
        """
        for account in self.accounts.values():
            account_type = type(account).__name__
            account_number = str(account.account_number).zfill(9)
            balance = account.balance.quantize(Decimal('0.01'))
            print(f"{account_type}#{account_number},\tbalance: ${balance:,.2f}")

    def select_account(self, account_number):
        """
        Selects and returns an account based on the account number.
        Parameters:
            account_number (int): The account number to select.
        Returns:
            Account: The account object with the specified account number.
        """
        return self.accounts.get(account_number)

    def list_transactions(self, account_number):
        """
        Retrieves and returns a sorted list of transactions for a specified account.
        Parameters:
            account_number (int): The account number whose transactions are to be retrieved.
        Returns:
            list[Transaction]: A list of transaction objects sorted by date.
        """
        account = self.accounts.get(account_number)
        # Sort transactions by date
        sorted_transactions = sorted(account.transactions, key=lambda x: x.date)
        return sorted_transactions
