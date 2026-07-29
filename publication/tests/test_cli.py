from __future__ import annotations

from pathlib import Path

from deep20_publication.cli import _make_output_portable


def test_generated_html_is_portable_to_direct_file_access(tmp_path: Path) -> None:
    output = tmp_path / "docs"
    nested = output / "lab"
    nested.mkdir(parents=True)
    index_source = (
        '<link rel="stylesheet" href="/deep-20-bench/_assets/site.css">'
        '<a href="/deep-20-bench/">Home</a>'
        '<a href="/deep-20-bench/index.html#leaderboard">Results</a>'
        '<a href="/deep-20-bench/lab/">Lab</a>'
        '<script type="module" '
        'src="/deep-20-bench/_assets/PublicationChart.hash.js"></script>'
    )
    (output / "index.html").write_text(index_source, encoding="utf-8")
    (nested / "index.html").write_text(index_source, encoding="utf-8")

    _make_output_portable(output, "/deep-20-bench/")

    root_html = (output / "index.html").read_text(encoding="utf-8")
    assert 'href="./_assets/site.css"' in root_html
    assert 'href="./index.html"' in root_html
    assert 'href="./index.html#leaderboard"' in root_html
    assert 'href="./lab/index.html"' in root_html
    assert '<script defer src="./_assets/PublicationChart.hash.js"></script>' in root_html

    nested_html = (nested / "index.html").read_text(encoding="utf-8")
    assert 'href="../_assets/site.css"' in nested_html
    assert 'href="../index.html"' in nested_html
    assert 'href="../index.html#leaderboard"' in nested_html
    assert 'href="../lab/index.html"' in nested_html
    assert '<script defer src="../_assets/PublicationChart.hash.js"></script>' in nested_html
