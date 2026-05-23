# dashboard.py - AI HR Recruitment Dashboard (Streamlit)
# Run: streamlit run dashboard.py

import html
import importlib
import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from ai_parser import extract_best_candidate_name, get_rejection_reason
import config as app_config
from email_sender import build_result_email_content
from pdf_reader import extract_text_from_pdf

try:
    import pypdfium2 as pdfium
except ImportError:
    pdfium = None


app_config = importlib.reload(app_config)

st.set_page_config(
    page_title="HR Recruitment Platform",
    page_icon="HR",
    layout="wide",
    initial_sidebar_state="expanded",
)


ROLES = app_config.ROLES
BASE_DIR = app_config.BASE_DIR
ROLE_DETECTION_THRESHOLD = app_config.ROLE_DETECTION_THRESHOLD
SELECTION_THRESHOLD = app_config.SELECTION_THRESHOLD
CONFIG_FILE_PATH = Path(__file__).with_name("config.py")
ROLE_FOLDERS = {
    role_config["folder"]: role_config["display_name"]
    for role_key, role_config in ROLES.items()
}
MUST_HAVE_MIN_MATCH = 2

GENERIC_CANDIDATE_NAMES = {
    "",
    "candidate",
    "applicant",
    "the candidate",
    "name",
    "not mentioned",
    "unknown",
}


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500&display=swap');

:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f5efe4;
    --bg-dark: #1a3868;
    --surface-light: #fffdf8;
    --surface-soft: rgba(255, 255, 255, 0.82);
    --surface-muted: rgba(255, 255, 255, 0.55);
    --surface-dark: rgba(17, 17, 17, 0.96);
    --text-primary: #111111;
    --text-secondary: #444444;
    --text-light: #ffffff;
    --text-light-muted: #d6cbbd;
    --e-global-color-primary: #1A3868;
    --e-global-color-secondary: #111111;
    --e-global-color-text: #000000;
    --e-global-color-accent: #1A3868;
    --e-global-color-874cba6: #1A3868;
    --bg: var(--bg-secondary);
    --paper: rgba(255, 252, 246, 0.88);
    --card: var(--surface-soft);
    --card-strong: var(--surface-light);
    --line: rgba(26, 56, 104, 0.12);
    --text: var(--e-global-color-text);
    --muted: var(--text-secondary);
    --text-on-light: var(--text-primary);
    --muted-on-light: var(--text-secondary);
    --text-on-dark: var(--text-light);
    --muted-on-dark: var(--text-light-muted);
    --accent: var(--e-global-color-primary);
    --accent-soft: rgba(26, 56, 104, 0.14);
    --success: var(--e-global-color-primary);
    --success-soft: rgba(26, 56, 104, 0.12);
    --danger: var(--e-global-color-accent);
    --danger-soft: rgba(26, 56, 104, 0.10);
    --neutral: var(--e-global-color-secondary);
    --neutral-soft: rgba(26, 56, 104, 0.08);
    --btn-primary-bg: #1A3868;
    --btn-primary-bg-hover: #244985;
    --btn-primary-text: var(--text-light);
    --btn-secondary-bg: rgba(26, 56, 104, 0.08);
    --btn-secondary-bg-hover: rgba(26, 56, 104, 0.14);
    --btn-secondary-text: #1A3868;
    --select-bg: var(--bg-primary);
    --select-text: var(--text-primary);
    --select-placeholder: #5f6368;
    --menu-bg: var(--bg-primary);
    --menu-text: var(--text-primary);
    --menu-selected-bg: rgba(26, 56, 104, 0.12);
    --menu-selected-text: var(--text-primary);
    --shadow: 0 18px 45px rgba(72, 46, 26, 0.08);
}

html,
body,
[data-testid="stAppViewContainer"],
[data-testid="stSidebar"] {
    font-family: 'Manrope', sans-serif;
    color: var(--text-on-light);
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top left, rgba(244, 213, 182, 0.52), transparent 28%),
        radial-gradient(circle at top right, rgba(206, 223, 205, 0.48), transparent 24%),
        linear-gradient(180deg, #fbf7f1 0%, #f5efe4 100%);
}

.main .block-container {
    padding-top: 1.4rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(26, 56, 104, 0.98), rgba(17, 17, 17, 0.96));
    border-right: 1px solid rgba(255, 255, 255, 0.06);
    color: var(--text-on-dark);
}

[data-testid="stSidebar"] * {
    color: var(--text-on-dark);
}

[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="input"] input,
[data-testid="stSidebar"] [data-baseweb="textarea"] textarea {
    color: var(--text-primary) !important;
    -webkit-text-fill-color: var(--text-primary) !important;
}

[data-testid="stAppViewContainer"] .stTextInput input::placeholder,
[data-testid="stAppViewContainer"] .stTextArea textarea::placeholder,
[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder {
    color: var(--select-placeholder) !important;
    opacity: 1 !important;
}

/* Defensive widget styling:
   Keep the dashboard theme on visible triggers only.
   Avoid broad BaseWeb overrides that can corrupt Streamlit menus. */
.stSelectbox label,
.stMultiSelect label,
.stSelectbox [data-testid="stWidgetLabel"],
.stMultiSelect [data-testid="stWidgetLabel"] {
    color: var(--text-on-light) !important;
}

.stSelectbox label p,
.stMultiSelect label p,
.stSelectbox [data-testid="stWidgetLabel"] p,
.stMultiSelect [data-testid="stWidgetLabel"] p {
    color: var(--text-on-light) !important;
    font-weight: 700 !important;
}

.stTextInput input,
.stTextArea textarea,
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--select-bg) !important;
    border: 1px solid rgba(26, 56, 104, 0.18) !important;
    border-radius: 12px !important;
    color: var(--select-text) !important;
}

.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    min-height: 44px !important;
    box-shadow: none !important;
}

.stSelectbox [data-baseweb="select"] span,
.stMultiSelect [data-baseweb="select"] span,
.stSelectbox [data-baseweb="select"] input,
.stMultiSelect [data-baseweb="select"] input,
.stSelectbox [data-baseweb="select"] svg,
.stMultiSelect [data-baseweb="select"] svg {
    color: var(--select-text) !important;
    fill: var(--select-text) !important;
}

