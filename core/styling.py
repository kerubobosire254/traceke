"""
core/styling.py
TraceKE visual identity — light, warm, friendly.

Design direction:
- Warm white base with soft sage/teal accents
- Google Fonts: DM Sans for body (friendly, rounded, readable)
- No dark backgrounds, no harsh contrasts
- Rounded corners throughout
- Soft shadows instead of sharp borders
"""

import streamlit as st

WHITE       = "#FFFFFF"
OFF_WHITE   = "#F7F9F7"
SAGE        = "#4A7C6F"
SAGE_LIGHT  = "#E8F5F0"
SAGE_DARK   = "#2D5A50"
WARM_GRAY   = "#F0F2F0"
TEAL        = "#4A7C6F"
TEAL_LIGHT  = "#E8F5F0"
AMBER       = "#D47C0F"
AMBER_LIGHT = "#FEF6E4"
GREEN       = "#2E7D52"
GREEN_LIGHT = "#E8F5EE"
RED         = "#C0392B"
RED_LIGHT   = "#FDE8E6"
ORANGE      = "#D4580C"
ORANGE_LIGHT= "#FEF0E6"
BORDER      = "#DDE8E4"
TEXT_MAIN   = "#1A2E28"
TEXT_MUTED  = "#6B8A82"


def inject_style():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <style>
    /* Base */
    html, body, .stApp {{
        background-color: {OFF_WHITE} !important;
        color: {TEXT_MAIN};
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    /* Remove default Streamlit padding harshness */
    .main .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1100px;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {WHITE} !important;
        border-right: 1px solid {BORDER};
    }}
    [data-testid="stSidebar"] * {{
        font-family: 'DM Sans', sans-serif !important;
        color: {TEXT_MAIN} !important;
    }}
    [data-testid="stSidebar"] hr {{
        border-color: {BORDER} !important;
    }}

    /* Headings */
    h1, h2, h3, h4 {{
        font-family: 'DM Sans', sans-serif !important;
        color: {TEXT_MAIN} !important;
        font-weight: 600 !important;
        letter-spacing: -0.2px;
    }}
    h1 {{ font-size: 26px !important; }}
    h2 {{ font-size: 20px !important; }}
    h3 {{ font-size: 17px !important; }}

    /* Metric cards */
    [data-testid="metric-container"] {{
        background: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(74,124,111,0.06);
    }}
    [data-testid="metric-container"] label {{
        color: {TEXT_MUTED} !important;
        font-size: 11px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-family: 'DM Sans', sans-serif !important;
    }}
    [data-testid="metric-container"] [data-testid="stMetricValue"] {{
        color: {TEXT_MAIN} !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        font-family: 'DM Sans', sans-serif !important;
    }}

    /* Case ID monospace */
    .case-id {{
        font-family: 'DM Mono', monospace;
        color: {SAGE};
        font-size: 11px;
        font-weight: 500;
        background: {SAGE_LIGHT};
        padding: 2px 8px;
        border-radius: 6px;
        display: inline-block;
    }}

    /* Confidence badges */
    .conf-green {{
        background: {GREEN_LIGHT};
        color: {GREEN};
        border: 1px solid {GREEN};
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        font-family: 'DM Sans', sans-serif;
    }}
    .conf-orange {{
        background: {ORANGE_LIGHT};
        color: {ORANGE};
        border: 1px solid {ORANGE};
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        font-family: 'DM Sans', sans-serif;
    }}
    .conf-grey {{
        background: {WARM_GRAY};
        color: {TEXT_MUTED};
        border: 1px solid {BORDER};
        border-radius: 20px;
        padding: 3px 12px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        font-family: 'DM Sans', sans-serif;
    }}

    /* Location flags */
    .flag-far {{
        background: {RED_LIGHT};
        border-left: 3px solid {RED};
        padding: 10px 14px;
        font-size: 13px;
        color: #8B1A12;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-family: 'DM Sans', sans-serif;
    }}
    .flag-close {{
        background: {GREEN_LIGHT};
        border-left: 3px solid {GREEN};
        padding: 10px 14px;
        font-size: 13px;
        color: #1A5C35;
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-family: 'DM Sans', sans-serif;
    }}
    .flag-neutral {{
        background: {WARM_GRAY};
        border-left: 3px solid {BORDER};
        padding: 10px 14px;
        font-size: 13px;
        color: {TEXT_MUTED};
        border-radius: 0 8px 8px 0;
        margin: 8px 0;
        font-family: 'DM Sans', sans-serif;
    }}

    /* Score bar */
    .score-bar-wrap {{
        background: {BORDER};
        border-radius: 8px;
        height: 8px;
        width: 100%;
        margin: 6px 0 14px;
    }}
    .score-bar-fill {{
        height: 8px;
        border-radius: 8px;
    }}

    /* Inputs */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox select {{
        background: {WHITE} !important;
        border: 1.5px solid {BORDER} !important;
        color: {TEXT_MAIN} !important;
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
    }}
    .stTextInput input:focus,
    .stTextArea textarea:focus {{
        border-color: {SAGE} !important;
        box-shadow: 0 0 0 3px rgba(74,124,111,0.12) !important;
    }}

    /* Primary buttons */
    .stButton > button[kind="primary"] {{
        background: {SAGE} !important;
        color: {WHITE} !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        font-size: 14px !important;
        font-family: 'DM Sans', sans-serif !important;
        box-shadow: 0 2px 8px rgba(74,124,111,0.25);
        transition: all 0.2s;
    }}
    .stButton > button[kind="primary"]:hover {{
        background: {SAGE_DARK} !important;
        box-shadow: 0 4px 12px rgba(74,124,111,0.35);
    }}

    /* Secondary buttons */
    .stButton > button:not([kind="primary"]) {{
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
    }}

    /* Containers */
    [data-testid="stVerticalBlockBorderWrapper"] {{
        border-radius: 12px !important;
        border-color: {BORDER} !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}

    /* Demo banner */
    .demo-banner {{
        background: {SAGE_LIGHT};
        border: 1px solid #B8D8D0;
        border-left: 3px solid {SAGE};
        border-radius: 8px;
        padding: 10px 16px;
        font-size: 12px;
        color: {SAGE_DARK};
        margin-bottom: 12px;
        line-height: 1.5;
        font-family: 'DM Sans', sans-serif;
    }}

    /* Dividers */
    hr {{ border-color: {BORDER} !important; }}

    /* Captions */
    .stCaption, [data-testid="stCaptionContainer"] {{
        font-family: 'DM Sans', sans-serif !important;
        color: {TEXT_MUTED} !important;
    }}

    /* Radio buttons in sidebar */
    .stRadio label {{
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
    }}

    /* File uploader */
    [data-testid="stFileUploader"] {{
        background: {WHITE};
        border: 2px dashed {BORDER};
        border-radius: 12px;
        padding: 8px;
    }}
    [data-testid="stFileUploader"]:hover {{
        border-color: {SAGE};
    }}

    /* Selectbox */
    [data-testid="stSelectbox"] > div > div {{
        border-radius: 10px !important;
        font-family: 'DM Sans', sans-serif !important;
    }}

    /* Info/warning/error boxes */
    [data-testid="stInfo"] {{
        background: {SAGE_LIGHT} !important;
        border-left-color: {SAGE} !important;
        border-radius: 8px;
    }}
    [data-testid="stWarning"] {{
        border-radius: 8px;
    }}
    [data-testid="stError"] {{
        border-radius: 8px;
    }}
    [data-testid="stSuccess"] {{
        border-radius: 8px;
    }}

    /* Form submit button area */
    [data-testid="stForm"] {{
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 20px;
        background: {WHITE};
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }}
    </style>
    """, unsafe_allow_html=True)


def score_bar_html(score: float) -> str:
    if score >= 85:
        color = GREEN
    elif score >= 70:
        color = ORANGE
    else:
        color = TEXT_MUTED
    return (
        f'<div class="score-bar-wrap">'
        f'<div class="score-bar-fill" style="width:{min(score,100):.0f}%;background:{color};"></div>'
        f'</div>'
    )


def confidence_badge_html(label_dict: dict) -> str:
    icon = label_dict.get("icon", "")
    text = label_dict.get("text", "")
    color = label_dict.get("color", "grey")
    css_map = {"green": "conf-green", "orange": "conf-orange", "grey": "conf-grey"}
    css = css_map.get(color, "conf-grey")
    return f'<span class="{css}">{icon} {text}</span>'


def location_flag_html(ctx: dict) -> str:
    flag = ctx.get("flag", "neutral")
    css = {"far": "flag-far", "close": "flag-close"}.get(flag, "flag-neutral")
    return f'<div class="{css}">{ctx.get("icon","📍")} {ctx.get("message","")}</div>'


def case_id_html(case_id: str) -> str:
    return f'<span class="case-id">{case_id}</span>'
