"""Generate sample clinic PDFs under data/knowledge/."""

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "knowledge"

DOCS = {
    "specialties.pdf": {
        "title": "SmartHealth Specialty Guide",
        "sections": [
            (
                "How to use this guide",
                "This guide helps patients choose a specialist for common symptoms. "
                "It is educational clinic information, not a diagnosis. If you have "
                "chest pain, trouble breathing, severe bleeding, or sudden weakness, "
                "seek emergency care instead of booking a routine visit.",
            ),
            (
                "Family medicine and general clinic",
                "See family medicine for check-ups, mild fever, cough, cold, vaccinations, "
                "blood pressure follow-up, and routine lab orders. If you are not sure "
                "which specialist you need, start here. The clinician can refer you.",
            ),
            (
                "Cardiology",
                "See cardiology for chest discomfort that is not an emergency, palpitations, "
                "known heart disease, high blood pressure that is hard to control, swelling "
                "in the legs, or follow-up after a heart procedure. Bring a list of heart "
                "medications and any recent ECG or echo reports.",
            ),
            (
                "Dermatology",
                "See dermatology for rashes that last more than a week, acne that did not "
                "improve with pharmacy creams, moles that change shape or color, hair loss, "
                "or persistent itching. Take a photo of the rash if it comes and goes.",
            ),
            (
                "Orthopedics",
                "See orthopedics for joint pain, sports injuries, back or neck pain after "
                "an injury, suspected sprain, or follow-up after a fracture. For sudden "
                "inability to move a limb or loss of feeling, go to emergency care.",
            ),
            (
                "Gastroenterology",
                "See gastroenterology for ongoing stomach pain, heartburn, difficulty "
                "swallowing, unexplained weight loss, blood in stool, or follow-up for "
                "ulcer, IBS, or liver conditions. You may need fasting if a procedure "
                "is planned. Read the lab and procedure prep guide.",
            ),
            (
                "Endocrinology",
                "See endocrinology for diabetes, thyroid problems, hormone-related fatigue, "
                "or abnormal lab results for glucose, HbA1c, or thyroid hormones. Bring "
                "your latest lab printout and a glucose log if you have one.",
            ),
            (
                "Pediatrics",
                "Book pediatrics for patients under 18: well-child visits, vaccines, ear "
                "infections, growth concerns, and school physicals. A parent or guardian "
                "should attend. Use the same SmartHealth booking flow as adult visits.",
            ),
            (
                "Obstetrics and gynecology",
                "See OB/GYN for pregnancy care, annual exams, menstrual problems, or "
                "contraception counseling. First prenatal visits should be booked as soon "
                "as pregnancy is known. Mention if you need a longer slot when you book.",
            ),
            (
                "Mental health",
                "See behavioral health or psychiatry for anxiety, depression, trouble "
                "sleeping that lasts weeks, or medication review. This is not a crisis "
                "line. If you are in immediate danger, contact local emergency services.",
            ),
        ],
    },
    "lab-prep.pdf": {
        "title": "Test and Procedure Preparation",
        "sections": [
            (
                "General rules",
                "Arrive 15 minutes early. Bring a photo ID and your SmartHealth appointment "
                "details. Wear loose clothing. Tell the front desk about allergies, "
                "pregnancy, kidney disease, and all medicines including supplements. "
                "If you feel faint after a blood draw, sit until staff say you may leave.",
            ),
            (
                "Fasting blood tests",
                "Many cholesterol, glucose, and metabolic panels need 8 to 12 hours of "
                "fasting. Water is usually allowed. Do not eat food, drink juice, or chew "
                "gum. Ask your provider before skipping prescribed medicine. If you have "
                "diabetes, confirm fasting instructions the day before.",
            ),
            (
                "Complete blood count and routine labs",
                "CBC, thyroid tests, and many infection tests do not require fasting. "
                "You may eat a normal meal unless your order says otherwise. Drink water "
                "so veins are easier to find.",
            ),
            (
                "Urine tests",
                "For a standard urine sample, wash hands, use the mid-stream catch, and "
                "return the cup to the lab window. For a 24-hour urine collection, start "
                "after the first morning void, keep the jug cold, and return it the next "
                "morning. Do not skip bottles.",
            ),
            (
                "Imaging: X-ray",
                "Remove jewelry and metal from the area being imaged. Tell staff if you "
                "could be pregnant. No fasting is needed for a plain X-ray.",
            ),
            (
                "Imaging: ultrasound",
                "Abdominal ultrasound often needs 6 hours of fasting. Pelvic ultrasound "
                "may require a full bladder: drink water as instructed and do not empty "
                "your bladder until the scan is done.",
            ),
            (
                "Imaging: CT and MRI",
                "CT with contrast may need kidney labs first and a period without food. "
                "Tell staff about iodine or contrast allergy, metformin, and asthma. "
                "MRI: no metal implants unless cleared, no magnetic cards in the pocket, "
                "and tell staff about claustrophobia. Some MRI scans need contrast.",
            ),
            (
                "What to bring and what not to do",
                "Bring previous reports on paper or a USB if you have them. Do not apply "
                "lotion or deodorant before some heart tests. Do not book a fasting test "
                "late in the day if you cannot skip breakfast. If you miss prep, call the "
                "clinic before traveling in; the slot may need reschedule.",
            ),
        ],
    },
    "booking-faq.pdf": {
        "title": "SmartHealth Booking FAQ",
        "sections": [
            (
                "Who can book",
                "Patients register with name, email, and password. Public registration "
                "creates a patient account only. Providers are created by front desk "
                "staff. You must log in to book. The appointment time must be in the "
                "future. You choose a provider; you do not send someone else's patient id.",
            ),
            (
                "What happens when I book",
                "The slot is reserved for that provider at that date and time. The visit "
                "starts as pending. A short hold timer starts. A provider or front desk "
                "should confirm the visit. If nobody confirms before the hold expires, "
                "the booking is canceled automatically and the slot is released.",
            ),
            (
                "What does confirmed mean",
                "Confirmed means a clinician or front desk accepted the visit and the "
                "hold timer stopped. The slot stays blocked so nobody else can take it. "
                "You will see status confirmed, not pending. You can still complete, "
                "cancel, or reschedule after confirm.",
            ),
            (
                "Complete and cancel",
                "Complete means the visit happened. Cancel means the visit will not "
                "happen. Only the assigned provider or front desk can confirm, complete, "
                "or cancel through the booking workflow. Patients cannot complete their "
                "own appointment. Canceled and completed slots can be booked by someone "
                "else at that same time.",
            ),
            (
                "Reschedule",
                "Patients, the assigned provider, or front desk can reschedule a pending "
                "or confirmed visit to a new future time. The new slot must be free for "
                "that provider. You cannot reschedule a completed or canceled visit. "
                "If the new time is taken you will see a conflict and must pick another time.",
            ),
            (
                "Notifications",
                "You receive in-app notifications when a visit is booked, confirmed, "
                "rescheduled, canceled, or completed. Check Notifications after you book. "
                "These are product notifications, not SMS or email in this version.",
            ),
            (
                "Why was my booking refused",
                "Past times are rejected. If that provider already has an active visit "
                "at that minute, the slot is taken. If scheduling is temporarily down, "
                "the booking is not kept. Try again or pick another time. Inactive "
                "accounts cannot log in.",
            ),
            (
                "Privacy",
                "Do not share your password. Front desk can list patients and analytics. "
                "Patients only see their own appointments and notifications. This FAQ "
                "does not contain other patients' names or medical records.",
            ),
        ],
    },
    "appointment-steps.pdf": {
        "title": "Your Appointment Journey",
        "sections": [
            (
                "Step 1. Create your account",
                "Open SmartHealth Register. Enter your name, email, and a password of "
                "8 to 72 characters. The clinic creates a patient profile for you. "
                "Then log in. Providers and front desk accounts are not self-serve.",
            ),
            (
                "Step 2. Choose a provider and time",
                "Open the provider list and pick a clinician by name. Choose a future "
                "date and time. If you are unsure which specialty you need, read the "
                "Specialty Guide first or book family medicine.",
            ),
            (
                "Step 3. Slot is held (pending)",
                "After you book, status is pending. The clinic is holding that slot. "
                "A provider should confirm soon. If the hold expires with no confirm, "
                "status becomes canceled. Refresh your appointment list if you are waiting.",
            ),
            (
                "Step 4. Confirmation",
                "When the provider or front desk confirms, status becomes confirmed. "
                "You should see a notification that the appointment was confirmed. "
                "Prepare for the visit using the Test and Procedure Preparation guide "
                "if labs or imaging were ordered.",
            ),
            (
                "Step 5. Change of plans",
                "Need a new time while the visit is still pending or confirmed? Use "
                "reschedule and pick another future slot. If you cannot attend and do "
                "not want a new time, ask the clinic to cancel. Do not book a second "
                "overlapping slot with the same provider.",
            ),
            (
                "Step 6. The visit",
                "Arrive on time with ID. Front desk and the provider complete the visit "
                "in SmartHealth. Status becomes complete. You may get a completed "
                "notification. Follow-up booking uses the same book flow.",
            ),
            (
                "Step 7. After the visit",
                "Read any prep instructions before labs. Book a follow-up with the same "
                "or another specialist using the specialty guide. Check notifications "
                "for confirmations and cancellations. Questions about symptoms are not "
                "a substitute for in-person care when you are acutely unwell.",
            ),
            (
                "If something failed",
                "If booking returns that scheduling is unavailable, the hold never "
                "started and you should try again. If the hold expired, book a new time. "
                "If you are not allowed to change a visit, you are signed in as a patient "
                "on an action only staff can take.",
            ),
        ],
    },
}


def _styles():
    base = getSampleStyleSheet()
    title = ParagraphStyle(
        "DocTitle",
        parent=base["Title"],
        fontSize=18,
        spaceAfter=18,
        leading=22,
    )
    heading = ParagraphStyle(
        "DocHeading",
        parent=base["Heading2"],
        fontSize=13,
        spaceBefore=12,
        spaceAfter=6,
        leading=16,
    )
    body = ParagraphStyle(
        "DocBody",
        parent=base["BodyText"],
        fontSize=11,
        leading=15,
        spaceAfter=8,
    )
    return title, heading, body


def build_pdf(path: Path, title: str, sections: list[tuple[str, str]]) -> None:
    title_style, heading_style, body_style = _styles()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        title=title,
        author="SmartHealth",
    )
    story = [Paragraph(title, title_style)]
    for heading, text in sections:
        story.append(Paragraph(heading, heading_style))
        story.append(Paragraph(text, body_style))
        story.append(Spacer(1, 6))
    doc.build(story)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, payload in DOCS.items():
        path = OUT_DIR / filename
        build_pdf(path, payload["title"], payload["sections"])
        print(path)


if __name__ == "__main__":
    main()
