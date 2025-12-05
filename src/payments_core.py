import time
import threading
from queue import Queue
from src.transaction import Transaction
import json
import os

class PaymentCoreException(Exception):
    """
    General exception for payment-related errors.
    """
    pass


class PaymentsCore:
    """
    Core class for account management and transaction processing.

    Responsibilities:
    - Manage accounts and their balances
    - Creates test accounts
    - Perform antifraud checks
    - Log all transactions safely
    - Validate transactions before processing
    """
    def __init__(self, config, user_credentials,t_payment=4, t_antifraud=2, max=300):
        """
            Initialize the PaymentsCore instance.

            This sets up the internal data structures for account management,
            transaction logging, and worker thread coordination.

            :param t_payment: Number of payment worker threads to process transactions.
            :type t_payment: int
            :param t_antifraud: Number of antifraud worker threads to validate transactions.
            :type t_antifraud: int
            :param max: Maximum size of the incoming transaction queue.
            :type max: int

            Attributes:
            - queue_payment: PriorityQueue to hold incoming transactions.
            - stop_event: threading.Event used to signal worker threads to stop.
            - accounts: Dictionary mapping account IDs to Account instances.
            - accounts_lock: Lock to synchronize access to accounts dictionary.
            - transactions_log: List to store all transaction records.
            - log_lock: Lock to synchronize access to transactions_log.
            """
        self.config = config
        self.user_credentials = user_credentials
        self.t_payment = t_payment
        self.t_antifraud = t_antifraud

        self.queue_payment = Queue(maxsize=max)
        self.stop_event = threading.Event()

        self.accounts = {}
        self.accounts_lock = threading.Lock()

        self.transactions_log = []
        self.log_lock = threading.Lock()

        self.load_transactions()

    def load_transactions(self):
        """
        Load all transactions from the transactions log file into internal log.
        """
        self.transactions_log = []
        try:
            if os.path.exists(self.config["transactions_log_file"]):
                with open(self.config["transactions_log_file"], "r") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            self.transactions_log.append(entry)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"Error loading transactions log: {e}")

    def antifraud_check(self, tx: Transaction):
        """
        Perform antifraud check on a transaction.
        Assumes that the sending account exists.

        Unverified accounts cannot send more than 10,000.

       :param tx: Transaction dictionary {"from": id, "to": id, "amount": amount}
       :return: (True/False, reason)
       """
        from_acc = self.accounts[tx.from_acc]

        if not from_acc.verified and tx.amount > 10000:
            return False, "unverified_limit"

        return True, "Completed"

    def log_tx(self, tx: Transaction, status, reason=""):
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tx_id": tx.tx_id,
            "from": tx.from_acc,
            "to": tx.to_acc,
            "amount": tx.amount,
            "status": status,
            "reason": reason,
        }

        with self.log_lock:
            self.transactions_log.append(entry)

        if status == "approved":
            for username, data in self.user_credentials.items():
                acc = self.accounts.get(data["id"])
                if acc:
                    data["balance"] = acc.balance

            with open(self.config["users_file"], "w") as f:
                json.dump(self.user_credentials, f, indent=4)

        try:
            os.makedirs(os.path.dirname(self.config["transactions_log_file"]), exist_ok=True)
            with open(self.config["transactions_log_file"], "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print("Error writing to transactions log:", e)

    def validate_transaction(self, from_acc, to_acc, amount):
        """
        Validate transaction between two accounts.
        :param from_acc: Sender account ID
        :param to_acc: Recipient account ID
        :param amount: Transaction amount
        :raises PaymentCoreException: If accounts do not exist or amount <= 0
        """
        if from_acc not in self.accounts or to_acc not in self.accounts:
            raise PaymentCoreException("One of the accounts does not exist.")
        if amount <= 0:
            raise PaymentCoreException("Amount must be greater than 0.")
