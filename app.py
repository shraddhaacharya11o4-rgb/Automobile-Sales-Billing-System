from flask import Flask, render_template, request, redirect, session 
import sqlite3
from fpdf import FPDF
from datetime import datetime
from num2words import num2words
import os

app = Flask(__name__)
app.secret_key = "ssautos123"

# ---------------- DATABASE SETUP ----------------
def get_db():
    print(os.path.abspath("automobile.db"))
    return sqlite3.connect("automobile.db")


def ensure_customer_columns():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(customers)")
    columns = {row[1] for row in cur.fetchall()}
    if "gst_number" not in columns:
        cur.execute("ALTER TABLE customers ADD COLUMN gst_number TEXT")
    if "location" not in columns:
        cur.execute("ALTER TABLE customers ADD COLUMN location TEXT")
    conn.commit()
    conn.close()


ensure_customer_columns()


def ensure_product_columns():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(products)")
    columns = {row[1] for row in cur.fetchall()}
    if "hsn" not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN hsn INTEGER DEFAULT 0")
    if "mrp" not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN mrp REAL DEFAULT 0.0")
    conn.commit()
    conn.close()


ensure_product_columns()

# ---------------- HOME ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["user"] = username
            return redirect("/")

        else:
            return render_template("login.html", error="Invalid Username or Password")

    return render_template("login.html")

@app.route("/")
def home():

    if "user" not in session:
        return redirect("/login")

    return render_template("index.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

# ---------------- PRODUCTS ----------------
@app.route("/products")
def products():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    data = cur.fetchall()
    conn.close()
    return render_template("products.html", products=data)

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        hsn=int(request.form["hsn"])
        mrp = float(request.form["mrp"])
        price = float(request.form["price"])
        qty = int(request.form["quantity"])

        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO products (name, category, price, quantity, hsn, mrp) VALUES (?,?,?,?,?,?)",
                    (name, category, price, qty, hsn, mrp))
        conn.commit()
        conn.close()
        return redirect("/products")

    return render_template("add_product.html")

