from datetime import date

import pytest

from river_shift.science.data_access.catalog import CatalogRequestError, search_gcov


AOI = "POLYGON ((89.6 25.0, 89.8 25.0, 89.8 25.2, 89.6 25.2, 89.6 25.0))"


def test_search_gcov_uses_gc ow_and_provisional():
    captured = {}

    class Product:
        properties = {
            "fileName": "NISAR_TEST_GCOV.h5",
            "processingLevel": "GCOV",
            "dataMaturity": "PROVISIONAL",
            "startTime": "2026-07-01T00:00:00Z",
            "flightDirection": "ASCENDING",
            "pathNumber": 42,
            "url": "https://example.invalid/product.h5",
        }

    def fake_search(**kwargs):
        captured.update(kwargs)
        return [Product()]

    result = search_gcov(AOI, "2026-06-17", "2026-07-20", search_function=fake_search)
    assert captured["dataset"] == "NISAR"
    assert captured["processingLevel"] == "GCOV"
    assert captured["dataMaturity"] == "PROVISIONAL"
    assert result["catalogue_only"] is True
    assert result["data_downloaded"] is False
    assert result["scientific_analysis_performed"] is False
    assert result["result_count"] == 1
    assert result["scenes"][0]["granule_name"] == "NISAR_TEST_GCOV.h5"


@pytest.mark.parametrize("bad_wkt", ["not wkt", "POINT (89 25)"])
def test_invalid_geometry_rejected(bad_wkt):
    with pytest.raises(CatalogRequestError):
        search_gcov(bad_wkt, date(2026, 6, 17), date(2026, 7, 20), search_function=lambda **_: [])


def test_invalid_date_order_and_maturity_rejected():
    with pytest.raises(CatalogRequestError):
        search_gcov(AOI, "2026-07-20", "2026-06-17", search_function=lambda **_: [])
    with pytest.raises(CatalogRequestError):
        search_gcov(AOI, "2026-06-17", "2026-07-20", maturity="UNKNOWN", search_function=lambda **_: [])
