"""Point d'entrée de l'API DataFlow360."""
from fastapi import FastAPI

app = FastAPI(
    title="DataFlow360 API",
    description="API de détection de fraude et de scoring de crédit",
    version="0.1.0"
)

@app.get("/")
def accueil():
    return {"message": "Bienvenue sur l'API DataFlow360"}

@app.get("/health")
def health():
    return {"status": "ok"}