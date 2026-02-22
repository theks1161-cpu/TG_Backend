import json , shutil , os , qrcode , uuid , tempfile
from fastapi import HTTPException
from app.utils.supabase_uploads import upload_to_supabase_qr
from fastapi import FastAPI ,  HTTPException , Response , status , Depends , APIRouter , Form , File , UploadFile
from app import models , schema  
from sqlalchemy.orm import Session
from app.database import engine , get_db
from app.config import settings 
from fastapi import BackgroundTasks
from fastapi import Query

router = APIRouter()

CATEGORY_TEMPLES = {
    "Char Dham": ["Kedarnath", "Badrinath", "Gangotri", "Yamunotri"],
    "Jyotirlinga": [
        "Somnath", "Mallikarjuna", "Mahakaleshwar",
        "Omkareshwar", "Bhimashankar",
        "Kashi Vishwanath", "Trimbakeshwar",
        "Vaidyanath", "Nageshwar"
    ],
    "Shaktipeeth": [
        "Vaishno Devi", "Kamakhya Devi",
        "Kalighat", "Jwala Ji",
        "Chintpurni", "Hinglaj Mata",
        "Maa Tara Tarini", "Maa Sharda"
    ],
    "3D Abhishek": [
        "Mahakal 3D Abhishek",
        "Kashi Vishwanath 3D",
        "Somnath 3D",
        "Omkareshwar 3D"
    ]
}

def generate_payment_qr(amount: int) -> str:
    upi_id = "6260499299@okbizaxis"
    payee_name = "Tirth Ghumo"
    

    upi_url = (
        f"upi://pay?"
        f"pa={upi_id}"
        f"&pn={payee_name}"
        f"&am={amount}"
        f"&cu=INR"
        
    )

    qr = qrcode.make(upi_url)

    filename = f"vr_darshan_qr_{uuid.uuid4()}.png"

    # ✅ cross-platform temp directory
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)

    qr.save(file_path)

    return file_path


@router.get("/vr-darshan/price")
async def generate_vr_darshan_qr(
    devotees: str = Query(...)
):
    devotees_data = json.loads(devotees)
    total_amount = 0

    for devotee in devotees_data:

        age = int(devotee.get("age", 0))
        is_disabled = devotee.get("is_disabled", False)

        # 🔥 FREE CONDITION
        if is_disabled or age >= 60:
            continue
        temples_by_category = devotee.get("temples")

        if not temples_by_category:
            raise HTTPException(400, "Temple selection required")

        for category, temple_list in temples_by_category.items():

            if category not in CATEGORY_TEMPLES:
                raise HTTPException(400, f"Invalid category {category}")

            if "All Temples" in temple_list:
                temple_list = CATEGORY_TEMPLES[category]

            # Validate temple belongs to category
            for temple in temple_list:
                if temple not in CATEGORY_TEMPLES[category]:
                    raise HTTPException(
                        400,
                        f"{temple} not valid for {category}"
                    )

            count = len(temple_list)

            # Apply bundle logic
            if category == "Char Dham":
                total_amount += 151 if count == 4 else count * 51

            elif category == "Jyotirlinga":
                if count == 9:
                    total_amount += 451
                elif count == 6:
                    total_amount += 251
                else:
                    total_amount += count * 51

            elif category == "Shaktipeeth":
                total_amount += 401 if count == 8 else count * 51

            elif category == "3D Abhishek":
                total_amount += 351 if count == 4 else count * 51

    if total_amount > 0:
        qr_path = generate_payment_qr(total_amount)
        qr_url = upload_to_supabase_qr(qr_path, "vr_darshan_qr")
    else:
        qr_url = None
    return {
        "amount": total_amount,
        "payment_qr_url": qr_url
    }


@router.get("/manali/price")
async def calculate_manali_price(
    sleeper: int , 
    ac : int
):

    PRICE_PER_SLEPPER = 5000
    PRICE_PER_AC = 6000
    amount = (sleeper * PRICE_PER_SLEPPER) + (ac * PRICE_PER_AC)
    qr_path = generate_payment_qr(amount)
    qr_url = upload_to_supabase_qr(qr_path, "manali_qr")
    session_id = str(uuid.uuid4())

    return {
        "payment_qr_url": qr_url,
        "amount":amount , 
    }





