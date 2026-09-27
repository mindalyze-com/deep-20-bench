"""On-demand Sol Guesser experiment using the shared direct-Codex bridge."""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

import bridge
from deep20_benchmark.models import BenchmarkExecutionId, BenchmarkModelId


def configure(attempt: int = 2) -> None:
    """Select this run in this process without changing other experiments."""
    if not 1 <= attempt <= 999:
        raise ValueError("attempt must be between 1 and 999")
    suffix = "" if attempt == 1 else f"-{attempt:03d}"
    bridge.ROOT = bridge.REPOSITORY / f"private/reviews/sol-direct-20260910{suffix}"
    bridge.EXECUTION = f"BX-20260910-B-0003-codex-direct-M0010-{attempt:03d}"
    bridge.MODEL = BenchmarkModelId("M-0010")
    bridge.BASELINE = BenchmarkExecutionId("BX-20260908-B-0003-experimental-M0010-001")


def main() -> None:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("preview", "live", "pending", "next", "submit", "progress", "comparison"),
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--after", type=int, default=0)
    parser.add_argument("--attempt", type=int, default=2)
    args = parser.parse_args()
    configure(args.attempt)
    if args.command == "preview":
        bridge.ROOT.mkdir(parents=True, exist_ok=True)
        bridge.preview()
    elif args.command == "live":
        if not args.live:
            parser.error("paid Sol execution requires --live")
        import sol_live

        sol_live.main()
    elif args.command == "pending":
        bridge.pending()
    elif args.command == "submit":
        if args.input is None:
            parser.error("submit requires --input")
        bridge.submit(args.input)
    elif args.command == "comparison":
        import comparison

        comparison.BASELINE = bridge.BASELINE
        comparison.main()
    else:
        sys.argv = [args.command + ".py"]
        if args.command == "next":
            sys.argv.extend(("--after", str(args.after)))
        runpy.run_path(str(Path(__file__).with_name(args.command + ".py")), run_name="__main__")


if __name__ == "__main__":
    main()
