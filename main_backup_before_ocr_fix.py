from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import re
import os
import tempfile


app = FastAPI(
    title="SkillProof AI",
    version="1.1.0",
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


# ---------------------------------------------------------
# SKILL ALIASES
# ---------------------------------------------------------

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
    "machine learning": [
        "machine learning",
        "machine-learning"
    ],
    "deep learning": [
        "deep learning",
        "deep-learning"
    ],
    "tensorflow": [
        "tensorflow",
        "tensor flow"
    ],
    "pytorch": [
        "pytorch",
        "py torch"
    ],
    "react": ["react"],
    "node.js": [
        "node.js",
        "node js"
    ],
    "node": ["node"],
    "web development": [
        "web development",
        "web-development",
        "web developer",
        "full stack",
        "full-stack",
        "fullstack"
    ],
    "cloud computing": [
        "cloud computing",
        "cloud-computing"
    ],
    "data structures": [
        "data structures",
        "data-structures"
    ],
    "data analysis": [
        "data analysis",
        "data-analysis"
    ],
}


# ---------------------------------------------------------
# REST API ALIASES
# ---------------------------------------------------------

REST_API_ALIASES = [
    "rest api",
    "rest apis",
    "restful api",
    "restful apis"
]


# ---------------------------------------------------------
# REQUEST MODEL
# ---------------------------------------------------------

class JobDescription(BaseModel):
    job_description: str


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Welcome to SkillProof AI",
        "status": "running",
        "version": "1.1.0"
    }


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

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

    if not text:
        return ""

    text = text.lower()

    # Fix common PDF extraction artifacts
    artifact_patterns = {

        r"\bp\s+y\s+t\s+h\s+o\s+n\b":
            "python",

        r"\ba\s+w\s+s\b":
            "aws",

        r"\bf\s+a\s+s\s+t\s*a\s*p\s*i\b":
            "fastapi",

        r"\bp\s+o\s+s\s+t\s+g\s+r\s+e\s+s\s+q\s+l\b":
            "postgresql",

        r"\bm\s+y\s+\s*q\s+l\b":
            "mysql",

        r"\bg\s+i\s+t\s+h\s+u\s+b\b":
            "github",

        r"\bd\s+o\s+c\s+k\s+e\s+r\b":
            "docker",
    }

    for pattern, replacement in artifact_patterns.items():

        text = re.sub(
            pattern,
            replacement,
            text,
            flags=re.IGNORECASE
        )

    # Remove line-break hyphen artifacts
    text = re.sub(
        r"(\w)-\s+(\w)",
        r"\1\2",
        text
    )

    # Convert special characters to spaces
    text = re.sub(
        r"[^a-zA-Z0-9+#.\-/ ]",
        " ",
        text
    )

    # Multiple spaces -> one
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ---------------------------------------------------------
# PHRASE MATCHING
# ---------------------------------------------------------

def contains_phrase(text: str, phrase: str) -> bool:

    text_n = normalize_text(text)
    phrase_n = normalize_text(phrase)

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
            flags=re.IGNORECASE
        )
        is not None
    )


# ---------------------------------------------------------
# SKILL PRESENCE
# ---------------------------------------------------------

def skill_present(text: str, skill: str) -> bool:

    aliases = SKILL_ALIASES.get(
        skill,
        [skill]
    )

    for alias in aliases:

        if contains_phrase(
            text,
            alias
        ):
            return True

    return False


# ---------------------------------------------------------
# REST API PRESENCE
# ---------------------------------------------------------

def rest_api_present(text: str) -> bool:

    return any(
        contains_phrase(
            text,
            alias
        )
        for alias in REST_API_ALIASES
    )


# ---------------------------------------------------------
# DISPLAY NAMES
# ---------------------------------------------------------

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

    return display.get(
        skill,
        skill.title()
    )


# ---------------------------------------------------------
# SKILL EXTRACTION
# ---------------------------------------------------------

def extract_skills(text: str) -> List[str]:

    found = []

    for skill in SKILLS:

        if skill_present(
            text,
            skill
        ):

            found.append(skill)

    # REST API is treated separately
    if rest_api_present(text):

        found.append("rest api")

    return found


# ---------------------------------------------------------
# REQUIRED SKILL EXTRACTION
# ---------------------------------------------------------

def extract_required_skills(
    job_description: str
) -> List[str]:

    required = []

    for skill in SKILLS:

        if skill_present(
            job_description,
            skill
        ):

            required.append(skill)

    if rest_api_present(
        job_description
    ):

        required.append(
            "rest api"
        )

    return required


