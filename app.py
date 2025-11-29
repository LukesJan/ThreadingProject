import tkinter as tk
from tkinter import messagebox, ttk
import json

from src.payments_worker import PaymentsWorkers
from src.account import Account

class App:

    def __init__(self, root):
        self.root = root
        self.root.title("Payments GUI")
        self.root.geometry("800x700")
        self.user_account_id = None
        self.is_admin = False


        self.user_credentials = {
            "User1": (1, "pass1"),
            "User2": (2, "pass2"),
            "User3": (3, "pass3"),
            "User4": (4, "pass4"),
            "User5": (5, "pass5")
        }

        self.p = PaymentsWorkers()
        self.p.test_accounts(5, 50000)
        self.load_sample_transactions()
        self.p.start()



        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.show_login()


    def show_login(self):
        """
        Render graphical login form.
        """
        self.login_frame = tk.Frame(self.root, padx=20, pady=20)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(self.login_frame, text="Username:").grid(row=0, column=0, pady=5)
        tk.Label(self.login_frame, text="Password:").grid(row=1, column=0, pady=5)

        self.e_username = tk.Entry(self.login_frame)
        self.e_password = tk.Entry(self.login_frame, show="*")
        self.e_username.grid(row=0, column=1)
        self.e_password.grid(row=1, column=1)

        tk.Button(self.login_frame, text="Login", command=self.login).grid(row=2, column=0, columnspan=2, pady=10)

    def login(self):
        """
        Authentication for both admin and standard users
        - Admin login uses fixed "admin/admin"
        - On success: loads either admin UI or user UI
        - On failure: displays an error message
        """
        username = self.e_username.get()
        password = self.e_password.get()

        if username == "admin" and password == "admin":
            self.is_admin = True
            messagebox.showinfo("Login", "Logged in as admin")
            self.login_frame.destroy()
            self.build_ui()
            self.update_log()
            self.update_accounts()
        else:
            creds = self.user_credentials.get(username)
            if creds and creds[1] == password:
                self.user_account_id = creds[0]
                messagebox.showinfo("Login", f"Logged in as {username}")
                self.login_frame.destroy()
                self.build_ui(user_mode=True)
                self.update_log()
                self.update_accounts()
            else:
                messagebox.showerror("Login Failed", "User not found or wrong password")


    def load_sample_transactions(self):
        """
        Loads sample transactions.
        """
        for i in range(1, 4):
            self.p.transactions_log.append({
                "timestamp": f"2025-11-29 12:0{i}:00",
                "tx_id": i,
                "from": 1,
                "to": 2,
                "amount": 1000*i,
                "status": "approved",
                "reason": "completed"
            })


    def build_ui(self, user_mode=False):
        """
         Build the main application UI
         Admin mode:
         - Display full accounts table
         - Can create new accounts
         - Show all transaction logs
         User mode:
         - Show user balance
         - Can send new transactions
         - Display only users logs

         Parameters:
         user_mode : bool
             If True → user UI, otherwise admin UI.
         """
        frame_logout = tk.Frame(self.root)
        frame_logout.pack(fill="x", padx=10, pady=5)
        tk.Button(frame_logout, text="Logout", command=self.logout).pack(side="right")

        if user_mode:
            self.balance_label = tk.Label(self.root, text=f"Balance: {self.get_user_balance()}")
            self.balance_label.pack(pady=5)

            frame_tx = tk.LabelFrame(self.root, text="Send Transaction", padx=10, pady=10)
            frame_tx.pack(fill="x", padx=10, pady=10)

            tk.Label(frame_tx, text=f"From ID: {self.user_account_id}").grid(row=0, column=0, columnspan=2)
            tk.Label(frame_tx, text="To ID:").grid(row=1, column=0)
            tk.Label(frame_tx, text="Amount:").grid(row=2, column=0)

            self.e_to = tk.Entry(frame_tx)
            self.e_amount = tk.Entry(frame_tx)

            self.e_to.grid(row=1, column=1)
            self.e_amount.grid(row=2, column=1)

            tk.Button(frame_tx, text="Send", command=self.send_tx).grid(row=3, column=0, columnspan=2, pady=5)


        if self.is_admin:
            frame_accounts = tk.LabelFrame(self.root, text="Accounts", padx=10, pady=10)
            frame_accounts.pack(fill="both", padx=10, pady=10, expand=True)

            columns = ("id", "owner", "balance", "verified")
            self.accounts_table = ttk.Treeview(frame_accounts, columns=columns, show="headings")
            for col in columns:
                self.accounts_table.heading(col, text=col.capitalize())
            self.accounts_table.pack(fill="both", expand=True)


            frame_new_acc = tk.LabelFrame(self.root, text="Add New Account", padx=10, pady=10)
            frame_new_acc.pack(fill="x", padx=10, pady=10)

            tk.Label(frame_new_acc, text="Owner name:").grid(row=0, column=0)
            tk.Label(frame_new_acc, text="Password:").grid(row=1, column=0)
            tk.Label(frame_new_acc, text="Initial balance:").grid(row=2, column=0)
            tk.Label(frame_new_acc, text="Verified (0/1):").grid(row=3, column=0)

            self.e_owner = tk.Entry(frame_new_acc)
            self.e_password_new = tk.Entry(frame_new_acc, show="*")
            self.e_balance = tk.Entry(frame_new_acc)
            self.e_verified = tk.Entry(frame_new_acc)


            self.e_owner.grid(row=0, column=1)
            self.e_password_new.grid(row=1, column=1)
            self.e_balance.grid(row=2, column=1)
            self.e_verified.grid(row=3, column=1)


            tk.Button(frame_new_acc, text="Add Account", command=self.add_account).grid(row=4, column=0, columnspan=2, pady=5)

        frame_log = tk.LabelFrame(self.root, text="Transaction Log", padx=10, pady=10)
        frame_log.pack(fill="both", padx=10, pady=10, expand=True)

        self.log_box = tk.Text(frame_log, height=15)
        self.log_box.pack(fill="both", expand=True)


    def get_user_balance(self):
        """
        Return the balance of the currently logged-in user
        :return: balance of the currently logged-in user
        """
        with self.p.accounts_lock:
            acc = self.p.accounts.get(self.user_account_id)
            return acc.balance if acc else 0


    def logout(self):
        """
        Logs out user and opens login window
        """
        self.user_account_id = None
        self.is_admin = False
        for widget in self.root.winfo_children():
            widget.destroy()
        self.show_login()


    def send_tx(self):
        """
        Submit a new transaction from the logged-in user
        - Read values from input fields
        - Call PaymentsWorkers.submit()
        - Display success or error
        """
        try:
            t = int(self.e_to.get())
            amt = int(self.e_amount.get())
            self.p.submit(self.user_account_id, t, amt)
            messagebox.showinfo("OK", "Transaction submitted")
        except Exception as e:
            messagebox.showerror("Error", str(e))


    def add_account(self):
        """
        Add a new account
        - Validate input fields
        - Create new Account and assignes ID
        """
        try:
            owner = self.e_owner.get()
            balance = int(self.e_balance.get())
            verified = bool(int(self.e_verified.get()))
            password = self.e_password_new.get().strip()

            if not owner:
                messagebox.showerror("Error", "Owner name cannot be empty")
                return

            if not password:
                messagebox.showerror("Error", "Password cannot be empty")
                return

            if owner in self.user_credentials:
                messagebox.showerror("Error", f"Username '{owner}' already exists")
                return

            with self.p.accounts_lock:
                new_id = max(self.p.accounts.keys()) + 1
                self.p.accounts[new_id] = Account(owner, balance, verified)


            self.user_credentials[owner] = (new_id, password)

            messagebox.showinfo("OK", f"Account created with ID={new_id}")
            self.update_accounts()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def update_accounts(self):
        """
        Update the admin accounts table
        - Refreshes balances and verification
        - Does nothing if user is not admin
        """
        if not self.is_admin:
            return

        self.accounts_table.delete(*self.accounts_table.get_children())
        with self.p.accounts_lock:
            for acc_id, acc in self.p.accounts.items():
                self.accounts_table.insert("", "end", values=(acc_id, acc.owner, acc.balance, acc.verified))
        self.root.after(1000, self.update_accounts)


    def update_log(self):
        """
        Refresh transaction log displayed in the GUI
        - Admin sees all logs
        - Users see only logs involving their account
        - Updates balance label in user mode
        """
        if not hasattr(self, 'log_box') or not self.log_box.winfo_exists():
            return

        self.log_box.delete(1.0, tk.END)

        if self.is_admin:
            entries = self.p.transactions_log
        elif self.user_account_id:
            entries = [e for e in self.p.transactions_log
                       if e["from"] == self.user_account_id or e["to"] == self.user_account_id]
        else:
            entries = []

        for entry in entries:
            self.log_box.insert(tk.END, json.dumps(entry) + "\n")

        if self.user_account_id and hasattr(self, 'balance_label') and self.balance_label.winfo_exists():
            self.balance_label.config(text=f"Balance: {self.get_user_balance()}")

        self.root.after(500, self.update_log)


    def on_close(self):
        """
        Safely shut down the worker threads and close the application
        """
        self.p.stop()
        self.root.destroy()



root = tk.Tk()
App(root)
root.mainloop()
