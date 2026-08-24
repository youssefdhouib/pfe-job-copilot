import unittest

from pfe_job_copilot.alerts import extract_alert_jobs


class AlertParserTests(unittest.TestCase):
    def test_extracts_supported_links_and_deduplicates_tracking_variants(self) -> None:
        jobs = extract_alert_jobs(
            subject="New AI internships",
            html="""
                <div><a href="https://www.linkedin.com/jobs/view/123?trackingId=one">AI Engineer Intern</a></div>
                <div><a href="https://www.linkedin.com/jobs/view/123?trackingId=two">View job</a></div>
                <a href="https://example.com/privacy">Privacy</a>
            """,
        )
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].title, "AI Engineer Intern")
        self.assertEqual(jobs[0].source, "alert-linkedin")
        self.assertEqual(jobs[0].url, "https://www.linkedin.com/jobs/view/123")

    def test_canonicalizes_indeed_click_links(self) -> None:
        jobs = extract_alert_jobs(
            subject="Stage PFE IA",
            text="https://fr.indeed.com/rc/clk?jk=abc123&utm_source=alert",
        )
        self.assertEqual(jobs[0].url, "https://fr.indeed.com/viewjob?jk=abc123")
        self.assertEqual(jobs[0].title, "Stage PFE IA")


if __name__ == "__main__":
    unittest.main()
