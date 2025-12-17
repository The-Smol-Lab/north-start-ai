import sys
from pathlib import Path

import markdown

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import clean_markdown_table

def test_llm_table_renders_contiguously():
    raw = (
        "- intro line\n"
        "| Col1 | Col2 |\n"
        "| --- | --- |\n"
        "| A | B |\n"
        "| C | D |\n"
        "Trailing text"
    )

    cleaned = clean_markdown_table(raw)
    html = markdown.markdown(cleaned, extensions=["extra", "sane_lists"])

    assert "<table>" in html
    assert html.count("<tr>") >= 3  # header + two rows
    assert "| A | B |" not in html  # should be parsed, not raw text
