import streamlit as st
import os
import cv2
from datetime import date, datetime

from core.detector import detect_faces, crop_face, assess_photo_quality, draw_boxes
from core.embedder import get_average_embedding
from core.database import save_missing_person, PHOTOS_PATH
from core.styling import score_bar_html


def render():
    st.title("📝 Reporters Portal")
    st.caption("Report a missing person. Provide as much detail as possible every signal helps.")

    with st.form("register_form", clear_on_submit=False):
        st.markdown("#### Personal details")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full name *")
            age = st.number_input("Age when last seen *", min_value=0, max_value=120, step=1)
            sex = st.selectbox("Sex *", ["Female", "Male"])
        with c2:
            height_cm = st.number_input("Height (cm) if known", min_value=0, max_value=250, step=1)
            date_reported = st.date_input("Date reported missing *", value=date.today())
            reporter_contact = st.text_input("Your contact number *")

        st.markdown("#### Last seen")
        last_seen = st.text_input("Where were they last seen?",
                                   placeholder="e.g. Eastleigh, Nairobi near Section 3 market")
        clothing = st.text_area("Clothing description",
                                 placeholder="e.g. Blue school uniform, black shoes, red backpack")

        st.markdown("#### Distinguishing features")
        st.caption("Scars, tattoos, birthmarks, or anything distinctive. "
                   "This is shown to reviewers not used in automated scoring.")
        marks = st.text_area("Distinguishing features",
                              placeholder="e.g. small scar above left eyebrow, mole on right cheek")

        notes = st.text_area("Any other information")

        st.markdown("#### Photos")
        st.caption(
            "Upload up to 5 photos different angles, lighting, and ages all help. "
            "If you only have one photo, even a blurry one, upload it. "
            "**We never reject a photo for quality reasons.**"
        )
        photos = st.file_uploader(
            "Upload photos",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        submitted = st.form_submit_button("Register Case", type="primary")

    if not submitted:
        return

    if not name:
        st.error("Please enter the person's name.")
        return

    if not photos:
        st.error("Please upload at least one photo.")
        return

    if len(photos) > 5:
        st.info("Only the first 5 photos will be used.")
        photos = photos[:5]

    face_crops = []
    saved_paths = []
    quality_notes = []

    with st.spinner("Processing photos..."):
        for i, photo in enumerate(photos):
            try:
                photo.seek(0)
            except Exception:
                pass
            image, faces = detect_faces(photo)

            if len(faces) == 0:
                st.warning(f"Photo {i+1}: no face detected skipped. "
                           f"Try a photo where the person's face is clearly visible.")
                continue

            # multiple faces we'll handle selection below, outside the form
            # For now, store the image and faces for each photo
            quality = assess_photo_quality(image)

            if quality["confidence_level"] != "high":
                note_text = f"Photo {i+1}: {', '.join(quality['notes'])} photo still used."
                st.info(f"📸 {note_text}")
                quality_notes.append(note_text)

            # if multiple faces, pick the largest as default user can override in future
            if len(faces) > 1:
                st.info(f"Photo {i+1}: {len(faces)} faces detected using the largest face. "
                        f"If this is wrong, crop the photo to just the missing person and re-upload.")
                selected_face = max(faces, key=lambda f: f[2] * f[3])
            else:
                selected_face = faces[0]

            face_crop = crop_face(image, selected_face)
            face_crops.append(face_crop)

            os.makedirs(PHOTOS_PATH, exist_ok=True)
            filename = f"mp_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{i}.jpg"
            cv2.imwrite(os.path.join(PHOTOS_PATH, filename), image)
            saved_paths.append(filename)

    if not face_crops:
        st.error(
            "No usable face found in any uploaded photo. "
            "Please check that the photos clearly show the person's face and try again."
        )
        return

    with st.spinner(f"Building facial profile from {len(face_crops)} photo(s)..."):
        try:
            embedding = get_average_embedding(face_crops)
        except Exception as e:
            st.error(
                f"Could not generate a facial embedding. "
                f"Make sure facenet-pytorch is installed. "
                f"Run: pip install facenet-pytorch torch torchvision "
                f"--index-url https://download.pytorch.org/whl/cpu\n\n"
                f"Detail: {e}"
            )
            return

    case_id = save_missing_person(
        data={
            "name": name,
            "age": int(age),
            "sex": sex,
            "height_cm": int(height_cm) if height_cm else None,
            "last_seen": last_seen,
            "clothing": clothing,
            "marks": marks,
            "date_reported": date_reported.strftime("%Y-%m-%d"),
            "reporter_contact": reporter_contact,
            "notes": notes,
            "photo_quality": "moderate" if quality_notes else "high"
        },
        embedding=embedding,
        photo_paths=saved_paths
    )

    st.success(f"✅ Case registered. Share this ID with police or NGOs:")
    st.markdown(
        f'<div style="font-family:monospace; font-size:24px; color:#E8A838; '
        f'padding:16px; background:#0A1520; border-radius:4px; margin:8px 0;">'
        f'{case_id}</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"Facial profile built from **{len(face_crops)} of {len(photos)} photo(s)**. "
        f"More photos improve matching accuracy."
    )

    # age note
    from datetime import datetime as dt
    days_missing = (dt.now().date() - date_reported).days
    if days_missing > 365:
        years = round(days_missing / 365.25, 1)
        current_age = int(age) + int(years)
        st.info(
            f"📅 {name} was {age} when reported missing. "
            f"Based on {years} year(s) elapsed, they would currently be approximately "
            f"**{current_age} years old**. Keep this in mind when reviewing matches."
        )
