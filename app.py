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
    status_message = None

    if request.method == 'POST':

        resume_text = request.form.get('resume', '').strip()
        resume_file = request.files.get('resume_file')

        if resume_file and resume_file.filename.lower().endswith('.pdf'):
            resume_text = extract_text_from_pdf(resume_file)

        if resume_text:

            resume_skills = extract_skills(resume_text)

            matched_results, data_source = match_internships(resume_text)

            if len(matched_results) == 0:
                results = []
                data_source = "none"
            else:

                # Initialize explanation fields
                i = 0
                while i < len(matched_results):
                    matched_results[i]["reason"] = ""
                    matched_results[i]["matched_skills"] = []
                    matched_results[i]["missing_skills"] = []
                    i += 1

               
                llm_results = generate_explanations(resume_text, matched_results)

                if llm_results:
                    j = 0
                    while j < len(matched_results):

                        k = 0
                        while k < len(llm_results):

                            if matched_results[j]["title"].strip().lower() == \
                               llm_results[k]["title"].strip().lower():

                                matched_results[j]["reason"] = llm_results[k].get("reason", "")
                                matched_results[j]["matched_skills"] = llm_results[k].get("matched_skills", [])
                                matched_results[j]["missing_skills"] = llm_results[k].get("missing_skills", [])

                            k += 1
                        j += 1

                results = matched_results

            suggestions = generate_resume_suggestions(resume_text)

   
    if data_source == "live":
        status_message = "Showing live internships from API."
    elif data_source == "demo":
        status_message = "No live internship data available. Displaying fallback data."
    elif data_source == "none":
        status_message = "No internships available at the moment."

    return render_template(
        'index.html',
        results=results,
        resume_skills=resume_skills,
        suggestions=suggestions,
        data_source=data_source,
        status_message=status_message
    )


if __name__ == '__main__':
    app.run(debug=False)