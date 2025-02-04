from flask import Flask, request, jsonify
import bcrypt
import jwt
import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Load secret key from .env
app.config['SECRET_KEY'] = "SECRET_KEY"

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client['beproject']
users_collection = db['users']
task_collection = db["tasks"]

# Create Task API
@app.route("/create_task", methods=["POST"])
def create_task():
    data = request.json
    if "task_name" not in data or "user_response" not in data or "task_id" not in data:
        return jsonify({"error": "Missing fields"}), 400
    
    task = {
        "task_name": data["task_name"],
        "status": False,  # Default False
        "user_response": data["user_response"],
        "task_id": data["task_id"]
    }
    
    result = task_collection.insert_one(task)
    return jsonify({"message": "Task created", "task_id": str(result.inserted_id)}), 201

# Delete Task API
@app.route("/delete_task/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    result = task_collection.delete_one({"task_id": task_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Task deleted"}), 200

# Update Task API
@app.route("/update_task/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.json
    if "user_response" not in data:
        return jsonify({"error": "Missing user_response"}), 400

    result = task_collection.update_one(
        {"task_id": task_id},
        {"$set": {"user_response": data["user_response"], "status": True}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task updated successfully"}), 200

# Registration endpoint
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    age = data.get('age')
    mail = data.get('mail')
    phonenumber = data.get('phonenumber')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not all([name, age, mail, phonenumber, password, confirm_password]):
        return jsonify({'message': 'All fields are required'}), 400

    if password != confirm_password:
        return jsonify({'message': 'Passwords do not match'}), 400

    # Hash the password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Check if the user already exists
    if users_collection.find_one({'mail': mail}):
        return jsonify({'message': 'User already exists'}), 400

    # Save the user to the database
    users_collection.insert_one({
        'name': name,
        'age': age,
        'mail': mail,
        'phonenumber': phonenumber,
        'password': hashed_password
    })

    return jsonify({'message': 'User registered successfully'}), 201

# Login endpoint
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    mail = data.get('mail')
    password = data.get('password')

    if not all([mail, password]):
        return jsonify({'message': 'Mail and password are required'}), 400

    # Find the user in the database
    user = users_collection.find_one({'mail': mail})
    if not user:
        return jsonify({'message': 'User not found'}), 404

    # Verify the password
    if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
        return jsonify({'message': 'Incorrect password'}), 401

    # Generate JWT token
    token = jwt.encode(
        {'mail': mail, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
        app.config['SECRET_KEY'],
        algorithm="HS256"
    )

    return jsonify({'message': 'Login successful', 'token': token}), 200

# Dashboard endpoint
@app.route('/dashboard', methods=['GET'])
def dashboard():
    token = request.headers.get('x-access-token')

    if not token:
        return jsonify({'message': 'Token is missing'}), 401

    try:
        # Decode the token
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        mail = data['mail']

        # Find the user in the database
        user = users_collection.find_one({'mail': mail}, {'_id': 0, 'password': 0})
        if not user:
            return jsonify({'message': 'User not found'}), 404

        return jsonify({'message': 'Welcome to the dashboard', 'user': user}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token has expired'}), 401

    except jwt.InvalidTokenError:
        return jsonify({'message': 'Invalid token'}), 401


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
