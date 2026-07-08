"""
core/demo.py
------------
Seeds TraceKE with 15 realistic Kenyan demo cases so the app feels
alive the first time it's opened no downloads, no manual steps.

Cases cover a realistic spread of ages, counties, circumstances, statuses,
and time missing. Embeddings are random unit vectors real face matching
only activates when real photos are uploaded or LFW seeding is run.
Demo cases are flagged is_demo=1 so they can be identified or cleared.
"""

import numpy as np
import os
from datetime import datetime, timedelta

from core.database import (
    save_missing_person, save_found_person,
    log_match, is_db_empty, update_case_status, PHOTOS_PATH
)


def _days_ago(n: int) -> str:
    """Returns a date string N days before today."""
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


def _unit_vector(dims: int = 512) -> list:
    """Random normalised vector placeholder for a real face embedding."""
    v = np.random.randn(dims)
    return (v / np.linalg.norm(v)).tolist()


DEMO_CASES = [
    # ── Children ──
    {
        "name": "Kevin Omondi Achieng",
        "age": 9, "sex": "Male", "height_cm": 128,
        "last_seen": "Kibera, Nairobi Olympic estate near the primary school",
        "clothing": "Yellow t-shirt, grey shorts, brown sandals",
        "marks": "Birthmark on right forearm, gap in front teeth",
        "date_reported": _days_ago(3),
        "reporter_contact": "0723456789",
        "notes": "Sent to buy sugar from nearby kiosk. Did not return.",
        "status": "Open"
    },
    {
        "name": "Fatuma Hassan Abdullahi",
        "age": 14, "sex": "Female", "height_cm": 155,
        "last_seen": "Mombasa Majengo area, near Majengo Primary School",
        "clothing": "Black abaya, white hijab, blue school bag",
        "marks": "Mole on right cheek, small scar on left knee",
        "date_reported": _days_ago(7),
        "reporter_contact": "0756789012",
        "notes": "Did not return from school. Friends say she was approached by an unknown man outside the gate.",
        "status": "Open"
    },
    {
        "name": "Brian Mwenda Kirimi",
        "age": 11, "sex": "Male", "height_cm": 138,
        "last_seen": "Nyeri Karatina town, near the bus stage",
        "clothing": "Blue school uniform, black shoes",
        "marks": "Diagonal scar on chin from old fall",
        "date_reported": _days_ago(21),
        "reporter_contact": "0700112233",
        "notes": "Was travelling with uncle by bus. Got separated at Karatina stage.",
        "status": "Under Review"
    },
    # ── Teenagers ──
    {
        "name": "Amina Wanjiru Otieno",
        "age": 17, "sex": "Female", "height_cm": 162,
        "last_seen": "Eastleigh, Nairobi Section 3, near the market",
        "clothing": "Blue school uniform, black shoes, red backpack",
        "marks": "Small scar above left eyebrow, ears pierced twice",
        "date_reported": _days_ago(14),
        "reporter_contact": "0712345678",
        "notes": "Last seen walking home from school at 5pm on a Friday.",
        "status": "Open"
    },
    {
        "name": "Samuel Kipkemoi Bett",
        "age": 16, "sex": "Male", "height_cm": 171,
        "last_seen": "Eldoret Langas estate",
        "clothing": "Red hoodie, blue jeans, white sneakers",
        "marks": "Tribal marks on both cheeks (Kalenjin tradition)",
        "date_reported": _days_ago(45),
        "reporter_contact": "0733221100",
        "notes": "Left home after argument with step-father. May have gone to relatives in Kisumu.",
        "status": "Open"
    },
    # ── Young adults ──
    {
        "name": "Grace Njeri Kamau",
        "age": 34, "sex": "Female", "height_cm": 168,
        "last_seen": "Nakuru town near the railway station",
        "clothing": "Green dress, white headscarf, black handbag",
        "marks": "Tattoo of a cross on left wrist, pierced nose",
        "date_reported": _days_ago(45),
        "reporter_contact": "0734567890",
        "notes": "Left Nakuru for Nairobi for domestic work. Never arrived at employer's address.",
        "status": "Under Review"
    },
    {
        "name": "Daniel Kipchoge Ruto",
        "age": 22, "sex": "Male", "height_cm": 178,
        "last_seen": "Eldoret Huruma estate",
        "clothing": "White shirt, black trousers, brown leather shoes",
        "marks": "No distinguishing marks noted",
        "date_reported": _days_ago(180),
        "reporter_contact": "0745678901",
        "notes": "Went to Nairobi to look for work. Last phone contact 6 months ago.",
        "status": "Open"
    },
    {
        "name": "Mercy Akinyi Odhiambo",
        "age": 26, "sex": "Female", "height_cm": 160,
        "last_seen": "Kisumu Kondele roundabout area",
        "clothing": "Orange dress, yellow headwrap, sandals",
        "marks": "Burn scar on right forearm (cooking accident as child)",
        "date_reported": _days_ago(10),
        "reporter_contact": "0711887766",
        "notes": "Was escaping domestic violence situation. Contacted shelter in Nairobi but never arrived.",
        "status": "Open"
    },
    {
        "name": "Hassan Omar Suleiman",
        "age": 29, "sex": "Male", "height_cm": 175,
        "last_seen": "Garissa near Garissa University",
        "clothing": "White kanzu, sandals, carrying a brown satchel",
        "marks": "Beard, small scar on right cheek",
        "date_reported": _days_ago(90),
        "reporter_contact": "0722334455",
        "notes": "University employee. Left for Nairobi for a conference and did not return.",
        "status": "Open"
    },
    # ── Middle-aged adults ──
    {
        "name": "Joyce Wambui Mwangi",
        "age": 43, "sex": "Female", "height_cm": 158,
        "last_seen": "Kakamega town near Kakamega General Hospital",
        "clothing": "Purple blouse, black skirt, flat shoes",
        "marks": "Surgical scar on abdomen, hair usually braided",
        "date_reported": _days_ago(30),
        "reporter_contact": "0755443322",
        "notes": "Has a history of depression. Left saying she was going to the hospital.",
        "status": "Under Review"
    },
    {
        "name": "Peter Otieno Ndege",
        "age": 38, "sex": "Male", "height_cm": 182,
        "last_seen": "Kisii Kisii town, near the main stage",
        "clothing": "Grey suit, white shirt, no tie",
        "marks": "Missing left index finger tip (workshop accident), lion tattoo on right shoulder",
        "date_reported": _days_ago(60),
        "reporter_contact": "0766554433",
        "notes": "Businessman. Large cash withdrawal made the day before disappearance.",
        "status": "Under Review"
    },
    # ── Elderly ──
    {
        "name": "John Mwangi Kariuki",
        "age": 67, "sex": "Male", "height_cm": 170,
        "last_seen": "Nyeri Karatina market, near the vegetable section",
        "clothing": "Grey trousers, brown jacket, black cap",
        "marks": "Walks with a slight limp (left leg), scar on left cheek",
        "date_reported": _days_ago(21),
        "reporter_contact": "0767890123",
        "notes": "Has early-stage dementia. Wandered away from home while daughter was at work.",
        "status": "Open"
    },
    {
        "name": "Mary Wairimu Gichuki",
        "age": 72, "sex": "Female", "height_cm": 152,
        "last_seen": "Nairobi Ruaraka, near Thika Road Mall",
        "clothing": "Blue floral dress, white shawl, flat rubber sandals",
        "marks": "Cataracts in both eyes, usually carries a wooden walking stick",
        "date_reported": _days_ago(5),
        "reporter_contact": "0799887766",
        "notes": "Visited grandchildren in Roysambu. Left to go home alone. Cannot read or use a phone.",
        "status": "Open"
    },
    # ── Resolved / Closed ──
    {
        "name": "Zawadi Auma Ochieng",
        "age": 19, "sex": "Female", "height_cm": 165,
        "last_seen": "Nairobi CBD, near OTC bus terminus",
        "clothing": "Green jacket, black jeans, blue sneakers",
        "marks": "Dreadlocks to shoulders, small gap between front teeth",
        "date_reported": _days_ago(120),
        "reporter_contact": "0744332211",
        "notes": "RESOLVED: Found at Mathare Hospital. Had experienced a mental health episode. Family reunited.",
        "status": "Resolved"
    },
    {
        "name": "Amos Kibet Cheruiyot",
        "age": 45, "sex": "Male", "height_cm": 174,
        "last_seen": "Nakuru Section 58 estate",
        "clothing": "Blue overalls, work boots",
        "marks": "Eagle tattoo on left arm, walks with slight stoop",
        "date_reported": _days_ago(200),
        "reporter_contact": "0788776655",
        "notes": "CLOSED: Deceased. Body identified at Nakuru Level 5 Hospital mortuary. Family notified.",
        "status": "Closed"
    },
]

