# 🛒 Real-Time E-Commerce Order & Inventory Management

An end-to-end Python and MySQL powered dashboard for simulating client orders, tracking inventory tightly in real-time, and monitoring sales metrics through an interactive Streamlit frontend.

## 🌟 Features
- **Live Sales Dashboard**: Monitor total revenue, active users, and recent transaction history.
- **SQL Transactions**: Safely processes simulated orders utilizing ACID-compliant transaction blocks protecting data integrity.
- **Automated Inventory Alerts**: Database-level triggers automatically deduct product stock and generate low-inventory warnings.
- **Client Management**: Register new clients directly through the dashboard interface synced securely with the database.

## 🛠️ Tech Stack
- **Frontend/UI:** [Streamlit](https://streamlit.io/)
- **Backend/Logic:** Python 3, Pandas
- **Database Architecture:** MySQL 
- **Connector:** `mysql-connector-python`

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sravya5235/E-Commerce-Order-Inventory-Management.git
   cd E-Commerce-Order-Inventory-Management
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Database Environment:**
   Create a `.env` file in the root directory and add your local MySQL database credentials:
   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=ecommerce_db
   DB_PORT=3306
   ```

4. **Initialize the Database:**
   Run the setup script to automatically build the schema, views, triggers, and insert mock data:
   ```bash
   python setup_db.py
   ```

## 🚀 Running the Application

Once the database is configured and seeded, launch the Streamlit frontend:
```bash
streamlit run dashboard.py
```

The application will automatically open in your default web browser on `http://localhost:8501`.
