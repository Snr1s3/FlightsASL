import datetime
from pathlib import Path
from typing import Sequence
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from FlightRadar24 import FlightRadar24API
from FlightRadar24.errors import AirportNotFoundError
from pymongo import ASCENDING

from db.db_connection import MongoConnector
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

mongo_dependency = Depends(get_mongo)
fr_api = FlightRadar24API()
_DEFAULT_LIMIT = 100

@router.get("/getFlights")
async def get_flights(request: Request, iata: str = None, type: int = 1,
                        limit: int = _DEFAULT_LIMIT, page: int = 1,
                        mongo: MongoConnector = mongo_dependency):
    schedule_type = "arrivals" if type == 1 else "departures"
    if type == 1:
        flights = list(
            mongo.collection("flights").find(
                {
                    "t_flight": schedule_type,
                    "destination_iata": iata,
                },
                {
                    "_id": 0,
                },
            ).sort("scheduled_arrival", ASCENDING).limit(limit)
        )
        print(len(flights))
        return flights
    else:
        flights = list(
            mongo.collection("flights").find(
                {
                    "t_flight": schedule_type,
                    "origin_iata": iata,
                },
                {
                    "_id": 0,
                },
            ).sort("scheduled_departure", ASCENDING).limit(limit)
        )
        print(len(flights))
        return flights

@router.get("/storeFlights")
async def store_flights(request: Request, iata: str = None, type: int = 1,
                        limit: int = _DEFAULT_LIMIT, page: int = 1,
                        mongo: MongoConnector = mongo_dependency):
    if iata is None:
        return templates.TemplateResponse("airports.html", {"request": request})
    normalized_iata = (iata or "").strip()
    if normalized_iata.lower() in {"", "null", "none", "undefined"}:
        return []
    print(type)
    print(f"Cercant informació per a: {iata}")
    schedule_type = "arrivals" if type == 1 else "departures"
    items = fetch(fr_api, schedule_type, normalized_iata, limit=limit, page=page)
    
    print(f"total items from API: {len(items)}")

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    window_start = now_utc - datetime.timedelta(hours=1)
    window_end = now_utc + datetime.timedelta(hours=2)

    delete_query = {
        "$or": [
            {
                "t_flight": "arrivals",
                "$or": [
                    {"scheduled_arrival": {"$lt": window_start}},
                    {"scheduled_arrival": {"$gt": window_end}},
                ],
            },
            {
                "t_flight": "departures",
                "$or": [
                    {"scheduled_departure": {"$lt": window_start}},
                    {"scheduled_departure": {"$gt": window_end}},
                ],
            },
        ]
    }

    result = mongo.delete_many("flights", delete_query)
    print(f"removed stale flights: {result.deleted_count}")

    for item in items:
        ts = _extract_event_timestamp(item, schedule_type)
        if ts is None:
            print("excluded: no timestamp")
            continue

        event_dt_utc = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
        print(
            f"schedule_type={schedule_type} "
            f"event_dt_utc={event_dt_utc} "
            f"window_start={window_start} "
            f"window_end={window_end} "
            f"keep={window_start <= event_dt_utc <= window_end}"
        )
    filtered_items = [
        item for item in items
        if _in_time_window(item, schedule_type, window_start, window_end)
    ]
    print(f"items after time filter: {len(filtered_items)}")
    
    flights = [await _build_flight(item, schedule_type, iata) for item in items]
    

    if not flights:
        print("No flight data available.")
        return []
    for flight in flights:
        exists = await flight_exists(flight, mongo)
        if not exists:
            mongo.insert_one("flights", flight.model_dump())

    return []

async def flight_exists(flight: Flight, mongo: MongoConnector) -> bool:
    if not flight.id_flight:
        return False
    result = mongo.find_one("flights", {"id_flight": flight.id_flight})
    return result is not None

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
    flight_id=flight.get("identification", {}).get("id",{})
    num = (
        identification.get("number", {}).get("default")
        or identification.get("id")
        or "-"
    )
    origin_key = "origin"
    dest_key = "destination"
    airport_section = flight.get("airport", {}) or {}
    if schedule_type == "departures":
        origin_name = (await get_airport_by_iata(iata_airport_search, mongo=get_mongo())).name
        origin_iata = iata_airport_search
        dest_info = airport_section.get(dest_key, {}) or {}
        dest_name = dest_info.get("name") or "-"
        destination_iata= dest_info.get("code").get("iata") or "-"
        origin_info = airport_section.get(origin_key, {}) or {}
        dest_info = airport_section.get(dest_key, {}) or {}

        origin_timezone_name = (origin_info.get("timezone") or {}).get("name")
        dest_timezone_name = (dest_info.get("timezone") or {}).get("name")

        time_info = flight.get("time", {}) or {}
        departure = describe(time_info.get("scheduled", {}).get("departure"), origin_timezone_name)
        arrival = describe(time_info.get("scheduled", {}).get("arrival"), dest_timezone_name)

    if schedule_type == "arrivals":
        dest_name = (await get_airport_by_iata(iata_airport_search, mongo=get_mongo())).name
        destination_iata = iata_airport_search
        origin_info = airport_section.get(origin_key, {}) or {}
        origin_name = origin_info.get("name") or "-"
        origin_iata= origin_info.get("code").get("iata") or "-"
        origin_info = airport_section.get(origin_key, {}) or {}
        dest_info = airport_section.get(dest_key, {}) or {}

        origin_timezone_name = (origin_info.get("timezone") or {}).get("name")
        dest_timezone_name = (dest_info.get("timezone") or {}).get("name")

        time_info = flight.get("time", {}) or {}
        departure = describe(time_info.get("scheduled", {}).get("departure"), origin_timezone_name)
        arrival = describe(time_info.get("scheduled", {}).get("arrival"), dest_timezone_name)

    return Flight(
        id_flight=flight_id,
        t_flight=schedule_type,
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