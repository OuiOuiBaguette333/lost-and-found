from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.route('/')
def home():
    return render_template('index.html')

class lost_item(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable = False)
    description = db.Column(db.Text, nullable = False)
    location = db.Column(db.String(100), nullable = False)
    date_lost = db.Column(db.String(50), nullable = False)
    claim_person = db.Column(db.String(100), nullable = True)

@app.route('/report-lost', methods=['POST'])

def report_lost():
    data = request.json
    new_item = lost_item(name = data['name'], description = data['description'], location = data['location'], date_lost = data['date_lost'])
    db.session.add(new_item)
    db.session.commit()
    return jsonify({"message": "Lost item reported successfully!"})

@app.route('/lost-items', methods=['GET'])
def get_lost_items():
    items = lost_item.query.filter_by(claim_person=None).all()  # Get only unclaimed items
    return jsonify([{"id": i.id, "name": i.name, "description": i.description, "location": i.location} for i in items])

@app.route('/claimed-items', methods=['GET'])
def get_claimed_items():
    items = lost_item.query.filter(lost_item.claim_person.isnot(None)).all()  # Get only claimed items
    return jsonify([{"id": i.id, "name": i.name, "claim_person": i.claim_person} for i in items])
@app.route('/claim-item', methods=['POST'])
def claim_item():
    data = request.json
    item_id = data['item_id']
    claim_name = data['claim_name']

    # Find the item by ID
    item = lost_item.query.get(item_id)

    if item:
        # If the item is already claimed, send an error message
        if item.claim_person:
            return jsonify({"message": "This item has already been claimed."})

        # Set the claimant name and commit changes to the database
        item.claim_person = claim_name
        db.session.commit()
        return jsonify({"message": "Item claimed successfully!"})

    return jsonify({"message": "Item not found!"}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug = True)