# ---------------------------------------------------------
# FIND SKILL POSITION
# ---------------------------------------------------------

def find_skill_position(
    text: str,
    skill: str
):

    normalized_text = normalize_text(text)

    aliases = (
        REST_API_ALIASES
        if skill == "rest api"
        else SKILL_ALIASES.get(
            skill,
            [skill]
        )
    )

    for alias in aliases:

        alias_n = normalize_text(alias)

        if not alias_n:
            continue

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(alias_n)
            + r"(?![a-z0-9])"
        )

        match = re.search(
            pattern,
            normalized_text,
            flags=re.IGNORECASE
        )

        if match:
            return match.start(), match.end()

    return None


# ---------------------------------------------------------
# SHORT EVIDENCE SNIPPET
# ---------------------------------------------------------

def get_skill_context(
    text: str,
    skill: str
) -> str:

    if not text:
        return ""

    position = find_skill_position(
        text,
        skill
    )

    if position is None:
        return ""

    start_pos, end_pos = position

    # Short relevant window
    start = max(
        0,
        start_pos - 100
    )

    end = min(
        len(text),
        end_pos + 180
    )

    snippet = text[start:end]

    # Clean whitespace
    snippet = re.sub(
        r"\s+",
        " ",
        snippet
    ).strip()

    # Avoid overly long response
    if len(snippet) > 300:

        snippet = (
            snippet[:300].rsplit(
                " ",
                1
            )[0]
            + "..."
        )

    if start > 0:
        snippet = "..." + snippet

    if end < len(text):
        snippet = snippet + "..."

    return snippet


# ---------------------------------------------------------
# SKILL LEVEL
# ---------------------------------------------------------

def detect_skill_level(
    text: str,
    skill: str
) -> str:

    context = get_skill_context(
        text,
        skill
    ).lower()

    if not context:
        return "None"

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

    evidence_words = [
        "project",
        "internship",
        "experience",
        "developed",
        "built",
        "worked",
        "implemented",
        "created",
        "using"
    ]

    if any(
        word in context
        for word in evidence_words
    ):
        return "Intermediate"

    return "Unknown"


# ---------------------------------------------------------
# EVIDENCE ANALYSIS
# ---------------------------------------------------------

def analyze_skill_evidence(
    skill: str,
    resume: str
) -> Dict[str, Any]:

    present = (
        skill_present(
            resume,
            skill
        )
        if skill != "rest api"
        else rest_api_present(resume)
    )

    context = get_skill_context(
        resume,
        skill
    )

    level = detect_skill_level(
        resume,
        skill
    )

    # Missing skill
    if not present:

        return {
            "skill": skill_display(skill),
            "status": "Missing",
            "skill_level": "None",
            "evidence_type": "No Evidence",
            "evidence": (
                f"{skill_display(skill)} "
                "is not found in the resume."
            ),
            "recommendation": (
                f"Learn {skill_display(skill)} "
                "and build a practical project."
            )
        }

    lower_context = context.lower()

    practical_words = [
        "project",
        "internship",
        "experience",
        "developed",
        "built",
        "worked",
        "implemented",
        "created",
        "using"
    ]

    has_practical_evidence = any(
        word in lower_context
        for word in practical_words
    )

    # GitHub alone is not proof of Git
    if (
        skill == "git"
        and contains_phrase(
            resume,
            "github"
        )
        and not contains_phrase(
            resume,
            "git"
        )
    ):

        return {
            "skill": "Git",
            "status": "Weak Evidence",
            "skill_level": "Unknown",
            "evidence_type": "GitHub Profile",
            "evidence": (
                "A GitHub profile is present, "
                "but this alone does not prove "
                "Git proficiency."
            ),
            "recommendation": (
                "Add specific Git usage or "
                "project version control experience."
            )
        }

    # Practical evidence
    if has_practical_evidence:

        return {
            "skill": skill_display(skill),
            "status": "Evidence Found",
            "skill_level": level,
            "evidence_type": (
                "Project / Internship / Experience"
            ),
            "evidence": context,
            "recommendation": (
                f"Prepare to explain how "
                f"{skill_display(skill)} "
                "was actually used."
            )
        }

    # Mention only
    return {
        "skill": skill_display(skill),
        "status": "Claimed",
        "skill_level": level,
        "evidence_type": (
            "Skill Section / Resume Mention"
        ),
        "evidence": context,
        "recommendation": (
            f"Strengthen "
            f"{skill_display(skill)} "
            "evidence with a practical "
            "project and specific usage details."
        )
    }


