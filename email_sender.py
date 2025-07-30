# routers/email_sender.py

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import os

# Create an APIRouter instance. This is like a "mini" FastAPI app.
router = APIRouter(
    prefix="",  # All routes in this file will be prefixed with /email
    tags=["Email Sending"] # Group these routes under "Email Sending" in the docs
)

# --- Pydantic Models (copied from main.py) ---
class EmailSchema(BaseModel):
    to_email: EmailStr
    subject: str = Field(..., max_length=200)
    html_body: str
    text_body: Optional[str] = None

class EmailRequest(BaseModel):
    from_email: EmailStr
    from_name: Optional[str] = None
    emails: List[EmailSchema]

# --- SMTP Configuration (copied from main.py) ---
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# --- API Endpoint ---
# Note that the decorator is now @router.post and the path is simplified
@router.post("/send-emails", summary="Send Single or Multiple Emails")
async def send_emails(payload: EmailRequest = Body(...)):
    """
    Receives a list of email objects and sends them via SMTP.
    """
    if not all([SMTP_USERNAME, SMTP_PASSWORD]):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMTP server credentials are not configured on the server."
        )

    sent_count = 0
    failed_emails = []

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)

        for email_item in payload.emails:
            try:
                msg = MIMEMultipart('alternative')
                from_header = f"{payload.from_name} <{payload.from_email}>" if payload.from_name else payload.from_email
                msg['From'] = from_header
                msg['To'] = email_item.to_email
                msg['Subject'] = email_item.subject

                text_part = MIMEText(email_item.text_body or "HTML email requires a compatible client.", 'plain')
                html_part = MIMEText(email_item.html_body, 'html')
                msg.attach(text_part)
                msg.attach(html_part)

                server.sendmail(payload.from_email, email_item.to_email, msg.as_string())
                sent_count += 1
            except Exception as e:
                failed_emails.append({"email": email_item.to_email, "error": str(e)})
        
        server.quit()

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SMTP authentication failed. Check credentials."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SMTP connection error: {str(e)}"
        )

    return {
        "message": "Email sending process completed.",
        "sent_count": sent_count,
        "failed_count": len(failed_emails),
        "failed_details": failed_emails
    }