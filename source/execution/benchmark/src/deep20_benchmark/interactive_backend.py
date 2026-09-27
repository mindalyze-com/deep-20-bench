"""Interactive inference waits on typed work; it never reads another component's state."""

from collections.abc import Callable
from datetime import UTC, datetime
from time import monotonic, sleep

from deep20_backends.config import InteractiveSettings
from deep20_backends.models import (
    BackendCapabilities,
    BackendError,
    BackendKind,
    BackendObservation,
    BackendUsage,
    ModelRequest,
    ModelResponse,
)

from .work_models import WorkIdentity, WorkRequest
from .work_queue import WorkQueue


class InteractiveBackend:
    capabilities = BackendCapabilities()

    def __init__(
        self,
        settings: InteractiveSettings,
        identity: WorkIdentity,
        queue: WorkQueue,
        *,
        research_usage: Callable[[WorkRequest], BackendUsage] | None = None,
        wait: Callable[[float], None] = sleep,
    ):
        self.settings = settings
        self.identity = identity
        self.queue = queue
        self.research_usage = research_usage
        self.wait = wait

    def complete(self, request: ModelRequest) -> ModelResponse:
        if request.role is not self.identity.role:
            raise BackendError("interactive_role_mismatch", "interactive worker has a different role")
        requested_at = datetime.now(UTC).isoformat()
        work = self.queue.enqueue(self.identity, self.settings.operator, request)
        started = monotonic()
        try:
            while (reply := self.queue.reply(work)) is None:
                if (self.settings.wait_timeout_seconds is not None
                    and monotonic() - started >= self.settings.wait_timeout_seconds):
                    self.queue.cancel(work.request_id)
                    raise BackendError("interactive_timeout", "interactive response deadline elapsed")
                self.wait(0.2)
        except (KeyboardInterrupt, SystemExit):
            self.queue.cancel(work.request_id)
            raise
        usage = self.research_usage(work) if self.research_usage is not None else BackendUsage()
        return ModelResponse(
            content=reply.content, finish_reason="stop", requested_at=requested_at,
            completed_at=datetime.fromtimestamp(reply.submitted_at, UTC).isoformat(),
            # This is elapsed operator time; no provider latency or token measurement is inferred.
            latency_ms=max(0, round((monotonic() - started) * 1000)),
            observation=BackendObservation(
                kind=BackendKind.INTERACTIVE, model=self.settings.model,
                operator=self.settings.operator, inference_requests=0, usage=usage,
                research_workflow="parallel-tools-v1" if self.settings.research else None,
            ),
            native_record={"work_request_id": work.request_id, "work_request_hash": work.request_hash},
        )

    def close(self) -> None:
        pass  # The composition root commits receipts after persisting the episode.