@app.route("/update_product/<int:id>", methods=["GET", "POST"])
def update_product(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE product_id=?", (id,))
    product = cur.fetchone()

    if request.method == "POST":
        cur.execute(
            "UPDATE products SET name=?, category=?, price=?, quantity=?,  hsn=?, mrp=? WHERE product_id=?",
            (request.form["name"], request.form["category"], float(request.form["price"]), int(request.form["quantity"]), int(request.form["hsn"]), float(request.form["mrp"]), id)
        )
        conn.commit()
        conn.close()
        return redirect("/products")

    conn.close()
    return render_template("update_product.html", product=product)

@app.route("/delete_product/<int:id>")
def delete_product(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE product_id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/products")

# ---------------- CUSTOMERS ----------------
@app.route("/customers")
def customers():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT customer_id, name, contact, loyalty_points, gst_number, location FROM customers")
    data = cur.fetchall()
    conn.close()
    return render_template("customers.html", customers=data)

@app.route("/add_customer", methods=["GET", "POST"])
def add_customer():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        gst_number = request.form.get("gst_number", "").strip()
        location = request.form.get("location", "").strip()
        cur.execute("INSERT INTO customers (name, contact, gst_number, location, loyalty_points) VALUES (?,?,?,?,0)",
                    (request.form["name"], request.form["contact"], gst_number, location))
        conn.commit()
        conn.close()
        return redirect("/customers")

    return render_template("add_customer.html")

@app.route("/update_customer/<int:id>", methods=["GET", "POST"])
def update_customer(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT customer_id, name, contact, loyalty_points, gst_number, location FROM customers WHERE customer_id=?", (id,))
    customer = cur.fetchone()

    if request.method == "POST":
        gst_number = request.form.get("gst_number", "").strip()
        location = request.form.get("location", "").strip()
        cur.execute(
            "UPDATE customers SET name=?, contact=?, gst_number=?, location=?, loyalty_points=? WHERE customer_id=?",
            (request.form["name"], request.form["contact"], gst_number, location,
             request.form["loyalty_points"], id)
        )
        conn.commit()
        conn.close()
        return redirect("/customers")

    conn.close()
    return render_template("update_customer.html", customer=customer)

@app.route("/delete_customer/<int:id>")
def delete_customer(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM customers WHERE customer_id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/customers")

# ---------------- SALES ----------------
@app.route("/add_sale", methods=["GET", "POST"])
def add_sale():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers")
    customers = cur.fetchall()
    cur.execute("SELECT * FROM products")
    products = cur.fetchall()

    if request.method == "POST":
        cust_id = int(request.form["customer_id"])
        product_ids = request.form.getlist("product_id[]")
        quantities = request.form.getlist("quantity[]")
        discounts = request.form.getlist("discount[]")

        if (not product_ids or not quantities or len(product_ids) != len(quantities) or len(product_ids) != len(discounts)):
            conn.close()
            return "Please select at least one product and enter its quantity."

        line_items = []
        invoice_id = None

        for index, prod_id in enumerate(product_ids):
            prod_id = int(prod_id)
            qty = int(quantities[index])

            if qty < 1:
                conn.close()
                return "Quantity must be at least 1."

            cur.execute("SELECT name, hsn, price, quantity FROM products WHERE product_id=?", (prod_id,))
            pname, hsn, price, stock = cur.fetchone()

            if qty > stock:
                conn.close()
                return f"Not enough stock for {pname}!"

            discount = float(discounts[index]) if discounts[index] else 0

            original_amount = price * qty
            discount_amount = original_amount * discount / 100
            amount = original_amount - discount_amount
            line_items.append({
                "name": pname,
                "hsn": hsn,
                "qty": qty,
                "price": price,
                "discount": discount,
                "discount_amount": discount_amount,
                "amount": amount,
                "product_id": prod_id,
                "stock": stock
            })

        for item in line_items:
            cur.execute("""INSERT INTO sales 
                (customer_id, product_id, quantity, discount, total_price, date)
                VALUES (?,?,?,?,?,?)""",
                (cust_id, item["product_id"], item["qty"], item["discount"], item["amount"], datetime.now()))

            if invoice_id is None:
                invoice_id = cur.lastrowid

            cur.execute("UPDATE products SET quantity=? WHERE product_id=?",
                        (item["stock"] - item["qty"], item["product_id"]))

            cur.execute("UPDATE customers SET loyalty_points = loyalty_points + ? WHERE customer_id=?",
                        (int(item["amount"] // 100), cust_id))

        cur.execute("SELECT name, contact, gst_number, location FROM customers WHERE customer_id=?", (cust_id,))
        customer_record = cur.fetchone()
        cname = customer_record[0] if customer_record else "Walk-in Customer"
        ccontact = customer_record[1] if customer_record else ""
        customer_gst = customer_record[2] if customer_record else ""
        clocation = customer_record[3] if customer_record else ""

        conn.commit()
        conn.close()

        generate_invoice(invoice_id or 0, cname, ccontact, customer_gst, clocation, line_items)
        return redirect("/sales")

    conn.close()
    return render_template("add_sale.html", customers=customers, products=products)

@app.route("/sales")
def sales():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.sale_id, c.name, p.name, s.quantity, s.total_price, s.date, s.discount
        FROM sales s
        JOIN customers c ON s.customer_id=c.customer_id
        JOIN products p ON s.product_id=p.product_id
    """)
    data = cur.fetchall()
    conn.close()
    return render_template("sales.html", sales=data)

# ---------------- PDF INVOICE FUNCTION ----------------
def generate_invoice(sale_id, customer_name, customer_contact, customer_gst, customer_location, items):

    CGST_RATE = 0.09
    SGST_RATE = 0.09

    subtotal = sum(item["amount"] for item in items)
    cgst = round(subtotal * CGST_RATE, 2)
    sgst = round(subtotal * SGST_RATE, 2)
    grand_total = round(subtotal + cgst + sgst, 2)

    round_off = round(round(grand_total) - grand_total, 2)
    rounded_total = round(grand_total)

    customer_name = customer_name or "Walk-in Customer"
    customer_contact = customer_contact or "Not provided"
    customer_location = customer_location or "Not provided"

    def amount_in_words(n):
        return num2words(n, lang="en_IN").title() + " Rupees Only"

    pdf = FPDF("P", "mm", "A4")
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ===== COMPANY DETAILS =====

    pdf.set_text_color(0, 0, 0)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(100, 7, "S.S AUTOS", ln=True)

    pdf.set_font("Helvetica", "", 9)
    pdf.cell(100, 5, "3031 CITB Layout, Hubballi, Dharwad - 580009", ln=True)
    pdf.cell(100, 5, "Phone No.: 9876543210", ln=True)
    pdf.cell(100, 5, "GSTIN: 29AGVPA7545F1Z0", ln=True)
    pdf.cell(100, 5, "State: 29-Karnataka", ln=True)

    pdf.ln(3)

    # ===== TAX INVOICE TITLE =====

    pdf.set_draw_color(165, 172, 147)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())

    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(145, 140, 80)
    pdf.cell(0, 10, "Tax Invoice", ln=True, align="C")

    pdf.set_text_color(0, 0, 0)

    # ===== BILL TO =====

    left_y = pdf.get_y()

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(100, 6, "Bill To", ln=True)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(100, 6, customer_name, ln=True)

    pdf.set_font("Helvetica", "", 10)
    if customer_location:
        pdf.cell(100, 6, customer_location, ln=True)
    if customer_gst:
        pdf.cell(100, 6, f"GSTIN Number: {customer_gst}", ln=True)
    pdf.cell(100, 6, "State: 29-Karnataka", ln=True)

    # ===== INVOICE DETAILS (RIGHT SIDE) =====

    pdf.set_xy(140, left_y)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(50, 6, "Invoice Details", ln=True, align="R")

    pdf.set_font("Helvetica", "", 10)

    pdf.set_x(140)  
    pdf.cell(50, 6, f"Invoice No.: {sale_id}", ln=True, align="R")

    pdf.set_x(140)
    pdf.cell(50, 6, f"Date: {datetime.now().strftime('%d-%m-%Y')}", ln=True, align="R")

    pdf.set_x(140)
    pdf.cell(50, 6, "Place of Supply: 29-Karnataka", ln=True, align="R")

    pdf.ln(8)

    # ===== ITEMS TABLE (BS Traders Style) =====

    pdf.set_fill_color(165, 172, 147)      # Olive Grey
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)

    w_idx = 8
    w_name = 52
    w_hsn = 22
    w_qty = 18
    w_rate = 25
    w_discount = 20
    w_amt = 35
    # Total = 180 mm

    pdf.cell(w_idx, 7, "#", 0, 0, "C", True)
    pdf.cell(w_name, 7, "  Item Name", 0, 0, "L", True)
    pdf.cell(w_hsn, 7, "HSN Code", 0, 0, "C", True)
    pdf.cell(w_qty, 7, "Qty.", 0, 0, "C", True)
    pdf.cell(w_rate, 7, "Rate", 0, 0, "R", True)
    pdf.cell(w_discount, 7, "Disc %", 0, 0, "C", True)
    pdf.cell(w_amt, 7, "Amount", 0, 1, "R", True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)

    total_qty = 0

    for index, item in enumerate(items, start=1):

        qty = item["qty"]
        amount = item["amount"]
        rate = item["price"]

        total_qty += qty

        pdf.cell(w_idx, 7, str(index), 0, 0, "C")
        pdf.cell(w_name, 7, "  " + item["name"], 0, 0, "L")
        pdf.cell(w_hsn, 7, str(item["hsn"]), 0, 0, "C")
        pdf.cell(w_qty, 7, str(qty), 0, 0, "C")
        pdf.cell(w_rate, 7, f"Rs. {rate:.2f}", 0, 0, "R")
        pdf.cell(w_discount, 7, f'{item["discount"]:.0f}%', 0, 0, "C")
        pdf.cell(w_amt, 7, f"Rs. {amount:.2f}", 0, 1, "R")

    # ---------- Separator ----------
    pdf.set_draw_color(170, 170, 170)
    pdf.set_line_width(0.3)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())

    # ---------- Total Row ----------
    pdf.set_font("Helvetica", "B", 9)

    pdf.cell(w_idx, 7, "", 0, 0)              # Empty '#' column
    pdf.cell(w_name + w_hsn, 7, "  Total", 0, 0, "L")
    pdf.cell(w_qty, 7, str(total_qty), 0, 0, "C")
    pdf.cell(w_rate, 7, "", 0, 0)
    pdf.cell(w_discount, 7, "", 0, 0)
    pdf.cell(w_amt, 7, f"Rs. {subtotal:.2f}", 0, 1, "R")

    pdf.line(15, pdf.get_y(), 195, pdf.get_y())

    pdf.ln(6)

    # ===== SUMMARY & TOTALS (BS Traders Style) =====

    start_y = pdf.get_y()

    # ---------- Left Side ----------
    pdf.set_xy(15, start_y)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(100, 5, "Invoice Amount In Words", ln=True)

    pdf.ln(1)

    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(100, 5, amount_in_words(rounded_total))

    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(100, 5, "Terms And Conditions", ln=True)

    pdf.ln(1)

    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(100, 5, "Thank you for doing business with us.")


    # ---------- Right Side ----------
    pdf.set_xy(122, start_y)

    pdf.set_font("Helvetica", "", 9)

    pdf.cell(43, 5.5, "Sub Total")
    pdf.cell(30, 5.5, f"Rs. {subtotal:.2f}", ln=True, align="R")

    pdf.set_xy(122, pdf.get_y())
    pdf.cell(43, 5.5, "SGST @9%")
    pdf.cell(30, 5.5, f"Rs. {sgst:.2f}", ln=True, align="R")

    pdf.set_xy(122, pdf.get_y())
    pdf.cell(43, 5.5, "CGST @9%")
    pdf.cell(30, 5.5, f"Rs. {cgst:.2f}", ln=True, align="R")

    pdf.set_xy(122, pdf.get_y())
    pdf.cell(43, 5.5, "Round Off")
    pdf.cell(30, 5.5, f"Rs. {round_off:.2f}", ln=True, align="R")

    pdf.set_xy(122, pdf.get_y())

    pdf.set_fill_color(165, 172, 147)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 10)

    pdf.cell(43, 7, "Grand Total", fill=True)
    pdf.cell(30, 7, f"Rs. {rounded_total:.2f}", ln=True, align="R", fill=True)

    pdf.ln(10)

    pdf.set_text_color(0, 0, 0)

    # ===== BANK DETAILS & AUTHORIZED SIGNATORY (BS Traders Style) =====

    footer_y = pdf.get_y()

    # ---------- Left Side : Bank Details ----------
    pdf.set_xy(15, footer_y)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(90, 5, "Pay To:", ln=True)

    pdf.ln(1)

    pdf.set_font("Helvetica", "", 8.5)
    pdf.cell(90, 4, "Bank Name: Canara Bank, Hubballi", ln=True)
    pdf.cell(90, 4, "Bank Account No.: XXXXXXXXXXXX", ln=True)
    pdf.cell(90, 4, "IFSC Code: CNRB000XXXX", ln=True)
    pdf.cell(90, 4, "Account Holder: S.S AUTOS", ln=True)

    # ---------- Right Side : Authorized Signatory ----------
    pdf.set_xy(120, footer_y)

    pdf.set_font("Helvetica", "", 9.5)
    pdf.cell(78, 4.5, "For: S.S AUTOS", ln=True, align="C")

    pdf.set_y(footer_y + 20)      # Space for Signature

    pdf.set_x(120)

    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(78, 4.5, "Authorized Signatory", ln=True, align="C")

    # ---------- Footer ----------
    #pdf.set_y(-15)

    #pdf.set_font("Helvetica", "I", 8)
    #pdf.set_text_color(120, 120, 120)

    #pdf.cell(0, 5, "This is a computer-generated invoice.", 0, 1, align="C")

    # ---------- Save PDF ----------
    pdf.output(f"invoice_{sale_id}.pdf")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
