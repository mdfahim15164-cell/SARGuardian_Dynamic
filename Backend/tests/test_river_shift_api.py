from fastapi.testclient import TestClient

from app.auth import get_current_user
from app.main import app
from app import river_shift as river_shift_module


VALID_POLYGON = [
    [89.6, 25.0],
    [89.8, 25.0],
    [89.8, 25.2],
    [89.6, 25.2],
    [89.6, 25.0],
]


def test_river_shift_catalog_requires_authentication():
    client = TestClient(app)
    response = client.post("/api/river-shift/catalog/search", json={
        "coordinates": VALID_POLYGON,
        "start_date": "2026-06-17",
        "end_date": "2026-07-20",
    })
    assert response.status_code == 401


def test_river_shift_catalog_search_returns_real_adapter_contract(monkeypatch):
    captured = {}

    def fake_search(aoi_wkt, start_date, end_date, **kwargs):
        captured.update({"aoi_wkt": aoi_wkt, "start": start_date, "end": end_date, **kwargs})
        return {
            "dataset": "NISAR",
            "processing_level": "GCOV",
            "requested_maturity_filter": "PROVISIONAL",
            "result_count": 0,
            "scenes": [],
            "catalogue_only": True,
            "data_downloaded": False,
            "scientific_analysis_performed": False,
            "warnings": [],
        }

    monkeypatch.setattr(river_shift_module, "search_gcov", fake_search)
    app.dependency_overrides[get_current_user] = lambda: {"uid": "test-user"}
    try:
        client = TestClient(app)
        response = client.post("/api/river-shift/catalog/search", json={
            "coordinates": VALID_POLYGON,
            "start_date": "2026-06-17",
            "end_date": "2026-07-20",
            "data_maturity": "PROVISIONAL",
            "max_results": 50,
        })
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["dataset"] == "NISAR"
    assert payload["processing_level"] == "GCOV"
    assert payload["catalogue_only"] is True
    assert payload["data_downloaded"] is False
    assert payload["scientific_analysis_performed"] is False
    assert payload["aoi_area_km2"] > 0
    assert captured["maturity"] == "PROVISIONAL"
    assert captured["max_results"] == 50


def test_river_shift_catalog_rejects_open_or_invalid_polygon():
    app.dependency_overrides[get_current_user] = lambda: {"uid": "test-user"}
    try:
        client = TestClient(app)
        response = client.post("/api/river-shift/catalog/search", json={
            "coordinates": VALID_POLYGON[:-1],
            "start_date": "2026-06-17",
            "end_date": "2026-07-20",
        })
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 422


def test_river_shift_catalog_rejects_reversed_dates():
    app.dependency_overrides[get_current_user] = lambda: {"uid": "test-user"}
    try:
        client = TestClient(app)
        response = client.post("/api/river-shift/catalog/search", json={
            "coordinates": VALID_POLYGON,
            "start_date": "2026-07-20",
            "end_date": "2026-06-17",
        })
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert response.status_code == 422
