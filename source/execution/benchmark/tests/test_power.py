from __future__ import annotations

import logging
import subprocess
from pathlib import Path

import pytest
from deep20_benchmark import power


class FakeCaffeinate:
    def __init__(self) -> None:
        self.terminated = False
        self.killed = False
        self.wait_timeouts: list[int | None] = []

    def poll(self) -> int | None:
        return None

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: int | None = None) -> int:
        self.wait_timeouts.append(timeout)
        return 0


class ExitedCaffeinate(FakeCaffeinate):
    def terminate(self) -> None:
        raise ProcessLookupError


def test_sleep_prevention_is_a_noop_outside_macos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(power.sys, "platform", "linux")
    monkeypatch.setattr(
        power.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("caffeinate must not run on Linux"),
    )

    with power.prevent_idle_system_sleep():
        pass


def test_sleep_prevention_can_be_disabled_on_macos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(power.sys, "platform", "darwin")
    monkeypatch.setenv("DEEP20BENCH_CAFFEINATE", "0")
    monkeypatch.setattr(
        power.subprocess,
        "Popen",
        lambda *_args, **_kwargs: pytest.fail("disabled caffeinate must not run"),
    )

    with power.prevent_idle_system_sleep():
        pass


def test_sleep_prevention_tracks_the_benchmark_process_and_is_reaped(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    executable = tmp_path / "caffeinate"
    executable.touch()
    fake = FakeCaffeinate()
    command: tuple[str, ...] | None = None

    def fake_popen(
        args: tuple[str, ...],
        **_kwargs: object,
    ) -> FakeCaffeinate:
        nonlocal command
        command = args
        return fake

    monkeypatch.setattr(power.sys, "platform", "darwin")
    monkeypatch.delenv("DEEP20BENCH_CAFFEINATE", raising=False)
    monkeypatch.setattr(power, "_CAFFEINATE_PATH", executable)
    monkeypatch.setattr(power.os, "getpid", lambda: 12345)
    monkeypatch.setattr(power.subprocess, "Popen", fake_popen)

    with (
        caplog.at_level(logging.INFO, logger="deep20.benchmark"),
        power.prevent_idle_system_sleep(),
    ):
        assert not fake.terminated

    assert command == (str(executable), "-i", "-w", "12345")
    assert fake.terminated
    assert not fake.killed
    assert fake.wait_timeouts == [2]
    assert "idle_sleep=prevented display_sleep=allowed" in caplog.text


def test_sleep_prevention_failure_does_not_fail_the_benchmark(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    executable = tmp_path / "caffeinate"
    executable.touch()
    guarded_operation_ran = False

    def fail_to_start(
        _args: tuple[str, ...],
        **_kwargs: object,
    ) -> subprocess.Popen[bytes]:
        raise OSError("not available")

    monkeypatch.setattr(power.sys, "platform", "darwin")
    monkeypatch.delenv("DEEP20BENCH_CAFFEINATE", raising=False)
    monkeypatch.setattr(power, "_CAFFEINATE_PATH", executable)
    monkeypatch.setattr(power.subprocess, "Popen", fail_to_start)

    with (
        caplog.at_level(logging.WARNING, logger="deep20.benchmark"),
        power.prevent_idle_system_sleep(),
    ):
        guarded_operation_ran = True

    assert guarded_operation_ran
    assert "error_code=caffeinate_start_failed" in caplog.text


def test_sleep_prevention_cleanup_race_does_not_fail_the_benchmark(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    executable = tmp_path / "caffeinate"
    executable.touch()
    fake = ExitedCaffeinate()

    monkeypatch.setattr(power.sys, "platform", "darwin")
    monkeypatch.delenv("DEEP20BENCH_CAFFEINATE", raising=False)
    monkeypatch.setattr(power, "_CAFFEINATE_PATH", executable)
    monkeypatch.setattr(power.subprocess, "Popen", lambda *_args, **_kwargs: fake)

    with power.prevent_idle_system_sleep():
        pass
