from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
import stripe

import sys
sys.path.append('/opt/streamtracker/backend')

from database import SessionLocal, User, Subscription
from auth.steam import get_current_user

stripe_router = APIRouter()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
PREMIUM_PRICE_ID = os.getenv("STRIPE_PREMIUM_PRICE_ID", "")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@stripe_router.post("/create-checkout-session")
def create_checkout_session(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not stripe.api_key or not PREMIUM_PRICE_ID:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    try:
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email or f"{user.username}@streamtracker.local",
                name=user.username,
                metadata={"user_id": str(user.id), "steam_id": user.steam_id}
            )
            user.stripe_customer_id = customer.id
            db.commit()
        
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": PREMIUM_PRICE_ID, "quantity": 1}],
            mode="subscription",
            success_url=f"{os.getenv('BASE_URL', 'http://74.208.147.236')}/dashboard?checkout=success",
            cancel_url=f"{os.getenv('BASE_URL', 'http://74.208.147.236')}/dashboard?checkout=cancel",
            metadata={"user_id": str(user.id), "steam_id": user.steam_id}
        )
        
        return {"checkout_url": checkout_session.url}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@stripe_router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")
    
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    if event["type"] == "checkout.session.completed":
        await handle_checkout_completed(event["data"]["object"], db)
    elif event["type"] == "invoice.payment_succeeded":
        await handle_payment_succeeded(event["data"]["object"], db)
    elif event["type"] == "customer.subscription.deleted":
        await handle_subscription_cancelled(event["data"]["object"], db)
    
    return {"status": "success"}

async def handle_checkout_completed(session, db):
    user_id = session.get("metadata", {}).get("user_id")
    if not user_id:
        return
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        return
    
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not subscription:
        subscription = Subscription(user_id=user.id)
        db.add(subscription)
    
    subscription.stripe_customer_id = session.get("customer")
    subscription.stripe_subscription_id = session.get("subscription")
    subscription.status = "active"
    subscription.tier = "premium"
    subscription.current_period_start = datetime.utcnow()
    user.is_premium = True
    db.commit()

async def handle_payment_succeeded(invoice, db):
    customer_id = invoice.get("customer")
    subscription = db.query(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
    
    if subscription:
        subscription.status = "active"
        subscription.current_period_start = datetime.utcnow()
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            user.is_premium = True
        db.commit()

async def handle_subscription_cancelled(stripe_subscription, db):
    subscription = db.query(Subscription).filter(
        Subscription.stripe_subscription_id == stripe_subscription.get("id")
    ).first()
    
    if subscription:
        subscription.status = "cancelled"
        subscription.cancelled_at = datetime.utcnow()
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            user.is_premium = False
        db.commit()

@stripe_router.get("/subscription-status")
def get_subscription_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    return {
        "is_premium": user.is_premium,
        "status": subscription.status if subscription else "inactive",
        "tier": subscription.tier if subscription else "free",
        "current_period_end": subscription.current_period_end.isoformat() if subscription and subscription.current_period_end else None
    }

@stripe_router.post("/cancel-subscription")
def cancel_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subscription = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    
    if not subscription or not subscription.stripe_subscription_id:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    try:
        stripe.Subscription.modify(subscription.stripe_subscription_id, cancel_at_period_end=True)
        subscription.status = "pending_cancellation"
        db.commit()
        return {"status": "success", "message": "Subscription will cancel at period end"}
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
