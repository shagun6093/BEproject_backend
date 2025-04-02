import torch
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, RemoveMessage
from dotenv import load_dotenv, find_dotenv
import os
from typing import Literal
from langchain_groq import ChatGroq
from utils import State, bert_tokenizer, bert_model, label_map, memory, sentinment_tokenizer, sentiment_model, senti_mapping, negative_keywords, neutral_keywords, positive_keywords, device
    
# def should_continue(state: State) -> Literal["summarize_conversation", "detect_node"]:
#     """Return the next node to execute."""
#     messages = state["messages"]
#     # If there are more than six messages, then we summarize the conversation
#     if len(messages) > 6:
#         return "summarize_conversation"
#     # Otherwise we can just end
#     return "detect_node"

load_dotenv(find_dotenv())

llm = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama3-8b-8192", temperature=0.7)

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
    summarizer = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="mistral-saba-24b")    
    response = summarizer.invoke(messages)

    summary = response.content
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][-2:]]
    
    return {"summary": response.content}

def classifier_node(state: State):
    user_input = state["user_input"]
    
    prompt = (
        "You are an expert in cognitive behavioral therapy (CBT). Your task is to analyze the given message "
        "and determine if it contains a cognitive distortion. If it contains a distortion, respond with 'distortion'. "
        "If it is a general chat message, respond with 'chat'."
        "Only respond with 'distortion' or 'chat'.\n\n"
        f"Message: {user_input}\n"
    )
    
    classifier = ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="mistral-saba-24b", temperature=0.3, max_tokens=20) 
    response = classifier.invoke(prompt).content.strip().lower()
    print(response)
    
    if response != "distortion":
        state["distortion"].append("No Distortion")
        print(state["distortion"])
        return {"needs_distortion_check": response == "distortion", "distortion": state["distortion"]}
    
    return {"needs_distortion_check": response == "distortion"}

