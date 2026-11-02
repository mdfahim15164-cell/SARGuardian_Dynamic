from __future__ import annotations

import hashlib
import hmac
import json
from datetime import date
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator

from science_adapter.geometry import validate_wkt

from .config import RuntimeSettings
from .jobs import JobState
from .river_shift import RiverShiftCatalogRequest, search_gcov_catalogue


class CreateRiverShiftJobRequest(BaseModel):
    aoi_wkt: str = Field(min_length=20, max_length=100_000)
    start_date: date
    end_date: date
    event_date: date
    maturity: Literal["BETA", "PROVISIONAL"] = "PROVISIONAL"
    frequency: Literal["frequencyA", "frequencyB"] = "frequencyA"
    covariance_term: Literal["HHHH", "HVHV", "VVVV", "VHVH", "RHRH", "RVRV"] = "HHHH"
    threshold_method: Literal["otsu", "manual"] = "otsu"
    threshold_db: float | None = None
    idempotency_key: str = Field(min_length=16, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")

    @field_validator("aoi_wkt")
    @classmethod
    def validate_aoi(cls, value: str) -> str:
        try:
            return validate_wkt(value).wkt
        except ValueError as exc:
            raise ValueError(str(exc)) from None

    @model_validator(mode="after")
    def validate_dates_and_threshold(self) -> "CreateRiverShiftJobRequest":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date.")
        if (self.end_date - self.start_date).days > 366:
            raise ValueError("RiverShift observation window cannot exceed 366 days.")
        if self.end_date > date.today() or self.event_date > date.today():
            raise ValueError("Observation and event dates cannot be in the future.")
        if not self.start_date <= self.event_date <= self.end_date:
            raise ValueError("event_date must fall inside the observation window.")
        if self.threshold_method == "manual" and self.threshold_db is None:
            raise ValueError("A manual threshold requires threshold_db.")
        if self.threshold_method == "otsu" and self.threshold_db is not None:
            raise ValueError("threshold_db must be omitted when using Otsu.")
        return self


class RiverShiftWorkerCallback(BaseModel):
    job_id: UUID
    request_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    state: Literal["running", "succeeded", "failed"]
    sequence: int = Field(ge=1, le=1000)
    stage: str = Field(min_length=1, max_length=100)
    github_run_id: str = Field(min_length=1, max_length=64)
    github_run_url: str | None = Field(default=None, max_length=2048)
    error_code: str | None = Field(default=None, max_length=80)
    error_message: str | None = Field(default=None, max_length=500)
    result_summary: dict[str, Any] | None = None
    artifact_manifest: list[dict[str, Any]] | None = None


class RiverShiftJobResponse(BaseModel):
    id: UUID
    state: JobState
    stage: str
    aoi_wkt: str
    start_date: date
    end_date: date
    maturity: Literal["BETA", "PROVISIONAL"]
    frequency: str
    covariance_term: str
    github_run_id: str | None = None
    github_run_url: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    result_summary: dict[str, Any] | None = None
    artifact_manifest: list[dict[str, Any]] | None = None
    created_at: str
    updated_at: str


def request_fingerprint(request: dict[str, Any], manifest: dict[str, Any]) -> str:
    canonical = json.dumps({"request": request, "manifest": manifest}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def discover_request_manifest(request: CreateRiverShiftJobRequest) -> tuple[dict[str, Any], list[str]]:
    aoi = validate_wkt(request.aoi_wkt)
    response = search_gcov_catalogue(RiverShiftCatalogRequest(
        coordinates=[list(point) for point in aoi.coordinates],
        start_date=request.start_date, end_date=request.end_date,
        maturity=request.maturity, frame_coverage="ALL", max_results=100,
    ))
    products = [product.model_dump(mode="json") for product in response.products]
    names = sorted({str(item["granule_name"]) for item in products if item.get("granule_name")})
    dates = sorted({str(item.get("start_time_utc", ""))[:10] for item in products if item.get("start_time_utc")})
    if len(dates) < 4:
        raise HTTPException(status_code=422, detail="NASA CMR currently returns fewer than four observation dates for this AOI and window; flood and persistent-change screening need more compatible observations.")
    manifest = {
        "schema_version": 1,
        "source": "NASA CMR UMM-G / ASF DAAC",
        "endpoint": response.query.get("endpoint"),
        "collection_short_names": response.query.get("collection_short_names"),
        "reported_cmr_hits": response.query.get("reported_cmr_hits"),
        "product_count": len(products),
        "unique_dates": dates,
        "products": products,
        "catalogue_only": True,
        "warning": "CMR metadata discovery only; exact HDF5 datasets and valid masks require worker inspection.",
    }
    return manifest, names


def dispatch_river_shift_workflow(settings: RuntimeSettings, job_id: UUID, request: dict[str, Any], granule_names: list[str], fingerprint: str) -> None:
    if not settings.river_shift_actions_enabled:
        raise RuntimeError("RiverShift processing dispatch is disabled on the backend.")
    endpoint = (
        f"{settings.github_api_url}/repos/{settings.river_shift_github_actions_repository}"
        f"/actions/workflows/{settings.river_shift_github_actions_workflow}/dispatches"
    )
    inputs = {
        "job_id": str(job_id), "aoi_wkt": request["aoi_wkt"],
        "start_date": str(request["start_date"]), "end_date": str(request["end_date"]),
        "event_date": str(request["event_date"]), "maturity": str(request["maturity"]),
        "frequency": str(request["frequency"]), "covariance_term": str(request["covariance_term"]),
        "threshold_method": str(request["threshold_method"]),
        "threshold_db": "" if request.get("threshold_db") is None else str(request["threshold_db"]),
        "granule_names_json": json.dumps(granule_names, separators=(",", ":")),
        "request_fingerprint": fingerprint,
        "callback_url": settings.river_shift_public_api_url,
    }
    body = json.dumps({"ref": settings.river_shift_github_actions_ref, "inputs": inputs}).encode("utf-8")
    http_request = Request(endpoint, data=body, method="POST", headers={
        "Accept": "application/vnd.github+json", "Authorization": f"Bearer {settings.river_shift_github_actions_token}",
        "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json",
    })
    try:
        with urlopen(http_request, timeout=20) as response:
            if response.status != 204:
                raise RuntimeError("GitHub Actions did not accept the RiverShift workflow.")
    except HTTPError as exc:
        raise RuntimeError(f"GitHub Actions rejected RiverShift dispatch (HTTP {exc.code}).") from None
    except (URLError, TimeoutError):
        raise RuntimeError("Could not reach GitHub Actions to dispatch RiverShift processing.") from None


def callback_signature_is_valid(secret: str, body: bytes, signature: str | None) -> bool:
    if not secret or not signature:
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def validate_callback_contract(payload: RiverShiftWorkerCallback) -> None:
    if payload.state != "succeeded":
        return
    summary = payload.result_summary
    artifacts = payload.artifact_manifest
    if (not isinstance(summary, dict) or summary.get("schema_version") != 1
            or summary.get("processing_status") != "PASS"
            or summary.get("release_status") != "PROVISIONAL"
            or summary.get("independent_validation_status") != "PENDING"):
        raise HTTPException(status_code=409, detail="Success must contain a structurally validated provisional science report with independent validation clearly pending.")
    if not isinstance(artifacts, list) or not artifacts:
        raise HTTPException(status_code=409, detail="Success requires private result artifact receipts.")
    for artifact in artifacts:
        if (not isinstance(artifact, dict)
                or not isinstance(artifact.get("drive_file_id"), str)
                or not isinstance(artifact.get("name"), str)
                or not isinstance(artifact.get("path"), str)
                or not isinstance(artifact.get("sha256"), str)
                or len(artifact["sha256"]) != 64
                or not isinstance(artifact.get("bytes"), int)
                or artifact["bytes"] <= 0
                or artifact.get("remote_verification", {}).get("status") != "PASS"):
            raise HTTPException(status_code=409, detail="Result artifact receipt is incomplete or failed private-storage verification.")
