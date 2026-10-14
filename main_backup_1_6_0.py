from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import re
import os
import tempfile


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="SkillProof AI",
    version="1.6.0",
    description="Resume vs Job Description Analysis API"
)


# =========================================================
# GLOBAL RESUME STORAGE
# =========================================================

resume_text = ""
resume_filename = ""


# =========================================================
# SKILL LIST
# =========================================================

SKILLS = [
    "python",
    "java",
    "c",
    "html",
    "css",
    "javascript",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "fastapi",
    "flask",
    "django",
    "git",
    "github",
    "docker",
    "aws",
    "azure",
    "gcp",
    "machine learning",
    "deep learning",
    "tensorflow",
    "pytorch",
    "react",
    "node.js",
    "node",
    "web development",
    "cloud computing",
    "data structures",
    "data analysis",
]


# =========================================================
# SKILL ALIASES
# =========================================================

SKILL_ALIASES = {

    "python": [
        "python",
        "p ython",
        "p y t h o n",
    ],

    "java": [
        "java",
        "ja va",
    ],

    "c": [
        "c programming",
        "c language",
    ],

    "html": [
        "html",
        "h t m l",
    ],

    "css": [
        "css",
        "c s s",
    ],

    "javascript": [
        "javascript",
        "java script",
        "java s cript",
    ],

    "sql": [
        "sql",
        "s q l",
    ],

    "postgresql": [
        "postgresql",
        "postgre sql",
        "p o s t g r e s q l",
    ],

    "mysql": [
        "mysql",
        "my sql",
        "m y s q l",
    ],

    "mongodb": [
        "mongodb",
        "mongo db",
        "m o n g o d b",
    ],

    "fastapi": [
        "fastapi",
        "fast api",
        "f astapi",
        "f a s t a p i",
    ],

    "flask": [
        "flask",
    ],

    "django": [
        "django",
    ],

    "git": [
        "git",
    ],

    "github": [
        "github",
        "git hub",
        "g i t h u b",
    ],

    "docker": [
        "docker",
        "d o c k e r",
    ],

    "aws": [
        "aws",
        "a ws",
        "a w s",
    ],

    "azure": [
        "azure",
    ],

    "gcp": [
        "gcp",
        "google cloud platform",
    ],

    "machine learning": [
        "machine learning",
        "machine-learning",
        "machine  learning",
    ],

    "deep learning": [
        "deep learning",
        "deep-learning",
    ],

    "tensorflow": [
        "tensorflow",
        "tensor flow",
    ],

    "pytorch": [
        "pytorch",
        "py torch",
    ],

    "react": [
        "react",
    ],

    "node.js": [
        "node.js",
        "node js",
    ],

    "node": [
        "node",
    ],

    "web development": [
        "web development",
        "web-development",
        "web developer",
        "full stack",
        "full-stack",
        "fullstack",
    ],

    "cloud computing": [
        "cloud computing",
        "cloud-computing",
    ],

    "data structures": [
        "data structures",
        "data-structures",
    ],

    "data analysis": [
        "data analysis",
        "data-analysis",
    ],
}


# =========================================================
# REST API ALIASES
# =========================================================

REST_API_ALIASES = [
    "rest api",
    "rest apis",
    "restful api",
    "restful apis",
    "r e s t a p i",
]


# =========================================================
# REQUEST MODEL
# =========================================================

class JobDescription(BaseModel):
    job_description: str


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "Welcome to SkillProof AI",
        "status": "running",
        "version": "1.6.0",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "resume_uploaded": bool(resume_text),
    }


# =========================================================
# PDF TEXT EXTRACTION
# =========================================================

def extract_pdf_text(file_path: str) -> str:

    try:

        from PyPDF2 import PdfReader

    except ImportError:

        raise HTTPException(
            status_code=500,
            detail="PyPDF2 is not installed. Run: pip install PyPDF2",
        )

    try:

        reader = PdfReader(file_path)

        text_parts = []

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                text_parts.append(page_text)

        return "\n".join(text_parts).strip()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Unable to read PDF: {str(e)}",
        )


# =========================================================
# OCR CLEANING
# =========================================================

