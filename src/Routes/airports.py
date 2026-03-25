import re
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from FlightRadar24 import FlightRadar24API

from db.db_connection import PostgresConnector, get_pg
from Models.airport import Airport, AirportSearchRequest

router = APIRouter(
    prefix="/api/airport",
    tags=["airport"],
    responses={404: {"description": "Not found"}}
)

fr_api = FlightRadar24API()

pg_dependency = Depends(get_pg)

@router.get("/all")
async def get_all(pg: PostgresConnector = pg_dependency) -> list[Airport]:
    aeroports = pg.execute("SELECT * FROM airports WHERE search IS TRUE ORDER BY iata", fetch="all")
    if aeroports:
        return aeroports
    return []

@router.post("/save")
async def save_airport(airport: Airport, pg: PostgresConnector = pg_dependency):
    result = await _save_airport(airport, pg, True)
    return result

@router.post("/search")
async def search_airport(payload: AirportSearchRequest) -> list[Airport]:
    aeroports = await _search_airport(payload.name)
    return aeroports

async def _save_airport(airport: Airport, pg: PostgresConnector, search: bool):
    if await airport_exists(airport.iata, pg):
        raise HTTPException(
            status_code=409,
            detail={"error": "airport_already_exists", "message": "This airport already exists"},
        )
    
    result = pg.insert_one(
        """
        INSERT INTO airports (name, iata, icao, lat, lon, search)
        VALUES (%s, %s, %s, %s, %s,%s)
        """,
        (airport.name, airport.iata, airport.icao, airport.lat, airport.lon, search),
    )
    return {
        "inserted": result > 0,
        "rows_affected": result,
    }

async def _search_airport(name: str) -> list[Airport]:
    print(f"Cercant informació per a: {name}")
    resultats = fr_api.search(name)
    aeroports = await _parse_results(resultats)
    if not aeroports:
        raise HTTPException(
            status_code=404,
            detail={"error": "airport_not_found", "message": "This airport does not exist"},
        )
    return aeroports



async def get_airport_by_iata(iata: str, pg: PostgresConnector = pg_dependency) -> Airport:
    normalized_iata = (iata or "").strip().upper()
    if not normalized_iata:
        raise HTTPException(
            status_code=400,
            detail={"error": "iata_required", "message": "iata is required"},
        )

    saved = pg.execute(
        "SELECT name, iata, icao, lat, lon FROM airports WHERE UPPER(iata) = %s LIMIT 1",
        (normalized_iata,),
        fetch="one",
    )
    if saved:
        return Airport.model_validate(saved)

    resultats = fr_api.search(normalized_iata)
    airports = await _parse_results(resultats)
    for airport in airports:
        if (airport.iata or "").upper() == normalized_iata:
            return airport

    raise HTTPException(
        status_code=404,
        detail={"error": "airport_not_found", "message": "This airport does not exist"},
    )

async def airport_exists(iata, pg: PostgresConnector) -> bool:
    result = pg.execute(
        "SELECT 1 FROM airports WHERE iata = %s LIMIT 1",
        (iata,),
        fetch="one",
    )
    return result is not None
    
async def _parse_results(resultats: Any) -> List[Airport]:
    if not isinstance(resultats, dict):
        return []
    aeroports_raw = resultats.get("airport", []) or []
    return [_from_api(item) for item in aeroports_raw]

async def _from_api(data: dict) -> Airport:
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