from pydantic import BaseModel

class Flight(BaseModel):
    number: str
    origin: str
    eta: str
    arrival_info: str