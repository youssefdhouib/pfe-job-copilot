import unittest

from pfe_job_copilot.deadlines import extract_application_deadline


class DeadlineTests(unittest.TestCase):
    def test_extracts_explicit_french_deadline(self) -> None:
        self.assertEqual(
            extract_application_deadline("Date limite de candidature : 15/02/2027"),
            "2027-02-15",
        )

    def test_extracts_explicit_english_deadline(self) -> None:
        self.assertEqual(
            extract_application_deadline("Application deadline: 2027-03-01"),
            "2027-03-01",
        )

    def test_ignores_unlabelled_and_invalid_dates(self) -> None:
        self.assertIsNone(extract_application_deadline("Internship starts 2027-03-01"))
        self.assertIsNone(extract_application_deadline("Apply by 31/02/2027"))


if __name__ == "__main__":
    unittest.main()
