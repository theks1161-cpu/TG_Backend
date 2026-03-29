from fastapi import FastAPI ,  HTTPException , Response , status , Depends , APIRouter , Form , File , UploadFile , Request
from app import models , schema  
from sqlalchemy.orm import Session 
from sqlalchemy.exc import IntegrityError
from app.database import engine , get_db
from app.config import settings  
from app.utils.mail.vr_admin_mail import send_admin_vr_darshan_email
import shutil, os , json
from fastapi import BackgroundTasks
from app.utils.invoice_generator import generate_invoice
from datetime import date
from app.utils.supabase_uploads import upload_to_supabase
from app.models import InstantVRDarshan , ShivratriVRDarshan
from app.schema import InstantVRDarshanRequest
from app.utils.hash.vr_aadhar_image import generate_image_hash


router = APIRouter()
WEEKDAY_SLOTS = [
    "7:00-8:00 PM",
    "9:00-10:00 PM"
]

WEEKEND_SLOTS = [
    "11:00-12:00 PM",
    "1:00-2:00 PM",
    "3:00-4:00 PM",
    "5:00-6:00 PM",
    "7:00-8:00 PM",
    "9:00-10:00 PM"
]




CATEGORY_TEMPLES = {
    "Char Dham": [
      "Kedarnath — Rudraprayag, Uttarakhand",
      "Badrinath — Chamoli, Uttarakhand",
      "Yamunotri — Uttarakhand",
      "Gangotri — Uttarkashi, Uttarakhand",
    ],
    "Jyotirlinga & Shiv Darshan": [
        "Kedarnath — Rudraprayag, Uttarakhand",
      "Baba Baidyanath Jyotirlinga — Deoghar, Jharkhand",
      "Shri Bhimashankar Jyotirlinga — Pune, Maharashtra",
      "Shri Trimbakeshwar Jyotirlinga — Nashik, Maharashtra",
      "Shri Nageshwar Jyotirlinga — Dwarka, Gujarat",
      "Shri Omkareshwar Jyotirlinga — Khandwa, Madhya Pradesh",
      "Shri Mangalnath Mandir — Ujjain, Madhya Pradesh",
      "Shri Pashupatinath — Mandsaur, Madhya Pradesh",
      "Bhojeshwar Mahadev — Bhojpur, Madhya Pradesh",
      "Shri Kaal Bhairav — Ujjain, Madhya Pradesh"
    ],
    "Shaktipeeth & Devi Darshan": [
        "Maa Sharda Shaktipeeth — Maihar, Madhya Pradesh",
      "Maa Harsiddhi Devi Shaktipeeth — Ujjain, Madhya Pradesh",
      "Maa Bhadrakali Shaktipeeth — Kurukshetra, Haryana",
      "Maa Chamunda Devi Shaktipeeth — Dewas, Madhya Pradesh",
      "Shri Ambabai Mahalakshmi Mandir — Kolhapur, Maharashtra",
      "Maa Baglamukhi Mandir — Nalkheda, Madhya Pradesh",
      "Shri Mahalakshmi Jagdamba Mandir — Koradi, Nagpur, Maharashtra",
      "Maa Gadkalika Devi — Ujjain, Madhya Pradesh",
      "Maa Annapurna Mandir — Indore, Madhya Pradesh"
    ],
    "3D Abhishek": [
        "Shri Kashi Vishwanath Jyotirlinga — Varanasi, UP",
      "Shri Baidyanath Jyotirlinga — Deoghar, Jharkhand",
      "Shri Grishneshwar Jyotirlinga — Aurangabad, Maharashtra",
      "Shri Bhimashankar Jyotirlinga — Pune, Maharashtra",
      "Shri Nageshwar Jyotirlinga — Dwarka, Gujarat",
      "Shri Kedarnath Jyotirlinga — Rudraprayag, Uttarakhand",
      "Shri Somnath Jyotirlinga — Gir Somnath, Gujarat",
      "Shri Omkareshwar Jyotirlinga — Khandwa, Madhya Pradesh"
    ],
    "Shri Vishnu Darshan":[
        "Shri Banke Bihari — Vrindavan, UP",
      "Badrinath — Chamoli, Uttarakhand",
      "Shri Ram Lala Surya Tilak — Ayodhya, UP",
      "Shri Jagannath Rath Yatra — Puri, Odisha",
      "Radha Raman Ji — Vrindavan, UP",
      "Shri Gopal Mandir — Ujjain, Madhya Pradesh",
      "Shri Jagannath Darshan — Koraput, Odisha"
    ],
    "Ayodhya Nagar Darshan":[
        "Shri Ram Mandir — Ayodhya, UP",
      "Hanuman Garhi — Ayodhya, UP",
      "Saryu Aarti — Saryu Ghat, Ayodhya, UP",
      "Ayodhya Deepotsav — Ayodhya, UP"
    ],
    "Shri Hanuman Darshan":[
        "Bade Hanuman Ji — Prayagraj, UP",
      "Shri Chhind Dham — Chhind, Madhya Pradesh",
      "Hanuman Garhi — Ayodhya, UP",
      "Shri Bageshwar Dham — Chhatarpur, Madhya Pradesh"
    ],
    "Divya Aarti Darshan":[
        "Saryu Aarti — Ayodhya, UP",
      "Ganga Aarti — Varanasi, UP",
      "Hanuman Ji Ki Aarti — Hanuman Mandir",
      "Hanuman Garhi Aarti — Ayodhya, UP",
      "Harsiddhi Devi Aarti — Ujjain, Madhya Pradesh",
      "Omkareshwar Shayan Aarti — Omkareshwar, Madhya Pradesh",
      "Bhimashankar Marathi Aarti — Bhimashankar, Maharashtra",
      "Maa Sharda Devi Aarti — Maihar, Madhya Pradesh"
    ],
    "Ujjain Nagar Darshan":[
        "Shri Kaal Bhairav Mandir — Ujjain, Madhya Pradesh",
      "Shri Mangalnath Mandir — Ujjain, Madhya Pradesh",
      "Maa Harsiddhi Devi Mandir — Ujjain, Madhya Pradesh",
      "Shri Chintaman Ganesh Mandir — Ujjain, Madhya Pradesh",
      "Ram Ghat (Shipra River) — Ujjain, Madhya Pradesh",
      "Shri Sandipani Ashram — Ujjain, Madhya Pradesh",
      "Maa Gadkalika Devi Mandir — Ujjain, Madhya Pradesh",
      "Shri Bhartrihari Gufa — Ujjain, Madhya Pradesh",
      "Shri Gopal Mandir — Ujjain, Madhya Pradesh"
    ],
    "Additional Darshan":[
        "Chitrakoot Darshan", "Maa Narmada Parikrama"
    ]

}

