# routers/communication.py

import smtplib
import asyncio
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor
import os

# --- Router Setup ---
router = APIRouter(
    prefix="/communication",
    tags=["Communication"]
)

# --- Pydantic Models ---
class EmailSchema(BaseModel):
    to_email: EmailStr
    subject: str = Field(..., max_length=200)
    html_body: str
    text_body: Optional[str] = None

class EmailRequest(BaseModel):
    from_email: EmailStr
    from_name: Optional[str] = None
    emails: List[EmailSchema]
    batch_size: Optional[int] = Field(default=50, ge=1, le=1000, description="Number of emails per batch")
    delay_between_batches: Optional[float] = Field(default=1.0, ge=0, le=60, description="Delay in seconds between batches")
    max_retries: Optional[int] = Field(default=3, ge=0, le=10, description="Maximum retry attempts for failed emails")
    concurrent_connections: Optional[int] = Field(default=5, ge=1, le=20, description="Number of concurrent SMTP connections")

# --- SMTP Configuration ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# --- Global Thread Pool for SMTP operations ---
executor = ThreadPoolExecutor(max_workers=20)

# --- Helper Functions ---
def create_smtp_connection():
    """Create and authenticate an SMTP connection."""
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
    server.starttls()
    server.login(SMTP_USERNAME, SMTP_PASSWORD)
    return server

def send_single_email(
    server: smtplib.SMTP,
    from_email: str,
    from_name: Optional[str],
    email_item: EmailSchema
) -> Dict:
    """Send a single email."""
    from_header = f"{from_name} <{from_email}>" if from_name else from_email
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = from_header
        msg['To'] = email_item.to_email
        msg['Subject'] = email_item.subject
        msg.attach(MIMEText(email_item.text_body or "Enable HTML to view this email.", 'plain'))
        msg.attach(MIMEText(email_item.html_body, 'html'))
        
        server.sendmail(from_email, email_item.to_email, msg.as_string())
        return {"status": "success", "email": email_item.to_email}
    except Exception as e:
        return {"status": "failed", "email": email_item.to_email, "error": str(e)}

def send_email_batch(
    emails: List[EmailSchema],
    from_email: str,
    from_name: Optional[str],
    max_retries: int,
    connection_id: int
) -> Dict:
    """Send a batch of emails using a single SMTP connection with retry logic."""
    sent_count = 0
    failed_emails = []
    server = None
    
    try:
        server = create_smtp_connection()
        
        for email_item in emails:
            success = False
            last_error = None
            
            # Retry logic for each email
            for attempt in range(max_retries + 1):
                try:
                    result = send_single_email(server, from_email, from_name, email_item)
                    
                    if result["status"] == "success":
                        sent_count += 1
                        success = True
                        break
                    else:
                        last_error = result.get("error", "Unknown error")
                        
                        # If connection lost, try to reconnect
                        if "disconnected" in last_error.lower() or "connection" in last_error.lower():
                            if attempt < max_retries:
                                try:
                                    server.quit()
                                except:
                                    pass
                                server = create_smtp_connection()
                                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                                continue
                        
                        # For other errors, retry with backoff
                        if attempt < max_retries:
                            time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                            continue
                        
                except smtplib.SMTPServerDisconnected:
                    # Reconnect and retry
                    if attempt < max_retries:
                        try:
                            server.quit()
                        except:
                            pass
                        server = create_smtp_connection()
                        time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                        continue
                    last_error = "SMTP connection lost after retries"
                    break
                except Exception as e:
                    last_error = str(e)
                    if attempt < max_retries:
                        time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                        continue
                    break
            
            if not success:
                failed_emails.append({
                    "email": email_item.to_email,
                    "error": last_error or "Max retries exceeded"
                })
        
        if server:
            try:
                server.quit()
            except:
                pass
    except Exception as e:
        # If batch fails completely, mark all as failed
        for email_item in emails:
            failed_emails.append({
                "email": email_item.to_email,
                "error": f"Batch processing error: {str(e)}"
            })
        if server:
            try:
                server.quit()
            except:
                pass
    
    return {
        "sent_count": sent_count,
        "failed_emails": failed_emails
    }

