import unittest
from src.account import Account


class TestAccount(unittest.TestCase):
    def test_account_properties_and_repr(self):
        """Check that Account initializes correctly and string representation works."""
        a = Account("Alice", 12345, verified=True)

        self.assertEqual(a.owner, "Alice")
        self.assertEqual(a.balance, 12345)
        self.assertTrue(a.verified)

        r = str(a)
        self.assertIn("Account(owner=Alice", r)
        self.assertIn("balance=12345", r)


if __name__ == "__main__":
    unittest.main()
