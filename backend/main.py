from fastapi import FastAPI
from pydantic import BaseModel
import tempfile
import subprocess
import json
import re
import os

from dotenv import load_dotenv
import google.generativeai as genai

# -----------------------------------
# Environment
# -----------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    "gemini-2.5-flash"
)

# -----------------------------------
# FastAPI
# -----------------------------------

app = FastAPI()


class CodeInput(BaseModel):
    code: str
    language: str


# -----------------------------------
# Gemini Review
# -----------------------------------

def get_ai_review(code, issues, language):

    prompt = f"""
You are an expert {language} software engineer.

Review this code.

Language:
{language}

Code:
{code}

Issues:
{issues}

Return ONLY valid JSON.

Example:

{{
    "summary": "Short summary",
    "fixes": "Suggested fixes",
    "corrected_code": "Corrected code"
}}

Do not use markdown.
Do not use ```json.
Return JSON only.
"""

    response = model.generate_content(
        prompt
    )

    return response.text


# -----------------------------------
# Python Static Analysis
# -----------------------------------

def run_pylint(code):

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".py",
        mode="w",
        encoding="utf-8"
    ) as temp:

        temp.write(code)

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

        issues = json.loads(
            result.stdout
        )

    except Exception:

        issues = []

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

    error_count = sum(
        1
        for issue in filtered_issues
        if issue.get("type") == "error"
    )

    score = max(
        10 - (error_count * 2),
        1
    )

    return score, filtered_issues


# -----------------------------------
# Home
# -----------------------------------

@app.get("/")
def home():

    return {
        "message":
        "AI Multi-Language Code Reviewer Running"
    }


# -----------------------------------
# Review Endpoint
# -----------------------------------

@app.post("/review")
def review_code(data: CodeInput):

    language = data.language

    if language == "Python":

        score, issues = run_pylint(
            data.code
        )

    else:

        score = 10

        issues = []

    try:

        ai_response = get_ai_review(
            data.code,
            json.dumps(
                issues,
                indent=2
            ),
            language
        )

        ai_response = ai_response.replace(
            "```json",
            ""
        )

        ai_response = ai_response.replace(
            "```",
            ""
        )

        json_match = re.search(
            r"\{.*\}",
            ai_response,
            re.DOTALL
        )

        if json_match:

            ai_review = json.loads(
                json_match.group()
            )

        else:

            raise Exception(
                "No JSON found"
            )

    except Exception as e:

        print(
            "Gemini Error:",
            str(e)
        )

        ai_review = {
            "summary":
            "AI review unavailable.",

            "fixes":
            "Unable to generate fixes.",

            "corrected_code":
            data.code
        }

    return {

        "score": score,

        "issues": issues,

        "summary":
        ai_review.get(
            "summary",
            ""
        ),

        "fixes":
        ai_review.get(
            "fixes",
            ""
        ),

        "corrected_code":
        ai_review.get(
            "corrected_code",
            data.code
        )
    }