from __future__ import annotations

from dataclasses import dataclass

RESULT_ARTIFACT = "result.yml"


@dataclass(frozen=True, slots=True)
class RunArtifactPolicy:
    """One shared rule for artifacts produced by every run component."""

    verbose: bool = False

    def permits(self, filename: str) -> bool:
        """Keep the terminal result by default; gate every other file as verbose."""
        return filename == RESULT_ARTIFACT or self.verbose
