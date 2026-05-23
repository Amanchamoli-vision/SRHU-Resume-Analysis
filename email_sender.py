# email_sender.py — Clean HTML email templates
# Score aur reasons sirf dashboard/JSON mein — email mein nahi

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config import ROLES


GENERIC_GREETING_NAMES = {"", "candidate", "applicant", "the candidate", "name", "not mentioned", "unknown"}


def resolve_greeting_name(candidate_name: str) -> str:
    cleaned = str(candidate_name or "").strip()
    return cleaned if cleaned.lower() not in GENERIC_GREETING_NAMES else "Applicant"


def get_selected_html(candidate_name: str, role_display: str) -> str:
    """Selected candidate ka clean email — koi score/reason nahi."""
    greeting_name = resolve_greeting_name(candidate_name)
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ margin: 0; padding: 0; background: #f0f4f8; font-family: 'Segoe UI', Arial, sans-serif; }}
  .wrapper {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
  .header {{ background: linear-gradient(135deg, #1a7a4a 0%, #24a060 100%); padding: 40px 32px; text-align: center; }}
  .header h1 {{ color: #ffffff; margin: 0; font-size: 26px; font-weight: 700; letter-spacing: -0.5px; }}
  .header p {{ color: rgba(255,255,255,0.85); margin: 8px 0 0; font-size: 14px; }}
  .badge {{ display: inline-block; background: #ffffff; color: #1a7a4a; padding: 6px 20px; border-radius: 20px; font-size: 13px; font-weight: 700; margin-top: 16px; letter-spacing: 1px; }}
  .body {{ padding: 36px 32px; }}
  .greeting {{ font-size: 20px; font-weight: 600; color: #1a1a2e; margin-bottom: 16px; }}
  .text {{ font-size: 15px; color: #4a4a6a; line-height: 1.7; margin-bottom: 16px; }}
  .steps {{ background: #fafafa; border-radius: 8px; padding: 20px 24px; margin: 24px 0; }}
  .steps h3 {{ font-size: 14px; font-weight: 700; color: #1a1a2e; margin: 0 0 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .step {{ display: flex; align-items: flex-start; margin-bottom: 10px; font-size: 14px; color: #4a4a6a; }}
  .step-num {{ background: #24a060; color: white; border-radius: 50%; width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; margin-right: 12px; flex-shrink: 0; }}
  .footer {{ background: #f8fafc; padding: 24px 32px; text-align: center; border-top: 1px solid #e8ecf0; }}
  .footer p {{ font-size: 12px; color: #8899aa; margin: 4px 0; }}
  .company {{ font-weight: 700; color: #1a7a4a; font-size: 14px; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>🎉 Congratulations!</h1>
    <p>Your application has been reviewed</p>
    <div class="badge">✓ SHORTLISTED</div>
  </div>
  <div class="body">
    <div class="greeting">Dear {greeting_name},</div>
    <p class="text">
      We are pleased to inform you that after a thorough review of your application
      for the position of <strong>{role_display}</strong>, you have been
      <strong>shortlisted</strong> for the next stage of our selection process.
    </p>
    <div class="steps">
      <h3>Next Steps</h3>
      <div class="step">
        <div class="step-num">1</div>
        Our HR team will reach out to you within <strong>2–3 working days</strong> to schedule your interview.
      </div>
      <div class="step">
        <div class="step-num">2</div>
        Please keep your phone reachable and check your email regularly.
      </div>
      <div class="step">
        <div class="step-num">3</div>
        Keep your original documents ready for verification.
      </div>
    </div>
    <p class="text">We look forward to speaking with you soon. Thank you for your interest in joining our organization.</p>
    <p class="text">Warm regards,<br><strong>HR Recruitment Team</strong></p>
  </div>
  <div class="footer">
    <p class="company">HR Recruitment Platform</p>
    <p>This is an automated message. Please do not reply directly to this email.</p>
  </div>
</div>
</body>
</html>
"""


def get_rejected_html(candidate_name: str, role_display: str) -> str:
    """Rejected candidate ka clean email — koi score/reason nahi."""
    greeting_name = resolve_greeting_name(candidate_name)
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ margin: 0; padding: 0; background: #f0f4f8; font-family: 'Segoe UI', Arial, sans-serif; }}
  .wrapper {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
  .header {{ background: linear-gradient(135deg, #2d3748 0%, #4a5568 100%); padding: 40px 32px; text-align: center; }}
  .header h1 {{ color: #ffffff; margin: 0; font-size: 26px; font-weight: 700; }}
  .header p {{ color: rgba(255,255,255,0.75); margin: 8px 0 0; font-size: 14px; }}
  .body {{ padding: 36px 32px; }}
  .greeting {{ font-size: 20px; font-weight: 600; color: #1a1a2e; margin-bottom: 16px; }}
  .text {{ font-size: 15px; color: #4a4a6a; line-height: 1.7; margin-bottom: 16px; }}
  .encouragement {{ background: #fffbf0; border-radius: 8px; padding: 20px; margin: 24px 0; text-align: center; }}
  .encouragement p {{ font-size: 14px; color: #744210; margin: 0; line-height: 1.7; }}
  .footer {{ background: #f8fafc; padding: 24px 32px; text-align: center; border-top: 1px solid #e8ecf0; }}
  .footer p {{ font-size: 12px; color: #8899aa; margin: 4px 0; }}
  .company {{ font-weight: 700; color: #4a5568; font-size: 14px; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Application Update</h1>
    <p>Thank you for applying — {role_display}</p>
  </div>
  <div class="body">
    <div class="greeting">Dear {greeting_name},</div>
    <p class="text">
      Thank you for taking the time to apply for the position of
      <strong>{role_display}</strong> with us. We truly appreciate your interest
      in our organization.
    </p>
    <p class="text">
      After carefully reviewing your application, we regret to inform you that
      we will not be moving forward with your candidacy at this time.
    </p>
    <div class="encouragement">
      <p>💪 This decision does not diminish your potential. We encourage you to
      continue developing your skills and to apply for future opportunities
      that may be a better match.</p>
    </div>
    <p class="text">We wish you the very best in your career journey and thank you once again for considering us as a potential employer.</p>
    <p class="text">Best regards,<br><strong>AI HR Recruitment Team</strong></p>
  </div>
  <div class="footer">
    <p class="company">HR Recruitment Platform</p>
    <p>This is an automated message. Please do not reply directly to this email.</p>
  </div>
</div>
</body>
</html>
"""


def get_unknown_role_html(candidate_name: str) -> str:
    """Unknown role ka email — candidate ko batao ki konse roles open hain."""
    greeting_name = resolve_greeting_name(candidate_name)
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {{ margin: 0; padding: 0; background: #f0f4f8; font-family: 'Segoe UI', Arial, sans-serif; }}
  .wrapper {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
  .header {{ background: linear-gradient(135deg, #553c9a 0%, #7c3aed 100%); padding: 40px 32px; text-align: center; }}
  .header h1 {{ color: #ffffff; margin: 0; font-size: 26px; font-weight: 700; }}
  .header p {{ color: rgba(255,255,255,0.80); margin: 8px 0 0; font-size: 14px; }}
  .body {{ padding: 36px 32px; }}
  .greeting {{ font-size: 20px; font-weight: 600; color: #1a1a2e; margin-bottom: 16px; }}
  .text {{ font-size: 15px; color: #4a4a6a; line-height: 1.7; margin-bottom: 16px; }}
  .info-box {{ background: #ede9fe; border-left: 4px solid #7c3aed; border-radius: 0 8px 8px 0; padding: 16px 20px; margin: 20px 0; }}
  .info-box p {{ margin: 0; font-size: 14px; color: #4c1d95; line-height: 1.7; font-weight: 500; }}
  .roles-box {{ background: #fafafa; border-radius: 10px; padding: 20px 24px; margin: 24px 0; border: 1px solid #e5e7eb; }}
  .roles-box h3 {{ font-size: 13px; font-weight: 700; color: #6b7280; margin: 0 0 14px; text-transform: uppercase; letter-spacing: 0.8px; }}
  .role-item {{ font-size: 14px; color: #1f2937; margin-bottom: 10px; padding: 10px 14px; background: white; border-radius: 8px; border: 1px solid #e5e7eb; }}
  .role-item span {{ font-weight: 600; }}
  .role-sub {{ font-size: 12px; color: #9ca3af; margin-top: 2px; }}
  .footer {{ background: #f8fafc; padding: 24px 32px; text-align: center; border-top: 1px solid #e8ecf0; }}
  .footer p {{ font-size: 12px; color: #8899aa; margin: 4px 0; }}
  .company {{ font-weight: 700; color: #7c3aed; font-size: 14px; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Application Received</h1>
    <p>Thank you for reaching out to us</p>
  </div>
  <div class="body">
    <div class="greeting">Dear {greeting_name},</div>
    <p class="text">
      Thank you for sending us your resume. We appreciate your interest
      in our organization and the time you took to apply.
    </p>
    <div class="info-box">
      <p>ℹ️ After reviewing your application, we found that your profile does not
      match any of our <strong>currently open positions</strong>. We are actively
      hiring only for the roles listed below.</p>
    </div>
    <div class="roles-box">
      <h3>Currently Open Positions</h3>
      <div class="role-item">
        🏥 <span>BSC Nursing</span>
        <div class="role-sub">Clinical nursing, patient care, ICU, OT, GNM/ANM graduates</div>
      </div>
      <div class="role-item">
        💻 <span>Technical Staff</span>
        <div class="role-sub">Software development, IT, engineering, data science roles</div>
      </div>
      <div class="role-item">
        📋 <span>Clerical Role</span>
        <div class="role-sub">Admin, data entry, MS Office, receptionist, back office</div>
      </div>
    </div>
    <p class="text">
      If your qualifications align with any of the above roles, we warmly encourage
      you to apply again with a resume tailored to that specific position.
    </p>
    <p class="text">We wish you the very best in your job search and career ahead.</p>
    <p class="text">Best regards,<br><strong>AI HR Recruitment Team</strong></p>
  </div>
  <div class="footer">
    <p class="company">HR Recruitment Platform</p>
    <p>This is an automated message. Please do not reply directly to this email.</p>
  </div>
</div>
</body>
</html>
"""


def build_result_email_content(candidate_name: str, status: str, role_key: str) -> dict:
    """Build the outgoing email content for a candidate."""
    role_config = ROLES[role_key]
    role_display = role_config["display_name"]
    greeting_name = resolve_greeting_name(candidate_name)

    if role_key == "UNKNOWN_ROLE":
        subject = "Application Update – No Matching Position Found"
        html_body = get_unknown_role_html(candidate_name)
        plain_text = (
            f"Dear {greeting_name},\n\n"
            f"Thank you for applying. Unfortunately, your profile does not match "
            f"any of our currently open positions.\n\n"
            f"We are currently hiring for:\n"
            f"  • BSC Nursing\n"
            f"  • Technical Staff\n"
            f"  • Clerical Role\n\n"
            f"Please apply again if your profile matches any of the above.\n\n"
            f"Best regards,\nAI HR Recruitment Team"
        )
    elif status == "SELECTED":
        subject = role_config["email_subject_selected"]
        html_body = get_selected_html(candidate_name, role_display)
        plain_text = (
            f"Dear {greeting_name},\n\n"
            f"Congratulations! Your application for {role_display} has been reviewed "
            f"and you have been shortlisted.\n\n"
            f"Our HR team will contact you within 2-3 working days.\n\n"
            f"Best regards,\nAI HR Recruitment Team"
        )
    else:
        subject = role_config["email_subject_rejected"]
        html_body = get_rejected_html(candidate_name, role_display)
        plain_text = (
            f"Dear {greeting_name},\n\n"
            f"Thank you for applying for {role_display}. After reviewing your "
            f"application, we regret that we will not be moving forward at this time.\n\n"
            f"We wish you the best in your career.\n\n"
            f"Best regards,\nAI HR Recruitment Team"
        )

    return {
        "subject": subject,
        "html_body": html_body,
        "plain_text": plain_text,
        "role_display": role_display,
    }


def send_result_email(
    receiver_email: str,
    candidate_name: str,
    status: str,
    role_key: str,
    rejection_reason: str = "",    # sirf JSON/dashboard ke liye — email mein nahi jaata
    selection_reason: str = "",    # sirf JSON/dashboard ke liye — email mein nahi jaata
    sender_email: str = None,
    sender_password: str = None
) -> bool:
    try:
        email_content = build_result_email_content(candidate_name, status, role_key)
        subject = email_content["subject"]
        html_body = email_content["html_body"]
        plain_text = email_content["plain_text"]
        role_display = email_content["role_display"]
        greeting_line = plain_text.splitlines()[0] if plain_text else "Greeting unavailable"

        print(f"   ✉️ Email greeting: {greeting_line}")

        # ── Send email ───────────────────────────────────────────
        msg = MIMEMultipart("alternative")
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        print(f"   ✅ Email sent → {receiver_email} | Status: {status} | Role: {role_display}")
        return True

    except Exception as error:
        print(f"   ❌ Email Error: {error}")
        return False
