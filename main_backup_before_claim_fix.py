from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import re
import os
import tempfile

app = FastAPI(
    title="SkillProof AI",
    version="1.0.0",
    description="Resume vs Job Description Analysis API"
)

# ---------------------------------------------------------
# GLOBAL RESUME STORAGE
# ---------------------------------------------------------

resume_text = ""
resume_filename = ""

# ---------------------------------------------------------
# SKILL LIST
# ---------------------------------------------------------
# Keep this list controlled so generic words like "api" or
# single-letter "c" are not accidentally extracted from a JD.

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

# Canonical skill -> accepted PDF/JD variants.
# This fixes extraction artifacts such as "P ython" and "A WS".
SKILL_ALIASES = {
    "python": ["python", "p ython"],
    "java": ["java"],
    "c": ["c programming", "c language"],
    "html": ["html"],
    "css": ["css"],
    "javascript": ["javascript", "java script"],
    "sql": ["sql"],
    "postgresql": ["postgresql", "postgre sql"],
    "mysql": ["mysql", "my sql"],
    "mongodb": ["mongodb", "mongo db"],
    "fastapi": ["fastapi", "fast api", "f astapi"],
    "flask": ["flask"],
    "django": ["django"],
    "git": ["git"],
    "github": ["github", "git hub"],
    "docker": ["docker"],
    "aws": ["aws", "a ws"],
    "azure": ["azure"],
    "gcp": ["gcp", "google cloud platform"],
    "machine learning": ["machine learning", "machine-learning"],
    "deep learning": ["deep learning", "deep-learning"],
    "tensorflow": ["tensorflow", "tensor flow"],
    "pytorch": ["pytorch", "py torch"],
    "react": ["react"],
    "node.js": ["node.js", "node js"],
    "node": ["node"],
    "web development": ["web development", "web-development"],
    "cloud computing": ["cloud computing", "cloud-computing"],
    "data structures": ["data structures", "data-structures"],
    "data analysis": ["data analysis", "data-analysis"],
}

# REST API is a capability rather than a standalone skill here.
# It is intentionally handled as an alias/capability so
# "REST APIs", "REST API" and generic "API" do not become
# duplicate required skills.
REST_API_ALIASES = ["rest api", "rest apis", "restful api", "restful apis"]


class JobDescription(BaseModel):
    job_description: str


# ---------------------------------------------------------
# ROOT / HEALTH
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Welcome to SkillProof AI",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "resume_uploaded": bool(resume_text)
    }


# ---------------------------------------------------------
# PDF TEXT EXTRACTION
# ---------------------------------------------------------

def extract_pdf_text(file_path: str) -> str:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PyPDF2 is not installed. Run: pip install PyPDF2"
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
            detail=f"Unable to read PDF: {str(e)}"
        )


# ---------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------

