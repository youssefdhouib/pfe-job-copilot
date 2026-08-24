from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SearchProfile:
    locations: tuple[str, ...]
    queries: tuple[str, ...]


DEFAULT_PROFILE = SearchProfile(
    locations=(
        "France",
        "Paris",
        "Toulouse",
        "Lyon",
        "Grenoble",
        "Sophia Antipolis",
        "Bordeaux",
        "Nantes",
        "Lille",
        "Rennes",
        "Montpellier",
    ),
    queries=(
        "stage PFE intelligence artificielle",
        "stage de fin d'études IA",
        "stage machine learning",
        "stage IA générative",
        "stage GenAI LLM",
        "stage NLP computer vision",
        "stage MLOps",
        "stage data scientist",
        "stage ingénieur logiciel IA",
        "stage développeur Python IA",
        "AI engineer internship",
        "machine learning engineer internship",
        "generative AI internship",
        "LLM engineer internship",
        "software engineering internship AI",
        "research engineer internship AI",
    ),
)
