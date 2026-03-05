from pydantic import BaseModel
from typing import List
from Models import Flight

class Airport(BaseModel):
    name: str
    iata: str
    icao: str
    lat: float | None = None
    lon: float | None = None
    flights_list: List[Flight]