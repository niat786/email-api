# routers/generation.py

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List
from faker import Faker

# --- Router Setup ---
router = APIRouter(
    prefix="/generate",
    tags=["Generation"]
)

# --- Faker Instance ---
fake = Faker()

# --- Pydantic Models ---
class FakeEmailResponse(BaseModel):
    email: str
    job_title: Optional[str] = None

# --- API Endpoints ---

@router.get("/fake-email", summary="Generate Fake Emails", response_model=List[FakeEmailResponse])
def generate_fake_email(
    count: int = Query(1, ge=1, le=100, description="Number of emails to generate."),
    domain: Optional[str] = Query(None, description="Optional domain to use (e.g., 'example.com')."),
    include_job_title: bool = Query(True, description="Include a fake job title with each email.")
):
    """Generates one or more plausible-looking but fake business emails."""
    if domain and ('.' not in domain or ' ' in domain):
        raise HTTPException(status_code=400, detail="Invalid domain format provided.")

    emails = []
    for _ in range(count):
        first_name = fake.first_name().lower()
        last_name = fake.last_name().lower()
        
        final_domain = domain if domain else fake.company().lower().replace(" ", "").replace(",", "") + "." + fake.tld()
        
        email = f"{first_name}.{last_name}@{final_domain}"
        job_title = fake.job() if include_job_title else None
        emails.append({"email": email, "job_title": job_title})
    
    return emails
