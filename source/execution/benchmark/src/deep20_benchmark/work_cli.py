"""Explicit private operator I/O. These payloads are never routine console diagnostics."""

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path
from typing import Annotated

import typer
from deep20_backends.models import BackendError, Role
from deep20_backends.parallel import ParallelResearchTools
from deep20_backends.research import ExtractInput, ResearchScope, SearchInput
from deep20_oracle.models import StrictModel
from deep20_oracle.util import repository_root
from pydantic import Field

from .backend_config import RuntimeSnapshot
from .models import BenchmarkExecutionId, BenchmarkModelId
from .parallel_credentials import load_parallel_api_key
from .research_journal import SqliteResearchJournal
from .spending import SqliteSpendingLedger
from .work_models import WorkClaim, WorkRequestId, WorkStatus, WorkSubmission
from .work_queue import SqliteWorkQueue

work_app = typer.Typer(help="Operate private draft role requests. Read output is role-private data.")


class WorkLocation(StrictModel):
    edition_id: str = Field(pattern=r"^[0-9]+\.[0-9]+$")
    model_id: BenchmarkModelId
    execution_id: BenchmarkExecutionId

    def run_root(self) -> Path:
        return (repository_root() / "private" / "editions" / self.edition_id / "runs"
                / str(self.model_id) / str(self.execution_id))


@work_app.callback()
def work_options(
    ctx: typer.Context,
    model_id: Annotated[str, typer.Option("--model")],
    run_id: Annotated[str, typer.Option("--run-id")],
    edition_id: Annotated[str, typer.Option("--edition")] = "1.2",
) -> None:
    ctx.obj = WorkLocation(edition_id=edition_id, model_id=BenchmarkModelId(model_id),
                           execution_id=BenchmarkExecutionId(run_id))


def location(ctx: typer.Context) -> WorkLocation:
    if not isinstance(ctx.obj, WorkLocation):
        raise TypeError("missing work location")
    return ctx.obj


@contextmanager
def queue_for(ctx: typer.Context) -> Iterator[SqliteWorkQueue]:
    path = location(ctx).run_root() / "work.sqlite"
    try:
        if not path.is_file():
            raise BackendError("work_queue_missing", "no work queue exists for this draft execution")
        connection = sqlite3.connect(path.as_uri() + "?mode=rw", uri=True, timeout=30)
        try:
            yield SqliteWorkQueue(connection)
        finally:
            connection.close()
    except (BackendError, OSError, ValueError, sqlite3.Error) as error:
        typer.echo(json.dumps({"error": {"code": getattr(error, "code", "work_command_failed"),
                                         "message": "Work command failed; check its identifiers and claim."}}), err=True)
        raise typer.Exit(1) from None


def load_claim(path: Path) -> WorkClaim:
    return WorkClaim.model_validate_json(path.read_text(encoding="utf-8"))


@work_app.command("list")
def list_work(ctx: typer.Context, role: Annotated[Role | None, typer.Option()] = None) -> None:
    with queue_for(ctx) as queue:
        typer.echo(json.dumps({"work": [receipt.model_dump(mode="json") for receipt in queue.receipts(role=role)
                                       if receipt.status in {WorkStatus.PENDING, WorkStatus.CLAIMED}]}))


@work_app.command("claim")
def claim_work(
    ctx: typer.Context, request_id: str,
    operator: Annotated[str, typer.Option()], role: Annotated[Role, typer.Option()],
    output: Annotated[Path, typer.Option(help="Private claim file for read, renew, and submit.")],
) -> None:
    with queue_for(ctx) as queue:
        claim = queue.claim(WorkRequestId(request_id), operator=operator, role=role)
        output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        import os
        descriptor = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as target:
            target.write(claim.model_dump_json(indent=2) + "\n")
        typer.echo(json.dumps({"status": "claimed", "claim_file": str(output)}))


@work_app.command("read")
def read_work(ctx: typer.Context, claim_file: Annotated[Path, typer.Option()]) -> None:
    with queue_for(ctx) as queue:
        work = queue.read(load_claim(claim_file))
        # Controllers keep the claim out of the model context. Guesser workers receive
        # only the unchanged messages; the schema documents their existing wire contract.
        typer.echo(json.dumps({
            "messages": [{"role": m.role.value, "content": m.content} for m in work.inference.messages],
            "output_schema": work.inference.output_schema,
        }, ensure_ascii=False))


