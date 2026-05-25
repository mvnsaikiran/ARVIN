"""
Inject MediBuddy-specific super-chunks into the vectorstore.
These consolidate facts from slide-deck screenshots that PDF text extraction misses.
All text is sourced from the actual policy PDF.
"""

import os, json, hashlib
import chromadb
from chromadb.utils import embedding_functions

VECTORSTORE_DIR = "vectorstore"
CHUNKS_FILE     = os.path.join(VECTORSTORE_DIR, "chunks.json")
POLICY_NAME     = "MediBuddy Health & Wellness (User Manual)"

EMBED_FN = embedding_functions.ONNXMiniLM_L6_V2()

SUPER_CHUNKS = [
    # 1 — Overview & Services
    {
        "text": (
            "MediBuddy Gold is an Online Consultation Program provided to Arvind employees as a "
            "corporate benefit. The program is accessible through the MediBuddy app under "
            "Arvind Limited Benefits — Corporate Sponsored Account. "
            "MediBuddy Gold provides four main services: Doctor Consultations (online), "
            "Lab Tests (with home sample collection), Buy Medicines (with pharmacy discounts), "
            "and Surgery Care. All services are available through the MediBuddy mobile application."
        ),
        "page": 1,
    },
    # 2 — Coverage & Family
    {
        "text": (
            "MediBuddy Gold coverage: Employee + 5 family members. "
            "The 5 members include Spouse, 2 Children, and Parents. "
            "Coverage is available for Self, Spouse, Children, and Parents. "
            "MediBuddy Gold is available for Employee + 5 members. "
            "FAQ: What is the procedure to avail consultation for family members? "
            "Steps: Add health problem that the family member is facing. "
            "Select relationship under the heads mentioned in the application. "
            "Fill in details of the patient including their mobile number — doctor's call "
            "will be directed to that user directly. "
            "In case of video chat, it is mandatory for the family member to download the application. "
            "Family members can be added as beneficiaries and get discounts on lab tests and pharmacy — "
            "those benefits are to be booked through the employee's application. "
            "If the employee and a family member are located differently, the employee still has to "
            "book the benefits and choose the family member's location."
        ),
        "page": 24,
    },
    # 3 — Specialties
    {
        "text": (
            "MediBuddy Gold provides online consultations across 22 specialities (also referred to "
            "as 22 specialties or 25+ specialities in the app). "
            "Available medical specialties include: General Physician, Cold/Cough/Fever, "
            "Orthopedics, Cardiology, Diabetes, Cancer, Skin (Dermatology), ENT "
            "(Ear Nose Throat), Neurology, Pregnancy/Gynaecology, and more. "
            "Consultations are provided by qualified specialist MD Doctors. "
            "FAQ: What are the benefits of the services provided? "
            "Unlimited Online Doctor consultations from the comfort of your home across "
            "22 specialties from specialist MD Doctors. 24x7 consultation from anywhere in India. "
            "Available for Employee + 5 members. "
            "FAQ: What services are available? "
            "Instant Video/Audio/Chat consultation with a qualified specialist doctor across "
            "22 specialities from anywhere in India. "
            "Ongoing discount applicable on pharmacy. "
            "Lab Tests and Home sample collection with ongoing discount applicable on each booking."
        ),
        "page": 7,
    },
    # 4 — Availability & SLA
    {
        "text": (
            "MediBuddy Gold online consultations are available 24x7 (24 hours a day, 7 days a week) "
            "from anywhere in India. "
            "SLA (Service Level Agreement): Doctor callback within 30 mins. "
            "85% of consultations are responded to within 15 mins. "
            "After consultation is confirmed, the doctor will start consultation in the next 30 mins. "
            "The response time shown in the app is 30 mins. "
            "Consultation is 100% Private with a Digital Prescription provided."
        ),
        "page": 3,
    },
    # 5 — Login & App
    {
        "text": (
            "How to download and log in to MediBuddy: "
            "Step 1: Download MediBuddy app from Play Store (Android) or App Store (iOS). "
            "Step 2: Select 'I have a Corporate Account'. "
            "Step 3: Enter your corporate email address (@arvind.in) to receive OTP. "
            "Step 4: Verify OTP to complete registration. "
            "Login uses corporate email — employees use their @arvind.in email address. "
            "CLARA is an AI tool on MediBuddy that collects symptoms from the patient "
            "before connecting to a doctor. CLARA is the AI-powered symptom collection tool."
        ),
        "page": 4,
    },
    # 6 — Languages
    {
        "text": (
            "MediBuddy supports 16 Indian languages for online consultations. "
            "The 16 Indian languages are: Hindi, English, Telegu, Kannada, Malayalam, "
            "Marathi, Gujarati, Tamil, Bengali, Punjabi, Odia, Konkani, Assamese. "
            "FAQ 7: What are the 16 Indian languages in which consultation is happening? "
            "Hindi, English, Telegu, Kannada, Malayalam, Marathi, Gujarati, Tamil, "
            "Bengali, Punjabi, Odia, Konkani, Assamese."
        ),
        "page": 26,
    },
    # 7 — Consultations & Doctor Choice
    {
        "text": (
            "FAQ 5: Do we have a cap on number of consultations in a given frame of time? "
            "No, there is no cap on the number of consultations per employee. "
            "All employees and their family members can avail unlimited consultation. "
            "FAQ 6: Can I choose the doctor as per my wish? "
            "When a user avails consultation there is an auto-assigned doctor for the first consultation. "
            "If the user wants to choose a different doctor, there is an option called "
            "'change doctor' available for the same consultation. "
            "In case of follow up consultation employee can choose either the doctor they had "
            "already consulted or there is option to choose others from the list. "
            "Doctor's Profile will be visible — click on Start Consultation to interact with Doctor. "
            "Click on 'Connect with Doctor now' for confirmation. "
            "As a Gold member, you get the consultation worth Rs.199 for free."
        ),
        "page": 25,
    },
    # 8 — Lab Tests
    {
        "text": (
            "Lab Tests on MediBuddy: Select 'Lab Test' from the home screen. "
            "The app will detect location automatically or it can be selected manually. "
            "Search for Lab test by name or browse categories: "
            "Book Lab Tests, Popular Health Checks, X-Rays, Scans & MRI, Previous Orders. "
            "Available test packages include: COVID-19 Tests (Influenza Virus RTPCR, Covid RT PCR SWAB), "
            "Women's Primary Prevention Health Checkup, MediBuddy Basic Health Checkup, "
            "Women's Staying Strong Health Checkup, Comprehensive full body checkup, "
            "MediBuddy Swift Health Checkup, MediBuddy Full Body Health Check (82+ lab tests, "
            "MRP Rs.1899/- discounted to Rs.999/-), MediBuddy Advance Health Checkup. "
            "Home Sample Collection: A trained Phlebotomist will arrive at the address provided "
            "to collect the sample. Enter address for sample collection (Home, Work, or Other). "
            "Select Date and Time slot for Home Sample Collection (morning slots 06:00-12:00, "
            "afternoon slots 12:00-18:00). Once payment is successful appointment details "
            "will be shared on mail and text message. "
            "Family members can also book lab tests — add another patient during checkout."
        ),
        "page": 14,
    },
    # 9 — Medicines / Pharmacy
    {
        "text": (
            "Buy Medicines on MediBuddy: Select 'Buy Medicine' from the home screen. "
            "Set your delivery location by entering Pincode and click Search. "
            "Get up to 40% off on all health and wellness needs. "
            "Delivery takes 7 to 10 days. "
            "Search for Medicine in the search bar and add it to the cart. "
            "Click 'Proceed' to add items to cart. "
            "For prescription medicines: Select 'Upload Prescription'. "
            "Upload prescription from Camera, Gallery, or PDF file. "
            "Accepted file formats: .jpg, .png, or .pdf files. Size limit is 15 MB. "
            "Delivery options: Home Delivery (24 to 48 hours, up to 15% off) or "
            "Store Pickup (5 hours, up to 15% off). "
            "Select Address and click 'Proceed' to order medicine. "
            "Select 'Confirm Order' to proceed to payment gateway page. "
            "Once payment is successful, order details will be shared on mail and text."
        ),
        "page": 19,
    },
    # 10 — Payment
    {
        "text": (
            "Payment methods on MediBuddy (powered by Razorpay — Razorpay Trusted Business): "
            "Preferred Payment Methods: UPI — PayTM, UPI — Google Pay. "
            "Cards: VISA, MasterCard, RuPay and more. "
            "UPI: Pay with installed app or use others (Google Pay, PhonePe, PayTM, Others). "
            "Netbanking: All Indian banks. "
            "Wallet: PhonePe & more. "
            "After payment is successful, appointment details or order details will be "
            "shared on mail and text message. "
            "Lab test payment example: MRP Total Rs.1799/-, Payable Amount Rs.1799/-. "
            "Medicine payment shows: Total MRP, Delivery Charges (FREE), Meds Discount, "
            "Payable Amount (Online Payment)."
        ),
        "page": 18,
    },
    # 11 — Customer Care & Contact
    {
        "text": (
            "MediBuddy Customer Care: "
            "FAQ 8: What happens when I do not get a response from a Doctor? "
            "You can contact our 24x7 voice and non-voice support — 9999991555 for MediBuddy Gold. "
            "FAQ 9: What are the customer care numbers? "
            "MediBuddy has 24x7 voice and non-voice support. "
            "The user can call 9999991555 or they can write to hello@medibuddy.in. "
            "MediBuddy support is available 24x7 (24 hours a day, 7 days a week). "
            "For additional FAQs: https://faq.medibuddy.in"
        ),
        "page": 26,
    },
]


