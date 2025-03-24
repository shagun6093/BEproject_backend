import torch
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv, find_dotenv
from transformers import BertTokenizer, BertForSequenceClassification
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt
import os
import groq
from langgraph.graph import MessagesState
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
import datetime
from flask_cors import CORS
from model import assistant
from utils import State
from langchain_core.messages import HumanMessage

load_dotenv(find_dotenv())

mongo_uri = os.getenv("MONGO_URI")
mongo_client = MongoClient(mongo_uri)
db = mongo_client["chat_db"]
conversations_collection = db["conversations"]
journal_reports_collection = db["journal_reports"]
users_collection = db["users"]

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET") 
jwt = JWTManager(app)
bcrypt = Bcrypt(app)


@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    full_name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    phone_number = data.get("phoneNumber")
    age = data.get("age")
    gender = data.get("gender")
    
    if not full_name or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400
    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    new_user = {
        "fullName": full_name,
        "email": email,
        "password": hashed_password,
        "phoneNumber": phone_number,
        "age": age,
        "gender": gender,
        "created_at": datetime.datetime.utcnow()
    }
    users_collection.insert_one(new_user)
    
    return jsonify({"message": "User created successfully"}), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400
    
    user = users_collection.find_one({"email": email})
    if user and bcrypt.check_password_hash(user["password"], password):
        access_token = create_access_token(identity=email, expires_delta=datetime.timedelta(days=1))
        return jsonify({
            "message": "Login successful",
            "token": access_token,
            "email": email,
            "userName": user["fullName"],
            "userId": str(user["_id"])
        }), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/protected", methods=["GET"])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify({"message": f"Hello, {current_user}. This is a protected route!"}), 200


@app.route("/")
def index():
    return "Backend is running."

@app.route("/api/conversations/<user_id>", methods=["GET"])
def get_conversations(user_id):
    conversation_doc = conversations_collection.find_one({"user_id": user_id})
    if not conversation_doc:
        return jsonify({"error": "No conversations found"}), 404
    
    conversation = conversation_doc["conversation"]
    return jsonify({"conversation": conversation}), 200

@socketio.on("send_message")
def handle_message(json_data):
    user_id = json_data["userId"]
    user_message = json_data["userMessage"]
    user_content = HumanMessage(content=user_message["content"])
    
    initial_state = State(messages=[user_content], user_input=user_message["content"])
    config = {"configurable": {"thread_id": user_id}}
    
    response = assistant.invoke(initial_state, config)
    
    ai_responses = [msg.content for msg in response["messages"] if isinstance(msg, AIMessage)]
    ai_response = ai_responses[-1]

    # Generate timestamps as ISO format
    ai_timestamp = datetime.datetime.now().isoformat()
    user_timestamp = user_message["timestamp"]

    # Update MongoDB using $push for efficiency
    conversations_collection.update_one(
        {"user_id": user_id},
        {"$push": {
            "conversation": {"sender": "user", "content": user_message["content"], "timestamp": user_timestamp}
        }},
        upsert=True
    )

    conversations_collection.update_one(
        {"user_id": user_id},
        {"$push": {
            "conversation": {"sender": "ai", "content": ai_response, "timestamp": ai_timestamp}
        }},
        upsert=True
    )
    
    socketio.emit("receive_message", {
        "content": ai_response,
        "sender": "ai",
        "timestamp": ai_timestamp
    })
    
    
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)