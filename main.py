# main.py — AI HR Recruitment Engine
# Processes incoming emails, detects role, analyzes resume, sends result

import imaplib
import email
import os
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from email.utils import parseaddr

from pdf_reader import extract_text_from_pdf
from ai_parser import analyze_resume, extract_best_candidate_name
from role_detector import detect_role, check_selection_criteria
from email_sender import send_result_email, build_result_email_content
from folder_manager import build_folder_structure, save_candidate_info
from config import ROLES

# ══════════════════════════════════════════════════════════════════
# LOAD ENV VARIABLES
# ══════════════════════════════════════════════════════════════════

load_dotenv()

EMAIL_ADDR  = os.getenv("EMAIL")
PASSWORD    = os.getenv("PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")

# ── Thresholds ───────────────────────────────────────────────────
SELECTION_SCORE_THRESHOLD = 60   # score >= 60 → SELECTED
MUST_HAVE_MIN_MATCH       = 2    # kam se kam 2 must_have keywords chahiye

# ══════════════════════════════════════════════════════════════════
# CONNECT TO GMAIL
# ══════════════════════════════════════════════════════════════════

def connect_mail():
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ADDR, PASSWORD)
        print("✅ Connected to Gmail")
        return mail
    except Exception as error:
        print(f"❌ Connection Error: {error}")
        return None


# ══════════════════════════════════════════════════════════════════
# FINAL DECISION — single place, clear logic
# ══════════════════════════════════════════════════════════════════

def make_final_decision(candidate_data: dict, rule_selected: bool,
                        matched_must: list, resume_text: str,
                        role_key: str) -> str:
    """
    Final selection/rejection decision — ek jagah, clear rules.

    Rules:
    1. Score < SELECTION_SCORE_THRESHOLD → REJECT (koi exception nahi)
    2. must_have matches < MUST_HAVE_MIN_MATCH → REJECT (wrong role)
    3. Score >= threshold AND must_have >= 2 → SELECTED

    AI ka status yahan use nahi hota — sirf score aur rule check.
    """
    score         = int(candidate_data.get("match_score", "0") or "0")
    must_matched  = len(matched_must)

    print(f"\n   === FINAL DECISION ===")
    print(f"   Score         : {score}/100  (threshold: {SELECTION_SCORE_THRESHOLD})")
    print(f"   Must-have hit : {must_matched}  (minimum: {MUST_HAVE_MIN_MATCH})")
    print(f"   Rule selected : {rule_selected}")

    # Rule 1: Score threshold
    if score < SELECTION_SCORE_THRESHOLD:
        print(f"   → REJECTED (score {score} < {SELECTION_SCORE_THRESHOLD})")
        return "REJECTED"

    # Rule 2: Must-have minimum
    if must_matched < MUST_HAVE_MIN_MATCH:
        print(f"   → REJECTED (only {must_matched} must_have matched, "
              f"need {MUST_HAVE_MIN_MATCH})")
        return "REJECTED"

    # Rule 3: Both pass → SELECTED
    print(f"   → SELECTED (score {score} >= {SELECTION_SCORE_THRESHOLD}, "
          f"must_have {must_matched} >= {MUST_HAVE_MIN_MATCH})")
    return "SELECTED"


# ══════════════════════════════════════════════════════════════════
# PROCESS SINGLE EMAIL
# ══════════════════════════════════════════════════════════════════

