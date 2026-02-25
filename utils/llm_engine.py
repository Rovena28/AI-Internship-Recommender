import os
import json
import re
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY not found in .env")

client = genai.Client(api_key=api_key)


def clean_markdown(text):
    text = text.replace("**", "")
    text = text.replace("* ", "- ")
    text = text.replace("*", "")
    return text.strip()


def generate_explanations(resume_text, top_internships):

    if not top_internships:
        return []

    internship_text = ""

    i = 0
    while i < len(top_internships):
        internship_text += f"""
Title: {top_internships[i]['title']}
Description: {top_internships[i]['description']}
"""
        i += 1

    prompt = f"""
You are an AI internship matching assistant speaking directly to the candidate.

The candidate resume:

{resume_text}

Internships:

{internship_text}

For EACH internship:

1. Give a short 1-2 sentence explanation why it matches.
2. Extract matched skills as SHORT technical keywords (1-4 words each).
3. Extract missing skills as SHORT technical keywords (1-4 words each).
4. Do NOT write long paragraphs inside skill lists.
5. Keep tone professional and constructive.
6. Avoid mentioning years of experience or salary.
7. Use "you".

Return ONLY valid JSON:

[
  {{
    "title": "",
    "reason": "",
    "matched_skills": [],
    "missing_skills": []
  }}
]
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if not response.text:
            return []

        text_output = response.text.strip()

        match = re.search(r"\[.*\]", text_output, re.DOTALL)

        if match:
            return json.loads(match.group())

        return []

    except Exception as e:
        print("Gemini Error:", e)
        return []


def generate_resume_suggestions(resume_text):

    prompt = f"""
You are a career advisor.

Resume:

{resume_text}

Provide:
- Three clear improvement suggestions.
- Technical skills to consider adding.
- Missing technical areas.

Rules:
- Use "-" bullets only.
- Do NOT use markdown symbols like **.
- Be concise.
- Use second person ("you").
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        if not response.text:
            return "Unable to generate suggestions at this time."

        clean_text = clean_markdown(response.text)

        return clean_text

    except Exception as e:
        print("Suggestion Error:", e)
        return "Unable to generate suggestions at this time."