from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse



router = APIRouter(
    prefix="/web",
    tags=["web"],
    responses={404: {"description": "Not found"}}
)

@router.get("/welcome", tags=["System"])
async def welcome_api() -> JSONResponse:
	return JSONResponse({"message": "Welcome to FlightsASL!"})