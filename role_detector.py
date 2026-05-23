# role_detector.py — Accurate role detection from resume text

import re
from config import ROLES, ROLE_DETECTION_THRESHOLD


def normalize(text: str) -> str:
    """Lowercase and clean text for matching."""
    return text.lower()


def count_keyword_matches(text: str, keywords: list) -> int:
    """Count how many keywords appear in the resume text."""
    text_lower = normalize(text)
    count = 0
    for keyword in keywords:
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, text_lower):
            count += 1
    return count


def detect_role(resume_text: str, subject: str = "") -> str:
    """
    Detect which role this resume belongs to.

    Strategy:
    1. Check email subject line first (highest priority)
    2. Score each role by keyword frequency
    3. Return highest-scoring role only if above threshold
    4. Return UNKNOWN_ROLE if no clear match found

    Returns role_key string: 'BSC_NURSING', 'TECHNICAL_STAFF', 'CLERICAL_ROLE', or 'UNKNOWN_ROLE'
    """
    combined_text = f"{subject} {resume_text}"

    # Step 1: Check subject for explicit role mention
    subject_lower = normalize(subject)

    if any(word in subject_lower for word in ["nursing", "nurse", "gnm", "anm"]):
        return "BSC_NURSING"

    if any(word in subject_lower for word in [
        "technical", "developer", "engineer", "software", "it staff",
        "data scientist", "programmer", "devops"
    ]):
        return "TECHNICAL_STAFF"

    if any(word in subject_lower for word in [
        "clerical", "admin", "clerk", "office assistant", "receptionist",
        "data entry", "secretary"
    ]):
        return "CLERICAL_ROLE"

    # Step 2: Score each role (exclude UNKNOWN_ROLE from scoring)
    scores = {}
    for role_key, role_config in ROLES.items():
        if role_key == "UNKNOWN_ROLE":
            continue
        score = count_keyword_matches(combined_text, role_config["keywords"])
        scores[role_key] = score

    # Step 3: Check education for strong nursing signal
    text_lower = normalize(resume_text)
    nursing_edu = ["bsc nursing", "b.sc nursing", "gnm", "anm", "bscn", "registered nurse"]
    if any(edu in text_lower for edu in nursing_edu):
        scores["BSC_NURSING"] = scores.get("BSC_NURSING", 0) + 10  # heavy boost

    # Step 4: Return role with highest score ONLY if above threshold
    if scores:
        best_role = max(scores, key=scores.get)
        best_score = scores[best_role]

        print(f"   Role Scores: { {k: v for k, v in scores.items()} }")
        print(f"   Best Match : {best_role} (score: {best_score})")

        if best_score >= ROLE_DETECTION_THRESHOLD:
            return best_role

    # Step 5: No clear match — UNKNOWN_ROLE
    print("   ⚠️  No role matched — marking as UNKNOWN_ROLE")
    return "UNKNOWN_ROLE"


def check_selection_criteria(resume_text: str, role_key: str) -> tuple:
    """
    Check if candidate meets selection criteria for the role.

    Returns:
        (is_selected: bool, matched_must_have: list, matched_good_to_have: list)
    """
    # UNKNOWN_ROLE ke liye seedha False return karo
    if role_key == "UNKNOWN_ROLE":
        return False, [], []

    text_lower = normalize(resume_text)
    role_config = ROLES[role_key]
    criteria = role_config["selection_criteria"]

    matched_must = []
    matched_good = []

    for keyword in criteria["must_have"]:
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, text_lower):
            matched_must.append(keyword)

    for keyword in criteria["good_to_have"]:
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        if re.search(pattern, text_lower):
            matched_good.append(keyword)

    is_selected = len(matched_must) >= 2

    return is_selected, matched_must, matched_good