"""Parse stable acquisition identity fields from official NISAR product names."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re
from typing import Any


def parse_gcov_granule_identity(granule_name: str) -> dict[str, Any] | None:
    """Return identity fields from a GCOV name; return None rather than guessing."""
    if not isinstance(granule_name, str) or not granule_name.strip():
        return None
    stem = Path(granule_name.strip()).name
    if stem.lower().endswith(".h5"):
        stem = stem[:-3]
    parts = stem.split("_")
    try:
        marker = parts.index("GCOV")
    except ValueError:
        return None
    prefix, suffix = parts[:marker], parts[marker + 1:]
    if not prefix or prefix[0] != "NISAR" or not any(item in {"L2", "S2"} for item in prefix):
        return None
    instrument_level = next((item for item in prefix if item in {"L1", "L2", "L3", "S1", "S2", "S3"}), None)
    processing_type = next((item for item in prefix if item in {"PR", "UR", "OD"}), None)
    if instrument_level is None or processing_type is None or len(suffix) != 14:
        return None

    (cycle, relative_orbit, direction, frame, mode, polarization, source,
     start_time, end_time, crid, orbit_accuracy, coverage, location, counter) = suffix
    if not re.fullmatch(r"\d{3}", cycle) or not re.fullmatch(r"\d{3}", relative_orbit):
        return None
    if direction not in {"A", "D"} or not re.fullmatch(r"\d{3}", frame):
        return None
    if len(mode) != 4 or len(polarization) != 4 or source not in {"A", "M"}:
        return None
    if not re.fullmatch(r"\d{8}T\d{6}", start_time) or not re.fullmatch(r"\d{8}T\d{6}", end_time):
        return None
    try:
        start_dt = datetime.strptime(start_time, "%Y%m%dT%H%M%S")
        end_dt = datetime.strptime(end_time, "%Y%m%dT%H%M%S")
    except ValueError:
        return None
    if end_dt < start_dt or not crid or not re.fullmatch(r"\d{3}", counter):
        return None
    return {
        "instrument_band": instrument_level[0],
        "processing_level": instrument_level,
        "processing_type": processing_type,
        "cycle_number": cycle,
        "relative_orbit": relative_orbit,
        "flight_direction": "ASCENDING" if direction == "A" else "DESCENDING",
        "frame_number": frame,
        "acquisition_mode": mode,
        "polarization_mode": polarization,
        "source_mode": source,
        "start_time_utc": start_dt.isoformat() + "Z",
        "stop_time_utc": end_dt.isoformat() + "Z",
        "crid": crid,
        "orbit_accuracy": orbit_accuracy,
        "coverage": coverage,
        "location_code": location,
        "product_counter": counter,
    }
