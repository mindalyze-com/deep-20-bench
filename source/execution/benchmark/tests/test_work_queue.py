import sqlite3
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest
from deep20_backends.config import InteractiveSettings
from deep20_backends.models import BackendError, Message, MessageRole, ModelRequest, Role
from deep20_benchmark.interactive_backend import InteractiveBackend
from deep20_benchmark.models import BenchmarkExecutionId, BenchmarkModelId, SubjectId, TrialId
from deep20_benchmark.spending import SqliteSpendingLedger
from deep20_benchmark.work_models import WorkIdentity, WorkStatus, WorkSubmission
from deep20_benchmark.work_queue import MemoryWorkQueue, SqliteWorkQueue


def identity(role=Role.VALIDATOR, attempt=1):
    return WorkIdentity(
        execution_id=BenchmarkExecutionId("BX-queue"), model_id=BenchmarkModelId("M-0001"),
        target_id=SubjectId("T-0001"), trial_id=TrialId("trial-001"), attempt_number=attempt, role=role,
    )


def request(role=Role.VALIDATOR):
    return ModelRequest(
        role=role, messages=(Message(role=MessageRole.USER, content="private role fixture"),),
        output_schema={"type": "object"}, schema_name="fixture",
    )


def submit(queue, work, content='{"answer":"YES"}'):
    claim = queue.claim(work.request_id, operator="operator", role=work.identity.role)
    submission = WorkSubmission(request_id=work.request_id, request_hash=work.request_hash,
                                claim_id=claim.claim_id, content=content)
    return claim, submission, queue.submit(submission)


def test_identical_submission_is_idempotent_even_after_payload_scrubbing():
    queue = MemoryWorkQueue()
    work = queue.enqueue(identity(), "operator", request())
    claim, submission, receipt = submit(queue, work)
    assert queue.submit(submission) == receipt
    assert queue.reply(work).content == submission.content
    queue.finish_attempt(identity())
    assert queue.submit(submission).status is WorkStatus.CONSUMED
    row = queue.connection.execute("SELECT request_json,response_text FROM role_work").fetchone()
    assert row == (None, None)
    with pytest.raises(BackendError) as error:
        queue.submit(submission.model_copy(update={"content": '{"answer":"NO"}'}))
    assert error.value.code == "conflicting_work_submission"
    with pytest.raises(BackendError):
        queue.read(claim)


def test_expired_claim_cannot_submit_after_another_worker_reclaims():
    now = [100.0]
    queue = MemoryWorkQueue(clock=lambda: now[0])
    work = queue.enqueue(identity(), "operator", request())
    first = queue.claim(work.request_id, operator="operator", role=Role.VALIDATOR, lease_seconds=1)
    now[0] = 102.0
    second = queue.claim(work.request_id, operator="operator", role=Role.VALIDATOR)
    with pytest.raises(BackendError):
        queue.submit(WorkSubmission(request_id=work.request_id, request_hash=work.request_hash,
                                     claim_id=first.claim_id, content="old response"))
    assert queue.read(second).inference == request()


def test_wrong_role_and_request_hash_are_rejected():
    queue = MemoryWorkQueue()
    work = queue.enqueue(identity(), "operator", request())
    with pytest.raises(BackendError):
        queue.claim(work.request_id, operator="operator", role=Role.GUESSER)
    claim = queue.claim(work.request_id, operator="operator", role=Role.VALIDATOR)
    with pytest.raises(BackendError):
        queue.submit(WorkSubmission(request_id=work.request_id, request_hash="0" * 64,
                                     claim_id=claim.claim_id, content="wrong request"))


def test_repair_invalidates_old_pending_and_submitted_work():
    queue = MemoryWorkQueue()
    old = queue.enqueue(identity(), "operator", request())
    _, submission, _ = submit(queue, old)
    queue.invalidate_prior_attempts(identity(attempt=2))
    with pytest.raises(BackendError):
        queue.submit(submission)
    assert queue.receipts()[0].status is WorkStatus.CANCELLED


def test_interactive_guesser_passes_malformed_output_to_counted_engine_validation():
    queue = MemoryWorkQueue()
    def operator(_seconds):
        receipt = queue.receipts()[0]
        work = queue.connection.execute("SELECT request_json FROM role_work").fetchone()[0]
        from deep20_benchmark.work_models import WorkRequest
        submit(queue, WorkRequest.model_validate_json(work), content="malformed action")
        assert receipt.identity.role is Role.GUESSER

    backend = InteractiveBackend(InteractiveSettings(operator="operator", isolated_context=True),
                                  identity(Role.GUESSER), queue, wait=operator)
    response = backend.complete(request(Role.GUESSER))
    assert response.content == "malformed action"
    assert response.observation.inference_requests == 0
    assert response.observation.usage.cost_usd is None
    assert response.observation.usage.input_tokens is None
    assert queue.receipts()[0].status is WorkStatus.SUBMITTED


def test_only_one_process_can_claim_a_work_item(tmp_path):
    path = tmp_path / "queue.sqlite"
    with sqlite3.connect(path) as connection:
        queue = SqliteWorkQueue(connection)
        work = queue.enqueue(identity(), "operator", request())
    def claim(_index):
        with sqlite3.connect(path) as connection:
            try:
                return SqliteWorkQueue(connection).claim(work.request_id, operator="operator", role=Role.VALIDATOR)
            except BackendError:
                return None
    with ThreadPoolExecutor(2) as pool:
        outcomes = tuple(pool.map(claim, range(2)))
    assert sum(outcome is not None for outcome in outcomes) == 1


def test_unknown_billing_remains_reserved_after_reopening(tmp_path):
    path = tmp_path / "budget.sqlite"
    with sqlite3.connect(path) as connection:
        ledger = SqliteSpendingLedger(connection, Decimal(2))
        reservation = ledger.reserve("openrouter", Decimal("1.6"))
        ledger.settle(reservation, None)
    with sqlite3.connect(path) as connection:
        ledger = SqliteSpendingLedger(connection, Decimal(2))
        assert ledger.snapshot().reserved_usd == Decimal("1.6")
        with pytest.raises(BackendError):
            ledger.reserve("parallel_search", Decimal("0.5"))
        ledger.settle(reservation, Decimal("0.1"))
        assert ledger.snapshot().remaining_usd == Decimal("1.9")
        assert ledger.snapshot().unmetered_requests == 0


def test_concurrent_reservations_cannot_exceed_total_limit(tmp_path):
    path = tmp_path / "budget.sqlite"
    with sqlite3.connect(path) as connection:
        SqliteSpendingLedger(connection, Decimal(2))
    def reserve(_index):
        with sqlite3.connect(path) as connection:
            try:
                return SqliteSpendingLedger(connection, Decimal(2)).reserve("openrouter", Decimal("1.1"))
            except BackendError:
                return None
    with ThreadPoolExecutor(2) as pool:
        outcomes = tuple(pool.map(reserve, range(2)))
    assert sum(outcome is not None for outcome in outcomes) == 1
