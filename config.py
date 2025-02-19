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