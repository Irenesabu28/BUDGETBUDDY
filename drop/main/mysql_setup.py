import tkinter as tk
from tkinter import ttk
import mysql.connector
import configparser
from pathlib import Path

class MySQLSetup:
    def __init__(self, parent):
        self.parent = parent
        
        # Create a new window
        self.window = tk.Toplevel(parent)
        self.window.title("MySQL Setup - DROP")
        self.window.geometry("500x400")
        self.window.minsize(500, 400)
        self.window.grab_set()  # Make window modal
        
        # Configure style
        style = ttk.Style()
        bg_color = "#f5f5f5"
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10))
        style.configure("TEntry", font=("Arial", 10))
        
        # Create main frame
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create form
        ttk.Label(main_frame, text="MySQL Configuration", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Host
        ttk.Label(form_frame, text="Host:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.host_var = tk.StringVar(value="localhost")
        ttk.Entry(form_frame, textvariable=self.host_var, width=30).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Port
        ttk.Label(form_frame, text="Port:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.port_var = tk.StringVar(value="3306")
        ttk.Entry(form_frame, textvariable=self.port_var, width=30).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Database
        ttk.Label(form_frame, text="Database:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.database_var = tk.StringVar(value="clothing_shop")
        ttk.Entry(form_frame, textvariable=self.database_var, width=30).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # User
        ttk.Label(form_frame, text="User:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.user_var = tk.StringVar(value="root")
        ttk.Entry(form_frame, textvariable=self.user_var, width=30).grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # Password
        ttk.Label(form_frame, text="Password:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.password_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.password_var, width=30, show="*").grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        # Use MySQL checkbox
        self.use_mysql_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form_frame, text="Use MySQL (uncheck to use SQLite)", variable=self.use_mysql_var).grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(button_frame, text="Test Connection", command=self.test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Configuration", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="blue")
        status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Load existing configuration
        self.load_config()
        
        # Center the window
        self.center_window()
    
    def center_window(self):
        """Center the window on the screen"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def load_config(self):
        """Load existing configuration if available"""
        try:
            # Try to load from Python module format
            try:
                from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE, USE_MYSQL
                self.host_var.set(MYSQL_HOST)
                self.port_var.set("3306")  # Default port
                self.database_var.set(MYSQL_DATABASE)
                self.user_var.set(MYSQL_USER)
                self.password_var.set(MYSQL_PASSWORD)
                self.use_mysql_var.set(USE_MYSQL)
                self.status_var.set("Configuration loaded")
            except (ImportError, AttributeError):
                # If module format fails, try ConfigParser format
                config = configparser.ConfigParser()
                config.read('config.py')
                
                if 'mysql' in config:
                    self.host_var.set(config['mysql'].get('host', 'localhost'))
                    self.port_var.set(config['mysql'].get('port', '3306'))
                    self.database_var.set(config['mysql'].get('database', 'clothing_shop'))
                    self.user_var.set(config['mysql'].get('user', 'root'))
                    self.password_var.set(config['mysql'].get('password', ''))
                    self.use_mysql_var.set(config['mysql'].getboolean('use_mysql', True))
                    self.status_var.set("Configuration loaded")
        except (configparser.Error, ValueError, FileNotFoundError) as e:
            self.status_var.set(f"Could not load configuration: {e}")
    
    def test_connection(self):
        """Test the MySQL connection with the provided credentials"""
        self.status_var.set("Testing connection...")
        self.window.update_idletasks()
        
        try:
            # Get connection parameters
            host = self.host_var.get()
            port = self.port_var.get()
            user = self.user_var.get()
            password = self.password_var.get()
            database = self.database_var.get()
            
            # Try to connect
            conn = mysql.connector.connect(
                host=host,
                port=port,
                user=user,
                password=password
            )
            
            # Check if database exists, create if not
            cursor = conn.cursor()
            cursor.execute(f"SHOW DATABASES LIKE '{database}'")
            result = cursor.fetchone()
            
            if not result:
                self.status_var.set(f"Database '{database}' does not exist. Creating...")
                self.window.update_idletasks()
                cursor.execute(f"CREATE DATABASE {database}")
                self.status_var.set(f"Database '{database}' created successfully.")
            
            # Close connection
            cursor.close()
            conn.close()
            
            from tkinter import messagebox
            messagebox.showinfo("Success", "Connection successful!")
            self.status_var.set("Connection test successful")
        except mysql.connector.Error as err:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to connect: {err}")
            self.status_var.set(f"Connection test failed: {err}")
    
    def save_config(self):
        """Save the configuration to config.py"""
        try:
            # Save in Python module format
            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(f'''# MySQL Configuration
MYSQL_HOST = "{self.host_var.get()}"
MYSQL_USER = "{self.user_var.get()}"
MYSQL_PASSWORD = "{self.password_var.get()}"
MYSQL_DATABASE = "{self.database_var.get()}"
USE_MYSQL = {self.use_mysql_var.get()}
''')
            
            from tkinter import messagebox
            messagebox.showinfo("Success", "Configuration saved successfully!")
            self.status_var.set("Configuration saved")
            self.window.destroy()
        except IOError as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            self.status_var.set(f"Save failed: {e}")


if __name__ == "__main__":
    app_window = tk.Tk()
    app = MySQLSetup(app_window)
    app_window.mainloop()