def clean_evidence_text(text: str) -> str:

    if not text:
        return ""

    text = text.replace("\r", "\n")

    # -----------------------------------------------------
    # OCR split skill names
    # -----------------------------------------------------

    replacements = {

        r"\bP\s*y\s*t\s*h\s*o\s*n\b":
            "Python",

        r"\bP\s*y\s*thon\b":
            "Python",

        r"\bA\s*W\s*S\b":
            "AWS",

        r"\bH\s*T\s*M\s*L\b":
            "HTML",

        r"\bC\s*S\s*S\b":
            "CSS",

        r"\bJ\s*a\s*v\s*a\s*S\s*c\s*r\s*i\s*p\s*t\b":
            "JavaScript",

        r"\bF\s*a\s*s\s*t\s*A\s*P\s*I\b":
            "FastAPI",

        r"\bP\s*o\s*s\s*t\s*g\s*r\s*e\s*S\s*Q\s*L\b":
            "PostgreSQL",

        r"\bM\s*y\s*S\s*Q\s*L\b":
            "MySQL",

        r"\bM\s*o\s*n\s*g\s*o\s*D\s*B\b":
            "MongoDB",

        r"\bG\s*i\s*t\s*H\s*u\s*b\b":
            "GitHub",

        r"\bD\s*o\s*c\s*k\s*e\s*r\b":
            "Docker",

        r"\bR\s*E\s*S\s*T\s*A\s*P\s*I\b":
            "REST API",

        r"\bM\s*a\s*c\s*h\s*i\s*n\s*e\s*L\s*e\s*a\s*r\s*n\s*i\s*n\s*g\b":
            "Machine Learning",

        r"\bD\s*e\s*e\s*p\s*L\s*e\s*a\s*r\s*n\s*i\s*n\s*g\b":
            "Deep Learning",

        r"\bW\s*e\s*b\s*D\s*e\s*v\s*e\s*l\s*o\s*p\s*m\s*e\s*n\s*t\b":
            "Web Development",

        r"\bC\s*l\s*o\s*u\s*d\s*C\s*o\s*m\s*p\s*u\s*t\s*i\s*n\s*g\b":
            "Cloud Computing",

        r"\bD\s*a\s*t\s*a\s*S\s*t\s*r\s*u\s*c\s*t\s*u\s*r\s*e\s*s\b":
            "Data Structures",

        r"\bD\s*a\s*t\s*a\s*A\s*n\s*a\s*l\s*y\s*s\s*i\s*s\b":
            "Data Analysis",
    }

    for pattern, replacement in replacements.items():

        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE,
        )

    # -----------------------------------------------------
    # Common OCR word splits
    # -----------------------------------------------------

    common_words = {

        r"\bJa\s*va\b":
            "Java",

        r"\bPr\s*ogramming\b":
            "Programming",

        r"\bProgr\s*amming\b":
            "Programming",

        r"\bDevel\s*opment\b":
            "Development",

        r"\bDevelopm\s*ent\b":
            "Development",

        r"\bDe\s*velopment\b":
            "Development",

        r"\bExper\s*ience\b":
            "Experience",

        r"\bExperi\s*ence\b":
            "Experience",

        r"\bEduca\s*tion\b":
            "Education",

        r"\bTechn\s*ologies\b":
            "Technologies",

        r"\bTechnol\s*ogies\b":
            "Technologies",

        r"\bApplic\s*ation\b":
            "Application",

        r"\bApplic\s*ations\b":
            "Applications",

        r"\bProj\s*ect\b":
            "Project",

        r"\bProje\s*ct\b":
            "Project",

        r"\bProjec\s*ts\b":
            "Projects",

        r"\bSoft\s*ware\b":
            "Software",

        r"\bEng\s*ineering\b":
            "Engineering",

        r"\bIntern\s*ship\b":
            "Internship",

        r"\bAchiev\s*ements\b":
            "Achievements",

        r"\bConfr\s*ence\b":
            "Conference",

        r"\bDevelop\s*ed\b":
            "Developed",

        r"\bPerson\s*alized\b":
            "Personalized",
    }

    for pattern, replacement in common_words.items():

        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE,
        )

    # -----------------------------------------------------
    # Company / common OCR
    # -----------------------------------------------------

    text = re.sub(
        r"\bE\s*dup\s*h\s*o\s*n\s*i\s*x\b",
        "Eduphonix",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\bG\s*i\s*t\s*H\s*u\s*b\b",
        "GitHub",
        text,
        flags=re.IGNORECASE,
    )

    # -----------------------------------------------------
    # Line-break hyphen cleanup
    # -----------------------------------------------------

    text = re.sub(
        r"(\w)-\s+(\w)",
        r"\1\2",
        text,
    )

    # -----------------------------------------------------
    # Spaces before punctuation
    # -----------------------------------------------------

    text = re.sub(
        r"\s+([,.;:])",
        r"\1",
        text,
    )

    # -----------------------------------------------------
    # Clean each line but preserve line structure
    # -----------------------------------------------------

    lines = []

    for line in text.split("\n"):

        line = re.sub(
            r"[ \t]+",
            " ",
            line,
        ).strip()

        if line:
            lines.append(line)

    return "\n".join(lines).strip()


