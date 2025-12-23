# routers/validation.py

import re
import math
import smtplib
import dns.resolver
import uuid
import urllib.request
import urllib.error
import ssl
import asyncio
import socket
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, status, Body
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Tuple
import io
import csv
import openpyxl
import time
from rapidfuzz import process, fuzz
from gibberish_detector import detector
import gender_guesser.detector as gender

from config import DISPOSABLE_DOMAINS, SUSPICIOUS_TLDS, WELL_EMAIL_DOMAINS, PAID_EMAIL_DOMAINS

# Strict email regex: allows alphanumeric and ._%+- separators, no leading/trailing special chars
EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9]+(?:[._%+-][A-Za-z0-9]+)*@"  # local part
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*"         # domain labels
    r"\.[A-Za-z]{2,}$"                          # TLD
)

# Role-based email prefixes (common non-personal email addresses)
ROLE_BASED_PREFIXES = {
    'admin', 'administrator', 'contact', 'info', 'support', 'help', 'sales', 
    'marketing', 'noreply', 'no-reply', 'donotreply', 'webmaster', 'postmaster',
    'hostmaster', 'abuse', 'security', 'privacy', 'legal', 'billing', 'accounts',
    'accounting', 'hr', 'humanresources', 'jobs', 'careers', 'newsletter', 'news',
    'press', 'media', 'publicrelations', 'pr', 'customer', 'customerservice',
    'service', 'helpdesk', 'tech', 'technical', 'it', 'dev', 'development',
    'engineering', 'ops', 'operations', 'finance', 'payments', 'orders',
    'shipping', 'delivery', 'returns', 'refunds', 'complaints', 'feedback'
}

# Initialize AI analysis tools
_gender_detector = gender.Detector(case_sensitive=False)
_gibberish_model = None
try:
    _gibberish_model = detector.create_from_model('big.model')
except Exception:
    _gibberish_model = None

# --- Router Setup ---
router = APIRouter(
    prefix="/validate",
    tags=["Validation"]
)

# --- Thread Pool for blocking operations ---
executor = ThreadPoolExecutor(max_workers=10)

# --- Pydantic Models ---
class InboxStatusResponse(BaseModel):
    email: str
    is_valid_syntax: bool
    is_disposable: bool
    has_mx_records: bool
    is_deliverable_smtp: bool
    is_catch_all_domain: bool
    is_role_based: bool = False
    is_paid_domain: bool = False
    confidence_score: float = Field(..., ge=0, le=1)
    details: Dict[str, Any]

class SyntaxCheckResponse(BaseModel):
    email: str
    is_valid_syntax: bool
    error_message: Optional[str] = None

class BulkValidationRequest(BaseModel):
    emails: List[str] = Field(..., min_items=1, max_items=1000, description="List of email addresses to validate")

class BulkInboxStatusResponse(BaseModel):
    total: int
    valid_count: int
    invalid_count: int
    results: List[InboxStatusResponse]

# --- Helper Functions ---

def is_valid_syntax(email: str) -> Tuple[bool, Optional[str]]:
    """
    Strict syntax check using regex. Returns (is_valid, error_message).
    """
    if not email or not isinstance(email, str):
        return False, "Email is empty or invalid type"
    
    email = email.strip().lower()
    
    if not EMAIL_REGEX.fullmatch(email):
        return False, "Invalid email format"
    
    # Additional checks
    local_part, domain_part = email.split('@', 1)
    
    # Check local part length (RFC 5321: 64 chars max)
    if len(local_part) > 64:
        return False, "Local part exceeds 64 characters"
    
    # Check domain length (RFC 5321: 255 chars max)
    if len(domain_part) > 255:
        return False, "Domain exceeds 255 characters"
    
    # Check for consecutive dots
    if '..' in local_part or '..' in domain_part:
        return False, "Consecutive dots not allowed"
    
    # Check for leading/trailing dots
    if local_part.startswith('.') or local_part.endswith('.'):
        return False, "Local part cannot start or end with a dot"
    
    if domain_part.startswith('.') or domain_part.endswith('.'):
        return False, "Domain cannot start or end with a dot"
    
    return True, None


