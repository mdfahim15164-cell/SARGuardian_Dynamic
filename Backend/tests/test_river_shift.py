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


def umm_item():
    return {
        "meta": {"concept-id": "G1234567890-ASF"},
        "umm": {
            "GranuleUR": GRANULE,
            "TemporalExtents": [{
                "RangeDateTimes": [{
                    "BeginningDateTime": "2026-07-18T15:50:41.000Z",
                    "EndingDateTime": "2026-07-18T15:50:59.000Z"
                }]
            }],
            "SpatialExtent": {
                "HorizontalSpatialDomain": {
                    "Geometry": {
                        "GPolygons": [{
                            "Boundary": {
                                "Points": [
                                    {"Longitude": 89.5, "Latitude": 24.4},
                                    {"Longitude": 89.8, "Latitude": 24.4},
                                    {"Longitude": 89.8, "Latitude": 24.7},
                                    {"Longitude": 89.5, "Latitude": 24.7},
                                    {"Longitude": 89.5, "Latitude": 24.4}
                                ]
                            }
                        }]
                    }
                }
            },
            "RelatedUrls": [{"URL": URL, "Type": "GET DATA", "URLContentType": "DistributionURL"}],
            "DataGranule": {
                "ArchiveAndDistributionInformation": [{"Size": "100", "SizeUnit": "MB"}]
            }
        }
    }


def request(maturity="PROVISIONAL", frame_coverage="ALL"):
    return river_shift.RiverShiftCatalogRequest(
        coordinates=[[89.6, 25.1], [89.7, 25.1], [89.7, 25.2], [89.6, 25.2], [89.6, 25.1]],
        start_date=date(2026, 6, 17),
        end_date=date(2026, 10, 31),
        maturity=maturity,
        frame_coverage=frame_coverage,
    )


def test_catalogue_product_extracts_official_gcove_provenance():
    product = river_shift._umm_product(umm_item(), "PROVISIONAL")
    assert product is not None
    assert product.product_type == "GCOV"
    assert product.maturity == "PROVISIONAL"
    assert product.relative_orbit == "151"
    assert product.flight_direction == "ASCENDING"
    assert product.frame_coverage == "FULL"
    assert product.start_time_utc == "2026-07-18T15:50:41.000Z"
    assert product.main_band_polarization == "HH+HV"
    assert product.download_url == URL
    assert product.cmr_concept_id == "G1234567890-ASF"
    assert product.footprint["type"] == "Polygon"
    assert product.size_mb == 100.0


def test_catalogue_product_constructs_canonical_asset_when_get_data_url_missing():
    item = umm_item()
    item["umm"]["RelatedUrls"] = []
    product = river_shift._umm_product(item, "PROVISIONAL")
    assert product is not None
    assert product.download_url == URL


def test_catalogue_excludes_malformed_non_gcove_name():
    item = umm_item()
    item["umm"]["GranuleUR"] = "NISAR_L2_GUNW_not_a_gcove_name"
    assert river_shift._umm_product(item, "PROVISIONAL") is None


def test_catalogue_search_uses_official_cmr_short_name_and_umm_json(monkeypatch):
    captured = []

    class FakeResponse:
        headers = {"CMR-Hits": "1"}
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self):
            return json.dumps({"hits": 1, "items": [umm_item()]}).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured.append(request.full_url)
        return FakeResponse()

    monkeypatch.setattr(river_shift.urllib.request, "urlopen", fake_urlopen)
    result = river_shift.search_gcov_catalogue(request())
    assert len(captured) == 1
    params = parse_qs(urlparse(captured[0]).query)
    assert params["short_name"] == ["NISAR_L2_GCOV_PROVISIONAL_V1"]
    assert params["temporal[]"] == ["2026-06-17T00:00:00Z,2026-10-31T23:59:59Z"]
    assert "polygon" in params
    assert result.status == "ready"
    assert result.product_count == 1
    assert result.data_downloaded is False
    assert result.scientific_analysis_performed is False
    assert result.products[0].granule_name == GRANULE


def test_all_maturity_searches_beta_and_provisional_collections_separately(monkeypatch):
    captured = []

    class FakeResponse:
        headers = {"CMR-Hits": "0"}
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def read(self):
            return json.dumps({"hits": 0, "items": []}).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured.append(parse_qs(urlparse(request.full_url).query))
        return FakeResponse()

    monkeypatch.setattr(river_shift.urllib.request, "urlopen", fake_urlopen)
    result = river_shift.search_gcov_catalogue(request(maturity="ALL"))
    assert len(captured) == 2
    assert {params["short_name"][0] for params in captured} == {
        "NISAR_L2_GCOV_BETA_V1",
        "NISAR_L2_GCOV_PROVISIONAL_V1",
    }
    assert result.product_count == 0
    assert result.query["collection_short_names"] == [
        "NISAR_L2_GCOV_BETA_V1",
        "NISAR_L2_GCOV_PROVISIONAL_V1",
    ]


def test_coordinates_must_be_closed_and_finite():
    with pytest.raises(HTTPException, match="repeat its first coordinate"):
        river_shift._validate_coordinates([[90.0, 25.0], [90.1, 25.0], [90.1, 25.1], [90.0, 25.1]])
    with pytest.raises(HTTPException, match="finite numbers"):
        river_shift._validate_coordinates([[90.0, 25.0], [90.1, 25.0], [90.1, float("nan")], [90.0, 25.0]])


def test_catalogue_search_rejects_aoi_larger_than_limit():
    huge = river_shift.RiverShiftCatalogRequest(
        coordinates=[[-10.0, -10.0], [10.0, -10.0], [10.0, 10.0], [-10.0, 10.0], [-10.0, -10.0]],
        start_date=date(2026, 1, 1),
        end_date=date(2026, 2, 1),
        maturity="PROVISIONAL",
    )
    with pytest.raises(HTTPException, match="AOI area"):
        river_shift.search_gcov_catalogue(huge)
