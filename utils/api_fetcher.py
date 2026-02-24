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

CACHE_DURATION = 3600          # 1 hour cache
MAX_JOB_AGE_DAYS = 14          # Only internships from last 14 days


# Strong tech keywords (positive filter)
TECH_KEYWORDS = [
    "software", "developer", "engineer",
    "programmer", "python", "java", "c++",
    "react", "node", "web", "application",
    "machine learning", "ai", "data",
    "backend", "frontend", "full stack",
    "cloud", "aws", "azure", "cyber",
    "devops", "database", "testing",
    "qa", "automation", "iot",
    "embedded", "android", "ios",
    "ui", "ux"
]

# Explicit non-tech rejection list
NON_TECH_KEYWORDS = [
    "finance", "accounting", "hr", "human resource",
    "marketing", "sales", "mba", "recruitment",
    "talent acquisition", "operations",
    "copywriting", "content", "seo",
    "outreach", "coordinator"
]


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
        job_date = datetime.strptime(created_date_str, "%Y-%m-%dT%H:%M:%SZ")
        job_date = job_date.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - job_date) <= timedelta(days=days)
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


def is_tech_internship(title, description):
    text = (title + " " + description).lower()

    # Reject non-tech first
    i = 0
    while i < len(NON_TECH_KEYWORDS):
        if NON_TECH_KEYWORDS[i] in text:
            return False
        i += 1

    # Accept only strong tech signals
    j = 0
    while j < len(TECH_KEYWORDS):
        if TECH_KEYWORDS[j] in text:
            return True
        j += 1

    return False


def is_generic_title(title):
    title_lower = title.lower().strip()

    if title_lower in ["intern", "summer intern"]:
        return True

    if len(title_lower.split()) <= 1:
        return True

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

    print("---- Adzuna Fetch Started ----")

    if not APP_ID or not APP_KEY:
        print("API keys missing in .env")
        return []

    # Use cache if still valid
    if is_cache_valid():
        print("Using cached internships")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": 25,
        "what": "software intern OR developer intern OR data intern OR AI intern",
        "where": "India"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        print("Status Code:", response.status_code)

        if response.status_code != 200:
            print("API returned non-200 status")
            return []

        data = response.json()
        print("Total count from API:", data.get("count"))
        print("Results returned:", len(data.get("results", [])))

    except Exception as e:
        print("API Request Error:", e)
        return []

    internships = []
    seen_titles = set()
    results_list = data.get("results", [])

    i = 0
    while i < len(results_list):
        job = results_list[i]

        title = job.get("title", "")
        description = job.get("description", "")
        created = job.get("created", "")

        #  Freshness filter
        if not is_recent(created):
            i += 1
            continue

        #  Reject senior roles
        if not is_valid_internship(title, description):
            i += 1
            continue

        # Reject generic titles
        if is_generic_title(title):
            i += 1
            continue

        #  Strict tech filtering
        if not is_tech_internship(title, description):
            i += 1
            continue

        # Remove duplicates
        clean_title = normalize_title(title)
        if clean_title in seen_titles:
            i += 1
            continue

        seen_titles.add(clean_title)

        internships.append({
            "title": title,
            "description": description,
            "location": job.get("location", {}).get("display_name", "N/A"),
            "duration": "Not specified",
            "target_candidates": "Open to students",
            "domain": "Technology"
        })

        i += 1

    # Cache only if results exist
    if len(internships) > 0:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(internships, f, indent=4)
        print("Cached", len(internships), "clean tech internships.")
    else:
        print("No valid internships after filtering.")

    print("---- Adzuna Fetch Ended ----")

    return internships