def is_role_based_email(email: str) -> bool:
    """Check if email is role-based (non-personal)."""
    local_part = email.split('@', 1)[0].lower()
    # Check if local part matches role-based patterns
    return local_part in ROLE_BASED_PREFIXES or any(
        local_part.startswith(prefix) for prefix in ROLE_BASED_PREFIXES
    )


def detect_domain_typo(domain: str) -> Dict[str, Any]:
    """
    Uses Fuzzy Logic to find if 'gmil.com' was actually meant to be 'gmail.com'
    Returns dict with has_typo, suggestion, and confidence.
    Uses WELL_EMAIL_DOMAINS from config for trusted domains list.
    """
    # Convert set to list for rapidfuzz
    trusted_domains_list = list(WELL_EMAIL_DOMAINS) if WELL_EMAIL_DOMAINS else []
    
    if not trusted_domains_list:
        return {"has_typo": False, "suggestion": None, "confidence": 0}
    
    match = process.extractOne(domain, trusted_domains_list, scorer=fuzz.ratio)
    
    # If match confidence is > 85 (high) but not 100 (exact), it's a typo
    if match and 85 < match[1] < 100:
        return {"has_typo": True, "suggestion": match[0], "confidence": match[1]}
    return {"has_typo": False, "suggestion": None, "confidence": 0}


def _calculate_entropy(text: str) -> float:
    """Calculates randomness of a string (entropy)."""
    if not text:
        return 0.0
    prob = [float(text.count(c)) / len(text) for c in dict.fromkeys(list(text))]
    return -sum([p * math.log(p) / math.log(2.0) for p in prob if p > 0])


def detect_gibberish(local_part: str) -> Dict[str, Any]:
    """
    Checks if the username part (e.g., 'asdfghjkl') is likely gibberish/bot-generated.
    Returns dict with is_gibberish boolean.
    """
    is_gibberish = False
    
    if _gibberish_model:
        is_gibberish = _gibberish_model.is_gibberish(local_part)
    else:
        # Fallback: High entropy usually means random keys
        entropy = _calculate_entropy(local_part)
        if entropy > 3.5:  # Threshold for randomness
            is_gibberish = True
    
    return {"is_gibberish": is_gibberish}


def infer_demographics(local_part: str) -> Dict[str, Any]:
    """
    Tries to guess name and gender from email local part: 'john.smith.123' -> 'male'
    Returns dict with likely_name, likely_gender, and confidence.
    """
    # Clean the string: remove numbers and dots to isolate the name
    clean_name = re.split(r'[._0-9]', local_part)[0]
    
    if not clean_name:
        return {
            "likely_name": None,
            "likely_gender": "unknown",
            "confidence": "low"
        }
    
    # Guess gender
    guessed_gender = _gender_detector.get_gender(clean_name)
    
    # Normalize response
    confidence = "low"
    if guessed_gender in ['male', 'female']:
        confidence = "high"
    elif guessed_gender in ['mostly_male', 'mostly_female']:
        confidence = "medium"
    
    return {
        "likely_name": clean_name.capitalize(),
        "likely_gender": guessed_gender,
        "confidence": confidence
    }