DEMO_FOUND = [
    {
        "approx_age": 35, "sex": "Female",
        "location_found": "Kisumu Kondele area, near the roundabout",
        "date_found": _days_ago(10),
        "institution": "Jaramogi Oginga Odinga Teaching Hospital",
        "contact": "0700111222",
        "notes": "Found unconscious near bus stop. No ID. Cross-shaped tattoo on left wrist. Burn scar on right arm.",
        "photo_quality": "moderate"
    },
    {
        "approx_age": 10, "sex": "Male",
        "location_found": "Westlands, Nairobi near ABC Place shopping centre",
        "date_found": _days_ago(2),
        "institution": "Nairobi Children's Home Westlands",
        "contact": "0700222333",
        "notes": "Child found wandering alone near shopping mall at 8pm. Gap in front teeth. Very scared.",
        "photo_quality": "high"
    },
    {
        "approx_age": 70, "sex": "Female",
        "location_found": "Mathare, Nairobi along Juja Road",
        "date_found": _days_ago(4),
        "institution": "Mathare North Police Station",
        "contact": "0700333444",
        "notes": "Elderly woman found confused and dehydrated near roadside. Has eye problems. Carrying a broken walking stick.",
        "photo_quality": "low"
    },
]


def seed_demo_data():
    """Seeds demo data only if the database is completely empty."""
    if not is_db_empty():
        return

    os.makedirs(PHOTOS_PATH, exist_ok=True)

    missing_ids = []
    for case in DEMO_CASES:
        data = {k: v for k, v in case.items() if k != "status"}
        data["photo_quality"] = "high"
        case_id = save_missing_person(
            data=data,
            embedding=_unit_vector(),
            photo_paths=["demo_placeholder.jpg"],
            is_demo=True
        )
        if case.get("status", "Open") != "Open":
            update_case_status(case_id, case["status"])
        missing_ids.append(case_id)

    found_ids = []
    for found in DEMO_FOUND:
        found_id = save_found_person(
            data=found,
            embedding=_unit_vector(),
            photo_path="demo_placeholder.jpg",
            is_demo=True
        )
        found_ids.append(found_id)

    # Two realistic match log entries
    log_match(
        missing_id=missing_ids[5],   # Grace Njeri Under Review, Nakuru→Kisumu
        found_id=found_ids[0],
        scores={
            "face_score": 84.2,
            "age_score": 92.0,
            "gender_score": 100.0,
            "final_score": 88.1,
            "location_context": {
                "flag": "far",
                "message": "Found ~350km from last seen may indicate trafficking or relocation. Prioritise review."
            }
        }
    )
    log_match(
        missing_id=missing_ids[12],  # Mary Wairimu elderly, Ruaraka→Mathare
        found_id=found_ids[2],
        scores={
            "face_score": 79.4,
            "age_score": 88.0,
            "gender_score": 100.0,
            "final_score": 83.7,
            "location_context": {
                "flag": "close",
                "message": "Found approximately 4km from last seen location."
            }
        }
    )

    print(f"TraceKE: seeded {len(DEMO_CASES)} cases, {len(DEMO_FOUND)} found persons, 2 match log entries.")
