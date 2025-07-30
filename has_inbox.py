# routers/validation.py

import smtplib
import socket
import dns.resolver
import uuid
from fastapi import APIRouter, HTTPException, status, Query
from pydantic import EmailStr, BaseModel, Field
from typing import Dict, Any

# Improvement: Reading from a local, user-controlled file is more reliable
# than a library that may not be updated frequently.
# This requires a `config.py` file in your project root.
from config import DISPOSABLE_DOMAINS

# Create an APIRouter instance for validation endpoints
router = APIRouter(
    prefix="",  # Using an empty prefix as requested
    tags=["Email Inbox Validation"] 
)

# --- Pydantic Models for the new endpoint's response ---
# Improved model to be more consistent.
class InboxStatusResponse(BaseModel):
    email: EmailStr
    is_valid_syntax: bool = Field(..., description="Indicates if the email format is syntactically correct.")
    is_disposable: bool = Field(..., description="Indicates if the email belongs to a known disposable email provider.")
    has_mx_records: bool = Field(..., description="Indicates if the domain has valid Mail Exchange (MX) records.")
    is_deliverable_smtp: bool = Field(..., description="Indicates if the specific mailbox responded positively to an SMTP check.")
    is_catch_all_domain: bool = Field(..., description="Indicates if the domain appears to accept all emails, regardless of the local part.")
    confidence_score: float = Field(..., ge=0, le=1, description="A score from 0.0 to 1.0 indicating the confidence in the email's deliverability.")
    details: Dict[str, Any] = Field(..., description="A dictionary containing detailed results of each check.")

# --- Helper Functions for Live SMTP Checks ---

def get_mx_records(domain: str):
    """Resolves MX records for a given domain."""
    try:
        return dns.resolver.resolve(domain, 'MX')
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return None

def check_smtp_connection(email: str, mail_exchanger: str) -> (int, str):
    """Performs an SMTP RCPT TO command and returns the server's response code and message."""
    try:
        server = smtplib.SMTP(timeout=5)
        server.connect(mail_exchanger)
        server.helo(server.local_hostname)
        server.mail('test@example.com')
        code, message = server.rcpt(email)
        server.quit()
        return code, message
    except (smtplib.SMTPConnectError, socket.timeout, smtplib.SMTPServerDisconnected):
        return -1, "Connection failed"
    except Exception as e:
        return -1, str(e)

# --- Existing Endpoint for backward compatibility ---

@router.get("/has-inbox", summary="Check if Mailbox Can Receive Email (Simple SMTP)")
async def check_has_inbox(email: EmailStr = Query(..., description="The email address to verify.")):
    mx_records = get_mx_records(email.split('@')[1])
    if not mx_records:
        return {"email": email, "has_inbox": False, "status": "success"}
    
    code, _ = check_smtp_connection(email, str(mx_records[0].exchange))
    return {"email": email, "has_inbox": code == 250, "status": "success"}


# --- Improved Advanced Inbox Status Endpoint ---

@router.get("/inbox-status", summary="Advanced Inbox Availability Check", response_model=InboxStatusResponse)
async def get_inbox_status(email: EmailStr = Query(..., description="The email address to analyze.")):
    """
    Performs a comprehensive, multi-step check to determine inbox availability and deliverability confidence.
    
    Checks include:
    - **Syntax:** Validates the email format.
    - **Disposable Email:** Identifies if the email is from a temporary provider.
    - **MX Records:** Confirms the domain is configured to receive mail.
    - **SMTP Response:** Verifies the specific mailbox with the mail server.
    - **Catch-all Detection:** Determines if the server accepts emails to non-existent mailboxes.
    """
    domain = email.split('@')[1].lower()
    details = {}

    # Step 1: Syntax Check (handled by Pydantic's EmailStr)
    is_valid_syntax = True
    details['syntax_check'] = "Valid format"

    # Step 2: Disposable Domain Check (High Priority)
    # Logical Fix: This now checks against the user-controlled DISPOSABLE_DOMAINS set.
    is_disposable = domain in DISPOSABLE_DOMAINS
    details['disposable_check'] = "Domain is a known disposable provider" if is_disposable else "Domain is not a known disposable provider"
    
    # If the domain is disposable, we should stop immediately.
    if is_disposable:
        return InboxStatusResponse(
            email=email, is_valid_syntax=True, is_disposable=True, has_mx_records=False,
            is_deliverable_smtp=False, is_catch_all_domain=False, confidence_score=0.01, details=details
        )

    # Step 3: MX Record Check
    mx_records = get_mx_records(domain)
    has_mx_records = mx_records is not None
    details['mx_check'] = "MX records found" if has_mx_records else "No MX records found"
    
    if not has_mx_records:
        return InboxStatusResponse(
            email=email, is_valid_syntax=True, is_disposable=False, has_mx_records=False,
            is_deliverable_smtp=False, is_catch_all_domain=False, confidence_score=0.10, details=details
        )
    mail_exchanger = str(mx_records[0].exchange)

    # Step 4: SMTP Response Check for the actual email
    smtp_code, _ = check_smtp_connection(email, mail_exchanger)
    is_deliverable_smtp = smtp_code == 250
    details['smtp_check'] = f"Mailbox check returned code {smtp_code} ({'OK' if is_deliverable_smtp else 'Failed'})"

    # Step 5: Catch-all Detection
    is_catch_all = False
    if is_deliverable_smtp:
        random_user = uuid.uuid4().hex
        catch_all_email = f"{random_user}@{domain}"
        catch_all_code, _ = check_smtp_connection(catch_all_email, mail_exchanger)
        is_catch_all = catch_all_code == 250
    details['catch_all_check'] = "Domain appears to be a catch-all" if is_catch_all else "Domain is not a catch-all"
    
    # Step 6: Calculate Final Confidence Score
    confidence = 0.0
    if is_valid_syntax: confidence += 0.10
    if not is_disposable: confidence += 0.15
    if has_mx_records: confidence += 0.25
    if is_deliverable_smtp:
        confidence += 0.40
        if not is_catch_all:
            confidence += 0.10

    final_confidence = min(round(confidence, 2), 1.0)

    return InboxStatusResponse(
        email=email,
        is_valid_syntax=is_valid_syntax,
        is_disposable=is_disposable,
        has_mx_records=has_mx_records,
        is_deliverable_smtp=is_deliverable_smtp,
        is_catch_all_domain=is_catch_all,
        confidence_score=final_confidence,
        details=details
    )
