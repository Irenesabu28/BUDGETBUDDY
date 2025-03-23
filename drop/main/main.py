import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
import mysql.connector
import os
from datetime import datetime
import threading
from queue import Queue
import configparser
import subprocess

# Import MySQL configuration
try:
    from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, USE_MYSQL
    DB_CONFIG = {
        'host': MYSQL_HOST,
        'user': MYSQL_USER,
        'password': MYSQL_PASSWORD,
        'database': MYSQL_DATABASE,
        'use_sqlite': not USE_MYSQL
    }
except ImportError:
    # Default configuration if config.py doesn't exist
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'clothing_shop',
        'use_sqlite': True
    }

class ClothingShopManager:
    def __init__(self, root):
        """Initialize the application"""
        self.root = root
        
        # Create a queue for thread-safe operations
        self.queue = Queue()
        
        # Create UI
        self.create_ui()
        
        # Start the queue processing
        self.process_queue()
        
    def create_ui(self):
        """Create the user interface"""
        # Set window properties
        self.root.title("DROP")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)  # Set minimum window size
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')  # Use a modern theme
        
        # Configure colors
        bg_color = "#f5f5f5"
        accent_color = "#4a6fa5"
        
        # Configure styles
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10), background=accent_color)
        style.configure("TEntry", font=("Arial", 10))
        style.configure("Heading.TLabel", font=("Arial", 12, "bold"))
        style.configure("Status.TLabel", foreground="blue", background=bg_color)
        
        # Configure Treeview
        style.configure("Treeview", 
                        background=bg_color, 
                        fieldbackground=bg_color, 
                        font=("Arial", 9))
        style.configure("Treeview.Heading", 
                        font=("Arial", 10, "bold"), 
                        background=accent_color, 
                        foreground="white")
        
        # Configure alternating row colors - using proper tag-based approach instead of invalid state names
        self.tree_odd_row = "#e8e8e8"
        self.tree_even_row = bg_color
        
        # Main container
        main_container = ttk.Frame(self.root, padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create header
        self.create_header(main_container)
        
        # Create left panel for form
        left_panel = ttk.Frame(main_container, padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Create form
        self.create_form(left_panel)
        
        # Create right panel for data
        right_panel = ttk.Frame(main_container, padding=10)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create data display
        self.create_data_frame(right_panel)
        
        # Create summary frame
        summary_frame = ttk.Frame(left_panel)
        summary_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create summary display
        self.create_summary_display(summary_frame)
        
        # Create status bar
        status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(5, 2))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_bar, textvariable=self.status_var, style="Status.TLabel")
        status_label.pack(side=tk.LEFT)
        
        # Version label
        version_label = ttk.Label(status_bar, text="v1.2.0", style="Status.TLabel")
        version_label.pack(side=tk.RIGHT)
        
        # Initialize database
        self.init_database()
        
        # Load transactions
        self.load_transactions()
        
        # Update summary
        self.update_summary()
        
    def create_header(self, parent):
        """Create the header with title and logo"""
        header_frame = ttk.Frame(parent, padding=10)
        header_frame.pack(fill=tk.X, pady=5)
        
        # Title
        title_label = ttk.Label(header_frame, text="DROP", 
                               font=("Arial", 18, "bold"), foreground="#4a6fa5")
        title_label.pack(side=tk.LEFT)
        
        # Buttons frame
        buttons_frame = ttk.Frame(header_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        # MySQL Setup button
        mysql_button = ttk.Button(buttons_frame, text="MySQL Setup", 
                                command=self.open_mysql_setup)
        mysql_button.pack(side=tk.LEFT, padx=5)
        
        # Export button
        export_button = ttk.Button(buttons_frame, text="Export Data", 
                                 command=self.export_data)
        export_button.pack(side=tk.LEFT, padx=5)
        
        # View MySQL Data button
        view_mysql_button = ttk.Button(buttons_frame, text="View MySQL Data", 
                                      command=self.view_mysql_data)
        view_mysql_button.pack(side=tk.LEFT, padx=5)
        
    def create_form(self, parent):
        """Create the form for adding transactions"""
        form_frame = ttk.LabelFrame(parent, text="Add Transaction", padding=10)
        form_frame.pack(fill=tk.BOTH, expand=False)
        
        # Clothing Type
        ttk.Label(form_frame, text="Clothing Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.clothing_type_var = tk.StringVar()
        clothing_types = ["Shirt", "T-shirt", "Sweatshirt", "Jackets", "Jeans", "Corduroy", "Formals", 
                         "Jersy", "Jersy Shorts", "Hoodie", "Denim Jacket", "Womens(kg)"]
        ttk.Combobox(form_frame, textvariable=self.clothing_type_var, 
                   values=clothing_types, width=18, state="readonly").grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Quantity
        ttk.Label(form_frame, text="Quantity:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.quantity_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.quantity_var, width=20).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Amount
        ttk.Label(form_frame, text="Amount (₹):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.amount_var, width=20).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Transaction Type
        ttk.Label(form_frame, text="Transaction Type:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.transaction_type_var = tk.StringVar(value="Credited")
        transaction_frame = ttk.Frame(form_frame)
        transaction_frame.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(transaction_frame, text="Credited", value="Credited", 
                      variable=self.transaction_type_var).pack(side=tk.LEFT)
        ttk.Radiobutton(transaction_frame, text="Debited", value="Debited", 
                      variable=self.transaction_type_var).pack(side=tk.LEFT)
        
        # Payment Method
        ttk.Label(form_frame, text="Payment Method:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.payment_method_var = tk.StringVar(value="Cash")
        payment_methods = ["Cash", "GPay", "Card", "UPI", "Other"]
        ttk.Combobox(form_frame, textvariable=self.payment_method_var, 
                   values=payment_methods, width=18, state="readonly").grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.category_var = tk.StringVar(value="Shop")
        category_frame = ttk.Frame(form_frame)
        category_frame.grid(row=5, column=1, sticky="w", padx=5, pady=5)
        ttk.Radiobutton(category_frame, text="Shop", value="Shop", 
                      variable=self.category_var).pack(side=tk.LEFT)
        ttk.Radiobutton(category_frame, text="Employee", value="Employee", 
                      variable=self.category_var).pack(side=tk.LEFT)
        
        # Add Button
        self.add_button = ttk.Button(form_frame, text="Add Transaction", command=self.add_transaction)
        self.add_button.grid(row=6, column=0, columnspan=2, padx=5, pady=10)
        
        # Filter section
        filter_frame = ttk.LabelFrame(parent, text="Filter Transactions", padding=10)
        filter_frame.pack(fill=tk.X, pady=10)
        
        # Date filter
        ttk.Label(filter_frame, text="Date:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.filter_date = DateEntry(filter_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2, date_pattern='yyyy-mm-dd')
        self.filter_date.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Transaction type filter
        ttk.Label(filter_frame, text="Type:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.filter_type_var = tk.StringVar(value="All")
        type_options = ["All", "Credited", "Debited"]
        ttk.Combobox(filter_frame, textvariable=self.filter_type_var, 
                   values=type_options, width=10, state="readonly").grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Filter buttons
        button_frame = ttk.Frame(filter_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=5)
        
        ttk.Button(button_frame, text="Apply Filter", 
                 command=lambda: self.load_transactions(
                     filter_date=self.filter_date.get_date(),
                     filter_type=self.filter_type_var.get()
                 )).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Show All", 
                 command=self.load_transactions).pack(side=tk.LEFT, padx=5)
        
    def create_data_frame(self, parent):
        """Create the frame for displaying transaction data"""
        data_frame = ttk.LabelFrame(parent, text="Transaction Records")
        data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add search bar at the top
        search_frame = ttk.Frame(data_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_transactions)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(search_frame, text="Clear", 
                 command=lambda: self.search_var.set("")).pack(side=tk.RIGHT, padx=5)
        
        # Create Treeview
        columns = ("id", "clothing_type", "quantity", "amount", "transaction_type", "payment_method", "category", "date", "time")
        self.tree = ttk.Treeview(data_frame, columns=columns, show="headings")
        
        # Define headings
        self.tree.heading("id", text="ID")
        self.tree.heading("clothing_type", text="Clothing Type")
        self.tree.heading("quantity", text="Quantity")
        self.tree.heading("amount", text="Amount (₹)")
        self.tree.heading("transaction_type", text="Transaction Type")
        self.tree.heading("payment_method", text="Payment Method")
        self.tree.heading("category", text="Category")
        self.tree.heading("date", text="Date")
        self.tree.heading("time", text="Time")
        
        # Define columns width
        self.tree.column("id", width=50)
        self.tree.column("clothing_type", width=100)
        self.tree.column("quantity", width=70)
        self.tree.column("amount", width=100)
        self.tree.column("transaction_type", width=120)
        self.tree.column("payment_method", width=120)
        self.tree.column("category", width=100)
        self.tree.column("date", width=100)
        self.tree.column("time", width=100)
        
        # Configure tags for alternating row colors
        self.tree.tag_configure('odd', background=self.tree_odd_row)
        self.tree.tag_configure('even', background=self.tree_even_row)
        
        # Configure tags for search filtering
        self.tree.tag_configure('visible')
        self.tree.tag_configure('hidden', background='gray', foreground='light gray')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(expand=True, fill=tk.BOTH)
        
        # Add delete button
        ttk.Button(data_frame, text="Delete Selected", command=self.delete_transaction).pack(pady=5)
        
    def create_summary_display(self, parent):
        """Create the frame for displaying summary information"""
        # Create the frame
        summary_frame = ttk.Frame(parent)
        summary_frame.pack(fill=tk.BOTH, expand=True)
        
        # Summary period selection
        period_frame = ttk.Frame(summary_frame)
        period_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(period_frame, text="Summary Period:").pack(side=tk.LEFT, padx=5)
        self.summary_period_var = tk.StringVar(value="Month")
        ttk.Radiobutton(period_frame, text="Day", variable=self.summary_period_var, value="Day", 
                      command=self.update_summary).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(period_frame, text="Month", variable=self.summary_period_var, value="Month", 
                      command=self.update_summary).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(period_frame, text="Year", variable=self.summary_period_var, value="Year", 
                      command=self.update_summary).pack(side=tk.LEFT, padx=5)
        
        # Summary Treeview
        tree_frame = ttk.Frame(summary_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("clothing_type", "quantity_sold", "total_sales")
        self.summary_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=6)
        
        # Define headings
        self.summary_tree.heading("clothing_type", text="Clothing Type")
        self.summary_tree.heading("quantity_sold", text="Quantity Sold")
        self.summary_tree.heading("total_sales", text="Total Sales (₹)")
        
        # Define columns width
        self.summary_tree.column("clothing_type", width=100)
        self.summary_tree.column("quantity_sold", width=100)
        self.summary_tree.column("total_sales", width=120)
        
        # Configure tags for alternating row colors
        self.summary_tree.tag_configure('odd', background=self.tree_odd_row)
        self.summary_tree.tag_configure('even', background=self.tree_even_row)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.summary_tree.yview)
        self.summary_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.summary_tree.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        # Totals frame
        totals_frame = ttk.Frame(summary_frame)
        totals_frame.pack(fill=tk.X, pady=10)
        
        # Total summary labels
        ttk.Label(totals_frame, text="Total Income:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.total_income_var = tk.StringVar(value="₹0.00")
        ttk.Label(totals_frame, textvariable=self.total_income_var, 
                font=("Arial", 10, "bold"), foreground="#008800").grid(row=0, column=1, padx=5, pady=2, sticky="w")
        
        ttk.Label(totals_frame, text="Total Expenses:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.total_expense_var = tk.StringVar(value="₹0.00")
        ttk.Label(totals_frame, textvariable=self.total_expense_var, 
                font=("Arial", 10, "bold"), foreground="#cc0000").grid(row=1, column=1, padx=5, pady=2, sticky="w")
        
        ttk.Label(totals_frame, text="Net Profit:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
        self.net_profit_var = tk.StringVar(value="₹0.00")
        ttk.Label(totals_frame, textvariable=self.net_profit_var, 
                font=("Arial", 11, "bold")).grid(row=2, column=1, padx=5, pady=2, sticky="w")
        
    def init_database(self):
        """Initialize the database connection based on configuration settings"""
        # Check if we should use SQLite (from config)
        use_sqlite = DB_CONFIG.get('use_sqlite', True)
        
        if use_sqlite:
            # Use SQLite as the primary database
            self._init_sqlite_database()
        else:
            # Try to use MySQL first, fall back to SQLite if it fails
            try:
                self._init_mysql_database()
            except Exception as e:
                messagebox.showwarning("MySQL Connection Failed", 
                                     f"Could not connect to MySQL: {e}\n\nFalling back to SQLite database.")
                self._init_sqlite_database()
    
    def _init_sqlite_database(self):
        """Initialize SQLite database"""
        self.status_var.set("Connecting to SQLite database...")
        self.root.update_idletasks()
        
        self.using_mysql = False
        
        # Create SQLite database directory if it doesn't exist
        sqlite_path = 'shop_data/transactions.db'
        db_dir = os.path.dirname(sqlite_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            
        self.conn = sqlite3.connect(sqlite_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Create transactions table for SQLite
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clothing_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            category TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
        ''')
        self.conn.commit()
        self.status_var.set("SQLite database initialized successfully")
    
    def _init_mysql_database(self):
        """Initialize MySQL database"""
        self.status_var.set("Connecting to MySQL database...")
        self.root.update_idletasks()
        
        self.using_mysql = True
        
        try:
            # MySQL connection parameters from config file
            self.conn = mysql.connector.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                connection_timeout=5
            )
            
            cursor = self.conn.cursor()
            
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            cursor.execute(f"USE {DB_CONFIG['database']}")
            
            # Create transactions table for MySQL
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                clothing_type VARCHAR(255) NOT NULL,
                quantity INT NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                transaction_type VARCHAR(50) NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                category VARCHAR(50) NOT NULL,
                timestamp DATETIME NOT NULL
            )
            ''')
            self.conn.commit()
            
            # Set cursor for future operations
            self.cursor = self.conn.cursor()
            self.status_var.set("MySQL database initialized successfully")
            
        except mysql.connector.Error as err:
            self.status_var.set(f"MySQL Error: {err}")
            raise Exception(f"MySQL connection failed: {err}")
    
    def process_queue(self):
        """Process the queue of database operations"""
        try:
            while not self.queue.empty():
                task = self.queue.get(0)
                task()
                self.queue.task_done()
        except Exception as e:
            print(f"Error processing queue: {e}")
        finally:
            # Schedule to run again
            self.root.after(100, self.process_queue)

    def execute_db_operation(self, operation, *args, **kwargs):
        """Execute a database operation in a thread-safe manner"""
        def task():
            try:
                operation(*args, **kwargs)
            except Exception as e:
                print(f"Database operation error: {e}")
                self.status_var.set(f"Error: {e}")
        
        self.queue.put(task)

    def add_transaction(self):
        """Add a new transaction to the database"""
        # Get form values
        clothing_type = self.clothing_type_var.get().strip()
        quantity_str = self.quantity_var.get().strip()
        amount_str = self.amount_var.get().strip()
        transaction_type = "Credit" if self.transaction_type_var.get() == "Credited" else "Debit"
        payment_method = self.payment_method_var.get()
        category = self.category_var.get()
        
        # Validate inputs
        if not clothing_type:
            messagebox.showerror("Error", "Please enter clothing type")
            return
        
        try:
            quantity = int(quantity_str)
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid quantity (positive integer)")
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount (positive number)")
            return
        
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Disable the add button to prevent double submissions
        self.add_button.configure(state="disabled")
        self.status_var.set("Adding transaction...")
        self.root.update_idletasks()
        
        # Define the database operation
        def db_operation():
            try:
                if self.using_mysql:
                    # Insert into MySQL
                    self.cursor.execute('''
                    INSERT INTO transactions 
                    (clothing_type, quantity, amount, transaction_type, payment_method, category, timestamp)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (clothing_type, quantity, amount, transaction_type, payment_method, category, timestamp))
                else:
                    # Insert into SQLite
                    self.cursor.execute('''
                    INSERT INTO transactions 
                    (clothing_type, quantity, amount, transaction_type, payment_method, category, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (clothing_type, quantity, amount, transaction_type, payment_method, category, timestamp))
                    self.conn.commit()
                
                # Clear form fields
                self.clothing_type_var.set("")
                self.quantity_var.set("")
                self.amount_var.set("")
                
                # Update data display
                self.load_transactions()
                self.update_summary()
                
                # Re-enable the add button
                self.root.after(0, lambda: self.add_button.configure(state="normal"))
                self.status_var.set("Transaction added successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add transaction: {e}")
                self.root.after(0, lambda: self.add_button.configure(state="normal"))
                self.status_var.set(f"Error: {e}")
        
        # Execute the operation
        self.execute_db_operation(db_operation)

    def load_transactions(self, filter_date=None, filter_type=None):
        """Load transactions from the database"""
        self.status_var.set("Loading transactions...")
        
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Define the database operation
        def db_operation():
            try:
                # Build the query based on filters
                query = "SELECT * FROM transactions"
                params = []
                
                # Apply filters if provided
                if filter_date or filter_type:
                    query += " WHERE"
                    
                    if filter_date:
                        query += " DATE(timestamp) = ?"
                        params.append(filter_date)
                        
                        if filter_type:
                            query += " AND"
                    
                    if filter_type:
                        query += " transaction_type = ?"
                        params.append(filter_type)
                
                # Order by timestamp
                query += " ORDER BY timestamp DESC"
                
                # Limit to 100 records for performance
                query += " LIMIT 100"
                
                # Execute the query
                if self.using_mysql:
                    # Convert ? to %s for MySQL
                    query = query.replace("?", "%s")
                    self.cursor.execute(query, params)
                else:
                    self.cursor.execute(query, params)
                
                # Get the results
                transactions = self.cursor.fetchall()
                
                # Insert into treeview with alternating row colors
                for i, transaction in enumerate(transactions):
                    # Format the timestamp into date and time
                    try:
                        timestamp = transaction[7]  # Assuming timestamp is at index 7
                        if isinstance(timestamp, str):
                            # Parse the timestamp string
                            dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                        else:
                            # Already a datetime object
                            dt = timestamp
                            
                        date_str = dt.strftime("%Y-%m-%d")
                        time_str = dt.strftime("%H:%M:%S")
                    except Exception as e:
                        # Fallback if timestamp parsing fails
                        date_str = str(timestamp).split()[0] if timestamp else "N/A"
                        time_str = str(timestamp).split()[1] if timestamp and len(str(timestamp).split()) > 1 else "N/A"
                
                    # Create values tuple with separate date and time
                    values = (
                        transaction[0],  # id
                        transaction[1],  # clothing_type
                        transaction[2],  # quantity
                        f"₹{float(transaction[3]):.2f}",  # amount
                        transaction[4],  # transaction_type
                        transaction[5],  # payment_method
                        transaction[6],  # category
                        date_str,        # date
                        time_str         # time
                    )
                    
                    # Apply alternating row colors using tags
                    tag = 'even' if i % 2 == 0 else 'odd'
                    self.tree.insert("", tk.END, values=values, tags=(tag,))
                
                # Update status
                if filter_date or filter_type:
                    filter_text = []
                    if filter_date:
                        filter_text.append(f"date: {filter_date}")
                    if filter_type:
                        filter_text.append(f"type: {filter_type}")
                    
                    self.status_var.set(f"Loaded {len(transactions)} transactions with filter: {', '.join(filter_text)}")
                else:
                    self.status_var.set(f"Loaded {len(transactions)} transactions")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load transactions: {e}")
                self.status_var.set(f"Error: {e}")
        
        # Execute the operation
        self.execute_db_operation(db_operation)

    def update_summary(self):
        """Update the summary display"""
        self.status_var.set("Updating summary...")
        
        # Clear existing data
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        
        # Define the database operation
        def db_operation():
            try:
                # Get the current date
                today = datetime.now()
                
                # Determine the period based on selection
                period = self.summary_period_var.get()
                
                # Build the query based on the period
                if self.using_mysql:
                    if period == "Day":
                        date_filter = f"DATE(timestamp) = '{today.strftime('%Y-%m-%d')}'"
                    elif period == "Month":
                        date_filter = f"YEAR(timestamp) = {today.year} AND MONTH(timestamp) = {today.month}"
                    else:  # Year
                        date_filter = f"YEAR(timestamp) = {today.year}"
                else:
                    # SQLite date functions
                    if period == "Day":
                        date_filter = f"DATE(timestamp) = '{today.strftime('%Y-%m-%d')}'"
                    elif period == "Month":
                        date_filter = f"strftime('%Y', timestamp) = '{today.strftime('%Y')}' AND strftime('%m', timestamp) = '{today.strftime('%m')}'"
                    else:  # Year
                        date_filter = f"strftime('%Y', timestamp) = '{today.strftime('%Y')}'"
                
                # Query for credited transactions (sales)
                query = f"""
                SELECT clothing_type, SUM(quantity) as total_quantity, SUM(amount) as total_amount
                FROM transactions
                WHERE {date_filter} AND transaction_type = 'Credit'
                GROUP BY clothing_type
                ORDER BY total_amount DESC
                """
                
                self.cursor.execute(query)
                sales_data = self.cursor.fetchall()
                
                # Insert into summary tree with alternating row colors
                total_income = 0
                for i, row in enumerate(sales_data):
                    clothing_type = row[0]
                    quantity = row[1]
                    amount = row[2]
                    
                    # Format amount with currency symbol
                    formatted_amount = f"₹{float(amount):.2f}"
                    
                    # Insert into treeview with alternating row colors
                    tag = 'even' if i % 2 == 0 else 'odd'
                    self.summary_tree.insert("", tk.END, values=(clothing_type, quantity, formatted_amount), tags=(tag,))
                    
                    # Add to total income
                    total_income += float(amount)
                
                # If no sales data, show a message
                if not sales_data:
                    self.summary_tree.insert("", tk.END, values=("No sales data", "", ""), tags=('even',))
                
                # Query for total expenses
                query = f"""
                SELECT SUM(amount) as total_expenses
                FROM transactions
                WHERE {date_filter} AND transaction_type = 'Debit'
                """
                
                self.cursor.execute(query)
                result = self.cursor.fetchone()
                total_expenses = float(result[0]) if result[0] is not None else 0
                
                # Calculate net profit
                net_profit = total_income - total_expenses
                
                # Update summary labels with color coding
                self.total_income_var.set(f"₹{total_income:.2f}")
                self.total_expense_var.set(f"₹{total_expenses:.2f}")
                self.net_profit_var.set(f"₹{net_profit:.2f}")
                
                # Update status
                self.status_var.set(f"Summary updated for {period.lower()}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update summary: {e}")
                self.status_var.set(f"Error: {e}")
        
        # Execute the operation
        self.execute_db_operation(db_operation)

    def open_mysql_setup(self):
        """Open the MySQL setup tool"""
        try:
            from mysql_setup import MySQLSetup
            setup = MySQLSetup(self.root)
            self.root.wait_window(setup.window)
            
            # After setup is complete, try to reconnect to the database
            self.status_var.set("Reconnecting to database...")
            self.init_database()
            self.load_transactions()
            self.update_summary()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open MySQL setup: {e}")
            self.status_var.set(f"Error: {e}")

    def export_data(self):
        """Export transaction data to CSV"""
        self.status_var.set("Exporting data...")
        
        # Define the database operation
        def db_operation():
            try:
                # Get all transactions
                if self.using_mysql:
                    self.cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
                else:
                    self.cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
                
                transactions = self.cursor.fetchall()
                
                # Get column names
                if self.using_mysql:
                    columns = [desc[0] for desc in self.cursor.description]
                else:
                    columns = [desc[0] for desc in self.cursor.description]
                
                # Create a pandas DataFrame
                import pandas as pd
                df = pd.DataFrame(transactions, columns=columns)
                
                # Ask user for save location
                from tkinter import filedialog
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    title="Save Export As"
                )
                
                if file_path:
                    # Export to CSV
                    df.to_csv(file_path, index=False)
                    self.status_var.set(f"Data exported to {file_path}")
                    messagebox.showinfo("Export Complete", f"Data has been exported to {file_path}")
                else:
                    self.status_var.set("Export cancelled")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export data: {e}")
                self.status_var.set(f"Error: {e}")
        
        # Execute the operation
        self.execute_db_operation(db_operation)

    def view_mysql_data(self):
        """Launch the MySQL data viewer"""
        try:
            self.status_var.set("Opening MySQL Data Viewer...")
            # Run the MySQL data viewer in a separate process
            subprocess.Popen(['python', 'view_mysql_data.py'], 
                           cwd=os.path.dirname(os.path.abspath(__file__)))
            self.status_var.set("MySQL Data Viewer launched")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch MySQL Data Viewer: {e}")
            self.status_var.set(f"Error: {e}")

    def delete_transaction(self):
        """Delete the selected transaction"""
        # Get selected item
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a transaction to delete")
            return
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this transaction?"):
            return
        
        # Get transaction ID
        transaction_id = self.tree.item(selected_item[0], "values")[0]
        
        # Disable the tree to prevent further selections during deletion
        self.tree.configure(selectmode="none")
        self.status_var.set("Deleting transaction...")
        
        # Define the database operation
        def db_operation():
            try:
                if self.using_mysql:
                    # Delete the transaction
                    self.cursor.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
                    
                    # Update IDs for all transactions with higher IDs
                    self.cursor.execute("""
                    SET @count = 0;
                    UPDATE transactions SET id = (@count:=@count+1) ORDER BY timestamp;
                    """)
                else:
                    # For SQLite, we need to do this in multiple steps
                    # First, delete the transaction
                    self.cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
                    self.conn.commit()
                    
                    # Then, create a temporary table and copy data with new IDs
                    self.cursor.execute("""
                    CREATE TEMPORARY TABLE temp_transactions AS 
                    SELECT NULL as id, clothing_type, quantity, amount, transaction_type, 
                           payment_method, category, timestamp 
                    FROM transactions 
                    ORDER BY timestamp;
                    """)
                    
                    # Delete all from original table
                    self.cursor.execute("DELETE FROM transactions")
                    self.conn.commit()
                    
                    # Copy back with auto-incrementing IDs
                    self.cursor.execute("""
                    INSERT INTO transactions (clothing_type, quantity, amount, transaction_type, 
                                           payment_method, category, timestamp)
                    SELECT clothing_type, quantity, amount, transaction_type, 
                           payment_method, category, timestamp
                    FROM temp_transactions;
                    """)
                    
                    # Drop the temporary table
                    self.cursor.execute("DROP TABLE temp_transactions")
                    self.conn.commit()
                
                # Refresh the data display
                self.load_transactions()
                self.update_summary()
                
                # Re-enable the tree
                self.root.after(0, lambda: self.tree.configure(selectmode="browse"))
                self.status_var.set("Transaction deleted successfully and IDs updated")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete transaction: {e}")
                self.status_var.set(f"Error: {e}")
                # Re-enable the tree
                self.root.after(0, lambda: self.tree.configure(selectmode="browse"))
        
        # Execute the operation
        self.execute_db_operation(db_operation)

    def filter_transactions(self, *args):
        """Filter transactions based on search query"""
        query = self.search_var.get().lower()
        
        if not query:
            # If search is empty, show all items with their original tags
            for i, item in enumerate(self.tree.get_children()):
                tag = 'even' if i % 2 == 0 else 'odd'
                self.tree.item(item, tags=(tag,))
        else:
            # If search has a value, show/hide based on match
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                if any(query in str(value).lower() for value in values):
                    # Item matches search, keep visible with original tag
                    i = self.tree.index(item)
                    tag = 'even' if i % 2 == 0 else 'odd'
                    self.tree.item(item, tags=(tag,))
                else:
                    # Item doesn't match search, apply hidden tag
                    self.tree.item(item, tags=('hidden',))

if __name__ == "__main__":
    root = tk.Tk()
    
    # Create the application
    app = ClothingShopManager(root)
    
    # Configure grid weights for main window
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    # Set a minimum size for the window
    root.minsize(900, 600)
    
    # Add window close handler
    def on_closing():
        """Handle window closing"""
        try:
            if hasattr(app, 'conn') and app.conn:
                app.conn.close()
        except Exception:
            pass
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the main loop
    root.mainloop()
