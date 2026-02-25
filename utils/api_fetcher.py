import os
import json
import time
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_FILE = os.path.join(BASE_DIR, "api_internships.json")

CACHE_DURATION = 3600
MAX_JOB_AGE_DAYS = 30


def is_cache_valid():
    if not os.path.exists(CACHE_FILE):
        return False

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if len(data) == 0:
        return False

    file_time = os.path.getmtime(CACHE_FILE)
    current_time = time.time()

    return (current_time - file_time) < CACHE_DURATION


def is_recent(created_date_str, days=MAX_JOB_AGE_DAYS):
    try:
        internship_date = datetime.strptime(created_date_str, "%Y-%m-%dT%H:%M:%SZ")
        internship_date = internship_date.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - internship_date) <= timedelta(days=days)
    except:
        return False


def is_valid_internship(title, description):
    text = (title + " " + description).lower()

    reject_keywords = [
        "senior", "manager", "lead", "principal",
        "3 years", "4 years", "5 years",
        "experience required", "minimum experience",
        "internal"
    ]

    i = 0
    while i < len(reject_keywords):
        if reject_keywords[i] in text:
            return False
        i += 1

    return True


def is_generic_title(title):
    title_lower = title.lower().strip()

    if title_lower in ["intern", "summer intern"]:
        return True

    if len(title_lower.split()) <= 1:
        return True

    return False


def is_tech_internship(title, description):
    text = (title + " " + description).lower()

    tech_keywords = [
        "software", "developer", "data", "machine learning",
        "ai", "cloud", "backend", "frontend",
        "cybersecurity", "python", "java",
        "web", "full stack", "devops",
        "mobile", "android", "react",
        "node", "sql", "analytics"
    ]

    i = 0
    while i < len(tech_keywords):
        if tech_keywords[i] in text:
            return True
        i += 1

    return False


def normalize_title(title):
    title = title.lower()
    remove_words = ["internship", "intern", "program", "role", "position"]

    i = 0
    while i < len(remove_words):
        title = title.replace(remove_words[i], "")
        i += 1

    return title.strip()


def fetch_from_api(search_query=None):

    print("---- Adzuna Internship Fetch Started ----")

    if not APP_ID or not APP_KEY:
        print("API keys missing in .env")
        return []

    if is_cache_valid():
        print("Using cached internships")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": 25,
        "what": "internship",
        "where": "India"
    }

    try:
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            print("API failed. Using fallback cache if available.")
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            return []

        data = response.json()

    except Exception:
        print("Exception occurred. Using fallback cache if available.")
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    internships = []
    seen_titles = set()
    results_list = data.get("results", [])

    i = 0
    while i < len(results_list):

        internship = results_list[i]

        title = internship.get("title", "")
        description = internship.get("description", "")
        created = internship.get("created", "")

        if not is_recent(created):
            i += 1
            continue

        if not is_valid_internship(title, description):
            i += 1
            continue

        if is_generic_title(title):
            i += 1
            continue

        if not is_tech_internship(title, description):
            i += 1
            continue

        clean_title = normalize_title(title)

        if clean_title in seen_titles:
            i += 1
            continue

        seen_titles.add(clean_title)

        internships.append({
            "title": title,
            "description": description,
            "location": internship.get("location", {}).get("display_name", "N/A"),
            "duration": "Not specified",
            "target_candidates": "Open to students",
            "domain": "Tech"
        })

        i += 1

    if len(internships) > 0:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(internships, f, indent=4)

    print("---- Adzuna Internship Fetch Ended ----")

    return internships