# Payments Worker Project

## About
This project is about safely handling payments between accounts using threads.

### What is the problem?
When multiple payments happen at the same time, account balances can get messed up if two threads try to update the same account. This is a classic concurrency problem.

## Solution
My solution uses **threading** and **locks** to make sure payments are processed safely and in the right order.

### Key Features

1. **Concurrent Payments**  
   - Multiple payment threads run at the same time to process transactions faster.

2. **Thread-Safe Account Access**  
   - Each account has a `lock` so only one thread can change its balance at a time.  

3. **Antifraud Checks**  
   - Special antifraud threads check payments before they are processed.  
   - Suspicious or invalid payments are rejected safely.

4. **Transaction Logging**  
   - Every payment is logged with status: approved, declined, or rejected.  
   - Logs can be used to track all transactions.

5. **Priority Handling**  
   - Payments can have different priorities, so urgent transactions can be processed first.

6. **Safe Concurrent Queue**  
   - Payments are stored in a queue, so threads don’t interfere with each other.  
   - The queue ensures payments are handled in the right order.

### How it Works
- You submit a payment with sender, receiver, and amount.  
- An antifraud thread checks the payment.  
- If approved, a payment thread updates the accounts safely.  
- The transaction is logged with its final status.
