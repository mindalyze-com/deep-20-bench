"""On-demand Claude Fable 5.1 Guesser experiment with direct Codex decisions."""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

import bridge
from deep20_benchmark.models import BenchmarkExecutionId, BenchmarkModelId


def configure() -> None:
    """Select this experiment without changing another run or registered model."""
    bridge.ROOT = bridge.REPOSITORY / "private/reviews/fable51-direct-20260910"
    bridge.EXECUTION = "BX-20260910-B-0003-codex-direct-M0020-001"
    bridge.MODEL = BenchmarkModelId("M-0020")
    bridge.BASELINE = BenchmarkExecutionId("BX-20260908-B-0003-experimental-M0020-001")


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
    args = parser.parse_args()
    configure()
    if args.command == "preview":
        bridge.preview()
    elif args.command == "live":
        if not args.live:
            parser.error("paid Claude Fable 5.1 execution requires --live")
        import fable51_live
        import live_entry

        try:
            fable51_live.main()
        except Exception as error:  # noqa: BLE001 - redact executable-boundary diagnostics.
            live_entry.status("interrupted", f"Experiment stopped with {type(error).__name__}.")
            raise SystemExit(1) from None
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