.stSelectbox [data-baseweb="select"] input,
.stMultiSelect [data-baseweb="select"] input {
    color: var(--select-text) !important;
    -webkit-text-fill-color: var(--select-text) !important;
    caret-color: var(--select-text) !important;
}

.stSelectbox [data-baseweb="select"] input::placeholder,
.stMultiSelect [data-baseweb="select"] input::placeholder {
    color: var(--select-placeholder) !important;
    opacity: 1 !important;
}

.stMultiSelect [data-baseweb="tag"] {
    background: rgba(26, 56, 104, 0.10) !important;
    border: 1px solid rgba(26, 56, 104, 0.16) !important;
    border-radius: 999px !important;
}

.stMultiSelect [data-baseweb="tag"] span,
.stMultiSelect [data-baseweb="tag"] div,
.stMultiSelect [data-baseweb="tag"] svg {
    color: var(--text-on-light) !important;
    fill: var(--text-on-light) !important;
}

[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div,
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div,
[data-testid="stSidebar"] [data-baseweb="textarea"] > div {
    background: var(--bg-primary) !important;
    background-image: none !important;
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] span,
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] span,
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] input,
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] input,
[data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] svg,
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] svg {
    color: var(--text-primary) !important;
    fill: var(--text-primary) !important;
}

[data-testid="stSidebar"] .stSelectbox label p,
[data-testid="stSidebar"] .stMultiSelect label p,
[data-testid="stSidebar"] .stSelectbox [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] .stMultiSelect [data-testid="stWidgetLabel"] p {
    color: var(--text-on-dark) !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stSelectbox [data-baseweb="select"] > div:focus-within,
.stMultiSelect [data-baseweb="select"] > div:focus-within {
    border-color: #1A3868 !important;
    box-shadow: 0 0 0 1px #1A3868 !important;
}

[data-baseweb="popover"] {
    background-color: #ffffff !important;
    background-image: none !important;
    color: #111111 !important;
    opacity: 1 !important;
    filter: none !important;
    mix-blend-mode: normal !important;
    z-index: 9999 !important;
}

[data-baseweb="popover"] > div {
    background-color: #ffffff !important;
    background-image: none !important;
    color: #111111 !important;
    opacity: 1 !important;
    filter: none !important;
}

[data-baseweb="menu"] {
    background-color: #ffffff !important;
    background-image: none !important;
    color: #111111 !important;
    min-height: auto !important;
    height: auto !important;
    max-height: 300px !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding: 4px !important;
    border: 1px solid rgba(26, 56, 104, 0.14) !important;
    border-radius: 12px !important;
    box-shadow: 0 12px 30px rgba(17, 17, 17, 0.12) !important;
}

div[role="listbox"] {
    background-color: #ffffff !important;
    background-image: none !important;
    color: #111111 !important;
    min-height: auto !important;
    height: auto !important;
    max-height: 300px !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}

div[role="option"] {
    background: transparent !important;
    color: #111111 !important;
    min-height: 36px !important;
    height: auto !important;
    display: flex !important;
    align-items: center !important;
    margin: 0 !important;
    padding: 0.55rem 0.85rem !important;
}

div[role="option"]:hover,
div[role="option"][data-highlighted="true"] {
    background: #f3f4f6 !important;
    color: #111111 !important;
}

div[role="option"][aria-selected="true"] {
    background: #dbeafe !important;
    color: #111111 !important;
}

.stButton button,
.stDownloadButton button {
    background: var(--btn-primary-bg) !important;
    color: var(--btn-primary-text) !important;
    border: 1px solid var(--btn-primary-bg) !important;
    border-radius: 14px !important;
}

.stButton button:hover,
.stDownloadButton button:hover {
    background: var(--btn-primary-bg-hover) !important;
    border-color: var(--btn-primary-bg-hover) !important;
    color: var(--btn-primary-text) !important;
}

[data-testid="stAppViewContainer"] button[kind="secondary"],
[data-testid="stSidebar"] button[kind="secondary"] {
    background: var(--btn-secondary-bg) !important;
    color: var(--btn-secondary-text) !important;
    border: 1px solid rgba(26, 56, 104, 0.16) !important;
}

[data-testid="stSidebar"] button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.12) !important;
    color: var(--text-on-dark) !important;
    border-color: rgba(255, 255, 255, 0.18) !important;
}

[data-testid="stAppViewContainer"] button[kind="secondary"]:hover,
[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background: var(--btn-secondary-bg-hover) !important;
    color: var(--btn-secondary-text) !important;
    border-color: rgba(26, 56, 104, 0.24) !important;
}

[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background: rgba(255, 255, 255, 0.18) !important;
    color: var(--text-on-dark) !important;
    border-color: rgba(255, 255, 255, 0.24) !important;
}

.stButton button:disabled,
.stDownloadButton button:disabled,
[data-testid="stAppViewContainer"] button[kind="secondary"]:disabled,
[data-testid="stSidebar"] button[kind="secondary"]:disabled {
    opacity: 0.65 !important;
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] button[kind="secondary"]:disabled {
    color: var(--text-on-dark) !important;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: #1A3868 !important;
}

[data-testid="stTabs"] button[aria-selected="true"]::after {
    background: #1A3868 !important;
}

.hero-shell {
    position: relative;
    overflow: hidden;
    border: 1px solid var(--line);
    background:
        radial-gradient(circle at top right, rgba(255, 255, 255, 0.58), transparent 34%),
        linear-gradient(135deg, rgba(255, 249, 241, 0.92), rgba(246, 234, 218, 0.88));
    border-radius: 28px;
    padding: 28px 30px;
    box-shadow: var(--shadow);
    margin-bottom: 1.2rem;
}

.hero-shell::after {
    content: "";
    position: absolute;
    right: -40px;
    top: -40px;
    width: 180px;
    height: 180px;
    border-radius: 999px;
    background: rgba(26, 56, 104, 0.08);
}

