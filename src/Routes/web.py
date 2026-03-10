from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from FlightRadar24 import FlightRadar24API

from src.db.db_connection import MongoConnector

router = APIRouter(
    prefix="/web",
    tags=["web"],
    responses={404: {"description": "Not found"}}
)

fr_api = FlightRadar24API()

def get_mongo() -> MongoConnector:
    return MongoConnector()

mongo_dependency = Depends(get_mongo)

@router.get("/welcome")
async def welcome_api() -> JSONResponse:
	return JSONResponse({"message": "Welcome to FlightsASL!"})

@router.get("/dropAll")
async def drop_all(mongo: MongoConnector = mongo_dependency) -> JSONResponse:
    mongo.collection("FLIGHTSASL").drop()
    return JSONResponse({"message": "Collection dropped successfully"})