async def process_campaign_async(
    emails: List[EmailSchema],
    from_email: str,
    from_name: Optional[str],
    batch_size: int,
    delay_between_batches: float,
    max_retries: int,
    concurrent_connections: int
) -> Dict:
    """Process email campaign asynchronously with batching and connection pooling."""
    total_emails = len(emails)
    sent_count = 0
    failed_emails = []
    
    # Split emails into batches
    batches = [emails[i:i + batch_size] for i in range(0, total_emails, batch_size)]
    total_batches = len(batches)
    
    # Process batches with controlled concurrency
    semaphore = asyncio.Semaphore(concurrent_connections)
    
    async def process_batch_with_semaphore(batch_idx: int, batch: List[EmailSchema]):
        async with semaphore:
            # Add delay before starting batch (except first batch) to spread out load
            if batch_idx > 0 and delay_between_batches > 0:
                await asyncio.sleep(delay_between_batches * (batch_idx / concurrent_connections))
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor,
                send_email_batch,
                batch,
                from_email,
                from_name,
                max_retries,
                batch_idx
            )
            return result
    
    # Process all batches concurrently (limited by semaphore)
    tasks = [
        process_batch_with_semaphore(idx, batch)
        for idx, batch in enumerate(batches)
    ]
    
    # Wait for all batches to complete
    results = await asyncio.gather(*tasks)
    
    # Aggregate results
    for result in results:
        sent_count += result["sent_count"]
        failed_emails.extend(result["failed_emails"])
    
    return {
        "total_emails": total_emails,
        "sent_count": sent_count,
        "failed_count": len(failed_emails),
        "failed_details": failed_emails,
        "batches_processed": total_batches
    }

# --- API Endpoints ---

@router.post("/send-email", summary="Send Email Campaign (Unlimited)")
async def send_emails(payload: EmailRequest = Body(...)):
    """
    Send email campaigns with unlimited recipients.
    
    Features:
    - Batch processing with configurable batch sizes
    - Connection pooling for better performance
    - Automatic retry logic for failed emails
    - Rate limiting to avoid overwhelming SMTP server
    - Concurrent processing for faster delivery
    
    Parameters:
    - batch_size: Number of emails per batch (default: 50, max: 1000)
    - delay_between_batches: Delay in seconds between batches (default: 1.0)
    - max_retries: Maximum retry attempts for failed emails (default: 3)
    - concurrent_connections: Number of concurrent SMTP connections (default: 5, max: 20)
    """
    if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD]):
        raise HTTPException(status_code=503, detail="SMTP service is not configured.")
    
    if not payload.emails:
        raise HTTPException(status_code=400, detail="No emails provided in the request.")
    
    # Process the campaign
    try:
        result = await process_campaign_async(
            emails=payload.emails,
            from_email=payload.from_email,
            from_name=payload.from_name,
            batch_size=payload.batch_size or 50,
            delay_between_batches=payload.delay_between_batches or 1.0,
            max_retries=payload.max_retries or 3,
            concurrent_connections=payload.concurrent_connections or 5
        )
        
        return {
            "message": "Email campaign processing completed.",
            "total_emails": result["total_emails"],
            "sent_count": result["sent_count"],
            "failed_count": result["failed_count"],
            "success_rate": f"{(result['sent_count'] / result['total_emails'] * 100):.2f}%" if result["total_emails"] > 0 else "0%",
            "batches_processed": result["batches_processed"],
            "failed_details": result["failed_details"][:100] if len(result["failed_details"]) > 100 else result["failed_details"]  # Limit failed details to first 100
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Campaign processing error: {str(e)}"
        )
