import time
import threading
from queue import Empty
from concurrent.futures import ThreadPoolExecutor
from src.payments_core import PaymentsCore
import random

class PaymentWorkersException(Exception):
    """General exception for payment-related errors."""
    pass

class PaymentsWorkers(PaymentsCore):
    """
    Worker class for concurrent transaction processing using threads.

    Responsibilities:
    - Run antifraud and payment workers in separate threads
    - Perform atomic transfers between accounts
    - Log all transaction statuses
    - Track number of processed transactions
    """
    def __init__(self, t_payment=4, t_antifraud=2):
        """
        Initialize PaymentsWorkers instance.

        :param t_payment: Number of payment worker threads
        :param t_antifraud: Number of antifraud worker threads
        """
        super().__init__(t_payment, t_antifraud)
        self.processed_count = 0
        self.count_lock = threading.Lock()
        self.pool_w = None
        self.pool_a = None
        self.tx_counter = 0
        self.tx_lock = threading.Lock()  # Lock to make tx_id assignment thread-safe

    def start(self):
        """Start all worker threads."""
        self.stop_event.clear()
        self.pool_w = ThreadPoolExecutor(max_workers=self.t_payment)
        self.pool_a = ThreadPoolExecutor(max_workers=self.t_antifraud)

        for i in range(self.t_antifraud):
            self.pool_a.submit(self.antifraud_worker)

        for i in range(self.t_payment):
            self.pool_w.submit(self.payment_worker)

    def stop(self):
        """Stop all worker threads."""
        self.stop_event.set()
        time.sleep(0.2)
        if self.pool_w:
            self.pool_w.shutdown(wait=True)
        if self.pool_a:
            self.pool_a.shutdown(wait=True)

    def submit(self, from_acc, to_acc, amount):
        """
        Submit a transaction with random priority (1-5) and unique integer tx_id.

        :param from_acc: Sender account ID
        :param to_acc: Recipient account ID
        :param amount: Transaction amount
        :raises PaymentWorkersException: if accounts do not exist or amount <= 0
        """
        self.validate_transaction(from_acc, to_acc, amount)
        priority = random.randint(1, 5)


        with self.tx_lock:
            self.tx_counter += 1
            tx_id = self.tx_counter

        tx = {"tx_id": tx_id, "from": from_acc, "to": to_acc, "amount": amount}
        self.queue_in.put((priority, time.time(),tx["tx_id"] ,tx))

    def antifraud_worker(self):
        while not self.stop_event.is_set():
            try:
                item = self.queue_in.get(timeout=0.1)
                tx = item[3]
            except Empty:
                continue

            ok, reason = self.antifraud_check(tx)
            tx["ok"] = ok
            tx["reject_reason"] = reason


            self.process_payment(tx)
    def payment_worker(self):
        """Worker loop for processing payments."""
        while not self.stop_event.is_set():
            time.sleep(0.1)

    def process_payment(self, tx):
        """Process a single transaction and log the result."""
        try:
            if not tx.get("ok", True):
                self.log_tx(tx["tx_id"], tx["from"], tx["to"], tx["amount"], "rejected", tx.get("reject_reason", ""))
                return

            from_acc = self.accounts.get(tx["from"])
            to_acc = self.accounts.get(tx["to"])
            amount = tx["amount"]

            if not from_acc or not to_acc:
                raise PaymentWorkersException("Account does not exist.")
            if amount <= 0:
                raise PaymentWorkersException(f"Invalid amount: {amount}")

            acc1, acc2 = sorted([from_acc, to_acc], key=id)
            with acc1.lock:
                with acc2.lock:
                    if from_acc.balance < amount:
                        self.log_tx(tx["tx_id"], tx["from"], tx["to"], amount, "declined", "insufficient_funds")
                        return

                    from_acc.balance -= amount
                    to_acc.balance += amount
                    self.log_tx(tx["tx_id"], tx["from"], tx["to"], amount, "approved", "completed")

            with self.count_lock:
                self.processed_count += 1

        except PaymentWorkersException:
            self.log_tx(tx.get("tx_id"), tx.get("from"), tx.get("to"), tx.get("amount"), "rejected", "PaymentCore exception")