# =========================================================
# NORMALIZATION FOR MATCHING
# =========================================================

def normalize_text(text: str) -> str:

    if not text:
        return ""

    text = clean_evidence_text(text)

    text = text.lower()

    text = re.sub(
        r"\bjava\s+script\b",
        "javascript",
        text,
    )

    text = re.sub(
        r"\bpostgre\s+sql\b",
        "postgresql",
        text,
    )

    text = re.sub(
        r"\bmy\s+sql\b",
        "mysql",
        text,
    )

    text = re.sub(
        r"\bmongo\s+db\b",
        "mongodb",
        text,
    )

    text = re.sub(
        r"\bfast\s+api\b",
        "fastapi",
        text,
    )

    text = re.sub(
        r"\bnode\s+js\b",
        "node.js",
        text,
    )

    text = re.sub(
        r"[^a-zA-Z0-9+#.\-/ ]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# =========================================================
# CLEAN PHRASE FOR SEARCH
# =========================================================

def clean_search_phrase(phrase: str) -> str:

    if not phrase:
        return ""

    cleaned = clean_evidence_text(phrase)

    cleaned = cleaned.lower()

    cleaned = re.sub(
        r"[^a-zA-Z0-9+#.\-/ ]",
        " ",
        cleaned,
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    ).strip()

    return cleaned


# =========================================================
# PHRASE MATCHING
# =========================================================

def contains_phrase(
    text: str,
    phrase: str,
) -> bool:

    if not text or not phrase:
        return False

    text_n = normalize_text(text)

    phrase_n = clean_search_phrase(phrase)

    if not phrase_n:
        return False

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(phrase_n)
        + r"(?![a-z0-9])"
    )

    return (
        re.search(
            pattern,
            text_n,
            flags=re.IGNORECASE,
        )
        is not None
    )


# =========================================================
# SKILL PRESENCE
# =========================================================

def skill_present(
    text: str,
    skill: str,
) -> bool:

    aliases = SKILL_ALIASES.get(
        skill,
        [skill],
    )

    for alias in aliases:

        if contains_phrase(
            text,
            alias,
        ):
            return True

    return False


# =========================================================
# REST API PRESENCE
# =========================================================

def rest_api_present(
    text: str,
) -> bool:

    return any(
        contains_phrase(
            text,
            alias,
        )
        for alias in REST_API_ALIASES
    )


# =========================================================
# DISPLAY NAMES
# =========================================================

def skill_display(
    skill: str,
) -> str:

    display = {

        "python": "Python",
        "java": "Java",
        "c": "C",
        "html": "HTML",
        "css": "CSS",
        "javascript": "JavaScript",
        "sql": "SQL",
        "postgresql": "PostgreSQL",
        "mysql": "MySQL",
        "mongodb": "MongoDB",
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "git": "Git",
        "github": "GitHub",
        "docker": "Docker",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "tensorflow": "TensorFlow",
        "pytorch": "PyTorch",
        "react": "React",
        "node.js": "Node.js",
        "node": "Node",
        "web development": "Web Development",
        "cloud computing": "Cloud Computing",
        "data structures": "Data Structures",
        "data analysis": "Data Analysis",
        "rest api": "REST API",
    }

    return display.get(
        skill,
        skill.title(),
    )


# =========================================================
# SKILL EXTRACTION
# =========================================================

def extract_skills(
    text: str,
) -> List[str]:

    found = []

    for skill in SKILLS:

        if skill_present(
            text,
            skill,
        ):
            found.append(skill)

    # Node.js represents Node
    if "node.js" in found and "node" in found:
        found.remove("node")

    # REST API
    if rest_api_present(text):
        found.append("rest api")

    return found


# =========================================================
# REQUIRED SKILL EXTRACTION
# =========================================================

def extract_required_skills(
    job_description: str,
) -> List[str]:

    required = []

    for skill in SKILLS:

        if skill_present(
            job_description,
            skill,
        ):
            required.append(skill)

    if "node.js" in required and "node" in required:
        required.remove("node")

    if rest_api_present(job_description):
        required.append("rest api")

    return required


# =========================================================
# FIND SKILL POSITION
# =========================================================

def find_skill_position(
    text: str,
    skill: str,
):
    if not text:
        return None

    cleaned_text = clean_evidence_text(text)

    search_text = cleaned_text.lower()

    aliases = (
        REST_API_ALIASES
        if skill == "rest api"
        else SKILL_ALIASES.get(
            skill,
            [skill],
        )
    )

    aliases = sorted(
        aliases,
        key=len,
        reverse=True,
    )

    for alias in aliases:

        alias_clean = clean_search_phrase(alias)

        if not alias_clean:
            continue

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(alias_clean)
            + r"(?![a-z0-9])"
        )

        match = re.search(
            pattern,
            search_text,
            flags=re.IGNORECASE,
        )

        if match:

            return (
                match.start(),
                match.end(),
                cleaned_text,
            )

    return None


