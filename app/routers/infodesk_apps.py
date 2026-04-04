"""Infodesk apps routes (STEP 1 scaffold)."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_placeholder():
    return {"items": []}
