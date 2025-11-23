from src.payments_worker import PaymentsWorkers
import random
import time

if __name__ == "__main__":
    p = PaymentsWorkers(t_payment=4, t_antifraud=2)
    p.test_accounts(count=5, balance=50000)

    p.start()
    total_tx = 30
    for i in range(total_tx):
        f = random.randint(1, 5)
        t_id = random.randint(1, 5)
        if f != t_id:
            amt = random.randint(5000, 20000)
            p.submit(f, t_id, amt)
        time.sleep(0.02)

    time.sleep(2)
    p.stop()

    print("=== BALANCES ===")
    for acc_id, acc in p.accounts.items():
        print(acc_id, acc)

    print("\n=== LOG ===")
    for entry in p.transactions_log:
        print(entry)

    print("\n=== THREADS ===")
    print(f"Payment threads: {p.t_payment}")
    print(f"Antifraud threads: {p.t_antifraud}")

    print("\n=== TRANSACTIONS ===")
    print(f"Approved transactions: {p.processed_count}")
    print(f"All transactions: {len(p.transactions_log)}")


