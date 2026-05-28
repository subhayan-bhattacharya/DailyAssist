from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from api.auth import get_user_context
from api.routes import flashcards, words, examples, settings, prompts

app = FastAPI(
    title="German Language Learning API",
    description="Backend for the German Flashcard App",
    version="0.1.0"
)

# CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://poulomi-subhayan.click",
        "https://flashcards.poulomi-subhayan.click",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

authenticated_route_dependencies = [Depends(get_user_context)]

# Include routers
app.include_router(
    flashcards.router,
    prefix="/flashcards",
    tags=["Flashcards"],
    dependencies=authenticated_route_dependencies,
)
app.include_router(
    words.router,
    prefix="/words",
    tags=["Words"],
    dependencies=authenticated_route_dependencies,
)
app.include_router(
    examples.router,
    prefix="/words",
    tags=["Examples"],
    dependencies=authenticated_route_dependencies,
)
app.include_router(
    settings.router,
    prefix="/settings",
    tags=["Settings"],
    dependencies=authenticated_route_dependencies,
)
app.include_router(
    prompts.router,
    prefix="/prompts",
    tags=["Prompts"],
    dependencies=authenticated_route_dependencies,
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Mangum handler for AWS Lambda
handler = Mangum(app)
