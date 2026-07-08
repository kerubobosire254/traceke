"""
app/dashboard.py
-----------------
TraceKE Dashboard analytics-first redesign.

Four sections:
1. Command strip live stats with delta indicators
2. Analytics row gender split, age groups, status distribution
3. Urgency breakdown cases bucketed by time missing
4. Case list sortable, filterable, with inline status updates
"""

import streamlit as st
from datetime import datetime, timedelta
from collections import Counter
from core.database import (
    get_all_missing_persons, get_dashboard_stats,
    update_case_status, get_conn
)


# ── Cached queries ──────────────────────────────────────────────────────────

@st.cache_data(ttl=15)
def _stats():
    return get_dashboard_stats()


@st.cache_data(ttl=15)
def _all_cases():
    return get_all_missing_persons()


@st.cache_data(ttl=15)
def _cases_by_status(status):
    return get_all_missing_persons(status)


@st.cache_data(ttl=30)
def _match_score_avg():
    """Average final confidence score across all logged matches."""
    conn = get_conn()
    row = conn.cursor().execute(
        "SELECT AVG(final_score), COUNT(*) FROM match_log"
    ).fetchone()
    conn.close()
    return round(row[0] or 0, 1), row[1] or 0


@st.cache_data(ttl=30)
def _recent_tips_count():
    """Tips submitted in the last 7 days."""
    conn = get_conn()
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    count = conn.cursor().execute(
        "SELECT COUNT(*) FROM tips WHERE timestamp >= ?", (cutoff,)
    ).fetchone()[0]
    conn.close()
    return count


# ── Helpers ─────────────────────────────────────────────────────────────────

def _days_missing(date_reported: str) -> int:
    try:
        d = datetime.strptime(date_reported, "%Y-%m-%d")
        return (datetime.now() - d).days
    except Exception:
        return 0


def _urgency_bucket(days: int) -> str:
    if days <= 7:   return "Critical (0–7 days)"
    if days <= 30:  return "Urgent (8–30 days)"
    if days <= 365: return "Long-term (1–12 months)"
    return "Cold (1+ year)"


def _age_group(age) -> str:
    if age is None: return "Unknown"
    age = int(age)
    if age < 12:  return "Child (0–11)"
    if age < 18:  return "Teenager (12–17)"
    if age < 35:  return "Young adult (18–34)"
    if age < 60:  return "Adult (35–59)"
    return "Elderly (60+)"


def _priority_score(case: dict) -> int:
    days = _days_missing(case.get("date_reported", ""))
    score = 0
    if days <= 7:   score += 50
    elif days <= 30: score += 30
    age = case.get("age") or 0
    if age < 12:    score += 30
    elif age < 18:  score += 20
    elif age >= 65: score += 20
    return score


def _urgency_color(days: int) -> str:
    if days <= 7:   return "#DC2626"
    if days <= 30:  return "#EA580C"
    if days <= 365: return "#D97706"
    return "#94A3B8"


def _days_label(days: int) -> str:
    if days < 30:
        return f"{days}d"
    elif days < 365:
        return f"{days // 30}mo"
    else:
        years = days // 365
        months = (days % 365) // 30
        return f"{years}yr {months}mo" if months else f"{years}yr"


# ── Charts ──────────────────────────────────────────────────────────────────

def _render_donut(values: list, labels: list, colors: list, title: str, center_text: str = ""):
    """Renders a donut chart as inline SVG no external chart library needed."""
    total = sum(values)
    if total == 0:
        st.caption(f"No data for {title}")
        return

    # calculate slice angles
    slices = []
    angle = -90  # start from top
    for i, v in enumerate(values):
        pct = v / total
        sweep = pct * 360
        slices.append((angle, sweep, colors[i % len(colors)], labels[i], v))
        angle += sweep

    def polar(cx, cy, r, deg):
        import math
        rad = math.radians(deg)
        return cx + r * math.cos(rad), cy + r * math.sin(rad)

    cx, cy, R, r = 80, 80, 65, 38
    paths = []
    for start, sweep, color, label, val in slices:
        if sweep < 0.5:
            continue
        end = start + sweep
        large = 1 if sweep > 180 else 0
        x1, y1 = polar(cx, cy, R, start)
        x2, y2 = polar(cx, cy, R, end)
        xi1, yi1 = polar(cx, cy, r, start)
        xi2, yi2 = polar(cx, cy, r, end)
        paths.append(
            f'<path d="M{x1:.1f},{y1:.1f} A{R},{R} 0 {large},1 {x2:.1f},{y2:.1f} '
            f'L{xi2:.1f},{yi2:.1f} A{r},{r} 0 {large},0 {xi1:.1f},{yi1:.1f} Z" '
            f'fill="{color}" stroke="white" stroke-width="2"/>'
        )

    legend = ""
    for i, (label, val) in enumerate(zip(labels, values)):
        if val == 0:
            continue
        pct = round(val / total * 100)
        legend += (
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px;">'
            f'<div style="width:10px;height:10px;border-radius:2px;background:{colors[i % len(colors)]};flex-shrink:0;"></div>'
            f'<span style="font-size:12px;color:#475569;">{label}</span>'
            f'<span style="font-size:12px;font-weight:600;color:#0F172A;margin-left:auto;">{val} ({pct}%)</span>'
            f'</div>'
        )

    svg = f"""
    <div style="display:flex;align-items:center;gap:16px;">
        <svg width="160" height="160" viewBox="0 0 160 160">
            {''.join(paths)}
            <text x="{cx}" y="{cy-6}" text-anchor="middle" font-size="18" font-weight="700" fill="#0F172A">{center_text or total}</text>
            <text x="{cx}" y="{cy+12}" text-anchor="middle" font-size="10" fill="#64748B">total</text>
        </svg>
        <div style="flex:1;">{legend}</div>
    </div>
    """
    st.markdown(f"**{title}**")
    st.markdown(svg, unsafe_allow_html=True)


