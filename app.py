from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length
from flask_bcrypt import Bcrypt

# App Initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'supersecretkey'  # Change this for security
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# Login Manager Setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Lost Item Model
class LostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_lost = db.Column(db.String(50), nullable=False)
    claim_person = db.Column(db.String(100), nullable=True)

# Load user forLogin
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=150)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')

@app.route('/')
def home():
    return render_template('index.html')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials. Try again.', 'danger')
    return render_template('login.html', form=form)

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Report Lost Item (Protected)
@app.route('/report-lost', methods=['POST'])
@login_required
def report_lost():
    data = request.json
    new_item = LostItem(
        name=data['name'],
        description=data['description'],
        location=data['location'],
        date_lost=data['date_lost']
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify({"message": "Lost item reported successfully!"})

# Get Lost Items (Only Unclaimed)
@app.route('/lost-items', methods=['GET'])
def get_lost_items():
    items = LostItem.query.filter_by(claim_person=None).all()
    return jsonify([{"id": i.id, "name": i.name, "description": i.description, "location": i.location} for i in items])

# Get Claimed Items
@app.route('/claimed-items', methods=['GET'])
def get_claimed_items():
    items = LostItem.query.filter(LostItem.claim_person.isnot(None)).all()
    return jsonify([{"id": i.id, "name": i.name, "claim_person": i.claim_person} for i in items])

# Claim Item (Protected)
@app.route('/claim-item', methods=['POST'])
@login_required
def claim_item():
    data = request.json
    item_id = data['item_id']
    claim_name = current_user.username  # Use the logged-in user's name

    item = LostItem.query.get(item_id)

    if item:
        if item.claim_person:
            return jsonify({"message": "This item has already been claimed."})

        item.claim_person = claim_name
        db.session.commit()
        return jsonify({"message": "Item claimed successfully!"})

    return jsonify({"message": "Item not found!"}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