# =========================================================
# CHECK IF LINE IS A SKILLS SECTION
# =========================================================

def is_skill_section_text(text: str) -> bool:

    if not text:
        return False

    lower = text.lower()

    section_words = [
        "skills",
        "technical skill",
        "technical skills",
        "soft skill",
        "soft skills",
        "skill set",
        "technologies",
        "core skills",
    ]

    return any(
        word in lower
        for word in section_words
    )


# =========================================================
# PRACTICAL KEYWORDS
# =========================================================

PRACTICAL_KEYWORDS = [
    "project",
    "projects",
    "internship",
    "intern",
    "experience",
    "developed",
    "develop",
    "built",
    "implemented",
    "created",
    "worked",
    "using",
    "used",
    "deployment",
    "deployed",
    "application",
    "applications",
    "website",
    "system",
    "api",
    "database",
    "model",
    "trained",
    "training",
]


# =========================================================
# STRONG PRACTICAL KEYWORDS
# =========================================================

STRONG_PRACTICAL_KEYWORDS = [
    "developed",
    "built",
    "implemented",
    "created",
    "deployed",
    "trained",
    "designed",
    "integrated",
    "configured",
]


# =========================================================
# CHECK PRACTICAL EVIDENCE
# =========================================================

def has_practical_evidence(
    context: str,
) -> bool:

    if not context:
        return False

    lower_context = context.lower()

    # Skills section alone should NOT count
    if is_skill_section_text(lower_context):
        return False

    return any(
        word in lower_context
        for word in PRACTICAL_KEYWORDS
    )


# =========================================================
# CHECK STRONG PRACTICAL EVIDENCE
# =========================================================

def has_strong_practical_evidence(
    context: str,
) -> bool:

    if not context:
        return False

    lower_context = context.lower()

    if is_skill_section_text(lower_context):
        return False

    strong_count = sum(
        1
        for word in STRONG_PRACTICAL_KEYWORDS
        if word in lower_context
    )

    return strong_count >= 1


# =========================================================
# SPLIT INTO EVIDENCE CHUNKS
# =========================================================

def build_evidence_chunks(
    text: str,
) -> List[str]:

    cleaned = clean_evidence_text(text)

    if not cleaned:
        return []

    chunks = []

    # -----------------------------------------------------
    # First preserve PDF lines
    # -----------------------------------------------------

    for line in cleaned.split("\n"):

        line = line.strip()

        if not line:
            continue

        # -------------------------------------------------
        # Split long lines using sentence punctuation
        # -------------------------------------------------

        parts = re.split(
            r"(?<=[.!?])\s+",
            line,
        )

        for part in parts:

            part = re.sub(
                r"\s+",
                " ",
                part,
            ).strip()

            if part:
                chunks.append(part)

    # -----------------------------------------------------
    # If PDF produced one huge line, create smaller chunks
    # around common resume headings.
    # -----------------------------------------------------

    final_chunks = []

    heading_pattern = re.compile(
        r"\b("
        r"objective|profile|summary|experience|education|"
        r"skills|technical skills|projects|internship|"
        r"certifications|achievements|languages"
        r")\b",
        flags=re.IGNORECASE,
    )

    for chunk in chunks:

        matches = list(
            heading_pattern.finditer(chunk)
        )

        if len(chunk) > 450 and matches:

            positions = [
                m.start()
                for m in matches
            ]

            for i, start in enumerate(positions):

                end = (
                    positions[i + 1]
                    if i + 1 < len(positions)
                    else len(chunk)
                )

                section = chunk[start:end].strip()

                if section:
                    final_chunks.append(section)

        else:
            final_chunks.append(chunk)

    return final_chunks


# =========================================================
# SHORTEN CONTEXT AROUND SKILL
# =========================================================

def shorten_skill_context(
    chunk: str,
    skill: str,
    maximum: int = 220,
) -> str:

    if not chunk:
        return ""

    chunk = re.sub(
        r"\s+",
        " ",
        chunk,
    ).strip()

    if len(chunk) <= maximum:
        return chunk

    result = find_skill_position(
        chunk,
        skill,
    )

    if result is None:
        return chunk[:maximum].rsplit(" ", 1)[0] + "..."

    start_pos, end_pos, _ = result

    before = 70
    after = maximum - before

    start = max(
        0,
        start_pos - before,
    )

    end = min(
        len(chunk),
        end_pos + after,
    )

    snippet = chunk[start:end].strip()

    if start > 0:
        first_space = snippet.find(" ")

        if first_space > 0:
            snippet = snippet[first_space + 1:]

    if end < len(chunk):
        last_space = snippet.rfind(" ")

        if last_space > 0:
            snippet = snippet[:last_space]

    snippet = re.sub(
        r"\s+",
        " ",
        snippet,
    ).strip()

    if start > 0:
        snippet = "..." + snippet

    if end < len(chunk):
        snippet = snippet + "..."

    return snippet


