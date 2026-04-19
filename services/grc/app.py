from fastapi import FastAPI

app = FastAPI()

@app.post("/compliance")
def compliance():
    return {"framework":"ISO27001","status":"mapped"}