@router.post(
    "/vr-darshan/booking",
    status_code=status.HTTP_201_CREATED
)
async def create_vr_darshan_booking(
    background_tasks: BackgroundTasks,

    # -------- Common Booking Fields --------
    contact_number: str = Form(...),
    whatsapp_number: str = Form(...),
    email_address: str = Form(...),
    address: str = Form(...),
    preferred_date: date = Form(...),
    time_slot: str = Form(...),
    special_request: str | None = Form(None),

    # -------- Devotee Data --------
    devotees: str = Form(...),  # JSON string
    aadhar_images: list[UploadFile] = File(...),

    # -------- Payment --------
    payment_screenshot: UploadFile | None = File(None),

    db: Session = Depends(get_db)
):
    try:
        devotees_data = json.loads(devotees)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid devotees JSON format."
        )

    if not isinstance(devotees_data, list) or not devotees_data:
        raise HTTPException(
            status_code=400,
            detail="At least one devotee is required."
        )

    if len(devotees_data) != len(aadhar_images):
        raise HTTPException(
            status_code=400,
            detail="Devotees count and Aadhaar images count must match."
        )

    # -------- Upload Payment Screenshot --------
    payment_screenshot_url = None
    if payment_screenshot:
        try:
            payment_screenshot_url = upload_to_supabase(
                payment_screenshot,
                folder="vr_darshan_payments"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Payment upload failed: {str(e)}"
            )

    # -------- Create Booking --------
    booking = models.VRDarshanBooking(
        contact_number=contact_number,
        whatsapp_number=whatsapp_number,
        email_address=email_address,
        address=address,
        preferred_date=preferred_date,
        time_slot=time_slot,
        special_request=special_request,
        payment_screenshot=payment_screenshot_url,
        booking_status="Confirmed"
    )

    db.add(booking)
    db.flush()

    # -------- Create Devotees --------
    for index, devotee in enumerate(devotees_data):

        required_fields = [
            "full_name",
            "age",
            "gender",
            "temples"
            
        ]
    

        if not all(field in devotee for field in required_fields):
            raise HTTPException(
                status_code=400,
                detail=f"Missing fields in devotee at index {index}"
            )

        temples_by_category = devotee["temples"]

        if not isinstance(temples_by_category, dict):
            raise HTTPException(400, "temples must be an object")

        # Validate categories and temples
        if not temples_by_category:
            raise HTTPException(400, "At least one temple must be selected")

        for category, temple_list in temples_by_category.items():

            if category not in CATEGORY_TEMPLES:
                raise HTTPException(400, f"Invalid category: {category}")

            if "All Temples" in temple_list:
                temple_list = CATEGORY_TEMPLES[category]
                temples_by_category[category] = temple_list

            for temple in temple_list:
                if temple not in CATEGORY_TEMPLES[category]:
                    raise HTTPException(
                        400,
                        f"{temple} not valid under {category}"
                    )

        image_hash, _ = await generate_image_hash(aadhar_images[index])
        age = int(devotee["age"])
        is_disabled = devotee.get("is_disabled", False)


        if age >= 60 or is_disabled:
            try:
                claim = models.VRBenefitClaim(
                    benefit_code="FREE_VR_60_PLUS",
                    aadhar_image_hash=image_hash
                )
                db.add(claim)
                db.flush()  # triggers UNIQUE constraint

            except IntegrityError:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail="This Aadhaar has already claimed free VR Darshan."
                )
        aadhar_images[index].file.seek(0)

        try:
            aadhar_url = upload_to_supabase(
                aadhar_images[index],
                folder="vr_darshan_aadhar"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Aadhaar upload failed: {str(e)}"
            )

        db.add(
            models.VRDarshanDevotee(
                booking_id=booking.id,
                full_name=devotee["full_name"],
                age=devotee["age"],
                gender=devotee["gender"],
                is_disabled=is_disabled,
                temples=temples_by_category,
                aadhar_image_url=aadhar_url,
                aadhar_image_hash=image_hash
            )
        )

    db.commit()

    
    background_tasks.add_task(send_admin_vr_darshan_email, booking)

    return {
        "message": "VR Darshan booking created successfully",
        "booking_id": booking.id
    }

