from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'secreta_key_pentru_sesiuni'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ========== MODELE ==========
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

# ========== CREARE BAZA DATE ==========
with app.app_context():
    db.create_all()
    
    # Adauga produse test daca nu exista
    if Product.query.count() == 0:
        produse_test = [
            Product(name='Telefon XYZ', description='Telefon nou', price=1500, quantity=10),
            Product(name='Laptop ABC', description='Laptop performant', price=3500, quantity=5),
            Product(name='Casti Bluetooth', description='Casti wireless', price=200, quantity=15)
        ]
        for p in produse_test:
            db.session.add(p)
        db.session.commit()
        print("✅ Produse test adaugate!")

# ========== RUTE ==========
@app.route('/')
def index():
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password']).decode('utf-8')
        role = request.form.get('role', 'user')
        
        if User.query.filter_by(username=username).first():
            return "Utilizator deja exista!"
        
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('index'))
        return "Date gresite!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    quantity = int(request.form['quantity'])
    cart_item = Cart.query.filter_by(user_id=session['user_id'], product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(user_id=session['user_id'], product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cart_items = Cart.query.filter_by(user_id=session['user_id']).all()
    items_data = []
    total = 0
    
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:
            subtotal = product.price * item.quantity
            total += subtotal
            items_data.append({
                'id': item.id,
                'name': product.name,
                'price': product.price,
                'quantity': item.quantity,
                'subtotal': subtotal
            })
    
    return render_template('cart.html', cart_items=items_data, total=total)

@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    cart_item = Cart.query.get_or_404(cart_id)
    db.session.delete(cart_item)
    db.session.commit()
    return redirect(url_for('cart'))

if __name__ == '__main__':
    app.run(debug=True)