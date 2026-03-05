from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

app = FastAPI(title="FlightsASL API", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
WELCOME_TEMPLATE = BASE_DIR / "templates" / "welcome.html"


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