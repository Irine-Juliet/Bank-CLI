import sys
import pickle
from decimal import Decimal
from bank import Bank
from account import Account, Checking, Savings

class BankCLI:
    """
    A command-line interface (CLI) for interacting with a Bank instance.
    Attributes:
        bank (Bank): The Bank instance with which this CLI interacts.
        current_account (Account): The account currently selected in the CLI.
        choices (dict): A dictionary mapping menu options to their corresponding methods.
    """

    def __init__(self):
        """
        Initializes a new BankCLI instance.
        """
        self.bank = Bank()
        self.current_account = None
        self._choices = {
            "1": self._open_account,
            "2": self._summary,
            "3": self._select_account,
            "4": self._add_transaction,
            "5": self._list_transactions,
            "6": self._interest_and_fees,
            "7": self._save,
            "8": self._load,
            "9": self._quit,
        }

    def _display_menu(self):
        """
        Displays the main menu of the CLI.
        """
        current_account_display = "None"
        if self.current_account:
            account_type = type(self.current_account).__name__
            account_number = str(self.current_account.account_number).zfill(9)
            balance = self.current_account.balance.quantize(Decimal('0.01'))
            current_account_display = f"{account_type}#{account_number},\tbalance: ${balance:,.2f}"

        print(f"--------------------------------\n"
              f"Currently selected account: {current_account_display}\n"
              f"Enter command\n"
              f"1: open account\n"
              f"2: summary\n"
              f"3: select account\n"
              f"4: add transaction\n"
              f"5: list transactions\n"
              f"6: interest and fees\n"
              f"7: save\n"
              f"8: load\n"
              f"9: quit\n"
              f">", end="")

    def run(self):
        """
        Runs the main loop of the CLI, processing user input.
        """
        while True:
            self._display_menu()
            choice = input()
            action = self._choices.get(choice)
            action()

    def _open_account(self):
        """
        Opens a new bank account of the specified type (checking or savings).
        """
        account_type = input("Type of account? (checking/savings)\n>").lower()
        account = self.bank.open_account(account_type)

    def _summary(self):
        """
        Displays a summary of all accounts in the bank.
        """
        self.bank.summary()

    def _select_account(self):
        """
        Selects an account based on the user-input account number.
        """
        account_number = int(input("Enter account number\n>"))
        account = self.bank.select_account(account_number)
        self.current_account = account

    def _add_transaction(self):
        """
        Adds a transaction to the currently selected account.
        """
        amount = input("Amount?\n>")
        transaction_date = input("Date? (YYYY-MM-DD)\n>")
        self.current_account.add_transaction(amount, transaction_date)

    def _list_transactions(self):
        """
        Lists all transactions for the currently selected account.
        """
        transactions = self.bank.list_transactions(self.current_account.account_number)
        for transaction in transactions:
            print(f"{transaction.date}, ${transaction.amount:,.2f}")

    def _interest_and_fees(self):
        """
        Applies interest and fees to the currently selected account.
        """
        self.current_account.apply_interest_and_fees()
       
    def _save(self):
        """
        Saves the current state of the bank (including all accounts and transactions) to a file.
        """
        with open('bank_data.pkl', 'wb') as f:
            pickle.dump(self.bank, f)

    def _load(self):
        """
        Loads the state of the bank from a file.
        """
        with open('bank_data.pkl', 'rb') as f:
            self.bank = pickle.load(f)
        self.current_account = None  

    def _quit(self):
        """
        Exits the CLI application.
        """
        sys.exit(0)

if __name__ == "__main__":
    BankCLI().run()
