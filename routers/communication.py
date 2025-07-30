# routers/communication.py

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
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

# --- SMTP Configuration ---
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# --- API Endpoints ---

@router.post("/send-email", summary="Send Single or Multiple Emails")
async def send_emails(payload: EmailRequest = Body(...)):
    """Receives and sends a batch of emails via a configured SMTP server."""
    if not all([SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD]):
        raise HTTPException(status_code=503, detail="SMTP service is not configured.")

    sent_count = 0
    failed_emails = []
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        for email_item in payload.emails:
            try:
                msg = MIMEMultipart('alternative')
                msg['From'] = f"{payload.from_name} <{payload.from_email}>" if payload.from_name else payload.from_email
                msg['To'] = email_item.to_email
                msg['Subject'] = email_item.subject
                msg.attach(MIMEText(email_item.text_body or "Enable HTML to view this email.", 'plain'))
                msg.attach(MIMEText(email_item.html_body, 'html'))
                server.sendmail(payload.from_email, email_item.to_email, msg.as_string())
                sent_count += 1
            except Exception as e:
                failed_emails.append({"email": email_item.to_email, "error": str(e)})
        server.quit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMTP error: {str(e)}")

    return {
        "message": "Email sending process completed.",
        "sent_count": sent_count,
        "failed_count": len(failed_emails),
        "failed_details": failed_emails
    }
