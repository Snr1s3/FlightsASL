from typing import List

from pydantic import BaseModel

from .flight import Flight

class Airport(BaseModel):
    name: str
    iata: str
    icao: str
    lat: float | None = None
    lon: float | None = None
    flights_list: List[Flight]