def get_mx_records(domain: str, timeout: int = 5):
    """Get MX records for domain with timeout."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = timeout
        resolver.lifetime = timeout
        mx_records = resolver.resolve(domain, 'MX')
        # Sort by priority (lower is better)
        sorted_mx = sorted(mx_records, key=lambda x: x.preference)
        return sorted_mx
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return None
    except dns.exception.DNSException as e:
        return None
    except Exception:
        return None


def check_smtp_connection(email: str, mail_exchanger: str, timeout: int = 5, max_retries: int = 1) -> Tuple[int, str]:
    """Check SMTP connection with retries and better error handling."""
    for attempt in range(max_retries + 1):
        try:
            server = smtplib.SMTP(timeout=timeout)
            server.set_debuglevel(0)
            server.connect(mail_exchanger, 25)
            server.ehlo()
            server.mail('test@example.com')
            code, message = server.rcpt(email)
            server.quit()
            
            message_str = message.decode('utf-8', errors='ignore') if isinstance(message, bytes) else str(message)
            return code, message_str
        except smtplib.SMTPServerDisconnected:
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))
                continue
            return -1, "SMTP server disconnected"
        except smtplib.SMTPConnectError as e:
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))
                continue
            return -1, f"SMTP connection error: {str(e)}"
        except socket.timeout:
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))
                continue
            return -1, "SMTP connection timeout"
        except Exception as e:
            if attempt < max_retries:
                time.sleep(0.5 * (attempt + 1))
                continue
            return -1, f"SMTP error: {str(e)}"
    
    return -1, "SMTP check failed after retries"


async def check_smtp_connection_async(email: str, mail_exchanger: str, timeout: int = 5, max_retries: int = 1) -> Tuple[int, str]:
    """Async wrapper for SMTP connection check."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        check_smtp_connection,
        email,
        mail_exchanger,
        timeout,
        max_retries
    )


async def check_http_status_async(domain: str, timeout: int = 3) -> bool:
    """
    Robust check: Tries HTTPS then HTTP with browser headers.
    Returns True if a valid website exists.
    
    Features:
    - Browser-like User-Agent to avoid blocking by security firewalls (Cloudflare, etc.)
    - Handles SSL certificate issues gracefully
    - Tries both HTTPS and HTTP
    - Considers 200, 403, 401, 301, 302 as valid (server exists)
    """
    
    # Fake a browser User-Agent to avoid being blocked by security firewalls (Cloudflare, etc.)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    def _check_url(url):
        try:
            req = urllib.request.Request(url, headers=headers)
            # Create unverified context to avoid SSL cert errors on minor misconfigurations
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with urllib.request.urlopen(req, timeout=timeout, context=context) as resp:
                # We consider 200 (OK) and 403 (Forbidden) as "Valid Website Exists"
                # 403 usually means a protected real site, whereas disposable domains usually Connection Refuse or 404.
                # Also accept redirects (301, 302) as valid
                return resp.status in [200, 403, 301, 302]
        except urllib.error.HTTPError as e:
            # If we get a 403/401, a server exists and is protecting content -> Likely Valid
            if e.code in [403, 401]:
                return True
            return False
        except Exception:
            return False

    loop = asyncio.get_event_loop()
    
    # 1. Try HTTPS first (Standard for modern web)
    https_valid = await loop.run_in_executor(executor, _check_url, f"https://{domain}")
    if https_valid:
        return True
        
    # 2. Fallback to HTTP (For older legitimate domains)
    http_valid = await loop.run_in_executor(executor, _check_url, f"http://{domain}")
    return http_valid


