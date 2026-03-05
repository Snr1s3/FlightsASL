from __future__ import annotations
from typing import Optional

from pydantic import BaseModel, Field

from .flight import Flight


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
    arrivals_list: list[Flight] = Field(
        default_factory=list,
        description="Flights scheduled to land at this airport",
    )

    departures_list: list[Flight] = Field(
        default_factory=list,
        description="Flights scheduled to depart from this airport",
    )