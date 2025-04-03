from flask import Flask, render_template, request, redirect, session, g
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecret'
DATABASE = 'database.db'

# ================= DATABASE =================
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# ================= LOGIN =================
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    if user:
        session['user_id'] = user['userID']
        session['role'] = user['role']
        return redirect('/warehouses')
    else:
        return "Login Failed", 401

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ================= WAREHOUSE =================
@app.route('/warehouses')
def view_warehouses():
    db = get_db()
    warehouses = db.execute('SELECT * FROM warehouses').fetchall()
    return render_template('warehouses.html', warehouses=warehouses)

@app.route('/warehouse/add', methods=['POST'])
def add_warehouse():
    name = request.form['name']
    location = request.form['location']
    db = get_db()
    db.execute('INSERT INTO warehouses (name, location) VALUES (?, ?)', (name, location))
    db.commit()
    if 'user_id' in session:
        db.execute('INSERT INTO logs (userID, action) VALUES (?, ?)', (session['user_id'], f'เพิ่มคลังใหม่: {name} ({location})'))
        db.commit()
    return redirect('/warehouses')

@app.route('/warehouse/delete/<int:warehouse_id>', methods=['POST'])
def delete_warehouse(warehouse_id):
    db = get_db()
    check = db.execute('SELECT COUNT(*) as count FROM inventory WHERE warehouseID = ?', (warehouse_id,)).fetchone()
    if check['count'] > 0:
        return "❌ ไม่สามารถลบคลังได้ เพราะยังมีสินค้าคงคลัง", 400
    db.execute('DELETE FROM warehouses WHERE warehouseID = ?', (warehouse_id,))
    db.commit()
    if 'user_id' in session:
        db.execute('INSERT INTO logs (userID, action) VALUES (?, ?)', (session['user_id'], f'ลบคลัง: warehouseID={warehouse_id}'))
        db.commit()
    return redirect('/warehouses')

@app.route('/warehouse/<int:warehouse_id>')
def warehouse_detail(warehouse_id):
    db = get_db()
    warehouse = db.execute('SELECT * FROM warehouses WHERE warehouseID = ?', (warehouse_id,)).fetchone()
    inventory = db.execute('''
        SELECT i.inventoryID, p.name AS product, i.quantity
        FROM inventory i
        JOIN products p ON i.productID = p.productID
        WHERE i.warehouseID = ?
    ''', (warehouse_id,)).fetchall()
    products = db.execute('SELECT * FROM products').fetchall()
    return render_template('warehouse_detail.html', warehouse=warehouse, inventory=inventory, products=products)

@app.route('/warehouse/<int:warehouse_id>/add_inventory', methods=['POST'])
def add_inventory_to_warehouse(warehouse_id):
    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])
    db = get_db()
    existing = db.execute('SELECT * FROM inventory WHERE warehouseID = ? AND productID = ?', (warehouse_id, product_id)).fetchone()
    if existing:
        db.execute('UPDATE inventory SET quantity = quantity + ? WHERE inventoryID = ?', (quantity, existing['inventoryID']))
    else:
        db.execute('INSERT INTO inventory (warehouseID, productID, quantity) VALUES (?, ?, ?)', (warehouse_id, product_id, quantity))
    db.commit()
    if 'user_id' in session:
        db.execute('INSERT INTO logs (userID, action) VALUES (?, ?)', (session['user_id'], f'เพิ่มสินค้าในคลัง warehouseID={warehouse_id}, productID={product_id}, qty={quantity}'))
        db.commit()
    return redirect(f'/warehouse/{warehouse_id}')

@app.route('/warehouse/<int:warehouse_id>/delete_inventory/<int:inventory_id>', methods=['POST'])
def delete_inventory_in_warehouse(warehouse_id, inventory_id):
    db = get_db()
    current = db.execute('SELECT quantity FROM inventory WHERE inventoryID = ?', (inventory_id,)).fetchone()
    if current and current['quantity'] > 0:
        return "❌ ไม่สามารถลบสินค้าได้: quantity ยังไม่เป็น 0", 400
    db.execute('DELETE FROM inventory WHERE inventoryID = ?', (inventory_id,))
    db.commit()
    if 'user_id' in session:
        db.execute('INSERT INTO logs (userID, action) VALUES (?, ?)', (session['user_id'], f'ลบสินค้าออกจาก inventoryID={inventory_id} ของ warehouseID={warehouse_id}'))
        db.commit()
    return redirect(f'/warehouse/{warehouse_id}')

@app.route('/warehouse/<int:warehouse_id>/adjust_inventory/<int:inventory_id>', methods=['POST'])
def adjust_inventory(warehouse_id, inventory_id):
    try:
        delta = int(request.form['delta'])
    except:
        delta = 0
    db = get_db()
    current = db.execute('SELECT quantity FROM inventory WHERE inventoryID = ?', (inventory_id,)).fetchone()
    if current:
        new_qty = max(0, current['quantity'] + delta)
        db.execute('UPDATE inventory SET quantity = ? WHERE inventoryID = ?', (new_qty, inventory_id))
        db.commit()
        if 'user_id' in session and delta != 0:
            db.execute('INSERT INTO logs (userID, action) VALUES (?, ?)', (session['user_id'], f'ปรับจำนวนสินค้า inventoryID={inventory_id} ของ warehouseID={warehouse_id} → {"+" if delta > 0 else ""}{delta}'))
            db.commit()
    return redirect(f'/warehouse/{warehouse_id}')

@app.route('/warehouse/<int:warehouse_id>/logs')
def warehouse_logs(warehouse_id):
    db = get_db()
    warehouse = db.execute('SELECT * FROM warehouses WHERE warehouseID = ?', (warehouse_id,)).fetchone()
    logs = db.execute('''
        SELECT l.timestamp, l.action, u.username
        FROM logs l
        JOIN users u ON l.userID = u.userID
        WHERE l.action LIKE ?
        ORDER BY l.timestamp DESC
    ''', (f'%warehouseID={warehouse_id}%',)).fetchall()
    return render_template('warehouse_logs.html', warehouse=warehouse, logs=logs)

# ================= PRODUCTS =================
@app.route('/products/add', methods=['POST'])
def add_product():
    name = request.form['name']
    description = request.form['description']
    cost = float(request.form['cost'])
    price = float(request.form['price'])
    category = request.form['category']
    db = get_db()
    existing = db.execute('SELECT * FROM products WHERE name = ?', (name,)).fetchone()
    if existing:
        return "❌ ชื่อสินค้านี้มีอยู่ในระบบแล้ว", 400
    db.execute('INSERT INTO products (name, description, cost, price, category) VALUES (?, ?, ?, ?, ?)', (name, description, cost, price, category))
    db.commit()
    if 'user_id' in session:
        db.execute('INSERT INTO logs (userID, action) VALUES (?, ?)', (session['user_id'], f'เพิ่มสินค้าใหม่: {name} ({category})'))
        db.commit()
    return redirect(request.referrer or '/warehouses')


# ================= RUN =================
if __name__ == '__main__':
    app.run(debug=True)
