import json , shutil , os , qrcode , uuid , tempfile , base64
from io import BytesIO
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

CATALOGUE = {
  "Char Dham": {
    "perTemple": 51,
    "packages": [
      {
        "label": "Char Dham Package",
        "value": "PKG_CHARDHAM_ALL",
        "price": 151,
        
      },
    ],
    "temples": [
      "Kedarnath — Rudraprayag, Uttarakhand",
      "Badrinath — Chamoli, Uttarakhand",
      "Yamunotri — Uttarakhand",
      "Gangotri — Uttarkashi, Uttarakhand",
    ],
  },
  "Jyotirlinga & Shiv Darshan": {
    "perTemple": 51,
    "packages": [
      {
        "label": "6 Jyotirlinga Package",
        "value": "PKG_JYO_6",
        "price": 251,
        "temples": [
          "Kedarnath — Rudraprayag, Uttarakhand",
          "Baba Baidyanath Jyotirlinga — Deoghar, Jharkhand",
          "Shri Bhimashankar Jyotirlinga — Pune, Maharashtra",
          "Shri Trimbakeshwar Jyotirlinga — Nashik, Maharashtra",
          "Shri Nageshwar Jyotirlinga — Dwarka, Gujarat",
          "Shri Omkareshwar Jyotirlinga — Khandwa, Madhya Pradesh",
        ],
      },
      {
        "label": "All 10 Jyotirlinga Package",
        "value": "PKG_JYO_ALL",
        "price": 451,
        
      },
    ],
    "temples": [
      "Kedarnath — Rudraprayag, Uttarakhand",
      "Baba Baidyanath Jyotirlinga — Deoghar, Jharkhand",
      "Shri Bhimashankar Jyotirlinga — Pune, Maharashtra",
      "Shri Trimbakeshwar Jyotirlinga — Nashik, Maharashtra",
      "Shri Nageshwar Jyotirlinga — Dwarka, Gujarat",
      "Shri Omkareshwar Jyotirlinga — Khandwa, Madhya Pradesh",
      "Shri Mangalnath Mandir — Ujjain, Madhya Pradesh",
      "Shri Pashupatinath — Mandsaur, Madhya Pradesh",
      "Bhojeshwar Mahadev — Bhojpur, Madhya Pradesh",
      "Shri Kaal Bhairav — Ujjain, Madhya Pradesh",
    ],
  },
  "3D Abhishek": {
    "perTemple": 51,
    "packages": [
      {
        "label": "3D Abhishek Package",
        "value": "PKG_3DABHISHEK_ALL",
        "price": 351,
        
      },
    ],
    "temples": [
      "Shri Kashi Vishwanath Jyotirlinga — Varanasi, UP",
      "Shri Baidyanath Jyotirlinga — Deoghar, Jharkhand",
      "Shri Grishneshwar Jyotirlinga — Aurangabad, Maharashtra",
      "Shri Bhimashankar Jyotirlinga — Pune, Maharashtra",
      "Shri Nageshwar Jyotirlinga — Dwarka, Gujarat",
      "Shri Kedarnath Jyotirlinga — Rudraprayag, Uttarakhand",
      "Shri Somnath Jyotirlinga — Gir Somnath, Gujarat",
      "Shri Omkareshwar Jyotirlinga — Khandwa, Madhya Pradesh",
    ],
  },
  "Shri Vishnu Darshan": {
    "perTemple": 51,
    "packages": [
      {
        "label": "Vishnu Darshan Package",
        "value": "PKG_VISHNU_ALL",
        "price": 301,
        
      },
    ],
    "temples": [
      "Shri Banke Bihari — Vrindavan, UP",
      "Badrinath — Chamoli, Uttarakhand",
      "Shri Ram Lala Surya Tilak — Ayodhya, UP",
      "Shri Jagannath Rath Yatra — Puri, Odisha",
      "Radha Raman Ji — Vrindavan, UP",
      "Shri Gopal Mandir — Ujjain, Madhya Pradesh",
      "Shri Jagannath Darshan — Koraput, Odisha",
    ],
  },
  "Shaktipeeth & Devi Darshan": {
    "perTemple": 51,
    "packages": [
      {
        "label": "Shaktipeeth Package",
        "value": "PKG_SHAKTI_ALL",
        "price": 401,
        
      },
    ],
    "temples": [
      "Maa Sharda Shaktipeeth — Maihar, Madhya Pradesh",
      "Maa Harsiddhi Devi Shaktipeeth — Ujjain, Madhya Pradesh",
      "Maa Bhadrakali Shaktipeeth — Kurukshetra, Haryana",
      "Maa Chamunda Devi Shaktipeeth — Dewas, Madhya Pradesh",
      "Shri Ambabai Mahalakshmi Mandir — Kolhapur, Maharashtra",
      "Maa Baglamukhi Mandir — Nalkheda, Madhya Pradesh",
      "Shri Mahalakshmi Jagdamba Mandir — Koradi, Nagpur, Maharashtra",
      "Maa Gadkalika Devi — Ujjain, Madhya Pradesh",
      "Maa Annapurna Mandir — Indore, Madhya Pradesh",
    ],
  },
  "Ayodhya Nagar Darshan": {
    "perTemple": 51,
    "packages": [
      {
        "label": "Ayodhya Package",
        "value": "PKG_AYODHYA_ALL",
        "price": 151,
        
      },
    ],
    "temples": [
      "Shri Ram Mandir — Ayodhya, UP",
      "Hanuman Garhi — Ayodhya, UP",
      "Saryu Aarti — Saryu Ghat, Ayodhya, UP",
      "Ayodhya Deepotsav — Ayodhya, UP",
    ],
  },
  "Shri Hanuman Darshan": {
    "perTemple": 51,
    "packages": [
      {
        "label": "Hanuman Darshan Package",
        "value": "PKG_HANUMAN_ALL",
        "price": 151,
        
      },
    ],
    "temples": [
      "Bade Hanuman Ji — Prayagraj, UP",
      "Shri Chhind Dham — Chhind, Madhya Pradesh",
      "Hanuman Garhi — Ayodhya, UP",
      "Shri Bageshwar Dham — Chhatarpur, Madhya Pradesh",
    ],
  },
  "Divya Aarti Darshan": {
    "perTemple": 51,
    "packages": [
      {
        "label": "Divya Aarti Package",
        "value": "PKG_AARTI_ALL",
        "price": 351,
        
      },
    ],
    "temples": [
      "Saryu Aarti — Ayodhya, UP",
      "Ganga Aarti — Varanasi, UP",
      "Hanuman Ji Ki Aarti — Hanuman Mandir",
      "Hanuman Garhi Aarti — Ayodhya, UP",
      "Harsiddhi Devi Aarti — Ujjain, Madhya Pradesh",
      "Omkareshwar Shayan Aarti — Omkareshwar, Madhya Pradesh",
      "Bhimashankar Marathi Aarti — Bhimashankar, Maharashtra",
      "Maa Sharda Devi Aarti — Maihar, Madhya Pradesh",
    ],
  },
  "Ujjain Nagar Darshan": {
    "perTemple": 51,
    "packages": [
      {
        "label": "Ujjain Package",
        "value": "PKG_UJJAIN_ALL",
        "price": 401,
        
      },
    ],
    "temples": [
      "Shri Kaal Bhairav Mandir — Ujjain, Madhya Pradesh",
      "Shri Mangalnath Mandir — Ujjain, Madhya Pradesh",
      "Maa Harsiddhi Devi Mandir — Ujjain, Madhya Pradesh",
      "Shri Chintaman Ganesh Mandir — Ujjain, Madhya Pradesh",
      "Ram Ghat (Shipra Ryourupiiver) — Ujjain, Madhya Pradesh",
      "Shri Sandipani Ashram — Ujjain, Madhya Pradesh",
      "Maa Gadkalika Devi Mandir — Ujjain, Madhya Pradesh",
      "Shri Bhartrihari Gufa — Ujjain, Madhya Pradesh",
      "Shri Gopal Mandir — Ujjain, Madhya Pradesh",
    ],
  },
  "Additional Darshan": {
    "perTemple": 101,
    "packages": [],
    "temples": ["Chitrakoot Darshan", "Maa Narmada Parikrama"],
  },
}
def create_qr_base64(amount: float) -> str:

    upi_id = "6260499299@okbizaxis"
    name = "Tirth Ghumo"

    upi_string = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"

    img = qrcode.make(upi_string)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    qr_base64 = base64.b64encode(buffer.read()).decode()

    return qr_base64