def process_email(mail, email_id, processed_ids):
    """Process one email and its PDF attachments."""

    if email_id in processed_ids:
        return

    processed_ids.add(email_id)

    status, msg_data = mail.fetch(email_id, "(RFC822)")
    if status != "OK":
        return

    raw_email = msg_data[0][1]
    msg = email.message_from_bytes(raw_email)

    sender_name, sender_email = parseaddr(msg.get("From"))
    subject = msg.get("Subject", "")

    print(f"\n{'='*60}")
    print(f"📩 NEW EMAIL")
    print(f"   From   : {sender_email}")
    print(f"   Subject: {subject}")
    print(f"{'='*60}")

    pdf_found = False

    for part in msg.walk():
        if part.get_content_disposition() != "attachment":
            continue

        filename = part.get_filename()
        if not filename:
            continue

        if not filename.lower().endswith(".pdf"):
            print(f"⚠️  Skipping non-PDF: {filename}")
            continue

        pdf_found = True
        pdf_data  = part.get_payload(decode=True)

        print(f"\n📄 Processing PDF: {filename}")

        # ── STEP 1: Save temp PDF ────────────────────────────────
        temp_path = f"/tmp/{filename}"
        with open(temp_path, "wb") as f:
            f.write(pdf_data)

        # ── STEP 2: Extract text ─────────────────────────────────
        resume_text = extract_text_from_pdf(temp_path)

        if not resume_text:
            print("❌ Could not extract text from PDF")
            continue

        print(f"✅ Text extracted ({len(resume_text)} chars)")

        # ── STEP 3: Detect Role ──────────────────────────────────
        role_key = detect_role(resume_text, subject)
        print(f"🎯 Role Detected: {ROLES[role_key]['display_name']}")

        # ── STEP 4: UNKNOWN ROLE handling ───────────────────────
        if role_key == "UNKNOWN_ROLE":
            print("⚠️  Resume does not match any open role")

            candidate_name = extract_best_candidate_name(
                resume_text,
                email=sender_email,
                fallback_name=sender_name,
            )

            unknown_data = {
                "status":            "UNKNOWN",
                "full_name":         candidate_name,
                "email":             sender_email,
                "phone":             "Not Mentioned",
                "location":          "Not Mentioned",
                "total_experience":  "Not Mentioned",
                "education":         "Not Mentioned",
                "skills":            "Not Mentioned",
                "certifications":    "Not Mentioned",
                "work_experience":   "Not Mentioned",
                "match_score":       "0",
                "key_strengths":     "Not Mentioned",
                "concerns":          "Resume does not match any of the 3 open roles.",
                "rejection_reason":  "Profile does not match BSC Nursing, Technical Staff, or Clerical Role.",
                "selection_reason":  "",
                "role_key":          "UNKNOWN_ROLE",
                "role_display":      "Unknown / Other",
                "sender_email":      sender_email,
                "received_email_subject": subject,
                "original_filename": filename,
                "processed_at":      datetime.now().isoformat(),
                "matched_must_have": [],
                "matched_good_to_have": [],
            }

            unknown_email = build_result_email_content(candidate_name, "UNKNOWN", "UNKNOWN_ROLE")
            unknown_data["sent_to_email"] = sender_email
            unknown_data["sent_from_email"] = EMAIL_ADDR
            unknown_data["sent_email_subject"] = unknown_email["subject"]
            unknown_data["sent_email_plain"] = unknown_email["plain_text"]
            unknown_data["sent_email_html"] = unknown_email["html_body"]

            paths = build_folder_structure("UNKNOWN_ROLE", "rejected", candidate_name)
            with open(paths["resume_path"], "wb") as f:
                f.write(pdf_data)
            save_candidate_info(paths["info_path"], unknown_data)
            print(f"💾 Saved to: {paths['candidate_dir']}")

            send_result_email(
                receiver_email=sender_email,
                candidate_name=candidate_name,
                status="UNKNOWN",
                role_key="UNKNOWN_ROLE",
                sender_email=EMAIL_ADDR,
                sender_password=PASSWORD
            )

            try:
                os.remove(temp_path)
            except Exception:
                pass

            continue

        # ── STEP 5: AI Analysis ──────────────────────────────────
        # (AI sirf fields extract karta hai — score AI se nahi aata)
        print("🤖 Running AI Analysis...")
        candidate_data = analyze_resume(resume_text, role_key)

        # ── STEP 6: Rule-based keyword validation ────────────────
        rule_selected, matched_must, matched_good = check_selection_criteria(
            resume_text, role_key
        )

        # ── STEP 7: FINAL DECISION ───────────────────────────────
        # Ek jagah, clear rules — AI ka status use nahi hota
        final_status = make_final_decision(
            candidate_data  = candidate_data,
            rule_selected   = rule_selected,
            matched_must    = matched_must,
            resume_text     = resume_text,
            role_key        = role_key,
        )

        # candidate_data update karo
        candidate_data["status"]               = final_status
        candidate_data["matched_must_have"]    = matched_must
        candidate_data["matched_good_to_have"] = matched_good
        candidate_data["sender_email"]         = sender_email
        candidate_data["received_email_subject"] = subject
        candidate_data["original_filename"]    = filename
        candidate_data["processed_at"]         = datetime.now().isoformat()

        # Reason bhi update karo final_status ke basis pe
        final_score = int(candidate_data.get("match_score", "0") or "0")
        if final_status == "SELECTED":
            from ai_parser import get_selection_reason
            candidate_data["rejection_reason"] = ""
            candidate_data["selection_reason"] = get_selection_reason(
                candidate_data, role_key, final_score
            )
        else:
            from ai_parser import get_rejection_reason
            candidate_data["selection_reason"] = ""
            candidate_data["rejection_reason"] = get_rejection_reason(
                candidate_data, role_key, final_score
            )

        # ── STEP 8: Build folder & save files ────────────────────
        candidate_name = candidate_data.get("full_name", "Unknown_Candidate")
        if not candidate_name or candidate_name.lower() in ["not mentioned", "unknown"]:
            candidate_name = (
                filename.replace(".pdf", "")
                        .replace("_", " ")
                        .replace("-", " ")
                        .title()
            )

        candidate_name = extract_best_candidate_name(
            resume_text,
            ai_name=candidate_name,
            email=candidate_data.get("email", sender_email),
            fallback_name=sender_name,
        )
        candidate_data["full_name"] = candidate_name

        print(f"\n📊 Result  : {final_status}")
        print(f"   Name   : {candidate_name}")
        print(f"   Score  : {final_score}/100")
        print(f"   Must-Have Matched: {matched_must}")

        outgoing_email = build_result_email_content(candidate_name, final_status, role_key)
        candidate_data["sent_to_email"] = sender_email
        candidate_data["sent_from_email"] = EMAIL_ADDR
        candidate_data["sent_email_subject"] = outgoing_email["subject"]
        candidate_data["sent_email_plain"] = outgoing_email["plain_text"]
        candidate_data["sent_email_html"] = outgoing_email["html_body"]

        paths = build_folder_structure(role_key, final_status, candidate_name)

        with open(paths["resume_path"], "wb") as f:
            f.write(pdf_data)

        save_candidate_info(paths["info_path"], candidate_data)
        print(f"💾 Saved to: {paths['candidate_dir']}")

        # ── STEP 9: Send result email ────────────────────────────
        email_sent = send_result_email(
            receiver_email=sender_email,
            candidate_name=candidate_name,
            status=final_status,
            role_key=role_key,
            rejection_reason=candidate_data.get("rejection_reason", ""),
            selection_reason=candidate_data.get("selection_reason", ""),
            sender_email=EMAIL_ADDR,
            sender_password=PASSWORD
        )

        if email_sent:
            print(f"📧 Notification sent → {sender_email}")
        else:
            print(f"⚠️  Email failed for {sender_email}")

        try:
            os.remove(temp_path)
        except Exception:
            pass

    if not pdf_found:
        print("ℹ️  No PDF attachment found in this email")


