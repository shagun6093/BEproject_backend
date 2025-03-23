import torch
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv, find_dotenv
from transformers import BertTokenizer, BertForSequenceClassification


import os
import groq
from langgraph.graph import MessagesState
from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
import datetime
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv(find_dotenv())

# Connect to MongoDB
mongo_uri = os.getenv("MONGO_URI")
mongo_client = MongoClient(mongo_uri)
db = mongo_client["chat_db"]
conversations_collection = db["conversations"]
journal_reports_collection = db["journal_reports"]
users_collection = db["users"]  # For user authentication

# Load fine-tuned BERT model for cognitive distortion detection
bert_tokenizer = BertTokenizer.from_pretrained(os.getenv("BERT_TOKENIZER"), token=os.getenv("HF_TOKEN"))

bert_model = BertForSequenceClassification.from_pretrained(os.getenv("BERT_MODEL"), token=os.getenv("HF_TOKEN"))




# Initialize Groq Client
groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

# Define label mapping for cognitive distortions
label_map = {
    0: 'Control Fallacies',
    1: 'Blaming',
    2: 'Shoulds',
    3: "Heaven's Reward Fallacy",
    4: 'No Distortion',
    5: 'Jumping to Conclusions',
    6: 'Fallacy Of Fairness',
    7: 'Polarized Thinking',
    8: 'Overgeneralization',
    9: 'Global Labeling',
    10: 'Always Being Right',
    11: 'Catastrophizing',
    12: 'Filtering',
    13: 'Personalization',
    14: 'Fallacy Of Change',
    15: 'Emotional Reasoning'
}

# Define our State class. It behaves like a dict.
class State(MessagesState):
    user_input: str
    distortion: str
    task: str
    answer: str
    summary: str
    restruct: str

# Node functions for conversation workflow
def detect_cognitive_distortion(state: State):
    inputs = bert_tokenizer(state["user_input"], return_tensors='pt', padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = bert_model(**inputs)
    predicted_class = torch.argmax(outputs.logits, dim=-1).item()
    state["distortion"] = label_map.get(predicted_class, "No Distortion")
    return state

def chat_agent(state: State):
    if state.get("restruct"):
        prompt = (
          f"User: {state['user_input']}\n"
            f"Previously detected distortion: {state['distortion']}\n"
            f"Current restructuring progress: {state['restruct']}\n"
           "You are a cognitive behavioral therapist. Your task is to present the restructured sentence to the user in a supportive way."
            "Keep responses under 75 words unless deeper clarification is absolutely needed."
        )
    else:
        prompt = (
            f"User now says: {state['user_input']}\n"
           "Respond as a normal chatbot and introduce yourself as Mindmend a CBT-informed chatbot. Engage in a natural conversation, providing direct answers or gentle guidance as needed. "
            "If no distortion is detected, chat normally while staying attentive to subtle cognitive patterns that might emerge. "
            "Keep responses under 75 words unless necessary."
        )
    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
    except Exception:
        answer = "I'm here to help you."
    state["answer"] = answer
    state["messages"] = [HumanMessage(content=state["user_input"]), AIMessage(content=answer)]
    return state

def restructuring_agent(state: State):
    if state["distortion"] != "No Distortion":
        try:
            response = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                   {"role": "system", "content": 
                        f"You're a CBT therapist helping a user recognize and gradually reframe their thoughts. "
                        f"The user has expressed a thought categorized under '{state['distortion']}'. "
                        "Based on the cognitive behavioral therapy technique of cognitive restructuring to reframe the sentence entered by the user to a positive and constructive thought. "
                        "Keep responses under 75 words unless necessary."
                    },
                    {"role": "user", "content": state["user_input"]}
                ]
            )
            state["restruct"] = response.choices[0].message.content
        except Exception:
            state["restruct"] = "Default restructuring."
    return state

def task_assignment_agent(state: State):
    messages = state.get("messages", [])
    if len(messages) >= 3:
        try:
            response = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are a cognitive behavioral therapist. Based on the following conversation history, generate a very brief behavioral activation task to help the user change his negative thinking pattern. The task should be something the user can do in their day-to-day life and should resonate with their previous conversations. Avoid excessive details. Provide the reponse in a conversational manner"
          

                    "complete the whole content in 50 words"           
                            
                            },
                    {"role": "user", "content": str(messages)}


                ]
            )
            state["task"] = response.choices[0].message.content
        except Exception:
            state["task"] = "Default task: Try a mindfulness exercise."
    return state

def journal_report(state: State):
    user_email = state.get("email")
    doc = conversations_collection.find_one({"email": user_email})
    conversation_array = doc.get("conversation", []) if doc else []
    conversation_text = " ".join([f"User: {entry['user']} AI: {entry['ai']}" for entry in conversation_array])
    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a therapist summarizing and analyzing the user's session progress."},
                {"role": "user", "content": f"Please analyze the following conversation and generate a detailed journal report with progress analysis:\n{conversation_text}"}
            ]
        )
        state["summary"] = response.choices[0].message.content
    except Exception:
        state["summary"] = "Could not generate journal report."
    return state

