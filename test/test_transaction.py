import unittest
from src.transaction import Transaction, TransactionException
import time

class TestTransaction(unittest.TestCase):

    def test_transaction_initialization(self):
        """Check that a transaction is initialized correctly with all attributes."""
        tx = Transaction(tx_id=1, from_acc=10, to_acc=20, amount=500)

        self.assertEqual(tx.tx_id, 1)
        self.assertEqual(tx.from_acc, 10)
        self.assertEqual(tx.to_acc, 20)
        self.assertEqual(tx.amount, 500)
        self.assertTrue(hasattr(tx, "timestamp"))
        self.assertTrue(hasattr(tx, "ok"))
        self.assertTrue(hasattr(tx, "reason"))

    def test_invalid_amount_raises(self):
        """Check that a transaction with negative amount raises TransactionException."""
        with self.assertRaises(TransactionException):
            Transaction(tx_id=1, from_acc=1, to_acc=2, amount=-100)

    def test_same_account_not_allowed(self):
        """Check that a transaction from and to the same account is not allowed."""
        with self.assertRaises(TransactionException):
            Transaction(tx_id=1, from_acc=5, to_acc=5, amount=50)

    def test_string_representation(self):
        """Check that __str__ method returns a descriptive string of the transaction."""
        tx = Transaction(tx_id=99, from_acc=1, to_acc=2, amount=150)
        text = str(tx)

        self.assertIn("tx_id=99", text)
        self.assertIn("from=1", text)
        self.assertIn("to=2", text)
        self.assertIn("amount=150", text)

    def test_reject_method(self):
        """Check that rejecting a transaction sets ok to False and reason correctly."""
        tx = Transaction(tx_id=1, from_acc=1, to_acc=2, amount=100)
        tx.reject("fraud_detected")
        self.assertFalse(tx.ok)
        self.assertEqual(tx.reason, "fraud_detected")


if __name__ == "__main__":
    unittest.main()
