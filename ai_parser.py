# ai_parser.py — Simple resume analyzer for local Ollama models

import ollama
import re
from config import ROLES


GENERIC_NAME_VALUES = {
    "", "not mentioned", "n/a", "na", "none", "-", "unknown", "candidate",
    "applicant", "the candidate", "name"
}

SELECTION_SCORE_THRESHOLD = 60
MAX_NAME_WORDS = 5
MAX_NAME_LENGTH = 40
HEADER_SCAN_LINES = 20
DETAIL_SCAN_LINES = 40
MIN_ACCEPT_SCORE = 35
MIN_WIN_MARGIN = 4
MAX_CANDIDATE_CHARS_PER_LINE = 80
SECTION_HEADER_PHRASES = {
    "work experience": "experience",
    "professional experience": "experience",
    "experience": "experience",
    "employment history": "experience",
    "career history": "experience",
    "education": "education",
    "academic background": "education",
    "projects": "projects",
    "project": "projects",
    "skills": "skills",
    "technical skills": "skills",
    "key skills": "skills",
    "summary": "summary",
    "professional summary": "summary",
    "profile": "summary",
    "objective": "summary",
    "certifications": "certifications",
    "certification": "certifications",
    "achievements": "achievements",
    "personal details": "details",
    "contact": "details",
}
ROLE_TITLE_TOKENS = {
    "engineer", "developer", "analyst", "intern", "manager", "scientist",
    "consultant", "specialist", "programmer", "designer", "architect",
    "executive", "associate", "officer", "administrator", "coordinator",
    "researcher", "fellow", "lecturer", "professor", "teacher", "clerk",
    "assistant", "nurse", "recruiter", "lead", "director", "head"
}
ROLE_TITLE_PHRASES = {
    "machine learning engineer",
    "software engineer",
    "data analyst",
    "data scientist",
    "full stack developer",
    "frontend developer",
    "backend developer",
    "remote internship",
    "software developer",
    "research intern",
}
SECTION_TOKENS = {
    "experience", "skills", "projects", "education", "summary", "profile",
    "objective", "certifications", "contact", "details", "achievements",
    "professional", "employment", "history", "technologies", "work"
}
TECH_TOKENS = {
    "aws", "azure", "gcp", "flask", "django", "mongodb", "mysql", "postgresql",
    "tensorflow", "pytorch", "react", "node", "nodejs", "javascript", "python",
    "java", "nlp", "llm", "docker", "kubernetes", "machine", "learning",
    "software", "data", "science", "ai", "frontend", "backend", "fullstack",
    "devops", "android", "ios", "cloud", "api", "sql"
}
TECH_PHRASES = {
    "machine learning",
    "data science",
    "artificial intelligence",
    "deep learning",
    "software development",
    "web development",
    "cloud computing",
}
COMPANY_TOKENS = {
    "tech", "technologies", "technology", "labs", "lab", "solutions", "systems",
    "services", "soft", "software", "consulting", "consultancy", "pvt", "ltd",
    "llp", "inc", "corp", "company", "group", "studio", "media", "digital",
    "ventures", "works", "global", "international"
}
COMPANY_SUFFIX_PATTERNS = (
    "tech", "labs", "lab", "solutions", "systems", "services", "consulting",
    "consultancy", "software", "digital", "media", "global", "ventures", "works",
    "group", "studio", "pvt", "ltd", "llp", "inc", "corp",
)
RESUME_LABEL_TOKENS = {
    "resume", "curriculum", "vitae", "email", "phone", "mobile", "contact",
    "address", "linkedin", "github", "candidate", "name"
}
RESUME_LABEL_PHRASES = {
    "curriculum vitae",
    "resume of",
    "candidate name",
    "personal details",
    "professional summary",
    "work experience",
    "professional experience",
}
NAME_STOP_TOKENS = (
    ROLE_TITLE_TOKENS
    | SECTION_TOKENS
    | TECH_TOKENS
    | COMPANY_TOKENS
    | RESUME_LABEL_TOKENS
    | {"with", "for", "at", "on", "in", "remote", "internship", "intern", "of"}
)


def build_prompt(resume_text: str, role_key: str) -> str:
    role = ROLES[role_key]
    must_have = role["selection_criteria"]["must_have"]
    must_have_str = ", ".join(must_have)

    prompt = f"""Extract information from this resume and return ONLY the fields below. No extra text.

STATUS: SELECTED or REJECTED (SELECTED if candidate fits {role['display_name']} role)
Full Name: \nEmail: \nPhone: \nLocation: \nExperience: \nEducation: \nSkills: \nMatch Score: (0-100)\nKey Strengths: \nConcerns: \n
RESUME:
{resume_text[:2000]}

Selection Rule: Candidate should be SELECTED only if their resume clearly matches the {role['display_name']} role.
Must have at least some of these keywords to be SELECTED: {must_have_str}
Fill every field. Write "Not Mentioned" only if truly not found.
IMPORTANT: STATUS must be either SELECTED or REJECTED — never "Not Mentioned".
IMPORTANT: Match Score must be a number from 0 to 100 — never "Not Mentioned".
IMPORTANT: Full Name must be the candidate's real name exactly as it appears on the resume header.
IMPORTANT: Do not invent placeholder names. Do not return "Candidate", "Applicant", or email text as Full Name unless that is literally the only name visible."""

    return prompt


