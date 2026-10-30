import numpy as np
import pytest

rasterio = pytest.importorskip("rasterio")

from pyproj import CRS

from science_adapter.river_shift.data_access.gcov_reader import GcovRaster
from science_adapter.river_shift.data_access.raster_export import (
    RasterExportError,
    write_water_candidate_geotiff,
)


def _gcov_fixture():
    return GcovRaster(
        power=np.ones((2, 3), dtype=np.float32),
        valid_mask=np.ones((2, 3), dtype=bool),
        x_coordinates=np.array([500005.0, 500015.0, 500025.0]),
        y_coordinates=np.array([2800005.0, 2799995.0]),
        crs_wkt=CRS.from_epsg(32646).to_wkt(),
        epsg=32646,
        frequency="A",
        covariance_term="VVVV",
        source_path="synthetic-gcov.h5",
        units="linear gamma0 power",
    )


def test_export_writes_georeferenced_candidate_mask_and_nodata(tmp_path):
    gcov = _gcov_fixture()
    water = np.array([[True, False, True], [False, True, False]])
    valid = np.array([[True, True, False], [True, True, True]])
    output = tmp_path / "candidate.tif"

    write_water_candidate_geotiff(
        output, gcov, water, valid,
        threshold_db=-15.0, classification_method="fixed",
    )

    with rasterio.open(output) as dataset:
        assert dataset.crs.to_epsg() == 32646
        assert dataset.nodata == 255
        assert dataset.res == (10.0, 10.0)
        assert dataset.read(1).tolist() == [[1, 0, 255], [0, 1, 0]]
        tags = dataset.tags()
        assert tags["source_product"] == "NISAR GCOV"
        assert tags["interpretation"] == "candidate open water; not independently validated"


def test_export_rejects_invalid_validity_mask(tmp_path):
    gcov = _gcov_fixture()
    valid = np.ones((2, 3), dtype=float)
    valid[0, 0] = np.nan
    with pytest.raises(RasterExportError):
        write_water_candidate_geotiff(
            tmp_path / "candidate.tif",
            gcov,
            np.zeros((2, 3), dtype=bool),
            valid,
            threshold_db=-15.0,
            classification_method="fixed",
        )
