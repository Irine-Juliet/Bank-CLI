from base import Base
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy.orm import  mapped_column
from sqlalchemy import Integer, Numeric, Date, Boolean, ForeignKey

class Transaction(Base):
    """
    Represents a financial transaction in a bank account.
    Attributes:
        amount (Decimal): A positive value represents a deposit, and a negative value represents a withdrawal.
        date (datetime.date): The date when the transaction occurred.
        is_interest (bool): Flag indicating whether the transaction is an interest payment.
    """

    __tablename__ = 'transactions'

    _id = mapped_column(Integer, primary_key=True, autoincrement=True)
    _amount = mapped_column(Numeric(10, 2), nullable=False)
    _date = mapped_column(Date, nullable=False)
    _is_interest = mapped_column(Boolean, default=False, nullable=False)
    _account_number = mapped_column(Integer, ForeignKey('accounts._account_number'))

    def __init__(self, amount, transaction_date, _account_number, is_interest=False):
        """
        Initializes a new Transaction instance.
        Parameters:
            amount (Decimal): The amount of money involved in the transaction.
            transaction_date (str or datetime.date, optional): The date of the transaction.
            is_interest (bool, optional): Specifies if the transaction is an interest payment. Defaults to False.
        """
        self._amount = Decimal(amount)
        if isinstance(transaction_date, str):
            # Parse string to datetime.date object
            self._date= datetime.strptime(transaction_date, "%Y-%m-%d").date()
        elif isinstance(transaction_date, date):
            # If it's already a date, just use it 
            self._date= transaction_date
        self._is_interest = is_interest
        self._account_number = _account_number 
