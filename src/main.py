from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from src.Routes import airports, web

from .Models import Airport, Flight

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
()

app.include_router(airports.router)
app.include_router(web.router)
@app.get("/", tags=["Pages"])
async def welcome_page() -> FileResponse:
	return FileResponse(WELCOME_TEMPLATE, media_type="text/html")


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
	return {"status": "ok"}
