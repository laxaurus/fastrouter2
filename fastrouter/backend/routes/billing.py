from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.middleware.auth import get_current_user
from backend.models.user import User
from backend.services.stripe_service import StripeService

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    success_url: str
    cancel_url: str


@router.get("/status", response_model=None)
async def billing_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return {
        "subscription_status": user.subscription_status,
        "free_requests_used": user.free_requests_used,
        "free_requests_limit": user.free_requests_limit,
        "free_requests_remaining": max(0, user.free_requests_limit - user.free_requests_used),
    }


@router.post("/checkout", response_model=None)
async def create_checkout(
    req: CheckoutRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.email:
        raise HTTPException(status_code=400, detail="User has no email")

    stripe_service = StripeService()
    checkout_url = await stripe_service.create_checkout_session(
        user,
        success_url=req.success_url,
        cancel_url=req.cancel_url,
    )
    await db.commit()

    return {"checkout_url": checkout_url}


@router.post("/portal", response_model=None)
async def create_portal(
    return_url: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing history")

    stripe_service = StripeService()
    portal_url = await stripe_service.create_portal_session(user, return_url)
    return {"portal_url": portal_url}
