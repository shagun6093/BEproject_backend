from transformers import BertTokenizer, BertForSequenceClassification
import torch

tokenizer = BertTokenizer.from_pretrained("Tony25503/sentimentcbtbert", token="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")
model = BertForSequenceClassification.from_pretrained("Tony25503/sentimentcbtbert", num_labels=4, token="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")

label_mapping = {"Excellent": 3, "Very Good": 2, "Good": 1, "Poor": 0}
sentiment_mapping = {"Positive": 2, "Neutral": 1, "Negative": 0}

summary = "Great effort on attempting the CBT task! You acknowledged your emotions, which is a big step. Constructive feedback: Instead of focusing on the emotions, try to identify specific thoughts that contribute to your underconfidence and self-consciousness. Challenge those thoughts by reappraising them with evidence and reframe them in a more balanced way."
inputs = tokenizer(summary, return_tensors="pt", padding=True, truncation=True)

# Move inputs to the same device as the model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu") # Get the device
inputs = {k: v.to(device) for k, v in inputs.items()} # Move inputs to the device

with torch.no_grad():
    logits = model(**inputs).logits
prediction = torch.argmax(logits, dim=1).item()

# Map prediction back to label
predicted_label = [k for k, v in label_mapping.items() if v == prediction][0]
print(f"Predicted Rating: {predicted_label}")