from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from api.routes import flashcards, words, examples, settings

app = FastAPI(
    title="German Language Learning API",
    description="Backend for the German Flashcard App",
    version="0.1.0"
)

# CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(flashcards.router, prefix="/flashcards", tags=["Flashcards"])
app.include_router(words.router, prefix="/words", tags=["Words"])
app.include_router(examples.router, prefix="/words", tags=["Examples"])
app.include_router(settings.router, prefix="/settings", tags=["Settings"])

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Mangum handler for AWS Lambda
handler = Mangum(app)
