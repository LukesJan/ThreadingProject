import time
import threading
import random
from queue import Empty
from concurrent.futures import ThreadPoolExecutor

from src.payments_core import PaymentsCore
from src.transaction import Transaction


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
        self.tx_lock = threading.Lock()


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

        tx = Transaction(tx_id, priority, from_acc, to_acc, amount)


        self.queue_in.put((priority, time.time(), tx.tx_id, tx))


    def antifraud_worker(self):
        while not self.stop_event.is_set():
            try:
                item = self.queue_in.get(timeout=0.1)
                tx = item[3]
            except Empty:
                continue

            ok, reason = self.antifraud_check(tx)

            if not ok:
                tx.reject(reason)

            self.process_payment(tx)

    def payment_worker(self):
        """Worker loop for processing payments."""
        while not self.stop_event.is_set():
            time.sleep(0.1)

    def process_payment(self, tx: Transaction):
        """Process a single transaction and log the result."""
        try:
            if not tx.ok:
                self.log_tx(tx, "rejected", tx.reason)
                return

            from_acc = self.accounts[tx.from_acc]
            to_acc = self.accounts[tx.to_acc]
            acc1, acc2 = sorted([from_acc, to_acc], key=id)
            with acc1.lock:
                with acc2.lock:
                    if from_acc.balance < tx.amount:
                        self.log_tx(tx, "declined", "insufficient_funds")
                        return
                    from_acc.balance -= tx.amount
                    to_acc.balance += tx.amount
            self.log_tx(tx, "approved", "completed")
            with self.count_lock:
                self.processed_count += 1

        except PaymentWorkersException:
            self.log_tx(tx, "rejected", "internal_error")
