import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import pandas as pd
import warnings

# Suppress the pandas SQLAlchemy warning since we are using mysql-connector
warnings.filterwarnings('ignore', category=UserWarning, module='pandas')

# Load environment variables from .env file
load_dotenv()

def get_connection():
    """Establish and return a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "ecommerce_db"),
            port=os.getenv("DB_PORT", "3306")
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def fetch_data(query, params=None):
    """Utility function to run a SELECT query and return a Pandas DataFrame."""
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    try:
        if params:
            df = pd.read_sql(query, conn, params=params)
        else:
            df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()
    finally:
        if conn.is_connected():
            conn.close()

def place_order(customer_id, items):
    """
    Places a new order using SQL Transactions.
    items: list of tuples (product_id, quantity, price)
    Returns: (success_bool, message_string)
    """
    conn = get_connection()
    if conn is None:
        return False, "Database connection failed"
    
    try:
        cursor = conn.cursor()
        
        # 1. Start transaction 
        conn.start_transaction()
        
        # 2. Calculate the total order amount
        total_amount = sum([qty * price for _, qty, price in items])
        
        # 3. Create the order record
        cursor.execute(
            "INSERT INTO Orders (customer_id, total_amount) VALUES (%s, %s)",
            (customer_id, total_amount)
        )
        order_id = cursor.lastrowid
        
        # 4. Process each item
        for product_id, quantity, price in items:
            # First, explicitly check stock to avoid breaking constraints unnecessarily
            cursor.execute("SELECT stock, name FROM Products WHERE id = %s FOR UPDATE", (product_id,))
            result = cursor.fetchone()
            
            if not result:
                raise Exception(f"Product ID {product_id} not found")
                
            stock, name = result
            if stock < quantity:
                raise Exception(f"Insufficient stock for {name}. Only {stock} remaining.")
                
            # Insert the item (Trigger will fire here and reduce stock)
            cursor.execute(
                "INSERT INTO Order_Items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)",
                (order_id, product_id, quantity, price)
            )
            
        # 5. Commit transaction if all steps succeed
        conn.commit()
        return True, f"Order #{order_id} placed successfully! Total: ${total_amount:.2f}"
        
    except Exception as e:
        # 6. Rollback everything on ANY failure to protect data integrity
        conn.rollback()
        return False, str(e)
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def add_customer(name, email):
    """Inserts a new customer (client) into the database."""
    conn = get_connection()
    if conn is None:
        return False, "Database connection failed"
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Customers (name, email) VALUES (%s, %s)", (name, email))
        conn.commit()
        return True, f"Successfully registered new client: {name}!"
    except Error as e:
        return False, f"Failed to add client: {e}"
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