# ══════════════════════════════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════════════════════════════

def main():
    print("\n" + "="*60)
    print("🚀 AI HR RECRUITMENT ENGINE STARTED")
    print(f"   Selection threshold : {SELECTION_SCORE_THRESHOLD}/100")
    print(f"   Must-have minimum   : {MUST_HAVE_MIN_MATCH} keywords")
    print("   Monitoring roles:")
    for role_key, role in ROLES.items():
        if role_key != "UNKNOWN_ROLE":
            print(f"   • {role['display_name']}")
    print("   • Unknown/Other → auto-redirect email")
    print("="*60 + "\n")

    mail = connect_mail()
    if not mail:
        print("❌ Cannot start — email connection failed")
        return

    processed_ids = set()

    while True:
        try:
            mail.select("inbox")
            status, messages = mail.search(None, "UNSEEN")

            if status == "OK":
                email_ids = messages[0].split()

                if email_ids:
                    print(f"\n📬 {len(email_ids)} unread email(s) found")

                for email_id in email_ids:
                    process_email(mail, email_id, processed_ids)
            else:
                print("⚠️  Could not search inbox")

            time.sleep(2)

        except KeyboardInterrupt:
            print("\n\n🛑 Engine stopped by user")
            break

        except imaplib.IMAP4.abort:
            print("\n🔄 Connection lost, reconnecting...")
            time.sleep(5)
            mail = connect_mail()

        except Exception as error:
            print(f"\n❌ Runtime Error: {error}")
            print("🔄 Reconnecting in 5 seconds...")
            time.sleep(5)
            mail = connect_mail()


if __name__ == "__main__":
    main()
