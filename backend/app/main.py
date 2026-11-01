from fastapi import FastAPI

app = FastAPI(title="Guerreros Fit API")

@app.get("/api/health")
def health():
    return {"status": "ok"}