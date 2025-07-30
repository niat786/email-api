# routers/validation.py

import re
import smtplib
import dns.resolver
import uuid
import urllib.request
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, status
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import io
import csv
import openpyxl

from config import DISPOSABLE_DOMAINS, SUSPICIOUS_TLDS, FREE_EMAIL_DOMAINS

# Strict email regex: allows alphanumeric and ._%+- separators, no leading/trailing special chars
EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9]+(?:[._%+-][A-Za-z0-9]+)*@"  # local part
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*"         # domain labels
    r"\.[A-Za-z]{2,}$"                          # TLD
)

# --- Router Setup ---
router = APIRouter(
    prefix="/validate",
    tags=["Validation"]
)

# --- Pydantic Models ---
class InboxStatusResponse(BaseModel):
    email: str
    is_valid_syntax: bool
    is_disposable: bool
    has_mx_records: bool
    is_deliverable_smtp: bool
    is_catch_all_domain: bool
    confidence_score: float = Field(..., ge=0, le=1)
    details: Dict[str, Any]

class SyntaxCheckResponse(BaseModel):
    email: str
    is_valid_syntax: bool

# --- Helper Functions ---

def is_valid_syntax(email: str) -> bool:
    """
    Strict syntax check using regex. Returns False for any disallowed characters.
    """
    return bool(EMAIL_REGEX.fullmatch(email))


def get_mx_records(domain: str):
    try:
        return dns.resolver.resolve(domain, 'MX')
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.DNSException):
        return None


def check_smtp_connection(email: str, mail_exchanger: str) -> (int, str):
    try:
        server = smtplib.SMTP(timeout=5)
        server.connect(mail_exchanger)
        server.ehlo()
        server.mail(f'test@{mail_exchanger}')
        code, message = server.rcpt(email)
        server.quit()
        return code, message.decode() if isinstance(message, bytes) else str(message)
    except Exception as e:
        return -1, str(e)


def check_http_status(domain: str) -> bool:
    """
    Returns True if HTTPS GET to domain returns 200 OK using urllib.
    """
    try:
        with urllib.request.urlopen(f"https://{domain}", timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False

# --- API Endpoints ---

@router.get(
    "/syntax",
    summary="Validate Email Syntax (Single)",
    response_model=SyntaxCheckResponse
)
async def validate_syntax_single(email: str = Query(..., description="Email to validate.")):
    """
    Checks if a single email address has a valid format using strict regex.
    """
    return {"email": email, "is_valid_syntax": is_valid_syntax(email)}

@router.post(
    "/syntax-bulk",
    summary="Validate Email Syntax (Bulk from File)",
    response_model=List[SyntaxCheckResponse]
)
async def validate_syntax_bulk(file: UploadFile = File(...)):
    """
    Checks a list of emails from a TXT, CSV, or XLSX file for valid syntax.
    """
    content = await file.read()
    filename = file.filename.lower()
    emails: List[str] = []
    try:
        if filename.endswith('.txt'):
            emails = content.decode('utf-8-sig').splitlines()
        elif filename.endswith('.csv'):
            reader = csv.reader(io.StringIO(content.decode('utf-8-sig')))
            emails = [row[0] for row in reader if row and row[0]]
        elif filename.endswith(('.xlsx', '.xls')):
            wb = openpyxl.load_workbook(io.BytesIO(content))
            sheet = wb.active
            emails = [str(row[0]) for row in sheet.iter_rows(values_only=True) if row and row[0]]
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported file type.")
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"File processing error: {e}")

    return [{"email": e.strip(), "is_valid_syntax": is_valid_syntax(e.strip())}
            for e in emails if e.strip()]

@router.get(
    "/inbox-status",
    summary="Advanced Inbox Availability Check",
    response_model=InboxStatusResponse
)
async def get_inbox_status(
    email: str = Query(..., description="The email address to analyze.")
):
    """
    Performs a comprehensive check: strict syntax, disposable/TLD, HTTP, MX, SMTP, catch-all, confidence.
    """
    details: Dict[str, Any] = {}

    # 1. Syntax validation
    if not is_valid_syntax(email):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid email syntax.")
    details['syntax'] = "Valid"

    domain = email.split('@', 1)[1].lower()
    tld = domain.rsplit('.', 1)[-1]

    # 2. Disposable & TLD check
   
    details['tld_check'] = "Suspicious TLD" if tld in SUSPICIOUS_TLDS else "TLD OK"

    # 3. HTTP status heuristic (skip check for known free providers)
    http_ok = domain in FREE_EMAIL_DOMAINS or check_http_status(domain)
    details['http_status'] = "200 OK" if http_ok else "Non-200 or unreachable"
    domain_suspicious = (domain in DISPOSABLE_DOMAINS or tld in SUSPICIOUS_TLDS or not http_ok)
    details['disposable_list'] = "This is a disposable email" if domain_suspicious else "Not a disposable email"

    if domain_suspicious:
        return InboxStatusResponse(
            email=email,
            is_valid_syntax=True,
            is_disposable=True,
            has_mx_records=False,
            is_deliverable_smtp=False,
            is_catch_all_domain=False,
            confidence_score=0.0,
            details=details
        )

    # 4. MX record check
    mx_records = get_mx_records(domain)
    has_mx = bool(mx_records)
    details['mx_records'] = "Found" if has_mx else "No MX records found"
    if not has_mx:
        return InboxStatusResponse(
            email=email,
            is_valid_syntax=True,
            is_disposable=False,
            has_mx_records=False,
            is_deliverable_smtp=False,
            is_catch_all_domain=False,
            confidence_score=0.1,
            details=details
        )

    # Prepare MX host for SMTP
    mx_host = str(mx_records[0].exchange)

    # 5. SMTP deliverability
    if domain in FREE_EMAIL_DOMAINS:
        # Skip SMTP probing for major email providers
        deliverable = True
        details['smtp'] = "Skipped SMTP checking for well known email provider"
    else:
        code, msg = check_smtp_connection(email, mx_host)
        deliverable = (code == 250)
        details['smtp'] = f"{code} {msg}"

    # 6. Catch-all detection
    is_catch_all = False
    if deliverable:
        fake_addr = f"{uuid.uuid4().hex}@{domain}"
        code2, _ = check_smtp_connection(fake_addr, mx_host)
        is_catch_all = (code2 == 250)
    details['catch_all'] = "Yes" if is_catch_all else "No"

    # 7. Confidence scoring
    score = 0.2  # syntax
    score += 0.2  # not disposable
    score += 0.2 if has_mx else 0.0
    score += 0.3 if deliverable else 0.0
    score += 0.1 if (deliverable and not is_catch_all) else 0.0
    confidence = round(min(score, 1.0), 2)

    return InboxStatusResponse(
        email=email,
        is_valid_syntax=True,
        is_disposable=False,
        has_mx_records=has_mx,
        is_deliverable_smtp=deliverable,
        is_catch_all_domain=is_catch_all,
        confidence_score=confidence,
        details=details
    )