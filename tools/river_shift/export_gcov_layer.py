#!/usr/bin/env python3
"""Extract one calibrated GCOV diagonal covariance term to an AOI-clipped GeoTIFF."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from inspect_gcov_product import inspect_product


SUPPORTED_TERMS = {"HHHH", "HVHV", "VVVV", "VHVH", "RHRH", "RVRV"}


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def export_layer(
    product: Path,
    output: Path,
    *,
    frequency: str,
    term: str,
    aoi_wkt: str,
    maturity: str,
) -> dict[str, Any]:
    if term not in SUPPORTED_TERMS:
        raise ValueError(f"term must be one of {sorted(SUPPORTED_TERMS)}.")
    if frequency not in {"frequencyA", "frequencyB"}:
        raise ValueError("frequency must be frequencyA or frequencyB.")
    if maturity not in {"BETA", "PROVISIONAL", "UNKNOWN"}:
        raise ValueError("maturity must be BETA, PROVISIONAL or UNKNOWN.")
    if not aoi_wkt.strip().upper().startswith("POLYGON"):
        raise ValueError("AOI must be a WGS84 POLYGON WKT.")

    inventory = inspect_product(product)
    expected_suffix = f"/science/LSAR/GCOV/grids/{frequency}/{term}"
    matches = [
        item["subdataset"]
        for item in inventory["available_diagonal_terms"]
        if item["subdataset"].endswith(expected_suffix)
    ]
    if not matches:
        raise ValueError(f"Requested GCOV layer was not found: {frequency}/{term}.")

    subdataset = matches[0]
    output.parent.mkdir(parents=True, exist_ok=True)
    clipped = output.with_name(output.stem + ".aoi-intermediate.tif")

    # Warp the selected HDF5 subdataset directly to the AOI. This avoids first
    # materializing a potentially multi-gigabyte full-frame raster.
    run([
        "gdalwarp", "-overwrite", "-of", "GTiff",
        "-cutline", aoi_wkt,
        "-cutline_srs", "EPSG:4326",
        "-crop_to_cutline",
        "-dstalpha",
        "-co", "TILED=YES",
        "-co", "COMPRESS=DEFLATE",
        subdataset, str(clipped),
    ])
    run([
        "gdal_translate", "-of", "COG",
        "-co", "COMPRESS=DEFLATE",
        "-co", "BLOCKSIZE=512",
        str(clipped), str(output),
    ])

    clipped.unlink(missing_ok=True)
    metadata = {
        "schema_version": 1,
        "source_product_file": str(product.resolve()),
        "source_product_type": "NISAR_L2_GCOV",
        "maturity": maturity,
        "frequency": frequency,
        "covariance_term": term,
        "output_cog": str(output.resolve()),
        "input_dataset": subdataset,
        "aoi_wkt": aoi_wkt,
        "units": "gamma0_power",
        "gdal_version": inventory["gdal_version"],
    }
    output.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", required=True, type=Path)
    parser.add_argument("--frequency", choices=("frequencyA", "frequencyB"), default="frequencyA")
    parser.add_argument("--term", choices=sorted(SUPPORTED_TERMS), required=True)
    parser.add_argument("--maturity", choices=("BETA", "PROVISIONAL", "UNKNOWN"), required=True)
    parser.add_argument("--aoi-wkt", required=True, help="WGS84 polygon WKT copied from the study-area AOI.")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = export_layer(
            args.product, args.out, frequency=args.frequency, term=args.term,
            aoi_wkt=args.aoi_wkt, maturity=args.maturity,
        )
        print(f"GCOV_COG={result['output_cog']}")
        print(f"GCOV_TERM={args.frequency}/{args.term}")
        print(f"MATURITY={args.maturity}")
        return 0
    except Exception as exc:
        print(f"ERROR={exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