async def validate_inbox_status_single(email: str, skip_smtp: bool = True) -> InboxStatusResponse:
    """Validate a single email's inbox status (async) - Optimized for speed."""
    details: Dict[str, Any] = {}
    
    # 1. Syntax validation - EARLY RETURN if invalid (fastest check)
    is_valid, error_msg = is_valid_syntax(email)
    if not is_valid:
        return InboxStatusResponse(
            email=email,
            is_valid_syntax=False,
            is_disposable=False,
            has_mx_records=False,
            is_deliverable_smtp=False,
            is_catch_all_domain=False,
            is_role_based=False,
            is_paid_domain=False,
            confidence_score=0.0,
            details={"syntax": f"Invalid: {error_msg}"}
        )
    details['syntax'] = "Valid"
    
    email_lower = email.lower()
    domain = email_lower.split('@', 1)[1]
    tld = domain.rsplit('.', 1)[-1]
    local_part = email_lower.split('@', 1)[0]
    
    # 2. Check if well-known email provider - FAST PATH
    is_well_known = domain in WELL_EMAIL_DOMAINS
    is_paid_domain = domain in PAID_EMAIL_DOMAINS
    
    # 3. Role-based check (fast, no I/O)
    is_role_based = is_role_based_email(email_lower)
    details['role_based'] = "Yes" if is_role_based else "No"
    
    # 4. Disposable & TLD check (fast, no I/O)
    is_disposable_domain = domain in DISPOSABLE_DOMAINS
    is_suspicious_tld = tld in SUSPICIOUS_TLDS
    details['tld_check'] = (
        "Warning: High-risk TLD"
        if is_suspicious_tld
        else "OK: Standard TLD"
    )

    details['disposable_list'] = (
        "Warning: Disposable email detected"
        if is_disposable_domain
        else "OK: Permanent email domain"
    )
    
    # Add paid domain info to details
    details['paid_domain'] = (
        "Yes: Paid email domain detected"
        if is_paid_domain
        else "No: Free or unknown domain"
    )
    
    # 4a. AI Analysis - Domain typo detection (fast, no I/O)
    typo_check = detect_domain_typo(domain)
    details['typo_check'] = typo_check
    
    # 4b. AI Analysis - Gibberish detection (fast, no I/O)
    gibberish_check = detect_gibberish(local_part)
    details['bot_check'] = gibberish_check
    
    # 4c. AI Analysis - Demographics inference (fast, no I/O)
    demographics = infer_demographics(local_part)
    details['demographics'] = demographics
    
    # 5. EARLY RETURN if disposable/suspicious (skip all expensive checks)
    if is_disposable_domain or is_suspicious_tld:
        return InboxStatusResponse(
            email=email,
            is_valid_syntax=True,
            is_disposable=True,
            has_mx_records=False,
            is_deliverable_smtp=False,
            is_catch_all_domain=False,
            is_role_based=is_role_based,
            is_paid_domain=is_paid_domain,
            confidence_score=0.0,
            details=details
        )
    
    # 6. For well-known or paid providers, skip expensive checks and return fast
    if is_well_known or is_paid_domain:
        provider_type = "Paid email provider" if is_paid_domain else "Well-known email provider"
        details['http_status'] = f"{provider_type} - skipped check"
        details['mx_records'] = f"{provider_type} - MX records assumed available"
        details['smtp'] = f"{provider_type} - SMTP assumed deliverable"
        details['catch_all'] = "Unknown (skipped for known provider)"
        
        # High confidence for well-known/paid providers
        # Paid domains get slightly higher confidence as they're more reliable
        score = 0.98 if is_paid_domain else 0.95  # Very high confidence
        score -= 0.05 if is_role_based else 0.0  # Slight reduction for role-based
        
        return InboxStatusResponse(
            email=email,
            is_valid_syntax=True,
            is_disposable=False,
            has_mx_records=True,  # Assumed true for well-known/paid providers
            is_deliverable_smtp=True,  # Assumed true for well-known/paid providers
            is_catch_all_domain=False,  # Unknown, but not critical
            is_role_based=is_role_based,
            is_paid_domain=is_paid_domain,
            confidence_score=round(max(0.0, min(score, 1.0)), 2),
            details=details
        )
    
    # 7. MX record check (async) - Check MX first (faster and more reliable than HTTP)
    loop = asyncio.get_event_loop()
    mx_records = await loop.run_in_executor(executor, get_mx_records, domain)
    has_mx = bool(mx_records)
    details['mx_records'] = f"Found {len(mx_records)} MX record(s)" if has_mx else "No MX records found"
    
    # 8. EARLY RETURN if no MX records (most reliable indicator)
    if not has_mx:
        # Skip HTTP check if no MX - saves time
        details['http_status'] = "Skipped (no MX records found)"
        return InboxStatusResponse(
            email=email,
            is_valid_syntax=True,
            is_disposable=False,
            has_mx_records=False,
            is_deliverable_smtp=False,
            is_catch_all_domain=False,
            is_role_based=is_role_based,
            is_paid_domain=is_paid_domain,
            confidence_score=0.1,
            details=details
        )
    
    # 9. HTTP status check (async) - Only if MX exists (faster path: skip if MX found)
    # Use shorter timeout for faster response
    http_ok = await check_http_status_async(domain, timeout=3)  # Reduced from 5 to 3 seconds
    if http_ok:
        details['http_status'] = "Website accessible (HTTPS/HTTP with valid response)"
    else:
        details['http_status'] = "Website unreachable or invalid (but MX exists)"
    
    # 10. Prepare MX host for SMTP
    mx_host = str(mx_records[0].exchange).rstrip('.')
    
    # 11. SMTP deliverability (async) - Only if not skipped (default: skipped for speed)
    deliverable = False
    if skip_smtp:
        details['smtp'] = "Skipped for faster response (use skip_smtp=false to enable)"
        # Assume deliverable if MX exists and SMTP is skipped
        deliverable = True  # Optimistic assumption when skipped
    else:
        code, msg = await check_smtp_connection_async(email, mx_host, timeout=5, max_retries=1)
        deliverable = (code == 250)
        details['smtp'] = f"Code {code}: {msg}"
    
    # 12. Catch-all detection (async) - Only if SMTP check passed and not skipped
    # Skip catch-all by default for speed (it's not critical)
    is_catch_all = False
    if deliverable and not skip_smtp:
        # Only check catch-all if explicitly requested (skip by default)
        fake_addr = f"{uuid.uuid4().hex[:16]}@{domain}"
        code2, _ = await check_smtp_connection_async(fake_addr, mx_host, timeout=5, max_retries=1)
        is_catch_all = (code2 == 250)
    else:
        details['catch_all'] = "Unknown (skipped for faster response)"
    
    if 'catch_all' not in details:
        details['catch_all'] = "Yes" if is_catch_all else "No"
    
    # 14. Enhanced confidence scoring
    score = 0.15  # syntax valid
    score += 0.15  # not disposable
    score += 0.20 if has_mx else 0.0
    score += 0.30 if deliverable else 0.0
    score += 0.10 if (deliverable and not is_catch_all) else 0.0
    score += 0.05 if not is_role_based else 0.0  # Personal emails slightly more trusted
    score -= 0.05 if is_role_based else 0.0  # Role-based emails slightly less trusted
    score += 0.05 if is_paid_domain else 0.0  # Paid domains get bonus confidence
    
    confidence = round(max(0.0, min(score, 1.0)), 2)
    
    return InboxStatusResponse(
        email=email,
        is_valid_syntax=True,
        is_disposable=False,
        has_mx_records=has_mx,
        is_deliverable_smtp=deliverable,
        is_catch_all_domain=is_catch_all,
        is_role_based=is_role_based,
        is_paid_domain=is_paid_domain,
        confidence_score=confidence,
        details=details
    )

