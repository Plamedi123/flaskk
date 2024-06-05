from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'azertyuiopqsdfghjklmwxcvbnazertyuiopqsdfghjklmwxcvbn'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/USER/Desktop/db_isuku/isukura'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Set no cache by default for development
db = SQLAlchemy(app)
login_manager = LoginManager(app)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))
    address = db.Column(db.String(200))  # For household users
    company = db.Column(db.String(100))  # For waste collectors

    def __init__(self, email, password, role, address=None, company=None):
        self.email = email
        self.password = password
        self.role = role
        self.address = address
        self.company = company

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class ScheduledPickup(db.Model):
    __tablename__ = 'scheduled_pickups'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    date = db.Column(db.Date)

    def __init__(self, user_id, date):
        self.user_id = user_id
        self.date = date

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':  # Fixed from 'if request.method == ['POST']'
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        address = request.form.get('address', None)  # For household users
        company = request.form.get('company', None)  # For waste collectors

        user = User(email, generate_password_hash(password), role, address, company)  # Hash the password
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    scheduled_pickups = ScheduledPickup.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', user=current_user, scheduled_pickups=scheduled_pickups)

@app.route('/schedule_pickup', methods=['POST'])
@login_required
def schedule_pickup():
    if current_user.role != 'household':
        flash('Only household users can schedule pickups.', 'error')
        return redirect(url_for('dashboard'))
    
    pickup_date = request.form['pickup_date']
    amount = request.form['amount']
    types = request.form['types']
    description = request.form['description']
    scheduled_pickup = ScheduledPickup(current_user.id, datetime.strptime(pickup_date, '%Y-%m-%d').date(), amount, types, description)
    db.session.add(scheduled_pickup)
    db.session.commit()
    flash('Pickup scheduled successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/edit_pickup/<int:pickup_id>', methods=['GET', 'POST'])
@login_required
def edit_pickup(pickup_id):
    pickup = ScheduledPickup.query.get(pickup_id)
    if request.method == 'POST':
        pickup.date = datetime.strptime(request.form['pickup_date'], '%Y-%m-%d').date()
        pickup.amount = request.form['amount']
        pickup.types = request.form['types']
        pickup.description = request.form['description']
        db.session.commit()
        flash('Pickup updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_pickup.html', pickup=pickup)

@app.route('/delete_pickup/<int:pickup_id>', methods=['POST'])
@login_required
def delete_pickup(pickup_id):
    pickup = ScheduledPickup.query.get(pickup_id)
    db.session.delete(pickup)
    db.session.commit()
    flash('Pickup deleted successfully!', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