# =========================================================
# SCORE EVIDENCE CHUNK
# =========================================================

def score_evidence_chunk(
    chunk: str,
    skill: str,
) -> int:

    if not chunk:
        return -999

    lower = chunk.lower()

    score = 0

    # Skill itself
    if (
        skill == "rest api"
        and rest_api_present(chunk)
    ):
        score += 5

    elif (
        skill != "rest api"
        and skill_present(chunk, skill)
    ):
        score += 5

    # Practical evidence
    for word in PRACTICAL_KEYWORDS:

        if word in lower:
            score += 2

    # Strong practical evidence
    for word in STRONG_PRACTICAL_KEYWORDS:

        if word in lower:
            score += 3

    # Resume section clues
    if "project" in lower:
        score += 4

    if "internship" in lower or "intern" in lower:
        score += 4

    if "experience" in lower:
        score += 4

    # Skills section gets penalty
    if is_skill_section_text(lower):
        score -= 8

    # Objective / profile should not be considered strong
    if "objective" in lower:
        score -= 3

    if "profile" in lower:
        score -= 2

    # -----------------------------------------------------
    # Skill-specific indicators
    # -----------------------------------------------------

    if skill == "machine learning":

        indicators = [
            "supervised",
            "unsupervised",
            "preprocessing",
            "model training",
            "model evaluation",
            "dataset",
            "predictive",
        ]

        for word in indicators:

            if word in lower:
                score += 3

    elif skill == "aws":

        indicators = [
            "ec2",
            "s3",
            "lambda",
            "iam",
            "cloudwatch",
            "aws services",
            "aws cloud",
        ]

        for word in indicators:

            if word in lower:
                score += 4

    elif skill == "git":

        indicators = [
            "commit",
            "branch",
            "merge",
            "pull",
            "push",
            "repository",
            "version control",
        ]

        for word in indicators:

            if word in lower:
                score += 4

    elif skill == "docker":

        indicators = [
            "container",
            "containerized",
            "dockerfile",
            "image",
            "docker compose",
        ]

        for word in indicators:

            if word in lower:
                score += 4

    elif skill == "fastapi":

        indicators = [
            "api",
            "endpoint",
            "pydantic",
            "uvicorn",
            "routing",
        ]

        for word in indicators:

            if word in lower:
                score += 3

    elif skill == "sql":

        indicators = [
            "query",
            "queries",
            "database",
            "select",
            "join",
            "mysql",
            "postgresql",
        ]

        for word in indicators:

            if word in lower:
                score += 2

    return score


# =========================================================
# GET SKILL CONTEXT - VERSION 1.6
# =========================================================

def get_skill_context(
    text: str,
    skill: str,
) -> str:

    if not text:
        return ""

    chunks = build_evidence_chunks(
        text
    )

    if not chunks:
        return ""

    candidates = []

    for index, chunk in enumerate(chunks):

        present = (
            rest_api_present(chunk)
            if skill == "rest api"
            else skill_present(
                chunk,
                skill,
            )
        )

        if not present:
            continue

        score = score_evidence_chunk(
            chunk,
            skill,
        )

        candidates.append(
            (
                score,
                index,
                chunk,
            )
        )

    if not candidates:
        return ""

    # -----------------------------------------------------
    # Highest scoring evidence
    # -----------------------------------------------------

    candidates.sort(
        key=lambda item: (
            item[0],
            -len(item[2]),
        ),
        reverse=True,
    )

    best_score, best_index, best_chunk = candidates[0]

    # -----------------------------------------------------
    # If practical evidence exists, prefer it.
    # -----------------------------------------------------

    practical_candidates = [
        item
        for item in candidates
        if has_practical_evidence(item[2])
    ]

    if practical_candidates:

        practical_candidates.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        best_score, best_index, best_chunk = (
            practical_candidates[0]
        )

    # -----------------------------------------------------
    # Skills section:
    # return focused skill phrase instead of whole section
    # -----------------------------------------------------

    if is_skill_section_text(best_chunk):

        result = shorten_skill_context(
            best_chunk,
            skill,
            maximum=140,
        )

        # If section is huge, keep only nearby skill text.
        if len(result) > 160:
            result = shorten_skill_context(
                best_chunk,
                skill,
                maximum=120,
            )

        return result

    # -----------------------------------------------------
    # Practical evidence:
    # include only best chunk.
    # -----------------------------------------------------

    result = shorten_skill_context(
        best_chunk,
        skill,
        maximum=220,
    )

    return result


