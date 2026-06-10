from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import tempfile
import json
import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# -----------------------------
# Gemini Configuration
# -----------------------------

GEMINI_API_KEY = ""

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

# -----------------------------
# FastAPI App
# -----------------------------

app = FastAPI()


class CodeInput(BaseModel):
    code: str


# -----------------------------
# AI Review Function
# -----------------------------

def get_ai_review(code, issues):

    prompt = f"""
You are a senior Python developer.

Analyze this code.

CODE:
{code}

ISSUES:
{issues}

Return ONLY valid JSON.

Format:

{{
    "summary": "short summary",
    "fixes": "list of fixes",
    "corrected_code": "full corrected python code"
}}

Do not return markdown.
Do not use ```python.
Return JSON only.
"""

    response = model.generate_content(prompt)

    return response.text

# -----------------------------
# Health Check
# -----------------------------

@app.get("/")
def home():
    return {
        "message": "AI Intelligent Code Reviewer Running"
    }


# -----------------------------
# Review Endpoint
# -----------------------------

@app.post("/review")
def review_code(data: CodeInput):

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".py"
    ) as temp:

        temp.write(data.code.encode())
        temp_path = temp.name

    result = subprocess.run(
        [
            "pylint",
            temp_path,
            "--output-format=json",
            "--disable=all",
            "--enable=E,F,W,C"
        ],
        capture_output=True,
        text=True
    )

    try:
        issues = json.loads(result.stdout)

    except Exception:
        issues = []

    # -----------------------------
    # Remove noisy convention issues
    # -----------------------------

    filtered_issues = []

    for issue in issues:

        if issue.get("type") == "convention":
            continue

        filtered_issues.append(
            {
                "type": issue.get("type"),
                "line": issue.get("line"),
                "message": issue.get("message")
            }
        )

    issues = filtered_issues

    # -----------------------------
    # Score Calculation
    # -----------------------------

    error_count = sum(
        1 for issue in issues
        if issue.get("type") == "error"
    )

    score = max(10 - (error_count * 2), 1)

    # -----------------------------
    # AI Review
    # -----------------------------

    ai_response = get_ai_review(
    data.code,
    json.dumps(issues, indent=2)
)

    try:
        ai_review = json.loads(ai_response)

    except Exception:

        ai_review = {
        "summary": "Unable to parse AI response.",
        "fixes": "",
        "corrected_code": ""
    }

    # -----------------------------
    # Response
    # -----------------------------

    return {
    "score": score,
    "issues": issues,
    "summary": ai_review.get("summary", ""),
    "fixes": ai_review.get("fixes", ""),
    "corrected_code": ai_review.get("corrected_code", "")
}