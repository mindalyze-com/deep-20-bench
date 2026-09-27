"""On-demand Muse Spark Guesser experiment with direct Codex support decisions."""

from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path

import bridge
from deep20_benchmark.models import BenchmarkExecutionId, BenchmarkModelId


def configure() -> None:
    """Select a separate run while retaining the registered Guesser configuration."""
    bridge.ROOT = bridge.REPOSITORY / "private/reviews/muse-direct-20260910"
    bridge.EXECUTION = "BX-20260910-B-0003-codex-direct-M0026-002"
    bridge.MODEL = BenchmarkModelId("M-0026")
    bridge.BASELINE = BenchmarkExecutionId("BX-20260909-B-0003-experimental-M0026-003")


def main() -> None:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("preview", "live", "pending", "next", "submit", "progress", "comparison")
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
            parser.error("paid Muse Spark execution requires --live")
        import live_entry

        try:
            live_entry.main()
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
