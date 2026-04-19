from fastapi import FastAPI
import random

app = FastAPI()

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/risk")
def risk():
    return {"risk_score": random.randint(1,100)}
