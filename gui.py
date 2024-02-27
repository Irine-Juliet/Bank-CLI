import sys
import logging
import sqlalchemy
import tkinter as tk
from bank import Bank
from base import Base
from account import Account
from datetime import datetime
from tkinter import messagebox
from tkcalendar import DateEntry
from sqlalchemy.orm import sessionmaker
from decimal import Decimal, InvalidOperation
from exceptions import OverdrawError, TransactionSequenceError, TransactionLimitError, NoAccountSelectedError

logging.basicConfig(filename='bank.log', level=logging.DEBUG, format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# a callback function that handles exceptions
def handle_exception(exception, value, traceback):
    messagebox.showerror(
        "Unexpected Error",
        "Sorry! Something unexpected happened. Check the logs or contact the developer for assistance."
    )
    exception_message = repr(str(value)).replace('\n', '\\n')
    logging.error(f"{exception.__name__}: {exception_message}")
    sys.exit(0)

class BankGUI:
    def __init__(self):
        self._window = tk.Tk()
        self._window.report_callback_exception = handle_exception 
        self._window.title("MY BANK")
        self._window.geometry('800x500')

        self._bg_color = "#f0f0f0" 
        self._window.configure(bg=self._bg_color)
        
        # Button frame
        self._button_frame = tk.Frame(self._window)
        self._button_frame.pack(pady=10) 

        # Open Account button
        self._open_account_btn = tk.Button(self._button_frame, text="open account", command=self._display_open_account_options)
        self._open_account_btn.pack(side=tk.LEFT, padx=5) 

        # Add Transaction button
        self._add_transaction_btn = tk.Button(self._button_frame, text="add transaction", command=self._on_add_transaction_button_click)
        self._add_transaction_btn.pack(side=tk.LEFT, padx=5)

        # Interest and Fees button
        self._interest_fees_btn = tk.Button(self._button_frame, text="interest and fees", command=self._interest_and_fees)
        self._interest_fees_btn.pack(side=tk.LEFT, padx=5)

        # Frame for account Radiobuttons
        self._accounts_frame = tk.Frame(self._window)
        self._accounts_frame.pack()

        self._selected_account = None

        # Create a new session
        self._session = Session() 
        self._bank = self._session.query(Bank).first()  # Query the database for the bank state
        if self._bank:
            logging.debug("Loaded from bank.db")
            self._update_accounts_display()
        else:
            # If there's no bank state in the database, create a new one
            self._bank = Bank() 
            self._session.add(self._bank)

        self._window.mainloop()

    def _display_open_account_options(self):
        # Create a new frame for the account options
        self._account_options_frame = tk.Frame(self._window)
        self._account_options_frame.pack(pady=10)

        # Dropdown menu for account type
        self._account_type = tk.StringVar(self._window)
        self._account_type.set("Select Account Type") 
        self._account_type_menu = tk.OptionMenu(self._account_options_frame, self._account_type, "Checking", "Savings")
        self._account_type_menu.pack(side=tk.LEFT, padx=5)

        # Enter button
        self._enter_btn = tk.Button(self._account_options_frame, text="Enter", command=self._open_account)
        self._enter_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        self._cancel_btn = tk.Button(self._account_options_frame, text="Cancel", command=self._cancel_open_account)
        self._cancel_btn.pack(side=tk.LEFT, padx=5)

    def _open_account(self):
        prev_selected_account_id = self._selected_account._account_number if self._selected_account else None

        account_type = self._account_type.get().lower()
        if account_type in ["checking", "savings"]:
            account = self._bank.open_account(account_type, self._session)
            self._session.commit()
            logging.debug("Saved to bank.db")
            messagebox.showinfo("Account Created", f"A new {account_type} account has been created with ID: {account._account_number}")
            self._update_accounts_display(prev_selected_account_id)
            self._cancel_open_account() # Clear the options after operation
        else:
            messagebox.showwarning("Selection Required", "Please select an account type.")

    def _update_accounts_display(self, prev_selected_account_id=None):
        # Clear previous Checkbuttons
        for widget in self._accounts_frame.winfo_children():
            widget.destroy()

        accounts = self._session.query(Account).all()  
        if accounts:
            for  account in accounts:
                balance = account._balance.quantize(Decimal('0.01'))
                radio = tk.Radiobutton(
                    self._accounts_frame, 
                    text=f"{type(account).__name__}#{str(account._account_number).zfill(9)},\tbalance: ${balance:,.2f}", 
                    variable=self._selected_account,
                    value=str(account._account_number),
                    command=lambda acc=account: self._select_account(acc._account_number)
                    )
                radio.pack(anchor='w')
               
                # reselect previously selected account
                if str(account._account_number) == str(prev_selected_account_id):
                    radio.select()
                    self._selected_account = account 
        else:
            # Display a message if no accounts are available
            tk.Label(self._accounts_frame, text="No accounts available").pack()


    def _cancel_open_account(self):
        self._account_options_frame.destroy()
    
    def _select_account(self, account_number):
        account = self._bank.select_account(account_number, self._session)
        self._selected_account = account
        self._display_transactions(self._selected_account)
    
    def _add_transaction(self):
        if not self._selected_account:
            raise NoAccountSelectedError("This command requires that you first select an account.")
      
        # Create a new frame for the transaction options
        self._transaction_options_frame = tk.Frame(self._window)
        self._transaction_options_frame.pack(pady=10)

        # Validator for the amount entry
        vcmd_amount = (self._window.register(self._validate_amount), '%P')

        # Label for the amount entry
        tk.Label(self._transaction_options_frame, text="Amount:").pack(side=tk.LEFT, padx=5)

        self._amount_entry = tk.Entry(self._transaction_options_frame, 
                                    validate="key", validatecommand=vcmd_amount, 
                                    foreground='dark blue', bg='white')
        self._amount_entry.pack(side=tk.LEFT, padx=5)
        self._amount_entry.focus_set()

        # Label for the date entry
        tk.Label(self._transaction_options_frame, text="Date (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)

        self._date_entry = DateEntry(self._transaction_options_frame, 
                                    foreground='white', 
                                    borderwidth=2, state='readonly',
                                    date_pattern='y-mm-dd') # Defaults to today's date
        self._date_entry.pack(side=tk.LEFT, padx=5)

        # Enter button for transaction
        self._enter_transaction_btn = tk.Button(self._transaction_options_frame, text="Enter", command=self._process_transaction)
        self._enter_transaction_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button for transaction
        self.__cancel_transaction_btn = tk.Button(self._transaction_options_frame, text="Cancel", command=self._cancel_transaction)
        self.__cancel_transaction_btn.pack(side=tk.LEFT, padx=5)
    
    def _on_add_transaction_button_click(self):
        try:
            self._add_transaction()
        except NoAccountSelectedError as e:
            messagebox.showwarning("No Account Selected", str(e))  
            return 

    def _process_transaction(self):
        # validate and process the transaction.
        try:
            amount_str = self._amount_entry.get()
            amount = Decimal(amount_str)
        except InvalidOperation:
                messagebox.showwarning("Invalid Operation Error", "Please try again with a valid dollar amount.")
                return
        
        valid_date = datetime.strptime(self._date_entry.get(), "%Y-%m-%d").date()
        
        try:
            self._selected_account.add_transaction(amount, self._session, valid_date)
            self._session.commit()
            logging.debug("Saved to bank.db")
        except OverdrawError as overdraw:
            messagebox.showwarning("Overdraw Error", str(overdraw))
        except TransactionLimitError as limit_error:
            messagebox.showwarning("Transaction Limit Error", str(limit_error))
        except TransactionSequenceError as sequence_error:
            messagebox.showwarning("Transaction Sequence Error",
                                   f"New transactions must be from {sequence_error.latest_date.strftime('%Y-%m-%d')} onward.")

        if self._selected_account:
            self._display_transactions(self._selected_account)

        self._transaction_options_frame.destroy()
        self._update_accounts_display(self._selected_account._account_number)

    def _cancel_transaction(self):
        self._transaction_options_frame.destroy()

    def _validate_amount(self, P):
        # Check if the entry text is a valid or potentially valid decimal number
        if P == "" or P == "-":
            return True
        try:
            value = Decimal(P)
            self._amount_entry.config()
            return True
        except InvalidOperation:
            self._amount_entry.config()
            return False

    def _display_transactions(self, account):
        # Clear existing transaction display frame if it exists
        if hasattr(self, '_transaction_display_frame'):
            self._transaction_display_frame.destroy()
        
        self._transaction_display_frame = tk.Frame(self._window)
        self._transaction_display_frame.pack(pady=10)

        transactions = self._bank.list_transactions(int(account._account_number), self._session)

        for transaction in transactions:
            color = 'green' if transaction._amount >= 0 else 'red'
            transaction_text = f"{transaction._date}, ${transaction._amount:,.2f}"
            tk.Label(self._transaction_display_frame, text=transaction_text, fg=color).pack()

    def _interest_and_fees(self):
        try:
            self._selected_account.apply_interest_and_fees(self._session)
            self._session.commit()
            logging.debug("Saved to bank.db")
        except AttributeError:
            messagebox.showwarning("No account selected", "This command requires that you first select an account.")
            return
        except TransactionSequenceError as interest_error:
            messagebox.showwarning("Sequence Error", str(interest_error))
        self._display_transactions(self._selected_account)
        self._update_accounts_display(self._selected_account._account_number)

if __name__ == "__main__":
    engine = sqlalchemy.create_engine("sqlite:///bank.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(engine) 
    BankGUI()


"""
to do:
validate amt    done
validate date    done
overdraft: checking,  done
            savings   done
sequence: checking done
          savings done
limits: savings: daily  done
        monthly  done
interest: checking: monthly done
                    fees; done
            savings: interest not counted towards  daily and monthly .limits done
                    monthly done.
            exceptions handled. done

allspecified exceptions: done

TO DO OH:
DATE PICKER ACTING UP
ENTERING AMT ACTING UP

"""