# =========================================================
# SKILL LEVEL
# =========================================================

def detect_skill_level(
    text: str,
    skill: str,
) -> str:

    context = get_skill_context(
        text,
        skill,
    ).lower()

    if not context:
        return "None"

    # Explicit level has priority
    if (
        "advanced" in context
        or "expert" in context
    ):
        return "Advanced"

    if "intermediate" in context:
        return "Intermediate"

    if (
        "basic" in context
        or "fundamental" in context
    ):
        return "Basic"

    if (
        "proficient" in context
        or "experienced" in context
    ):
        return "Intermediate"

    # Practical evidence can imply Intermediate
    if has_practical_evidence(context):
        return "Intermediate"

    return "Unknown"


# =========================================================
# EVIDENCE ANALYSIS
# =========================================================

def analyze_skill_evidence(
    skill: str,
    resume: str,
) -> Dict[str, Any]:

    present = (
        skill_present(
            resume,
            skill,
        )
        if skill != "rest api"
        else rest_api_present(
            resume
        )
    )

    context = get_skill_context(
        resume,
        skill,
    )

    level = detect_skill_level(
        resume,
        skill,
    )

    # -----------------------------------------------------
    # Missing
    # -----------------------------------------------------

    if not present:

        return {

            "skill":
                skill_display(skill),

            "status":
                "Missing",

            "skill_level":
                "None",

            "evidence_type":
                "No Evidence",

            "evidence":
                f"{skill_display(skill)} "
                "is not found in the resume.",

            "recommendation":
                f"Learn {skill_display(skill)} "
                "and build a practical project.",
        }

    # -----------------------------------------------------
    # GitHub does NOT prove Git
    # -----------------------------------------------------

    if skill == "git":

        explicit_git = contains_phrase(
            resume,
            "git",
        )

        github_present = contains_phrase(
            resume,
            "github",
        )

        if (
            github_present
            and not explicit_git
        ):

            return {

                "skill": "Git",

                "status":
                    "Weak Evidence",

                "skill_level":
                    "Unknown",

                "evidence_type":
                    "GitHub Profile",

                "evidence":
                    "A GitHub profile is present, "
                    "but this alone does not prove "
                    "Git proficiency.",

                "recommendation":
                    "Add specific Git usage such as "
                    "commit, branch, merge, pull or "
                    "push experience.",
            }

    # -----------------------------------------------------
    # Practical evidence
    # -----------------------------------------------------

    practical = has_practical_evidence(
        context
    )

    strong_practical = has_strong_practical_evidence(
        context
    )

    if practical:

        status = (
            "Evidence Found"
            if strong_practical
            else "Moderate Evidence"
        )

        return {

            "skill":
                skill_display(skill),

            "status":
                status,

            "skill_level":
                level,

            "evidence_type":
                "Project / Internship / Experience",

            "evidence":
                context,

            "recommendation":
                f"Prepare to explain how "
                f"{skill_display(skill)} "
                "was actually used.",
        }

    # -----------------------------------------------------
    # Mention only
    # -----------------------------------------------------

    return {

        "skill":
            skill_display(skill),

        "status":
            "Claimed",

        "skill_level":
            level,

        "evidence_type":
            "Skill Section / Resume Mention",

        "evidence":
            context,

        "recommendation":
            f"Strengthen "
            f"{skill_display(skill)} "
            "evidence with a practical "
            "project and specific usage details.",
    }


# =========================================================
# CLAIM ANALYSIS
# =========================================================

