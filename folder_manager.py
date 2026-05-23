# folder_manager.py — Smart folder creation with duplicate name handling

import os
import re
import json
from datetime import datetime
from config import BASE_DIR, ROLES


def sanitize_name(name: str) -> str:
    """Convert candidate name to safe folder name."""
    name = name.strip().title()
    # Remove special characters, keep letters/numbers/spaces
    name = re.sub(r"[^\w\s-]", "", name)
    # Replace spaces with underscores
    name = re.sub(r"\s+", "_", name)
    return name


def get_unique_folder_name(parent_dir: str, candidate_name: str) -> str:
    """
    Generate a unique folder for a candidate.
    If 'John_Doe' exists, creates 'John_Doe_2', then 'John_Doe_3', etc.
    Also appends timestamp to guarantee uniqueness.
    """
    base_name = sanitize_name(candidate_name)
    candidate_dir = os.path.join(parent_dir, base_name)

    if not os.path.exists(candidate_dir):
        return candidate_dir

    # Folder exists — append incrementing number
    counter = 2
    while True:
        new_name = f"{base_name}_{counter}"
        new_dir = os.path.join(parent_dir, new_name)
        if not os.path.exists(new_dir):
            return new_dir
        counter += 1


def build_folder_structure(role_key: str, status: str, candidate_name: str) -> dict:
    """
    Build complete folder path for a candidate.

    Structure:
    recruitment_data/
      └── bsc_nursing/
            ├── selected/
            │     └── John_Doe/
            │           ├── resume.pdf
            │           └── candidate_info.json
            └── rejected/
                  └── Jane_Smith/
                        ├── resume.pdf
                        └── candidate_info.json

    Returns dict with all relevant paths.
    """
    role_config = ROLES[role_key]
    role_folder = role_config["folder"]
    status_folder = status.lower()  # "selected" or "rejected"

    parent_dir = os.path.join(BASE_DIR, role_folder, status_folder)
    os.makedirs(parent_dir, exist_ok=True)

    candidate_dir = get_unique_folder_name(parent_dir, candidate_name)
    os.makedirs(candidate_dir, exist_ok=True)

    return {
        "candidate_dir": candidate_dir,
        "resume_path": os.path.join(candidate_dir, "resume.pdf"),
        "info_path": os.path.join(candidate_dir, "candidate_info.json"),
        "role_key": role_key,
        "status": status,
    }


def save_candidate_info(info_path: str, candidate_data: dict):
    """Save structured candidate info as JSON."""
    candidate_data["saved_at"] = datetime.now().isoformat()
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(candidate_data, f, indent=4, ensure_ascii=False)


def load_all_candidates() -> list:
    """
    Load all candidate records from all role/status folders.
    Returns a flat list of candidate dicts for the dashboard.
    """
    all_candidates = []

    if not os.path.exists(BASE_DIR):
        return all_candidates

    for role_key, role_config in ROLES.items():
        role_folder = os.path.join(BASE_DIR, role_config["folder"])

        for status in ["selected", "rejected"]:
            status_dir = os.path.join(role_folder, status)

            if not os.path.exists(status_dir):
                continue

            for candidate_folder in os.listdir(status_dir):
                candidate_dir = os.path.join(status_dir, candidate_folder)
                info_file = os.path.join(candidate_dir, "candidate_info.json")

                if os.path.isfile(info_file):
                    try:
                        with open(info_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                        data["_folder"] = candidate_dir
                        data["_role_display"] = role_config["display_name"]
                        data["_status"] = status.upper()
                        all_candidates.append(data)
                    except Exception:
                        pass

    # Sort by saved_at descending (newest first)
    all_candidates.sort(
        key=lambda x: x.get("saved_at", ""),
        reverse=True
    )
    return all_candidates