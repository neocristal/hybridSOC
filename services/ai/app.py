from fastapi import FastAPI
import numpy as np

app = FastAPI()

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/anomaly")
def anomaly():
    score = int(np.random.randint(1,100))
    return {"risk_score": score}
