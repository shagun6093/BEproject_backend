import os
from dotenv import load_dotenv, find_dotenv
from transformers import BertTokenizer, BertForSequenceClassification
from langgraph.graph import MessagesState
from langgraph.checkpoint.memory import MemorySaver


# Load environment variables
load_dotenv(find_dotenv())

# Load fine-tuned BERT model for cognitive distortion detection
bert_tokenizer = BertTokenizer.from_pretrained(os.getenv("BERT_TOKENIZER"), token=os.getenv("HF_TOKEN"))
bert_model = BertForSequenceClassification.from_pretrained(os.getenv("BERT_MODEL"), token=os.getenv("HF_TOKEN"))

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
    distortion: list[str]
    task: str
    answer: str
    summary: str
    restruct: str

memory = MemorySaver()