# app/main.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from celery.result import AsyncResult
from worker import analyze_text_task 
import redis
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Text Detection API")


origins = ["*"] 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Redis to store results
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

class TextIn(BaseModel):
    text: str

class TaskOut(BaseModel):
    task_id: str

@app.post("/analyze", response_model=TaskOut, status_code=202)
def submit_analysis(text_in: TextIn):
    """
    Accepts text and queues it for analysis.
    Returns a task ID to check for results later.
    """
    task = analyze_text_task.delay(text_in.text)
    return {"task_id": task.id}

@app.get("/results/{task_id}")
def get_results(task_id: str):
    """
    Fetches the result of a specific task.
    """
    task_result = AsyncResult(task_id, app=analyze_text_task.app)

    if not task_result.ready():
        return {"status": "processing"}

    result = task_result.get()
    return {"status": "complete", "result": result}