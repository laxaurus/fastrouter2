import stripe
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.user import User

settings = get_settings()
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Handles Stripe subscription checkout, portal, and webhooks."""

    async def create_checkout_session(self, user: User, success_url: str, cancel_url: str) -> str:
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={"user_id": str(user.id)},
            )
            user.stripe_customer_id = customer.id

        checkout = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": settings.stripe_price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": str(user.id)},
        )
        return checkout.url

    async def create_portal_session(self, user: User, return_url: str) -> str:
        if not user.stripe_customer_id:
            raise ValueError("No Stripe customer found")

        portal = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=return_url,
        )
        return portal.url

    async def handle_webhook(self, payload: bytes, signature: str, db: AsyncSession) -> dict:
        try:
            event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            return {"error": str(e)}

        handlers = {
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "customer.subscription.updated": self._handle_subscription_updated,
            "invoice.payment_failed": self._handle_invoice_failed,
        }

        handler = handlers.get(event["type"])
        if handler:
            await handler(event["data"]["object"], db)

        return {"status": "ok", "type": event["type"]}

    async def _handle_checkout_completed(self, session: dict, db: AsyncSession):
        user_id = session["metadata"].get("user_id")
        if not user_id:
            return

        subscription_id = session.get("subscription")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.subscription_status = "active"
            user.stripe_subscription_id = subscription_id
            await db.commit()

    async def _handle_subscription_deleted(self, subscription: dict, db: AsyncSession):
        customer_id = subscription["customer"]
        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.subscription_status = "inactive"
            user.stripe_subscription_id = None
            await db.commit()

    async def _handle_subscription_updated(self, subscription: dict, db: AsyncSession):
        customer_id = subscription["customer"]
        status = subscription.get("status", "inactive")
        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()
        if user:
            if status == "active":
                user.subscription_status = "active"
            elif status == "past_due":
                user.subscription_status = "past_due"
            await db.commit()

    async def _handle_invoice_failed(self, invoice: dict, db: AsyncSession):
        customer_id = invoice.get("customer")
        if customer_id:
            result = await db.execute(
                select(User).where(User.stripe_customer_id == customer_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.subscription_status = "past_due"
                await db.commit()
