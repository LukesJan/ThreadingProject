import time


class TransactionException(Exception):
    pass

class Transaction:
    """
    Represents a single money transfer request.

    Attributes:
        tx_id: Unique transaction ID
        from_acc: Sender account ID
        to_acc: Receiver account ID
        amount: Amount to be transferred
        ok: Antifraud status (True if passed, False if rejected)
        reason: Reason for rejection, if any
        timestamp: Time of creation, used for FIFO ordering within same priority
    """

    def __init__(self, tx_id: int, from_acc: int, to_acc: int, amount: int):
        """
        Initialize a new Transaction instance.

        :param tx_id: Unique ID of the transaction
        :param from_acc: Sender account ID
        :param to_acc: Receiver account ID
        :param amount: Amount to be transferred (must be > 0)
        :raises TransactionException: If amount <= 0, from_acc == to_acc, or priority is not in 1-5
        """
        if amount <= 0:
            raise TransactionException("Amount must be > 0")

        if from_acc == to_acc:
            raise TransactionException("Sender and receiver must be different")

        self.tx_id = tx_id
        self.from_acc = from_acc
        self.to_acc = to_acc
        self.amount = amount
        self.ok = True
        self.reason = "Completed"
        self.timestamp = time.time()


    def reject(self, reason: str):
        """
        Reject the transaction with a given reason.

        :param reason: Reason why the transaction is rejected
        :return: None
        """
        self.ok = False
        self.reason = reason

    def __str__(self):
        """
        Return a string representation of the transaction.

        :return: A string showing tx_id, from_acc, to_acc, amount, and ok status
        """
        return (f"Transaction(tx_id={self.tx_id}, from={self.from_acc}, "
                f"to={self.to_acc}, amount={self.amount}, ok={self.ok})")
