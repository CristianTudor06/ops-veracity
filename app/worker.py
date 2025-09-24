import torch
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
from app.celery_config import celery_app
import time
import sqlite3
import os

DB_PATH = "/database/queries.db"

def init_db():
    """Create the database table if it doesn't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        query_text TEXT NOT NULL,
        prediction TEXT NOT NULL,
        confidence REAL NOT NULL,
        processing_time_seconds REAL NOT NULL
    )
    """)
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

MODEL_PATH = "/code/model/detector_model"
print("Loading model...")
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval()
print("Model loaded successfully.")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

init_db()

@celery_app.task(name="analyze_text_task")
def analyze_text_task(text: str):
    """
    Celery task to analyze text and now also LOG the result to the database.
    """
    start_time = time.time()
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512).to(device)
    
    with torch.no_grad():
        logits = model(**inputs).logits
    
    probabilities = torch.softmax(logits, dim=1).squeeze()
    
    predicted_class_id = torch.argmax(probabilities).item()
    confidence_score = probabilities[predicted_class_id].item()
    
    label_map = {0: "Human-written", 1: "AI-generated"}
    prediction = label_map[predicted_class_id]
    
    end_time = time.time()
    processing_time = round(end_time - start_time, 4)

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO queries (query_text, prediction, confidence, processing_time_seconds) VALUES (?, ?, ?, ?)",
            (text, prediction, round(confidence_score * 100, 2), processing_time)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database logging failed: {e}")

    return {
        "prediction": prediction,
        "confidence": round(confidence_score * 100, 2),
        "processing_time_seconds": processing_time
    }