# --- API Endpoints ---

@router.get(
    "/syntax",
    summary="Validate Email Syntax (Single)",
    response_model=SyntaxCheckResponse
)
async def validate_syntax_single(email: str = Query(..., description="Email to validate.")):
    """
    Checks if a single email address has a valid format using strict regex with comprehensive validation.
    """
    is_valid, error_msg = is_valid_syntax(email)
    return {
        "email": email,
        "is_valid_syntax": is_valid,
        "error_message": error_msg
    }

@router.post(
    "/syntax-bulk",
    summary="Validate Email Syntax (Bulk from File)",
    response_model=List[SyntaxCheckResponse]
)
async def validate_syntax_bulk(file: UploadFile = File(...)):
    """
    Checks a list of emails from a TXT, CSV, or XLSX file for valid syntax.
    Supports up to 10,000 emails per file.
    """
    content = await file.read()
    filename = file.filename.lower() if file.filename else ""
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported file type. Supported formats: .txt, .csv, .xlsx, .xls"
            )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Please ensure the file is UTF-8 encoded."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File processing error: {str(e)}"
        )
    
    # Limit file size
    if len(emails) > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File contains too many emails. Maximum 10,000 emails per file."
        )
    
    # Validate and return results
    results = []
    seen_emails = set()
    for e in emails:
        if not e or not e.strip():
            continue
        email = e.strip()
        # Deduplicate
        if email.lower() in seen_emails:
            continue
        seen_emails.add(email.lower())
        
        is_valid, error_msg = is_valid_syntax(email)
        results.append({
            "email": email,
            "is_valid_syntax": is_valid,
            "error_message": error_msg
        })
    
    return results


