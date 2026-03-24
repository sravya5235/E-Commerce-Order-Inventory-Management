import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
conn = None

print("Connecting to local MySQL using password from .env...")
try:
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "")
    )
    print("Connected successfully!")
except Exception as e:
    print(f"FAILED TO CONNECT. Please ensure your password is correct in .env. Error: {e}")
    exit(1)

cursor = conn.cursor()
try:
    # Setup Schema
    cursor.execute("CREATE DATABASE IF NOT EXISTS ecommerce_db;")
    cursor.execute("USE ecommerce_db;")
    
    cursor.execute("CREATE TABLE IF NOT EXISTS Products (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL, price DECIMAL(10, 2) NOT NULL, stock INT NOT NULL);")
    cursor.execute("CREATE TABLE IF NOT EXISTS Customers (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255) NOT NULL, email VARCHAR(255) UNIQUE NOT NULL);")
    cursor.execute("CREATE TABLE IF NOT EXISTS Orders (id INT AUTO_INCREMENT PRIMARY KEY, customer_id INT NOT NULL, order_date DATETIME DEFAULT CURRENT_TIMESTAMP, total_amount DECIMAL(10, 2) NOT NULL, FOREIGN KEY (customer_id) REFERENCES Customers(id));")
    cursor.execute("CREATE TABLE IF NOT EXISTS Order_Items (id INT AUTO_INCREMENT PRIMARY KEY, order_id INT NOT NULL, product_id INT NOT NULL, quantity INT NOT NULL, price DECIMAL(10, 2) NOT NULL, FOREIGN KEY (order_id) REFERENCES Orders(id), FOREIGN KEY (product_id) REFERENCES Products(id));")
    cursor.execute("CREATE TABLE IF NOT EXISTS Alerts (id INT AUTO_INCREMENT PRIMARY KEY, product_id INT NOT NULL, alert_message VARCHAR(255) NOT NULL, created_at DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (product_id) REFERENCES Products(id));")

    # Setup Views
    cursor.execute("CREATE OR REPLACE VIEW Monthly_Revenue_View AS SELECT DATE_FORMAT(order_date, '%Y-%m') AS month, SUM(total_amount) AS total_revenue, COUNT(id) AS total_orders FROM Orders GROUP BY DATE_FORMAT(order_date, '%Y-%m') ORDER BY month DESC;")
    cursor.execute("CREATE OR REPLACE VIEW Top_Selling_Products_View AS SELECT p.name AS product_name, SUM(oi.quantity) AS total_quantity_sold, SUM(oi.quantity * oi.price) AS total_revenue FROM Order_Items oi JOIN Products p ON oi.product_id = p.id GROUP BY p.id, p.name ORDER BY total_quantity_sold DESC;")

    # Setup Trigger
    cursor.execute("DROP TRIGGER IF EXISTS after_order_item_insert")
    trigger_sql = """
    CREATE TRIGGER after_order_item_insert
    AFTER INSERT ON Order_Items
    FOR EACH ROW
    BEGIN
        DECLARE current_stock INT;
        DECLARE prod_name VARCHAR(255);
        UPDATE Products SET stock = stock - NEW.quantity WHERE id = NEW.product_id;
        SELECT stock, name INTO current_stock, prod_name FROM Products WHERE id = NEW.product_id;
        IF current_stock < 10 THEN
            INSERT INTO Alerts (product_id, alert_message) VALUES (NEW.product_id, CONCAT('Low stock alert for ', prod_name, '. Remaining stock: ', current_stock));
        END IF;
    END
    """
    cursor.execute(trigger_sql)

    # Setup Data
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("TRUNCATE TABLE Alerts;")
    cursor.execute("TRUNCATE TABLE Order_Items;")
    cursor.execute("TRUNCATE TABLE Orders;")
    cursor.execute("TRUNCATE TABLE Customers;")
    cursor.execute("TRUNCATE TABLE Products;")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
    cursor.execute("INSERT INTO Products (name, price, stock) VALUES ('Wireless Headphones', 99.99, 100), ('Mechanical Keyboard', 149.50, 50), ('Gaming Mouse', 59.99, 75), ('27-inch 4K Monitor', 299.00, 30), ('USB-C Hub', 25.00, 200), ('Laptop Stand', 35.00, 150), ('Webcam 1080p', 45.00, 60), ('Ergonomic Chair', 199.99, 15);")
    cursor.execute("INSERT INTO Customers (name, email) VALUES ('Alice Smith', 'alice@example.com'), ('Bob Johnson', 'bob@example.com'), ('Charlie Brown', 'charlie@example.com'), ('Diana Prince', 'diana@example.com');")

    conn.commit()
    print("Database `ecommerce_db` created and populated with Mock Data successfully!")

except Exception as e:
    print(f"Error during setup: {e}")
finally:
    cursor.close()
    conn.close()
