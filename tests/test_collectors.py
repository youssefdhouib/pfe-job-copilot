import unittest

from pfe_job_copilot.collectors.ats import AshbyCollector, GreenhouseCollector, LeverCollector
from pfe_job_copilot.collectors.jobspy import JobSpyCollector
from pfe_job_copilot.collectors.registry import get_collector
from pfe_job_copilot.collectors.public_pages import PublicJobsPageCollector
import re


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeFetcher:
    def __init__(self, text: str) -> None:
        self.text = text

    def get(self, url: str) -> FakeResponse:
        return FakeResponse(self.text)


class CollectorRegistryTests(unittest.TestCase):
    def test_builds_greenhouse_collector_from_source_identifier(self) -> None:
        collector = get_collector("greenhouse:example")
        self.assertIsInstance(collector, GreenhouseCollector)
        self.assertEqual(collector.board_token, "example")

    def test_builds_lever_collector_from_source_identifier(self) -> None:
        collector = get_collector("lever:example")
        self.assertIsInstance(collector, LeverCollector)
        self.assertEqual(collector.site, "example")

    def test_builds_ashby_collector_from_source_identifier(self) -> None:
        collector = get_collector("ashby:example")
        self.assertIsInstance(collector, AshbyCollector)
        self.assertEqual(collector.board_name, "example")

    def test_builds_supported_jobspy_collector(self) -> None:
        collector = get_collector("jobspy-linkedin")
        self.assertIsInstance(collector, JobSpyCollector)
        self.assertEqual(collector.site, "linkedin")

    def test_registers_public_french_collectors(self) -> None:
        self.assertEqual(get_collector("wttj").source, "wttj")
        self.assertEqual(get_collector("hellowork").source, "hellowork")

    def test_public_collector_reads_jobposting_jsonld_and_deduplicates_links(self) -> None:
        html = '''
        <script type="application/ld+json">{
          "@type":"JobPosting", "title":"Stage Ingénieur IA Générative",
          "url":"/fr/companies/acme/jobs/stage-ia_paris", "description":"LLM et RAG",
          "hiringOrganization":{"name":"Acme"},
          "jobLocation":{"address":{"addressLocality":"Paris","addressCountry":"FR"}}
        }</script>
        <article><a href="/fr/companies/acme/jobs/stage-ia_paris">Stage Ingénieur IA Générative</a></article>
        '''
        collector = PublicJobsPageCollector(
            source="test", base_url="https://example.test",
            url_builder=lambda query, location: "https://example.test/jobs",
            job_path_pattern=re.compile(r"/fr/companies/.+/jobs/.+"),
            fetcher=FakeFetcher(html),
        )
        jobs = list(collector.search("ia", "France", 10))
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].company, "Acme")
        self.assertEqual(jobs[0].location, "Paris, FR")
        self.assertEqual(jobs[0].description, "LLM et RAG")

    def test_rejects_unknown_source(self) -> None:
        with self.assertRaises(ValueError):
            get_collector("unknown")


if __name__ == "__main__":
    unittest.main()
