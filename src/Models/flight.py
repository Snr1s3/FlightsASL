from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

_DEFAULT_LIMIT_MODEL = 100

class FlightBase(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
    )
    id_flight: Optional[str] = Field(
        default=None,
        description="Type: arrivals/departures",
        min_length=8,
        max_length=10,
    )
    number: Optional[str] = Field(
        default=None,
        description="Published flight identifier (e.g., AS123)",
        min_length=1,
        max_length=16,
    )
class Flight(FlightBase):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
    )
    origin: Optional[str] = Field(
        default=None,
        description="Origin airport name",
        min_length=1,
        max_length=120,
    )
    origin_iata: Optional[str] = Field(
        default=None,
        description="Origin airport IATA code (e.g., JFK)",
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
        description="Destination airport IATA code (e.g., BCN)",
        min_length=3,
        max_length=8,
    )
    scheduled_departure: Optional[str] = Field(
        default=None,
        description="Scheduled departure formatted text",
        validation_alias=AliasChoices("departure_info", "arrival_info"),
        max_length=40,
    )
    utc_departure: Optional[int] = Field(
        default=None,
        description="Scheduled departure as UTC milliseconds",
    )
    scheduled_arrival: Optional[str] = Field(
        default=None,
        description="Scheduled arrival formatted text",
        validation_alias=AliasChoices("departure_info", "arrival_info"),
        max_length=40,
    )
    utc_arrival: Optional[int] = Field(
        default=None,
        description="Scheduled arrival as UTC milliseconds",
    )
    def __str__(self) -> str:
        return (
            f"Flight({self.number}| "
            f"airport_origin_iata={self.origin_iata} | airport_origin={self.origin} | "
            f"airport_dest_iata={self.destination_iata} | airport_dest={self.destination} | "
            f"departure={self.scheduled_departure} | arrival={self.scheduled_arrival})"
        )
    
class FlightDetail(Flight):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        populate_by_name=True,
    )
    lat: Optional[float] = Field(
        default=None,
        description="Latitude in decimal degrees",
    )
    lon: Optional[float] = Field(
        default=None,
        description="Longitude in decimal degrees",
    )

class FlightQuery(BaseModel):
    iata: str
    type: int = 1
    limit: int = _DEFAULT_LIMIT_MODEL
    page: int = 1
    asc: int = 1
