from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from operation.load import process_uploaded_file

upload_router = APIRouter()

@upload_router.post("/upload/", tags=["Upload"], summary="Upload PDF or TXT file")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ["application/pdf", "text/plain"]:
        raise HTTPException(status_code=400, detail="Only PDF or TXT files are allowed.")

    file_bytes = await file.read()

    try:
        result = process_uploaded_file(file_bytes, file.filename, file.content_type)
        return JSONResponse(content={"detail": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
