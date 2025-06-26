from fastapi import APIRouter, Body
from operation.booking import process_booking

booking_router = APIRouter()

@booking_router.post("/booking/", tags=["Booking"], summary="Book an interview")
async def book_interview(request: str):
    result = process_booking(request)
    return result