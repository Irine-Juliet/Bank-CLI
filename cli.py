import sys
import logging
import sqlalchemy
from bank import Bank
from base import Base
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from decimal import Decimal, InvalidOperation
from exceptions import OverdrawError, TransactionSequenceError, TransactionLimitError

logging.basicConfig(filename='bank.log', level=logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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
        self._session = Session()  # Create a new session
        self._bank = self._session.query(Bank).first()  # Query the database for the bank state
        if self._bank:
            logging.debug("Loaded from bank.db")
        else:
            # If there's no bank state in the database, create a new one
            self._bank = Bank() 
            self._session.add(self._bank)
            self._session.commit()
        self._current_account = None
        self._choices = {
            "1": self._open_account,
            "2": self._summary,
            "3": self._select_account,
            "4": self._add_transaction,
            "5": self._list_transactions,
            "6": self._interest_and_fees,
            "7": self._quit,
        }
    def _display_menu(self):
        """
        Displays the main menu of the CLI.
        """
        current_account_display = "None"
        if self._current_account:
            account_type = type(self._current_account).__name__
            account_number = str(self._current_account._account_number).zfill(9)
            balance = self._current_account._balance.quantize(Decimal('0.01'))
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
              f"7: quit\n"
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
        account = self._bank.open_account(account_type, self._session)
        self._session.commit()
        logging.debug("Saved to bank.db")
        
    def _summary(self):
        """
        Displays a summary of all accounts in the bank.
        """
        self._bank.summary(self._session)

    def _select_account(self):
        """
        Selects an account based on the user-input account number.
        """
        account_number = int(input("Enter account number\n>"))
        account = self._bank.select_account(account_number, self._session)
        self._current_account = account

    def _add_transaction(self):
        """
        Adds a transaction to the currently selected account.
        """

        try:
            while True:
                try:
                    amount_str = input("Amount?\n>")
                    amount = Decimal(amount_str) 
                    break 
                except InvalidOperation:
                    print("Please try again with a valid dollar amount.")

            while True:
                transaction_date = input("Date? (YYYY-MM-DD)\n>")
                try:
                    valid_date = datetime.strptime(transaction_date, "%Y-%m-%d").date()
                    break
                except ValueError:
                    print("Please try again with a valid date in the format YYYY-MM-DD.")

            try:
                self._current_account.add_transaction(amount, self._session, valid_date)
                self._session.commit()
                logging.debug("Saved to bank.db")
            except OverdrawError as overdraw:
                print(overdraw)
            except TransactionLimitError as limit_error:
                print(limit_error)
            except TransactionSequenceError as sequence_error:
                print(f"New transactions must be from {sequence_error.latest_date.strftime('%Y-%m-%d')} onward.")
        except AttributeError:
            print("This command requires that you first select an account.")


    def _list_transactions(self):
        """
        Lists all transactions for the currently selected account.
        """

        try:
            transactions = self._bank.list_transactions(self._current_account._account_number, self._session)
            for transaction in transactions:
                print(f"{transaction._date}, ${transaction._amount:,.2f}")
        except AttributeError:
            print("This command requires that you first select an account.")


    def _interest_and_fees(self):
        """
        Applies interest and fees to the currently selected account.
        """
        try:
            self._current_account.apply_interest_and_fees(self._session)
            self._session.commit()
            logging.debug("Saved to bank.db")
        except AttributeError:
             print("This command requires that you first select an account.")
        except TransactionSequenceError as interest_error:
            print(interest_error)

    def _quit(self):
        """
        Exits the CLI application.
        """
        sys.exit(0)

if __name__ == "__main__":

    engine = sqlalchemy.create_engine("sqlite:///bank.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine) 

    try:
        BankCLI().run()
    except Exception as e:
        # Extract the exception type and message 
        exception_type = e.__class__.__name__
        exception_message = repr(str(e)).replace('\n', '\\n') 
        logging.error(f"{exception_type}: {exception_message}")
        # Inform the user
        print("Sorry! Something unexpected happened. Check the logs or contact the developer for assistance.")
        sys.exit(0)


#INCORPORATE SQL ON GUI
#CLEAN UP GUI
# EDIT ESSAY
