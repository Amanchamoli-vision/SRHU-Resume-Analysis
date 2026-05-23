# config.py — Centralized configuration for all roles

ROLES = {
    "BSC_NURSING": {
        "display_name": "BSC Nursing",
        "folder": "bsc_nursing",

        "keywords": [
            "nursing", "nurse", "bsc nursing", "b.sc nursing", "bscn",
            "gnm", "anm", "patient care", "clinical", "ward", "icu",
            "operation theatre", "ot", "rn", "registered nurse",
            "medication", "vitals", "iv", "catheter", "hospital",
            "nicu", "picu", "ccu", "labour room", "maternity",
            "dialysis", "oncology", "orthopedic", "pediatric",
            "triage", "bls", "acls", "cpr", "infection control",
            "nursing council", "rnc", "state nursing", "bedside",
        ],

        "required_skills": [
            "Patient Care", "Clinical Assessment", "Medication Administration",
            "Vital Signs", "Wound Care", "Dressing", "IV Line", "IV Therapy", 
            "Catheterization", "Infection Control", "Sterilization", 
            "Emergency Response", "First Aid", "CPR", "BLS", "Medical Terminology",
            "Patient Documentation", "Nursing Notes", "Doctor Coordination",
        ],

        "preferred_skills": [
            "ICU", "CCU", "NICU", "PICU", "Operation Theatre", "OT", 
            "Labour Room", "Maternity Care", "Dialysis", "Oncology", 
            "ACLS Certification", "ACLS", "EMR", "Hospital Software", 
            "Triage Assessment", "Ventilator Care", "Ventilator",
            "Nasogastric Tube", "NGT", "Central Line Care",
        ],

        "required_education": [
            "bsc nursing", "b.sc nursing", "b.sc. nursing", "bsc (nursing)",
            "bachelor of science in nursing", "gnm", "general nursing and midwifery",
            "anm", "auxiliary nurse midwife", "bscn",
            "post basic bsc nursing", "pb bsc nursing",
            "m.sc nursing", "msc nursing",
        ],

        "experience_min_years": 0,

        "selection_criteria": {
            "must_have": [
                "nursing",
                "nurse",
                "registered nurse",
                "bsc nursing",
                "gnm",
                "anm",
                "patient care",
                "medication administration",
                "ward nurse",
                "clinical nurse",
                "hospital",
                "clinical"
            ],
            "good_to_have": [
                "icu", "operation theatre", "ot", "nicu", "bls", "acls",
                "cpr", "ventilator", "dialysis", "labour room", "maternity",
                "catheter", "wound care", "infection control", "vitals", "bedside"
            ],
        },

        "email_subject_selected": "Interview Call – BSC Nursing Position",
        "email_subject_rejected": "Application Update – BSC Nursing Position",
    },

    # ════════════════════════════════════════════════════════════
    "TECHNICAL_STAFF": {
        "display_name": "Technical Staff",
        "folder": "technical_staff",

        "keywords": [
            "python", "java", "javascript", "typescript", "react", "angular",
            "vue", "node", "node.js", "express", "django", "flask", "spring",
            "sql", "mysql", "postgresql", "mongodb", "redis",
            "machine learning", "deep learning", "ai", "artificial intelligence",
            "nlp", "llm", "computer vision", "data science", "data analysis",
            "developer", "engineer", "software", "programmer", "coder",
            "backend", "frontend", "fullstack", "full stack", "devops",
            "cloud", "aws", "azure", "gcp", "docker", "kubernetes",
            "api", "rest api", "graphql", "microservices",
            "git", "github", "linux", "android", "ios", "flutter",
            "btech", "b.tech", "mtech", "mca", "bca",
        ],

        "required_skills": [
            "Python", "Java", "JavaScript", "C++", "HTML", "CSS",
            "Data Structures", "Algorithms", "SQL", "NoSQL", "MySQL", "PostgreSQL",
            "MongoDB", "SDLC", "Git", "GitHub", "Version Control", "REST API",
            "Debugging", "Testing", "Linux", "Command Line", "OOP", "Object Oriented"
        ],

        "preferred_skills": [
            "Cloud", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI-CD", "CI/CD",
            "Machine Learning", "Deep Learning", "AI", "Data Science", "System Design", 
            "Architecture", "Agile", "Scrum", "Android", "iOS", "Flutter",
            "Django", "React", "Spring Boot", "Node.js", "Microservices"
        ],

        "required_education": [
            "btech", "b.tech", "be", "b.e", "bachelor of engineering",
            "bachelor of technology", "mtech", "m.tech",
            "bsc computer science", "b.sc computer science",
            "bsc it", "b.sc it", "bsc information technology",
            "mca", "master of computer applications",
            "bca", "bachelor of computer applications",
            "msc computer science", "diploma in computer engineering",
            "diploma in it", "pgdca",
        ],

        "experience_min_years": 0,

        "selection_criteria": {
            "must_have": [
                "software developer",
                "software engineer",
                "web developer",
                "python developer",
                "java developer",
                "full stack developer",
                "backend developer",
                "frontend developer",
                "data scientist",
                "machine learning engineer",
                "android developer",
                "ios developer",
                "devops engineer",
                "data analyst",
                "developer",
                "programmer",
                "engineer",
                "coding"
            ],
            "good_to_have": [
                "react", "node.js", "django", "flask", "spring boot",
                "aws", "azure", "docker", "kubernetes", "mongodb",
                "postgresql", "rest api", "machine learning",
                "deep learning", "nlp", "flutter", "android",
                "data science", "devops", "microservices", "git", "sql", "linux"
            ],
        },

        "email_subject_selected": "Interview Call – Technical Staff Position",
        "email_subject_rejected": "Application Update – Technical Staff Position",
    },

    # ════════════════════════════════════════════════════════════
    "CLERICAL_ROLE": {
        "display_name": "Clerical Role",
        "folder": "clerical_role",

        "keywords": [
            "ms office", "microsoft office", "excel", "word", "powerpoint",
            "data entry", "typing", "clerical", "administrative", "admin",
            "office assistant", "receptionist", "secretary", "clerk",
            "filing", "documentation", "record keeping", "accounts",
            "tally", "tally erp", "tally prime", "billing", "invoicing",
            "dispatch", "front desk", "back office", "office management",
            "mis report", "mis", "pivot table", "shorthand", "steno",
            "google sheets", "google docs", "spreadsheet",
        ],

        "required_skills": [
            "MS Office", "Word", "Excel", "PowerPoint", "Data Entry", "Typing", 
            "Email Drafting", "Email Handling", "File Management", "Record Management", 
            "Computer Operation", "Communication", "Office Correspondence"
        ],

        "preferred_skills": [
            "Tally", "Tally ERP", "Tally Prime", "MIS", "MIS Report",
            "Pivot Table", "VLOOKUP", "Scheduling", "Calendar Management",
            "Shorthand", "Stenography", "Customer Handling", "Front Desk",
            "Billing", "Invoicing", "Payroll", "Attendance Management",
            "Google Workspace", "Google Sheets", "Google Docs"
        ],

        "required_education": [
            "12th", "12th pass", "intermediate", "hsc", "higher secondary",
            "graduation", "graduate", "any graduate", "ba", "b.a",
            "bachelor of arts", "bcom", "b.com", "bachelor of commerce",
            "bba", "b.b.a", "bsc", "b.sc", "mba", "mcom", "m.com",
            "diploma", "pgdca", "dca", "office management diploma",
        ],

        "experience_min_years": 0,

        "selection_criteria": {
            "must_have": [
                "data entry operator",
                "office assistant",
                "office clerk",
                "administrative assistant",
                "tally",
                "tally erp",
                "tally prime",
                "mis report",
                "data entry",
                "receptionist",
                "back office",
                "front desk",
                "clerk",
                "typing",
                "documentation"
            ],
            "good_to_have": [
                "pivot table", "vlookup", "shorthand", "stenography",
                "scheduling", "invoicing", "google sheets",
                "email handling", "petty cash", "purchase order",
                "attendance management", "billing", "payroll", "excel", "word"
            ],
        },

        "email_subject_selected": "Interview Call – Clerical Role Position",
        "email_subject_rejected": "Application Update – Clerical Role Position",
    },

    # ════════════════════════════════════════════════════════════
    "UNKNOWN_ROLE": {
        "display_name": "Unknown / Other",
        "folder": "unknown_role",
        "keywords": [],
        "required_skills": [],
        "preferred_skills": [],
        "required_education": [],
        "experience_min_years": 0,
        "selection_criteria": {
            "must_have": [],
            "good_to_have": [],
        },
        "email_subject_selected": "",
        "email_subject_rejected": "Application Update – No Matching Position",
    },
}

# ── Thresholds ───────────────────────────────────────────────────
ROLE_DETECTION_THRESHOLD = 2
SELECTION_THRESHOLD      = 2

# ── Base folder ──────────────────────────────────────────────────
BASE_DIR = "recruitment_data"