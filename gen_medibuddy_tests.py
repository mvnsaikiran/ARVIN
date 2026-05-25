"""
Generate test cases for the 18th policy: MediBuddy Health & Wellness (User Manual)
"""
import json, random

QUERIES_MEDIBUDDY = [
    # ── Overview ──────────────────────────────────────────────────────────
    ("What is MediBuddy Gold?", ["online consultation", "medibuddy gold", "MediBuddy Gold"], "Overview"),
    ("What does MediBuddy provide to Arvind employees?", ["online consultation", "lab test", "medicine"], "Overview"),
    ("What is the MediBuddy benefit at Arvind?", ["medibuddy gold", "MediBuddy Gold", "online consultation"], "Overview"),
    ("What services does MediBuddy offer?", ["doctor consultation", "lab test", "medicine", "surgery"], "Services"),
    ("What are the four main services of MediBuddy?", ["doctor", "lab", "medicine", "surgery"], "Services"),
    ("Is MediBuddy a corporate benefit at Arvind?", ["corporate sponsored", "arvind", "MediBuddy"], "Overview"),
    ("What is the MediBuddy app used for?", ["consultation", "lab", "medicine"], "Overview"),

    # ── Family Coverage ────────────────────────────────────────────────────
    ("Who is covered under MediBuddy?", ["employee", "spouse", "children", "parents"], "Coverage"),
    ("How many family members can use MediBuddy?", ["5", "five"], "Coverage"),
    ("Can my parents use MediBuddy?", ["parents", "family"], "Coverage"),
    ("Can my spouse use MediBuddy?", ["spouse", "family"], "Coverage"),
    ("Can I add my children to MediBuddy?", ["children", "family"], "Coverage"),
    ("What is the family coverage in MediBuddy?", ["employee + 5", "employee+5", "5 members", "five members"], "Coverage"),
    ("How many dependents can I add on MediBuddy?", ["5", "five", "family"], "Coverage"),

    # ── Specialties ────────────────────────────────────────────────────────
    ("How many specialties are available on MediBuddy?", ["22", "specialit"], "Specialties"),
    ("What medical specialties are available on MediBuddy?", ["general physician", "cardiology", "diabetes", "skin", "ent"], "Specialties"),
    ("Can I consult a cardiologist on MediBuddy?", ["cardiology", "cardiolog", "specialist"], "Specialties"),
    ("Is diabetes care available on MediBuddy?", ["diabetes", "specialit"], "Specialties"),
    ("Can I get a dermatologist on MediBuddy?", ["skin", "dermatolog", "specialit"], "Specialties"),
    ("What types of doctors are on MediBuddy?", ["general physician", "specialist", "md doctor"], "Specialties"),

    # ── Availability / SLA ────────────────────────────────────────────────
    ("Is MediBuddy available 24/7?", ["24x7", "24*7", "24 x 7", "anytime"], "Availability"),
    ("Can I consult a doctor at night on MediBuddy?", ["24x7", "24*7", "anytime", "anywhere"], "Availability"),
    ("What is the SLA for doctor response on MediBuddy?", ["30 mins", "30 minutes", "sla"], "SLA"),
    ("How quickly will a doctor respond on MediBuddy?", ["30 mins", "30 minutes", "15 mins"], "SLA"),
    ("What percentage of consultations are answered within 15 minutes?", ["85", "15 mins"], "SLA"),

    # ── Languages ─────────────────────────────────────────────────────────
    ("How many languages does MediBuddy support?", ["16", "sixteen"], "Languages"),
    ("In which languages can I consult on MediBuddy?", ["hindi", "english", "telegu", "kannada", "marathi"], "Languages"),
    ("Is Tamil available on MediBuddy?", ["tamil", "16", "language"], "Languages"),
    ("Can I consult in Gujarati on MediBuddy?", ["gujarati", "language"], "Languages"),
    ("What are the 16 languages on MediBuddy?", ["hindi", "english", "telegu", "kannada", "malayalam", "marathi", "gujarati", "tamil"], "Languages"),
    ("Is consultation available in Bengali on MediBuddy?", ["bengali", "language"], "Languages"),
    ("What Indian languages are supported on MediBuddy?", ["hindi", "telegu", "kannada", "malayalam", "konkani", "assamese"], "Languages"),

    # ── Login / App ───────────────────────────────────────────────────────
    ("How do I log in to MediBuddy?", ["corporate", "email", "otp", "arvind.in"], "Login"),
    ("How do I register on MediBuddy?", ["corporate account", "corporate email", "otp"], "Login"),
    ("What email do I use to login to MediBuddy?", ["arvind.in", "corporate email"], "Login"),
    ("How do I download the MediBuddy app?", ["download", "app", "play store", "app store"], "App"),
    ("What is CLARA on MediBuddy?", ["clara", "symptom", "ai"], "App"),
    ("What does CLARA do on MediBuddy?", ["symptom", "ai", "clara"], "App"),
    ("What is the first step to use MediBuddy?", ["download", "corporate account", "login"], "Login"),
    ("What account type should I select on MediBuddy?", ["corporate account", "corporate", "i have corporate"], "Login"),

    # ── Consultations / Doctor ────────────────────────────────────────────
    ("Is there a limit on consultations on MediBuddy?", ["no cap", "unlimited", "no limit"], "Consultations"),
    ("How many consultations can I take on MediBuddy?", ["unlimited", "no cap", "no limit"], "Consultations"),
    ("Can I choose my doctor on MediBuddy?", ["change doctor", "auto assigned", "auto-assigned"], "Doctor-Choice"),
    ("How is a doctor assigned on MediBuddy?", ["auto assigned", "auto-assigned", "first consultation"], "Doctor-Choice"),
    ("What if I don't like the assigned doctor on MediBuddy?", ["change doctor", "different doctor"], "Doctor-Choice"),
    ("Can I request a different doctor on MediBuddy?", ["change doctor", "different doctor"], "Doctor-Choice"),
    ("How do I start a consultation on MediBuddy?", ["start consultation", "connect with doctor"], "Consultations"),
    ("Can I do a follow-up consultation on MediBuddy?", ["follow up", "follow-up", "previous doctor"], "Consultations"),

    # ── Lab Tests ─────────────────────────────────────────────────────────
    ("How do I book a lab test on MediBuddy?", ["lab test", "select lab", "search"], "Lab-Tests"),
    ("Does MediBuddy offer home sample collection?", ["home sample collection", "phlebotomist", "home"], "Lab-Tests"),
    ("Who collects the sample at home for lab tests?", ["phlebotomist", "home sample"], "Lab-Tests"),
    ("How do I select the date for home sample collection?", ["date", "slot", "morning", "afternoon"], "Lab-Tests"),
    ("What health check packages are available on MediBuddy?", ["health check", "full body", "health package"], "Lab-Tests"),
    ("Is full body checkup available on MediBuddy?", ["full body", "full body checkup", "health check"], "Lab-Tests"),
    ("Can I add family members for lab tests?", ["family", "add another patient", "add family"], "Lab-Tests"),
    ("Is X-Ray booking available on MediBuddy?", ["x-ray", "xray", "scan", "mri"], "Lab-Tests"),

    # ── Medicines ─────────────────────────────────────────────────────────
    ("How do I order medicines on MediBuddy?", ["buy medicine", "search medicine", "pharmacy"], "Medicines"),
    ("Is there a discount on medicines through MediBuddy?", ["discount", "40%", "pharmacy discount"], "Medicines"),
    ("How long does medicine delivery take on MediBuddy?", ["24", "48", "hours", "delivery"], "Medicines"),
    ("Can I do store pickup for medicines on MediBuddy?", ["store pickup", "5 hours"], "Medicines"),
    ("What is the store pickup time for medicines on MediBuddy?", ["5 hours", "store pickup"], "Medicines"),
    ("What documents do I need to order prescription medicines?", ["prescription", "upload prescription", "rx"], "Medicines"),
    ("What file formats are accepted for prescription upload?", ["jpg", "png", "pdf"], "Medicines"),
    ("What is the maximum file size for prescription upload on MediBuddy?", ["15 mb", "15mb", "size limit"], "Medicines"),
    ("How are medicine order details shared?", ["mail", "text", "email", "sms"], "Medicines"),

    # ── Family Booking ────────────────────────────────────────────────────
    ("Can family members get discounts on lab tests through MediBuddy?", ["employee", "application", "book"], "Family-Booking"),
    ("How should I book MediBuddy services for my family?", ["employee", "application", "book", "employee's application"], "Family-Booking"),
    ("If my family member lives elsewhere, how do I book for them?", ["location", "employee", "choose", "family member's location"], "Family-Booking"),

    # ── Payments ──────────────────────────────────────────────────────────
    ("What payment methods are available on MediBuddy?", ["upi", "card", "netbanking", "wallet", "razorpay"], "Payment"),
    ("Can I pay via UPI on MediBuddy?", ["upi", "google pay", "phonepe", "paytm"], "Payment"),
    ("What happens after successful payment for lab tests?", ["mail", "text", "appointment"], "Payment"),
    ("Can I pay via netbanking on MediBuddy?", ["netbanking", "indian banks"], "Payment"),

    # ── Tracking / Profile ────────────────────────────────────────────────
    ("How do I track my orders on MediBuddy?", ["profile", "track", "orders"], "Tracking"),
    ("Where can I find my past consultations on MediBuddy?", ["past video consultation", "profile", "track"], "Tracking"),

    # ── Customer Care ─────────────────────────────────────────────────────
    ("What is MediBuddy customer care number?", ["9999991555"], "Customer-Care"),
    ("How do I contact MediBuddy support?", ["9999991555", "hello@medibuddy.in"], "Customer-Care"),
    ("What if the doctor doesn't respond on MediBuddy?", ["9999991555", "24x7", "support"], "Customer-Care"),
    ("Is MediBuddy support 24x7?", ["24x7", "9999991555", "support"], "Customer-Care"),
    ("What is the MediBuddy email for support?", ["hello@medibuddy.in"], "Customer-Care"),

    # ── FAQ / Edge Cases ──────────────────────────────────────────────────
    ("Can I consult from any part of India on MediBuddy?", ["anywhere in india", "india", "anywhere"], "FAQ"),
    ("What modes of consultation are available on MediBuddy?", ["video", "audio", "chat"], "FAQ"),
    ("What type of doctor handles consultations on MediBuddy?", ["md doctor", "specialist", "qualified"], "FAQ"),
    ("Is online pharmacy discount available on MediBuddy?", ["pharmacy", "discount", "ongoing discount"], "FAQ"),
    ("What is the MediBuddy Full Body Health Checkup?", ["82", "lab test", "full body"], "Lab-Tests"),
]

