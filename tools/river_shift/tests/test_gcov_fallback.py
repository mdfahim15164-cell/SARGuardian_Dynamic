import json
from datetime import date

from discover_gcov_products import search_catalogue


GRANULE = "NISAR_L2_PR_GCOV_025_151_A_011_4005_DHDH_A_20260718T155041_20260718T155059_P05023_N_F_J_001"
URL = (
    "https://nisar.asf.earthdatacloud.nasa.gov/NISAR/"
    "NISAR_L2_GCOV_PROVISIONAL_V1/" + GRANULE + "/" + GRANULE + ".h5"
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_zero_strict_results_trigger_local_gcove_identity_fallback(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.full_url)
        if len(calls) == 1:
            return FakeResponse({"results": []})
        return FakeResponse({
            "results": [
                {"granuleName": GRANULE, "processingLevel": "GCOV", "url": URL},
                {"granuleName": "NISAR_L2_GUNW_001_151_A_011_20260718T155041_20260718T155059.h5", "processingLevel": "GUNW"},
            ]
        })

    monkeypatch.setattr("discover_gcov_products.urllib.request.urlopen", fake_urlopen)
    result = search_catalogue(
        "POLYGON ((89.6 24.4, 89.8 24.4, 89.8 24.6, 89.6 24.6, 89.6 24.4))",
        date(2026, 6, 17),
        date(2026, 10, 31),
        "PROVISIONAL",
        None,
        None,
        100,
        20,
        "ALL",
    )
    assert len(calls) == 2
    assert result["product_count"] == 1
    assert result["products"][0]["granule_name"] == GRANULE
    assert result["search_diagnostics"]["broader_query_used"] is True
    assert result["search_diagnostics"]["local_gcov_filter_applied"] is True
    assert result["query"]["local_gcov_fallback_used"] is True


def test_broader_search_without_gcov_records_is_not_mislabelled(monkeypatch):
    def fake_urlopen(request, timeout):
        return FakeResponse({"results": []})

    monkeypatch.setattr("discover_gcov_products.urllib.request.urlopen", fake_urlopen)
    result = search_catalogue(
        "POLYGON ((89.6 24.4, 89.8 24.4, 89.8 24.6, 89.6 24.6, 89.6 24.4))",
        date(2026, 6, 17),
        date(2026, 10, 31),
        "PROVISIONAL",
        None,
        None,
        100,
        20,
        "ALL",
    )
    assert result["product_count"] == 0
    assert result["search_diagnostics"]["broader_query_used"] is True
    assert not result["search_diagnostics"]["local_gcov_filter_applied"]
    assert any("both returned zero GCOV" in item for item in result["warnings"])
