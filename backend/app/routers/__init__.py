from fastapi import APIRouter

from . import activities, admin, auth, settlement, signups

api_router = APIRouter(prefix="/api")
api_router.include_router(activities.router)
api_router.include_router(signups.router)
api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(settlement.router)
