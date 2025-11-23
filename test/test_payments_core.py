import unittest
from src.payments_core import PaymentsCore
from src.transaction import Transaction


class TestPaymentsCore(unittest.TestCase):

    def setUp(self):
        self.core = PaymentsCore(t_payment=1, t_antifraud=1)

    def test_seed_accounts_and_verified_flags(self):
        """Check that test accounts are seeded with correct verified flags."""
        self.core.test_accounts(count=4, balance=1000)

        self.assertIn(1, self.core.accounts)
        self.assertIn(4, self.core.accounts)

        self.assertFalse(self.core.accounts[1].verified)
        self.assertTrue(self.core.accounts[2].verified)
        self.assertFalse(self.core.accounts[3].verified)
        self.assertTrue(self.core.accounts[4].verified)

    def test_antifraud_check_limits(self):
        """Check that antifraud rules are applied correctly for verified/unverified accounts."""
        self.core.test_accounts(count=2, balance=10000)

        tx1 = Transaction(tx_id=1, priority=1, from_acc=1, to_acc=2, amount=15000)
        ok, reason = self.core.antifraud_check(tx1)
        self.assertFalse(ok)
        self.assertEqual(reason, "unverified_limit")

        tx2 = Transaction(tx_id=2, priority=1, from_acc=2, to_acc=1, amount=20000)
        ok2, reason2 = self.core.antifraud_check(tx2)
        self.assertTrue(ok2)
        self.assertEqual(reason2, "Completed")


if __name__ == "__main__":
    unittest.main()
