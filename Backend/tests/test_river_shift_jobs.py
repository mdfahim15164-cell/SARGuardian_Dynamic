from __future__ import annotations

import json
from datetime import date
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.config import get_settings
from app.river_shift_jobs import (
    CreateRiverShiftJobRequest,
    RiverShiftWorkerCallback,
    callback_signature_is_valid,
    dispatch_river_shift_workflow,
    validate_callback_contract,
)


def valid_request() -> CreateRiverShiftJobRequest:
    return CreateRiverShiftJobRequest(
        aoi_wkt="POLYGON ((89.0 24.0, 89.2 24.0, 89.2 24.2, 89.0 24.2, 89.0 24.0))",
        start_date=date(2026, 4, 1), end_date=date(2026, 5, 31), event_date=date(2026, 5, 1),
        maturity="PROVISIONAL", frequency="frequencyA", covariance_term="HHHH",
        threshold_method="otsu", threshold_db=None, idempotency_key="river-shift-test-001",
    )


def test_github_dispatch_targets_the_checked_in_processing_workflow(monkeypatch):
    captured = {}

    class Response:
        status = 204
        def __enter__(self): return self
        def __exit__(self, *_args): return False

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["authorization"] = request.headers["Authorization"]
        assert timeout == 20
        return Response()

    monkeypatch.setattr("app.river_shift_jobs.urlopen", fake_urlopen)
    settings = get_settings({
        "RIVERSHIFT_ACTIONS_ENABLED": "true",
        "RIVERSHIFT_GITHUB_ACTIONS_TOKEN": "server-token",
        "RIVERSHIFT_GITHUB_ACTIONS_REPOSITORY": "mdfahim15164-cell/SARGuardian_Dynamic",
        "RIVERSHIFT_GITHUB_ACTIONS_WORKFLOW": "river-shift-gcov-process.yml",
        "RIVERSHIFT_GITHUB_ACTIONS_REF": "main",
        "RIVERSHIFT_CALLBACK_SECRET": "callback-secret",
        "RIVERSHIFT_PUBLIC_API_URL": "https://api.example.test",
    })
    request = valid_request()
    job_id = UUID("11111111-1111-1111-1111-111111111111")
    dispatch_river_shift_workflow(settings, job_id, request.model_dump(mode="json"), ["NISAR_TEST_GRANULE"], "a" * 64)

    assert captured["url"].endswith("/actions/workflows/river-shift-gcov-process.yml/dispatches")
    assert captured["authorization"] == "Bearer server-token"
    assert captured["body"]["ref"] == "main"
    assert captured["body"]["inputs"] == {
        "job_id": str(job_id),
        "aoi_wkt": request.aoi_wkt,
        "start_date": "2026-04-01",
        "end_date": "2026-05-31",
        "event_date": "2026-05-01",
        "maturity": "PROVISIONAL",
        "frequency": "frequencyA",
        "covariance_term": "HHHH",
        "threshold_method": "otsu",
        "threshold_db": "",
        "granule_names_json": '["NISAR_TEST_GRANULE"]',
        "request_fingerprint": "a" * 64,
        "callback_url": "https://api.example.test",
    }


def test_github_dispatch_rejects_inputs_over_the_safe_payload_limit(monkeypatch):
    def unexpected_request(*_args, **_kwargs):
        pytest.fail("Oversized workflow input must be rejected before making a network request.")

    monkeypatch.setattr("app.river_shift_jobs.urlopen", unexpected_request)
    settings = get_settings({
        "RIVERSHIFT_ACTIONS_ENABLED": "true",
        "RIVERSHIFT_GITHUB_ACTIONS_TOKEN": "server-token",
        "RIVERSHIFT_GITHUB_ACTIONS_REPOSITORY": "mdfahim15164-cell/SARGuardian_Dynamic",
        "RIVERSHIFT_GITHUB_ACTIONS_WORKFLOW": "river-shift-gcov-process.yml",
        "RIVERSHIFT_GITHUB_ACTIONS_REF": "main",
        "RIVERSHIFT_CALLBACK_SECRET": "callback-secret",
        "RIVERSHIFT_PUBLIC_API_URL": "https://api.example.test",
    })
    request = valid_request().model_dump(mode="json")
    request["aoi_wkt"] = "x" * 65_000

    with pytest.raises(RuntimeError, match="safe GitHub Actions input size"):
        dispatch_river_shift_workflow(settings, UUID("11111111-1111-1111-1111-111111111111"), request, ["NISAR_TEST_GRANULE"], "a" * 64)


def test_worker_callback_signature_is_bound_to_the_exact_body():
    body = b'{"job_id":"11111111-1111-1111-1111-111111111111"}'
    import hashlib
    import hmac

    signature = "sha256=" + hmac.new(b"callback-secret", body, hashlib.sha256).hexdigest()
    assert callback_signature_is_valid("callback-secret", body, signature)
    assert not callback_signature_is_valid("wrong-secret", body, signature)
    assert not callback_signature_is_valid("callback-secret", body + b" ", signature)


def test_success_requires_provisional_review_state_and_private_verified_files():
    callback = RiverShiftWorkerCallback(
        job_id=UUID("11111111-1111-1111-1111-111111111111"),
        request_fingerprint="a" * 64, state="succeeded", sequence=2, stage="completed",
        github_run_id="123", github_run_url="https://github.com/example/repo/actions/runs/123",
        result_summary={
            "schema_version": 1, "processing_status": "PASS", "release_status": "PROVISIONAL",
            "independent_validation_status": "PENDING",
        },
        artifact_manifest=[{
            "drive_file_id": "private-file-123", "name": "river_shift_timeseries_preview.json",
            "path": "outputs/river_shift_timeseries_preview.json", "sha256": "b" * 64,
            "bytes": 100, "remote_verification": {"status": "PASS"},
        }],
    )

    validate_callback_contract(callback)

    callback.result_summary["release_status"] = "VERIFIED"
    with pytest.raises(HTTPException) as error:
        validate_callback_contract(callback)
    assert "independent validation clearly pending" in error.value.detail
