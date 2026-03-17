import datetime
from pathlib import Path
from typing import Sequence
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from FlightRadar24 import FlightRadar24API
from FlightRadar24.errors import AirportNotFoundError

from Models.airport import Airport
from db.db_connection import PostgresConnector
from Routes.airports import _save_airport, _search_airport, airport_exists, get_airport_by_iata, get_pg

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

pg_dependency = Depends(get_pg)
fr_api = FlightRadar24API()
_DEFAULT_LIMIT = 100

@router.get("/getFlights")
async def get_flights(request: Request, iata: str = None, type: int = 1,
                        limit: int = _DEFAULT_LIMIT, page: int = 1,
                        pg: PostgresConnector = pg_dependency, asc: int =1 ):
    normalized_iata = (iata or "").strip().upper()
    if not normalized_iata:
        return []
    airport_id = await _airport_id_from_iata(normalized_iata, pg)
    if airport_id is None:
        return []
    order_dir = "ASC" if asc == 1 else "DESC"
    print(type)
    select = """
            SELECT
                f.id_flight,
                f.number,
                ao.name AS origin,
                ao.iata AS origin_iata,
                ad.name AS destination,
                ad.iata AS destination_iata,
                f.scheduled_departure,
                f.utc_departure,
                f.scheduled_arrival,
                f.utc_arrival
            FROM flights f
            LEFT JOIN airports ao ON ao.id = f.origin_airport_id
            LEFT JOIN airports ad ON ad.id = f.destination_airport_id
            """
    if type == 1:
        select += f"""
            WHERE f.destination_airport_id = %s
            ORDER BY f.scheduled_arrival {order_dir}
            LIMIT %s
                """
    else:
        select += f"""
            WHERE f.origin_airport_id = %s
              AND f.utc_departure >= EXTRACT(EPOCH FROM (NOW() - INTERVAL '2 hours'))::bigint
            ORDER BY f.scheduled_departure {order_dir}
            LIMIT %s
            """

    flights = pg.execute(
        select,
        (airport_id, limit),
        fetch="all",
    )
    return flights

@router.post("/storeFlights")
async def store_flights(request: Request, iata: str = None, type: int = 1,
                        limit: int = _DEFAULT_LIMIT, page: int = 1,
                        pg: PostgresConnector = pg_dependency):
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
    window_start = now_utc - datetime.timedelta(hours=3)
    window_end = now_utc + datetime.timedelta(hours=2)

    filtered_items = [
        item for item in items
        if _in_time_window(item, schedule_type, window_start, window_end)
    ]
    print(f"items after time filter: {len(filtered_items)}")
    
    flights = [await _build_flight(item, schedule_type, iata) for item in filtered_items]
    

    if not flights:
        print("No flight data available.")
        return []
    for flight in flights:
        exists = await flight_exists(flight, pg)
        if not exists:
            origin_airport_id = await _ensure_airport_id(flight.origin_iata, flight.origin, pg)
            destination_airport_id = await _ensure_airport_id(flight.destination_iata, flight.destination, pg)
            pg.insert_one(
                """
                INSERT INTO flights (
                    id_flight,
                    number,
                    origin_airport_id,
                    destination_airport_id,
                    scheduled_departure,
                    utc_departure,
                    scheduled_arrival,
                    utc_arrival
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    flight.id_flight,
                    flight.number,
                    origin_airport_id,
                    destination_airport_id,
                    flight.scheduled_departure,
                    flight.utc_departure,
                    flight.scheduled_arrival,
                    flight.utc_arrival,
                ),
            )

    return []

async def flight_exists(flight: Flight, pg: PostgresConnector) -> bool:
    if not flight.id_flight:
        return False
    result = pg.execute(
        "SELECT 1 FROM flights WHERE id_flight = %s LIMIT 1",
        (flight.id_flight,),
        fetch="one",
    )
    return result is not None


async def _airport_id_from_iata(iata: str, pg: PostgresConnector) -> int | None:
    if not iata:
        return None
    row = pg.execute(
        "SELECT id FROM airports WHERE UPPER(iata) = %s LIMIT 1",
        (iata.strip().upper(),),
        fetch="one",
    )
    return row.get("id") if row else None


async def _ensure_airport_id(iata: str | None, name: str | None, pg: PostgresConnector) -> int | None:
    normalized_iata = (iata or "").strip().upper()
    if not normalized_iata or normalized_iata in {"-", "N/A", "NULL", "NONE", "UNDEFINED"}:
        return None

    existing = pg.execute(
        "SELECT id FROM airports WHERE UPPER(iata) = %s LIMIT 1",
        (normalized_iata,),
        fetch="one",
    )
    if existing:
        return existing.get("id")

    airports = await _search_airport(normalized_iata)
    if not airports:
        return None

    selected = next(
        (a for a in airports if (a.iata or "").strip().upper() == normalized_iata),
        airports[0],
    )
    await _save_airport(selected, pg, False)

    inserted = pg.execute(
        "SELECT id FROM airports WHERE UPPER(iata) = %s LIMIT 1",
        (normalized_iata,),
        fetch="one",
    )
    return inserted.get("id") if inserted else None

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
    utc_departure = None
    utc_arrival = None
    departure = "-"
    arrival = "-"

    if schedule_type == "departures":
        origin_name = (await get_airport_by_iata(iata_airport_search, pg=get_pg())).name
        origin_iata = iata_airport_search
        dest_info = airport_section.get(dest_key, {}) or {}
        dest_name = dest_info.get("name") or "-"
        destination_iata= dest_info.get("code").get("iata") or "-"
        origin_info = airport_section.get(origin_key, {}) or {}
        dest_info = airport_section.get(dest_key, {}) or {}

        origin_timezone_name = (origin_info.get("timezone") or {}).get("name")
        dest_timezone_name = (dest_info.get("timezone") or {}).get("name")

        time_info = flight.get("time", {}) or {}
        utc_departure = time_info.get("scheduled", {}).get("departure")
        utc_arrival = time_info.get("scheduled", {}).get("arrival")
        departure = describe(time_info.get("scheduled", {}).get("departure"), origin_timezone_name)
        arrival = describe(time_info.get("scheduled", {}).get("arrival"), dest_timezone_name)

    if schedule_type == "arrivals":
        dest_name = (await get_airport_by_iata(iata_airport_search, pg=get_pg())).name
        destination_iata = iata_airport_search
        origin_info = airport_section.get(origin_key, {}) or {}
        origin_name = origin_info.get("name") or "-"
        origin_iata= origin_info.get("code").get("iata") or "-"
        origin_info = airport_section.get(origin_key, {}) or {}
        dest_info = airport_section.get(dest_key, {}) or {}

        origin_timezone_name = (origin_info.get("timezone") or {}).get("name")
        dest_timezone_name = (dest_info.get("timezone") or {}).get("name")

        time_info = flight.get("time", {}) or {}
        utc_departure = time_info.get("scheduled", {}).get("departure")
        departure = describe(time_info.get("scheduled", {}).get("departure"), origin_timezone_name)
        utc_arrival = time_info.get("scheduled", {}).get("arrival")        
        arrival = describe(time_info.get("scheduled", {}).get("arrival"), dest_timezone_name)


    return Flight(
        id_flight=flight_id,
        number=num,
        origin=origin_name,
        origin_iata=origin_iata,
        destination=dest_name,
        destination_iata=destination_iata,
        scheduled_departure = departure,
        scheduled_arrival = arrival,
        utc_arrival=utc_arrival,
        utc_departure=utc_departure
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