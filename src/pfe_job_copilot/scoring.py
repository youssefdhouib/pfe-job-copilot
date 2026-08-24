from __future__ import annotations

import unicodedata


POSITIVE_KEYWORDS = {
    "pfe": 30,
    "projet de fin d etudes": 30,
    "stage de fin d etudes": 30,
    "stage fin d etudes": 30,
    "final year internship": 30,
    "end of studies internship": 30,
    "stage": 20,
    "stagiaire": 20,
    "internship": 20,
    "intern": 15,
    "6 mois": 10,
    "six month": 10,
    "bac 5": 10,
    "m2": 10,
    "intelligence artificielle": 25,
    "artificial intelligence": 25,
    "ai engineer": 25,
    "ingenieur ia": 25,
    "machine learning": 18,
    "deep learning": 18,
    "generative ai": 18,
    "genai": 18,
    "llm": 15,
    "large language model": 15,
    "rag": 12,
    "nlp": 12,
    "computer vision": 12,
    "mlops": 12,
    "data science": 12,
    "python": 8,
    "pytorch": 6,
    "tensorflow": 6,
    "hugging face": 6,
    "backend": 6,
    "full stack": 6,
    "fullstack": 6,
    "software engineer": 8,
    "ingenieur logiciel": 8,
}

NEGATIVE_KEYWORDS = {
    "alternance": -35,
    "apprentissage": -35,
    "cdi": -40,
    "senior": -35,
    "staff": -35,
    "principal": -35,
    "lead": -35,
    "manager": -35,
    "commercial": -30,
    "marketing": -30,
    "recrutement": -30,
}

FRANCE_LOCATIONS = (
    "france", "paris", "ile de france", "lyon", "toulouse", "nantes", "lille",
    "grenoble", "bordeaux", "rennes", "montpellier", "sophia antipolis", "nice",
)

INTERNSHIP_TITLE_TERMS = (
    "stage", "stagiaire", "intern", "internship", "pfe", "graduate",
    "working student", "werkstudent",
)
EXCLUDED_TITLE_TERMS = (
    "alternance", "apprentissage", "apprenticeship", "cdi", "director",
    "head of", "lead", "manager", "principal", "senior", "staff",
)
TECHNICAL_TERMS = (
    "ai", "ia", "artificial intelligence", "intelligence artificielle",
    "machine learning", "deep learning", "data", "software", "logiciel",
    "developer", "developpeur", "software engineer", "ingenieur logiciel", "python", "backend",
    "fullstack", "full stack", "cloud", "devops", "mlops", "computer vision",
    "nlp", "llm", "genai", "cyber", "robot",
)


def normalize_for_matching(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join("".join(char if char.isalnum() else " " for char in without_accents).split())


def score_job(title: str, company: str = "", location: str = "", description: str = "") -> int:
    text = normalize_for_matching(f"{title} {company} {location} {description}")
    score = sum(weight for keyword, weight in POSITIVE_KEYWORDS.items() if keyword in text)
    score += sum(weight for keyword, weight in NEGATIVE_KEYWORDS.items() if keyword in text)
    if any(city in text for city in FRANCE_LOCATIONS):
        score += 10
    return min(max(score, 0), 100)


def is_target_internship(title: str, company: str = "", location: str = "", description: str = "") -> bool:
    normalized_title = normalize_for_matching(title)
    text = normalize_for_matching(f"{title} {company} {location} {description}")
    padded_title = f" {normalized_title} "
    return (
        any(f" {term} " in padded_title for term in INTERNSHIP_TITLE_TERMS)
        and not any(f" {term} " in padded_title for term in EXCLUDED_TITLE_TERMS)
        and any(f" {term} " in f" {text} " for term in TECHNICAL_TERMS)
        and score_job(title, company, location, description) >= 25
    )
