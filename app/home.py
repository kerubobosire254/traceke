import streamlit as st
from core.database import get_dashboard_stats
from core.styling import AMBER, TEAL, TEXT_MAIN


def render():
    st.markdown("""
    <div style="padding: 40px 0 24px;">
        <div style="font-size:13px; color:#E8A838; letter-spacing:0.12em; text-transform:uppercase; margin-bottom:12px;">
            Missing Persons Identification Support System
        </div>
        <h1 style="font-size:42px; font-weight:800; line-height:1.1; margin:0;">
            Every face has a name.<br>Every name has a family.
        </h1>
        <p style="margin-top:20px; font-size:16px; color:#475569; max-width:560px; line-height:1.7;">
            TraceKE connects missing persons reports with unidentified individuals
            found by hospitals, mortuaries, shelters, and police stations across Kenya  
            using face recognition combined with supporting evidence, reviewed by humans.
        </p>
    </div>
    """, unsafe_allow_html=True)

    stats = get_dashboard_stats()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Active Cases", stats["open"])
    c2.metric("Cases Resolved", stats["resolved"])
    c3.metric("Matches Flagged", stats["matches"])
    c4.metric("Tips Received", stats["tips"])

    st.divider()

    st.markdown("""
    <div style="background:rgba(232,168,56,0.07); border:1px solid rgba(232,168,56,0.25);
                border-radius:6px; padding:14px 20px; margin-bottom:24px; font-size:13px; color:#E8A838;">
        ⚠️ <strong>Important:</strong> TraceKE never confirms identity automatically.
        Every result is labelled a <em>potential match requiring human verification</em>.
        A trained reviewer must confirm before any family is contacted.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📝 Reporters Portal")
        st.markdown("""
        Report a missing person with photos and details.
        Upload up to 5 photos for a more accurate facial profile.
        A case ID is generated immediately share it with police or NGOs.
        """)
        if st.button("Report a missing person →", type="primary"):
            st.session_state["nav"] = "📝  Reporters Portal"
            st.rerun()

    with col2:
        st.markdown("### 🏥 Institution Portal")
        st.markdown("""
        For hospitals, mortuaries, children's homes, police stations, and NGOs.
        Upload a photo of an unidentified person the system searches for matches
        across all registered cases and returns a confidence-scored breakdown.
        """)
        if st.button("Search for a match →", type="primary"):
            st.session_state["nav"] = "🏥  Institution Portal"
            st.rerun()

    st.divider()

    st.markdown("### 📋 Anyone can submit a tip")
    st.markdown("""
    Spotted someone who might be a missing person? No account needed.
    Upload a photo, share where you saw them, and the system checks it
    against active cases. Tips go to human reviewers families are never
    contacted directly from a tip without verification.
    """)
