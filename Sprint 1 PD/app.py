from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuration for the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:pfwfall2024@donnadb.cvaai4e089sw.us-east-2.rds.amazonaws.com:3306/appdetail'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# User model for the database
class User(db.Model):
    __tablename__ = 'userdetail'  # Specify the table name
 
    fname = db.Column(db.String(50), nullable=False)
    lname = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False, primary_key=True)
    emailid = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Route for user signup
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    fname = data.get('fname')
    lname = data.get('lname')
    username = data.get('username')
    password = data.get('password')
    emailid=data.get('emailid')
    # Check if the user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"message": "Username already exists!"}), 400
    
    new_user = User(
        fname=fname,
        lname=lname,
        username=username,
        emailid=emailid,
        password=password
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User created successfully!"}), 201

# Route for user login
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Verify user credentials
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        return jsonify({"message": "Login successful!"}), 200
    return jsonify({"message": "Invalid credentials!"}), 401

if __name__ == '__main__':
    app.run(debug=True)