.eyebrow {
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: var(--accent);
    font-weight: 800;
    margin-bottom: 0.65rem;
}

.hero-title {
    font-size: 2rem;
    line-height: 1.05;
    font-weight: 800;
    color: var(--text-on-light);
    margin: 0;
}

.hero-copy {
    max-width: 760px;
    color: var(--muted-on-light);
    font-size: 0.98rem;
    line-height: 1.7;
    margin-top: 0.7rem;
}

.hero-stats {
    display: flex;
    gap: 0.7rem;
    flex-wrap: wrap;
    margin-top: 1rem;
}

.hero-pill {
    background: rgba(255, 255, 255, 0.64);
    border: 1px solid rgba(26, 56, 104, 0.1);
    border-radius: 999px;
    padding: 0.45rem 0.8rem;
    font-size: 0.84rem;
    color: var(--text-on-light);
}

.metric-card {
    border: 1px solid var(--line);
    background: var(--card);
    border-radius: 22px;
    padding: 18px 18px 16px;
    box-shadow: 0 12px 30px rgba(72, 46, 26, 0.05);
    min-height: 132px;
}

.metric-label {
    color: var(--muted-on-light);
    font-size: 0.76rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 700;
}

.metric-value {
    font-size: 2rem;
    line-height: 1.05;
    font-weight: 800;
    color: var(--text-on-light);
    margin: 0.55rem 0 0.25rem;
}

.metric-note {
    color: var(--muted-on-light);
    font-size: 0.84rem;
    line-height: 1.4;
}

.section-title {
    font-size: 1.2rem;
    font-weight: 800;
    color: var(--text-on-light);
    margin: 0.3rem 0 0.2rem;
}

.section-copy {
    color: var(--muted-on-light);
    font-size: 0.92rem;
    margin-bottom: 1rem;
}

.candidate-card {
    border: 1px solid var(--line);
    border-radius: 24px;
    background: var(--paper);
    box-shadow: var(--shadow);
    padding: 0.4rem 0.65rem;
    margin-bottom: 1rem;
    color: var(--text-on-light);
}

.headline-row {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    flex-wrap: wrap;
}

.identity-dot {
    width: 40px;
    height: 40px;
    border-radius: 14px;
    background: linear-gradient(135deg, rgba(26, 56, 104, 0.2), rgba(26, 56, 104, 0.06));
    display: flex;
    align-items: center;
    justify-content: center;
    color: #1A3868;
    font-weight: 800;
    font-size: 1rem;
}

.chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    border-radius: 999px;
    padding: 0.28rem 0.7rem;
    font-size: 0.78rem;
    font-weight: 700;
    border: 1px solid transparent;
    color: var(--text-on-light);
}

.chip-role {
    background: rgba(26, 56, 104, 0.1);
    color: var(--accent);
}

.chip-selected {
    background: var(--success-soft);
    color: var(--success);
}

.chip-rejected {
    background: var(--danger-soft);
    color: var(--danger);
}

.chip-unknown {
    background: rgba(26, 56, 104, 0.08);
    color: var(--accent);
}

.chip-score {
    background: rgba(26, 56, 104, 0.08);
    color: var(--accent);
    border-color: rgba(26, 56, 104, 0.16);
}

.detail-card {
    border: 1px solid var(--line);
    border-radius: 18px;
    background: var(--card-strong);
    padding: 1rem;
    height: 100%;
}

.detail-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted-on-light);
    font-weight: 800;
    margin-bottom: 0.35rem;
}

.detail-value {
    font-size: 0.95rem;
    color: var(--text-on-light);
    line-height: 1.55;
    margin-bottom: 0.9rem;
    word-break: break-word;
}

.skill-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.35rem;
}

.skill-chip {
    background: #f4ece3;
    border: 1px solid rgba(26, 56, 104, 0.1);
    color: var(--accent);
    border-radius: 999px;
    padding: 0.35rem 0.7rem;
    font-size: 0.78rem;
    font-weight: 600;
}

.tone-box {
    border-radius: 18px;
    padding: 0.95rem 1rem;
    line-height: 1.6;
    font-size: 0.92rem;
    margin-top: 0.75rem;
    border: 1px solid transparent;
}

.tone-good {
    background: var(--success-soft);
    color: #1e6244;
    border-color: rgba(47, 122, 87, 0.12);
}

.tone-warn {
    background: #faecd2;
    color: #835216;
    border-color: rgba(176, 119, 39, 0.14);
}

.tone-neutral {
    background: #f0ebe5;
    color: #5c544b;
    border-color: rgba(115, 102, 88, 0.14);
}

.path-box {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.77rem;
    color: var(--accent);
    background: #f8f3ed;
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.8rem 0.9rem;
    margin-top: 0.8rem;
    word-break: break-word;
}

.list-banner {
    border: 1px solid var(--line);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.55);
    padding: 0.9rem 1rem;
    margin-bottom: 0.9rem;
    color: var(--text-on-light);
}

.small-note {
    color: var(--muted-on-light);
    font-size: 0.82rem;
}

div[data-testid="stExpander"] {
    border: none;
    background: transparent;
}

div[data-testid="stExpander"] details {
    border: none;
    background: transparent;
}

div[data-testid="stExpander"] summary {
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.72);
    color: var(--text-on-light) !important;
    border: 1px solid rgba(26, 56, 104, 0.08);
    padding: 0.4rem 0.65rem;
}

div[data-testid="stExpander"] summary * {
    color: var(--text-on-light) !important;
}

div[data-testid="stExpander"] summary:hover {
    background: rgba(255, 255, 255, 0.9);
}

