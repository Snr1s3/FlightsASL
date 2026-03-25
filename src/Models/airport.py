from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Airport(BaseModel):
    name: str = Field(..., description="Human-readable airport name")
    iata: Optional[str] = Field(
        default=None,
        description="Three-letter IATA identifier (e.g., LAX)",
    )
    icao: Optional[str] = Field(
        default=None,
        description="Four-letter ICAO identifier (e.g., KLAX)",
    )
    lat: Optional[float] = Field(
        default=None,
        description="Latitude in decimal degrees",
    )
    lon: Optional[float] = Field(
        default=None,
        description="Longitude in decimal degrees",
    )
    search: Optional[bool] = Field(
        default= False,
        description="Was searched by the user"
    )


class AirportSearchRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Airport search text")