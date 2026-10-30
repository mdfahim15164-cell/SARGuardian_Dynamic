import json
from datetime import date

import pytest
from fastapi import HTTPException

from app import river_shift


def test_catalogue_product_extracts_gcove_provenance():
    name = "NISAR_L2_PR_GCOV_005_149_A_024_4005_DHDH_A_20261101T010203_20261101T010245_X05001_N_F_J_001"
    url = (
        "https://nisar.asf.earthdatacloud.nasa.gov/NISAR/"
        "NISAR_L2_GCOV_PROVISIONAL_V1/"
        + name + "/" + name + ".h5"
    )
    product = river_shift._product({
        "granuleName": name,
        "processingLevel": "GCOV",
        "url": url,
        "startTime": "2026-11-01T01:02:03Z",
        "stopTime": "2026-11-01T01:02:45Z",
    })
    assert product is not None
    assert product.product_type == "GCOV"
    assert product.maturity == "PROVISIONAL"
    assert product.relative_orbit == "149"
    assert product.flight_direction == "ASCENDING"


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
    name = "NISAR_L2_PR_GCOV_005_149_A_024_4005_DHDH_A_20261101T010203_20261101T010245_X05001_N_F_J_001"
    url = (
        "https://nisar.asf.earthdatacloud.nasa.gov/NISAR/"
        "NISAR_L2_GCOV_PROVISIONAL_V1/"
        + name + "/" + name + ".h5"
    )
    payload = {"results": [{"granuleName": name, "processingLevel": "GCOV", "url": url}]}

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self):
            return json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(river_shift.urllib.request, "urlopen", lambda *_a, **_k: FakeResponse())
    request = river_shift.RiverShiftCatalogRequest(
        coordinates=[[89.6, 25.1], [89.7, 25.1], [89.7, 25.2], [89.6, 25.2], [89.6, 25.1]],
        start_date=date(2026, 10, 1),
        end_date=date(2026, 11, 1),
        maturity="PROVISIONAL",
    )
    result = river_shift.search_gcov_catalogue(request)
    assert result.status == "ready"
    assert result.product_count == 1
    assert result.data_downloaded is False
    assert result.scientific_analysis_performed is False
    assert result.products[0].granule_name == name


def test_catalogue_search_rejects_aoi_larger_than_limit():
    request = river_shift.RiverShiftCatalogRequest(
        coordinates=[[-10.0, -10.0], [10.0, -10.0], [10.0, 10.0], [-10.0, 10.0], [-10.0, -10.0]],
        start_date=date(2026, 1, 1),
        end_date=date(2026, 2, 1),
        maturity="PROVISIONAL",
    )
    with pytest.raises(HTTPException, match="AOI area"):
        river_shift.search_gcov_catalogue(request)