def analyze_claims(
    resume: str,
    resume_skills: List[str],
) -> List[Dict[str, Any]]:

    results = []

    for skill in resume_skills:

        context = get_skill_context(
            resume,
            skill,
        )

        lower_context = context.lower()

        strong_evidence = False

        # -------------------------------------------------
        # Machine Learning
        # -------------------------------------------------

        if skill == "machine learning":

            ml_indicators = [

                "supervised",
                "unsupervised",
                "preprocessing",
                "model training",
                "model evaluation",
                "real-world datasets",
                "predictive models",
                "dataset",
            ]

            ml_count = sum(
                1
                for word in ml_indicators
                if word in lower_context
            )

            if ml_count >= 2:
                strong_evidence = True

        # -------------------------------------------------
        # Cloud Computing
        # -------------------------------------------------

        elif skill == "cloud computing":

            cloud_indicators = [

                "cloud architecture",
                "deployment models",
                "virtualization",
                "cloud security",
                "cloud platforms",
                "resource management",
                "cloud services",
            ]

            cloud_count = sum(
                1
                for word in cloud_indicators
                if word in lower_context
            )

            if cloud_count >= 2:
                strong_evidence = True

        # -------------------------------------------------
        # AWS
        # -------------------------------------------------

        elif skill == "aws":

            aws_indicators = [

                "ec2",
                "s3",
                "lambda",
                "iam",
                "cloudwatch",
                "aws services",
                "aws cloud",
                "deployment",
            ]

            aws_count = sum(
                1
                for word in aws_indicators
                if word in lower_context
            )

            if aws_count >= 1:
                strong_evidence = True

        # -------------------------------------------------
        # Git
        # -------------------------------------------------

        elif skill == "git":

            git_indicators = [

                "commit",
                "branch",
                "merge",
                "pull",
                "push",
                "repository",
                "version control",
            ]

            git_count = sum(
                1
                for word in git_indicators
                if word in lower_context
            )

            if git_count >= 1:
                strong_evidence = True

        # -------------------------------------------------
        # Docker
        # -------------------------------------------------

        elif skill == "docker":

            docker_indicators = [

                "container",
                "containerized",
                "dockerfile",
                "docker compose",
                "image",
            ]

            docker_count = sum(
                1
                for word in docker_indicators
                if word in lower_context
            )

            if docker_count >= 1:
                strong_evidence = True

        # -------------------------------------------------
        # FastAPI
        # -------------------------------------------------

        elif skill == "fastapi":

            fastapi_indicators = [

                "endpoint",
                "api",
                "pydantic",
                "uvicorn",
                "routing",
            ]

            fastapi_count = sum(
                1
                for word in fastapi_indicators
                if word in lower_context
            )

            if fastapi_count >= 1:
                strong_evidence = True

        # -------------------------------------------------
        # General practical evidence
        # -------------------------------------------------

        practical_indicators = [

            "project",
            "projects",
            "internship",
            "intern",
            "experience",
            "developed",
            "built",
            "implemented",
            "worked",
            "created",
            "deployment",
            "deployed",
        ]

        practical_count = sum(
            1
            for word in practical_indicators
            if word in lower_context
        )

        # -------------------------------------------------
        # Strong claim words
        # -------------------------------------------------

        strong_claim_words = [

            "expert",
            "advanced",
            "proficient",
            "experienced",
            "specialist",
        ]

        strong_claim = any(
            word in lower_context
            for word in strong_claim_words
        )

        # -------------------------------------------------
        # Determine strength
        # -------------------------------------------------

        if strong_evidence:

            claim_status = "Strong Evidence"
            confidence = "High"

            recommendation = (
                f"{skill_display(skill)} has strong "
                "practical evidence in the resume. "
                "Be ready to explain the exact work "
                "performed, tools used and your contribution."
            )

        elif practical_count >= 2:

            claim_status = "Strong Evidence"
            confidence = "High"

            recommendation = (
                f"{skill_display(skill)} has practical "
                "evidence. Prepare to explain the project, "
                "tools used and your contribution."
            )

        elif practical_count == 1:

            claim_status = "Moderate Evidence"
            confidence = "Medium"

            recommendation = (
                f"{skill_display(skill)} has some practical "
                "context. Add specific implementation details "
                "or measurable results to strengthen the claim."
            )

        elif strong_claim:

            claim_status = "Potentially Weak Claim"
            confidence = "Low"

            recommendation = (
                f"{skill_display(skill)} is presented as a "
                "strong skill but supporting practical evidence "
                "is limited. Add a project, internship or "
                "implementation example."
            )

        else:

            claim_status = "Claimed Without Strong Evidence"
            confidence = "Low"

            recommendation = (
                f"{skill_display(skill)} is listed in the "
                "resume, but strong practical evidence was "
                "not found. Add specific usage, project or "
                "implementation details."
            )

        results.append({

            "skill":
                skill_display(skill),

            "claim_status":
                claim_status,

            "confidence":
                confidence,

            "evidence":
                context,

            "recommendation":
                recommendation,
        })

    return results


# =========================================================
# UPLOAD RESUME
# =========================================================

@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
):

    global resume_text
    global resume_filename

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Please select a resume file.",
        )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension != ".pdf":

        raise HTTPException(
            status_code=400,
            detail="Only PDF resume files are supported.",
        )

    contents = await file.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf",
        ) as temp_file:

            temp_file.write(
                contents
            )

            temp_path = temp_file.name

        text = extract_pdf_text(
            temp_path
        )

        if not text:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract text from the PDF. "
                    "Please upload a text-based PDF."
                ),
            )

        resume_text = text
        resume_filename = file.filename

        return {

            "filename":
                file.filename,

            "message":
                "Resume uploaded successfully!",

            "text":
                text,
        }

    finally:

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            try:
                os.remove(temp_path)

            except Exception:
                pass