def build_name_extraction_prompt(resume_text: str) -> str:
    header_excerpt = get_resume_header_excerpt(resume_text, max_lines=HEADER_SCAN_LINES)
    return f"""Read this resume text and return ONLY the candidate's full name.

Rules:
- Output only the person's full name.
- Prefer the name shown in the top/header section of the resume.
- Ignore role titles, company names, section headings, and technology terms.
- Do not return labels like Name, Candidate, Applicant, Resume, CV, Email, Phone.
- Do not return any explanation or extra words.
- If no reliable full name is visible, return exactly: Not Mentioned

HEADER:
{header_excerpt}

RESUME:
{resume_text[:1500]}"""


def build_name_selection_prompt(resume_text: str, shortlist: list[str]) -> str:
    header_excerpt = get_resume_header_excerpt(resume_text, max_lines=HEADER_SCAN_LINES)
    candidate_lines = "\n".join(f"- {candidate}" for candidate in shortlist)
    return f"""Choose the candidate's real full name from this shortlist.

Rules:
- Return ONLY one exact candidate from the shortlist.
- Prefer a human name found near the top header or contact block.
- Reject company names, role titles, section headings, and technologies.
- If none is reliable, return exactly: Not Mentioned

HEADER:
{header_excerpt}

SHORTLIST:
{candidate_lines}
"""


def get_resume_header_excerpt(resume_text: str, max_lines: int = 12) -> str:
    lines = [line.strip() for line in str(resume_text or "").splitlines() if line.strip()]
    return "\n".join(lines[:max_lines])