# ---------------------------------------------------------
# CLAIM ANALYSIS
# ---------------------------------------------------------

def analyze_claims(
    resume: str,
    resume_skills: List[str]
) -> List[Dict[str, Any]]:

    results = []

    for skill in resume_skills:

        context = get_skill_context(
            resume,
            skill
        )

        lower_context = context.lower()

        # ---------------------------------------------
        # Strong evidence
        # ---------------------------------------------

        strong_evidence = False

        if skill == "machine learning":

            ml_indicators = [
                "supervised",
                "unsupervised",
                "preprocessing",
                "model training",
                "model evaluation",
                "real-world datasets",
                "predictive models"
            ]

            ml_count = sum(
                1
                for word in ml_indicators
                if word in lower_context
            )

            if ml_count >= 2:
                strong_evidence = True

        elif skill == "cloud computing":

            cloud_indicators = [
                "cloud architecture",
                "deployment models",
                "virtualization",
                "cloud security",
                "cloud platforms",
                "resource management"
            ]

            cloud_count = sum(
                1
                for word in cloud_indicators
                if word in lower_context
            )

            if cloud_count >= 2:
                strong_evidence = True

        # ---------------------------------------------
        # General practical evidence
        # ---------------------------------------------

        practical_indicators = [
            "project",
            "internship",
            "experience",
            "developed",
            "built",
            "implemented",
            "worked",
            "created",
            "deployment"
        ]

        practical_count = sum(
            1
            for word in practical_indicators
            if word in lower_context
        )

        # ---------------------------------------------
        # Strong claim words
        # ---------------------------------------------

        strong_claim_words = [
            "expert",
            "advanced",
            "proficient",
            "experienced",
            "specialist"
        ]

        strong_claim = any(
            word in lower_context
            for word in strong_claim_words
        )

        # ---------------------------------------------
        # Determine claim strength
        # ---------------------------------------------

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

        results.append(
            {
                "skill": skill_display(skill),
                "claim_status": claim_status,
                "confidence": confidence,
                "evidence": context,
                "recommendation": recommendation
            }
        )

    return results


# ---------------------------------------------------------
# UPLOAD RESUME
# ---------------------------------------------------------

@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...)
):

    global resume_text
    global resume_filename

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Please select a resume file."
        )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

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

        if (
            temp_path
            and os.path.exists(temp_path)
        ):

            try:
                os.remove(temp_path)
            except Exception:
                pass


# ---------------------------------------------------------
# ANALYZE RESUME
# ---------------------------------------------------------

@app.post("/analyze")
def analyze_resume(
    data: JobDescription
):

    if not resume_text:

        raise HTTPException(
            status_code=400,
            detail=(
                "Please upload a resume first "
                "using /upload-resume."
            )
        )

    job_description = (
        data.job_description.strip()
    )

    if not job_description:

        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty."
        )

    # ---------------------------------------------
    # Extract skills
    # ---------------------------------------------

    required_skills = extract_required_skills(
        job_description
    )

    resume_skills = extract_skills(
        resume_text
    )

    # ---------------------------------------------
    # Match skills
    # ---------------------------------------------

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

    # ---------------------------------------------
    # Match percentage
    # ---------------------------------------------

    if required_skills:

        match_percentage = round(
            (
                len(matched_skills)
                / len(required_skills)
            ) * 100,
            2
        )

    else:

        match_percentage = 0.0

    # ---------------------------------------------
    # Evidence analysis
    # ---------------------------------------------

    evidence_analysis = []

    for skill in required_skills:

        evidence = analyze_skill_evidence(
            skill,
            resume_text
        )

        evidence_analysis.append(
            evidence
        )

    # ---------------------------------------------
    # Claim analysis
    # ---------------------------------------------

    claim_analysis = analyze_claims(
        resume_text,
        resume_skills
    )

    # ---------------------------------------------
    # Interview recommendations
    # ---------------------------------------------

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
                    "HTML, CSS, JavaScript and application architecture."
            }

            interview_recommendations.append(
                recommendations.get(
                    skill,
                    f"Learn {skill_title} "
                    "and build a practical project."
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
                    "endpoints, HTTP methods and status codes."
            }

            interview_recommendations.append(
                recommendations.get(
                    skill,
                    f"Prepare practical "
                    f"{skill_title} questions and "
                    "explain your project experience."
                )
            )

    # ---------------------------------------------
    # Message
    # ---------------------------------------------

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

    # ---------------------------------------------
    # Final response
    # ---------------------------------------------

    return {

        "message": message,

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
            interview_recommendations
    }