from science_adapter.river_shift.data_access.scene_identity import parse_gcov_granule_identity


EXAMPLE = (
    "NISAR_L2_PR_GCOV_008_029_A_010_0005_NASV_A_"
    "20251031T044409_20251031T044425_P05000_N_P_J_001.h5"
)


def test_parse_official_gcov_product_name():
    identity = parse_gcov_granule_identity(EXAMPLE)
    assert identity is not None
    assert identity["relative_orbit"] == "029"
    assert identity["flight_direction"] == "ASCENDING"
    assert identity["frame_number"] == "010"
    assert identity["crid"] == "P05000"
    assert identity["start_time_utc"] == "2025-10-31T04:44:09Z"


def test_malformed_name_is_not_guessed():
    assert parse_gcov_granule_identity("NISAR_NOT_A_GCOV_PRODUCT.h5") is None
