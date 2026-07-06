import sqlite3
from datetime import datetime

# ---------------- Database Setup ----------------
conn = sqlite3.connect('automobile.db')
cursor = conn.cursor()

# Products Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL
)
""")

# Customers Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT,
    loyalty_points INTEGER DEFAULT 0
)
""")

# Sales Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    product_id INTEGER,
    quantity INTEGER,
    total_price REAL,
    date TEXT,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY(product_id) REFERENCES products(product_id)
)
""")

conn.commit()
conn.close()

# ---------------- Products Module ----------------
def add_product(name, category, price, quantity):
    conn = sqlite3.connect('automobile.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, category, price, quantity) VALUES (?, ?, ?, ?)",
                   (name, category, price, quantity))
    conn.commit()
    conn.close()
    print(f"Product '{name}' added successfully!")

def view_products():
    conn = sqlite3.connect('automobile.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    
    print("\n---- Products ----")
    for product in products:
        print(product)

def update_product(product_id, name=None, category=None, price=None, quantity=None):
    conn = sqlite3.connect('automobile.db')
    cursor = conn.cursor()
    
    if name:
        cursor.execute("UPDATE products SET name=? WHERE product_id=?", (name, product_id))
    if category:
        cursor.execute("UPDATE products SET category=? WHERE product_id=?", (category, product_id))
    if price:
        cursor.execute("UPDATE products SET price=? WHERE product_id=?", (price, product_id))
    if quantity:
        cursor.execute("UPDATE products SET quantity=? WHERE product_id=?", (quantity, product_id))
    
    conn.commit()
    conn.close()
    print(f"Product ID {product_id} updated successfully!")

def delete_product(product_id):
    conn = sqlite3.connect('automobile.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE product_id=?", (product_id,))
    conn.commit()
    conn.close()
    print(f"Product ID {product_id} deleted successfully!")

# ---------------- Customers Module ----------------
def add_customer(name, contact):
    conn = sqlite3.connect('automobile.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO customers (name, contact) VALUES (?, ?)", (name, contact))
    conn.commit()
    conn.close()
    print(f"Customer '{name}' added successfully!")

def view_customers():
    conn = sqlite3.connect('automobile.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers")
    customers = cursor.fetchall()
    conn.close()
    
    print("\n---- Customers ----")
    for customer in customers:
        print(customer)

def update_customer(customer_id, name=None, contact=None, loyalty_points=None):
    conn = sqlite3.connect('automobile.db')
    cursor = conn.cursor()
    if name:
        cursor.execute("UPDATE customers SET name=? WHERE customer_id=?", (name, customer_id))
    if contact:
        cursor.execute("UPDATE customers SET contact=? WHERE customer_id=?", (contact, customer_id))
    if loyalty_points is not None:
        cursor.execute("UPDATE customers SET loyalty_points=? WHERE customer_id=?", (loyalty_points, customer_id))
    conn.commit()
    conn.close()
    print(f"Customer ID {customer_id} updated successfully!")

def delete_customer(customer_id):
    conn = sqlite3.connect('automobile.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE customer_id=?", (customer_id,))
    conn.commit()
    conn.close()
    print(f"Customer ID {customer_id} deleted successfully!")

# ---------------- Sales & Billing Module ----------------
def add_sale(customer_id, product_id, quantity):
    conn = sqlite3.connect('automobile.db')
    cursor = conn.cursor()
    
    # Get product price and stock
    cursor.execute("SELECT price, quantity FROM products WHERE product_id=?", (product_id,))
    result = cursor.fetchone()
    if result:
        price, stock = result
        if stock < quantity:
            print("Not enough stock!")
            conn.close()
            return
        total_price = price * quantity
        
        # Insert sale record
        cursor.execute("INSERT INTO sales (customer_id, product_id, quantity, total_price, date) VALUES (?, ?, ?, ?, ?)",
                       (customer_id, product_id, quantity, total_price, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Update product stock
        cursor.execute("UPDATE products SET quantity=? WHERE product_id=?", (stock - quantity, product_id))
        
        # Update customer loyalty points (+1 point for every 100 spent)
        points = int(total_price // 100)
        cursor.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE customer_id=?", (points, customer_id))
        
        conn.commit()
        print(f"Sale completed! Total: {total_price}, Loyalty points added: {points}")
    else:
        print("Product not found!")
    
    conn.close()

def view_sales():
    conn = sqlite3.connect('automobile.db')
    cursor = conn.cursor()
    cursor.execute("""
    SELECT s.sale_id, c.name, p.name, s.quantity, s.total_price, s.date
    FROM sales s
    JOIN customers c ON s.customer_id = c.customer_id
    JOIN products p ON s.product_id = p.product_id
    """)
    sales = cursor.fetchall()
    conn.close()
    
    print("\n---- Sales ----")
    for sale in sales:
        print(sale)

# ---------------- Example Usage ----------------

# Products
add_product("Engine Oil", "Oil", 450.0, 10)
add_product("Car Battery", "Battery", 2500.0, 5)
view_products()

# Customers
add_customer("Rahul Sharma", "9876543210")
add_customer("Priya Singh", "9123456780")
view_customers()

# Sales
add_sale(1, 1, 2)  # Customer 1 buys 2 Engine Oil
add_sale(1, 2, 1)  # Customer 1 buys 1 Car Battery
view_sales()

# View updated products & customers
view_products()
view_customers()