[data-testid="stTable"] *,
[data-testid="stDataFrame"] *,
.stTable *,
.stDataFrame * {
    color: var(--text-on-light) !important;
}
</style>
""",
    unsafe_allow_html=True,
)


def safe_text(value):
    return html.escape(str(value if value not in [None, ""] else "Not Mentioned"))


def normalize_candidate_field(value):
    text = str(value or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    if lowered in {"not mentioned", "n/a", "na", "unknown", "none", "-"}:
        return ""
    return text


def normalize_phone(value):
    text = normalize_candidate_field(value)
    dummy_values = {
        "(123) 456-7890",
        "123-456-7890",
        "1234567890",
        "+1 123-456-7890",
    }
    if text in dummy_values:
        return ""
    digits = "".join(char for char in text if char.isdigit())
    if digits and len(set(digits)) == 1:
        return ""
    if digits in {"1234567890", "0000000000"}:
        return ""
    return text


def list_to_text(items):
    return "\n".join(str(item).strip() for item in (items or []) if str(item).strip())


def text_to_list(value):
    return [line.strip() for line in str(value or "").splitlines() if line.strip()]


def serialize_config_content(roles, role_detection_threshold, selection_threshold, base_dir):
    roles_text = json.dumps(roles, indent=4, ensure_ascii=False)
    return (
        "# config.py — Centralized configuration for all roles\n\n"
        f"ROLES = {roles_text}\n\n"
        "# ── Thresholds ───────────────────────────────────────────────────\n"
        f"ROLE_DETECTION_THRESHOLD = {int(role_detection_threshold)}\n"
        f"SELECTION_THRESHOLD = {int(selection_threshold)}\n\n"
        "# ── Base folder ──────────────────────────────────────────────────\n"
        f'BASE_DIR = {json.dumps(base_dir, ensure_ascii=False)}\n'
    )


def save_rules_config(roles, role_detection_threshold, selection_threshold, base_dir):
    content = serialize_config_content(
        roles,
        role_detection_threshold,
        selection_threshold,
        base_dir,
    )
    with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as config_file:
        config_file.write(content)


def is_generic_candidate_name(value):
    return str(value or "").strip().lower() in GENERIC_CANDIDATE_NAMES


def repair_candidate_record(data, info_file, resume_file):
    updated = False
    current_name = data.get("full_name", "")

    if is_generic_candidate_name(current_name) and os.path.isfile(resume_file):
        resume_text = extract_text_from_pdf(resume_file)
        repaired_name = extract_best_candidate_name(
            resume_text,
            ai_name=current_name,
            email=data.get("email", "") or data.get("sender_email", ""),
        )
        if not is_generic_candidate_name(repaired_name):
            data["full_name"] = repaired_name
            current_name = repaired_name
            updated = True

    saved_plain = str(data.get("sent_email_plain", "") or "")
    saved_html = str(data.get("sent_email_html", "") or "")
    if updated or "Dear Candidate" in saved_plain or "Dear Candidate" in saved_html:
        try:
            rebuilt_email = build_result_email_content(
                data.get("full_name", ""),
                data.get("status", "REJECTED"),
                data.get("role_key", "UNKNOWN_ROLE"),
            )
            data["sent_email_subject"] = rebuilt_email["subject"]
            data["sent_email_plain"] = rebuilt_email["plain_text"]
            data["sent_email_html"] = rebuilt_email["html_body"]
            updated = True
        except Exception:
            pass

    if updated:
        data["saved_at"] = datetime.now().isoformat()
        with open(info_file, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    return data


def load_all_candidates():
    candidates = []
    if not os.path.exists(BASE_DIR):
        return candidates

    for folder_name, role_display in ROLE_FOLDERS.items():
        role_dir = os.path.join(BASE_DIR, folder_name)
        for status in ["selected", "rejected"]:
            status_dir = os.path.join(role_dir, status)
            if not os.path.exists(status_dir):
                continue

            for candidate_folder in os.listdir(status_dir):
                candidate_dir = os.path.join(status_dir, candidate_folder)
                info_file = os.path.join(candidate_dir, "candidate_info.json")
                resume_file = os.path.join(candidate_dir, "resume.pdf")
                if not os.path.isfile(info_file):
                    continue

                try:
                    with open(info_file, "r", encoding="utf-8") as file:
                        data = json.load(file)
                    data = repair_candidate_record(data, info_file, resume_file)
                    data["_folder"] = candidate_dir
                    data["_resume_path"] = resume_file if os.path.isfile(resume_file) else ""
                    data["_role_display"] = role_display
                    data["_status"] = data.get("status", status.upper())
                    data["_folder_name"] = candidate_folder
                    candidates.append(data)
                except Exception:
                    continue

    candidates.sort(key=lambda item: item.get("processed_at", ""), reverse=True)
    return candidates


def get_score_color(score, status="REJECTED", matched_must=None):
    score = int(score or 0)
    matched_must = matched_must or []

    if status == "UNKNOWN":
        return "#7a5c36"
    if status == "REJECTED" and score >= 60 and len(matched_must) < MUST_HAVE_MIN_MATCH:
        return "#9f4c3a"
    if status == "REJECTED":
        return "#9f4c3a"
    if score >= 80:
        return "#2f7a57"
    if score >= 60:
        return "#a16422"
    if score >= 40:
        return "#7a5c36"
    return "#9f4c3a"


def format_time(value):
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return "Not available"


def score_bucket_label(score):
    if score >= 80:
        return "Strong fit"
    if score >= 60:
        return "Worth reviewing"
    if score >= 40:
        return "Borderline fit"
    return "Low fit"


def get_review_signal(candidate):
    status = candidate.get("_status", "REJECTED")
    score = int(candidate.get("match_score", 0) or 0)
    matched_must = candidate.get("matched_must_have", []) or []

    if status == "UNKNOWN":
        return "Role not identified"
    if status == "REJECTED" and score >= 60 and len(matched_must) < MUST_HAVE_MIN_MATCH:
        return "Rejected by rule check"
    if status == "REJECTED":
        return "Below hiring threshold"
    return score_bucket_label(score)


def get_display_rejection_reason(candidate):
    role_key = candidate.get("role_key")
    if not role_key:
        return candidate.get("rejection_reason", "")

    try:
        score = int(candidate.get("match_score", 0) or 0)
        return get_rejection_reason(candidate, role_key, score)
    except Exception:
        return candidate.get("rejection_reason", "")


def summarize_filters(role_filter, status_filter, query):
    summary = []
    if role_filter != "All roles":
        summary.append(role_filter)
    if status_filter != "All statuses":
        summary.append(status_filter)
    if query:
        summary.append(f'Search: "{query}"')
    return " | ".join(summary) if summary else "Showing the full pipeline view"


def render_pdf_preview(pdf_path, height=720):
    if not pdf_path or not os.path.isfile(pdf_path):
        st.info("Resume PDF is not available for this candidate.")
        return

    with open(pdf_path, "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    try:
        st.pdf(pdf_bytes, height=height)
        return
    except Exception:
        pass

    if pdfium is None:
        st.warning("PDF preview is unavailable in this environment. Use the download button to open the resume.")
        return

    st.caption("Preview fallback: rendering PDF pages as images because the Streamlit PDF component is not installed.")

    try:
        pdf_document = pdfium.PdfDocument(pdf_path)
        total_pages = len(pdf_document)
        max_pages_to_render = min(total_pages, 5)

        for page_index in range(max_pages_to_render):
            page = pdf_document[page_index]
            page_image = page.render(scale=1.4).to_pil()
            st.image(
                page_image,
                caption=f"Page {page_index + 1} of {total_pages}",
                use_container_width=True,
            )

        if total_pages > max_pages_to_render:
            st.info(f"Showing the first {max_pages_to_render} pages in the dashboard. Download the PDF to view the full file.")
    except Exception:
        st.warning("Unable to render this PDF preview in the browser. You can still download the resume below.")


def get_sent_email_details(candidate):
    candidate_name = candidate.get("full_name") or "Candidate"
    status = candidate.get("_status") or candidate.get("status") or "REJECTED"
    role_key = candidate.get("role_key") or "UNKNOWN_ROLE"

    saved_subject = candidate.get("sent_email_subject")
    saved_plain = candidate.get("sent_email_plain")
    saved_html = candidate.get("sent_email_html")
    sent_from_email = candidate.get("sent_from_email") or candidate.get("sender_email") or "Not available"
    sent_to_email = candidate.get("sent_to_email") or candidate.get("email") or "Not available"

    try:
        fallback_email = build_result_email_content(candidate_name, status, role_key)
    except Exception:
        fallback_email = {
            "subject": "Not available",
            "plain_text": "Email preview is not available for this candidate.",
        }

    has_saved_email = bool(saved_subject or saved_plain or saved_html)
    plain_text = saved_plain if saved_plain else fallback_email["plain_text"]

    return {
        "from_email": sent_from_email,
        "to_email": sent_to_email,
        "subject": saved_subject if saved_subject else fallback_email["subject"],
        "plain_text": plain_text,
        "html_text": saved_html or fallback_email.get("html_body", ""),
        "source": "Sent email record" if has_saved_email else "Generated preview",
        "received_subject": candidate.get("received_email_subject") or candidate.get("email_subject") or "Not available",
    }


all_candidates = load_all_candidates()


with st.sidebar:
    st.markdown(
        """
        <div style="padding:0.8rem 0 0.5rem;">
          <div style="font-size:0.8rem; text-transform:uppercase; letter-spacing:0.12em; color:var(--text-on-dark); font-weight:800;">Hiring Control Room</div>
          <div style="font-size:1.5rem; font-weight:800; margin-top:0.45rem;">AI Recruitment Platform</div>
          <div style="font-size:0.92rem; color:var(--muted-on-dark); line-height:1.6; margin-top:0.55rem;">
            Designed for faster review, lower cognitive load, and clearer hiring decisions.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Focus filters")
    role_options = ["All roles", "BSC Nursing", "Technical Staff", "Clerical Role", "Unknown / Other"]
    filter_role = st.selectbox(
        "Filter by role",
        role_options,
        index=0,
        help="Narrow the list to one hiring category.",
    )
    status_options = ["All statuses", "Selected", "Rejected", "Unknown"]
    filter_status = st.selectbox(
        "Filter by status",
        status_options,
        index=0,
        help="Focus on shortlisted, rejected, or unmatched candidates.",
    )
    search_query = st.text_input(
        "Search candidates",
        placeholder="Search by name, email, location, or skill",
        help="Type any candidate detail to filter the list instantly.",
    )

    st.markdown("### Why this layout works")
    st.caption(
        "The screen groups related information, uses warm contrast to reduce strain, "
        "and keeps the most important decisions visible first."
    )

    if st.button("Refresh data", use_container_width=True):
        st.rerun()


