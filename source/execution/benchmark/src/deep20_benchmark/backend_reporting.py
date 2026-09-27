"""Allowlisted local draft result export, derived only after episodes finish."""

from decimal import Decimal

from deep20_backends.models import BackendKind, BackendObservation, Role
from deep20_backends.reporting import DraftRunReport, RoleActivity
from deep20_game.models import ActionTurnResult, OracleResultCallAudit
from deep20_oracle.models import OracleDecisionPath
from deep20_oracle.util import canonical_json, sha256_text

from .models import BenchmarkResult, CompletedTrialResult


def _known_sum(values: tuple[int | None, ...]) -> int | None:
    return sum(v for v in values if v is not None) if all(v is not None for v in values) else None


def draft_run_report(result: BenchmarkResult) -> DraftRunReport:
    runtime = result.run.runtime
    if runtime is None:
        raise ValueError("a draft report requires an explicit runtime")
    records: dict[Role, list[BackendObservation]] = {role: [] for role in Role}
    bypasses = 0
    for subject in result.subjects:
        for trial in subject.trials:
            if not isinstance(trial, CompletedTrialResult):
                continue
            episode = trial.result
            bypasses += sum(isinstance(turn, ActionTurnResult) and turn.adjudication.oracle_quality is not None
                and turn.adjudication.oracle_quality.decision_path is OracleDecisionPath.REVIEW_BYPASSED for turn in episode.turns)
            if episode.audit is None:
                continue
            for call in episode.audit.calls:
                if isinstance(call, OracleResultCallAudit):
                    if call.cache_source is not None:
                        continue
                    research = (tuple(a.provider for a in call.research.attempts) if call.research else (call.oracle.provider,))
                    for provider in research:
                        if provider.backend is not None:
                            records[Role.ORACLE].append(provider.backend)
                    for role, part in ((Role.REVIEWER, call.reviewer), (Role.JUDGE, call.judge)):
                        if part is not None and part.provider.backend is not None:
                            records[role].append(part.provider.backend)
                elif call.provider.backend is not None:
                    records[Role(call.component)].append(call.provider.backend)
    roles = []
    for role in Role:
        binding = runtime.roles.binding(role)
        observations = records[role]
        roles.append(RoleActivity(role=role, backend=BackendKind(binding.implementation),
            model=getattr(binding, "model", f"mock/{role.value}"), logical_calls=len(observations),
            inference_requests=sum(o.inference_requests for o in observations),
            control_bypasses=bypasses if role is Role.REVIEWER else 0,
            search_requests=sum(o.usage.search_requests for o in observations),
            extract_requests=sum(o.usage.extract_requests for o in observations),
            input_tokens=_known_sum(tuple(o.usage.input_tokens for o in observations)),
            output_tokens=_known_sum(tuple(o.usage.output_tokens for o in observations)),
            reported_cost_usd=sum((o.usage.cost_usd or Decimal(0) for o in observations), Decimal(0)),
            unmetered_calls=sum(o.usage.cost_usd is None for o in observations),
            model_digests=tuple(sorted({o.model_digest for o in observations if o.model_digest is not None}))))
    report = DraftRunReport(edition_id=runtime.edition.edition_id, execution_id=str(result.run.execution_id),
        model_id=str(result.run.model.model_id), runtime_fingerprint=runtime.fingerprint,
        manifest_integrity_hash=result.artifacts.manifest.integrity_hash or "0" * 64,
        synthetic=runtime.roles.synthetic, scheduled_trials=result.summary.counts.scheduled,
        scoring_eligible_trials=result.summary.counts.scoring_eligible,
        infrastructure_failed_trials=result.summary.counts.infrastructure_failed,
        roles=tuple(roles), integrity_hash="0" * 64)
    return report.model_copy(update={"integrity_hash": sha256_text(canonical_json(report.model_dump(mode="json", exclude={"integrity_hash"})))})


def draft_report_lines(result: BenchmarkResult) -> list[str]:
    if result.run.runtime is None:
        return []
    report = draft_run_report(result)
    return [
        f"- Edition: {report.edition_id} DRAFT; local only; publication ineligible",
        f"- Synthetic: {'yes' if report.synthetic else 'no'}",
        "- Cost figures below are reported subtotals. Unmetered model or operator work is not free.",
        "- Full spending allowance, including canaries, failures, retries and tools: `spending-summary.json` when configured.",
        "", "| Role | Backend | Inference requests | Searches | Fetches | Bypasses | Unmetered calls |",
        "|---|---|---:|---:|---:|---:|---:|",
        *(f"| {r.role.value} | {r.backend.value} | {r.inference_requests} | {r.search_requests} | {r.extract_requests} | {r.control_bypasses} | {r.unmetered_calls} |" for r in report.roles),
        "", "Activity counts above cover retained episode audits. The spending ledger also covers superseded and failed attempts.", "",
    ]
