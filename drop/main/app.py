import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import psycopg2
import os
from datetime import datetime
from queue import Queue

# PostgreSQL Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',
    'database': 'budget_db'
}

class ClothingShopManager:
    def __init__(self, root):
        self.root = root
        self.queue = Queue()
        self.create_ui()
        self.process_queue()
        self.init_database()
        self.load_transactions()
        self.update_summary()

    def init_database(self):
        """Initialize the PostgreSQL database"""
        self.status_var = tk.StringVar(value="Connecting to PostgreSQL...")
        try:
            self.conn = psycopg2.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                dbname=DB_CONFIG['database']
            )
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                clothing_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                transaction_type TEXT NOT NULL,
                payment_method TEXT NOT NULL,
                category TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )''')
            self.conn.commit()
            self.status_var.set("PostgreSQL database initialized successfully")
        except Exception as e:
            self.status_var.set(f"PostgreSQL Error: {e}")

    def add_transaction(self):
        """Add a new transaction to the PostgreSQL database"""
        clothing_type = self.clothing_type_var.get().strip()
        quantity = int(self.quantity_var.get().strip())
        amount = float(self.amount_var.get().strip())
        transaction_type = "Credit" if self.transaction_type_var.get() == "Credited" else "Debit"
        payment_method = self.payment_method_var.get()
        category = self.category_var.get()
        timestamp = datetime.now()
        
        try:
            self.cursor.execute('''
            INSERT INTO transactions (clothing_type, quantity, amount, transaction_type, payment_method, category, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (clothing_type, quantity, amount, transaction_type, payment_method, category, timestamp))
            self.conn.commit()
            self.status_var.set("Transaction added successfully")
            self.load_transactions()
            self.update_summary()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add transaction: {e}")
            self.status_var.set(f"Error: {e}")
    
    def load_transactions(self):
        """Load transactions from the PostgreSQL database"""
        self.status_var.set("Loading transactions...")
        self.cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
        transactions = self.cursor.fetchall()
        # Display logic for transactions in Treeview (not included here)

    def update_summary(self):
        """Update the summary display"""
        self.status_var.set("Updating summary...")
        self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE transaction_type = 'Credit'")
        total_income = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT SUM(amount) FROM transactions WHERE transaction_type = 'Debit'")
        total_expense = self.cursor.fetchone()[0] or 0
        net_profit = total_income - total_expense
        self.status_var.set(f"Summary Updated: Income ₹{total_income}, Expenses ₹{total_expense}, Profit ₹{net_profit}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ClothingShopManager(root)
    root.mainloop()
