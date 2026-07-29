from __future__ import annotations

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "scripts" / "run-all-models.sh"


def test_wrapper_is_valid_bash_and_requires_an_explicit_benchmark_mode() -> None:
    syntax = subprocess.run(
        ["bash", "-n", str(SCRIPT)],
        check=False,
        capture_output=True,
        text=True,
    )
    missing_mode = subprocess.run(
        [str(SCRIPT)],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert syntax.returncode == 0, syntax.stderr
    assert missing_mode.returncode == 2
    assert "<official|experimental>" in missing_mode.stderr


def test_wrapper_runs_models_in_parallel_without_injecting_subject_data() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert ') &' in source
    assert 'done <<< "$MODEL_IDS"' in source
    assert "--targets" not in source
    assert "T-" not in source
    assert 'run_id="BX-${RUN_DATE}-${MODE}-${compact_model}-${SEQUENCE}"' in source
    assert 'logs=$PWD/$LOG_DIR' in source
    assert "status=started" in source
    assert "status=completed" in source
    assert "status=failed" in source
