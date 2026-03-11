import datetime
import re
from pathlib import Path
from typing import Any, List, Sequence
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from FlightRadar24 import FlightRadar24API
from FlightRadar24.errors import AirportNotFoundError

try:
    from db.db_connection import MongoConnector
    from Models.airport import Airport
    from Models.flight import Flight
except ModuleNotFoundError:
    from src.db.db_connection import MongoConnector
    from src.Models.airport import Airport
    from src.Models.flight import Flight

router = APIRouter(
    prefix="/api/airport",
    tags=["airport"],
    responses={404: {"description": "Not found"}}
)
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

fr_api = FlightRadar24API()
_DEFAULT_LIMIT = 100
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
    if aeroports:
        return aeroports
    return []


@router.get("/getFlights")
async def flights_airport(request: Request, iata: str = None, type: int = 1,
                        limit: int = _DEFAULT_LIMIT, page: int = 1) -> List[Flight] | Any:
    if iata is None:
        return templates.TemplateResponse("airports.html", {"request": request})
    normalized_iata = (iata or "").strip()
    if normalized_iata.lower() in {"", "null", "none", "undefined"}:
        return []
    print(f"Cercant informació per a: {iata}")
    schedule_type = "arrivals" if type == 1 else "departures"
    items = fetch(fr_api, schedule_type, normalized_iata, limit=limit, page=page)
    print(schedule_type)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    window_start = now_utc - datetime.timedelta(hours=1)
    window_end = now_utc + datetime.timedelta(hours=4)

    filtered_items = [
        item for item in items
        if _in_time_window(item, schedule_type, window_start, window_end)
    ]

    sorted_items = sorted(
        filtered_items,
        key=lambda item: _extract_event_timestamp(item, schedule_type) or float("inf")
    )

    flights = [_build_flight(item, schedule_type) for item in sorted_items]
    if not flights:
        print("No flight data available.")
        return []
    return flights
def fetch(fr_api,schedule_type:str,
        iata:str, limit: int = _DEFAULT_LIMIT, page: int = 1) -> Sequence[dict]:
    try:
        details = fr_api.get_airport_details(iata, flight_limit=limit, page=page)
    except AirportNotFoundError:
        return []
    schedule = (
        details
        .get("airport", {})
        .get("pluginData", {})
        .get("schedule", {})
        .get(schedule_type, {})
    )
    return schedule.get("data", []) or []

def _build_flight(item: dict, schedule_type: str) -> Flight:
    flight = item.get("flight", {}) or {}
    identification = flight.get("identification", {}) or {}
    number = (
        identification.get("number", {}).get("default")
        or identification.get("id")
        or "-"
    )
    airport_section = flight.get("airport", {}) or {}
    location_key = "origin" if schedule_type == "arrivals" else "destination"
    location_info = airport_section.get(location_key, {}) or {}
    location_name = location_info.get("name") or "-"

    # Use destination timezone for the event time (arrival/departure at this airport)
    dest_key = "destination" if schedule_type == "arrivals" else "origin"
    dest_info = airport_section.get(dest_key, {}) or {}
    dest_timezone_name = dest_info.get("timezone", {}).get("name")

    time_info = flight.get("time", {}) or {}
    eta = describe(time_info.get("other", {}).get("eta"), dest_timezone_name)
    event_key = "arrival" if schedule_type == "arrivals" else "departure"
    event_time = describe(
        time_info.get("scheduled", {}).get(event_key),
        dest_timezone_name,
    )
    return Flight(
        number=number,
        origin=location_name,
        eta=eta,
        arrival_info=event_time,
    )
async def airport_exists(airport: Airport, mongo: MongoConnector) -> bool:
    result = mongo.find_one("FLIGHTSASL", {"name": airport.name})
    return result is not None

def describe(timestamp: int | float | None, tz_name: str | None = None) -> str:
        if timestamp is None:
            return "-"
        try:
            ts = float(timestamp)
        except (TypeError, ValueError):
            return "-"
        tzinfo = _resolve_timezone(tz_name)
        return datetime.datetime.fromtimestamp(ts, tzinfo).strftime("%Y-%m-%d %H:%M")

def _resolve_timezone(name: str | None):
    try:
        return ZoneInfo(name) if name else datetime.timezone.utc
    except Exception:
        return datetime.timezone.utc
    
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

def _in_time_window(
    item: dict,
    schedule_type: str,
    start_dt: datetime.datetime,
    end_dt: datetime.datetime,
) -> bool:
    ts = _extract_event_timestamp(item, schedule_type)
    if ts is None:
        return False
    event_dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
    return start_dt <= event_dt <= end_dt


def _extract_event_timestamp(item: dict, schedule_type: str) -> float | None:
    flight = item.get("flight", {}) or {}
    time_info = flight.get("time", {}) or {}
    event_key = "arrival" if schedule_type == "arrivals" else "departure"
    
    ts = (time_info.get("scheduled", {}) or {}).get(event_key)
    if ts is not None:
        try:
            return float(ts)
        except (TypeError, ValueError):
            return None
    return None