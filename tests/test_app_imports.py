"""Every dashboard page runs without error (Streamlit AppTest, headless)."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / "app" / "Home.py"] + sorted((ROOT / "app" / "pages").glob("*.py"))

pytestmark = pytest.mark.skipif(not (ROOT / "artifacts" / "scores.parquet").exists(),
                                reason="run `make all` first")


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_page_runs(page):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(page), default_timeout=60).run()
    assert not at.exception, [e.message for e in at.exception]
