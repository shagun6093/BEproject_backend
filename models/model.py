import torch
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, RemoveMessage
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser 
from dotenv import load_dotenv, find_dotenv
from transformers import AutoModelForSequenceClassification, AutoTokenizer, BertTokenizer, BertForSequenceClassification
import os
import groq
from langgraph.graph import MessagesState
from typing import List, Annotated


load_dotenv(find_dotenv())

# Load your fine-tuned BERT model for cognitive distortion detection
bert_tokenizer = BertTokenizer.from_pretrained(pretrained_model_name_or_path=os.getenv("BERT_TOKENIZER"), token=os.getenv("HF_TOKEN"))
bert_model = BertForSequenceClassification.from_pretrained(pretrained_model_name_or_path=os.getenv("BERT_MODEL"), token=os.getenv("HF_TOKEN"))

# Initialize Groq Client
groq_client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

label_map = {
    0: 'Control Fallacies',
    1: 'Blaming',
    2: 'Shoulds',
    3: "Heaven's Reward Fallacy",
    4: 'No',
    5: 'Jumping to Conclusions',
    6: 'Fallacy Of Fairness',
    7: 'Polarized',
    8: 'Overgeneralization',
    9: 'Global Labelling',
    10: 'Always Being Right',
    11: 'Catastrophizing',
    12: 'Filtering',
    13: 'Personalization',
    14: 'Fallacy Of Change',
    15: 'Emotional Reasoning'
}

class State(MessagesState):
    user_input: str
    distortion: str
    task: str
    answer: str
    summary: str
    restruct: str

def detect_cognitive_distortion(state: State):
    """Detects cognitive distortions in user input."""
    user_input = state.get("user_input", None)
    inputs = bert_tokenizer(user_input, return_tensors='pt', padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = bert_model(**inputs)
    predicted_class = torch.argmax(outputs.logits, dim=-1).item()
    distortion = label_map.get(predicted_class, None)  # Use None if not found
    state["distortion"] = distortion
    return state

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
    response = groq_client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {"role": "system", "content": messages}
        ]
    )

    state["summary"] = response.choices[0].message.content.strip()
    return state

# def build_dynamic_prompt(current_input):
#     """Builds a dynamic prompt that includes a summary of recent conversation."""
#     summary = summarize_history(conversation_memory)
#     prompt = (
#         f"Summary of previous conversations: {summary}\n"
#         f"User now says: {current_input}\n"
#         "You are a cognitive behavioral therapist. Your task is to help users explore their thoughts and feelings in a supportive way. If the user responds positively, encourage the user."
#     )
#     return prompt

def chat_agent(state: State):
    """Handles natural conversation with the user."""
    
    if state['restruct'] != None:
      prompt = (
          f"User now says: {state['user_input']}\n"
          f"Cognitive Distortion: {state['distortion']}\n"
          f"Restructured sentence: {state['restruct']}\n"
          "You are a cognitive behavioral therapist. Your task is to present the restructured sentence to the user in a supportive way."
      )
    else:
      prompt = (
          f"User now says: {state['user_input']}\n"
          "You are a cognitive behavioral therapist. Your task is to help users explore their thoughts and feelings in a supportive way. If the user responds positively, encourage the user."
      )

    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}]
    )
    ai_response = response.choices[0].message.content
    
    state["answer"] = ai_response
    
    return {
        "messages": [
            HumanMessage(content=state['user_input']),
            AIMessage(content=ai_response)
        ],
        "answer": state["answer"]
    }

def restructuring_agent(state: State):
    """Reframes distorted thoughts when needed."""
    # Only reframe if a clear distortion is detected
    distortion = state["distortion"]
    user_input = state["user_input"]
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": f"Based on the cognitive behavioral therapy technique of cognitive restructuring to reframe the sentence entered by the user to a positive and constructive thought. Cognitive Distortion: {distortion}\n"},
            {"role": "user", "content": user_input}
        ]
    )
    ai_response = response.choices[0].message.content
    state["restruct"] = ai_response
    return state


def task_assignment_agent(state: State):
    """
    Decides whether to assign a task.
    For example, if the last few user messages contain persistent negativity,
    assign a reflective exercise.
    """
    negative_count = 0
    history = state["messages"]  # List of HumanMessage and AIMessage objects
    
    # Extract only user messages from the last few interactions
    user_messages = [msg.content for msg in history[-6:] if isinstance(msg, HumanMessage)]
    
    for text in user_messages:
        distortion = detect_cognitive_distortion(text)
        if distortion != "No":
            negative_count += 1
    
    if negative_count >= 2:
        # Only assign a task if there is repeated distress, otherwise let the conversation flow naturally.
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a cognitive behavioral therapist. Based on the following conversation history, generate a very brief behavioral activation task to help the user change their negative thinking pattern. The task should be something the user can do in their day-to-day life and should resonate with their previous conversations. Avoid excessive details. Provide the response in a conversational manner.\n\n"
            f"Conversation History: {user_messages}\n\nTask:"}
            ]
        )
        state["task"] = response.choices[0].message.content
    return state



# def read_journal_entry(journal_entry):
#     """Reads and responds to the user's journal entry."""
#     response = groq_client.chat.completions.create(
#         model="llama3-8b-8192",
#         messages=[
#             {"role": "system", "content": "You analyze a user's journal entry and provide thoughtful, supportive feedback."},
#             {"role": "user", "content": journal_entry}
#         ]
#     )
#     return response.choices[0].message.content

# def track_progress():
#     """Provides a simple progress report based on conversation history."""
#     progress_report = "Reviewing your progress:\n"
#     # Naively count positive markers (you could use more sophisticated sentiment tracking)
#     positive_count = sum(1 for msg in conversation_memory if "No" in msg or "happy" in msg.lower() or "good" in msg.lower())
#     total = len(conversation_memory)
#     if total:
#         progress_report += f"You've had {positive_count} positive remarks out of {total} interactions.\n"
#     else:
#         progress_report += "Let's begin tracking your progress.\n"
#     progress_report += "Keep up the reflective work—small improvements add up over time."
#     return progress_report


workflow = StateGraph(State)
workflow.support_multiple_edges = True

# Use unique node names that do not conflict with the state schema keys.
workflow.add_node("detect_node", detect_cognitive_distortion)
workflow.add_node("chat_node", chat_agent)
workflow.add_node("restructure_node", restructuring_agent)
workflow.add_node("task_node", task_assignment_agent)

# Connect nodes by referring to these new names.
workflow.add_edge(START, "detect_node")
workflow.add_conditional_edges("detect_node", lambda x: x["distortion"] != "No", path_map={True: "restructure_node", False: "chat_node"})
workflow.add_edge("chat_node", "task_node")
workflow.add_edge("restructure_node", "chat_node")
workflow.add_edge("task_node", END)


memory = MemorySaver()
assistant = workflow.compile(checkpointer=memory)

config = {"configurable": {"thread_id": 123}}
user = "I'm so stupid, everyone hates me."
initial_state = State(user_input=user)

fin = assistant.invoke(initial_state, config)
print(fin["messages"])