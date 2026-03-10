from fastapi import FastAPI , HTTPException , Response , status , Depends , APIRouter , Form , File , UploadFile
from app import models , schema
from sqlalchemy.orm import Session
from app.database import engine , get_db
from app.config import settings
from fastapi import BackgroundTasks
from datetime import date
import requests
import resend 

router = APIRouter()

@router.post("/bhajan-jamming")
async def create_bhajan_jamming_form(
    background_tasks: BackgroundTasks,

    full_name: str = Form(...),
    email_address: str = Form(...),
    contact_number: str = Form(...),
    db: Session = Depends(get_db)
):
    bhajan_jamming_entry = models.BhajanJamming(
        full_name=full_name,
        email_address=email_address,
        contact_number=contact_number
    )

    db.add(bhajan_jamming_entry)
    db.commit()
    db.refresh(bhajan_jamming_entry)
    if(email_address):
        background_tasks.add_task(send_bhajan_jamming_email, bhajan_jamming_entry)

    return {"status": "Bhajan Jamming form submitted successfully"}

async def send_bhajan_jamming_email(data):
    email_body = f"""
    Hello {data.full_name},
    
    You’re warmly invited to join an Open Bhajan Jamming Session by TirthGhumo — a simple evening to sit together, sing bhajans, and experience a peaceful devotional vibe.

    Event Details
    📅 Date: 29th March 2026
    ⏰ Time: [Event Time]
    📍 Venue: [Cafe Name & Location]
    🎟 Entry: Free & Open for All

    Feel free to come with friends and be part of this beautiful evening.

    Warm regards,
    Team TirthGhumo
    """
    email = {
        "from": "Tirth Ghumo <no-reply@tirthghumo.in>",
        "to": [data.email_address],
        "subject": "Open Bhajan Jamming Session Invitation 🎶",
        "text": email_body.strip()
    }
    try:
        resend.Emails.send(email)
    except Exception as e:
        raise Exception(f"Bhajan Jamming email sending failed: {str(e)}")