from datetime import datetime, date
from decimal import Decimal

class Transaction:
    """
    Represents a financial transaction in a bank account.
    Attributes:
        amount (Decimal): A positive value represents a deposit, and a negative value represents a withdrawal.
        date (datetime.date): The date when the transaction occurred.
        is_interest (bool): Flag indicating whether the transaction is an interest payment.
    """
    def __init__(self, amount, transaction_date, is_interest=False):
        """
        Initializes a new Transaction instance.
        Parameters:
            amount (Decimal): The amount of money involved in the transaction.
            transaction_date (str or datetime.date, optional): The date of the transaction.
            is_interest (bool, optional): Specifies if the transaction is an interest payment. Defaults to False.
        """
        self.amount = Decimal(amount)
        if isinstance(transaction_date, str):
            # Parse string to datetime.date object
            self.date = datetime.strptime(transaction_date, "%Y-%m-%d").date()
        elif isinstance(transaction_date, date):
            # If it's already a date, just use it 
            self.date = transaction_date
        self.is_interest = is_interest
