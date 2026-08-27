from __future__ import annotations

import unicodedata


PFE_TERMS = (
    "pfe", "projet de fin d etudes", "stage de fin d etudes",
    "stage fin d etudes", "final year internship", "end of studies internship",
)
AI_TERMS = (
    "intelligence artificielle", "artificial intelligence", "ai engineer",
    "ingenieur ia", "machine learning", "deep learning", "generative ai",
    "ia generative", "genai", "llm", "large language model",
)
SOFTWARE_TERMS = (
    "software", "logiciel", "developer", "developpeur", "backend",
    "full stack", "fullstack", "cloud", "devops",
)
DATA_TERMS = ("data science", "data scientist", "data engineer")
SPECIALTY_GROUPS = (
    ("generative ai", "ia generative", "genai", "llm", "large language model", "rag"),
    ("nlp", "natural language processing"),
    ("computer vision", "vision par ordinateur"),
    ("mlops",),
)
SKILL_TERMS = ("python", "pytorch", "tensorflow", "hugging face")
LEVEL_TERMS = ("6 mois", "six month", "bac 5", "master 2", "m2")
NEGATIVE_TITLE_TERMS = (
    "alternance", "apprentissage", "apprenticeship", "cdi", "senior", "staff",
    "principal", "lead", "manager", "director", "head of", "commercial", "marketing",
)

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


def _contains(text: str, terms: tuple[str, ...]) -> bool:
    padded = f" {text} "
    return any(f" {term} " in padded for term in terms)


def score_job(title: str, company: str = "", location: str = "", description: str = "") -> int:
    normalized_title = normalize_for_matching(title)
    text = normalize_for_matching(f"{title} {company} {location} {description}")
    normalized_location = normalize_for_matching(location)

    if _contains(normalized_title, PFE_TERMS) or _contains(text, PFE_TERMS):
        score = 30
    elif _contains(normalized_title, INTERNSHIP_TITLE_TERMS):
        score = 22
    else:
        score = 0

    if _contains(normalized_title, AI_TERMS):
        score += 30
    elif _contains(text, AI_TERMS):
        score += 24
    elif _contains(normalized_title, DATA_TERMS):
        score += 20
    elif _contains(text, DATA_TERMS):
        score += 16
    elif _contains(normalized_title, SOFTWARE_TERMS):
        score += 16
    elif _contains(text, SOFTWARE_TERMS):
        score += 12

    score += min(12, 4 * sum(_contains(text, group) for group in SPECIALTY_GROUPS))
    score += min(8, 2 * sum(_contains(text, (skill,)) for skill in SKILL_TERMS))
    if _contains(text, LEVEL_TERMS):
        score += 8
    if any(city in normalized_location for city in FRANCE_LOCATIONS):
        score += 10
    if _contains(normalized_title, NEGATIVE_TITLE_TERMS):
        score -= 45
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
