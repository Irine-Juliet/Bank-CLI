import logging
from base import Base
from decimal import Decimal
from sqlalchemy import Integer
from account import Account, Checking, Savings
from sqlalchemy.orm import relationship, backref, mapped_column

SAVINGS = "savings"
CHECKING = "checking"

class Bank(Base):
    """
    A class representing a bank that manages multiple accounts.
    Attributes:
        accounts (dict): A dictionary mapping account numbers to account objects.
    """
    __tablename__ = "bank"
    _id = mapped_column(Integer, primary_key=True)
    _accounts = relationship("Account", backref=backref("bank"))

    def open_account(self, account_type, session):
        """
        Opens a new account of the specified type.
        Parameters:
            account_type (str): The type of account to open, either 'checking' or 'savings'.
        Returns:
            Account: The newly created account object.
        """
        last_account = session.query(Account).order_by(Account._account_number.desc()).first()
        new_account_number = last_account._account_number + 1 if last_account else 1

        if account_type == CHECKING:
            account = Checking(new_account_number)
        elif account_type == SAVINGS :
            account = Savings(new_account_number)

        account._account_number = new_account_number

        session.add(account)
        logging.debug(f"Created account: {account._account_number}")
        return account

    def summary(self, session):
        """
        Prints a summary of all accounts in the bank.
        """
        accounts = session.query(Account).all()
        for account in accounts: 
            account_type = type(account).__name__
            account_number = str(account._account_number).zfill(9)
            balance = account._balance.quantize(Decimal('0.01'))
            print(f"{account_type}#{account_number},\tbalance: ${balance:,.2f}")

    def get_account_info(self):
        # If accounts are stored in a dict
        return [(account_number, account) for account_number, account in self._accounts.items()]

    def select_account(self, account_number, session):
        """
        Selects and returns an account based on the account number.
        Parameters:
            account_number (int): The account number to select.
        Returns:
            Account: The account object with the specified account number.
        """
        account = session.query(Account).filter_by(_account_number=account_number).first()
        return account

    def list_transactions(self, account_number, session):
        """
        Retrieves and returns a sorted list of transactions for a specified account.
        Parameters:
            account_number (int): The account number whose transactions are to be retrieved.
        Returns:
            list[Transaction]: A list of transaction objects sorted by date.
        """
        account = session.query(Account).filter_by(_account_number=account_number).first()
        # Sort transactions by date
        if account:
            sorted_transactions = sorted(account._transactions, key=lambda x: x._date)
        return sorted_transactions