def _render_bar(values: list, labels: list, colors: list, title: str):
    """Horizontal bar chart as inline SVG."""
    if not values or max(values) == 0:
        st.caption(f"No data for {title}")
        return

    max_val = max(values)
    bar_w = 160
    row_h = 28
    svg_h = len(values) * row_h + 10
    bars = ""
    for i, (label, val) in enumerate(zip(labels, values)):
        y = i * row_h + 5
        w = int((val / max_val) * bar_w) if max_val > 0 else 0
        color = colors[i % len(colors)]
        bars += (
            f'<rect x="0" y="{y+4}" width="{w}" height="16" rx="3" fill="{color}"/>'
            f'<text x="{w + 4}" y="{y+16}" font-size="11" fill="#0F172A" font-weight="600">{val}</text>'
            f'<text x="-4" y="{y+16}" text-anchor="end" font-size="11" fill="#475569">{label}</text>'
        )

    svg = f"""
    <svg width="100%" height="{svg_h}" viewBox="0 0 240 {svg_h}">
        <g transform="translate(72,0)">{bars}</g>
    </svg>
    """
    st.markdown(f"**{title}**")
    st.markdown(svg, unsafe_allow_html=True)


# ── Main render ─────────────────────────────────────────────────────────────

def render():
    st.title("📊 Dashboard")

    cases = _all_cases()
    stats = _stats()
    avg_score, total_matches = _match_score_avg()
    recent_tips = _recent_tips_count()

    # ── SECTION 1: Command strip ─────────────────────────────────────────
    st.markdown("#### Live overview")

    open_cases = [c for c in cases if c.get("status") == "Open"]
    critical = [c for c in open_cases if _days_missing(c.get("date_reported","")) <= 7]
    children = [c for c in open_cases if (c.get("age") or 99) < 18]
    resolution_rate = round(stats["resolved"] / stats["total"] * 100) if stats["total"] > 0 else 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Cases", stats["total"])
    c2.metric("Open", stats["open"])
    c3.metric("🔴 Critical", len(critical), help="Missing 7 days or less highest priority window")
    c4.metric("👶 Minors", len(children), help="Open cases involving people under 18")
    c5.metric("Matches Logged", stats["matches"],
              delta=f"avg {avg_score}%" if avg_score > 0 else None)
    c6.metric("Resolution Rate", f"{resolution_rate}%",
              help="Percentage of registered cases marked Resolved")

    st.divider()

    # ── SECTION 2: Analytics row ─────────────────────────────────────────
    st.markdown("#### Case analytics")

    col1, col2, col3 = st.columns(3)

    with col1:
        gender_counts = Counter(c.get("sex", "Unknown") for c in cases)
        _render_donut(
            values=[gender_counts.get("Female", 0), gender_counts.get("Male", 0), gender_counts.get("Unknown", 0)],
            labels=["Female", "Male", "Unknown"],
            colors=["#0F766E", "#D97706", "#CBD5E1"],
            title="Cases by gender"
        )

    with col2:
        age_groups = ["Child (0–11)", "Teenager (12–17)", "Young adult (18–34)", "Adult (35–59)", "Elderly (60+)", "Unknown"]
        age_counts = Counter(_age_group(c.get("age")) for c in cases)
        _render_bar(
            values=[age_counts.get(g, 0) for g in age_groups],
            labels=["0–11", "12–17", "18–34", "35–59", "60+", "?"],
            colors=["#DC2626", "#EA580C", "#0F766E", "#2563EB", "#7C3AED", "#CBD5E1"],
            title="Cases by age group"
        )

    with col3:
        statuses = ["Open", "Under Review", "Resolved", "Closed"]
        status_counts = Counter(c.get("status", "Open") for c in cases)
        _render_donut(
            values=[status_counts.get(s, 0) for s in statuses],
            labels=statuses,
            colors=["#D97706", "#EA580C", "#16A34A", "#94A3B8"],
            title="Cases by status"
        )

    st.divider()

    # ── SECTION 3: Urgency breakdown ─────────────────────────────────────
    st.markdown("#### Urgency breakdown open cases")

    buckets = {
        "Critical (0–7 days)":    {"cases": [], "color": "#DC2626", "icon": "🔴"},
        "Urgent (8–30 days)":     {"cases": [], "color": "#EA580C", "icon": "🟠"},
        "Long-term (1–12 months)":{"cases": [], "color": "#D97706", "icon": "🟡"},
        "Cold (1+ year)":         {"cases": [], "color": "#94A3B8", "icon": "⚪"},
    }
    for c in open_cases:
        days = _days_missing(c.get("date_reported", ""))
        bucket = _urgency_bucket(days)
        buckets[bucket]["cases"].append(c)

    ub_cols = st.columns(4)
    for col, (bucket_name, bucket_data) in zip(ub_cols, buckets.items()):
        count = len(bucket_data["cases"])
        color = bucket_data["color"]
        icon = bucket_data["icon"]
        label = bucket_name.split(" (")[0]
        timeframe = bucket_name.split("(")[1].rstrip(")")
        with col:
            st.markdown(
                f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;'
                f'border-top:4px solid {color};border-radius:8px;padding:16px;text-align:center;">'
                f'<div style="font-size:28px;font-weight:800;color:{color};">{count}</div>'
                f'<div style="font-size:13px;font-weight:600;color:#0F172A;margin:4px 0 2px;">{icon} {label}</div>'
                f'<div style="font-size:11px;color:#64748B;">{timeframe}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            if count > 0:
                names = ", ".join(c["name"].split()[0] for c in bucket_data["cases"][:3])
                suffix = f" +{count-3} more" if count > 3 else ""
                st.caption(f"{names}{suffix}")

    st.divider()

    # ── SECTION 4: Case list ─────────────────────────────────────────────
    st.markdown("#### Case records")

    filter_col, sort_col, search_col = st.columns([2, 2, 3])
    with filter_col:
        status_filter = st.selectbox(
            "Status", ["All", "Open", "Under Review", "Resolved", "Closed"],
            label_visibility="collapsed"
        )
    with sort_col:
        sort_by = st.selectbox(
            "Sort", ["Priority", "Most recent", "Longest missing", "Name"],
            label_visibility="collapsed"
        )
    with search_col:
        search = st.text_input("Search by name or location", placeholder="🔍  Search...",
                               label_visibility="collapsed")

    filtered = _cases_by_status(None if status_filter == "All" else status_filter)

    if search:
        q = search.lower()
        filtered = [c for c in filtered if
                    q in c.get("name", "").lower() or
                    q in c.get("last_seen", "").lower()]

    if sort_by == "Priority":
        filtered = sorted(filtered, key=_priority_score, reverse=True)
    elif sort_by == "Most recent":
        filtered = sorted(filtered, key=lambda c: c.get("date_reported", ""), reverse=True)
    elif sort_by == "Longest missing":
        filtered = sorted(filtered, key=lambda c: _days_missing(c.get("date_reported", "")), reverse=True)
    elif sort_by == "Name":
        filtered = sorted(filtered, key=lambda c: c.get("name", ""))

    st.caption(f"{len(filtered)} case{'s' if len(filtered) != 1 else ''}")

    for case in filtered:
        _render_case_row(case)


def _render_case_row(case: dict):
    days = _days_missing(case.get("date_reported", ""))
    color = _urgency_color(days)
    label = _days_label(days)
    age = case.get("age", " ")
    sex = case.get("sex", " ")
    status = case.get("status", "Open")

    status_colors = {
        "Open": "#D97706",
        "Under Review": "#EA580C",
        "Resolved": "#16A34A",
        "Closed": "#94A3B8"
    }

    with st.container(border=True):
        st.markdown(
            f'<div style="position:absolute;left:0;top:0;bottom:0;width:4px;'
            f'background:{color};border-radius:4px 0 0 4px;"></div>',
            unsafe_allow_html=True
        )

        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])

        with c1:
            st.markdown(
                f'<div style="font-weight:600;font-size:15px;">{case["name"]}</div>'
                f'<div style="font-family:monospace;font-size:11px;color:#0F766E;">{case["id"]}</div>',
                unsafe_allow_html=True
            )
            if case.get("last_seen"):
                st.caption(f"📍 {case['last_seen'][:50]}")

        with c2:
            st.markdown(
                f'<div style="font-size:12px;color:#64748B;">Age {age} · {sex}</div>',
                unsafe_allow_html=True
            )

        with c3:
            st.markdown(
                f'<div style="font-size:18px;font-weight:700;color:{color};">'
                f'Missing {label}</div>',
                unsafe_allow_html=True
            )

        with c4:
            st.markdown(
                f'<div style="color:{status_colors.get(status,"#94A3B8")};'
                f'font-weight:600;font-size:13px;">{status}</div>',
                unsafe_allow_html=True
            )

        with c5:
            options = ["Open", "Under Review", "Resolved", "Closed"]
            new_status = st.selectbox(
                "Update",
                options,
                index=options.index(status),
                key=f"status_{case['id']}",
                label_visibility="collapsed"
            )
            if new_status != status:
                update_case_status(case["id"], new_status)
                st.cache_data.clear()
                st.rerun()
