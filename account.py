import logging
from base import Base
from decimal import Decimal
from datetime import timedelta
from transaction import Transaction
from sqlalchemy.orm import relationship, backref, mapped_column
from sqlalchemy import Integer, String, ForeignKey, Numeric, func
from exceptions import OverdrawError, TransactionSequenceError, TransactionLimitError

class Account(Base):
    """
    A base class for different types of bank accounts.
    Attributes:
        account_number (int): Unique identifier for the account.
        balance (Decimal): The current balance of the account.
        transactions (list): A list of transactions associated with the account.
    """
    __tablename__ = 'accounts'

    _account_number = mapped_column(Integer, primary_key=True, autoincrement=False)
    _balance = mapped_column(Numeric(10, 2), default=Decimal('0.00'))
    _account_type = mapped_column(String)
    _transactions = relationship("Transaction", backref=backref("account"))
    _bank_id = mapped_column(Integer, ForeignKey('bank._id'))

    __mapper_args__ = {
        'polymorphic_identity':'account',
        'polymorphic_on':_account_type
    }

    def __init__(self, account_number, balance=Decimal('0.00')):
        """
        Initializes a new Account instance with a unique account number, zero balance, and an empty list of transactions.
        """
        self._account_number = account_number
        self._balance = balance
    
    def add_transaction(self, amount, session, transaction_date, bypass_limits=False, is_interest=False):
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
        latest_transaction = session.query(Transaction).filter(Transaction._account_number == self._account_number).order_by(Transaction._date.desc()).first()
        if latest_transaction and transaction_date < latest_transaction._date:
            raise TransactionSequenceError(latest_transaction._date)
        
        if not bypass_limits:
            # For SavingsAccount, check transaction limits
            if isinstance(self, Savings) and not self._can_add_transaction(amount, session, transaction_date):
                return False
            # Check for overdraft
            if self._balance + Decimal(amount) < Decimal('0.00'):
                raise OverdrawError("This transaction could not be completed due to an insufficient account balance.")
            
        # Add the transaction
        new_transaction = Transaction(amount=Decimal(amount), transaction_date=transaction_date, _account_number=self._account_number, is_interest=is_interest)
        session.add(new_transaction)
        # Update balance
        self._balance += amount
        return True

    def _get_last_transaction_date(self, session):
        """
        Determines the last transaction date of the month based on existing transactions.
        Returns:
            datetime.date: The last day of the month for the latest transaction.
        """
        latest_transaction_date = session.query(func.max(Transaction._date)).filter(Transaction._account_number == self._account_number).scalar()
        if latest_transaction_date is None:
            # No transactions found, return None 
            return None
        next_month = latest_transaction_date.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)
        
    def _can_apply_interest(self,session):
       # Query the date of the latest non-interest transaction
       last_user_transaction_date = session.query(func.max(Transaction._date))\
            .filter(Transaction._account_number == self._account_number, Transaction._is_interest == False)\
            .scalar()

        # If there are no non-interest transactions, interest can be applied
       if not last_user_transaction_date:
        return True
       # Query the date of the latest interest transaction
       last_interest_application_date = session.query(func.max(Transaction._date))\
            .filter(Transaction._account_number == self._account_number, Transaction._is_interest == True)\
            .scalar()

        # If there are no interest transactions yet, interest can be applied
       if not last_interest_application_date:
           return True
       # Check if the last non-interest transaction and the last interest application are in the same month and year
       if (last_user_transaction_date.month == last_interest_application_date.month and 
           last_user_transaction_date.year == last_interest_application_date.year):
           return False  # Interest was already applied in the same month of the last transaction

       return True

class Savings(Account):
    """
    Represents a savings account, inheriting from Account.
    Savings accounts have transaction limits.
    """
    __mapper_args__ = {
        'polymorphic_identity':'savings',
    }

    def _can_add_transaction(self, amount, session, transaction_date):
        """
        Checks if a new transaction can be added to the account without exceeding transaction limits.
        Parameters:
            amount (Decimal): The amount of the proposed transaction.
            transaction_date (str or datetime.date): The date of the proposed transaction.
        Returns:
            bool: True if the transaction can be added, False otherwise.
        """
        same_day_transactions = session.query(func.count(Transaction._id)).filter(Transaction._account_number == self._account_number,
                                                                          func.date(Transaction._date) == transaction_date,
                                                                          Transaction._is_interest == False ).scalar()
        same_month_transactions = session.query(func.count(Transaction._id)).filter(Transaction._account_number == self._account_number,
                                                                            func.extract('month', Transaction._date) == transaction_date.month,
                                                                            func.extract('year', Transaction._date) == transaction_date.year,
                                                                            Transaction._is_interest == False).scalar()
        if same_day_transactions >= 2:
            raise TransactionLimitError('daily')
        if same_month_transactions >= 5:
            raise TransactionLimitError('monthly')
        return True

    def apply_interest_and_fees(self, session):
        """
        Applies interest to the account balance and bypasses transaction limits.
        """
        if not self._can_apply_interest(session):
            last_interest_date = self._get_last_transaction_date(session)
            raise TransactionSequenceError(last_interest_date, "Cannot apply interest and fees again in the month of {}.")
        
        interest_rate = Decimal('0.0041')
        interest = self._balance * interest_rate
        self.add_transaction(interest, session,  self._get_last_transaction_date(session), bypass_limits=True, is_interest=True)
        logging.debug("Triggered interest and fees")

class Checking(Account):
    """
    Represents a checking account, inheriting from Account.
    Checking accounts may incur a fee if the balance is below a certain threshold.
    """
    __mapper_args__ = {
        'polymorphic_identity':'checking',
    }

    def apply_interest_and_fees(self, session):
        """
        Applies interest to the account balance and charges a fee if the balance is below the threshold.
        """
        
        if not self._can_apply_interest(session):
            last_interest_date = self._get_last_transaction_date(session)
            raise TransactionSequenceError(last_interest_date, "Cannot apply interest and fees again in the month of {}.")

        interest_rate = Decimal('0.0008')
        interest = self._balance * interest_rate
        self.add_transaction(interest, session, self._get_last_transaction_date(session), bypass_limits=True, is_interest=True)
        logging.debug("Triggered interest and fees")

        fee_threshold = Decimal('100.00')
        fee = Decimal('5.44')
        if self._balance < fee_threshold:
            self.add_transaction(-fee, session, self._get_last_transaction_date(session), bypass_limits=True, is_interest=True)

