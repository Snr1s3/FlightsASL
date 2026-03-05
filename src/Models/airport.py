from pydantic import BaseModel

from .flight import Flight

class Airport(BaseModel):
    name: str
    iata: str
    icao: str
    lat: float
    lon: float 
    flights_list: list[Flight]