def _make_id(policy_name: str, page: int, idx: int) -> str:
    raw = f"{policy_name}::superchunk_mb::{page}::{idx}"
    return "chunk_" + hashlib.md5(raw.encode()).hexdigest()[:12]


def main():
    print("Loading chunks.json ...")
    with open(CHUNKS_FILE) as f:
        chunks = json.load(f)
    print(f"  Existing chunks: {len(chunks)}")

    client = chromadb.PersistentClient(path=VECTORSTORE_DIR)
    col    = client.get_collection("arvind_policies", embedding_function=EMBED_FN)
    print(f"  ChromaDB docs: {col.count()}")

    new_docs = []
    new_meta = []
    new_ids  = []
    new_chunks_json = []

    existing_ids = set(col.get(include=[])["ids"])

    for i, sc in enumerate(SUPER_CHUNKS):
        idx = len(chunks) + len(new_chunks_json)
        cid = _make_id(POLICY_NAME, sc["page"], i)
        chunk_id = f"chunk_{idx}"
        if chunk_id in existing_ids:
            print(f"  Skipped (already exists): {chunk_id}")
            continue
        new_docs.append(sc["text"])
        new_meta.append({"policy_name": POLICY_NAME, "page": sc["page"], "chunk_id": chunk_id})
        new_ids.append(chunk_id)
        new_chunks_json.append({
            "id": chunk_id,
            "policy_name": POLICY_NAME,
            "page": sc["page"],
            "text": sc["text"],
            "filename": "medibuddy_user_manual.pdf",
            "chunk_type": "prose",
        })
        print(f"  Queued: [{chunk_id}] {POLICY_NAME} — {len(sc['text'])} chars")

    if not new_docs:
        print("Nothing to add.")
        return

    print(f"\nAdding {len(new_docs)} MediBuddy super-chunks to ChromaDB ...")
    col.add(documents=new_docs, metadatas=new_meta, ids=new_ids)
    print(f"  ChromaDB docs after: {col.count()}")

    chunks.extend(new_chunks_json)
    with open(CHUNKS_FILE, "w") as f:
        json.dump(chunks, f, indent=2)
    print(f"  chunks.json updated: {len(chunks)} total chunks")
    print("\nDone.")


if __name__ == "__main__":
    main()
