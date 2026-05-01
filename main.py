from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, trips

# Create tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TravelApp API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://192.168.0.159:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(trips.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "TravelApp API 運行中"}