def summarize_task_response(state: State):
    user_email = state.get("email")
    doc = conversations_collection.find_one({"email": user_email})
    task_response = doc.get("task_response", "") if doc else ""
    if not task_response:
        state["summary"] = "No task response found."
        return state
    try:
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a therapist providing feedback on CBT exercises."},
                {"role": "user", "content": f"Analyze the following CBT task response and provide a brief summary with constructive feedback with in 50 words:\n{task_response}"}
            ]
        )
        state["summary"] = response.choices[0].message.content
    except Exception:
        state["summary"] = "Could not generate feedback on the task response."
    return state

# Create workflow
workflow = StateGraph(State)
workflow.support_multiple_edges = True
workflow.add_node("detect_node", detect_cognitive_distortion)
workflow.add_node("chat_node", chat_agent)
workflow.add_node("restructure_node", restructuring_agent)
workflow.add_node("task_node", task_assignment_agent)
workflow.add_edge(START, "detect_node")
workflow.add_conditional_edges("detect_node", lambda x: x["distortion"] != "No Distortion", path_map={True: "restructure_node", False: "chat_node"})
workflow.add_edge("chat_node", "task_node")
workflow.add_edge("restructure_node", "chat_node")
workflow.add_edge("task_node", END)
memory = MemorySaver()
assistant = workflow.compile(checkpointer=memory)

# Flask + SocketIO setup
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Authentication endpoints using email as unique identifier
@app.route("/api/signup", methods=["POST"])
def signup():
    data = request.get_json()
    full_name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    phoneNumber = data.get("phoneNumber")
    age = data.get("age")
    gender = data.get("gender")
    
    if not full_name or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400
    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400
    hashed_password = generate_password_hash(password)
    new_user = {
        "fullName": full_name,
        "email": email,
        "password": hashed_password,
        "phoneNumber": phoneNumber,
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
    if user and check_password_hash(user["password"], password):
        return jsonify({"message": "Login successful", "email": email, "userName": user["fullName"], "userId": str(user["_id"])}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

@app.route("/")
def index():
    return "Backend is running."

@app.route("/api/conversation/<email>", methods=["GET"])
def get_conversation(email):
    doc = conversations_collection.find_one({"email": email})
    if doc:
        return {
            "conversation": doc.get("conversation", []),
            "task": doc.get("task", "")
        }, 200
    else:
        return {"conversation": [], "task": ""}, 404

@app.route("/api/task/<email>", methods=["GET"])
def get_task(email):
    doc = conversations_collection.find_one({"email": email})
    if doc and doc.get("task"):
        return {"task": doc["task"]}, 200
    else:
        return {"task": ""}, 404

@socketio.on("send_message")
def handle_message(json_data):
    user_input = json_data.get("user_input")
    email = json_data.get("akshay@gmail.com")
    # user_name = json_data.get("user_name")
    # if not user_input or not email or not user_name:
    #     return
    initial_state = State(user_input=user_input)
    final_state = assistant.invoke(initial_state, {"configurable": {"thread_id": 123}})
    ai_responses = [msg.content for msg in final_state.get("messages", []) if isinstance(msg, AIMessage)]
    ai_response = ai_responses[-1] if ai_responses else "No response generated."
    doc = conversations_collection.find_one({"email": email})
    if not doc:
        conversation_data = {
            "email": email,
            # "user_name": user_name,
            "conversation": [],
            "task": ""
        }
    else:
        conversation_data = doc
    conversation_entry = {"user": user_input, "ai": ai_response}
    conversation_data["conversation"].append(conversation_entry)
    
    # change this logic while using new model workflow
    # if len(conversation_data["conversation"]) >= 3:
    #     state_for_task = State(user_input=user_input)
    #     state_for_task["messages"] = final_state.get("messages", [])
    #     state_for_task = task_assignment_agent(state_for_task)
    #     conversation_data["task"] = state_for_task.get("task", "")
    # else:
    #     conversation_data["task"] = conversation_data.get("task", "")
    # conversations_collection.update_one(
    #     {"email": email},
    #     {"$set": {
    #         "email": email,
    #         "user_name": user_name,
    #         "conversation": conversation_data["conversation"],
    #         "task": conversation_data["task"]
    #     }},
    #     upsert=True
    # )
    
    socketio.emit("receive_message", {
        "conversation": conversation_data["conversation"],
        "task": conversation_data["task"],
        "email": email
    })

@socketio.on("complete_session")
def handle_complete_session(json_data):
    email = json_data.get("email")
    user_name = json_data.get("user_name")
    if not email or not user_name:
        return
    state = State(user_input="session complete")
    state["email"] = email
    state = journal_report(state)
    report = state.get("summary", "No report generated.")
    conversations_collection.update_one(
        {"email": email},
        {"$set": {"journal_report": report}},
        upsert=True
    )
    socketio.emit("session_complete", {"report": report})

@socketio.on("complete_task")
def handle_complete_task(json_data):
    email = json_data.get("email")
    user_response = json_data.get("user_response")
    if not email or not user_response:
        return
    conversations_collection.update_one(
        {"email": email},
        {"$set": {"task_response": user_response}},
        upsert=True
    )
    state = State(user_input="task complete")
    state["email"] = email
    state = summarize_task_response(state)
    feedback = state.get("summary", "No feedback generated.")
    conversations_collection.update_one(
        {"email": email},
        {"$set": {"task_feedback": feedback}},
        upsert=True
    )
    socketio.emit("task_feedback", {"feedback": feedback, "email": email})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)






