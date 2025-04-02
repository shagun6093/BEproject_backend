from transformers import BertTokenizer, BertForSequenceClassification
import torch

tokenizer = BertTokenizer.from_pretrained("Tony25503/sentimentcbtbert", token="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")
model = BertForSequenceClassification.from_pretrained("Tony25503/sentimentcbtbert", num_labels=4, token="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")

label_mapping = {"Excellent": 3, "Very Good": 2, "Good": 1, "Poor": 0}
sentiment_mapping = {"Positive": 2, "Neutral": 1, "Negative": 0}

summary = "Really poor, I couldn't do the task, nothing worked, I was stuck the whole time. I don't know what to do, I am really confused. I don't know how to proceed."
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