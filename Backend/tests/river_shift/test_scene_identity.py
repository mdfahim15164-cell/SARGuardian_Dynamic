from science_adapter.river_shift.data_access.scene_identity import parse_gcov_granule_identity


OFFICIAL_EXAMPLE = (
    "NISAR_L2_PR_GCOV_025_151_A_011_4005_DHDH_A_"
    "20260718T155041_20260718T155059_P05023_N_P_J_001.h5"
)


def test_parse_official_gcov_product_name():
    identity = parse_gcov_granule_identity(OFFICIAL_EXAMPLE)
    assert identity is not None
    assert identity["instrument_band"] == "L"
    assert identity["processing_level"] == "L2"
    assert identity["relative_orbit"] == "151"
    assert identity["flight_direction"] == "ASCENDING"
    assert identity["frame_number"] == "011"
    assert identity["acquisition_mode"] == "4005"
    assert identity["polarization_mode"] == "DHDH"
    assert identity["crid"] == "P05023"
    assert identity["start_time_utc"] == "2026-07-18T15:50:41Z"


def test_s_band_is_preserved_as_a_distinct_instrument_band():
    name = OFFICIAL_EXAMPLE.replace("NISAR_L2_", "NISAR_S2_")
    identity = parse_gcov_granule_identity(name)
    assert identity is not None
    assert identity["instrument_band"] == "S"


def test_malformed_name_is_not_guessed():
    assert parse_gcov_granule_identity("NISAR_NOT_A_GCOV_PRODUCT.h5") is None
