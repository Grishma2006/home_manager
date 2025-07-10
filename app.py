from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from datetime import datetime, date
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# --------------------- Models ---------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(80))


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    type = db.Column(db.String(100))
    price = db.Column(db.Float)
    expiry_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


# --------------------- Load User ---------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# --------------------- Routes ---------------------

@app.route('/')
def home():
    return redirect('/login')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = User(username=request.form['username'], password=request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please login.")
        return redirect('/login')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username'], password=request.form['password']).first()
        if user:
            login_user(user)
            return redirect('/dashboard')
        else:
            flash("Invalid credentials")
            return redirect('/login')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')


@app.route('/dashboard')
@login_required
def dashboard():
    search = request.args.get('search', '')
    if search:
        products = Product.query.filter(Product.user_id == current_user.id, Product.name.contains(search)).all()
    else:
        products = Product.query.filter_by(user_id=current_user.id).all()

    # Calculate days remaining
    today = date.today()
    for p in products:
        p.days_remaining = (p.expiry_date - today).days
    return render_template('dashboard.html', products=products, search=search)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form['name']
        type_ = request.form['type']
        price = float(request.form['price'])
        expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
        product = Product(name=name, type=type_, price=price, expiry_date=expiry_date, user_id=current_user.id)
        db.session.add(product)
        db.session.commit()
        return redirect('/dashboard')
    return render_template('add_product.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        flash("Unauthorized access")
        return redirect('/dashboard')

    if request.method == 'POST':
        product.name = request.form['name']
        product.type = request.form['type']
        product.price = float(request.form['price'])
        product.expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
        db.session.commit()
        return redirect('/dashboard')

    return render_template('edit_product.html', product=product)


@app.route('/delete/<int:id>')
@login_required
def delete(id):
    product = Product.query.get_or_404(id)
    if product.user_id != current_user.id:
        flash("Unauthorized access")
        return redirect('/dashboard')

    db.session.delete(product)
    db.session.commit()
    return redirect('/dashboard')


# --------------------- Run App ---------------------

if __name__ == '__main__':
    if not os.path.exists('database.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
