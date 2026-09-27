"""Private local preview of the versioned benchmark draft projection."""

from decimal import Decimal
from html import escape
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from .edition_registry import EditionRegistry
from .integrity import (
    PublicationInputError,
    canonical_json,
    parse_json_object,
    parse_yaml_object,
    sha256_text,
    verify_signed_object,
)
from .models import FrozenModel

type Role = Literal["guesser", "oracle", "reviewer", "judge", "validator"]


class _ManifestRequest(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    execution_id: str
    model_id: str
    runtime: dict[str, JsonValue]


class _ManifestHeader(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)
    schema_version: Literal[4]
    request: _ManifestRequest


class RoleActivity(FrozenModel):
    role: Role
    backend: Literal["openrouter", "ollama", "interactive", "mock"]
    model: str
    logical_calls: int = Field(ge=0)
    inference_requests: int = Field(ge=0)
    control_bypasses: int = Field(default=0, ge=0)
    search_requests: int = Field(ge=0)
    extract_requests: int = Field(ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    reported_cost_usd: Decimal = Field(ge=0)
    unmetered_calls: int = Field(ge=0)
    model_digests: tuple[str, ...] = ()


class DraftReport(FrozenModel):
    schema_version: Literal[1]
    edition_id: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    status: Literal["draft"]
    execution_id: str = Field(pattern=r"^BX-[A-Za-z0-9._-]+$")
    model_id: str = Field(pattern=r"^M-[0-9]{4}$")
    runtime_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    manifest_integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    synthetic: bool
    publication_eligible: Literal[False]
    scheduled_trials: int = Field(ge=0)
    scoring_eligible_trials: int = Field(ge=0)
    infrastructure_failed_trials: int = Field(ge=0)
    accounting_scope: Literal["retained_episode_audits"]
    roles: tuple[RoleActivity, ...] = Field(min_length=5, max_length=5)
    integrity_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def no_synthetic_scores(self) -> "DraftReport":
        if {r.role for r in self.roles} != {"guesser", "oracle", "reviewer", "judge", "validator"}:
            raise ValueError("draft report requires each role exactly once")
        if self.synthetic != any(r.backend == "mock" for r in self.roles):
            raise ValueError("draft mock configuration and synthetic marker disagree")
        if self.synthetic and self.scoring_eligible_trials:
            raise ValueError("synthetic draft results cannot have eligible scores")
        return self


def load_draft(root: Path, *, edition_id: str, model_id: str, run_id: str) -> DraftReport:
    registry_path = root / "config" / "editions.yaml"
    registry = EditionRegistry.model_validate(parse_yaml_object(registry_path.read_text(encoding="utf-8"), str(registry_path)))
    if not any(e.edition_id == edition_id and e.status == "draft" for e in registry.editions):
        raise PublicationInputError("local draft preview requires an explicit draft edition")
    import re
    if not re.fullmatch(r"M-[0-9]{4}", model_id) or not re.fullmatch(r"BX-[A-Za-z0-9._-]+", run_id):
        raise PublicationInputError("invalid draft execution identity")
    run_root = root / "private" / "editions" / edition_id / "runs" / model_id / run_id
    report_path, manifest_path = run_root / "draft-report.json", run_root / "manifest.json"
    report_data = parse_json_object(report_path.read_text(encoding="utf-8"), str(report_path))
    manifest_data = parse_json_object(manifest_path.read_text(encoding="utf-8"), str(manifest_path))
    verify_signed_object(report_data, str(report_path))
    verify_signed_object(manifest_data, str(manifest_path))
    report = DraftReport.model_validate(report_data)
    manifest = _ManifestHeader.model_validate(manifest_data)
    if ((report.edition_id, report.model_id, report.execution_id) != (edition_id, model_id, run_id)
        or manifest_data.get("schema_version") != 4
        or (manifest.request.model_id, manifest.request.execution_id) != (model_id, run_id)
        or sha256_text(canonical_json(manifest.request.runtime)) != report.runtime_fingerprint
        or manifest_data.get("integrity_hash") != report.manifest_integrity_hash):
        raise PublicationInputError("draft projection differs from its source manifest or requested identity")
    return report


def render_draft(report: DraftReport) -> str:
    title = f"Deep20Bench {report.edition_id} DRAFT"
    rows = "".join("<tr>" + "".join(f"<td>{escape(str(value))}</td>" for value in (
        role.role, role.backend, role.model, role.inference_requests, role.search_requests,
        role.extract_requests, role.control_bypasses, role.reported_cost_usd,
        role.unmetered_calls,
    )) + "</tr>" for role in report.roles)
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>{escape(title)}</title><style>
body{{font:16px/1.5 system-ui;margin:3rem auto;padding:0 1rem;max-width:80rem;color:#202b36;background:#f7f8fa}}
h1{{font-size:1.7rem}}.notice{{padding:1rem;border-left:4px solid #b46b00;background:#fff4dc}}
.table{{overflow:auto}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:.7rem;text-align:left;border-bottom:1px solid #dde2e8}}
code{{overflow-wrap:anywhere}}th{{font-size:.9rem}}footer{{margin-top:2rem;color:#52606e}}</style>
<h1>{escape(title)}</h1><p class="notice">Local preview. This edition is inactive and excluded from the public leaderboard.</p>
<p><strong>{escape(report.model_id)}</strong> / <code>{escape(report.execution_id)}</code></p>
<p>Synthetic: <strong>{'yes' if report.synthetic else 'no'}</strong>. Scheduled trials: {report.scheduled_trials}.
Scoring-eligible trials: {report.scoring_eligible_trials}. Infrastructure failures: {report.infrastructure_failed_trials}.</p>
<div class="table"><table><thead><tr><th>Role</th><th>Backend</th><th>Model</th><th>Inference</th><th>Search</th><th>Fetch</th><th>Bypass</th><th>Reported USD</th><th>Unmetered calls</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>Reported USD is a subtotal. Unknown model, hardware, or operator cost is not zero. These counts cover retained episode audits.</p>
<p>The execution's <code>spending-summary.json</code> records the shared allowance, reported charges, and unresolved reservations across canaries, retries, failures, and tools.</p>
<footer>Runtime contract: <code>{escape(report.runtime_fingerprint)}</code></footer></html>"""
