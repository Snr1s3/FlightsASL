from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from Routes import flights

try:
	from Routes import airports, web
except ModuleNotFoundError:
	from src.Routes import airports, web

#app = FastAPI(title="FlightsASL API", version="0.1.0", docs_url=None, redoc_url=None)
app = FastAPI(title="FlightsASL API", version="0.1.0")
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")



app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(airports.router)
app.include_router(flights.router)
app.include_router(web.router)
@app.get("/", tags=["Pages"])
async def welcome_page(request: Request):
	return templates.TemplateResponse("index.html", {"request": request})


@app.get("/airports", tags=["Pages"])
async def airports_page(request: Request):
	return templates.TemplateResponse("airports.html", {"request": request})


@app.get("/airport", tags=["Pages"])
async def airport_page(request: Request):
	return templates.TemplateResponse("airport.html", {"request": request})


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
	return {"status": "ok"}
