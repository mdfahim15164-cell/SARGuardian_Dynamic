#!/usr/bin/env python3
"""Classify one NISAR GCOV diagonal layer as open-water candidates."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2] / "Backend"
sys.path.insert(0, str(BACKEND_ROOT))

from science_adapter.river_shift.data_access.gcov_reader import read_gcov
from science_adapter.river_shift.data_access.raster_export import write_water_candidate_geotiff
from science_adapter.river_shift.flood.water_classification import classify_open_water


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="NISAR GCOV HDF5 file")
    parser.add_argument("--output", required=True, type=Path, help="Output open-water candidate GeoTIFF")
    parser.add_argument("--frequency", choices=("A", "B"), default="A")
    parser.add_argument("--term", choices=("HHHH", "HVHV", "VVVV", "VHVH", "RHRH", "RVRV"), default="VVVV")
    parser.add_argument("--method", choices=("otsu", "fixed"), default="otsu")
    parser.add_argument("--threshold-db", type=float, default=None, help="Required only for --method fixed")
    parser.add_argument("--minimum-valid-pixels", type=int, default=100)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.method == "fixed" and args.threshold_db is None:
        raise SystemExit("--threshold-db is required when --method fixed")
    if args.method == "otsu" and args.threshold_db is not None:
        raise SystemExit("--threshold-db cannot be supplied with --method otsu")

    gcov = read_gcov(args.input, frequency=args.frequency, covariance_term=args.term)
    result = classify_open_water(
        gcov.power,
        valid_mask=gcov.valid_mask,
        method=args.method,
        threshold_db=args.threshold_db,
        minimum_valid_pixels=args.minimum_valid_pixels,
    )
    output = write_water_candidate_geotiff(
        args.output,
        gcov,
        result.water_mask,
        result.valid_mask,
        threshold_db=result.threshold_db,
        classification_method=result.method,
    )

    report = {
        "status": "candidate_classification",
        "source_product": "NISAR GCOV",
        "source_path": str(args.input),
        "frequency": gcov.frequency,
        "covariance_term": gcov.covariance_term,
        "epsg": gcov.epsg,
        "grid_shape_yx": list(gcov.shape),
        "pixel_area_m2": gcov.pixel_area_m2,
        "method": result.method,
        "threshold_db": result.threshold_db,
        "valid_pixel_count": result.valid_pixel_count,
        "open_water_candidate_count": result.water_candidate_count,
        "open_water_candidate_area_km2": result.water_candidate_count * gcov.pixel_area_m2 / 1_000_000.0,
        "output_geotiff": str(output),
        "independent_validation": "not_performed",
        "interpretation_warning": (
            "This is a single-scene low-backscatter open-water candidate mask. "
            "It is not a validated flood map and does not measure newly inundated area."
        ),
    }
    sidecar = output.with_suffix(".json")
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
