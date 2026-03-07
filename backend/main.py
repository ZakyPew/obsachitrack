from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from auth.steam import steam_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="StreamTracker Web", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(steam_router, prefix="/auth", tags=["auth"])

@app.get("/")
def root():
    return {"message": "StreamTracker Web API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
