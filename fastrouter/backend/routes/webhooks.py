from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.services.stripe_service import StripeService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe", response_model=None)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    stripe_service = StripeService()
    result = await stripe_service.handle_webhook(payload, signature, db)

    if "error" in result:
        return JSONResponse(status_code=400, content=result)

    return result
