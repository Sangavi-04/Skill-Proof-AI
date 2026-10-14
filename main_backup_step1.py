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
    version="1.0.0",
    description="Resume vs Job Description Analysis API"
)


# =========================================================
# GLOBAL RESUME STORAGE
# =========================================================

resume_text = ""
resume_filename = ""


# =========================================================
# SUPPORTED SKILLS
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
        "p ython"
    ],

    "java": [
        "java"
    ],

    "c": [
        "c programming",
        "c language"
    ],

    "html": [
        "html"
    ],

    "css": [
        "css"
    ],

    "javascript": [
        "javascript",
        "java script"
    ],

    "sql": [
        "sql"
    ],

    "postgresql": [
        "postgresql",
        "postgre sql"
    ],

    "mysql": [
        "mysql",
        "my sql"
    ],

    "mongodb": [
        "mongodb",
        "mongo db"
    ],

    "fastapi": [
        "fastapi",
        "fast api",
        "f astapi"
    ],

    "flask": [
        "flask"
    ],

    "django": [
        "django"
    ],

    "git": [
        "git"
    ],

    "github": [
        "github",
        "git hub"
    ],

    "docker": [
        "docker"
    ],

    "aws": [
        "aws",
        "a ws"
    ],

    "azure": [
        "azure"
    ],

    "gcp": [
        "gcp",
        "google cloud platform"
    ],

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

    "react": [
        "react"
    ],

    "node.js": [
        "node.js",
        "node js"
    ],

    "node": [
        "node"
    ],

    "web development": [
        "web development",
        "web-development"
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


# =========================================================
# REST API ALIASES
# =========================================================

REST_API_ALIASES = [
    "rest api",
    "rest apis",
    "restful api",
    "restful apis"
]


# =========================================================
# REQUEST SCHEMA
# =========================================================

class JobDescription(BaseModel):
    job_description: str


# =========================================================
# DISPLAY NAMES
# =========================================================

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


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "Welcome to SkillProof AI",
        "status": "running",
        "version": "1.0.0"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "resume_uploaded": bool(resume_text),
        "resume_filename": resume_filename
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
            detail=(
                "PyPDF2 is not installed. "
                "Run: pip install PyPDF2"
            )
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


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def normalize_text(text: str) -> str:

    if not text:
        return ""

    text = text.lower()

    # PDF extraction artifacts
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

    # Keep useful programming characters
    text = re.sub(
        r"[^a-zA-Z0-9+#./\-\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# PHRASE MATCHING
# =========================================================

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

    return re.search(
        pattern,
        text_n,
        flags=re.IGNORECASE
    ) is not None


# =========================================================
# SKILL PRESENT
# =========================================================

def skill_present(text: str, skill: str) -> bool:

    aliases = SKILL_ALIASES.get(
        skill,
        [skill]
    )

    for alias in aliases:

        if contains_phrase(text, alias):

            return True

    return False


# =========================================================
# REST API PRESENT
# =========================================================

def rest_api_present(text: str) -> bool:

    for alias in REST_API_ALIASES:

        if contains_phrase(text, alias):

            return True

    return False


# =========================================================
# EXTRACT RESUME SKILLS
# =========================================================

def extract_skills(text: str) -> List[str]:

    found = []

    for skill in SKILLS:

        if skill_present(text, skill):

            found.append(skill)

    return found


# =========================================================
# EXTRACT REQUIRED JD SKILLS
# =========================================================

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

    # REST API as one capability
    if rest_api_present(job_description):

        required.append("rest api")

    return required


# =========================================================
# GET LOCAL SKILL CONTEXT
# =========================================================

def get_skill_context(
    resume: str,
    skill: str
) -> str:

    normalized_resume = normalize_text(resume)

    aliases = SKILL_ALIASES.get(
        skill,
        [skill]
    )

    # Try line-based context first
    lines = [
        line.strip()
        for line in normalized_resume.splitlines()
        if line.strip()
    ]

    for i, line in enumerate(lines):

        if any(
            contains_phrase(line, alias)
            for alias in aliases
        ):

            start = max(0, i - 1)

            end = min(
                len(lines),
                i + 2
            )

            return "\n".join(
                lines[start:end]
            )

    # Fallback sentence-based search
    sentences = re.split(
        r"(?<=[.!?])\s+",
        normalized_resume
    )

    for i, sentence in enumerate(sentences):

        if any(
            contains_phrase(sentence, alias)
            for alias in aliases
        ):

            start = max(0, i - 1)

            end = min(
                len(sentences),
                i + 2
            )

            return " ".join(
                sentences[start:end]
            ).strip()

    return (
        f"{skill_display(skill)} "
        "is not found in the resume."
    )


# =========================================================
# ANALYZE SKILL EVIDENCE
# =========================================================

def analyze_skill_evidence(
    skill: str,
    resume: str
) -> Dict[str, Any]:

    context = get_skill_context(
        resume,
        skill
    )

    if context.endswith(
        "is not found in the resume."
    ):

        return {

            "skill": skill_display(skill),

            "status": "Missing",

            "skill_level": "None",

            "evidence_type": "No Evidence",

            "evidence": context,

            "recommendation": (
                f"Learn {skill_display(skill)} "
                "and build a practical project."
            )
        }

    lower_context = context.lower()

    # -----------------------------------------------------
    # LEVEL
    # -----------------------------------------------------

    level = "Unknown"

    if re.search(
        r"\badvanced\b",
        lower_context
    ):

        level = "Advanced"

    elif re.search(
        r"\bintermediate\b",
        lower_context
    ):

        level = "Intermediate"

    elif re.search(
        r"\bbasic(?:s)?\b",
        lower_context
    ):

        level = "Basic"

    # -----------------------------------------------------
    # MACHINE LEARNING
    # -----------------------------------------------------

    if skill == "machine learning":

        ml_indicators = [

            "supervised",
            "unsupervised",
            "preprocessing",
            "model training",
            "evaluation",
            "real-world datasets",
            "predictive models"
        ]

        ml_count = sum(
            1
            for word in ml_indicators
            if word in lower_context
        )

        if ml_count >= 2:

            return {

                "skill": "Machine Learning",

                "status": "Evidence Found",

                "skill_level": "Strong",

                "evidence_type":
                    "Internship / Practical Experience",

                "evidence": context,

                "recommendation": (
                    "Prepare to explain supervised and "
                    "unsupervised learning, preprocessing, "
                    "model training, evaluation and datasets."
                )
            }

    # -----------------------------------------------------
    # CLOUD COMPUTING
    # -----------------------------------------------------

    if skill == "cloud computing":

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

            return {

                "skill": "Cloud Computing",

                "status": "Evidence Found",

                "skill_level": "Strong",

                "evidence_type":
                    "Internship / Practical Experience",

                "evidence": context,

                "recommendation": (
                    "Prepare to explain cloud architecture, "
                    "deployment models, virtualization, "
                    "security and resource management."
                )
            }

    # -----------------------------------------------------
    # AWS
    # -----------------------------------------------------

    if skill == "aws":

        aws_indicators = [

            "ec2",
            "s3",
            "lambda",
            "iam",
            "cloudwatch",
            "aws deployment",
            "aws services",
            "deployed on aws"
        ]

        if any(
            word in lower_context
            for word in aws_indicators
        ):

            if level == "Unknown":

                level = "Intermediate"

            return {

                "skill": "AWS",

                "status": "Evidence Found",

                "skill_level": level,

                "evidence_type":
                    "AWS-Specific Practical Evidence",

                "evidence": context,

                "recommendation": (
                    "Prepare to explain the AWS services "
                    "used, why they were selected and "
                    "how you used them."
                )
            }

    # -----------------------------------------------------
    # PRACTICAL EVIDENCE
    # -----------------------------------------------------

    practical_indicators = [

        "project",
        "internship",
        "experience",
        "developed",
        "built",
        "implemented",
        "worked with",
        "created",
        "deployment",
        "using"
    ]

    practical_count = sum(
        1
        for word in practical_indicators
        if word in lower_context
    )

    if level != "Unknown":

        return {

            "skill": skill_display(skill),

            "status": "Claimed",

            "skill_level": level,

            "evidence_type":
                "Skill Section / Resume Mention",

            "evidence": context,

            "recommendation": (
                f"Be ready to explain your "
                f"{skill_display(skill)} knowledge "
                "with a concrete example."
            )
        }

    if practical_count >= 1:

        return {

            "skill": skill_display(skill),

            "status": "Evidence Found",

            "skill_level": "Unknown",

            "evidence_type":
                "Project / Internship / Experience",

            "evidence": context,

            "recommendation": (
                f"Prepare to explain how "
                f"{skill_display(skill)} was used "
                "and what you personally contributed."
            )
        }

    return {

        "skill": skill_display(skill),

        "status": "Claimed",

        "skill_level": "Unknown",

        "evidence_type":
            "Skill Section / Resume Mention",

        "evidence": context,

        "recommendation": (
            f"Strengthen {skill_display(skill)} "
            "evidence with a practical project "
            "and specific usage details."
        )
    }


# =========================================================
# CLAIM / WEAK CLAIM ANALYSIS
# =========================================================

def analyze_claims(
    resume: str,
    resume_skills: List[str]
) -> List[Dict[str, Any]]:

    results = []

    # -----------------------------------------------------
    # Normal resume skills
    # -----------------------------------------------------

    for skill in resume_skills:

        context = get_skill_context(
            resume,
            skill
        )

        lower_context = context.lower()

        # Explicit level
        if re.search(
            r"\badvanced\b",
            lower_context
        ):

            explicit_level = "Advanced"

        elif re.search(
            r"\bintermediate\b",
            lower_context
        ):

            explicit_level = "Intermediate"

        elif re.search(
            r"\bbasic(?:s)?\b",
            lower_context
        ):

            explicit_level = "Basic"

        else:

            explicit_level = "Unknown"

        # Strong evidence
        strong_evidence = False

        if skill == "machine learning":

            ml_indicators = [

                "supervised",
                "unsupervised",
                "preprocessing",
                "model training",
                "model evaluation",
                "evaluation",
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

        elif skill == "aws":

            aws_indicators = [

                "ec2",
                "s3",
                "lambda",
                "iam",
                "cloudwatch",
                "aws deployment",
                "aws services",
                "deployed on aws"
            ]

            if any(
                word in lower_context
                for word in aws_indicators
            ):

                strong_evidence = True

        # Practical evidence
        practical_indicators = [

            "project",
            "internship",
            "experience",
            "developed",
            "built",
            "implemented",
            "worked with",
            "created",
            "deployment"
        ]

        practical_count = sum(
            1
            for word in practical_indicators
            if word in lower_context
        )

        # Strong claim
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

        # Determine result
        if strong_evidence:

            claim_status = "Strong Evidence"

            confidence = "High"

            recommendation = (
                f"{skill_display(skill)} has strong "
                "practical evidence. Be ready to explain "
                "the exact work performed, tools used "
                "and your contribution."
            )

        elif explicit_level in [
            "Basic",
            "Intermediate",
            "Advanced"
        ]:

            claim_status = "Claimed"

            confidence = "Medium"

            recommendation = (
                f"{skill_display(skill)} is explicitly "
                f"listed as {explicit_level}. Be ready "
                "to demonstrate this level with a "
                "concrete example or project."
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
                "context. Add specific implementation "
                "details or measurable results."
            )

        elif strong_claim:

            claim_status = "Potentially Weak Claim"

            confidence = "Low"

            recommendation = (
                f"{skill_display(skill)} is presented as "
                "a strong skill but supporting practical "
                "evidence is limited. Add a project, "
                "internship or implementation example."
            )

        else:

            claim_status = "Claimed Without Strong Evidence"

            confidence = "Low"

            recommendation = (
                f"{skill_display(skill)} is listed in "
                "the resume, but strong practical "
                "evidence was not found. Add specific "
                "usage or project details."
            )

        results.append({

            "skill": skill_display(skill),

            "claim_status": claim_status,

            "confidence": confidence,

            "evidence": context,

            "recommendation": recommendation
        })

    # -----------------------------------------------------
    # GitHub-only Git evidence
    # -----------------------------------------------------

    if (
        "git" not in resume_skills
        and contains_phrase(resume, "github")
    ):

        github_context = get_skill_context(
            resume,
            "github"
        )

        results.append({

            "skill": "Git",

            "claim_status": "Weak Evidence",

            "confidence": "Low",

            "evidence": (
                "A GitHub profile/link is present, "
                "but this alone does not prove Git proficiency."
            ),

            "recommendation": (
                "Add specific Git usage such as commit, "
                "branch, merge, pull and push experience."
            )
        })

    return results


# =========================================================
# UPLOAD RESUME
# =========================================================

@app.post("/upload-resume")
async def upload_resume(
    file: UploadFile = File(...)
):

    global resume_text
    global resume_filename

    # Check filename
    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Please select a resume file."
        )

    # Check extension
    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension != ".pdf":

        raise HTTPException(
            status_code=400,
            detail="Only PDF resume files are supported."
        )

    # Read file
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

        # Extract PDF text
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

        # Store resume
        resume_text = text

        resume_filename = file.filename

        return {

            "filename": file.filename,

            "message":
                "Resume uploaded successfully!",

            "text": text,

            "resume_uploaded": True
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
    data: JobDescription
):

    # -----------------------------------------------------
    # Check resume
    # -----------------------------------------------------

    if not resume_text:

        raise HTTPException(
            status_code=400,
            detail=(
                "Please upload a resume first "
                "using /upload-resume."
            )
        )

    # -----------------------------------------------------
    # Job description
    # -----------------------------------------------------

    job_description = (
        data.job_description.strip()
    )

    if not job_description:

        raise HTTPException(
            status_code=400,
            detail="Job description cannot be empty."
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
    # Matched / Missing
    # -----------------------------------------------------

    matched_skills = []

    missing_skills = []

    for skill in required_skills:

        if skill in resume_skills:

            matched_skills.append(skill)

        else:

            missing_skills.append(skill)

    # -----------------------------------------------------
    # Match percentage
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Evidence analysis
    # -----------------------------------------------------

    evidence_analysis = [

        analyze_skill_evidence(
            skill,
            resume_text
        )

        for skill in required_skills
    ]

    # -----------------------------------------------------
    # Claim analysis
    # -----------------------------------------------------

    claim_analysis = analyze_claims(
        resume_text,
        resume_skills
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
                    "Learn FastAPI routing, Pydantic "
                    "models and REST API development.",

                "git":
                    "Prepare Git basics: commit, branch, "
                    "merge, pull and push.",

                "docker":
                    "Learn Docker basics and containerize "
                    "one project.",

                "rest api":
                    "Practice REST API methods, status codes, "
                    "request/response handling and API testing."
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
                    "Prepare AWS/cloud concepts and explain "
                    "your actual cloud experience.",

                "machine learning":
                    "Prepare ML concepts, preprocessing, "
                    "model training and evaluation.",

                "rest api":
                    "Be ready to explain REST API design, "
                    "endpoints, HTTP methods and status codes."
            }

            interview_recommendations.append(

                recommendations.get(
                    skill,
                    f"Prepare practical {skill_title} "
                    "questions and explain your project experience."
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
            f"{missing_text}. "
            "We recommend improving these skills "
            "before the interview."
        )

    else:

        message = (

            "Excellent! Your resume contains "
            "all required skills for this "
            "job description."
        )

    # -----------------------------------------------------
    # Final response
    # -----------------------------------------------------

    return {

        "message": message,

        "resume_filename":
            resume_filename,

        "resume_uploaded": True,

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