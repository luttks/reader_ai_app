from fastapi import APIRouter

from app.routes.health import router as health_router
from app.routes.documents import router as documents_router
from app.routes.upload import router as upload_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(documents_router)
api_router.include_router(upload_router)