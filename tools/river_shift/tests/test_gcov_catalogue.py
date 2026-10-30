import json
from datetime import date
from urllib.parse import parse_qs, urlparse

from discover_gcov_products import normalize_product, parse_granule_metadata, search_catalogue, validate_aoi


GRANULE = "NISAR_L2_PR_GCOV_025_151_A_011_4005_DHDH_A_20260718T155041_20260718T155059_P05023_N_F_J_001"
PROVISIONAL_URL = (
    "https://nisar.asf.earthdatacloud.nasa.gov/NISAR/"
    "NISAR_L2_GCOV_PROVISIONAL_V1/" + GRANULE + "/" + GRANULE + ".h5"
)


def test_parse_gcov_granule_metadata_from_official_single_acquisition_name():
    result = parse_granule_metadata(GRANULE)
    assert result["cycle"] == "025"
    assert result["relative_orbit"] == "151"
    assert result["orbit_direction"] == "A"
    assert result["frame"] == "011"
    assert result["bandwidth_mode"] == "4005"
    assert result["polarization_code"] == "DHDH"
    assert result["acquisition_start_utc"] == "20260718T155041"
    assert result["acquisition_end_utc"] == "20260718T155059"
    assert result["crid"] == "P05023"
    assert result["frame_coverage"] == "FULL"


def test_normalize_product_preserves_url_maturity_dates_and_polarization():
    product = normalize_product({
        "granuleName": GRANULE,
        "url": PROVISIONAL_URL,
        "processingLevel": "GCOV",
    })
    assert product is not None
    assert product["product"] == "GCOV"
    assert product["maturity"] == "PROVISIONAL"
    assert product["relative_orbit"] == "151"
    assert product["start_time_utc"] == "20260718T155041"
    assert product["main_band_polarization"] == "HH+HV"
    assert product["frame_coverage"] == "FULL"


def test_normalize_product_constructs_url_only_from_explicit_collection_maturity():
    product = normalize_product({
        "granuleName": GRANULE,
        "processingLevel": "GCOV",
        "collectionName": "NISAR_L2_GCOV_PROVISIONAL_V1",
    })
    assert product is not None
    assert product["maturity"] == "PROVISIONAL"
    assert product["download_url"] == PROVISIONAL_URL


def test_unknown_maturity_is_not_guessed_from_the_crid():
    product = normalize_product({"granuleName": GRANULE, "processingLevel": "GCOV"})
    assert product is not None
    assert product["maturity"] == "UNKNOWN"
    assert product["download_url"] is None


def test_search_uses_documented_asf_json_and_full_frame_filter(monkeypatch):
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
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("discover_gcov_products.urllib.request.urlopen", fake_urlopen)
    search_catalogue(
        "POLYGON ((89.5 24.4, 89.8 24.4, 89.8 24.7, 89.5 24.7, 89.5 24.4))",
        date(2026, 6, 17),
        date(2026, 10, 31),
        "PROVISIONAL",
        None,
        None,
        100,
        20,
        "FULL",
    )
    params = parse_qs(urlparse(captured["url"]).query)
    assert params["output"] == ["json"]
    assert params["frameCoverage"] == ["FULL"]
    assert params["processingLevel"] == ["GCOV"]


def test_validate_aoi_rejects_non_polygon():
    import pytest
    with pytest.raises(ValueError):
        validate_aoi("POINT (90 25)")


def test_validate_aoi_rejects_self_intersection():
    import pytest
    with pytest.raises(ValueError):
        validate_aoi("POLYGON ((0 0, 2 2, 0 2, 2 0, 0 0))")
