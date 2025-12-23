# main.py

from fastapi import FastAPI
from routers import validation, generation

# --- Application Setup ---
app = FastAPI(
    title="MailFlow API: Advanced Email Toolkit",
    description="A comprehensive API to validate, generate, and send emails.",
    version="3.0.0",
    contact={
        "name": "API Support",
        "url": "http://example.com/support",
        "email": "support@example.com",
    },
)

# --- Include Routers ---
# This keeps your main file clean and organized.
app.include_router(validation.router)
app.include_router(generation.router)
# app.include_router(communication.router)


# --- Root Endpoint ---
@app.get("/", tags=["General"])
def read_root():
    """A simple welcome endpoint to confirm the API is running."""
    return {"message": "Welcome to the PaperInbox API"}
