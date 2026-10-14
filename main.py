import io
import json
import re
import uuid
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from PyPDF2 import PdfReader

APP_VERSION = "2.5.0"
DATA_FILE = Path("resumes.json")

app = FastAPI(
title="SkillProof AI",
version=APP_VERSION,
description="AI-assisted Resume vs Job Description Analyzer",
)

resumes: Dict = {}

def load_resumes() -> Dict:
if not DATA_FILE.exists():
return {}

```
try:
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data if isinstance(data, dict) else {}

except Exception:
    return {}
```

def save_resumes() -> None:
with open(DATA_FILE, "w", encoding="utf-8") as file:
json.dump(resumes, file, indent=2, ensure_ascii=False)

resumes = load_resumes()

class AnalyzeRequest(BaseModel):
resume_id: str
job_description: str

def extract_pdf_text(pdf_bytes: bytes) -> str:
try:
reader = PdfReader(io.BytesIO(pdf_bytes))

```
    pages = []

    for page in reader.pages:
        pages.append(page.extract_text() or "")

    text = "\n".join(pages).strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF."
        )

    return text

except HTTPException:
    raise

except Exception as exc:
    raise HTTPException(
        status_code=400,
        detail=f"Could not read PDF: {str(exc)}"
    )
```

def normalize_text(text: str) -> str:
text = text.lower()

```
text = text.replace("\u200b", "")
text = text.replace("\ufeff", "")
text = text.replace("\xa0", " ")

text = re.sub(r"\s+", " ", text)

return text.strip()
```

def contains_phrase(text: str, phrase: str) -> bool:
if not text or not phrase:
return False

```
text_lower = normalize_text(text)
phrase_lower = normalize_text(phrase)

# Normal match
if phrase_lower in text_lower:
    return True

# Match PDF-extracted text with spaces between characters.
# Examples:
# P ython -> Python
# A WS -> AWS
# D ocker -> Docker
# H TML -> HTML
# Web De velopment -> Web Development

pattern = r"\s*".join(
    re.escape(char)
    for char in phrase_lower
    if not char.isspace()
)

if not pattern:
    return False

return re.search(
    pattern,
    text_lower,
    flags=re.IGNORECASE
) is not None
```

SKILL_ALIASES = {
"python": [
"python"
],
"fastapi": [
"fastapi",
"fast api"
],
"postgresql": [
"postgresql",
"postgres sql",
"postgres"
],
"sql": [
"sql"
],
"git": [
"git",
"github"
],
"docker": [
"docker"
],
"aws": [
"aws",
"amazon web services"
],
"rest api": [
"rest api",
"restful api",
"restful"
],
"machine learning": [
"machine learning",
"machine-learning"
],
"web development": [
"web development",
"web developer"
],
}

def find_skill(text: str, skill: str) -> bool:
aliases = SKILL_ALIASES.get(skill, [skill])

```
for alias in aliases:
    if contains_phrase(text, alias):
        return True

return False
```

def find_evidence(text: str, skill: str) -> str:
aliases = SKILL_ALIASES.get(skill, [skill])

```
for line in text.splitlines():
    line = line.strip()

    if not line:
        continue

    for alias in aliases:
        if contains_phrase(line, alias):
            return line[:250]

normalized = normalize_text(text)

for alias in aliases:
    normalized_alias = normalize_text(alias)

    if normalized_alias in normalized:
        position = normalized.find(normalized_alias)

        start = max(0, position - 80)
        end = min(
            len(normalized),
            position + len(normalized_alias) + 150
        )

        return normalized[start:end]

return ""
```

def calculate_score(
matched_skills: List[str],
missing_skills: List[str],
preferred_matches: List[str],
) -> int:

```
total_required = (
    len(matched_skills) +
    len(missing_skills)
)

if total_required == 0:
    return 0

required_score = (
    len(matched_skills) /
    total_required
) * 90

preferred_score = min(
    len(preferred_matches) * 5,
    10
)

return min(
    round(required_score + preferred_score),
    100
)
```

@app.get("/health")
def health():
return {
"status": "healthy",
"version": APP_VERSION
}

@app.post("/upload-resume")
async def upload_resume(
file: UploadFile = File(...)
):

```
if not file.filename:
    raise HTTPException(
        status_code=400,
        detail="Filename is required."
    )

if not file.filename.lower().endswith(".pdf"):
    raise HTTPException(
        status_code=400,
        detail="Only PDF files are supported."
    )

pdf_bytes = await file.read()

if not pdf_bytes:
    raise HTTPException(
        status_code=400,
        detail="Uploaded PDF is empty."
    )

text = extract_pdf_text(pdf_bytes)

resume_id = str(uuid.uuid4())

resumes[resume_id] = {
    "resume_id": resume_id,
    "filename": file.filename,
    "text": text,
    "text_length": len(text)
}

save_resumes()

return {
    "message": "Resume uploaded successfully.",
    "resume_id": resume_id,
    "filename": file.filename,
    "text_length": len(text)
}
```

@app.post("/analyze")
def analyze_resume(request: AnalyzeRequest):

```
if request.resume_id not in resumes:
    raise HTTPException(
        status_code=404,
        detail="Resume ID not found."
    )

if not request.job_description.strip():
    raise HTTPException(
        status_code=400,
        detail="Job description cannot be empty."
    )

resume_text = resumes[
    request.resume_id
]["text"]

required_skills = [
    "python",
    "fastapi",
    "postgresql",
    "sql",
    "git",
    "docker",
    "aws",
    "rest api",
]

preferred_skills = [
    "machine learning",
    "web development",
]

matched_skills = []
missing_skills = []
preferred_matches = []

for skill in required_skills:

    if find_skill(resume_text, skill):
        matched_skills.append(skill)
    else:
        missing_skills.append(skill)

for skill in preferred_skills:

    if find_skill(resume_text, skill):
        preferred_matches.append(skill)

score = calculate_score(
    matched_skills,
    missing_skills,
    preferred_matches
)

evidence = {}

for skill in matched_skills:
    evidence[skill] = find_evidence(
        resume_text,
        skill
    )

for skill in preferred_matches:
    evidence[skill] = find_evidence(
        resume_text,
        skill
    )

if score >= 80:
    recommendation = "Strong Match"
elif score >= 60:
    recommendation = "Good Match"
elif score >= 40:
    recommendation = "Partial Match"
else:
    recommendation = "Low Match"

return {
    "resume_id": request.resume_id,
    "filename": resumes[
        request.resume_id
    ]["filename"],
    "score": score,
    "recommendation": recommendation,
    "matched_skills": matched_skills,
    "missing_skills": missing_skills,
    "preferred_matches": preferred_matches,
    "evidence": evidence,
    "summary": {
        "required_skills_total": len(required_skills),
        "required_skills_matched": len(matched_skills),
        "required_skills_missing": len(missing_skills),
        "preferred_skills_matched": len(preferred_matches)
    },
    "version": APP_VERSION
}
```

@app.get("/resumes")
def list_resumes():

```
result = []

for resume_id, resume in resumes.items():
    result.append({
        "resume_id": resume_id,
        "filename": resume.get("filename"),
        "text_length": resume.get("text_length")
    })

return {
    "count": len(result),
    "resumes": result
}
```

@app.get("/resumes/{resume_id}")
def get_resume(resume_id: str):

```
if resume_id not in resumes:
    raise HTTPException(
        status_code=404,
        detail="Resume ID not found."
    )

resume = resumes[resume_id]

return {
    "resume_id": resume_id,
    "filename": resume.get("filename"),
    "text_length": resume.get("text_length"),
    "text": resume.get("text")
}
