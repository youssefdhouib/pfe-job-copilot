import unittest

from pfe_job_copilot.scoring import is_target_internship, normalize_for_matching, score_job


class ScoringTests(unittest.TestCase):
    def test_matching_normalizes_french_accents_and_punctuation(self) -> None:
        self.assertEqual(
            normalize_for_matching("Stage de fin d’études – IA Générative"),
            "stage de fin d etudes ia generative",
        )

    def test_pfe_ai_job_scores_highly(self) -> None:
        score = score_job(
            "Stage de fin d’études - Ingénieur IA Générative",
            location="Paris, France",
            description="PFE de 6 mois en Python, machine learning, LLM, RAG et Hugging Face.",
        )
        self.assertGreaterEqual(score, 100)

    def test_score_is_capped_at_100(self) -> None:
        score = score_job(
            "Stage PFE AI Engineer Internship",
            location="Paris, France",
            description="Python machine learning deep learning LLM RAG NLP MLOps computer vision.",
        )
        self.assertEqual(score, 100)

    def test_senior_cdi_is_downgraded(self) -> None:
        score = score_job(
            "Senior AI Engineer CDI",
            location="Paris, France",
            description="Machine learning and Python. Five years of experience required.",
        )
        self.assertLess(score, 40)

    def test_software_internship_with_ai_content_is_kept(self) -> None:
        score = score_job(
            "Software Engineer Internship",
            location="Toulouse",
            description="Build a Python backend for generative AI and LLM applications.",
        )
        self.assertGreaterEqual(score, 60)

    def test_target_gate_keeps_technical_internship(self) -> None:
        self.assertTrue(is_target_internship(
            "Software Engineer Internship",
            location="Paris",
            description="Build Python services for machine learning products.",
        ))

    def test_target_gate_rejects_senior_and_apprenticeship_titles(self) -> None:
        self.assertFalse(is_target_internship(
            "Senior Machine Learning Engineer",
            description="AI Python LLM platform.",
        ))
        self.assertFalse(is_target_internship(
            "Data Engineer Apprenticeship",
            description="Python and machine learning.",
        ))


if __name__ == "__main__":
    unittest.main()
