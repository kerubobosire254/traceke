import streamlit as st
from core.database import get_match_log, get_missing_person, get_found_person
from core.styling import score_bar_html, confidence_badge_html
from core.matcher import get_confidence_label


def render():
    st.title("📝 Match Log")
    st.caption("Every potential match flagged by TraceKE the audit trail.")

    logs = get_match_log()

    if not logs:
        st.info("No matches have been logged yet. Run a search from the Institution Portal to generate matches.")
        return

    st.markdown(f"### {len(logs)} logged match{'es' if len(logs) != 1 else ''}")

    for entry in logs:
        render_log_entry(entry)


def render_log_entry(entry: dict):
    missing = get_missing_person(entry["missing_id"])
    name = missing["name"] if missing else "Unknown"
    found = get_found_person(entry["found_id"])
    institution = found["institution"] if found else "Unknown institution"

    final = entry.get("final_score") or 0
    label = get_confidence_label(final)
    timestamp = (entry.get("timestamp") or "")[:16].replace("T", " ")

    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 2, 1])

        with c1:
            st.markdown(f"**{name}**")
            st.markdown(
                f'<span style="font-family:monospace; font-size:12px; color:#E8A838;">'
                f'{entry["missing_id"]}</span>',
                unsafe_allow_html=True
            )
            st.caption(f"Matched by: {institution}")

        with c2:
            st.markdown(
                f'<div style="font-size:22px; font-weight:700;">{final}%</div>',
                unsafe_allow_html=True
            )
            st.markdown(score_bar_html(final), unsafe_allow_html=True)
            st.markdown(confidence_badge_html(label), unsafe_allow_html=True)

        with c3:
            st.caption(timestamp)
            status = entry.get("status", "Pending")
            color = "#E8A838" if status == "Pending" else "#2ECC71"
            st.markdown(
                f'<div style="color:{color}; font-weight:600; font-size:12px;">{status}</div>',
                unsafe_allow_html=True
            )
