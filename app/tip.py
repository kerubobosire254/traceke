import streamlit as st
import os
import cv2
from datetime import datetime
from core.detector import detect_faces, crop_face
from core.embedder import get_embedding
from core.database import search_matches, save_tip, PHOTOS_PATH


def render():
    st.title("📋 Submit a Tip")
    st.caption("Spotted someone who might be a missing person? No account needed.")

    st.markdown("""
    <div style="background:rgba(232,168,56,0.07); border:1px solid rgba(232,168,56,0.2);
                border-radius:4px; padding:12px 16px; margin-bottom:20px; font-size:13px; color:#E8A838;">
        Tips are reviewed by a human before any family is contacted.
        Submitting a tip will never directly notify anyone it flags the case for review.
    </div>
    """, unsafe_allow_html=True)

    photo = st.file_uploader("Upload a photo *", type=["jpg", "jpeg", "png"])
    location = st.text_input("Where did you see them? *",
                              placeholder="e.g. Tom Mboya Street, Nairobi, near GPO")
    description = st.text_area("Describe what you saw",
                                placeholder="What were they doing? What were they wearing? Did they seem distressed?")
    contact = st.text_input("Your contact (optional leave blank to stay anonymous)")

    if st.button("Submit Tip", type="primary"):
        if not photo or not location:
            st.error("Please upload a photo and tell us the location.")
            return

        try:
            photo.seek(0)
        except Exception:
            pass

        image, faces = detect_faces(photo)
        if len(faces) == 0:
            st.error("No face detected. Please upload a photo where the person's face is visible.")
            return

        selected = max(faces, key=lambda f: f[2] * f[3]) if len(faces) > 1 else faces[0]
        face_crop = crop_face(image, selected)

        with st.spinner("Checking against active cases..."):
            try:
                embedding = get_embedding(face_crop)
            except Exception as e:
                st.error(f"Could not process this photo. Please try a clearer one. Detail: {e}")
                return
            matches = search_matches(embedding, top_k=3)
            missing_matches = [m for m in matches if m["type"] == "missing"]

        os.makedirs(PHOTOS_PATH, exist_ok=True)
        filename = f"tip_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        cv2.imwrite(os.path.join(PHOTOS_PATH, filename), image)

        save_tip({
            "photo_path": filename,
            "location": location,
            "description": description,
            "contact": contact or "Anonymous"
        })

        st.success("✅ Tip submitted. Thank you.")
        st.markdown(
            "Your tip will be reviewed by a trained team member. "
            "If there is a potential match, it will be carefully verified before any family is contacted."
        )
        st.caption("For emergencies, please call 999 or Kenya Police on 0800 720 999.")
