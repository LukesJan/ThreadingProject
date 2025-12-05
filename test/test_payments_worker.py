import unittest
import time
from src.payments_worker import PaymentsWorkers
from src.account import Account

def wait_for_condition(predicate, timeout=5.0, interval=0.05):
    start = time.time()
    while time.time() - start < timeout:
        if predicate():
            return True
        time.sleep(interval)
    return False

class TestPaymentsWorkersIntegration(unittest.TestCase):
    def setUp(self):
        self.config = {
            "transactions_log_file": "test_transactions.log",
            "users_file": "test_users.json",
            "data_folder": "test_data",
            "error_log_file": "test_error.log"
        }
        self.user_credentials = {
            1: {"id": 1, "balance": 10000, "verified": True, "password": "pass"},
            2: {"id": 2, "balance": 10000, "verified": True, "password": "pass"}
        }
        self.p = PaymentsWorkers(self.config, self.user_credentials, t_payment=2, t_antifraud=1)
        with self.p.accounts_lock:
            for uid, data in self.user_credentials.items():
                self.p.accounts[data["id"]] = Account(owner=f"User{uid}", balance=data["balance"], verified=data["verified"])
        self.p.start()

    def tearDown(self):
        try:
            self.p.stop()
        except:
            pass

    def test_successful_payment(self):
        self.p.submit(1, 2, 500)
        ok = wait_for_condition(lambda: any(tx["status"] == "approved" for tx in self.p.transactions_log))
        self.assertTrue(ok)
        self.assertEqual(self.p.accounts[1].balance, 9500)
        self.assertEqual(self.p.accounts[2].balance, 10500)

    def test_insufficient_funds_from_verified(self):
        self.p.submit(2, 1, 20000)
        ok = wait_for_condition(lambda: any(tx["status"] == "declined" for tx in self.p.transactions_log))
        self.assertTrue(ok)
        self.assertEqual(self.p.accounts[1].balance, 10000)
        self.assertEqual(self.p.accounts[2].balance, 10000)

    def test_rejected_unverified_limit(self):
        self.p.accounts[1].verified = False
        self.p.submit(1, 2, 20000)
        ok = wait_for_condition(lambda: any(tx["status"] == "rejected" and tx.get("reason") == "unverified_limit"
                                            for tx in self.p.transactions_log))
        self.assertTrue(ok)
        self.assertEqual(self.p.accounts[1].balance, 10000)
        self.assertEqual(self.p.accounts[2].balance, 10000)

    def test_multiple_concurrent_payments(self):
        payments = 10
        amount = 500
        for _ in range(payments):
            self.p.submit(1, 2, amount)

        ok = wait_for_condition(lambda: self.p.processed_count >= payments, timeout=10.0)
        self.assertTrue(ok)
        self.assertEqual(self.p.accounts[1].balance, 10000 - payments*amount)
        self.assertEqual(self.p.accounts[2].balance, 10000 + payments*amount)
        approved_count = sum(1 for tx in self.p.transactions_log if tx["status"] == "approved")
        self.assertGreaterEqual(approved_count, payments)

if __name__ == "__main__":
    unittest.main()