filtered = all_candidates
if filter_role != "All roles":
    filtered = [candidate for candidate in filtered if candidate.get("_role_display") == filter_role]
if filter_status != "All statuses":
    filtered = [candidate for candidate in filtered if candidate.get("_status") == filter_status.upper()]
if search_query:
    query = search_query.lower()
    filtered = [
        candidate for candidate in filtered
        if (
            query in candidate.get("full_name", "").lower()
            or query in candidate.get("email", "").lower()
            or query in candidate.get("skills", "").lower()
            or query in candidate.get("location", "").lower()
        )
    ]


total = len(all_candidates)
selected_count = sum(1 for item in all_candidates if item.get("_status") == "SELECTED")
rejected_count = sum(1 for item in all_candidates if item.get("_status") == "REJECTED")
unknown_count = sum(1 for item in all_candidates if item.get("_status") == "UNKNOWN")
known_role_displays = {
    role_key: role_config["display_name"]
    for role_key, role_config in ROLES.items()
    if role_key != "UNKNOWN_ROLE"
}
nursing_count = sum(1 for item in all_candidates if item.get("_role_display") == known_role_displays.get("BSC_NURSING"))
tech_count = sum(1 for item in all_candidates if item.get("_role_display") == known_role_displays.get("TECHNICAL_STAFF"))
clerical_count = sum(1 for item in all_candidates if item.get("_role_display") == known_role_displays.get("CLERICAL_ROLE"))
selection_rate = round((selected_count / total * 100) if total else 0, 1)
avg_score = round(
    sum(int(item.get("match_score", 0) or 0) for item in all_candidates if item.get("_status") != "UNKNOWN")
    / max(1, sum(1 for item in all_candidates if item.get("_status") != "UNKNOWN")),
    1,
)
    #   <div class="eyebrow">Human-centered review experience</div>
