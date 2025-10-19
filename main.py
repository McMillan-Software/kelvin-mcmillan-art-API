from fastapi import FastAPI
from database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from routers import web, admin, login
import logging


# Create the database
Base.metadata.create_all(engine)

# Initialize app
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:4173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add /api prefix to all routes
app.include_router(web.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(login.router, prefix="/api")
