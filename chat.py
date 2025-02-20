import torch
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv, find_dotenv
from transformers import BertTokenizer, BertForSequenceClassification
import os
import groq
from langgraph.graph import MessagesState
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from pymongo import MongoClient
import datetime
from flask_cors import CORS

# Load environment variables
load_dotenv(find_dotenv())

# Connect to MongoDB (ensure MONGO_URI is set in your .env or default to localhost)
mongo_uri = os.getenv("MONGO_URI")
mongo_client = MongoClient(mongo_uri)
db = mongo_client["mindmend"]
conversations_collection = db["conversations"]
journal_reports_collection = db["journal_reports"]

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

# Node functions
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
            "Continue the conversation naturally, helping the user reflect and refine their thought process. "
            "Provide direct answers when helpful, but keep the dialogue flowing without feeling abrupt. "
            "Encourage the user to share more, and slowly guide them toward alternative perspectives. "
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
    # Record conversation messages for this turn
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
                        "Don't immediately rewrite their thought—ask gentle questions that guide them toward seeing a different perspective. "
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
    # Generate a task if the accumulated messages are enough (adjust threshold as needed)
    if len(messages) >= 6:
        try:
            response = groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are an innovative cognitive behavioral therapist. Based on the conversation provided, "
                            "please generate a unique and creative CBT task for the user. Your task should go beyond "
                            "just reframing negative thoughts and may include activities such as mindfulness exercises, "
                            "journaling prompts, behavioral experiments, or reflective questions. Ensure that the task "
                            "is varied and engaging each time."},
                    {"role": "user", "content": str(messages)}
                ]
            )
            state["task"] = response.choices[0].message.content
        except Exception:
            state["task"] = "Default task: Try a mindfulness exercise."
    return state

def journal_report(state: State):
    """
    Generate a journal report using the conversation stored in MongoDB.
    """
    user_id = state.get("user_id")
    doc = conversations_collection.find_one({"user_id": user_id})
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

# Create workflow and add nodes/edges
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

# Apply CORS to the Flask app
CORS(app)

# Allow SocketIO connections from any origin (or set specific origins for production)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    # (Optional) You may serve an index template if needed.
    return "Backend is running."

@socketio.on("send_message")
def handle_message(json_data):
    # Extract user info and message from the frontend
    user_input = json_data.get("user_input")
    user_id = json_data.get("user_id")
    user_name = json_data.get("user_name")
    if not user_input or not user_id or not user_name:
        return

    # Process the current turn with the workflow
    initial_state = State(user_input=user_input)
    final_state = assistant.invoke(initial_state, {"configurable": {"thread_id": 123}})
    ai_responses = [msg.content for msg in final_state.get("messages", []) if isinstance(msg, AIMessage)]
    ai_response = ai_responses[-1] if ai_responses else "No response generated."

    # Retrieve existing conversation document for the user or create a new one
    doc = conversations_collection.find_one({"user_id": user_id})
    if not doc:
        conversation_data = {
            "user_id": user_id,
            "user_name": user_name,
            "conversation": [],  # conversation will be an array of {user, ai} objects
            "task": ""
        }
    else:
        conversation_data = doc

    # Append the new conversation pair to the conversation array
    conversation_entry = {"user": user_input, "ai": ai_response}
    conversation_data["conversation"].append(conversation_entry)

    # Generate/update task if applicable (adjust threshold as needed)
    if len(conversation_data["conversation"]) >= 3:
        state_for_task = State(user_input=user_input)
        state_for_task["messages"] = final_state.get("messages", [])
        state_for_task = task_assignment_agent(state_for_task)
        conversation_data["task"] = state_for_task.get("task", "")
    else:
        conversation_data["task"] = conversation_data.get("task", "")

    # Upsert the conversation document into MongoDB
    conversations_collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "user_name": user_name,
            "conversation": conversation_data["conversation"],
            "task": conversation_data["task"]
        }},
        upsert=True
    )

    # Emit the updated conversation and task to the frontend
    socketio.emit("receive_message", {
        "conversation": conversation_data["conversation"],
        "task": conversation_data["task"],
        "user_id": user_id
    })

@socketio.on("complete_session")
def handle_complete_session(json_data):
    user_id = json_data.get("user_id")
    user_name = json_data.get("user_name")
    if not user_id or not user_name:
        return

    state = State(user_input="session complete")
    state["user_id"] = user_id
    state = journal_report(state)
    report = state.get("summary", "No report generated.")

    # Optionally update the document with the journal report
    conversations_collection.update_one(
        {"user_id": user_id},
        {"$set": {"journal_report": report}},
        upsert=True
    )

    socketio.emit("session_complete", {"report": report})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8000, debug=True)
