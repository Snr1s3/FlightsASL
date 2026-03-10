import re
from typing import Any, List

from fastapi import APIRouter, Depends
from FlightRadar24 import FlightRadar24API

from src.db.db_connection import MongoConnector
from src.Models.airport import Airport

router = APIRouter(
    prefix="/api/airport",
    tags=["airport"],
    responses={404: {"description": "Not found"}}
)
fr_api = FlightRadar24API()

def get_mongo() -> MongoConnector:
    return MongoConnector()

mongo_dependency = Depends(get_mongo)

@router.post("/save")
async def save_airport(airport: Airport, mongo: MongoConnector = mongo_dependency):
    if await airport_exists(airport, mongo):
        print("Duplicat")
        return [{"Duplicated":"This airport already exists"}]
    result = mongo.insert_one("FLIGHTSASL", airport.model_dump())

    return {
        "acknowledged": result.acknowledged,
        "inserted_id": str(result.inserted_id),
    }

@router.get("/search")
async def search_airport(name: str) -> list[Airport]:
    print(f"Cercant informació per a: {name}")
    resultats = fr_api.search(name)
    aeroports = await _parse_results(resultats)
    if not aeroports:
        print("No s'han trobat aeroports.")
        return []
    return aeroports

@router.get("/all")
async def get_all(mongo: MongoConnector = mongo_dependency) -> list[Airport]:
    aeroports = mongo.find("FLIGHTSASL","")
    return aeroports

async def airport_exists(airport: Airport, mongo: MongoConnector) -> bool:
    result = mongo.find_one("FLIGHTSASL", {"name": airport.name})
    return result is not None

async def _parse_results(resultats: Any) -> List[Airport]:
    if not isinstance(resultats, dict):
        return []
    aeroports_raw = resultats.get("airport", []) or []
    return [from_api(item) for item in aeroports_raw]

def from_api(data: dict) -> Airport:
    label = (data.get("label") or "").strip()
    detail = data.get("detail") or {}
    match = re.search(r"\(([^/]+)\s*/\s*([^)]+)\)", label)
    iata = match.group(1).strip() if match else (data.get("id") or "")
    icao = match.group(2).strip() if match else ""
    name = label.split(" (")[0].strip() if label else (data.get("id") or "")
    return Airport(
        name=name,
        iata=iata,
        icao=icao,
        lat=detail.get("lat"),
        lon=detail.get("lon"),
    )