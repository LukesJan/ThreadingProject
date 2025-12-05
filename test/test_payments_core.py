import unittest
from src.payments_core import PaymentsCore
from src.transaction import Transaction
from src.account import Account
import os
import json

class TestPaymentsCore(unittest.TestCase):

    def setUp(self):
        """
        Config for tests
        """
        self.config = {
            "transactions_log_file": "test_transactions.log",
            "users_file": "test_users.json",
            "data_folder": "test_data",
            "error_log_file": "test_error.log"
        }
        self.user_credentials = {
            1: {"id": 1, "balance": 1000, "verified": False, "password": "pass"},
            2: {"id": 2, "balance": 1000, "verified": True, "password": "pass"},
            3: {"id": 3, "balance": 1000, "verified": False, "password": "pass"},
            4: {"id": 4, "balance": 1000, "verified": True, "password": "pass"}
        }

        self.core = PaymentsCore(self.config, self.user_credentials)


        with self.core.accounts_lock:
            for uid, data in self.user_credentials.items():
                self.core.accounts[data["id"]] = Account(
                    owner=f"User{uid}",
                    balance=data["balance"],
                    verified=data["verified"]
                )

    def tearDown(self):

        if os.path.exists(self.config["transactions_log_file"]):
            os.remove(self.config["transactions_log_file"])
        if os.path.exists(self.config["users_file"]):
            os.remove(self.config["users_file"])

    def test_accounts_seeded_correctly(self):
        """Check that accounts have correct verified flags."""
        self.assertIn(1, self.core.accounts)
        self.assertIn(4, self.core.accounts)

        self.assertFalse(self.core.accounts[1].verified)
        self.assertTrue(self.core.accounts[2].verified)
        self.assertFalse(self.core.accounts[3].verified)
        self.assertTrue(self.core.accounts[4].verified)

    def test_antifraud_check_limits(self):
        """Check that antifraud rules are applied correctly."""
        tx1 = Transaction(tx_id=1, from_acc=1, to_acc=2, amount=15000)
        ok, reason = self.core.antifraud_check(tx1)
        self.assertFalse(ok)
        self.assertEqual(reason, "unverified_limit")

        tx2 = Transaction(tx_id=2, from_acc=2, to_acc=1, amount=20000)
        ok2, reason2 = self.core.antifraud_check(tx2)
        self.assertTrue(ok2)
        self.assertEqual(reason2, "Completed")


if __name__ == "__main__":
    unittest.main()
