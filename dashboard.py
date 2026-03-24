import streamlit as st
import pandas as pd
import db_manager as db
import time
import importlib

# Force sync with newest backend changes
importlib.reload(db)

st.set_page_config(page_title="E-Commerce Dashboard", layout="wide")

st.markdown("""
<style>
    /* Center the tabs */
    [data-baseweb="tab-list"] {
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# Authentication Layer
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def login_screen():
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>🔒 Operations Console Login</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>Enter credentials to access real-time metrics and order processing.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Authenticate", use_container_width=True)
            
            if submitted:
                if hasattr(db, 'verify_user'):
                    success, msg = db.verify_user(user, pw)
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.success(msg)
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("System Error: Backend verification module not ready. Please refresh.")

if not st.session_state.authenticated:
    login_screen()
    st.stop()

# --- MAIN DASHBOARD (Only visible if authenticated) ---
with st.sidebar:
    st.header("Admin Controls")
    st.info(f"Logged in as: {st.session_state.get('user', 'Unknown')}")
    st.divider()
    st.success("Database Connected")
    st.write("Welcome to the Operations Portal. Navigate through the main tabs to monitor live sales and check inventory alerts.")
    st.divider()
    st.caption("System Status: Online")
    
    st.markdown("<br>" * 10, unsafe_allow_html=True) # Push the button down
    if st.button("Logout", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>E-Commerce Order & Inventory Management</h1>", unsafe_allow_html=True)

# Define tabs for our UI
tab1, tab2, tab3 = st.tabs(["Real-Time Dashboard", "Inventory & Alerts", "Simulate Order"])

# ----------------- TAB 1: DASHBOARD -----------------
with tab1:
    col_header, col_btn = st.columns([5, 1])
    with col_header:
        st.header("Real-Time Sales Metrics")
    with col_btn:
        st.button("Refresh Data", use_container_width=True)
    
    # KPIs
    metrics_query = """
    SELECT 
        (SELECT COUNT(*) FROM Orders) as total_orders,
        (SELECT SUM(total_amount) FROM Orders) as total_revenue,
        (SELECT COUNT(*) FROM Customers) as total_customers,
        (SELECT COUNT(*) FROM Alerts) as total_alerts
    """
    metrics_df = db.fetch_data(metrics_query)
    
    if not metrics_df.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        # Add simulated deltas for a more "active dashboard" look
        total_orders = metrics_df['total_orders'].iloc[0]
        col1.metric("Total Orders", f"{total_orders}", f"+{total_orders} this month")
        
        rev = metrics_df['total_revenue'].iloc[0]
        col2.metric("Total Revenue", f"${rev:,.2f}" if pd.notnull(rev) else "$0.00", "Updated just now")
        
        total_customers = metrics_df['total_customers'].iloc[0]
        col3.metric("Total Clients", f"{total_customers}", "Active base")
        
        active_alerts = metrics_df['total_alerts'].iloc[0]
        col4.metric("Active Alerts", f"{active_alerts}", f"{-active_alerts} resolved" if active_alerts > 0 else "All systems clear", delta_color="inverse")
    
    st.divider()
    
    st.subheader("Recent Transactions")
    recent_query = """
    SELECT o.id as 'Order ID', c.name as 'Client', o.total_amount as 'Amount ($)', DATE_FORMAT(o.order_date, '%Y-%m-%d %H:%i') as 'Date'
    FROM Orders o
    JOIN Customers c ON o.customer_id = c.id
    ORDER BY o.order_date DESC
    LIMIT 5
    """
    recent_df = db.fetch_data(recent_query)
    if not recent_df.empty:
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
    else:
        st.info("No recent transactions found.")
        
    st.divider()
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Monthly Revenue")
        revenue_df = db.fetch_data("SELECT * FROM Monthly_Revenue_View")
        if not revenue_df.empty:
            st.bar_chart(data=revenue_df.set_index('month')['total_revenue'])
        else:
            st.info("No revenue data to display yet.")
            
    with col_chart2:
        st.subheader("Top Selling Products")
        top_products_df = db.fetch_data("SELECT * FROM Top_Selling_Products_View LIMIT 5")
        if not top_products_df.empty:
            st.bar_chart(data=top_products_df.set_index('product_name')['total_quantity_sold'])
        else:
            st.info("No sales data to display yet.")

# ----------------- TAB 2: INVENTORY -----------------
with tab2:
    st.header("Inventory Management")
    
    col_inv1, col_inv2 = st.columns([2, 1])
    
    with col_inv1:
        st.subheader("Current Stock Levels")
        stock_df = db.fetch_data("SELECT id, name, price, stock FROM Products ORDER BY stock ASC")
        if not stock_df.empty:
            st.dataframe(
                stock_df, 
                use_container_width=True,
                hide_index=True,
                column_config={
                    "stock": st.column_config.ProgressColumn(
                        "Stock Level",
                        help="Current inventory count",
                        format="%d",
                        min_value=0,
                        max_value=200,
                    )
                }
            )
            
    with col_inv2:
        st.subheader("Low Stock Alerts (Triggered)")
        alerts_df = db.fetch_data("SELECT alert_message, created_at FROM Alerts ORDER BY created_at DESC LIMIT 10")
        if not alerts_df.empty:
            for _, row in alerts_df.iterrows():
                st.error(f"{row['alert_message']}\n\n*Time: {row['created_at']}*")
        else:
            st.success("No active stock alerts! All products are healthy.")

# ----------------- TAB 3: SIMULATE ORDER -----------------
with tab3:
    st.header("Simulate Real-Time Client Order")
    
    with st.expander("Register New Client"):
        with st.form("new_client_form"):
            st.write("Add a new client to the database to process their orders.")
            
            col_name, col_email = st.columns(2)
            with col_name:
                new_name = st.text_input("Full Name")
            with col_email:
                new_email = st.text_input("Email Address")
                
            if st.form_submit_button("Save Client"):
                if new_name and new_email:
                    success, msg = db.add_customer(new_name, new_email)
                    if success:
                        st.success(msg)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill out both fields.")
                    
    st.divider()
    
    # Load available customers and products for the UI dropdowns
    customers = db.fetch_data("SELECT id, name FROM Customers")
    products = db.fetch_data("SELECT id, name, price, stock FROM Products WHERE stock > 0")
    
    if customers.empty or products.empty:
        st.warning("Please ensure your Database is set up correctly and has mock data.")
    else:
        with st.form("order_form"):
            st.write("Please fill out the form below to process a new client order. Inventory will update automatically.")
            
            customer_options = dict(zip(customers['name'], customers['id']))
            selected_customer = st.selectbox("1. Select Client", options=list(customer_options.keys()))
            
            product_options = {f"{row['name']} (Stock: {row['stock']} | Price: ${row['price']})": (row['id'], row['price'], row['stock']) for _, row in products.iterrows()}
            selected_product = st.selectbox("2. Select Product", options=list(product_options.keys()))
            
            quantity = st.number_input("3. Quantity to Order", min_value=1, value=1)
            
            submitted = st.form_submit_button("Execute Order Transaction", use_container_width=True)
            
            if submitted:
                cust_id = customer_options[selected_customer]
                prod_id, price, stock = product_options[selected_product]
                
                # We do basic validation on frontend, but db_manager.py also enforces it in transaction
                if quantity > stock:
                    st.error(f"Cannot order {quantity}. Only {stock} available.")
                else:
                    success, msg = db.place_order(customer_id=cust_id, items=[(prod_id, quantity, price)])
                    if success:
                        st.success(msg)
                        time.sleep(2)  # Show the success message briefly before reload
                        st.rerun()     # Trigger a full reload of the dashboard to see changes
                    else:
                        st.error(f"Transaction Rollback - Failed: {msg}")