# ── Expand with paraphrase variants ──────────────────────────────────────────
# Each triple gets a few surface rewrites to increase volume
_PARAPHRASES = {
    "Is MediBuddy available 24/7?": [
        "Can I use MediBuddy at any time?",
        "Is MediBuddy accessible 24 hours a day?",
    ],
    "How many specialties are available on MediBuddy?": [
        "What is the number of specialities on MediBuddy?",
        "How many types of doctors are on MediBuddy?",
    ],
    "Is there a limit on consultations on MediBuddy?": [
        "How many times can I consult on MediBuddy in a month?",
        "Is there a cap on consultations per employee on MediBuddy?",
        "Can I take unlimited consultations on MediBuddy?",
    ],
    "What is the MediBuddy customer care number?": [
        "MediBuddy helpline number",
        "MediBuddy support contact",
    ],
    "Does MediBuddy offer home sample collection?": [
        "Can lab samples be collected at home through MediBuddy?",
        "Does a phlebotomist come home for MediBuddy lab tests?",
    ],
    "How long does medicine delivery take on MediBuddy?": [
        "What is the delivery time for medicines on MediBuddy?",
        "When will my MediBuddy medicine order arrive?",
    ],
}

def build_suite():
    cases = []
    added = set()
    for q, kf, cat in QUERIES_MEDIBUDDY:
        cases.append({"query": q, "key_facts": kf, "category": cat,
                      "policy": "MediBuddy Health & Wellness (User Manual)"})
        added.add(q)
        for paraphrase in _PARAPHRASES.get(q, []):
            if paraphrase not in added:
                cases.append({"query": paraphrase, "key_facts": kf, "category": cat,
                              "policy": "MediBuddy Health & Wellness (User Manual)"})
                added.add(paraphrase)
    return cases

if __name__ == "__main__":
    suite = build_suite()
    with open("medibuddy_test_suite.json", "w") as f:
        json.dump(suite, f, indent=2)
    print(f"Generated {len(suite)} test cases → medibuddy_test_suite.json")
