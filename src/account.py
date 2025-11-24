import threading

class AccountException(Exception):
    """
    General exception for account-related errors.

    Raised for invalid operations, such as negative balances
    or unauthorized access to account properties.
    """
    pass


class Account:
    """
    Represents a bank account.

    Attributes:
    - owner: Name of the account owner
    - balance: Current account balance
    - verified: Boolean flag indicating whether the account is verified
    - lock: Threading lock to ensure thread-safe operations on the account
    """

    def __init__(self, owner: str, balance: int, verified: bool = False):
        """
        Initialize a new Account instance.

        :param owner: Name of the account owner
        :param balance: Initial balance of the account
        :param verified: Whether the account is verified (default: False)
        :raises AccountException: If balance is negative
          """
        if balance < 0:
            raise AccountException("Initial balance cannot be negative.")

        self.owner = owner
        self.balance = balance
        self.verified = verified
        self.lock = threading.Lock()

    def __str__(self):
        """
        Return a string representation of the account.

        :return: A string showing owner, balance, and verified status
        """
        return f"Account(owner={self.owner}, balance={self.balance}, verified={self.verified})"
