from fastapi import APIRouter, Body
from operation.app import process_query

query_router = APIRouter()

@query_router.post("/query/", tags=["Query"], summary="Query documents with RAG")
async def query_documents(request: str):
    result = process_query(request)
    return result
