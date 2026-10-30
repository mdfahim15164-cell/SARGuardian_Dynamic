from datetime import date

import pytest

from science_adapter.river_shift.data_access.catalog import CatalogRequestError, search_gcov


AOI = "POLYGON ((89.6 25.0, 89.8 25.0, 89.8 25.2, 89.6 25.2, 89.6 25.0))"


def test_search_gcov_uses_gcov_and_provisional():
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
    assert result["requested_maturity_filter"] == "PROVISIONAL"
    assert result["catalogue_only"] is True
    assert result["data_downloaded"] is False
    assert result["scientific_analysis_performed"] is False
    assert result["result_count"] == 1
    scene = result["scenes"][0]
    assert scene["granule_name"] == "NISAR_TEST_GCOV.h5"
    assert scene["data_maturity"] == "PROVISIONAL"
    assert scene["catalogue_maturity_filter"] == "PROVISIONAL"
    assert scene["maturity_evidence"] == "product_metadata"


def test_missing_product_maturity_is_not_fabricated_from_query_filter():
    class Product:
        properties = {"fileName": "NISAR_TEST_GCOV.h5", "processingLevel": "GCOV"}

    result = search_gcov(AOI, "2026-06-17", "2026-07-20", search_function=lambda **_: [Product()])
    scene = result["scenes"][0]
    assert scene["data_maturity"] is None
    assert scene["catalogue_maturity_filter"] == "PROVISIONAL"
    assert scene["maturity_evidence"] == "ASF query filter only"


@pytest.mark.parametrize("bad_wkt", ["not wkt", "POINT (89 25)"])
def test_invalid_geometry_rejected(bad_wkt):
    with pytest.raises(CatalogRequestError):
        search_gcov(bad_wkt, date(2026, 6, 17), date(2026, 7, 20), search_function=lambda **_: [])


def test_invalid_date_order_and_maturity_rejected():
    with pytest.raises(CatalogRequestError):
        search_gcov(AOI, "2026-07-20", "2026-06-17", search_function=lambda **_: [])
    with pytest.raises(CatalogRequestError):
        search_gcov(AOI, "2026-06-17", "2026-07-20", maturity="UNKNOWN", search_function=lambda **_: [])
