import re
import string

SKILLS_DB = {
    "Programming": [
        "python", "java", "c", "c++", "javascript", "typescript",
        "go", "r", "matlab"
    ],
    "Web_Frontend": [
        "html", "css", "react", "angular", "vue",
        "bootstrap", "tailwind", "redux"
    ],
    "Web_Backend": [
        "flask", "django", "node.js", "express",
        "spring boot", "rest api", "graphql"
    ],
    "Databases": [
        "sql", "mysql", "postgresql", "mongodb",
        "firebase", "redis", "oracle",
        "database design"
    ],
    "Data_Science": [
        "pandas", "numpy", "matplotlib", "seaborn",
        "data analysis", "data visualization",
        "statistics", "probability",
        "exploratory data analysis"
    ],
    "AI_ML_Core": [
        "machine learning", "deep learning",
        "artificial intelligence", "nlp",
        "computer vision", "time series",
        "reinforcement learning"
    ],
    "AI_ML_Libraries": [
        "scikit-learn", "tensorflow", "pytorch",
        "keras", "xgboost", "lightgbm",
        "opencv", "nltk", "spacy",
        "transformers"
    ],
    "ML_Concepts": [
        "regression", "classification", "clustering",
        "decision trees", "random forest",
        "support vector machine",
        "k-means", "knn",
        "feature engineering",
        "model evaluation",
        "cross validation",
        "hyperparameter tuning"
    ],
    "Cloud_DevOps": [
        "aws", "azure", "gcp",
        "docker", "kubernetes",
        "ci/cd", "git", "github",
        "linux", "bash"
    ],
    "APIs_and_Systems": [
        "apis", "rest", "json", "jwt",
        "oauth", "microservices",
        "system design"
    ],
    "AI_Modern_Tech": [
        "llm", "large language models",
        "bert", "sentence embeddings",
        "vector database", "faiss",
        "prompt engineering"
    ]
}

ALL_SKILLS = [
    skill
    for category in SKILLS_DB.values()
    for skill in category
]


def clean_text(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text


def extract_skills(text):
    text = clean_text(text)
    found_skills = set()

    i = 0
    while i < len(ALL_SKILLS):
        skill = ALL_SKILLS[i]
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text):
            found_skills.add(skill)
        i += 1

    return list(found_skills)