# =========================================================
# ANALYZE RESUME
# =========================================================

@app.post("/analyze")
def analyze_resume(
    data: JobDescription,
):

    if not resume_text:

        raise HTTPException(
            status_code=400,
            detail=(
                "Please upload a resume first "
                "using /upload-resume."
            ),
        )

    job_description = (
        data.job_description.strip()
    )

    if not job_description:

        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty.",
        )

    # -----------------------------------------------------
    # Extract skills
    # -----------------------------------------------------

    required_skills = extract_required_skills(
        job_description
    )

    resume_skills = extract_skills(
        resume_text
    )

    # -----------------------------------------------------
    # Match skills
    # -----------------------------------------------------

    matched_skills = []
    missing_skills = []

    for skill in required_skills:

        if skill in resume_skills:

            matched_skills.append(
                skill
            )

        else:

            missing_skills.append(
                skill
            )

    # -----------------------------------------------------
    # Match percentage
    # -----------------------------------------------------

    if required_skills:

        match_percentage = round(
            (
                len(matched_skills)
                / len(required_skills)
            ) * 100,
            2,
        )

    else:

        match_percentage = 0.0

    # -----------------------------------------------------
    # Evidence analysis
    # -----------------------------------------------------

    evidence_analysis = []

    for skill in required_skills:

        evidence = analyze_skill_evidence(
            skill,
            resume_text,
        )

        evidence_analysis.append(
            evidence
        )

    # -----------------------------------------------------
    # Claim analysis
    # -----------------------------------------------------

    claim_analysis = analyze_claims(
        resume_text,
        resume_skills,
    )

    # -----------------------------------------------------
    # Interview recommendations
    # -----------------------------------------------------

    interview_recommendations = []

    for skill in required_skills:

        skill_title = skill_display(
            skill
        )

        if skill in missing_skills:

            recommendations = {

                "sql":
                    "Practice SQL SELECT, JOIN, "
                    "GROUP BY, subqueries and database queries.",

                "postgresql":
                    "Prepare PostgreSQL database concepts, "
                    "indexing and database design.",

                "fastapi":
                    "Learn FastAPI routing, Pydantic models "
                    "and REST API development.",

                "git":
                    "Prepare Git basics: commit, branch, "
                    "merge, pull and push.",

                "docker":
                    "Learn Docker basics and "
                    "containerize one project.",

                "rest api":
                    "Practice REST API methods, status codes, "
                    "request/response handling and API testing.",

                "web development":
                    "Practice frontend and backend web development, "
                    "HTML, CSS, JavaScript and application architecture.",
            }

            interview_recommendations.append(
                recommendations.get(
                    skill,
                    f"Learn {skill_title} "
                    "and build a practical project.",
                )
            )

        else:

            recommendations = {

                "python":
                    "Prepare Python fundamentals, "
                    "functions, OOP and coding questions.",

                "aws":
                    "Prepare AWS/cloud concepts and "
                    "explain your actual cloud experience.",

                "machine learning":
                    "Prepare ML concepts, preprocessing, "
                    "model training and evaluation.",

                "web development":
                    "Be ready to explain the web applications "
                    "you built, technologies used and your role.",

                "rest api":
                    "Be ready to explain REST API design, "
                    "endpoints, HTTP methods and status codes.",
            }

            interview_recommendations.append(
                recommendations.get(
                    skill,
                    f"Prepare practical "
                    f"{skill_title} questions and "
                    "explain your project experience.",
                )
            )

    # -----------------------------------------------------
    # Message
    # -----------------------------------------------------

    if missing_skills:

        missing_text = ", ".join(
            skill_display(skill)
            for skill in missing_skills
        )

        message = (
            f"You are missing "
            f"{len(missing_skills)} required skill(s): "
            f"{missing_text}. We recommend improving "
            "these skills before the interview."
        )

    else:

        message = (
            "Excellent! Your resume contains all "
            "required skills for this job description."
        )

    # -----------------------------------------------------
    # FINAL RESPONSE
    # -----------------------------------------------------

    return {

        "message":
            message,

        "resume_filename":
            resume_filename,

        "required_skills":
            required_skills,

        "resume_skills":
            resume_skills,

        "matched_skills":
            matched_skills,

        "missing_skills":
            missing_skills,

        "match_percentage":
            match_percentage,

        "evidence_analysis":
            evidence_analysis,

        "claim_analysis":
            claim_analysis,

        "interview_recommendations":
            interview_recommendations,
    }