@router.get("/vr-darshan/slots")
def get_slots(selected_date: date, db: Session = Depends(get_db)):

    # Determine weekday or weekend
    if selected_date.weekday() >= 5:
        # 5 = Saturday, 6 = Sunday
        all_slots = WEEKEND_SLOTS
    else:
        all_slots = WEEKDAY_SLOTS

    # Get booked slots for that date
    booked_slots = db.query(models.VRDarshanBooking.time_slot).filter(
        models.VRDarshanBooking.preferred_date == selected_date
    ).all()

    # Extract string from tuple
    booked_slots = [slot[0] for slot in booked_slots]

    return [
        {
            "time_slot": slot,
            "is_available": slot not in booked_slots
        }
        for slot in all_slots
    ]


@router.post("/instant-vr-darshan")
async def add_multiple(devotees: str = Form(...),          
    paymentMode: str = Form(...),
    aadhar_images: list[UploadFile] = File(...),
     db: Session = Depends(get_db)):
    
    devotees_list = json.loads(devotees)
    if len(devotees_list) != len(aadhar_images):
        raise HTTPException(
            status_code=400,
            detail="Devotees count and Aadhar images count must match."
        )
    rows = []

   

    for index , d in enumerate(devotees_list):
        #hash first
        image_hash,_ = await generate_image_hash(aadhar_images[index])

        if d["age"] >= 60:
            try:
                claim = models.VRBenefitClaim(
                    benefit_code="FREE_VR_60_PLUS",
                    aadhar_image_hash=image_hash
                )
                db.add(claim)
                db.flush()  # triggers UNIQUE constraint

            except IntegrityError:
                db.rollback()
                raise HTTPException(
                    status_code=400,
                    detail="This Aadhaar has already claimed free VR Darshan."
                )
        
        aadhar_images[index].file.seek(0)

        aadhar_url = upload_to_supabase(
            aadhar_images[index],
            folder="instant_vr_aadhar"
        )

        
        row = InstantVRDarshan(
            full_name=d["name"],              # frontend → DB
            age=d["age"],
            gender=d["gender"],
            darshanCategory=d["category"],    # IMPORTANT
            darshan=d["darshan"],
            contact_number="NA",              # frontend doesn’t send it
            payment_option=paymentMode.upper(),
            aadhar_image_url=aadhar_url,
            aadhar_image_hash=image_hash
        )
        db.add(row)
            

        
    db.commit()

    return {
        "inserted": len(devotees_list)
    }

@router.post("/shivratri-vr-darshan")
async def add_multiple(
    request: Request,
    devotees: str = Form(...),
    db: Session = Depends(get_db)
):
    # Validate JSON
    try:
        devotees_list = json.loads(devotees)
        if not isinstance(devotees_list, list):
            raise ValueError
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid devotees data")

    form = await request.form()

    try:
        for index, d in enumerate(devotees_list):

            aadhar_url = None
            file_key = f"aadhar_{index}"

            # Explicit file mapping per devotee
            if file_key in form:
                file = form[file_key]
                if file and hasattr(file, "filename") and file.filename:
                    aadhar_url = upload_to_supabase(
                        file,
                        folder="shivratri_vr_darshan"
                    )

            row = ShivratriVRDarshan(
                full_name=d.get("full_name") or None,
                age=int(d["age"]) if d.get("age") not in [None, ""] else None,
                gender=d.get("gender") or None,
                darshanCategory=d.get("darshanCategory") or None,
                darshan=d.get("darshan") or None,
                contact_number=d.get("contact_number") or None,
                aadhar_image_url=aadhar_url
            )

            db.add(row)

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"inserted": len(devotees_list)}