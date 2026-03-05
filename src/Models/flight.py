from typing import Optional

from pydantic import BaseModel, Field


class Flight(BaseModel):
    number: Optional[str] = Field(
        default=None,
        description="Published flight identifier (e.g., AS123)",
    )
    origin: Optional[str] = Field(
        default=None,
        description="Origin airport IATA code (e.g., SEA)",
    )
    eta: Optional[str] = Field(
        default=None,
        description="Estimated time of arrival in ISO 8601 (e.g., 2026-03-05T12:30:00Z)",
    )
    arrival_info: Optional[str] = Field(
        default=None,
        description="Status or gate information for arrivals",
    )