def normalize_text(text: str) -> str:
    text = text.lower()

    # Join common PDF extraction artifacts:
    # "P ython" -> "python", "A WS" -> "aws",
    # "F astAPI" -> "fastapi", etc.
    artifact_patterns = {
        r"\bp\s+y\s+t\s+h\s+o\s+n\b": "python",
        r"\ba\s+w\s+s\b": "aws",
        r"\bf\s+a\s+s\s+t\s*a\s*p\s*i\b": "fastapi",
        r"\bp\s+o\s+s\s+t\s+g\s+r\s+e\s+s\s+q\s+l\b": "postgresql",
        r"\bm\s+y\s+\s*q\s+l\b": "mysql",
        r"\bg\s+i\s+t\s+h\s+u\s+b\b": "github",
        r"\bd\s+o\s+c\s+k\s+e\s+r\b": "docker",
    }

    for pattern, replacement in artifact_patterns.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Remove line-break/hyphen artifacts.
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)

    # Special characters -> spaces, while keeping +, #, ., / and -
    text = re.sub(r"[^a-zA-Z0-9+#.\-/ ]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def contains_phrase(text: str, phrase: str) -> bool:
    """
    Boundary-aware phrase matching.
    Prevents 'git' from matching the inside of 'digital',
    and 'c' from matching every word containing c.
    """
    text_n = normalize_text(text)
    phrase_n = normalize_text(phrase)

    if not phrase_n:
        return False

    pattern = r"(?<![a-z0-9])" + re.escape(phrase_n) + r"(?![a-z0-9])"
    return re.search(pattern, text_n, flags=re.IGNORECASE) is not None


def skill_present(text: str, skill: str) -> bool:
    for alias in SKILL_ALIASES.get(skill, [skill]):
        if contains_phrase(text, alias):
            return True
    return False


def rest_api_present(text: str) -> bool:
    return any(contains_phrase(text, alias) for alias in REST_API_ALIASES)


def skill_display(skill: str) -> str:
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
    return display.get(skill, skill.title())


# ---------------------------------------------------------
# SKILL EXTRACTION
# ---------------------------------------------------------

def extract_skills(text: str) -> List[str]:
    found = []

    for skill in SKILLS:
        if skill_present(text, skill):
            found.append(skill)

    return found


def extract_required_skills(job_description: str) -> List[str]:
    required = []

    for skill in SKILLS:
        if skill_present(job_description, skill):
            required.append(skill)

    # REST API is only added once, never "REST APIs" + "REST API"
    # and generic "API" is never treated as a separate skill.
    if rest_api_present(job_description):
        required.append("rest api")

    return required


# ---------------------------------------------------------
# CONTEXT / LEVEL
# ---------------------------------------------------------

def get_skill_context(text: str, skill: str) -> str:
    aliases = SKILL_ALIASES.get(skill, [skill])

    for alias in aliases:
        lower_text = text.lower()
        position = lower_text.find(alias.lower())

        if position != -1:
            start = max(0, position - 180)
            end = min(len(text), position + len(alias) + 300)
            return text[start:end].strip()

    if skill == "rest api":
        for alias in REST_API_ALIASES:
            position = text.lower().find(alias.lower())
            if position != -1:
                start = max(0, position - 180)
                end = min(len(text), position + len(alias) + 300)
                return text[start:end].strip()

    return ""


def detect_skill_level(text: str, skill: str) -> str:
    context = get_skill_context(text, skill).lower()

    if not context:
        return "None"

    if "advanced" in context or "expert" in context:
        return "Advanced"

    if "intermediate" in context:
        return "Intermediate"

    if "basic" in context or "fundamental" in context:
        return "Basic"

    if "proficient" in context or "experienced" in context:
        return "Intermediate"

    evidence_words = [
        "project", "internship", "experience", "developed",
        "built", "worked", "implemented", "created", "using"
    ]

    if any(word in context for word in evidence_words):
        return "Intermediate"

    return "Unknown"


# ---------------------------------------------------------
# EVIDENCE ANALYSIS
# ---------------------------------------------------------

def analyze_skill_evidence(skill: str, resume: str) -> Dict[str, Any]:
    present = skill_present(resume, skill) if skill != "rest api" else rest_api_present(resume)
    context = get_skill_context(resume, skill)
    level = detect_skill_level(resume, skill)

    if not present:
        return {
            "skill": skill_display(skill),
            "status": "Missing",
            "skill_level": "None",
            "evidence_type": "No Evidence",
            "evidence": f"{skill_display(skill)} is not found in the resume.",
            "recommendation": (
                f"Learn {skill_display(skill)} and build a practical project."
            )
        }

    lower_context = context.lower()

    practical_words = [
        "project", "internship", "experience", "developed",
        "built", "worked", "implemented", "created", "using"
    ]

    has_practical_evidence = any(
        word in lower_context for word in practical_words
    )

    # GitHub profile alone should not be treated as proof of Git skill.
    if skill == "git" and "github" in resume.lower() and not contains_phrase(
        resume, "git"
    ):
        return {
            "skill": "Git",
            "status": "Weak Evidence",
            "skill_level": "Unknown",
            "evidence_type": "GitHub Profile",
            "evidence": (
                "A GitHub profile is present, but this alone does not "
                "prove Git proficiency."
            ),
            "recommendation": (
                "Add specific Git usage or project version control experience."
            )
        }

    if has_practical_evidence:
        return {
            "skill": skill_display(skill),
            "status": "Evidence Found",
            "skill_level": level,
            "evidence_type": "Project / Internship / Experience",
            "evidence": context,
            "recommendation": (
                f"Prepare to explain how {skill_display(skill)} "
                "was actually used."
            )
        }

    return {
        "skill": skill_display(skill),
        "status": "Claimed",
        "skill_level": level,
        "evidence_type": "Skill Section / Resume Mention",
        "evidence": context,
        "recommendation": (
            f"Strengthen {skill_display(skill)} evidence with "
            "a practical project and specific usage details."
        )
    }


# ---------------------------------------------------------
# CLAIM ANALYSIS
# ---------------------------------------------------------

def analyze_claims(resume: str, resume_skills: List[str]) -> List[Dict[str, Any]]:
    results = []

    for skill in resume_skills:
        context = get_skill_context(resume, skill)
        lower_context = context.lower()

        practical_indicators = [
            "project", "internship", "experience", "developed",
            "built", "implemented", "worked", "created",
            "using", "deployment", "trained", "training"
        ]

        practical_count = sum(
            1 for word in practical_indicators if word in lower_context
        )

        strong_claim_words = [
            "expert", "advanced", "proficient",
            "experienced", "specialist"
        ]

        strong_claim = any(
            word in lower_context for word in strong_claim_words
        )

        if practical_count >= 2:
            claim_status = "Strong Evidence"
            confidence = "High"
            recommendation = (
                f"{skill_display(skill)} has practical evidence. "
                "Prepare to explain the exact project, tools used "
                "and your contribution."
            )

        elif practical_count == 1:
            claim_status = "Moderate Evidence"
            confidence = "Medium"
            recommendation = (
                f"{skill_display(skill)} is mentioned with some practical "
                "context. Add measurable project details to strengthen the claim."
            )

        elif strong_claim:
            claim_status = "Potentially Weak Claim"
            confidence = "Low"
            recommendation = (
                f"{skill_display(skill)} appears to be a strong claim without "
                "enough supporting evidence. Add a project, internship or "
                "measurable implementation example."
            )

        else:
            claim_status = "Claimed Without Strong Evidence"
            confidence = "Low"
            recommendation = (
                f"{skill_display(skill)} is listed, but practical evidence "
                "is limited. Build a project or add specific usage details."
            )

        results.append({
            "skill": skill_display(skill),
            "claim_status": claim_status,
            "confidence": confidence,
            "evidence": context,
            "recommendation": recommendation
        })

    return results


# ---------------------------------------------------------
# UPLOAD RESUME
# ---------------------------------------------------------

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    global resume_text
    global resume_filename

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please select a resume file."
        )

    extension = os.path.splitext(file.filename)[1].lower()

    if extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF resume files are supported."
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".pdf"
        ) as temp_file:
            temp_file.write(contents)
            temp_path = temp_file.name

        text = extract_pdf_text(temp_path)

        if not text:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract text from the PDF. "
                    "Please upload a text-based PDF."
                )
            )

        resume_text = text
        resume_filename = file.filename

        return {
            "filename": file.filename,
            "message": "Resume uploaded successfully!",
            "text": text
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


# ---------------------------------------------------------
# ANALYZE RESUME
# ---------------------------------------------------------

@app.post("/analyze")
def analyze_resume(data: JobDescription):
    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="Please upload a resume first using /upload-resume."
        )

    job_description = data.job_description.strip()

    if not job_description:
        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty."
        )

    required_skills = extract_required_skills(job_description)
    resume_skills = extract_skills(resume_text)

    matched_skills = []
    missing_skills = []

    for skill in required_skills:
        if skill in resume_skills:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    if required_skills:
        match_percentage = round(
            (len(matched_skills) / len(required_skills)) * 100,
            2
        )
    else:
        match_percentage = 0.0

    evidence_analysis = [
        analyze_skill_evidence(skill, resume_text)
        for skill in required_skills
    ]

    claim_analysis = analyze_claims(
        resume_text,
        resume_skills
    )

    # -----------------------------------------------------
    # INTERVIEW RECOMMENDATIONS
    # -----------------------------------------------------

    interview_recommendations = []

    for skill in required_skills:
        skill_title = skill_display(skill)

        if skill in missing_skills:
            recommendations = {
                "sql": "Practice SQL SELECT, JOIN, GROUP BY, subqueries and database queries.",
                "postgresql": "Prepare PostgreSQL database concepts, indexing and database design.",
                "fastapi": "Learn FastAPI routing, Pydantic models and REST API development.",
                "git": "Prepare Git basics: commit, branch, merge, pull and push.",
                "docker": "Learn Docker basics and containerize one project.",
                "rest api": "Practice REST API methods, status codes, request/response handling and API testing.",
            }

            interview_recommendations.append(
                recommendations.get(
                    skill,
                    f"Learn {skill_title} and build a practical project."
                )
            )

        else:
            recommendations = {
                "python": "Prepare Python fundamentals, functions, OOP and coding questions.",
                "aws": "Prepare AWS/cloud concepts and explain your actual cloud experience.",
                "machine learning": "Prepare ML concepts, preprocessing, model training and evaluation.",
                "rest api": "Be ready to explain REST API design, endpoints, HTTP methods and status codes.",
            }

            interview_recommendations.append(
                recommendations.get(
                    skill,
                    f"Prepare practical {skill_title} questions and explain your project experience."
                )
            )

    # -----------------------------------------------------
    # MESSAGE
    # -----------------------------------------------------

    if missing_skills:
        missing_text = ", ".join(
            skill_display(skill)
            for skill in missing_skills
        )

        message = (
            f"You are missing {len(missing_skills)} required skill(s): "
            f"{missing_text}. We recommend improving these skills before "
            "the interview."
        )
    else:
        message = (
            "Excellent! Your resume contains all required skills "
            "for this job description."
        )

    return {
        "message": message,
        "required_skills": required_skills,
        "resume_skills": resume_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_percentage": match_percentage,
        "evidence_analysis": evidence_analysis,
        "claim_analysis": claim_analysis,
        "interview_recommendations": interview_recommendations
    }