@router.post(
    "/syntax-bulk-json",
    summary="Validate Email Syntax (Bulk from JSON)",
    response_model=List[SyntaxCheckResponse]
)
async def validate_syntax_bulk_json(request: BulkValidationRequest = Body(...)):
    """
    Validate multiple email addresses from JSON body.
    Supports up to 1000 emails per request.
    """
    results = []
    seen_emails = set()
    
    for email in request.emails:
        if not email or not isinstance(email, str):
            continue
        
        email = email.strip()
        if not email:
            continue
        
        # Deduplicate
        if email.lower() in seen_emails:
            continue
        seen_emails.add(email.lower())
        
        is_valid, error_msg = is_valid_syntax(email)
        results.append({
            "email": email,
            "is_valid_syntax": is_valid,
            "error_message": error_msg
        })
    
    return results

@router.get(
    "/inbox-status",
    summary="Advanced Inbox Availability Check",
    response_model=InboxStatusResponse
)
async def get_inbox_status(
    email: str = Query(..., description="The email address to analyze."),
    skip_smtp: bool = Query(True, description="Skip SMTP checking for faster results (default: True). Set to False for full SMTP validation.")
):
    """
    Performs a comprehensive check: strict syntax, disposable/TLD, HTTP, MX, SMTP, catch-all, role-based detection, and confidence scoring.
    
    Features:
    - Strict syntax validation
    - Disposable email detection
    - Suspicious TLD detection
    - HTTP status check
    - MX record validation
    - SMTP deliverability test (optional)
    - Catch-all domain detection
    - Free/Paid email provider detection
    - Role-based email detection
    - Confidence scoring
    """
    return await validate_inbox_status_single(email, skip_smtp=skip_smtp)


@router.post(
    "/inbox-status-bulk",
    summary="Advanced Inbox Availability Check (Bulk)",
    response_model=BulkInboxStatusResponse
)
async def get_inbox_status_bulk(
    request: BulkValidationRequest = Body(...),
    skip_smtp: bool = Query(True, description="Skip SMTP checking for faster results (default: True). Set to False for full SMTP validation.")
):
    """
    Validate multiple email addresses with comprehensive inbox status checks.
    Supports up to 100 emails per request (due to SMTP checking time).
    
    For larger batches, use skip_smtp=True for faster processing.
    """
    if len(request.emails) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 emails per bulk request. Use skip_smtp=True for faster processing."
        )
    
    # Process emails concurrently (limited concurrency for SMTP)
    semaphore = asyncio.Semaphore(5 if not skip_smtp else 10)
    
    async def validate_with_semaphore(email: str):
        async with semaphore:
            return await validate_inbox_status_single(email, skip_smtp=skip_smtp)
    
    tasks = [validate_with_semaphore(email.strip()) for email in request.emails if email and email.strip()]
    results = await asyncio.gather(*tasks)
    
    valid_count = sum(1 for r in results if r.is_valid_syntax)
    invalid_count = len(results) - valid_count
    
    return BulkInboxStatusResponse(
        total=len(results),
        valid_count=valid_count,
        invalid_count=invalid_count,
        results=results
    )