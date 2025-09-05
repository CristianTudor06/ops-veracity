# app/worker.py
import torch
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
from .celery_config import celery_app
import time

# Load the model and tokenizer ONCE when the worker starts
MODEL_PATH = "/app/model/detector_model"
print("Loading model...")
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval() # Set model to evaluation mode
print("Model loaded successfully.")

# Use GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

@celery_app.task(name="analyze_text_task")
def analyze_text_task(text: str):
    """
    Celery task to analyze text using the loaded model.
    """
    start_time = time.time()
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512).to(device)
    
    with torch.no_grad():
        logits = model(**inputs).logits
    
    # Apply softmax to get probabilities
    probabilities = torch.softmax(logits, dim=1).squeeze()
    
    # Get the prediction and confidence score
    predicted_class_id = torch.argmax(probabilities).item()
    confidence_score = probabilities[predicted_class_id].item()
    
    label_map = {0: "Human-written", 1: "AI-generated"}
    prediction = label_map[predicted_class_id]
    
    end_time = time.time()
    
    return {
        "prediction": prediction,
        "confidence": round(confidence_score * 100, 2),
        "processing_time_seconds": round(end_time - start_time, 4)
    }