def normalize_name(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    return text.strip(" ,:-")


def split_compound_name(text: str) -> str:
    value = normalize_name(text)
    if not value:
        return ""

    value = re.sub(r"([a-z])([A-Z])", r"\1 \2", value)
    value = re.sub(r"[_\-./]+", " ", value)
    value = re.sub(r"\d+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def canonical_token(token: str) -> str:
    return re.sub(r"[^a-z]", "", token.lower())


def tokenize_alpha_words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:['.-][A-Za-z]+)?", str(text or ""))


def normalize_line_text(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9 ]", " ", str(text or "").lower())
    return re.sub(r"\s+", " ", normalized).strip()


def contains_phrase(text: str, phrases: set[str]) -> bool:
    normalized = normalize_line_text(text)
    return any(phrase in normalized for phrase in phrases)


def looks_like_url(text: str) -> bool:
    return bool(re.search(r"(https?://|www\.|linkedin\.com|github\.com)", str(text or ""), flags=re.IGNORECASE))


def looks_like_email(text: str) -> bool:
    return bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", str(text or "")))


def looks_like_phone(text: str) -> bool:
    return bool(re.search(r"(\+?\d[\d\s\-()]{7,}\d)", str(text or "")))


def looks_like_date(text: str) -> bool:
    return bool(re.search(r"\b(?:19|20)\d{2}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", str(text or "")))


def is_all_caps_label(line: str) -> bool:
    cleaned = re.sub(r"[^A-Za-z ]", " ", str(line or "")).strip()
    if not cleaned:
        return False
    words = cleaned.split()
    if not words or len(words) > 4:
        return False
    return cleaned.upper() == cleaned and any(canonical_token(word) in SECTION_TOKENS for word in words)


def detect_section_name(line: str) -> str:
    lowered = re.sub(r"[^a-z ]", " ", str(line or "").lower())
    lowered = re.sub(r"\s+", " ", lowered).strip()
    if not lowered:
        return ""
    for phrase, section_name in SECTION_HEADER_PHRASES.items():
        if lowered == phrase or lowered.startswith(f"{phrase} "):
            return section_name
    if is_all_caps_label(line):
        return "section"
    return ""


def is_probable_company_token(token: str) -> bool:
    lowered = canonical_token(token)
    if not lowered:
        return False
    if lowered in COMPANY_TOKENS:
        return True
    return any(lowered.endswith(suffix) for suffix in COMPANY_TOKENS)


def looks_like_company_name(text: str) -> bool:
    words = tokenize_alpha_words(text)
    if not words:
        return False
    lowered_words = [canonical_token(word) for word in words]
    if any(word in COMPANY_TOKENS for word in lowered_words):
        return True
    normalized = normalize_line_text(text)
    if any(normalized.endswith(suffix) or f" {suffix}" in normalized for suffix in COMPANY_SUFFIX_PATTERNS):
        return True
    if len(words) == 1:
        token = words[0]
        if re.search(r"[a-z][A-Z]", token):
            return True
        if is_probable_company_token(token):
            return True
    return False


def has_excessive_punctuation(text: str) -> bool:
    cleaned = str(text or "")
    punctuation_count = len(re.findall(r"[^A-Za-z0-9\s]", cleaned))
    return punctuation_count >= 4


def line_has_resume_noise(text: str) -> bool:
    normalized = normalize_line_text(text)
    if not normalized:
        return False
    if contains_phrase(normalized, RESUME_LABEL_PHRASES):
        return True
    if contains_phrase(normalized, ROLE_TITLE_PHRASES):
        return True
    if contains_phrase(normalized, TECH_PHRASES):
        return True
    return False


def is_human_name_token(token: str) -> bool:
    stripped = token.replace(".", "").replace("-", "").replace("'", "")
    return stripped.isalpha() and 1 <= len(stripped) <= 20


def is_human_style_name(text: str) -> bool:
    words = tokenize_alpha_words(text)
    if not (2 <= len(words) <= MAX_NAME_WORDS):
        return False
    if not all(is_human_name_token(word) for word in words):
        return False
    if sum(1 for word in words if len(word) == 1) > 2:
        return False
    return True


def clean_candidate_text(text: str) -> str:
    value = split_compound_name(text)
    return " ".join(token.strip(" .") for token in value.split() if token.strip(" ."))


def candidate_precedes_section_marker(line_text: str, candidate_text: str) -> bool:
    line_clean = clean_candidate_text(line_text).lower()
    candidate_clean = clean_candidate_text(candidate_text).lower()
    if not line_clean or not candidate_clean or not line_clean.startswith(candidate_clean):
        return False
    remainder = line_clean[len(candidate_clean):].strip(" -:|")
    if not remainder:
        return False
    return bool(detect_section_name(remainder))


def is_valid_name(name: str) -> bool:
    candidate = clean_candidate_text(name)
    if candidate.lower() in GENERIC_NAME_VALUES:
        return False
    if not candidate or len(candidate) > MAX_NAME_LENGTH:
        return False
    if looks_like_url(candidate) or looks_like_email(candidate) or looks_like_phone(candidate) or looks_like_date(candidate):
        return False
    if not is_human_style_name(candidate):
        return False
    tokens = [canonical_token(word) for word in tokenize_alpha_words(candidate)]
    if any(token in ROLE_TITLE_TOKENS for token in tokens):
        return False
    if any(token in SECTION_TOKENS for token in tokens):
        return False
    if any(token in TECH_TOKENS for token in tokens):
        return False
    if any(token in RESUME_LABEL_TOKENS for token in tokens):
        return False
    if looks_like_company_name(candidate):
        return False
    if len(candidate) < 4:
        return False
    return True


def title_name(name: str) -> str:
    normalized = clean_candidate_text(name)
    parts = []
    for part in normalized.split():
        parts.append(part.upper() if len(part) == 1 else part.capitalize())
    return " ".join(parts)


def extract_prefix_candidate(words: list[str]) -> str:
    prefix = []
    for word in words:
        token = canonical_token(word)
        if not token or token in NAME_STOP_TOKENS:
            break
        prefix.append(word)
        if len(prefix) >= MAX_NAME_WORDS:
            break
    if len(prefix) >= 2:
        return " ".join(prefix)
    return ""


def extract_name_candidates_from_line(line: str) -> list[str]:
    if not line:
        return []
    if len(str(line)) > MAX_CANDIDATE_CHARS_PER_LINE and not re.search(r"(?:candidate\s+name|name)\s*[:\-]", line, flags=re.IGNORECASE):
        return []

    candidates = set()
    name_match = re.search(r"(?:candidate\s+name|name)\s*[:\-]\s*([A-Za-z .'-]+)", line, flags=re.IGNORECASE)
    if name_match:
        labeled_name = clean_candidate_text(name_match.group(1))
        if labeled_name:
            candidates.add(labeled_name)

    segments = re.split(r"[|,;/()\[\]{}]+", str(line))
    for segment in segments:
        if looks_like_url(segment) or looks_like_email(segment) or looks_like_phone(segment):
            continue
        words = tokenize_alpha_words(segment)
        if len(words) == 1 and len(words[0]) > 3:
            candidates.add(clean_candidate_text(words[0]))
        if len(words) < 2:
            continue
        prefix_candidate = extract_prefix_candidate(words)
        if prefix_candidate:
            candidates.add(clean_candidate_text(prefix_candidate))
        full_candidate = clean_candidate_text(" ".join(words[:MAX_NAME_WORDS]))
        if full_candidate:
            candidates.add(full_candidate)

    return [candidate for candidate in candidates if candidate]


def find_contact_line_indexes(lines: list[str]) -> list[int]:
    indexes = []
    for index, line in enumerate(lines):
        lowered = str(line or "").lower()
        if looks_like_email(line) or looks_like_phone(line) or "linkedin" in lowered or "github" in lowered:
            indexes.append(index)
    return indexes


def nearest_contact_distance(line_index: int, contact_indexes: list[int]) -> int | None:
    if not contact_indexes:
        return None
    return min(abs(line_index - contact_index) for contact_index in contact_indexes)


def score_name_candidate(candidate: str, line_index: int, line_text: str, section_name: str, contact_distance: int | None, first_section_index: int | None) -> float:
    score = 0.0
    words = tokenize_alpha_words(candidate)
    raw_line = str(line_text or "")

    if line_index < HEADER_SCAN_LINES:
        score += max(0, 18 - line_index)
    if first_section_index is not None and line_index < first_section_index:
        score += 10
    elif first_section_index is None and line_index < 5:
        score += 6
    if 2 <= len(words) <= 4:
        score += 12
    elif len(words) == 5:
        score += 6
    if raw_line.isupper():
        score += 6
    elif raw_line == raw_line.title():
        score += 4
    if contact_distance is not None:
        if contact_distance <= 1:
            score += 8
        elif contact_distance <= 3:
            score += 4
    if candidate_precedes_section_marker(raw_line, candidate):
        score += 10
    if section_name and section_name != "header":
        score -= 12
    if line_has_resume_noise(raw_line):
        score -= 18
    if any(canonical_token(word) in COMPANY_TOKENS for word in tokenize_alpha_words(raw_line)):
        score -= 10
    if any(canonical_token(word) in ROLE_TITLE_TOKENS for word in tokenize_alpha_words(raw_line)):
        score -= 12
    if looks_like_company_name(candidate):
        score -= 18
    if len(candidate) > 28:
        score -= 6
    return score


def normalize_confidence(raw_score: float) -> float:
    confidence = raw_score / 60.0
    return round(max(0.0, min(0.99, confidence)), 2)


def build_candidate_record(text: str, source: str, line_index: int | None = None, line_text: str = "", section_name: str = "header", contact_distance: int | None = None, first_section_index: int | None = None) -> dict:
    cleaned_text = clean_candidate_text(text)
    lowered_line = str(line_text or "").lower()
    candidate_before_section = candidate_precedes_section_marker(line_text, cleaned_text)
    rejection_reasons = []

    if not cleaned_text:
        rejection_reasons.append("empty")
    if cleaned_text and len(cleaned_text) > MAX_NAME_LENGTH:
        rejection_reasons.append("too_long")
    if looks_like_url(text) or looks_like_url(cleaned_text):
        rejection_reasons.append("url")
    if looks_like_email(text) or looks_like_email(cleaned_text):
        rejection_reasons.append("email")
    if looks_like_phone(text) or looks_like_phone(cleaned_text):
        rejection_reasons.append("phone")
    if looks_like_date(text) or looks_like_date(cleaned_text):
        rejection_reasons.append("date")
    if has_excessive_punctuation(text):
        rejection_reasons.append("excessive_punctuation")
    if source == "header_line" and is_all_caps_label(text) and not candidate_before_section:
        rejection_reasons.append("section_header")
    if section_name and section_name != "header" and not candidate_before_section:
        rejection_reasons.append(f"section_{section_name}")
    if line_has_resume_noise(line_text or text) and not candidate_before_section:
        rejection_reasons.append("resume_noise")

    tokens = [canonical_token(word) for word in tokenize_alpha_words(cleaned_text)]
    if tokens:
        if any(token in ROLE_TITLE_TOKENS for token in tokens):
            rejection_reasons.append("role_title")
        if any(token in SECTION_TOKENS for token in tokens):
            rejection_reasons.append("section_header")
        if any(token in TECH_TOKENS for token in tokens):
            rejection_reasons.append("tech_keyword")
        if any(token in RESUME_LABEL_TOKENS for token in tokens):
            rejection_reasons.append("resume_label")
        if any(is_probable_company_token(token) for token in tokens) or looks_like_company_name(cleaned_text):
            rejection_reasons.append("company_name")
        if len(tokens) < 2 or len(tokens) > MAX_NAME_WORDS:
            rejection_reasons.append("name_length")

    if any(keyword in lowered_line for keyword in ("work experience", "professional experience", "skills", "projects", "education")) and not candidate_before_section:
        rejection_reasons.append("section_context")
    if any(keyword in lowered_line for keyword in ("engineer", "developer", "analyst", "intern")):
        rejection_reasons.append("role_context")
    if len(cleaned_text.split()) == 1:
        rejection_reasons.append("single_token")

    accepted = not rejection_reasons and is_valid_name(cleaned_text)
    raw_score = score_name_candidate(cleaned_text, line_index or 0, line_text or cleaned_text, section_name, contact_distance, first_section_index) if accepted else 0.0

    return {
        "text": title_name(cleaned_text) if cleaned_text else "",
        "normalized_text": title_name(cleaned_text) if cleaned_text else "",
        "source": source,
        "line_index": line_index,
        "section": section_name,
        "raw_score": round(raw_score, 2),
        "score": normalize_confidence(raw_score),
        "accepted": accepted,
        "rejected": rejection_reasons[0] if rejection_reasons else "",
        "rejection_reasons": sorted(set(rejection_reasons)),
    }


def aggregate_candidate_records(records: list[dict]) -> list[dict]:
    aggregated = {}
    for record in records:
        key = record["normalized_text"] or record["text"]
        if not key:
            continue
        current = aggregated.get(key)
        if current is None or record["raw_score"] > current["raw_score"]:
            aggregated[key] = dict(record)
            aggregated[key]["sources"] = [record["source"]]
            current = aggregated[key]
        else:
            current["sources"] = sorted(set(current.get("sources", []) + [record["source"]]))
            current["rejection_reasons"] = sorted(set(current.get("rejection_reasons", []) + record.get("rejection_reasons", [])))
            if not current["accepted"] and record["accepted"]:
                current["accepted"] = True
                current["rejected"] = ""
    return sorted(
        aggregated.values(),
        key=lambda item: (-item["raw_score"], item["line_index"] if item["line_index"] is not None else 999, item["text"]),
    )


def generate_name_candidate_rankings(resume_text: str, ai_name: str = "", email: str = "", fallback_name: str = "") -> list[dict]:
    lines = [line.strip() for line in str(resume_text or "").splitlines() if line.strip()]
    contact_indexes = find_contact_line_indexes(lines[:DETAIL_SCAN_LINES])
    raw_records = []
    current_section = "header"
    first_section_index = None

    for line_index, line in enumerate(lines[:DETAIL_SCAN_LINES]):
        line_candidates = extract_name_candidates_from_line(line)
        has_header_prefix_name = any(
            candidate_precedes_section_marker(line, candidate)
            for candidate in line_candidates
        )
        section_name = "" if has_header_prefix_name else detect_section_name(line)
        if section_name:
            current_section = section_name
            if first_section_index is None:
                first_section_index = line_index

        if first_section_index is not None and line_index >= first_section_index:
            line_section = current_section
        else:
            line_section = "header"
        for candidate in line_candidates:
            raw_records.append(
                build_candidate_record(
                    candidate,
                    source="header_line",
                    line_index=line_index,
                    line_text=line,
                    section_name=line_section,
                    contact_distance=nearest_contact_distance(line_index, contact_indexes),
                    first_section_index=first_section_index,
                )
            )

    if ai_name:
        raw_records.append(build_candidate_record(ai_name, source="ai_name"))
    link_name = extract_name_from_links(resume_text)
    if link_name:
        raw_records.append(build_candidate_record(link_name, source="profile_link"))

    return aggregate_candidate_records(raw_records)


def infer_name_from_email(email: str) -> str:
    if not email or "@" not in email:
        return ""
    local_part = email.split("@", 1)[0]
    cleaned = re.sub(r"[._\-+]+", " ", local_part)
    cleaned = re.sub(r"\d+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return ""
    guessed_name = title_name(cleaned)
    return guessed_name if is_valid_name(guessed_name) else ""


def extract_name_from_links(resume_text: str) -> str:
    patterns = [
        r"linkedin\.com/in/([A-Za-z0-9._\-]+)",
        r"github\.com/([A-Za-z0-9._\-]+)",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, resume_text, flags=re.IGNORECASE)
        for match in matches:
            candidate = title_name(match)
            if is_valid_name(candidate):
                return candidate
    return ""


def extract_name_from_resume_header(resume_text: str) -> str:
    rankings = generate_name_candidate_rankings(resume_text)
    for candidate in rankings:
        if candidate["accepted"] and candidate["source"] == "header_line" and (candidate["line_index"] or 0) < HEADER_SCAN_LINES:
            return candidate["text"]
    return ""


def select_name_with_llm(resume_text: str, shortlist: list[str]) -> str:
    if not shortlist:
        return ""
    try:
        response = ollama.chat(
            model="qwen3:8b",
            messages=[{"role": "user", "content": build_name_selection_prompt(resume_text, shortlist)}],
            options={"num_predict": 20, "temperature": 0}
        )
        selected = title_name(normalize_name(response["message"]["content"].strip().replace('"', "").replace("'", "")))
        valid_shortlist = {title_name(candidate) for candidate in shortlist}
        if selected in valid_shortlist and is_valid_name(selected):
            return selected
    except Exception as error:
        print(f"   Name selection LLM failed: {error}")
    return ""


def extract_name_with_llm(resume_text: str, shortlist: list[str] | None = None) -> str:
    if not resume_text or not resume_text.strip():
        return ""

    shortlist = shortlist or []
    selected_from_shortlist = select_name_with_llm(resume_text, shortlist)
    if selected_from_shortlist:
        return selected_from_shortlist

    try:
        response = ollama.chat(
            # model="phi3",
            model="qwen3:8b",
            messages=[{"role": "user", "content": build_name_extraction_prompt(resume_text)}],
            options={"num_predict": 40, "temperature": 0}
        )
        raw_name = response["message"]["content"].strip()
        cleaned_name = normalize_name(raw_name.replace('"', "").replace("'", ""))
        if is_valid_name(cleaned_name):
            return title_name(cleaned_name)
    except Exception as error:
        print(f"   Name extraction LLM failed: {error}")

    return ""


def extract_best_candidate_name_debug(
    resume_text: str,
    ai_name: str = "",
    email: str = "",
    fallback_name: str = "",
) -> dict:
    candidate_rankings = generate_name_candidate_rankings(
        resume_text,
        ai_name=ai_name,
        email=email,
        fallback_name=fallback_name,
    )
    shortlist = [candidate["text"] for candidate in candidate_rankings if candidate["accepted"]][:5]
    llm_name = extract_name_with_llm(resume_text, shortlist=shortlist)

    selected_name = ""
    confidence = 0.0
    rejection_reasons = []

    if llm_name and is_valid_name(llm_name):
        selected_name = title_name(llm_name)
        for candidate in candidate_rankings:
            if candidate["text"] == selected_name:
                candidate["source"] = "llm_shortlist"
                candidate["accepted"] = True
                confidence = max(candidate["score"], 0.75)
                break
        else:
            confidence = 0.75
    else:
        accepted_candidates = [candidate for candidate in candidate_rankings if candidate["accepted"]]
        if accepted_candidates:
            best_candidate = accepted_candidates[0]
            second_candidate = accepted_candidates[1] if len(accepted_candidates) > 1 else None
            margin_ok = second_candidate is None or (best_candidate["raw_score"] - second_candidate["raw_score"]) >= MIN_WIN_MARGIN
            if best_candidate["raw_score"] >= MIN_ACCEPT_SCORE and margin_ok:
                selected_name = best_candidate["text"]
                confidence = best_candidate["score"]
            else:
                rejection_reasons.append("low_confidence")
        else:
            rejection_reasons.append("no_reliable_name_candidate")

    if not selected_name:
        top_rejections = [candidate["rejected"] for candidate in candidate_rankings if candidate["rejected"]]
        rejection_reasons.extend(reason for reason in top_rejections[:5] if reason)
        selected_name = "Candidate"

    return {
        "selected_name": selected_name,
        "confidence": round(confidence, 2),
        "confidence_score": round(confidence, 2),
        "rejection_reasons": sorted(set(rejection_reasons)),
        "top_candidates": candidate_rankings[:8],
        "candidate_rankings": candidate_rankings[:8],
    }


def extract_best_candidate_name(
    resume_text: str,
    ai_name: str = "",
    email: str = "",
    fallback_name: str = "",
) -> str:
    result = extract_best_candidate_name_debug(
        resume_text,
        ai_name=ai_name,
        email=email,
        fallback_name=fallback_name,
    )
    return result["selected_name"]


def calculate_score_from_resume(resume_text: str, role_key: str) -> int:
    """Calculate match score from resume keywords."""
    role = ROLES[role_key]
    resume_lower = resume_text.lower()

    must_have     = role["selection_criteria"]["must_have"]
    good_to_have  = role["selection_criteria"]["good_to_have"]
    required_skills  = role["required_skills"]
    preferred_skills = role["preferred_skills"]

    score = 0

    # Must-have: 15 points each (max 45)
    must_matched = [kw for kw in must_have if kw.lower() in resume_lower]
    score += min(len(must_matched) * 15, 45)

    # Good-to-have: 10 points each (max 20)
    good_matched = [kw for kw in good_to_have if kw.lower() in resume_lower]
    score += min(len(good_matched) * 10, 20)

    # Required skills: 5 points each (max 25)
    req_matched = [s for s in required_skills if s.lower() in resume_lower]
    score += min(len(req_matched) * 5, 25)

    # Preferred skills: 2 points each (max 10)
    pref_matched = [s for s in preferred_skills if s.lower() in resume_lower]
    score += min(len(pref_matched) * 2, 10)

    return min(score, 100)


def get_selection_reason(candidate_data: dict, role_key: str, score: int) -> str:
    """Generate professional selection reason based on candidate data."""
    role = ROLES[role_key]
    role_name = role["display_name"]
    name = candidate_data.get("full_name", "The candidate")
    strengths = candidate_data.get("key_strengths", "")
    education = candidate_data.get("education", "")
    experience = candidate_data.get("total_experience", "")

    reason_parts = []

    reason_parts.append(
        f"After a thorough evaluation of the submitted resume, {name} has demonstrated "
        f"a strong alignment with the requirements of the {role_name} position, achieving "
        f"a match score of {score}/100."
    )

    if strengths and strengths.lower() not in ["not mentioned", "n/a", ""]:
        reason_parts.append(
            f"The candidate exhibits notable strengths including {strengths.rstrip('.')}."
        )

    if education and education.lower() not in ["not mentioned", "n/a", ""]:
        short_edu = education[:120] + "..." if len(education) > 120 else education
        reason_parts.append(
            f"Educational background: {short_edu}"
        )

    if experience and experience.lower() not in ["not mentioned", "n/a", ""]:
        short_exp = experience[:120] + "..." if len(experience) > 120 else experience
        reason_parts.append(
            f"Professional experience: {short_exp}"
        )

    reason_parts.append(
        f"Based on the above assessment, the candidate has been shortlisted for the next "
        f"stage of the recruitment process."
    )

    return " ".join(reason_parts)


def get_rejection_reason(candidate_data: dict, role_key: str, score: int) -> str:
    """Generate professional rejection reason based on score and missing criteria."""
    role = ROLES[role_key]
    role_name = role["display_name"]
    must_have = role["selection_criteria"]["must_have"]
    matched_must = candidate_data.get("matched_must_have", []) or []
    must_missing = [kw for kw in must_have if kw not in matched_must]

    required_skills = role["required_skills"]
    skills_text = str(candidate_data.get("skills", "") or "").lower()
    skills_missing = [s for s in required_skills if s.lower() not in skills_text]
    must_match_count = len(matched_must)

    reason_parts = []

    reason_parts.append(
        f"Thank you for your interest in the {role_name} position. After a careful review "
        f"of your application, we regret to inform you that your profile did not meet the "
        f"minimum qualification criteria at this time, with a match score of {score}/100 "
        f"(minimum required: {SELECTION_SCORE_THRESHOLD}/100)."
    )

    if score < SELECTION_SCORE_THRESHOLD:
        reason_parts.append(
            "The submitted resume does not show enough overall alignment with the core "
            "requirements for this role."
        )
    elif must_match_count < 2:
        reason_parts.append(
            "Your profile includes some relevant technical keywords, but it does not clearly "
            "demonstrate enough role-defining must-have signals to confirm a strong match "
            "for this position."
        )
    else:
        reason_parts.append(
            "Your profile demonstrates partial alignment with the role requirements; "
            "however, it falls short of the standard needed to proceed to the next stage."
        )

    if must_missing:
        missing_str = ", ".join(must_missing[:8])
        reason_parts.append(
            f"Key competencies not clearly demonstrated in your resume: {missing_str}."
        )

    if skills_missing:
        missing_skills_str = ", ".join(skills_missing[:4])
        reason_parts.append(
            f"Required skills not evidenced: {missing_skills_str}."
        )

    reason_parts.append(
        "We encourage you to enhance your qualifications and skill set, and to consider "
        "applying for future opportunities that may be a better match for your profile. "
        "We wish you the very best in your career journey."
    )

    return " ".join(reason_parts)


def parse_ai_output(ai_text: str, resume_text: str = "", role_key: str = "") -> dict:
    result = {
        "status": "REJECTED",
        "rejection_reason": "",
        "full_name": "Not Mentioned",
        "email": "Not Mentioned",
        "phone": "Not Mentioned",
        "location": "Not Mentioned",
        "total_experience": "Not Mentioned",
        "education": "Not Mentioned",
        "skills": "Not Mentioned",
        "certifications": "Not Mentioned",
        "work_experience": "Not Mentioned",
        "match_score": "0",
        "key_strengths": "Not Mentioned",
        "concerns": "Not Mentioned",
        "raw_output": ai_text
    }

    # 1. Extract plain text regex values
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', ai_text)
    if email_match:
        result["email"] = email_match.group()

    phone_match = re.search(r'(\+?\d[\d\s\-]{8,14}\d)', ai_text)
    if phone_match:
        result["phone"] = phone_match.group().strip()

    # 2. Line-by-Line AI Output Processing Loop
    lines = ai_text.strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if not value or value.lower() in ["not mentioned", "n/a", "none", "-"]:
            continue

        if "full name" in key or key == "name":
            result["full_name"] = value
        elif "email" in key:
            if "@" in value:
                result["email"] = value
        elif "phone" in key or "mobile" in key or "contact" in key:
            result["phone"] = value
        elif "location" in key or "city" in key:
            result["location"] = value
        elif "experience" in key:
            result["total_experience"] = value
            result["work_experience"] = value
        elif "education" in key:
            result["education"] = value
        elif "skills" in key:
            result["skills"] = value
        elif "certif" in key:
            result["certifications"] = value
        elif "strength" in key:
            result["key_strengths"] = value
        elif "concern" in key:
            result["concerns"] = value

    if result["work_experience"] == "Not Mentioned" and result["total_experience"] != "Not Mentioned":
        result["work_experience"] = result["total_experience"]

    # 3. CRITICAL FIXED STEP: Force precise mathematical scoring over AI numbers
    if resume_text and role_key:
        calculated = calculate_score_from_resume(resume_text, role_key)
        result["match_score"] = str(calculated)
        print(f"   🎯 Token Bias Shield: Calculated score from keywords: {calculated}/100")
    else:
        result["match_score"] = "0"

    # 4. Sync baseline status mapping
    final_score = int(result["match_score"])
    result["status"] = "SELECTED" if final_score >= SELECTION_SCORE_THRESHOLD else "REJECTED"
    
    return result


def extract_from_resume_directly(resume_text: str) -> dict:
    extracted = {
        "full_name": "Not Mentioned",
        "email": "Not Mentioned",
        "phone": "Not Mentioned",
        "location": "Not Mentioned",
    }

    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', resume_text)
    if email_match:
        extracted["email"] = email_match.group()

    phone_match = re.search(
        r'(\+91[\s\-]?)?[6-9]\d{9}|(\+91[\s\-]?)?\d{10}|\d{3}[\s\-]\d{3}[\s\-]\d{4}',
        resume_text
    )
    if phone_match:
        extracted["phone"] = phone_match.group().strip()

    header_name = extract_name_from_resume_header(resume_text)
    if header_name:
        extracted["full_name"] = header_name

    return extracted


def analyze_resume(resume_text: str, role_key: str) -> dict:
    """Full resume analysis — AI extracts fields, score decides status."""
    direct = extract_from_resume_directly(resume_text)

    try:
        prompt = build_prompt(resume_text, role_key)

        response = ollama.chat(
            # model="phi3",
            model="qwen3:8b",
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": 400, "temperature": 0}
        )

        ai_text = response["message"]["content"]
        print(f"\n RAW AI OUTPUT:\n{ai_text}\n{'='*40}")

        parsed = parse_ai_output(ai_text, resume_text, role_key)

        for field in ["full_name", "email", "phone", "location"]:
            if parsed.get(field) in ["Not Mentioned", "", None]:
                parsed[field] = direct.get(field, "Not Mentioned")

        parsed["full_name"] = extract_best_candidate_name(
            resume_text,
            ai_name=parsed.get("full_name", ""),
            email=parsed.get("email", direct.get("email", "")),
        )

        parsed["role_key"] = role_key
        parsed["role_display"] = ROLES[role_key]["display_name"]

        # Generate proper professional reasons based on deterministic score
        final_score = int(parsed["match_score"])
        if parsed["status"] == "SELECTED":
            parsed["rejection_reason"] = ""
            parsed["selection_reason"] = get_selection_reason(parsed, role_key, final_score)
        else:
            parsed["selection_reason"] = ""
            parsed["rejection_reason"] = get_rejection_reason(parsed, role_key, final_score)

        print(f"   Final Status : {parsed['status']}")
        print(f"   Final Score  : {parsed['match_score']}/100")

        return parsed

    except Exception as error:
        print(f"   AI failed: {error} — using direct extraction")
        role = ROLES[role_key]
        resume_lower = resume_text.lower()
        must_have = role["selection_criteria"]["must_have"]
        matched = [kw for kw in must_have if kw.lower() in resume_lower]

        calculated_score = calculate_score_from_resume(resume_text, role_key)
        status = "SELECTED" if calculated_score >= 70 else "REJECTED"

        all_keywords = role["required_skills"] + role["preferred_skills"]
        found_skills = [s for s in all_keywords if s.lower() in resume_lower]

        fallback_data = {
            "status": status,
            "rejection_reason": "",
            "selection_reason": "",
            "full_name": extract_best_candidate_name(
                resume_text,
                ai_name=direct.get("full_name", ""),
                email=direct.get("email", ""),
            ),
            "email": direct.get("email", "Not Mentioned"),
            "phone": direct.get("phone", "Not Mentioned"),
            "location": direct.get("location", "Not Mentioned"),
            "total_experience": "Not Mentioned",
            "education": "Not Mentioned",
            "skills": ", ".join(found_skills) if found_skills else "Not Mentioned",
            "certifications": "Not Mentioned",
            "work_experience": "Not Mentioned",
            "match_score": str(calculated_score),
            "key_strengths": ", ".join(matched) if matched else "Not Mentioned",
            "concerns": "Could not complete AI analysis.",
            "raw_output": "",
            "role_key": role_key,
            "role_display": role["display_name"]
        }

        if status == "SELECTED":
            fallback_data["selection_reason"] = get_selection_reason(fallback_data, role_key, calculated_score)
        else:
            fallback_data["rejection_reason"] = get_rejection_reason(fallback_data, role_key, calculated_score)

        return fallback_data
