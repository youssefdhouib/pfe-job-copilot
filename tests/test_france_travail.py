import os
import unittest
from unittest.mock import Mock, patch

from pfe_job_copilot.collectors.france_travail import FranceTravailCollector


class FranceTravailCollectorTests(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_requires_api_credentials(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "FRANCE_TRAVAIL_CLIENT_ID"):
            list(FranceTravailCollector().search("stage IA", "France", 5))

    @patch.dict(
        os.environ,
        {
            "FRANCE_TRAVAIL_CLIENT_ID": "client-id",
            "FRANCE_TRAVAIL_CLIENT_SECRET": "client-secret",
        },
        clear=True,
    )
    @patch("pfe_job_copilot.collectors.france_travail.httpx.get")
    @patch("pfe_job_copilot.collectors.france_travail.httpx.post")
    def test_maps_api_results_to_jobs(self, post: Mock, get: Mock) -> None:
        post_response = Mock()
        post_response.is_error = False
        post_response.raise_for_status.return_value = None
        post_response.json.return_value = {"access_token": "token"}
        post.return_value = post_response

        get_response = Mock()
        get_response.raise_for_status.return_value = None
        get_response.json.return_value = {
            "resultats": [
                {
                    "id": "123ABC",
                    "intitule": "Stage PFE Intelligence Artificielle",
                    "description": "Machine learning et Python",
                    "entreprise": {"nom": "Example"},
                    "lieuTravail": {"libelle": "75 - Paris"},
                    "origineOffre": {},
                    "contact": {},
                }
            ]
        }
        get.return_value = get_response

        jobs = list(FranceTravailCollector().search("stage IA", "France", 10))

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "Stage PFE Intelligence Artificielle")
        self.assertEqual(jobs[0].company, "Example")
        self.assertEqual(
            jobs[0].url,
            "https://candidat.francetravail.fr/offres/recherche/detail/123ABC",
        )
        self.assertEqual(get.call_args.kwargs["headers"]["Authorization"], "Bearer token")

    @patch.dict(
        os.environ,
        {
            "FRANCE_TRAVAIL_CLIENT_ID": "client-id",
            "FRANCE_TRAVAIL_CLIENT_SECRET": "client-secret",
        },
        clear=True,
    )
    @patch("pfe_job_copilot.collectors.france_travail.httpx.get")
    @patch("pfe_job_copilot.collectors.france_travail.httpx.post")
    def test_returns_no_jobs_for_no_content_response(self, post: Mock, get: Mock) -> None:
        token_response = Mock(is_error=False)
        token_response.raise_for_status.return_value = None
        token_response.json.return_value = {"access_token": "token"}
        post.return_value = token_response

        search_response = Mock(status_code=204)
        search_response.raise_for_status.return_value = None
        get.return_value = search_response

        self.assertEqual(list(FranceTravailCollector().search("unlikely", "France", 5)), [])
        search_response.json.assert_not_called()


if __name__ == "__main__":
    unittest.main()
