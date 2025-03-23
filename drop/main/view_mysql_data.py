import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import os
from tkcalendar import DateEntry

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

class MySQLDataViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Database Viewer - DROP")
        self.root.geometry("900x600")
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')  # Use a modern theme
        
        # Configure colors
        bg_color = "#f5f5f5"
        accent_color = "#4a6fa5"
        
        # Configure styles
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10))
        style.configure("Treeview", 
                      background=bg_color, 
                      fieldbackground=bg_color, 
                      font=("Arial", 9))
        style.configure("Treeview.Heading", 
                      font=("Arial", 10, "bold"), 
                      background=accent_color, 
                      foreground="white")
        
        # Configure alternating row colors
        self.tree_odd_row = "#e8e8e8"
        self.tree_even_row = bg_color
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create top frame for controls
        top_frame = ttk.Frame(self.main_frame)
        top_frame.pack(fill=tk.X, pady=10)
        
        # Add refresh button
        ttk.Button(top_frame, text="Refresh Data", command=self.load_data).pack(side=tk.LEFT, padx=5)
        
        # Add export button
        ttk.Button(top_frame, text="Export to CSV", command=self.export_to_csv).pack(side=tk.LEFT, padx=5)
        
        # Add database info label
        db_type = "SQLite" if DB_CONFIG.get('use_sqlite', True) else "MySQL"
        db_name = DB_CONFIG.get('database', 'clothing_shop')
        db_info = f"Database: {db_type} - {db_name}"
        ttk.Label(top_frame, text=db_info, font=("Arial", 10, "bold")).pack(side=tk.RIGHT, padx=5)
        
        # Create filter frame
        filter_frame = ttk.LabelFrame(self.main_frame, text="Filter Options", padding=10)
        filter_frame.pack(fill=tk.X, pady=5)
        
        # First row of filters
        filter_row1 = ttk.Frame(filter_frame)
        filter_row1.pack(fill=tk.X, pady=5)
        
        # Transaction type filter
        ttk.Label(filter_row1, text="Transaction Type:").pack(side=tk.LEFT, padx=(5, 5))
        self.transaction_type_var = tk.StringVar(value="All")
        transaction_type_combo = ttk.Combobox(filter_row1, textvariable=self.transaction_type_var, 
                                             values=["All", "Credit", "Debit"], width=10)
        transaction_type_combo.pack(side=tk.LEFT, padx=5)
        transaction_type_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_all_filters())
        
        # Category filter
        ttk.Label(filter_row1, text="Category:").pack(side=tk.LEFT, padx=(20, 5))
        self.category_var = tk.StringVar(value="All")
        category_combo = ttk.Combobox(filter_row1, textvariable=self.category_var, 
                                     values=["All", "Shop", "Employee"], width=10)
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_all_filters())
        
        # Payment method filter
        ttk.Label(filter_row1, text="Payment Method:").pack(side=tk.LEFT, padx=(20, 5))
        self.payment_method_var = tk.StringVar(value="All")
        payment_method_combo = ttk.Combobox(filter_row1, textvariable=self.payment_method_var, 
                                           values=["All", "Cash", "Card", "GPay", "PhonePe", "Paytm", "UPI", "Other"], width=10)
        payment_method_combo.pack(side=tk.LEFT, padx=5)
        payment_method_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_all_filters())
        
        # Second row of filters - Date filters
        filter_row2 = ttk.Frame(filter_frame)
        filter_row2.pack(fill=tk.X, pady=5)
        
        # Date filter
        ttk.Label(filter_row2, text="Filter by Date:").pack(side=tk.LEFT, padx=5)
        self.date_var = tk.StringVar()
        date_entry = DateEntry(filter_row2, textvariable=self.date_var, width=12, 
                              bg="darkblue", fg="white", borderwidth=2, 
                              date_pattern='yyyy-mm-dd')
        date_entry.pack(side=tk.LEFT, padx=5)
        
        # Date range filter
        ttk.Label(filter_row2, text="Date Range:").pack(side=tk.LEFT, padx=(20, 5))
        ttk.Label(filter_row2, text="From:").pack(side=tk.LEFT, padx=(5, 2))
        self.date_from_var = tk.StringVar()
        date_from_entry = DateEntry(filter_row2, textvariable=self.date_from_var, width=12, 
                                   bg="darkblue", fg="white", borderwidth=2, 
                                   date_pattern='yyyy-mm-dd')
        date_from_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(filter_row2, text="To:").pack(side=tk.LEFT, padx=(5, 2))
        self.date_to_var = tk.StringVar()
        date_to_entry = DateEntry(filter_row2, textvariable=self.date_to_var, width=12, 
                                 bg="darkblue", fg="white", borderwidth=2, 
                                 date_pattern='yyyy-mm-dd')
        date_to_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # Apply filters button
        ttk.Button(filter_row2, text="Apply Filters", command=self.apply_all_filters).pack(side=tk.LEFT, padx=10)
        ttk.Button(filter_row2, text="Clear Filters", command=self.clear_filters).pack(side=tk.LEFT, padx=5)
        
        # Create treeview for data display
        self.create_treeview()
        
        # Status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Load data
        self.load_data()
    
    def create_treeview(self):
        """Create the treeview to display data"""
        # Create a frame for the treeview
        tree_frame = ttk.Frame(self.main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create treeview
        self.tree = ttk.Treeview(tree_frame, 
                                yscrollcommand=y_scrollbar.set,
                                xscrollcommand=x_scrollbar.set)
        
        # Configure scrollbars
        y_scrollbar.config(command=self.tree.yview)
        x_scrollbar.config(command=self.tree.xview)
        
        # Define columns
        self.tree['columns'] = ('id', 'clothing_type', 'quantity', 'amount', 
                               'transaction_type', 'payment_method', 'category', 'timestamp')
        
        # Format columns
        self.tree.column('#0', width=0, stretch=tk.NO)
        self.tree.column('id', width=50, anchor=tk.CENTER)
        self.tree.column('clothing_type', width=150, anchor=tk.W)
        self.tree.column('quantity', width=80, anchor=tk.CENTER)
        self.tree.column('amount', width=100, anchor=tk.E)
        self.tree.column('transaction_type', width=100, anchor=tk.CENTER)
        self.tree.column('payment_method', width=120, anchor=tk.CENTER)
        self.tree.column('category', width=100, anchor=tk.CENTER)
        self.tree.column('timestamp', width=150, anchor=tk.CENTER)
        
        # Create headings
        self.tree.heading('#0', text='', anchor=tk.CENTER)
        self.tree.heading('id', text='ID', anchor=tk.CENTER)
        self.tree.heading('clothing_type', text='Clothing Type', anchor=tk.CENTER)
        self.tree.heading('quantity', text='Quantity', anchor=tk.CENTER)
        self.tree.heading('amount', text='Amount', anchor=tk.CENTER)
        self.tree.heading('transaction_type', text='Type', anchor=tk.CENTER)
        self.tree.heading('payment_method', text='Payment Method', anchor=tk.CENTER)
        self.tree.heading('category', text='Category', anchor=tk.CENTER)
        self.tree.heading('timestamp', text='Timestamp', anchor=tk.CENTER)
        
        # Pack the treeview
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Add right-click menu
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="Delete Entry", command=self.delete_selected)
        
        # Bind right-click event
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # Configure alternating row colors
        self.tree.tag_configure('even', background=self.tree_even_row)
        self.tree.tag_configure('odd', background=self.tree_odd_row)
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        # Select the item under the cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def delete_selected(self):
        """Delete the selected entry from the database"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showinfo("Info", "No item selected")
            return
        
        # Get the ID of the selected item
        item_id = self.tree.item(selected_item[0], 'values')[0]
        
        # Confirm deletion
        if not messagebox.askyesno("Confirm", f"Are you sure you want to delete entry #{item_id}?"):
            return
        
        try:
            # Connect to the database
            conn = self.connect_to_db()
            cursor = conn.cursor()
            
            # Delete the entry
            cursor.execute("DELETE FROM transactions WHERE id = %s", (item_id,))
            conn.commit()
            
            # Close the connection
            cursor.close()
            conn.close()
            
            # Refresh the data
            self.load_data()
            
            self.status_var.set(f"Entry #{item_id} deleted successfully")
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Failed to delete entry: {err}")
            self.status_var.set(f"Error: {err}")
    
    def connect_to_db(self):
        """Connect to the MySQL database"""
        try:
            if DB_CONFIG['use_sqlite']:
                conn = sqlite3.connect('clothing_shop.db')
            else:
                conn = mysql.connector.connect(
                    host=DB_CONFIG['host'],
                    user=DB_CONFIG['user'],
                    password=DB_CONFIG['password'],
                    database=DB_CONFIG['database']
                )
            return conn
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Failed to connect to MySQL: {err}")
            self.status_var.set(f"Database connection error: {err}")
            raise
    
    def load_data(self):
        """Load data from MySQL database"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            # Connect to the database
            conn = self.connect_to_db()
            cursor = conn.cursor()
            
            # Get all transactions
            if DB_CONFIG['use_sqlite']:
                cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
            else:
                cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            
            # Store all data for filtering
            self.all_data = rows
            
            # Close the connection
            cursor.close()
            conn.close()
            
            # Apply filters
            self.apply_all_filters()
            
            self.status_var.set(f"Loaded {len(rows)} transactions from database")
            
        except mysql.connector.Error as err:
            self.status_var.set(f"Error loading data: {err}")
    
    def apply_all_filters(self):
        """Apply all filters to the data"""
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        if not hasattr(self, 'all_data'):
            return
        
        # Get filter values
        transaction_type_filter = self.transaction_type_var.get()
        category_filter = self.category_var.get()
        payment_method_filter = self.payment_method_var.get()
        date_filter = self.date_var.get()
        date_from_filter = self.date_from_var.get()
        date_to_filter = self.date_to_var.get()
        
        # Apply filters
        filtered_data = []
        for row in self.all_data:
            # Check transaction type filter
            if transaction_type_filter != "All":
                # Case-insensitive comparison for transaction type
                if transaction_type_filter.lower() not in str(row[4]).lower():
                    continue
            
            # Check category filter
            if category_filter != "All":
                # Case-insensitive comparison for category
                if category_filter.lower() not in str(row[6]).lower():
                    continue
            
            # Check payment method filter
            if payment_method_filter != "All":
                # Case-insensitive comparison for payment method
                if payment_method_filter.lower() not in str(row[5]).lower():
                    continue
            
            # Get timestamp as datetime object
            timestamp = row[7]
            timestamp_dt = None
            
            # Handle different timestamp formats
            if isinstance(timestamp, str):
                try:
                    # Try standard format
                    timestamp_dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        # Try alternative format
                        timestamp_dt = datetime.strptime(timestamp, "%Y-%m-%d")
                    except ValueError:
                        # If all parsing fails, skip this row for date filtering
                        continue
            elif isinstance(timestamp, datetime):
                timestamp_dt = timestamp
            else:
                # Skip this row for date filtering if timestamp is not in a recognizable format
                continue
            
            # Check date filter
            if date_filter:
                try:
                    # Convert date filter to datetime object
                    date_filter_dt = datetime.strptime(date_filter, "%Y-%m-%d")
                    
                    # Check if timestamp matches date filter
                    if timestamp_dt.date() != date_filter_dt.date():
                        continue
                except ValueError:
                    # If date parsing fails, ignore this filter
                    pass
            
            # Check date range filter
            if date_from_filter and date_to_filter:
                try:
                    # Convert date from filter to datetime object
                    date_from_dt = datetime.strptime(date_from_filter, "%Y-%m-%d")
                    
                    # Convert date to filter to datetime object
                    date_to_dt = datetime.strptime(date_to_filter, "%Y-%m-%d")
                    
                    # Add one day to date_to_dt to make the range inclusive
                    date_to_dt = date_to_dt + timedelta(days=1)
                    
                    # Check if timestamp is within date range
                    if timestamp_dt.date() < date_from_dt.date() or timestamp_dt.date() >= date_to_dt.date():
                        continue
                except ValueError:
                    # If date parsing fails, ignore this filter
                    pass
            
            filtered_data.append(row)
        
        # Display the filtered data
        self.display_data(filtered_data)
    
    def clear_filters(self):
        """Clear all filters"""
        self.transaction_type_var.set("All")
        self.category_var.set("All")
        self.payment_method_var.set("All")
        self.date_var.set("")
        self.date_from_var.set("")
        self.date_to_var.set("")
        self.apply_all_filters()
    
    def display_data(self, data):
        # Insert filtered data
        for i, row in enumerate(data):
            # Format amount with 2 decimal places
            formatted_amount = f"₹{row[3]:.2f}"
            
            # Format timestamp
            timestamp = row[7]
            if isinstance(timestamp, str):
                try:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    dt = datetime.now()  # Fallback
            else:
                dt = timestamp
                
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")
            
            # Insert into treeview with alternating row colors
            tag = 'even' if i % 2 == 0 else 'odd'
            self.tree.insert("", tk.END, values=(
                row[0],  # id
                row[1],  # clothing_type
                row[2],  # quantity
                formatted_amount,  # amount
                row[4],  # transaction_type
                row[5],  # payment_method
                row[6],  # category
                date_str,  # date
                time_str   # time
            ), tags=(tag,))
        
        # Update status
        self.status_var.set(f"Displaying {len(data)} records")
    
    def export_to_csv(self):
        """Export the current view to a CSV file"""
        try:
            # Get the data from the treeview
            data = []
            columns = ['ID', 'Clothing Type', 'Quantity', 'Amount', 
                      'Transaction Type', 'Payment Method', 'Category', 'Timestamp']
            
            for item in self.tree.get_children():
                values = self.tree.item(item, 'values')
                data.append(values)
            
            # Create a DataFrame
            df = pd.DataFrame(data, columns=columns)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"clothing_shop_data_{timestamp}.csv"
            
            # Save to CSV
            df.to_csv(filename, index=False)
            
            self.status_var.set(f"Data exported to {filename}")
            messagebox.showinfo("Export Successful", f"Data has been exported to {filename}")
            
        except Exception as e:
            self.status_var.set(f"Export failed: {e}")
            messagebox.showerror("Export Error", f"Failed to export data: {e}")

if __name__ == "__main__":
    # Check if pandas is installed
    try:
        import pandas as pd
    except ImportError:
        print("Pandas is required for this tool. Installing pandas...")
        import subprocess
        subprocess.call(['pip', 'install', 'pandas'])
        import pandas as pd
    
    root = tk.Tk()
    app = MySQLDataViewer(root)
    root.mainloop()
