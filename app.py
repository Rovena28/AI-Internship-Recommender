from flask import Flask, render_template, request
from utils.matcher import match_internships
from utils.llm_engine import generate_explanations, generate_resume_suggestions
from utils.resume_parser import extract_skills
import pdfplumber

app = Flask(__name__)


def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
    return text


@app.route('/', methods=['GET', 'POST'])
def home():
    results = None
    resume_skills = None
    suggestions = None
    data_source = None

    if request.method == 'POST':

        resume_text = request.form.get('resume', '').strip()
        resume_file = request.files.get('resume_file')

        if resume_file and resume_file.filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(resume_file)

        if resume_text:

            resume_skills = extract_skills(resume_text)

            tfidf_results, data_source = match_internships(resume_text)

            # Initialize explanation fields
            i = 0
            while i < len(tfidf_results):
                tfidf_results[i]["reason"] = ""
                tfidf_results[i]["matched_skills"] = []
                tfidf_results[i]["missing_skills"] = []
                i += 1

            if data_source != "none":
                llm_results = generate_explanations(resume_text, tfidf_results)

                if llm_results:
                    j = 0
                    while j < len(tfidf_results):

                        k = 0
                        while k < len(llm_results):

                            if tfidf_results[j]["title"].strip().lower() == \
                               llm_results[k]["title"].strip().lower():

                                tfidf_results[j]["reason"] = llm_results[k].get("reason", "")
                                tfidf_results[j]["matched_skills"] = llm_results[k].get("matched_skills", [])
                                tfidf_results[j]["missing_skills"] = llm_results[k].get("missing_skills", [])

                            k += 1
                        j += 1

            results = tfidf_results
            suggestions = generate_resume_suggestions(resume_text)

    return render_template(
        'index.html',
        results=results,
        resume_skills=resume_skills,
        suggestions=suggestions,
        data_source=data_source
    )


if __name__ == '__main__':
    app.run(debug=False)