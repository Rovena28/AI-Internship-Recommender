import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from utils.resume_parser import extract_skills
from utils.api_fetcher import fetch_from_api

model = SentenceTransformer("all-MiniLM-L6-v2")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_internships():
    file_path = os.path.join(BASE_DIR, "internships.json")
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def skill_overlap_score(resume_text, internship_text):
    resume_skills = set(extract_skills(resume_text))
    internship_skills = set(extract_skills(internship_text))

    if len(internship_skills) == 0:
        return 0

    overlap = resume_skills.intersection(internship_skills)
    return len(overlap) / len(internship_skills)


def normalize_title(title):
    title = title.lower()
    title = title.split("-")[0]
    title = title.split("|")[0]
    return title.strip()


def match_internships(resume_text, top_n=5):

    internships = fetch_from_api()
    data_source = "live"

    if not internships:
        internships = load_internships()
        data_source = "demo"

    if len(internships) == 0:
        return [], "none"

    descriptions = []

    i = 0
    while i < len(internships):
        desc = internships[i]["description"][:500]
        combined_text = internships[i]["title"] + " " + desc
        descriptions.append(combined_text)
        i += 1

    resume_embedding = model.encode([resume_text.strip()])
    internship_embeddings = model.encode(descriptions)

    semantic_scores = cosine_similarity(
        resume_embedding,
        internship_embeddings
    ).flatten()

    results = []

    j = 0
    while j < len(internships):

        semantic_score = semantic_scores[j]

        skill_score = skill_overlap_score(
            resume_text,
            internships[j]["description"]
        )

        # Hybrid scoring (semantic weighted higher)
        final_score = (0.7 * semantic_score) + (0.3 * skill_score)

        results.append({
            "title": internships[j]["title"],
            "description": internships[j]["description"],
            "location": internships[j].get("location", "N/A"),
            "duration": internships[j].get("duration", "N/A"),
            "target_candidates": internships[j].get("target_candidates", "N/A"),
            "score": round(final_score * 100, 2)
        })

        j += 1

    results.sort(key=lambda x: x["score"], reverse=True)

    unique_results = []
    seen_titles = set()

    k = 0
    while k < len(results):

        base_title = normalize_title(results[k]["title"])

        if base_title not in seen_titles:
            unique_results.append(results[k])
            seen_titles.add(base_title)

        k += 1

        if len(unique_results) == top_n:
            break

    return unique_results, data_source