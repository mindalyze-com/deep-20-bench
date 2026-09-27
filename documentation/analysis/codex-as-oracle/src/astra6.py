"""On-demand Astra Guesser profile for the existing interactive Codex bridge."""

from __future__ import annotations

import argparse
import importlib
import os
import runpy
import sys
from pathlib import Path

import bridge
from deep20_benchmark.models import BenchmarkExecutionId, BenchmarkModelId


def configure(attempt: int = 1) -> None:
    if attempt not in (1, 2, 3, 4):
        raise ValueError("Astra startup attempts are bounded to 1 through 4")
    suffix = "" if attempt == 1 else f"-{attempt:03d}"
    bridge.ROOT = bridge.REPOSITORY / f"private/reviews/astra6-direct-20260910{suffix}"
    bridge.EXECUTION = f"BX-20260910-B-0003-codex-direct-M0022-{attempt:03d}"
    bridge.MODEL = BenchmarkModelId("M-0022")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("preview", "run", "pending", "submit", "next", "progress", "comparison")
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--attempt", type=int, choices=(1, 2, 3, 4), default=1)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--after", type=int, default=0)
    args = parser.parse_args()
    configure(args.attempt)
    if args.command == "preview":
        bridge.ROOT.mkdir(parents=True, exist_ok=True)
        bridge.preview()
    elif args.command == "run":
        if not args.live:
            parser.error("paid Astra execution requires --live")
        if args.attempt not in (2, 3, 4):
            parser.error("the budgeted live retry requires --attempt 2, 3, or 4")
        import astra6_budget

        astra6_budget.run()
    elif args.command == "pending":
        bridge.pending()
    elif args.command == "submit":
        if args.input is None:
            parser.error("submit requires --input")
        bridge.submit(args.input)
    elif args.command == "comparison":
        import comparison

        comparison.BASELINE = BenchmarkExecutionId("BX-20260909-B-0003-experimental-M0022-002")
        comparison.main()
    elif args.command == "progress":
        importlib.import_module("progress")
    else:
        sys.argv = [args.command + ".py"]
        if args.command == "next":
            sys.argv.extend(("--after", str(args.after)))
        runpy.run_module(args.command, run_name="__main__")


if __name__ == "__main__":
    os.umask(0o077)
    main()
