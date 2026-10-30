import json

import pytest

from river_shift.transects import measure_bankline_migration


def write_collection(path, features):
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )
    return path


def line_feature(coords, properties=None):
    return {
        "type": "Feature",
        "properties": properties or {},
        "geometry": {"type": "LineString", "coordinates": coords},
    }


def prepare_case(tmp_path, *, reverse_transects=False, multiple_before=False):
    before_lines = [[0, 100], [100, 100]]
    after_lines = [[0, 120], [100, 120]]
    if multiple_before:
        before_geometry = {
            "type": "MultiLineString",
            "coordinates": [before_lines, [[0, 150], [100, 150]]],
        }
    else:
        before_geometry = {"type": "LineString", "coordinates": before_lines}

    before = write_collection(tmp_path / "before.geojson", [{
        "type": "Feature", "properties": {}, "geometry": before_geometry
    }])
    after = write_collection(tmp_path / "after.geojson", [
        line_feature(after_lines)
    ])

    transects = []
    for index, x in enumerate([20, 40, 60], start=1):
        coordinates = [[x, 0], [x, 200]]
        if reverse_transects:
            coordinates.reverse()
        transects.append(line_feature(coordinates, {"transect_id": f"T{index:02d}"}))
    transects_path = write_collection(tmp_path / "transects.geojson", transects)
    return before, after, transects_path


def run_case(tmp_path, before, after, transects, *, crs="EPSG:32646", positive="toward_channel",
             before_date="2026-06-01", after_date="2026-09-01"):
    return measure_bankline_migration(
        before_bankline_path=str(before),
        after_bankline_path=str(after),
        transects_path=str(transects),
        input_crs=crs,
        before_date=before_date,
        after_date=after_date,
        positive_direction_label=positive,
        source_mission="NISAR",
        source_product="GCOV",
        maturity="PROVISIONAL",
        output_dir=str(tmp_path / "result"),
    )


def test_signed_migration_measures_after_minus_before_chainage(tmp_path):
    before, after, transects = prepare_case(tmp_path)
    result = run_case(tmp_path, before, after, transects)
    metrics = result["metrics"]
    assert metrics["valid_transect_count"] == 3
    assert metrics["invalid_transect_count"] == 0
    assert metrics["mean_signed_displacement_m"] == pytest.approx(20.0)
    assert metrics["median_signed_displacement_m"] == pytest.approx(20.0)
    assert metrics["mean_net_rate_m_per_year"] == pytest.approx(20.0 / ((92 / 365.25)))
    assert result["inputs"]["positive_direction_label"] == "toward_channel"
    assert (tmp_path / "result" / "bankline_migration.csv").exists()
    assert (tmp_path / "result" / "bankline_migration_transects.geojson").exists()
    assert (tmp_path / "result" / "bankline_migration_summary.json").exists()


def test_reversing_transect_direction_reverses_displacement_sign(tmp_path):
    before, after, transects = prepare_case(tmp_path, reverse_transects=True)
    result = run_case(tmp_path, before, after, transects, positive="toward_land")
    assert result["metrics"]["mean_signed_displacement_m"] == pytest.approx(-20.0)


def test_multiple_bankline_intersections_mark_transect_invalid(tmp_path):
    before, after, transects = prepare_case(tmp_path, multiple_before=True)
    result = run_case(tmp_path, before, after, transects)
    assert result["metrics"]["valid_transect_count"] == 0
    assert result["metrics"]["invalid_transect_count"] == 3
    assert all(row["status"] == "before_no_unique_intersection" for row in result["transects"])
    assert result["metrics"]["mean_signed_displacement_m"] is None


def test_geographic_crs_is_rejected(tmp_path):
    before, after, transects = prepare_case(tmp_path)
    with pytest.raises(ValueError, match="projected CRS"):
        run_case(tmp_path, before, after, transects, crs="EPSG:4326")


def test_dates_and_positive_direction_are_required(tmp_path):
    before, after, transects = prepare_case(tmp_path)
    with pytest.raises(ValueError, match="after_date must be later"):
        run_case(tmp_path, before, after, transects, before_date="2026-09-01", after_date="2026-06-01")
    with pytest.raises(ValueError, match="positive_direction_label"):
        run_case(tmp_path, before, after, transects, positive="  ")
