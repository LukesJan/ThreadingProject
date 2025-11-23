import unittest
from src.transaction import Transaction, TransactionException
import time


class TestTransaction(unittest.TestCase):

    def test_transaction_initialization(self):
        """Check that a transaction is initialized correctly with all attributes."""
        tx = Transaction(tx_id=1, priority=3, from_acc=10, to_acc=20, amount=500)

        self.assertEqual(tx.tx_id, 1)
        self.assertEqual(tx.priority, 3)
        self.assertEqual(tx.from_acc, 10)
        self.assertEqual(tx.to_acc, 20)
        self.assertEqual(tx.amount, 500)
        self.assertIsNotNone(tx.timestamp)

    def test_invalid_amount_raises(self):
        """Check that a transaction with negative amount raises TransactionException."""
        with self.assertRaises(TransactionException):
            Transaction(tx_id=1, priority=1, from_acc=1, to_acc=2, amount=-100)

    def test_same_account_not_allowed(self):
        """Check that a transaction from and to the same account is not allowed."""
        with self.assertRaises(TransactionException):
            Transaction(tx_id=1, priority=1, from_acc=5, to_acc=5, amount=50)

    def test_priority_must_be_valid(self):
        """Check that a transaction with invalid priority raises TransactionException."""
        with self.assertRaises(TransactionException):
            Transaction(tx_id=1, priority=0, from_acc=1, to_acc=2, amount=50)
        with self.assertRaises(TransactionException):
            Transaction(tx_id=1, priority=10, from_acc=1, to_acc=2, amount=50)

    def test_string_representation(self):
        """Check that __str__ method returns a descriptive string of the transaction."""
        tx = Transaction(tx_id=99, priority=2, from_acc=1, to_acc=2, amount=150)
        text = str(tx)

        self.assertIn("tx_id=99", text)
        self.assertIn("from=1", text)
        self.assertIn("to=2", text)
        self.assertIn("amount=150", text)

    def test_sorting_by_priority(self):
        """Check that transactions are sorted correctly by priority and timestamp."""
        t1 = Transaction(1, priority=1, from_acc=1, to_acc=2, amount=50)
        time.sleep(0.01)
        t2 = Transaction(2, priority=3, from_acc=1, to_acc=2, amount=50)
        time.sleep(0.01)
        t3 = Transaction(3, priority=1, from_acc=1, to_acc=2, amount=50)

        sorted_list = sorted([t1, t2, t3])

        self.assertEqual(sorted_list[0].tx_id, t1.tx_id)
        self.assertEqual(sorted_list[1].tx_id, t3.tx_id)
        self.assertEqual(sorted_list[2].tx_id, t2.tx_id)

    def test_priority_queue_compatibility(self):
        """Check that Transaction instances work correctly with PriorityQueue."""
        from queue import PriorityQueue

        pq = PriorityQueue()
        t1 = Transaction(1, priority=5, from_acc=1, to_acc=2, amount=10)
        t2 = Transaction(2, priority=1, from_acc=1, to_acc=2, amount=10)

        pq.put(t1)
        pq.put(t2)

        first = pq.get()
        second = pq.get()

        self.assertEqual(first.tx_id, 2)
        self.assertEqual(second.tx_id, 1)


if __name__ == "__main__":
    unittest.main()
