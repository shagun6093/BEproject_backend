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
from model import assistant, journal_report
from utils import State
from langchain_core.messages import HumanMessage
from bson import ObjectId

load_dotenv(find_dotenv())

mongo_uri = os.getenv("MONGO_URI")
mongo_client = MongoClient(mongo_uri)
db = mongo_client["chat_db"]
conversations_collection = db["conversations"]
tasks_collection = db["tasks"]
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
    user = users_collection.find_one({"email": current_user})
    user_id = str(user["_id"])
    
    user_data = {
        "user_id": user_id, 
        "fullName": user["fullName"],
        "email": user["email"],
        "phoneNumber": user["phoneNumber"],
        "age": user["age"],
        "gender": user["gender"],
        "disorder": user.get("disorder", None),
    }
    
    print(user_data)    
    
    return jsonify({"user": user_data, }), 200 


@app.route("/")
def index():
    return "Backend is running."

# @app.route("/api/conversations", methods=["GET"])
# @jwt_required()
# def get_conversations():
#     current_user = get_jwt_identity()
#     user = users_collection.find_one({"email": current_user})
#     user_id = str(user["_id"])
#     conversation_doc = conversations_collection.find_one({"user_id": user_id})
#     if not conversation_doc:
#         conversation_doc["conversation"] = [{"sender": "ai", "content": "Hello! How can I help you today?", "timestamp": datetime.datetime.now().isoformat(), "type": "text"}]
    
#     conversation = conversation_doc["conversation"]
#     return jsonify({"conversation": conversation}), 200

@app.route("/api/conversations", methods=["GET"])
@jwt_required()
def get_conversations():
    current_user = get_jwt_identity()
    user = users_collection.find_one({"email": current_user})
    user_id = str(user["_id"])

    # Try to find the conversation document
    conversation_doc = conversations_collection.find_one({"user_id": user_id})

    # If no conversation exists, create a new one
    if not conversation_doc:
        new_conversation = {
            "user_id": user_id,
            "conversation": [
                {
                    "sender": "ai",
                    "content": "Hello! How can I help you today?",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "type": "text",
                }
            ],
        }
        conversations_collection.insert_one(new_conversation)
        conversation = new_conversation["conversation"]
    else:
        conversation = conversation_doc["conversation"]

    return jsonify({"conversation": conversation}), 200


@app.route("/api/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    current_user = get_jwt_identity()
    user = users_collection.find_one({"email": current_user})
    user_id = str(user["_id"])
    
    tasks_cursor = tasks_collection.find({"user_id": user_id})
    if not tasks_cursor:
        return jsonify({"error": "No conversations found"}), 404
    
    tasks_doc = []
    for task in tasks_cursor:
        task["_id"] = str(task["_id"])
        tasks_doc.append(task)
    
    return jsonify({"tasks": tasks_doc}), 200

@app.route("/api/singleTask", methods=["GET"])
@jwt_required()
def get_single_task():
    current_user = get_jwt_identity()
    user = users_collection.find_one({"email": current_user})
    user_id = str(user["_id"])
    
    task_doc = tasks_collection.find_one({"user_id": user_id, "completed": False})
    if not task_doc:
        return jsonify({"error": "No tasks found"}), 404
    
    task_doc["_id"] = str(task_doc["_id"])
    
    return jsonify({"task": task_doc}), 200

@app.route("/api/user", methods=["PUT"])
@jwt_required()
def update_user():
    current_user = get_jwt_identity()
    user = users_collection.find_one({"email": current_user})
    data = request.get_json()
    disorder = data.get("disorder")
    
    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {
            "disorder": disorder,
        }},
        upsert=True
    )
    
    return jsonify({"message": "User updated successfully"}), 200

@socketio.on("send_message")
def handle_message(json_data):
    user_id = json_data["userId"]
    user_message = json_data["userMessage"]
    user_content = [HumanMessage(content=user_message["content"])]
    
    initial_data = {
        "messages": user_content,
        "user_input": user_message["content"],
        "distortion": [],
        "task": ""
    }
    
    state_doc = conversations_collection.find_one({"user_id": user_id})
    if state_doc.get("distortion", []):
        initial_data["distortion"] = state_doc["distortion"]
        
    tasks = tasks_collection.find_one({"user_id": user_id, "completed": False})
    if tasks:
        initial_data["task"] = tasks["description"]
        
    
    config = {"configurable": {"thread_id": user_id}}
    response = assistant.invoke(initial_data, config)
    
    detected_distortion = response["distortion"]
    if response["task"] != "":
        tasks_collection.insert_one({
            "user_id": user_id,
            "description": response["task"],
            "completed": False,
        })
    
    ai_responses = [msg.content for msg in response["messages"] if isinstance(msg, AIMessage)]
    ai_response = ai_responses[-1]

    # Generate timestamps as ISO format
    ai_timestamp = datetime.datetime.now().isoformat()
    user_timestamp = user_message["timestamp"]
    
    user_entry = {
        "sender": "user",
        "content": user_message["content"],
        "timestamp": user_timestamp,
        "type": user_message["type"]
    }
    
    # If the message is audio, include URI
    if user_message["type"] == "audio":
        user_entry["uri"] = user_message.get("uri", "")
    
    conversations_collection.update_one(
    {"user_id": user_id},
    {
        "$push": {
            "conversation": {
                "$each": [
                    user_entry,
                    {"sender": "ai", "content": ai_response, "timestamp": ai_timestamp, "type": "text"}
                ]
            },
        },
        "$set": {
            "distortion": detected_distortion  # Replace the entire list with new distortions
        }
    },
    upsert=True
)

    
    socketio.emit("receive_message", {
        "content": ai_response,
        "sender": "ai",
        "timestamp": ai_timestamp,
        "task": response["task"]
    })
    
@app.route("/api/feedback/<taskId>", methods=["POST"])
@jwt_required()
def submit_feedback(taskId):
    data = request.get_json()
    feedback = data["feedback"]
    
    task_doc = tasks_collection.find_one({"_id": ObjectId(taskId)})
    if not task_doc:
        return jsonify({"error": "Task not found"}), 404
    
    response = journal_report(feedback, task_doc["description"])
    summary = response["ai_feedback"]
    rating = response["rating"]
    print(summary)
    print(rating)
    
    
    tasks_collection.update_one(
        {"_id": ObjectId(taskId)},
        {"$set": {
            "feedback": feedback,
            "summary": summary,
            "rating": rating,
            "completed": True
        }},
    )
    
    return jsonify({"message": "Feedback submitted", "summary": summary, "rating": rating}), 200

    
    
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)