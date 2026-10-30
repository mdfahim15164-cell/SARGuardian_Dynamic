from discover_gcov_products import normalize_product, parse_granule_metadata, validate_aoi


def test_parse_gcov_granule_metadata_from_product_name():
    name = "NISAR_L2_PR_GCOV_005_149_A_024_4005_DHDH_A_20261101T010203_20261101T010245_X05001_N_F_J_001"
    result = parse_granule_metadata(name)
    assert result["cycle"] == "005"
    assert result["relative_orbit"] == "149"
    assert result["orbit_direction"] == "A"
    assert result["frame"] == "024"
    assert result["bandwidth_mode"] == "4005"
    assert result["polarization_code"] == "DHDH"


def test_normalize_product_extracts_provisional_maturity():
    name = "NISAR_L2_PR_GCOV_005_149_A_024_4005_DHDH_A_20261101T010203_20261101T010245_X05001_N_F_J_001"
    url = "https://nisar.asf.earthdatacloud.nasa.gov/NISAR/NISAR_L2_GCOV_PROVISIONAL_V1/" + name + "/" + name + ".h5"
    product = normalize_product({"granuleName": name, "url": url, "processingLevel": "GCOV"})
    assert product is not None
    assert product["product"] == "GCOV"
    assert product["maturity"] == "PROVISIONAL"
    assert product["relative_orbit"] == "149"


def test_validate_aoi_rejects_non_polygon():
    import pytest
    with pytest.raises(ValueError):
        validate_aoi("POINT (90 25)")
