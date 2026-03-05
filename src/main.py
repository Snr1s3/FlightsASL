from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from .Models import Airport, Flight

app = FastAPI(title="FlightsASL API", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
WELCOME_TEMPLATE = BASE_DIR / "templates" / "welcome.html"

AIRPORTS: list[Airport] = [
	Airport(
		name="Seattle-Tacoma International Airport",
		iata="SEA",
		icao="KSEA",
		lat=47.4502,
		lon=-122.3088,
		arrivals_list=[
			Flight(
				number="AS123",
				origin="LAX",
				eta="2026-03-05T12:30:00Z",
				arrival_info="On time · Gate D4",
			)
		],
		departures_list=[
			Flight(
				number="DL456",
				origin="SEA",
				eta="2026-03-05T15:00:00Z",
				arrival_info="Departs to JFK · Gate B2",
			)
		],
	),
	Airport(
		name="San Francisco International Airport",
		iata="SFO",
		icao="KSFO",
		lat=37.6213,
		lon=-122.3790,
		arrivals_list=[
			Flight(
				number="UA789",
				origin="SEA",
				eta="2026-03-05T17:45:00Z",
				arrival_info="Delayed 10m · Gate F12",
			)
		],
		departures_list=[
			Flight(
				number="BA286",
				origin="SFO",
				eta="2026-03-06T00:15:00Z",
				arrival_info="Departs to LHR · Gate A5",
			)
		],
	),
	Airport(
		name="John F. Kennedy International Airport",
		iata="JFK",
		icao="KJFK",
		lat=40.6413,
		lon=-73.7781,
		arrivals_list=[
			Flight(
				number="DL456",
				origin="SEA",
				eta="2026-03-05T23:40:00Z",
				arrival_info="Taxiing · Gate 7",
			)
		],
		departures_list=[
			Flight(
				number="AF007",
				origin="JFK",
				eta="2026-03-06T02:10:00Z",
				arrival_info="Departs to CDG · Gate 4",
			)
		],
	),
]


app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/", tags=["System"])
async def read_root() -> dict[str, str]:
	return {"message": "FlightsASL API is up"}


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
	return {"status": "ok"}


@app.get("/welcome", tags=["Pages"])
async def welcome_page() -> FileResponse:
	return FileResponse(WELCOME_TEMPLATE, media_type="text/html")


@app.get("/api/welcome", tags=["System"])
async def welcome_api() -> JSONResponse:
	return JSONResponse({"message": "Welcome to FlightsASL!"})


@app.get("/api/airports", response_model=list[Airport], tags=["Airports"])
async def list_airports() -> list[Airport]:
	return AIRPORTS