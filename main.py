"""
main.py TraceKE entry point
Run: streamlit run main.py

SPEED NOTES:
- @st.cache_resource on load_model() means TensorFlow + Facenet load ONCE
  per process, never again not on page nav, not on rerun
- @st.cache_data(ttl=30) on stats means the DB isn't queried every single
  rerun, only every 30 seconds
- All heavy imports (torch, cv2) happen inside cached functions so they
  don't block the initial page render
"""

import streamlit as st

st.set_page_config(
    page_title="TraceKE",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Inject styles first page renders with correct theme immediately ──
from core.styling import inject_style
inject_style()

# ── DB init + demo seed ──
from core.database import init_db, is_db_empty
init_db()
if is_db_empty():
    from core.demo import seed_demo_data
    seed_demo_data()


# ── Model loaded ONCE, cached for the entire Streamlit process lifetime ──
@st.cache_resource(show_spinner=False)
def load_model():
    """
    st.cache_resource persists across ALL reruns and page navigations.
    TensorFlow + Facenet load here exactly once typically 10-20 seconds
    on first run, then permanently cached in memory.
    """
    from core.embedder import warm_up_model
    warm_up_model()
    return True


# ── Stats cached 30s so sidebar doesn't query DB on every keystroke ──
@st.cache_data(ttl=30)
def get_stats():
    from core.database import get_dashboard_stats
    return get_dashboard_stats()


# ── Load model (shows spinner only on first ever load) ──
if not load_model():
    st.error("Model failed to load.")
    st.stop()


# ── Sidebar ──
with st.sidebar:
    st.markdown("## 🔍 TraceKE")
    st.caption("Tupatane Let's find each other.")
    st.divider()

    page = st.radio(
        "Navigate",
        [
            "🏠  Home",
            "📝  Reporters Portal",
            "🏥  Institution Portal",
            "📋  Submit a Tip",
            "📊  Dashboard",
            "📝  Match Log"
        ],
        label_visibility="collapsed"
    )

    stats = get_stats()
    if stats["total"] > 0:
        st.divider()
        st.markdown(
            f'<div class="demo-banner">'
            f'🧪 <strong>Demo loaded</strong><br>'
            f'{stats["open"]} open · {stats["matches"]} matches</div>',
            unsafe_allow_html=True
        )

    st.divider()
    st.caption(
        "⚠️ All matches are **potential matches requiring human verification**."
    )

# ── Route to page ──
if page == "🏠  Home":
    from app.home import render; render()
elif page == "📝  Reporters Portal":
    from app.register import render; render()
elif page == "🏥  Institution Portal":
    from app.search import render; render()
elif page == "📋  Submit a Tip":
    from app.tip import render; render()
elif page == "📊  Dashboard":
    from app.dashboard import render; render()
elif page == "📝  Match Log":
    from app.match_log import render; render()
