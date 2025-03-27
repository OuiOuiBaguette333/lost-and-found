from flask import Flask, request, render_template, jsonify, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# App Initialization
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'supersecretkey'  # Change this for security
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Lost Item Model
class LostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    date_lost = db.Column(db.String(50), nullable=False)
    claim_person = db.Column(db.String(100), nullable=True)

@app.route('/')
def home():
    return render_template('index.html')

# Report Lost Item (No login required)
@app.route('/report-lost', methods=['POST'])
def report_lost():
    # Get data from the form
    name = request.form['name']
    description = request.form['description']
    location = request.form['location']
    date_lost = request.form['date_lost']

    # Create a new lost item
    new_item = LostItem(
        name=name,
        description=description,
        location=location,
        date_lost=date_lost
    )
    db.session.add(new_item)
    db.session.commit()

    flash('Lost item reported successfully!', 'success')
    return redirect(url_for('home'))

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

# Claim Item (No login required)
@app.route('/claim-item', methods=['POST'])
def claim_item():
    data = request.json
    item_id = data['item_id']
    claim_name = data['claim_name']

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
