from fastapi import FastAPI
from database.db import init_db
from routers.upload_router import upload_router
from routers.query_router import query_router
from routers.booking_router import booking_router

app = FastAPI(title="Document Upload API")

# Initialize the DB on app startup
init_db()

# Include routers
app.include_router(upload_router)
app.include_router(query_router)
app.include_router(booking_router)
