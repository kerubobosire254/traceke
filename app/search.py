import streamlit as st
import os
import cv2
from datetime import date, datetime

from core.detector import detect_faces, crop_face, assess_photo_quality
from core.embedder import get_embedding
from core.database import save_found_person, search_matches, get_missing_person, log_match, PHOTOS_PATH
from core.matcher import calculate_final_score
from core.styling import score_bar_html, confidence_badge_html, location_flag_html


def render():
    st.title("🏥 Institution Portal")
    st.caption("For hospitals, mortuaries, children's homes, police stations, and NGOs.")

    with st.form("found_form"):
        st.markdown("#### Details of the person found")
        c1, c2 = st.columns(2)
        with c1:
            approx_age = st.number_input("Approximate age", min_value=0, max_value=120, step=1)
            sex = st.selectbox("Sex", ["Female", "Male", "Unknown"])
            institution = st.text_input("Institution name *")
        with c2:
            location_found = st.text_input("Location found *",
                                            placeholder="e.g. Kondele area, Kisumu")
            date_found = st.date_input("Date found", value=date.today())
            contact = st.text_input("Contact number *")

        st.caption("Describe any visible marks, clothing, or condition. "
                   "This is shown to reviewers not used in automated scoring.")
        notes = st.text_area("Notes clothing, visible marks, condition",
                              placeholder="Any detail helps visible scars, what they were wearing, their condition")

        photo = st.file_uploader("Upload a photo *", type=["jpg", "jpeg", "png"])

        submitted = st.form_submit_button("Search for Matches", type="primary")

    if not submitted:
        return

    if not photo or not institution or not location_found:
        st.error("Please fill in all required fields and upload a photo.")
        return

    try:
        photo.seek(0)
    except Exception:
        pass
    image, faces = detect_faces(photo)

    if len(faces) == 0:
        st.error("No face detected in the uploaded photo. "
                 "Please try a clearer photo where the person's face is visible.")
        return

    # if multiple faces, use largest institution photos may have staff in frame
    if len(faces) > 1:
        st.info(f"{len(faces)} faces detected using the largest face. "
                f"If this is wrong, crop the photo and re-upload.")
        selected_face = max(faces, key=lambda f: f[2] * f[3])
    else:
        selected_face = faces[0]

    quality = assess_photo_quality(image)
    if quality["confidence_level"] == "low":
        st.warning(
            f"⚠️ Photo quality notes: {', '.join(quality['notes'])}. "
            f"The photo will still be used, but match confidence may be reduced. "
            f"A reviewer should weigh additional evidence carefully."
        )

    face_crop = crop_face(image, selected_face)

    with st.spinner("Analysing and searching..."):
        try:
            embedding = get_embedding(face_crop)
        except Exception as e:
            st.error(
                f"Could not generate a facial embedding. "
                f"Make sure facenet-pytorch is installed. "
                f"Run: pip install facenet-pytorch torch torchvision "
                f"--index-url https://download.pytorch.org/whl/cpu\n\n"
                f"Detail: {e}"
            )
            return
        raw_matches = search_matches(embedding, top_k=10)

    # save found person regardless of whether we find a match
    os.makedirs(PHOTOS_PATH, exist_ok=True)
    filename = f"fp_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    cv2.imwrite(os.path.join(PHOTOS_PATH, filename), image)

    found_data = {
        "approx_age": int(approx_age) if approx_age else None,
        "sex": sex if sex != "Unknown" else None,
        "location_found": location_found,
        "date_found": date_found.strftime("%Y-%m-%d"),
        "institution": institution,
        "contact": contact,
        "notes": notes,
        "photo_quality": quality["confidence_level"]
    }
    found_id = save_found_person(found_data, embedding, filename)

    # filter to missing persons only
    candidates = [m for m in raw_matches if m["type"] == "missing"]

    if not candidates:
        st.info("No potential matches found. This case has been logged "
                "it will automatically match if someone reports this person missing.")
        return

    # score all candidates
    scored = []
    for m in candidates:
        person = get_missing_person(m["case_id"])
        if not person:
            continue
        scores = calculate_final_score(
            face_similarity=m["similarity"],
            missing_data=person,
            found_data=found_data,
            distance_km=None
        )
        scored.append({"person": person, "scores": scores})
        log_match(m["case_id"], found_id, scores)

    # sort by final score descending show all, labelled by confidence
    scored.sort(key=lambda x: x["scores"]["final_score"], reverse=True)
    top = scored[:3]

    st.divider()
    st.markdown(f"### {len(top)} potential match{'es' if len(top) != 1 else ''} found")
    st.markdown(
        '<div style="font-size:13px; color:#8A9BB0; margin-bottom:16px;">'
        '⚠️ These are <strong>potential matches requiring human verification</strong>. '
        'Do not contact families based on this result alone.</div>',
        unsafe_allow_html=True
    )

    for match in top:
        render_match_card(match["person"], match["scores"])


def render_match_card(person: dict, scores: dict):
    label = scores["confidence_label"]
    loc_ctx = scores.get("location_context", {})

    with st.container(border=True):
        c1, c2 = st.columns([1, 2])

        with c1:
            st.markdown(f"### {person['name']}")
            st.markdown(
                f'<span class="case-id">{person["id"]}</span>',
                unsafe_allow_html=True
            )
            st.markdown(f"**Age reported:** {person['age']}")
            st.markdown(f"**Last seen:** {person.get('last_seen', ' ')}")
            if person.get("marks"):
                st.markdown(f"**Marks (family):** {person['marks']}")

        with c2:
            final = scores["final_score"]
            st.markdown(
                f'<div style="font-size:28px; font-weight:700; color:#F4F6F9;">'
                f'{final}% match</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                confidence_badge_html(label),
                unsafe_allow_html=True
            )
            st.markdown(score_bar_html(final), unsafe_allow_html=True)

            # score breakdown
            st.markdown(f"""
| Signal | Score | Weight |
|--------|-------|--------|
| Face similarity | {scores['face_score']}% | Primary |
| Age match | {scores['age_score'] if scores['age_score'] is not None else ' '}% | Supporting |
| Gender | {'Match ✓' if scores['gender_score'] == 100 else ('No match ✗' if scores['gender_score'] == 0 else ' ')} | Supporting |
""")
            # location flag informational, never scored
            if loc_ctx:
                st.markdown(
                    location_flag_html(loc_ctx),
                    unsafe_allow_html=True
                )

            # marks side by side for human comparison
            if scores.get("missing_marks") or scores.get("found_notes"):
                with st.expander("Compare distinguishing features"):
                    mc, fc = st.columns(2)
                    mc.markdown(f"**Family reported:**\n\n{scores.get('missing_marks') or 'None noted'}")
                    fc.markdown(f"**Institution notes:**\n\n{scores.get('found_notes') or 'None noted'}")
                    st.caption("These descriptions are for human review only not factored into the score.")
