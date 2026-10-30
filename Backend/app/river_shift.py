from __future__ import annotations

import logging
import math
from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from pyproj import Geod
from shapely.geometry import Polygon

from .auth import get_current_user
from science_adapter.river_shift.data_access.catalog import CatalogRequestError, search_gcov

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/river-shift", tags=["RiverShift"])
_GEOD = Geod(ellps="WGS84")
_MAX_AOI_AREA_KM2 = 1_000
_MAX_DATE_WINDOW_DAYS = 366


class RiverShiftCatalogRequest(BaseModel):
    """Request model for metadata-only NISAR GCOV discovery."""

    coordinates: list[list[float]] = Field(min_length=4, max_length=1000)
    start_date: date
    end_date: date
    data_maturity: Literal["PROVISIONAL", "BETA"] = "PROVISIONAL"
    max_results: int = Field(default=100, ge=1, le=500)


def _validate_aoi(coordinates: list[list[float]]) -> Polygon:
    normalized: list[tuple[float, float]] = []
    for point in coordinates:
        if len(point) != 2:
            raise HTTPException(status_code=422, detail="Each coordinate must be [longitude, latitude].")
        lon, lat = point
        if not math.isfinite(lon) or not math.isfinite(lat):
            raise HTTPException(status_code=422, detail="AOI coordinates must be finite.")
        if not -180 <= lon <= 180 or not -90 <= lat <= 90:
            raise HTTPException(status_code=422, detail="AOI must use WGS84 longitude/latitude.")
        normalized.append((lon, lat))

    if normalized[0] != normalized[-1]:
        raise HTTPException(status_code=422, detail="AOI polygon must repeat its first point at the end.")
    polygon = Polygon(normalized)
    if polygon.is_empty or polygon.area <= 0 or not polygon.is_valid:
        raise HTTPException(status_code=422, detail="AOI must be one valid, non-empty polygon.")
    area_m2, _ = _GEOD.geometry_area_perimeter(polygon)
    area_km2 = abs(area_m2) / 1_000_000
    if not 0 < area_km2 <= _MAX_AOI_AREA_KM2:
        raise HTTPException(status_code=422, detail=f"AOI area must be between 0 and {_MAX_AOI_AREA_KM2} km².")
    return polygon


@router.post("/catalog/search")
async def search_river_shift_gcov_catalog(
    request: RiverShiftCatalogRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Search actual ASF NISAR GCOV metadata; no files are downloaded or processed."""
    del current_user  # Authentication is required; search itself is not user-specific.
    if request.end_date < request.start_date:
        raise HTTPException(status_code=422, detail="end_date must not be earlier than start_date.")
    if (request.end_date - request.start_date).days > _MAX_DATE_WINDOW_DAYS:
        raise HTTPException(status_code=422, detail=f"Date window cannot exceed {_MAX_DATE_WINDOW_DAYS} days.")

    polygon = _validate_aoi(request.coordinates)
    try:
        result = await run_in_threadpool(
            search_gcov,
            polygon.wkt,
            request.start_date,
            request.end_date,
            maturity=request.data_maturity,
            max_results=request.max_results,
        )
    except CatalogRequestError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.warning("RiverShift GCOV catalogue search failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="ASF GCOV catalogue search failed. Retry later.") from None

    result["aoi_area_km2"] = abs(_GEOD.geometry_area_perimeter(polygon)[0]) / 1_000_000
    result["user_notice"] = (
        "This is an authenticated metadata-only archive search. It does not download NISAR data "
        "or establish scientific processing eligibility."
    )
    return result
