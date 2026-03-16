from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from FlightRadar24 import FlightRadar24API

try:
    from db.db_connection import PostgresConnector
except ModuleNotFoundError:
    from src.db.db_connection import PostgresConnector

router = APIRouter(
    prefix="/web",
    tags=["web"],
    responses={404: {"description": "Not found"}}
)

fr_api = FlightRadar24API()

def get_pg() -> PostgresConnector:
    return PostgresConnector()

pg_dependency = Depends(get_pg)

@router.get("/welcome")
async def welcome_api() -> JSONResponse:
	return JSONResponse({"message": "Welcome to FlightsASL!"})

@router.delete("/dropAll")
async def drop_all(pg: PostgresConnector = pg_dependency) -> JSONResponse:
    pg.execute("TRUNCATE TABLE flights RESTART IDENTITY CASCADE", fetch="none")
    pg.execute("TRUNCATE TABLE airports RESTART IDENTITY CASCADE", fetch="none")
    return JSONResponse({"message": "Tables truncated successfully"})


