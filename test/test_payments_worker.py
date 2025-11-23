import unittest
from src.payments_worker import PaymentsWorkers
import time


def wait_for_condition(predicate, timeout=2.0, interval=0.05):
    start = time.time()
    while time.time() - start < timeout:
        if predicate():
            return True
        time.sleep(interval)
    return False



class TestPaymentsWorkersIntegration(unittest.TestCase):
    def setUp(self):
        self.p = PaymentsWorkers(t_payment=2, t_antifraud=1)
        self.p.seed_accounts(count=2, balance=10000)

    def tearDown(self):
        try:
            self.p.stop()
        except:
            pass

    def test_successful_payment(self):
        self.p.submit(1, 2, 500)
        self.p.start()

        ok = wait_for_condition(
            lambda: any(tx["status"] == "approved" for tx in self.p.transactions_log)
        )
        self.p.stop()

        self.assertTrue(ok)
        self.assertEqual(self.p.accounts[1].balance, 9500)
        self.assertEqual(self.p.accounts[2].balance, 10500)

    def test_insufficient_funds_from_verified(self):
        self.p.submit(2, 1, 20000)
        self.p.start()

        ok = wait_for_condition(
            lambda: any(tx["status"] == "declined" for tx in self.p.transactions_log)
        )
        self.p.stop()

        self.assertTrue(ok)
        self.assertEqual(self.p.accounts[1].balance, 10000)
        self.assertEqual(self.p.accounts[2].balance, 10000)

    def test_rejected_unverified_limit(self):
        self.p.submit(1, 2, 20000)
        self.p.start()

        ok = wait_for_condition(
            lambda: any(
                tx["status"] == "rejected"
                and tx.get("reason") == "unverified_limit"
                for tx in self.p.transactions_log
            )
        )
        self.p.stop()

        self.assertTrue(ok)
        self.assertEqual(self.p.accounts[1].balance, 10000)
        self.assertEqual(self.p.accounts[2].balance, 10000)

    def test_multiple_concurrent_payments(self):
        payments = 10
        amount = 500

        for _ in range(payments):
            self.p.submit(1, 2, amount)

        self.p.start()

        ok = wait_for_condition(lambda: self.p.processed_count >= payments, timeout=5.0)

        self.p.stop()
        self.assertTrue(ok)

        expected_from = 10000 - payments * amount
        expected_to = 10000 + payments * amount
        self.assertEqual(self.p.accounts[1].balance, expected_from)
        self.assertEqual(self.p.accounts[2].balance, expected_to)

        approved_count = sum(1 for tx in self.p.transactions_log if tx["status"] == "approved")
        self.assertGreaterEqual(approved_count, payments)


if __name__ == "__main__":
    unittest.main()