# Node functions
def detect_cognitive_distortion(state: State):
    print("entered detect node")
    distortion = state.get("distortion", [])
    print(distortion)
    inputs = bert_tokenizer(state["user_input"], return_tensors='pt', padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = bert_model(**inputs)
    predicted_class = torch.argmax(outputs.logits, dim=-1).item()
    new_distortion = label_map.get(predicted_class, None)
    distortion.append(new_distortion)
    return {"distortion": distortion}

def chat_agent(state: State):
    print("entered chat node")
    summary = state.get("summary", "")
    messages= state["messages"][-6:]
    distortion = state.get("distortion", [])
    # restruct = state.get("restruct", "")
    user_input = state["user_input"]
    
    print(messages)
    
    prompt = (
        f"You're 'MindMend', a CBT-informed chatbot helping users challenge negative thoughts.\n\n"
        f"Here’s the conversation summary so far: {summary}\n"
        f"User's previous history: {messages}\n"
        f"User's latest message: {user_input}\n\n"
        f"Previously detected distortion: {distortion}\n"
        "If recent messages contain consecutive 'No Distortion' detections, respond normally—engage in supportive conversation "
        "without reframing the user's input. Focus on thoughtful insights, validation, and guidance.\n\n"
        "However, if a cognitive distortion is detected in the latest message, help the user recognize it and reframe their thought "
        "gently. Offer an alternative perspective without dismissing their feelings. Keep the conversation balanced—blend supportive "
        "statements.\n\n"
        "If similar concerns have appeared in previous messages, acknowledge patterns while maintaining an engaging, professional, "
        "and warm tone.\n\n"
        "Ensure responses are under 75 words, combining insight, empathy, and meaningful dialogue."
    )

    # if restruct:
    #     prompt += (
    #         f"Previously detected distortion: {distortion}\n"
    #         f"AI-generated Reframed Thought: {restruct}\n\n"
    #         "Present the reframed thought to the user in a natural, encouraging way. "
    #         "Help them reflect on it, guiding them toward insight without forcing agreement. "
    #         "Keep the conversation balanced—mix statements with thoughtful follow-up questions. "
    #         "If similar thoughts have been expressed in previous messages, acknowledge them. "
    #         "Your tone should be warm, professional, and engaging. "
    #         "Ensure responses are under 75 words, blending supportive insights with meaningful dialogue."
    #     )
    # else:
    #     prompt += (
    #         "If the user expresses positive feelings, acknowledge and validate them. "
    #         "Keep the conversation balanced—mix statements with thoughtful follow-up questions. "
    #         "Your tone should be warm, professional, and engaging. "
    #         "Ensure responses are under 75 words, blending supportive insights with meaningful dialogue."
    #     )
    
    response = llm.invoke(prompt)
    
    return {"messages": [AIMessage(content=response.content)] }

def restructuring_agent(state: State):
    print("entered restructure node")
    if state["distortion"] != "No Distortion":
        prompt = (
            "You're an expert CBT therapist helping a user reframe their thoughts.\n\n"
            f"User's original message: {state['user_input']}\n"
            f"Detected Cognitive Distortion: {state['distortion']}\n\n"
            "Rewrite the user's thought in a way that helps them see it from a healthier, more balanced perspective. "
            "Make sure the new thought still feels natural and true to their experience."
        )
        response = llm.invoke(prompt)
        return {"restruct": response.content}
    else:
        return {"restruct": ""}
    

def task_assignment_agent(state: State):
    print("entered task node")
    messages = state["messages"][-10:]
    distortions = state.get("distortion", [])
    if len(distortions) > 2:
        distortions = distortions[-3:]
    # Generate a task if the accumulated messages are enough (adjust threshold as needed)
    user_messages = [msg.content for msg in messages if isinstance(msg, HumanMessage)]
    
    if state.get("task", "") == "" and sum(1 for dist in distortions if dist != "No Distortion") > 2: 
        prompt = (
            # f"Previous User Messages: {user_messages}\n"
            # f"Previously detected distortions: {distortions}\n\n"
            # "You're a CBT therapist. Based on the conversation, create a meaningful and engaging CBT task for the user. "
            # "This task should go beyond just reframing thoughts and include interactive or reflective activities. "
            # "Ensure it's unique and adapted to the user's challenges. "
            # "The task should be clear and concise, with a specific goal. "
            # "Format the task as follows:\n"
            # "Task Name:\n"
            # "Task Description:\n"
            # "Task Goal:\n"
            f"Previous User Messages: {user_messages}\n"
            f"Previously detected distortions: {distortions}\n\n"
            "You're a Cognitive Behavioral Therapy (CBT) therapist. Your goal is to generate a **practical and structured task** "
            "that helps the user actively work on their cognitive distortions.\n\n"
            "### Task Requirements:\n"
            "- The task must involve **real-world actions or structured self-reflection** (e.g., journaling, thought records, behavioral experiments).\n"
            "- Avoid abstract storytelling or metaphorical journeys.\n"
            "- Focus on **CBT-based exercises** like identifying distortions, evidence collection, or perspective shifting.\n"
            "- The task should be **simple, actionable, and specific** to the user’s messages and distortions.\n"
            "- Keep it concise while ensuring **clear steps** the user can follow.\n\n"
            "Format:"
            '"Task Name": "Short, clear task title",\n'
            '"Task Description": "Step-by-step instructions for the user to complete the task.",\n'
            '"Task Goal": "The intended benefit of completing the task."\n'
            "}"   
        )
        
        response = llm.invoke(prompt)
        return {"task": response.content}
    else:
        return {"task": ""}

def journal_report(feedback, task):
    print("entered journal node")
        # Step 2: *Model-based prediction if no keyword matches*
    inputs = sentinment_tokenizer(feedback, return_tensors="pt", padding=True, truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}  # Move inputs to device

    with torch.no_grad():
        logits = sentiment_model(**inputs).logits
        
    prediction = torch.argmax(logits, dim=1).item()
    
    prompt = (
        f"Task: {task}\n"
        f"Feedback: {feedback}\n"
        "You are a CBT therapist reviewing a user's journal entry. Provide constructive feedback on the user's reflections. "
        "If the feedback is unsatisfactory, provide suggestions for improvement. "
        "If the feedback is satisfactory, provide positive reinforcement. "
        "Ensure that the responses are under 150 words."
    )
    
    response = llm.invoke(prompt)
    return {"ai_feedback": response.content, "rating": prediction}
    

# Create workflow and add nodes/edges
workflow = StateGraph(state_schema=State)
workflow.support_multiple_edges = True

workflow.add_node("detect_node", detect_cognitive_distortion)
workflow.add_node("summarize_conversation", summarize_history)
workflow.add_node("classifier_node", classifier_node)
workflow.add_node("chat_node", chat_agent)
workflow.add_node("restructure_node", restructuring_agent)
workflow.add_node("task_node", task_assignment_agent)

workflow.add_edge(START, "summarize_conversation")
workflow.add_edge("summarize_conversation", "classifier_node")
workflow.add_conditional_edges("classifier_node", lambda x: x["needs_distortion_check"], path_map={True: "detect_node", False: "chat_node"})
# workflow.add_conditional_edges("detect_node", lambda x: x["distortion"] != "No Distortion", path_map={True: "restructure_node", False: "chat_node"})
workflow.add_edge("detect_node", "chat_node")
workflow.add_edge("chat_node", "task_node")
# workflow.add_edge("restructure_node", "chat_node")
# workflow.add_edge("task_node", END)

assistant = workflow.compile(checkpointer=memory)