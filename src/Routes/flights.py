import datetime
from pathlib import Path
from typing import Any, List, Sequence
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from FlightRadar24 import FlightRadar24API
from FlightRadar24.errors import AirportNotFoundError

from Routes.airports import get_airport_by_iata, get_mongo

try:
    from Models.flight import Flight
except ModuleNotFoundError:
    from src.Models.flight import Flight

router = APIRouter(
    prefix="/api/flights",
    tags=["flights"],
    responses={404: {"description": "Not found"}}
)
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

fr_api = FlightRadar24API()
_DEFAULT_LIMIT = 100

@router.get("/getFlights")
async def flights_airport(request: Request, iata: str = None, type: int = 1,
                        limit: int = _DEFAULT_LIMIT, page: int = 1) -> List[Flight] | Any:
    if iata is None:
        return templates.TemplateResponse("airports.html", {"request": request})
    normalized_iata = (iata or "").strip()
    if normalized_iata.lower() in {"", "null", "none", "undefined"}:
        return []
    print(type)
    print(f"Cercant informació per a: {iata}")
    schedule_type = "arrivals" if type == 1 else "departures"
    items = fetch(fr_api, schedule_type, normalized_iata, limit=limit, page=page)
    #print(schedule_type)
    #print(items)
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    window_start = now_utc - datetime.timedelta(hours=1)
    window_end = now_utc + datetime.timedelta(hours=4)

    filtered_items = [
        item for item in items
        if _in_time_window(item, schedule_type, window_start, window_end)
    ]
    flights = [await _build_flight(item, schedule_type, iata) for item in filtered_items]
    for flight in flights:
        print(flight)

    if not flights:
        print("No flight data available.")
        return []
    return flights

def fetch(fr_api, schedule_type: str,
        iata: str, limit: int = _DEFAULT_LIMIT, page: int = 1) -> Sequence[dict]:
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

async def _build_flight(item: dict, schedule_type: str, iata_airport_search : str) -> Flight:
    flight = item.get("flight", {}) or {}
    identification = flight.get("identification", {}) or {}
    num = (
        identification.get("number", {}).get("default")
        or identification.get("id")
        or "-"
    )
    
    
    location_name  = None
    origin_key = "origin"
    dest_key = "destination"
    airport_section = flight.get("airport", {}) or {}
    if schedule_type == 2:
        
        location_info = airport_section.get(dest_key, {}) or {}
        location_name = location_info.get("name") or "-"
        dest_info = airport_section.get(origin_key, {}) or {}
        dest_timezone_name = dest_info.get("timezone", {}).get("name")

        time_info = flight.get("time", {}) or {}
        eta = describe(time_info.get("other", {}).get("eta"), dest_timezone_name)
        event_key = "arrival" if schedule_type == "arrivals" else "departure"
        event_time = describe(
            time_info.get("scheduled", {}).get(event_key),
            dest_timezone_name,
        )
    if schedule_type == "arrivals":
        dest_name = (await get_airport_by_iata(iata_airport_search, mongo=get_mongo())).name
        destination_iata = iata_airport_search
        origin_info = airport_section.get(origin_key, {}) or {}
        origin_name = origin_info.get("name") or "-"
        origin_iata= origin_info.get("code").get("iata") or "-"
        origin_timezone_name = origin_info.get("timezone", {}).get("name")
        time_info = flight.get("time", {}) or {}
        departure = describe(time_info.get("scheduled", {}).get("departure"), origin_timezone_name)
        arrival  = describe(time_info.get("scheduled", {}).get("arrival"), origin_timezone_name)

    return Flight(
        number=num,
        origin=origin_name,
        origin_iata=origin_iata,
        destination=dest_name,
        destination_iata=destination_iata,
        scheduled_departure = departure,
        scheduled_arrival = arrival
    )

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