# def generate_payment_qr(amount: int) -> str:
#     upi_id = "6260499299@okbizaxis"
#     payee_name = "Tirth Ghumo"
    

#     upi_url = (
#         f"upi://pay?"
#         f"pa={upi_id}"
#         f"&pn={payee_name}"
#         f"&am={amount}"
#         f"&cu=INR"
        
#     )

#     qr = qrcode.make(upi_url)

#     filename = f"vr_darshan_qr_{uuid.uuid4()}.png"

#     # ✅ cross-platform temp directory
#     temp_dir = tempfile.gettempdir()
#     file_path = os.path.join(temp_dir, filename)

#     qr.save(file_path)

#     return file_path



@router.get("/vr-darshan/price")
async def generate_vr_darshan_qr(
# devotees: str = Query(...),
price:int
):
    # devotees_data = json.loads(devotees)
    # total_amount = 0

    # for devotee in devotees_data:

    #     age = int(devotee.get("age", 0))
    #     is_disabled = devotee.get("disability", False)

    #     # 🔥 FREE condition
    #     if age >= 60 or is_disabled:
    #         continue

    #     temples_by_category = devotee.get("temples")

    #     if not temples_by_category:
    #         raise HTTPException(400, "Temple selection required")

    #     for category, temple_list in temples_by_category.items():

    #         if category not in CATALOGUE:
    #             raise HTTPException(400, f"Invalid category: {category}")

    #         category_data = CATALOGUE[category]
    #         all_temples = category_data["temples"]
    #         packages = category_data["packages"]
    #         per_temple_price = category_data["perTemple"]

    #         # Handle "All Temples"
    #         if "All Temples" in temple_list:
    #             temple_list = all_temples

    #         # Validate temples
    #         for temple in temple_list:
    #             if temple not in all_temples:
    #                 raise HTTPException(
    #                     400,
    #                     f"{temple} not valid for {category}"
    #                 )

    #         count = len(temple_list)
    #         applied_package = False

    #         # 🔥 Check all packages
    #         for pkg in packages:

    #             pkg_temples = pkg.get("temples")

    #             # Case 1: Full category package (no temples defined)
    #             if pkg_temples is None:
    #                 if count == len(all_temples):
    #                     total_amount += pkg["price"]
    #                     applied_package = True
    #                     break

    #             # Case 2: Specific bundle package
    #             else:
    #                 if set(temple_list) == set(pkg_temples):
    #                     total_amount += pkg["price"]
    #                     applied_package = True
    #                     break

    #         # If no package matched → apply perTemple
    #         if not applied_package:
    #             total_amount += count * per_temple_price

    # Generate QR only if payment required
    # if total_amount > 0:
    if price > 0:
        qr_url = create_qr_base64(price)
    else:
        qr_url = None

    return {
        "amount": price,
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
    
    qr_url = create_qr_base64(amount)
    session_id = str(uuid.uuid4())

    return {
        "payment_qr_url": qr_url,
        "amount":amount , 
    }

@router.get("/odt/qr")
async def generate_odt_qr(
  is_coupon_applied:bool,
  meal_preference:str
):
    with_meal_amount = 1201
    without_meal_amount = 1030

    if meal_preference == "with_meal":
        amount = with_meal_amount
    else:
        amount = without_meal_amount

    if is_coupon_applied:
        amount = amount-201

    qr_url = create_qr_base64(amount)

    return {
        "payment_qr_url": qr_url,
        "amount": amount
    } 





