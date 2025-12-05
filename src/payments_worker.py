from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from src.transaction import Transaction
from src.payments_core import PaymentsCore
from src.account import Account


class PaymentsWorkers(PaymentsCore):
    """
    Payment processing system with antifraud checks and concurrency support
    Attributes:
        queue_antifraud (Queue): Queue for transactions after antifraud check
        processed_count (int): Counter of processed transactions
        count_lock (Lock): Lock for thread-safe updates of processed_count
        tx_counter (int): Counter for generating unique transaction IDs
        tx_lock (Lock): Lock for thread-safe incrementing of tx_counter
        pool_a (ThreadPoolExecutor): Thread pool for antifraud workers
        pool_w (ThreadPoolExecutor): Thread pool for payment workers
    """

    def __init__(self, config, user_credentials, t_payment=4, t_antifraud=2):
        """
        Initialize PaymentsWorkers
        Arguments:
            t_payment (int): Number of concurrent payment worker threads
            t_antifraud (int): Number of concurrent antifraud worker threads
        """
        super().__init__(config, user_credentials, t_payment, t_antifraud)

        self.queue_antifraud = Queue()

        self.processed_count = 0
        self.count_lock = threading.Lock()

        self.tx_counter = 0
        self.tx_lock = threading.Lock()

        self.pool_a = None
        self.pool_w = None

        with self.accounts_lock:
            for username, data in self.user_credentials.items():
                acc_id = data["id"]
                balance = data.get("balance", 0)
                verified = data.get("verified", False)
                self.accounts[acc_id] = Account(owner=username, balance=balance, verified=verified)

    def start(self):
        """
        Start worker threads for antifraud and payment processing
        """
        self.stop_event.clear()

        self.pool_a = ThreadPoolExecutor(max_workers=self.t_antifraud)
        self.pool_w = ThreadPoolExecutor(max_workers=self.t_payment)

        for i in range(self.t_antifraud):
            self.pool_a.submit(self.antifraud_worker)

        for i in range(self.t_payment):
            self.pool_w.submit(self.payment_worker)

    def stop(self):
        """
        Stop all worker threads and shutdown thread pools.
        """
        self.stop_event.set()
        time.sleep(0.2)

        if self.pool_a:
            self.pool_a.shutdown(wait=True)
        if self.pool_w:
            self.pool_w.shutdown(wait=True)

    def submit(self, from_acc, to_acc, amount):
        """
        Submit a new transaction for processing
        Arguments:
          from_acc (int): Sender account ID
          to_acc (int): Receiver account ID
          amount (int): Amount to transfer
        """
        self.validate_transaction(from_acc, to_acc, amount)

        with self.tx_lock:
            self.tx_counter += 1
            tx_id = self.tx_counter

        tx = Transaction(tx_id, from_acc, to_acc, amount)

        with self.log_lock:
            self.transactions_log.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "tx_id": tx.tx_id,
                "from": from_acc,
                "to": to_acc,
                "amount": amount,
                "status": "pending",
                "reason": "processing"
            })

            def delay():
                time.sleep(2)
                self.queue_payment.put((tx.timestamp, tx.tx_id, tx))

            threading.Thread(target=delay).start()


    def antifraud_worker(self):
        """
        Continuously checks transactions from queue_payment
        Transactions that fail antifraud check are marked rejected
        All transactions are pushed to queue_antifraud for payment processing
        """
        while not self.stop_event.is_set():
            try:
                i, y, tx = self.queue_payment.get(timeout=0.1)
            except Empty:
                continue

            ok, reason = self.antifraud_check(tx)
            if not ok:
                tx.reject(reason)

            self.queue_antifraud.put((tx.timestamp, tx.tx_id, tx))

    def payment_worker(self):
        """
        Worker function that continuously processes transactions from queue_antifraud
        Calls process_payment for each transaction
        """
        while not self.stop_event.is_set():
            try:
                i, y, tx = self.queue_antifraud.get(timeout=0.1)
            except Empty:
                continue

            self.process_payment(tx)

    def process_payment(self, tx: Transaction):
        """
        Process a single transaction: update balances or reject/decline
            - Updates balances with locking
            - Logs transaction result
            - Increment processed_count after processing
        Arguments:
            tx (Transaction): Transaction to process.
            """
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
        except Exception:
            self.log_tx(tx, "rejected", "internal_error")

        with self.count_lock:
            self.processed_count += 1
