from fastapi import APIRouter


router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check():
    return {
        "status": "ok",
        "message": "Document Reader AI backend is running"
    }