from pfe_job_copilot.normalize import clean_text


def test_clean_text_accepts_numeric_source_ids() -> None:
    assert clean_text(4074) == "4074"


def test_clean_text_collapses_whitespace_and_none() -> None:
    assert clean_text("  AI\n engineer  ") == "AI engineer"
    assert clean_text(None) == ""
