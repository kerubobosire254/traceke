"""
core/matcher.py
----------------
Multi-signal matching engine — rebuilt with two key design changes:

1. LOCATION is informational only — never affects the score.
   A person found 500km from where they went missing may have been trafficked.
   Penalizing distance would make us worst at finding people most at risk.

2. DISTINGUISHING MARKS are shown to the human reviewer side by side —
   never scored algorithmically. "Scar above eyebrow" typed by a rushed
   mortuary intake nurse won't keyword-match "cut mark on forehead" from
   a family — same scar, zero overlap. Let a human read both and decide.

ACTIVE SIGNALS (scored):
  Face similarity — 55% weight — the strongest, most objective signal
  Age             — 25% weight — adjusted for time missing
  Gender          — 20% weight — binary match

CONTEXTUAL SIGNALS (displayed, not scored):
  Location distance — shown with trafficking flag if far
  Distinguishing marks — shown side by side for human comparison
"""

from datetime import datetime


WEIGHTS = {
    "face": 0.55,
    "age": 0.25,
    "gender": 0.20,
}


def score_age(estimated_age, reported_age_at_disappearance, date_reported: str = None) -> float:
    """
    Compares estimated age of found person against current estimated age
    of the missing person (accounts for time elapsed since disappearance).
    """
    if estimated_age is None or reported_age_at_disappearance is None:
        return None  # missing data — exclude from scoring, don't guess

    # adjust reported age for time elapsed
    current_expected_age = reported_age_at_disappearance
    if date_reported:
        try:
            reported_dt = datetime.strptime(date_reported, "%Y-%m-%d")
            years_elapsed = (datetime.now() - reported_dt).days / 365.25
            current_expected_age = reported_age_at_disappearance + years_elapsed
        except ValueError:
            pass

    diff = abs(estimated_age - current_expected_age)

    # 0 years diff = 100, loses 8 points per year — softer than before
    # because age estimates from photos are inherently imprecise
    score = max(0, 100 - (diff * 8))
    return round(score, 1)


def score_gender(gender_a: str, gender_b: str) -> float:
    """Binary match. Returns None if either side didn't provide gender."""
    if not gender_a or not gender_b:
        return None
    return 100.0 if gender_a.strip().lower() == gender_b.strip().lower() else 0.0


def get_location_context(last_seen: str, location_found: str, distance_km: float = None) -> dict:
    """
    Returns a contextual flag about location — never a score.
    The caller displays this to the human reviewer alongside the match.
    """
    if not last_seen or not location_found:
        return {
            "flag": "neutral",
            "message": "Location data not available for comparison.",
            "icon": "📍"
        }

    # if we have a calculated distance, use it for the trafficking flag
    if distance_km is not None:
        if distance_km <= 10:
            return {
                "flag": "close",
                "message": f"Found near last seen location (~{round(distance_km, 1)} km away).",
                "icon": "📍"
            }
        elif distance_km <= 100:
            return {
                "flag": "moderate",
                "message": f"Found in a different area from last seen (~{round(distance_km, 1)} km away).",
                "icon": "📍"
            }
        else:
            return {
                "flag": "far",
                "message": (
                    f"Found significantly far from last seen location "
                    f"(~{round(distance_km, 1)} km away) — may indicate trafficking "
                    f"or relocation. Prioritise review."
                ),
                "icon": "⚠️"
            }

    # no distance calculated — just show the location text for human reading
    return {
        "flag": "text_only",
        "message": f"Last seen: {last_seen} · Found at: {location_found}",
        "icon": "📍"
    }


def calculate_final_score(
    face_similarity: float,
    missing_data: dict,
    found_data: dict,
    distance_km: float = None
) -> dict:
    """
    Calculates the final confidence score from active signals only.
    Location and marks are returned as context, not factored into the score.

    If a signal has no data (None), its weight is redistributed proportionally
    to the signals that do have data — the face score never gets diluted by
    fields that simply weren't filled in.
    """
    age_s = score_age(
        found_data.get("approx_age"),
        missing_data.get("age"),
        missing_data.get("date_reported")
    )
    gender_s = score_gender(found_data.get("sex"), missing_data.get("sex"))

    # build the pool of signals we actually have
    active = {"face": face_similarity}
    if age_s is not None:
        active["age"] = age_s
    if gender_s is not None:
        active["gender"] = gender_s

    # redistribute weights across only available signals
    total_weight = sum(WEIGHTS[k] for k in active)
    final = sum(active[k] * WEIGHTS[k] for k in active) / total_weight

    # location context — informational only
    location_ctx = get_location_context(
        missing_data.get("last_seen", ""),
        found_data.get("location_found", ""),
        distance_km
    )

    return {
        "face_score": round(face_similarity, 1),
        "age_score": age_s,
        "gender_score": gender_s,
        "final_score": round(final, 1),
        "signals_used": list(active.keys()),
        "confidence_label": get_confidence_label(final),
        "location_context": location_ctx,
        # marks are passed through for display only — not scored
        "missing_marks": missing_data.get("marks", ""),
        "found_notes": found_data.get("notes", "")
    }


def get_confidence_label(score: float) -> dict:
    """
    Every match gets a label. Nothing is hidden — the human decides
    what to dismiss, not the algorithm.
    """
    if score >= 85:
        return {"text": "High confidence", "color": "green", "icon": "🟢"}
    elif score >= 70:
        return {"text": "Moderate confidence", "color": "orange", "icon": "🟡"}
    elif score >= 50:
        return {"text": "Low confidence — review only if other leads are exhausted", "color": "grey", "icon": "🔵"}
    else:
        return {"text": "Very low confidence", "color": "grey", "icon": "⚪"}
