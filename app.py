from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import os
from contextlib import contextmanager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['DATABASE'] = 'app.db'

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def load_products():
    with get_db_connection() as conn:
        products = conn.execute('SELECT * FROM products').fetchall()
        return [dict(product) for product in products]

def load_users():
    with get_db_connection() as conn:
        users = conn.execute('SELECT * FROM users').fetchall()
        return [dict(user) for user in users]

@app.before_request
def before_request():
    if 'cart' not in session:
        session['cart'] = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/catalog')
def catalog():
    return render_template('catalog.html')

@app.route('/catalog/wood')
def catalog_wood():
    products = load_products()
    return render_template('CatalogOneOne.html', products=products)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/cart')
def cart_page():
    return render_template('box.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        with get_db_connection() as conn:
            user = conn.execute(
                'SELECT * FROM users WHERE username = ? AND password = ?',
                (username, password)
            ).fetchone()

        if not user:
            return "Неверный логин или пароль"

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]

        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()

        with get_db_connection() as conn:
            existing_user = conn.execute(
                'SELECT * FROM users WHERE username = ?', 
                (username,)
            ).fetchone()

            if existing_user:
                return render_template('register.html', error="Пользователь уже существует")

            conn.execute(
                'INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                (username, password, 'user')
            )

        return redirect(url_for('login_page'))

    return render_template('register.html')

@app.route('/api/products')
def get_products():
    products = load_products()
    return jsonify(products)

@app.route('/api/cart/add', methods=['POST'])
def add_to_cart():

    if 'user_id' not in session:
        return jsonify({'error': 'Вы не можете добавлять товары в корзину. Пожалуйста, войдите в систему.'}), 401
    
    try:
        data = request.get_json()
        product_id = str(data.get('product_id'))
        quantity = data.get('quantity', 1)
        
        with get_db_connection() as conn:
            product = conn.execute(
                'SELECT * FROM products WHERE id = ?', 
                (product_id,)
            ).fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        cart = session.get('cart', {})
        
        if product_id in cart:
            cart[product_id]['quantity'] += quantity
        else:
            cart[product_id] = {
                'product_id': product_id,
                'quantity': quantity,
                'name': product['name'],
                'price': product['price'],
                'image_url': product['image_url']
            }
        
        session['cart'] = cart
        session.modified = True
        
        return jsonify({
            'message': 'Product added to cart', 
            'cart_count': len(cart)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cart')
def get_cart():
 
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for item_id, item in cart.items():
        item_total = item['quantity'] * item['price']
        total += item_total
        cart_items.append({
            'id': item_id,
            'product_id': item['product_id'],
            'name': item['name'],
            'price': item['price'],
            'quantity': item['quantity'],
            'total': item_total,
            'image_url': item['image_url']
        })
    
    return jsonify({
        'items': cart_items,
        'total': total,
        'count': len(cart_items),
        'is_authenticated': 'user_id' in session  
    })

@app.route('/api/cart/update/<item_id>', methods=['PUT'])
def update_cart_item(item_id):

    if 'user_id' not in session:
        return jsonify({'error': 'Вы не можете изменять корзину. Пожалуйста, войдите в систему.'}), 401
    
    data = request.get_json()
    quantity = data.get('quantity', 1)
    
    cart = session['cart']
    
    if item_id not in cart:
        return jsonify({'error': 'Item not found'}), 404
    
    if quantity <= 0:
        del cart[item_id]
    else:
        cart[item_id]['quantity'] = quantity
    
    session['cart'] = cart
    session.modified = True
    
    return jsonify({'message': 'Cart updated'})

@app.route('/api/cart/remove/<item_id>', methods=['DELETE'])
def remove_from_cart(item_id):

    if 'user_id' not in session:
        return jsonify({'error': 'Вы не можете изменять корзину. Пожалуйста, войдите в систему.'}), 401
    
    cart = session['cart']
    
    if item_id not in cart:
        return jsonify({'error': 'Item not found'}), 404
    
    del cart[item_id]
    session['cart'] = cart
    session.modified = True
    
    return jsonify({'message': 'Item removed from cart'})

@app.route('/api/cart/clear', methods=['DELETE'])
def clear_cart():

    if 'user_id' not in session:
        return jsonify({'error': 'Вы не можете очищать корзину. Пожалуйста, войдите в систему.'}), 401
    
    session['cart'] = {}
    session.modified = True
    
    return jsonify({'message': 'Cart cleared'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
def admin_panel():
    if session.get("role") != "admin":
        return "Доступ запрещён"

    products = load_products()
    return render_template('admin_products.html', products=products)

@app.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    if session.get("role") != "admin":
        return "Доступ запрещён"

    with get_db_connection() as conn:
        product = conn.execute(
            'SELECT * FROM products WHERE id = ?', 
            (product_id,)
        ).fetchone()

    if not product:
        return "Товар не найден", 404

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        image_url = request.form['image_url']

        with get_db_connection() as conn:
            conn.execute(
                'UPDATE products SET name = ?, price = ?, image_url = ? WHERE id = ?',
                (name, price, image_url, product_id)
            )

        return jsonify({"success": True})

    return render_template('admin_edit.html', product=dict(product))

@app.route('/admin/products/delete/<int:product_id>', methods=['POST'])
def admin_delete_product(product_id):
    if session.get("role") != "admin":
        return "Доступ запрещён"

    with get_db_connection() as conn:
        conn.execute('DELETE FROM products WHERE id = ?', (product_id,))

    return jsonify({"success": True})

@app.route('/admin/products/add', methods=['GET', 'POST'])
def admin_add_product():
    if session.get("role") != "admin":
        return "Доступ запрещён"

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        image_url = request.form['image_url']

        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO products (name, price, image_url) VALUES (?, ?, ?)',
                (name, price, image_url)
            )

        return jsonify({"success": True})

    return render_template('admin_edit.html', product=None)

if __name__ == '__main__':
    if not os.path.exists('app.db'):
        from init_db import init_database
        init_database()
    
    app.run(debug=True, port=5000)