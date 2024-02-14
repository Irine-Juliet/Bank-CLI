
class OverdrawError(Exception):
    """Exception raised for attempts to overdraw an account."""
    pass

class TransactionSequenceError(Exception):
    """Exception raised for adding transactions out of chronological order."""
    def __init__(self, latest_date, message=None):
        if not message:
            message = "New transactions must be from {} onward.".format(latest_date.strftime("%Y-%m-%d"))
        else:
            message = message.format(latest_date.strftime("%B"))
        super().__init__(message)
        self.latest_date = latest_date
class TransactionLimitError(Exception):
    """Exception raised for exceeding transaction limits."""
    def __init__(self, limit_type):
        if limit_type == 'daily':
            self.message = "This transaction could not be completed because this account already has 2 transactions in this day."
        elif limit_type == 'monthly':
            self.message = "This transaction could not be completed because this account already has 5 transactions in this month."
        else:
            self.message = "Transaction limit exceeded."
        super().__init__(self.message)