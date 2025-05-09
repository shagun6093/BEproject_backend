import os
from dotenv import load_dotenv, find_dotenv
from transformers import BertTokenizer, BertForSequenceClassification
from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import MemorySaver
import torch

# Load environment variables
load_dotenv(find_dotenv())

# Load fine-tuned BERT model for cognitive distortion detection
bert_tokenizer = BertTokenizer.from_pretrained(os.getenv("BERT_TOKENIZER"), token=os.getenv("HF_TOKEN"))
bert_model = BertForSequenceClassification.from_pretrained(os.getenv("BERT_MODEL"), token=os.getenv("HF_TOKEN"))

sentinment_tokenizer = BertTokenizer.from_pretrained(os.getenv("SENTIMENT_MODEL"), token=os.getenv("HF_TOKEN"))
sentiment_model = BertForSequenceClassification.from_pretrained(os.getenv("SENTIMENT_MODEL"), token=os.getenv("HF_TOKEN"))

# Move model to the appropriate device (CPU/GPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
sentiment_model.to(device)
sentiment_model.eval()  # Set model to evaluation mode


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

# Define label mapping (Removed "Very Good" and mapped it to "Good")
senti_mapping = {"Excellent": 3, "Very Good": 2, "Good": 1, "Poor": 0}

# Keyword-based sentiment classification
negative_keywords = {"underconfident", "conscious", "anxious", "nervous", "doubtful", "unsure"}
neutral_keywords = {"okay", "fine", "neutral", "satisfactory", "not bad", "average"}
positive_keywords = {"confident", "happy", "proud", "successful", "accomplished", "great", "excellent"}

# Define our State class. It behaves like a dict.
class State(MessagesState):
    user_input: str
    distortion: list[str]
    task: str
    answer: str
    summary: str
    restruct: str

memory = MemorySaver()