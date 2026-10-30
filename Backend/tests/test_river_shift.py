import json
from datetime import date
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException

from app import river_shift


GRANULE = "NISAR_L2_PR_GCOV_025_151_A_011_4005_DHDH_A_20260718T155041_20260718T155059_P05023_N_F_J_001"
URL = (
    "https://nisar.asf.earthdatacloud.nasa.gov/NISAR/"
    "NISAR_L2_GCOV_PROVISIONAL_V1/" + GRANULE + "/" + GRANULE + ".h5"
)


def test_catalogue_product_extracts_official_gcove_provenance():
    product = river_shift._product({
        "granuleName": GRANULE,
        "processingLevel": "GCOV",
        "url": URL,
    })
    assert product is not None
    assert product.product_type == "GCOV"
    assert product.maturity == "PROVISIONAL"
    assert product.relative_orbit == "151"
    assert product.flight_direction == "ASCENDING"
    assert product.frame_coverage == "FULL"
    assert product.start_time_utc == "20260718T155041"
    assert product.main_band_polarization == "HH+HV"


def test_catalogue_product_builds_official_download_url_from_collection_identity():
    product = river_shift._product({
        "granuleName": GRANULE,
        "processingLevel": "GCOV",
        "collectionName": "NISAR_L2_GCOV_PROVISIONAL_V1",
    })
    assert product is not None
    assert product.download_url == URL


def test_catalogue_does_not_guess_product_maturity():
    product = river_shift._product({
        "granuleName": GRANULE,
        "processingLevel": "GCOV",
    })
    assert product is not None
    assert product.maturity == "UNKNOWN"
    assert product.download_url is None


def test_catalogue_excludes_non_gcov_record():
    result = river_shift._product({
        "granuleName": "NOT_A_GCOV_PRODUCT",
        "processingLevel": "GUNW",
    })
    assert result is None


def test_coordinates_must_be_closed_and_finite():
    with pytest.raises(HTTPException, match="repeat its first coordinate"):
        river_shift._validate_coordinates([[90.0, 25.0], [90.1, 25.0], [90.1, 25.1], [90.0, 25.1]])
    with pytest.raises(HTTPException, match="finite numbers"):
        river_shift._validate_coordinates([[90.0, 25.0], [90.1, 25.0], [90.1, float("nan")], [90.0, 25.0]])


def test_catalogue_search_is_read_only_and_preserves_asf_products(monkeypatch):
    payload = {"results": [{
        "granuleName": GRANULE,
        "processingLevel": "GCOV",
        "url": URL,
    }]}
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self):
            return json.dumps(payload).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return FakeResponse()

    monkeypatch.setattr(river_shift.urllib.request, "urlopen", fake_urlopen)
    request = river_shift.RiverShiftCatalogRequest(
        coordinates=[[89.6, 25.1], [89.7, 25.1], [89.7, 25.2], [89.6, 25.2], [89.6, 25.1]],
        start_date=date(2026, 6, 17),
        end_date=date(2026, 10, 31),
        maturity="PROVISIONAL",
    )
    result = river_shift.search_gcov_catalogue(request)
    params = parse_qs(urlparse(captured["url"]).query)
    assert params["output"] == ["json"]
    assert "frameCoverage" not in params  # ALL is intentionally the default for catalogue discovery.
    assert result.status == "ready"
    assert result.product_count == 1
    assert result.data_downloaded is False
    assert result.scientific_analysis_performed is False
    assert result.products[0].granule_name == GRANULE


def test_catalogue_can_filter_to_full_frame_coverage(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self):
            return json.dumps({"results": []}).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        return FakeResponse()

    monkeypatch.setattr(river_shift.urllib.request, "urlopen", fake_urlopen)
    request = river_shift.RiverShiftCatalogRequest(
        coordinates=[[89.6, 25.1], [89.7, 25.1], [89.7, 25.2], [89.6, 25.2], [89.6, 25.1]],
        start_date=date(2026, 6, 17),
        end_date=date(2026, 10, 31),
        maturity="PROVISIONAL",
        frame_coverage="FULL",
    )
    result = river_shift.search_gcov_catalogue(request)
    params = parse_qs(urlparse(captured["url"]).query)
    assert params["frameCoverage"] == ["FULL"]
    assert result.query["frame_coverage"] == "FULL"


def test_catalogue_search_rejects_aoi_larger_than_limit():
    request = river_shift.RiverShiftCatalogRequest(
        coordinates=[[-10.0, -10.0], [10.0, -10.0], [10.0, 10.0], [-10.0, 10.0], [-10.0, -10.0]],
        start_date=date(2026, 1, 1),
        end_date=date(2026, 2, 1),
        maturity="PROVISIONAL",
    )
    with pytest.raises(HTTPException, match="AOI area"):
        river_shift.search_gcov_catalogue(request)