@work_app.command("renew")
def renew_work(ctx: typer.Context, claim_file: Annotated[Path, typer.Option()]) -> None:
    with queue_for(ctx) as queue:
        updated = queue.renew(load_claim(claim_file))
        claim_file.write_text(updated.model_dump_json(indent=2) + "\n", encoding="utf-8")
        typer.echo('{"status":"renewed"}')


@work_app.command("submit")
def submit_work(
    ctx: typer.Context, claim_file: Annotated[Path, typer.Option()],
    response_file: Annotated[Path, typer.Option(help="Raw role response; validated by the role service.")],
) -> None:
    with queue_for(ctx) as queue:
        claim = load_claim(claim_file)
        receipt = queue.submit(WorkSubmission(
            request_id=claim.request_id, request_hash=claim.request_hash, claim_id=claim.claim_id,
            content=response_file.read_text(encoding="utf-8"),
        ))
        typer.echo(json.dumps({"status": receipt.status.value}))


@work_app.command("status")
def work_status(ctx: typer.Context) -> None:
    with queue_for(ctx) as queue:
        receipts = queue.receipts()
        counts = {status.value: sum(r.status is status for r in receipts) for status in WorkStatus}
        typer.echo(json.dumps({"waiting_for_operator": bool(counts["pending"] + counts["claimed"]),
                              "counts": counts}))


@work_app.command("cancel")
def cancel_work(ctx: typer.Context, request_id: str) -> None:
    with queue_for(ctx) as queue:
        queue.cancel(WorkRequestId(request_id))
        typer.echo('{"status":"cancelled"}')


@contextmanager
def research_for(ctx: typer.Context, queue: SqliteWorkQueue, claim: WorkClaim) -> Iterator[ParallelResearchTools]:
    work = queue.read(claim)
    if work.identity.role is not Role.ORACLE or work.inference.max_search_requests is None:
        raise BackendError("research_role_required", "research is restricted to Oracle work")
    root = location(ctx).run_root()
    runtime = RuntimeSnapshot.model_validate_json((root / "backend-runtime.json").read_text(encoding="utf-8"))
    if getattr(runtime.roles.oracle, "research", None) != "parallel":
        raise BackendError("research_not_configured", "this Oracle does not have managed research")
    connection = sqlite3.connect((root / "spending.sqlite").as_uri() + "?mode=rw", uri=True, timeout=30)
    try:
        row = connection.execute("SELECT limit_usd FROM spending_config WHERE id=1").fetchone()
        if row is None:
            raise BackendError("spending_limit_missing", "research has no execution allowance")
        ledger = SqliteSpendingLedger(connection, Decimal(row[0]))
        scope = ResearchScope(scope_id=work.request_id, search_limit=work.inference.max_search_requests,
                              policy=runtime.research)
        tool = ParallelResearchTools(load_parallel_api_key(repository_root()), scope, ledger,
                                     SqliteResearchJournal(queue.connection, claim=claim))
        try:
            yield tool
        finally:
            tool.close()
    finally:
        connection.close()


@work_app.command("search")
def search_work(ctx: typer.Context, claim_file: Annotated[Path, typer.Option()],
                objective: Annotated[str, typer.Option()],
                query: Annotated[list[str], typer.Option("--query")]) -> None:
    """Search only for the claimed Oracle request; this consumes its saved allowance."""
    with queue_for(ctx) as queue, research_for(ctx, queue, load_claim(claim_file)) as tools:
        typer.echo(tools.search(SearchInput(objective=objective, search_queries=tuple(query))).model_dump_json())


@work_app.command("fetch")
def fetch_work(ctx: typer.Context, claim_file: Annotated[Path, typer.Option()],
               objective: Annotated[str, typer.Option()], url: Annotated[str, typer.Option()]) -> None:
    """Extract a page for the claimed Oracle request; this consumes its saved allowance."""
    with queue_for(ctx) as queue, research_for(ctx, queue, load_claim(claim_file)) as tools:
        typer.echo(tools.extract(ExtractInput.model_validate({"url": url, "objective": objective})).model_dump_json())
