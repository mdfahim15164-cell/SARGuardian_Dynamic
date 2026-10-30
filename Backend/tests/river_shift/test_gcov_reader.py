import h5py
import numpy as np
import pytest

from science_adapter.river_shift.data_access.gcov_reader import GcovReadError, read_gcov


def _write_fixture(path):
    with h5py.File(path, "w") as h5:
        base = h5.create_group("/science/LSAR/GCOV/grids/frequencyA")
        data = base.create_dataset("VVVV", data=np.array([[0.2, 0.1, 0.0], [0.3, np.nan, 0.4]], dtype=np.float32))
        data.attrs["units"] = "linear gamma0 power"
        base.create_dataset("xCoordinates", data=np.array([500005.0, 500015.0, 500025.0]))
        base.create_dataset("yCoordinates", data=np.array([2800005.0, 2799995.0]))
        base.create_dataset("projection", data=np.array(32646, dtype=np.int32))
        base.create_dataset("numberOfLooks", data=np.array([[4, 4, 0], [4, 4, 4]], dtype=np.float32))


def test_read_gcov_extracts_grid_and_masks_invalid_pixels(tmp_path):
    path = tmp_path / "synthetic_gcov.h5"
    _write_fixture(path)
    result = read_gcov(path, frequency="A", covariance_term="VVVV")
    assert result.shape == (2, 3)
    assert result.epsg == 32646
    assert result.valid_mask.tolist() == [[True, True, False], [True, False, True]]
    assert result.units == "linear gamma0 power"
    assert result.pixel_area_m2 == pytest.approx(100.0)


def test_missing_covariance_layer_is_rejected(tmp_path):
    path = tmp_path / "synthetic_gcov.h5"
    _write_fixture(path)
    with pytest.raises(GcovReadError):
        read_gcov(path, covariance_term="HHHH")


def test_invalid_frequency_is_rejected(tmp_path):
    path = tmp_path / "synthetic_gcov.h5"
    _write_fixture(path)
    with pytest.raises(GcovReadError):
        read_gcov(path, frequency="C")


def test_read_gcov_resolves_cf_grid_mapping_attributes(tmp_path):
    path = tmp_path / "synthetic_gcov_cf.h5"
    with h5py.File(path, "w") as h5:
        base = h5.create_group("/science/LSAR/GCOV/grids/frequencyA")
        base.create_dataset("VVVV", data=np.full((2, 2), 0.2, dtype=np.float32))
        base.create_dataset("xCoordinates", data=np.array([500005.0, 500015.0]))
        base.create_dataset("yCoordinates", data=np.array([2800005.0, 2799995.0]))
        projection = base.create_dataset("projection", data=np.array(0, dtype=np.int32))
        projection.attrs["grid_mapping_name"] = "transverse_mercator"
        projection.attrs["latitude_of_projection_origin"] = 0.0
        projection.attrs["longitude_of_central_meridian"] = 93.0
        projection.attrs["scale_factor_at_central_meridian"] = 0.9996
        projection.attrs["false_easting"] = 500000.0
        projection.attrs["false_northing"] = 0.0
        projection.attrs["semi_major_axis"] = 6378137.0
        projection.attrs["inverse_flattening"] = 298.257223563

    result = read_gcov(path, frequency="A", covariance_term="VVVV")
    assert result.crs.is_projected
    assert result.epsg is not None or "TRANSVERSE MERCATOR" in result.crs.to_wkt().upper()
