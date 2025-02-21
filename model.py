import torch
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, RemoveMessage
from dotenv import load_dotenv, find_dotenv
import os
from typing import Literal
from langchain_groq import ChatGroq
from utils import State, bert_tokenizer, bert_model, label_map, memory
    
# def should_continue(state: State) -> Literal["summarize_conversation", "detect_node"]:
#     """Return the next node to execute."""
#     messages = state["messages"]
#     # If there are more than six messages, then we summarize the conversation
#     if len(messages) > 6:
#         return "summarize_conversation"
#     # Otherwise we can just end
#     return "detect_node"

load_dotenv(find_dotenv())

llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama3-8b-8192")

def summarize_history(state: State):
    """Creates a brief summary of recent conversation turns for context."""
    summary = state.get("summary", "")

    if summary:
        summary_message = (
            f"This is a summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
        )
    else:
        summary_message = "Create a summary of the conversation above:"

    # Add prompt to our history
    messages = state["messages"] + [HumanMessage(content=summary_message)]
    summarizer = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="mixtral-8x7b-32768")    
    response = summarizer.invoke(messages)

    summary = response.content
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][-2:]]
    
    return {"summary": response.content, "messages": delete_messages}


# Node functions
def detect_cognitive_distortion(state: State):
    distortion = state.get("distortion", [])
    inputs = bert_tokenizer(state["user_input"], return_tensors='pt', padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = bert_model(**inputs)
    predicted_class = torch.argmax(outputs.logits, dim=-1).item()
    new_distortion = label_map.get(predicted_class, None)
    return {"distortion": distortion + [new_distortion]}

def chat_agent(state: State):
    summary = state.get("summary", "")
    messages= state["messages"][-6:]
    distortion = state["distortion"][-1:]
    
    if state.get("restruct"):
        prompt = (
            f"Previous Conversation Summary: {summary}\n"
            f"User: {messages}\n"
            f"Previously detected distortion: {distortion}\n"
            f"Current restructuring progress: {state['restruct']}\n"
            "Continue the conversation naturally, helping the user reflect and refine their thought process. "
            "Provide direct answers when helpful, but keep the dialogue flowing without feeling abrupt. "
            "Encourage the user to share more keeping the previous conversation in mind, and slowly guide them toward alternative perspectives. "
            "Keep responses under 75 words unless deeper clarification is absolutely needed."
        )
    else:
        prompt = (
            f"Previous Conversation Summary: {summary}\n"
            f"User: {messages}\n"
            "Respond as a normal chatbot and introduce yourself as Mindmend a CBT-informed chatbot. Engage in a natural conversation, providing direct answers or gentle guidance as needed. "
            "If no distortion is detected, chat normally while staying attentive to subtle cognitive patterns that might emerge. "
            "Keep responses under 75 words unless necessary."
        )
    
    response = llm.invoke(prompt)
    
    return {"messages": [AIMessage(content=response.content)]}

def restructuring_agent(state: State):
    if state["distortion"] != "No":
        prompt = (
            f"You're a CBT therapist helping a user recognize and gradually reframe their thoughts. "
            f"The user has expressed a thought categorized under '{state['distortion']}'. "
            "Don't immediately rewrite their thought—ask gentle questions that guide them toward seeing a different perspective. "
            "Keep responses under 75 words unless necessary."
        )
        response = llm.invoke(prompt)
        return {"restruct": response.content}
    else:
        return {"restruct": ""}
    

def task_assignment_agent(state: State):
    messages = state["messages"][-10:]
    distortions = state["distortion"][-5:]
    # Generate a task if the accumulated messages are enough (adjust threshold as needed)
    user_messages = [msg.content for msg in messages if isinstance(msg, HumanMessage)]
    
    if state.get("task", "") != "" and sum(1 for dist in distortions if dist != "No") > 2: 
        prompt = (
            f"Previous User Messages: {user_messages}\n"
            f"Previously detected distortions: {distortions}\n"
            "You are an innovative cognitive behavioral therapist. Based on the conversation and the distortions provided, "
            "please generate a unique and creative CBT task for the user. Your task should go beyond "
            "just reframing negative thoughts and may include activities such as mindfulness exercises, "
            "journaling prompts, behavioral experiments, or reflective questions. Ensure that the task "
            "is varied and engaging each time."
            "Follow the given structure for the output: "
            "Task Name: \n"
            "Task Description: \n"
            "Task Goal: \n"   
        )
        response = llm.invoke(prompt)
        return {"task": response.content}
    else:
        return {"task": ""}

# def journal_report(state: State):
#     """
#     Generate a journal report using the conversation stored in MongoDB.
#     """
#     user_id = state.get("user_id")
#     doc = conversations_collection.find_one({"user_id": user_id})
#     conversation_array = doc.get("conversation", []) if doc else []
#     conversation_text = " ".join([f"User: {entry['user']} AI: {entry['ai']}" for entry in conversation_array])
#     try:
#         response = groq_client.chat.completions.create(
#             model="llama3-8b-8192",
#             messages=[
#                 {"role": "system", "content": "You are a therapist summarizing and analyzing the user's session progress."},
#                 {"role": "user", "content": f"Please analyze the following conversation and generate a detailed journal report with progress analysis:\n{conversation_text}"}
#             ]
#         )
#         state["summary"] = response.choices[0].message.content
#     except Exception:
#         state["summary"] = "Could not generate journal report."
#     return state

# Create workflow and add nodes/edges
workflow = StateGraph(State)
workflow.support_multiple_edges = True

workflow.add_node("detect_node", detect_cognitive_distortion)
workflow.add_node("summarize_conversation", summarize_history)
workflow.add_node("chat_node", chat_agent)
workflow.add_node("restructure_node", restructuring_agent)
workflow.add_node("task_node", task_assignment_agent)

workflow.add_edge(START, "summarize_conversation")
workflow.add_edge("summarize_conversation", "detect_node")
workflow.add_conditional_edges("detect_node", lambda x: x["distortion"] != "No", path_map={True: "restructure_node", False: "chat_node"})
workflow.add_edge("chat_node", "task_node")
workflow.add_edge("restructure_node", "chat_node")
workflow.add_edge("task_node", END)

assistant = workflow.compile(checkpointer=memory)