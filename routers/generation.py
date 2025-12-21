# routers/generation.py

from fastapi import APIRouter, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from faker import Faker
import random
import re
import time

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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    job_title: Optional[str] = None
    company: Optional[str] = None
    domain: Optional[str] = None
    format: Optional[str] = None

# --- Email Format Patterns ---
EMAIL_FORMATS = [
    "first.last",      # john.doe@example.com
    "first_last",      # john_doe@example.com
    "firstlast",       # johndoe@example.com
    "first-last",      # john-doe@example.com
    "flast",           # jdoe@example.com
    "firstl",          # johnd@example.com
    "f.last",          # j.doe@example.com
    "first.last.number",  # john.doe.123@example.com
    "firstnumber",     # john123@example.com
    "lastfirst",       # doejohn@example.com
    "last.first",      # doe.john@example.com
    "lastnumber",      # doe123@example.com
]

def generate_email_by_format(
    first_name: str,
    last_name: str,
    domain: str,
    format_type: str,
    include_number: bool = False
) -> str:
    """Generate email address based on specified format."""
    first = first_name.lower()
    last = last_name.lower()
    number = str(random.randint(100, 9999)) if include_number else ""
    
    format_map = {
        "first.last": f"{first}.{last}",
        "first_last": f"{first}_{last}",
        "firstlast": f"{first}{last}",
        "first-last": f"{first}-{last}",
        "flast": f"{first[0]}{last}",
        "firstl": f"{first}{last[0]}",
        "f.last": f"{first[0]}.{last}",
        "first.last.number": f"{first}.{last}.{number}",
        "firstnumber": f"{first}{number}",
        "lastfirst": f"{last}{first}",
        "last.first": f"{last}.{first}",
        "lastnumber": f"{last}{number}",
    }
    
    local_part = format_map.get(format_type, f"{first}.{last}")
    if include_number and format_type not in ["first.last.number", "firstnumber", "lastnumber"]:
        local_part = f"{local_part}{number}"
    
    return f"{local_part}@{domain}"

def validate_domain(domain: str) -> bool:
    """Validate domain format."""
    if not domain:
        return False
    # Basic domain validation
    pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))

def generate_realistic_domain() -> str:
    """Generate a realistic-looking domain."""
    # Mix of company names and common patterns
    patterns = [
        lambda: f"{fake.company().lower().replace(' ', '').replace(',', '').replace('.', '')}.{fake.tld()}",
        lambda: f"{fake.word().lower()}{fake.word().lower()}.{fake.tld()}",
        lambda: f"{fake.company().lower().split()[0] if fake.company().lower().split() else 'company'}.{fake.tld()}",
    ]
    domain = random.choice(patterns)()
    # Clean up domain
    domain = re.sub(r'[^a-z0-9.-]', '', domain)
    return domain

# --- API Endpoints ---

@router.get("/fake-email", summary="Generate Fake Emails (Enhanced)", response_model=List[FakeEmailResponse])
def generate_fake_email(
    count: int = Query(1, ge=1, le=1000, description="Number of emails to generate (max 1000)."),
    domain: Optional[str] = Query(None, description="Optional domain to use (e.g., 'example.com'). If not provided, generates realistic domains."),
    format: Optional[Literal["first.last", "first_last", "firstlast", "first-last", "flast", "firstl", "f.last", "first.last.number", "firstnumber", "lastfirst", "last.first", "lastnumber", "random"]] = Query(
        "random",
        description="Email format pattern. Use 'random' for varied formats."
    ),
    include_job_title: bool = Query(True, description="Include a fake job title with each email."),
    include_company: bool = Query(True, description="Include company name in response."),
    include_names: bool = Query(True, description="Include first and last names in response."),
    include_number: bool = Query(False, description="Add random numbers to email addresses."),
    locale: Optional[str] = Query("en_US", description="Faker locale for localized names (e.g., 'en_US', 'de_DE', 'fr_FR', 'es_ES')."),
):
    """
    Generate realistic fake email addresses with extensive customization options.
    
    Features:
    - Multiple email format patterns (12+ formats)
    - Realistic domain generation
    - Localized name generation
    - Optional metadata (job titles, company names)
    - Configurable number suffix
    - Support for up to 1000 emails per request
    """
    # Validate domain if provided
    if domain and not validate_domain(domain):
        raise HTTPException(
            status_code=400,
            detail="Invalid domain format. Domain must be a valid format (e.g., 'example.com')."
        )
    
    # Validate locale
    try:
        fake_locale = Faker(locale)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid locale '{locale}'. Use format like 'en_US', 'de_DE', etc."
        )
    
    # Validate count limit
    if count > 1000:
        raise HTTPException(
            status_code=400,
            detail="Maximum count is 1000 emails per request."
        )
    
    emails = []
    used_emails = set()  # Track to avoid duplicates
    
    for _ in range(count):
        # Generate names
        first_name = fake_locale.first_name()
        last_name = fake_locale.last_name()
        
        # Generate domain
        final_domain = domain if domain else generate_realistic_domain()
        
        # Select format
        if format == "random":
            selected_format = random.choice(EMAIL_FORMATS)
        else:
            selected_format = format
        
        # Generate email
        email = generate_email_by_format(
            first_name,
            last_name,
            final_domain,
            selected_format,
            include_number
        )
        
        # Ensure uniqueness - add number if duplicate
        original_email = email
        counter = 1
        while email in used_emails and counter < 1000:
            # Add a number to make it unique
            try:
                local_part, domain_part = email.split('@')
                # Remove any existing number suffix if present
                if counter == 1:
                    # Try to remove existing number suffix for cleaner emails
                    local_part = re.sub(r'\d+$', '', local_part)
                email = f"{local_part}{counter}@{domain_part}"
                counter += 1
            except ValueError:
                # Invalid email format, generate a new one
                email = f"{first_name.lower()}.{last_name.lower()}.{random.randint(1000, 9999)}@{final_domain}"
                break
        
        # If still duplicate after 1000 attempts, use timestamp
        if email in used_emails:
            local_part, domain_part = email.split('@')
            email = f"{local_part}.{int(time.time() * 1000) % 10000}@{domain_part}"
        
        used_emails.add(email)
        
        # Generate metadata
        job_title = fake_locale.job() if include_job_title else None
        company = fake_locale.company() if include_company else None
        
        # Build response
        email_data = {
            "email": email,
            "format": selected_format,
            "domain": final_domain
        }
        
        if include_names:
            email_data["first_name"] = first_name
            email_data["last_name"] = last_name
        
        if include_job_title and job_title:
            email_data["job_title"] = job_title
        
        if include_company and company:
            email_data["company"] = company
        
        emails.append(email_data)
    
    return emails
