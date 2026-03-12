from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class Flight(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
    )
    number: Optional[str] = Field(
        default=None,
        description="Published flight identifier (e.g., AS123)",
        min_length=1,
        max_length=16,
    )
    origin: Optional[str] = Field(
        default=None,
        description="Origin airport name",
        min_length=1,
        max_length=120,
    )
    origin_iata: Optional[str] = Field(
        default=None,
        description="Airport being queried (e.g., BCN)",
        min_length=3,
        max_length=8,
    )
    destination: Optional[str] = Field(
        default=None,
        description="Destination airport name",
        min_length=1,
        max_length=120,
    )
    destination_iata: Optional[str] = Field(
        default=None,
        description="Airport being queried (e.g., BCN)",
        min_length=3,
        max_length=8,
    )
    scheduled_departure: Optional[str] = Field(
        default=None,
        description="Scheduled departure formatted text",
        validation_alias=AliasChoices("departure_info", "arrival_info"),
        max_length=40,
    )
    scheduled_arrival: Optional[str] = Field(
        default=None,
        description="Scheduled arrival formatted text",
        validation_alias=AliasChoices("departure_info", "arrival_info"),
        max_length=40,
    )

    def __str__(self) -> str:
        return (
            f"Flight({self.number}| "
            f"airport_origin_iata={self.origin_iata} | airport_origin={self.origin} | "
            f"airport_dest_iata={self.destination_iata} | airport_dest={self.destination} | "
            f"departure={self.scheduled_departure} | arrival={self.scheduled_arrival})"
        )