#   <div class="hero-copy">
#         The interface now uses stronger visual hierarchy, gentle contrast, and grouped information so recruiters can
#         scan less, compare faster, and move from candidate summary to full PDF review without leaving the UI.
#       </div>

st.markdown(
    f"""
    <div class="hero-shell">

      <h1 class="hero-title">Recruitment dashboard</h1>
    
      <div class="hero-stats">
        <div class="hero-pill">{total} applications tracked</div>
        <div class="hero-pill">{selection_rate}% selected</div>
        <div class="hero-pill">Average score {avg_score}</div>
        <div class="hero-pill">{summarize_filters(filter_role, filter_status, search_query)}</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


metric_columns = st.columns(6)
metric_items = [
    ("Applications", total, "Across all folders"),
    ("Selected", selected_count, "High-confidence shortlist"),
    ("Rejected", rejected_count, "Not aligned with criteria"),
    ("Unknown", unknown_count, "No mapped role detected"),
    ("Nursing", nursing_count, "Healthcare pipeline"),
    ("Technical + Clerical", tech_count + clerical_count, "Operations and tech roles"),
]

for column, (label, value, note) in zip(metric_columns, metric_items):
    with column:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">{safe_text(label)}</div>
              <div class="metric-value">{value}</div>
              <div class="metric-note">{safe_text(note)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


tab_candidates, tab_analytics, tab_rules = st.tabs(
    [f"Candidates ({len(filtered)})", "Analytics", "Rules"]
)

with tab_candidates:
    st.markdown('<div class="section-title">Candidate Review</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Summaries appear first, then detailed context, then the resume itself. This follows the way people naturally scan from overview to evidence.</div>',
        unsafe_allow_html=True,
    )

    if not filtered:
        if total == 0:
            st.info("No candidates yet. The system is monitoring your inbox for resumes.")
        else:
            st.warning("No candidates match the current filters.")
    else:
        sort_col, preview_col = st.columns([2, 3])
        with sort_col:
            sort_by = st.selectbox(
                "Sort candidates",
                ["Newest First", "Match Score (High to Low)", "Name A to Z", "Role"],
            )
        with preview_col:
            st.markdown(
                f'<div class="list-banner"><strong>{len(filtered)}</strong> profiles in view. '
                f'<span class="small-note">{safe_text(summarize_filters(filter_role, filter_status, search_query))}</span></div>',
                unsafe_allow_html=True,
            )

        if sort_by == "Match Score (High to Low)":
            filtered = sorted(filtered, key=lambda item: int(item.get("match_score", 0) or 0), reverse=True)
        elif sort_by == "Name A to Z":
            filtered = sorted(filtered, key=lambda item: item.get("full_name", "").lower())
        elif sort_by == "Role":
            filtered = sorted(filtered, key=lambda item: item.get("_role_display", ""))

        for candidate in filtered:
            name = candidate.get("full_name", "Unknown Candidate")
            email_addr = candidate.get("email", "Not Mentioned")
            phone = normalize_phone(candidate.get("phone", ""))
            location = normalize_candidate_field(candidate.get("location", ""))
            experience = normalize_candidate_field(candidate.get("total_experience", ""))
            skills_raw = candidate.get("skills", "")
            education = normalize_candidate_field(candidate.get("education", ""))
            status = candidate.get("_status", "REJECTED")
            role_display = candidate.get("_role_display", "Unknown / Other")
            match_score = int(candidate.get("match_score", 0) or 0)
            key_strengths = candidate.get("key_strengths", "")
            concerns = candidate.get("concerns", "")
            processed_at = candidate.get("processed_at", "")
            sel_reason = candidate.get("selection_reason", "")
            rej_reason = get_display_rejection_reason(candidate)
            folder_path = candidate.get("_folder", "")
            resume_path = candidate.get("_resume_path", "")
            time_str = format_time(processed_at)
            sent_email = get_sent_email_details(candidate)
            matched_must = candidate.get("matched_must_have", []) or []
            status_class = {
                "SELECTED": "chip-selected",
                "REJECTED": "chip-rejected",
                "UNKNOWN": "chip-unknown",
            }.get(status, "chip-unknown")
            initial = safe_text(name[:1].upper() if name else "?")
            score_text = f"{match_score}/100" if status != "UNKNOWN" else "No score"
            review_signal = get_review_signal(candidate)
            expander_label = f"{name} | {role_display} | {score_text}"
            skills_list = [skill.strip() for skill in skills_raw.split(",") if skill.strip()][:10]

            st.markdown('<div class="candidate-card">', unsafe_allow_html=True)
            with st.expander(expander_label, expanded=False):
                st.markdown(
                    f"""
                    <div class="headline-row">
                      <div class="identity-dot">{initial}</div>
                      <div>
                        <div style="font-size:1.15rem; font-weight:800; color:var(--text-on-light);">{safe_text(name)}</div>
                        <div style="font-size:0.9rem; color:var(--muted-on-light);">{safe_text(email_addr)} | {safe_text(location)}</div>
                      </div>
                    </div>
                    <div style="display:flex; gap:0.5rem; flex-wrap:wrap; margin:0.95rem 0 0.35rem;">
                      <span class="chip chip-role">{safe_text(role_display)}</span>
                      <span class="chip {status_class}">{safe_text(status)}</span>
                      <span class="chip chip-score">{safe_text(review_signal)} | {safe_text(score_text)}</span>
                      <span class="chip chip-score">Processed {safe_text(time_str)}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                left_col, right_col = st.columns([1.2, 1.2], gap="large")

                with left_col:
                    info_a, info_b = st.columns([1.2, 1], gap="medium")
                    with info_a:
                        primary_details = [
                            ("Email", email_addr),
                            ("Phone", phone),
                            ("Location", location),
                            ("Experience", experience),
                        ]
                        primary_details_html = "".join(
                            f'<div class="detail-label">{safe_text(label)}</div><div class="detail-value">{safe_text(value)}</div>'
                            for label, value in primary_details if value
                        )
                        if not primary_details_html:
                            primary_details_html = '<div class="detail-value">No contact details available</div>'
                        st.markdown(
                            f"""
                            <div class="detail-card">
                              {primary_details_html}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    with info_b:
                        score_color = get_score_color(match_score, status, matched_must)
                        if status == "UNKNOWN":
                            insight_copy = "Role not recognized by the current rule set."
                        elif status == "REJECTED" and match_score >= 60 and len(matched_must) < MUST_HAVE_MIN_MATCH:
                            insight_copy = "High keyword overlap, but the resume did not show enough must-have role signals."
                        elif status == "REJECTED":
                            insight_copy = "The profile did not clear the hiring threshold for this role."
                        else:
                            insight_copy = review_signal
                        education_html = (
                            f'<div class="detail-label">Education</div><div class="detail-value">{safe_text(education)}</div>'
                            if education else ""
                        )
                        st.markdown(
                            f"""
                            <div class="detail-card">
                              <div class="detail-label">Review signal</div>
                              <div style="font-size:2.15rem; font-weight:800; color:{score_color}; line-height:1;">{safe_text(score_text)}</div>
                              <div class="detail-value" style="margin-top:0.5rem;">{safe_text(insight_copy)}</div>
                              {education_html}
                              <div class="detail-label">Candidate folder</div>
                              <div class="detail-value">{safe_text(candidate.get("_folder_name", "Not available"))}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    st.markdown('<div class="detail-card" style="margin-top:1rem;">', unsafe_allow_html=True)
                    st.markdown('<div class="detail-label">Skills</div>', unsafe_allow_html=True)
                    if skills_list:
                        chips = "".join(f'<span class="skill-chip">{safe_text(skill)}</span>' for skill in skills_list)
                        st.markdown(f'<div class="skill-wrap">{chips}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="detail-value">Not mentioned</div>', unsafe_allow_html=True)

                    if key_strengths and key_strengths.lower() not in ["not mentioned", "n/a"]:
                        st.markdown(
                            f'<div class="tone-box tone-good"><strong>Key strengths:</strong> {safe_text(key_strengths)}</div>',
                            unsafe_allow_html=True,
                        )
                    if concerns and concerns.lower() not in ["not mentioned", "n/a", "none"]:
                        st.markdown(
                            f'<div class="tone-box tone-warn"><strong>Concerns:</strong> {safe_text(concerns)}</div>',
                            unsafe_allow_html=True,
                        )

                    if status == "SELECTED" and sel_reason:
                        st.markdown(
                            f'<div class="tone-box tone-good"><strong>Selection reason:</strong> {safe_text(sel_reason)}</div>',
                            unsafe_allow_html=True,
                        )
                    elif status == "REJECTED" and rej_reason:
                        st.markdown(
                            f'<div class="tone-box tone-warn"><strong>Rejection reason:</strong> {safe_text(rej_reason)}</div>',
                            unsafe_allow_html=True,
                        )
                    elif status == "UNKNOWN":
                        st.markdown(
                            '<div class="tone-box tone-neutral"><strong>Reason:</strong> Resume did not match BSC Nursing, Technical Staff, or Clerical Role.</div>',
                            unsafe_allow_html=True,
                        )

                    if folder_path:
                        st.markdown(f'<div class="path-box">{safe_text(folder_path)}</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with right_col:
                    st.markdown(
                        """
                        <div class="detail-card">
                          <div class="detail-label">Resume preview</div>
                          <div class="detail-value" style="margin-bottom:0.4rem;">
                            Recruiters can now read the PDF without leaving the dashboard.
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.expander("Email sent to this candidate", expanded=False):
                        st.markdown(
                            f"""
                            <div class="detail-card" style="margin-bottom:0.8rem;">
                              <div class="detail-label">From</div>
                              <div class="detail-value">{safe_text(sent_email["from_email"])}</div>
                              <div class="detail-label">To</div>
                              <div class="detail-value">{safe_text(sent_email["to_email"])}</div>
                              <div class="detail-label">Sent subject</div>
                              <div class="detail-value">{safe_text(sent_email["subject"])}</div>
                              <div class="detail-label">Original application subject</div>
                              <div class="detail-value">{safe_text(sent_email["received_subject"])}</div>
                              <div class="detail-label">Preview source</div>
                              <div class="detail-value">{safe_text(sent_email["source"])}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        st.code(sent_email["plain_text"], language="text")
                    render_pdf_preview(resume_path)
                    if resume_path and os.path.isfile(resume_path):
                        download_key_source = candidate.get("_folder", "") or resume_path or name
                        download_key = f"download-{download_key_source.replace(os.sep, '_')}"
                        with open(resume_path, "rb") as resume_file:
                            st.download_button(
                                "Download PDF",
                                data=resume_file.read(),
                                file_name=Path(resume_path).name,
                                mime="application/pdf",
                                use_container_width=True,
                                key=download_key,
                            )
            st.markdown("</div>", unsafe_allow_html=True)


with tab_analytics:
    st.markdown('<div class="section-title">Analytics Overview</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">A simple, low-noise summary helps people notice patterns before digging into individual profiles.</div>',
        unsafe_allow_html=True,
    )

    if total == 0:
        st.info("No data available yet.")
    else:
        a1, a2 = st.columns(2, gap="large")

        with a1:
            st.markdown("**Applications by Role**")
            role_data = {
                known_role_displays.get("BSC_NURSING", "BSC Nursing"): nursing_count,
                known_role_displays.get("TECHNICAL_STAFF", "Technical Staff"): tech_count,
                known_role_displays.get("CLERICAL_ROLE", "Clerical Role"): clerical_count,
                ROLES["UNKNOWN_ROLE"]["display_name"]: unknown_count,
            }
            role_df = pd.DataFrame(list(role_data.items()), columns=["Role", "Count"])
            st.bar_chart(role_df.set_index("Role"))

        with a2:
            st.markdown("**Application Status**")
            status_data = {
                "Selected": selected_count,
                "Rejected": rejected_count,
                "Unknown": unknown_count,
            }
            status_df = pd.DataFrame(list(status_data.items()), columns=["Status", "Count"])
            st.bar_chart(status_df.set_index("Status"))

        st.markdown("### Selection rate by role")
        for role_name in known_role_displays.values():
            role_candidates = [item for item in all_candidates if item.get("_role_display") == role_name]
            role_total = len(role_candidates)
            role_selected = sum(1 for item in role_candidates if item.get("_status") == "SELECTED")
            rate = (role_selected / role_total * 100) if role_total else 0
            st.markdown(f"**{role_name}**: {role_selected}/{role_total} selected ({rate:.0f}%)")
            st.progress(rate / 100 if rate > 0 else 0)


with tab_rules:
    st.markdown('<div class="section-title">Rules Editor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Update hiring rules without editing Python manually. Use one line per keyword or skill, then save your changes back to the live config file.</div>',
        unsafe_allow_html=True,
    )

    threshold_col, role_col = st.columns([1.1, 1.9], gap="large")

    with threshold_col:
        with st.form("global-rule-settings"):
            st.markdown("**Global thresholds**")
            role_detection_threshold_input = st.number_input(
                "Role detection threshold",
                min_value=0,
                value=int(ROLE_DETECTION_THRESHOLD),
                help="Minimum keyword hits needed before a role is considered a match.",
            )
            selection_threshold_input = st.number_input(
                "Selection threshold",
                min_value=0,
                value=int(SELECTION_THRESHOLD),
                help="Minimum must-have hits used by the selection rule engine.",
            )
            base_dir_input = st.text_input(
                "Candidate data folder",
                value=BASE_DIR,
                help="Folder where processed candidate records are stored.",
            )
            save_global = st.form_submit_button("Save global settings", use_container_width=True)

            if save_global:
                updated_roles = json.loads(json.dumps(ROLES))
                save_rules_config(
                    updated_roles,
                    role_detection_threshold_input,
                    selection_threshold_input,
                    base_dir_input.strip() or BASE_DIR,
                )
                st.success(f"Saved global settings to {CONFIG_FILE_PATH.name}. Refresh the app to reload the latest rules everywhere.")

    with role_col:
        editable_role_keys = [role_key for role_key in ROLES if role_key != "UNKNOWN_ROLE"]
        selected_role_key = st.selectbox(
            "Choose role to edit",
            editable_role_keys,
            format_func=lambda role_key: ROLES[role_key]["display_name"],
        )
        role_config = ROLES[selected_role_key]

        with st.form(f"role-rules-{selected_role_key}"):
            st.markdown(f"**Editing: {role_config['display_name']}**")
            st.caption("Write one item per line. Empty lines are ignored when saving.")

            email_selected_input = st.text_input(
                "Selected email subject",
                value=role_config.get("email_subject_selected", ""),
            )
            email_rejected_input = st.text_input(
                "Rejected email subject",
                value=role_config.get("email_subject_rejected", ""),
            )
            experience_input = st.number_input(
                "Minimum experience years",
                min_value=0,
                value=int(role_config.get("experience_min_years", 0) or 0),
            )

            left_rules, right_rules = st.columns(2, gap="large")

            with left_rules:
                keywords_input = st.text_area(
                    "Role keywords",
                    value=list_to_text(role_config.get("keywords", [])),
                    height=180,
                )
                required_skills_input = st.text_area(
                    "Required skills",
                    value=list_to_text(role_config.get("required_skills", [])),
                    height=180,
                )
                preferred_skills_input = st.text_area(
                    "Preferred skills",
                    value=list_to_text(role_config.get("preferred_skills", [])),
                    height=180,
                )

            with right_rules:
                required_education_input = st.text_area(
                    "Required education",
                    value=list_to_text(role_config.get("required_education", [])),
                    height=180,
                )
                must_have_input = st.text_area(
                    "Must-have rule keywords",
                    value=list_to_text(role_config.get("selection_criteria", {}).get("must_have", [])),
                    height=180,
                )
                good_to_have_input = st.text_area(
                    "Good-to-have rule keywords",
                    value=list_to_text(role_config.get("selection_criteria", {}).get("good_to_have", [])),
                    height=180,
                )

            save_role = st.form_submit_button("Save role rules", use_container_width=True)

            if save_role:
                updated_roles = json.loads(json.dumps(ROLES))
                updated_roles[selected_role_key]["email_subject_selected"] = email_selected_input.strip()
                updated_roles[selected_role_key]["email_subject_rejected"] = email_rejected_input.strip()
                updated_roles[selected_role_key]["experience_min_years"] = int(experience_input)
                updated_roles[selected_role_key]["keywords"] = text_to_list(keywords_input)
                updated_roles[selected_role_key]["required_skills"] = text_to_list(required_skills_input)
                updated_roles[selected_role_key]["preferred_skills"] = text_to_list(preferred_skills_input)
                updated_roles[selected_role_key]["required_education"] = text_to_list(required_education_input)
                updated_roles[selected_role_key]["selection_criteria"]["must_have"] = text_to_list(must_have_input)
                updated_roles[selected_role_key]["selection_criteria"]["good_to_have"] = text_to_list(good_to_have_input)

                save_rules_config(
                    updated_roles,
                    ROLE_DETECTION_THRESHOLD,
                    SELECTION_THRESHOLD,
                    BASE_DIR,
                )
                st.success(f"Saved {role_config['display_name']} rules to {CONFIG_FILE_PATH.name}. Refresh the app to reload the latest rules everywhere.")

        known_scores = [int(item.get("match_score", 0) or 0) for item in all_candidates if item.get("_status") != "UNKNOWN"]
        if known_scores:
            st.markdown("### Match score distribution")
            score_df = pd.DataFrame({"Match Score": known_scores})
            st.bar_chart(score_df["Match Score"].value_counts().sort_index())


st.markdown(
    """
    <div style="margin-top:2rem; padding:1rem 0.2rem 0; color:var(--accent); font-size:0.82rem; text-align:center;">
      HR Recruitment Platform | Streamlit dashboard with embedded resume preview
    </div>
    """,
    unsafe_allow_html=True,
)
