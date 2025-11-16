"""
Payment Service for Interior AI

Integrates with Stripe for:
- Subscription management
- Credit purchases
- Payment processing
- Webhook handling
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PaymentService:
    """Stripe payment integration"""

    def __init__(self):
        self.stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "")
        self.stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

        # Pricing (in cents)
        self.credit_prices = {
            "pack_10": 990,    # $9.90 for 10 credits
            "pack_50": 3990,   # $39.90 for 50 credits
            "pack_100": 6990,  # $69.90 for 100 credits
        }

        self.subscription_prices = {
            "pro_monthly": 2999,      # $29.99/month
            "pro_yearly": 29999,      # $299.99/year (save 17%)
            "enterprise_monthly": 9999,  # $99.99/month
            "enterprise_yearly": 99999,  # $999.99/year (save 17%)
        }

    def initialize_stripe(self):
        """Initialize Stripe with API key"""
        try:
            import stripe
            stripe.api_key = self.stripe_secret_key
            return stripe
        except ImportError:
            logger.error("Stripe library not installed. Run: pip install stripe")
            return None

    def create_customer(self, email: str, name: str, metadata: Optional[Dict] = None) -> Optional[str]:
        """Create a Stripe customer"""
        stripe = self.initialize_stripe()
        if not stripe:
            return None

        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
            logger.info(f"Created Stripe customer: {customer.id} for {email}")
            return customer.id
        except Exception as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            return None

    def create_payment_intent(
        self,
        amount: int,
        currency: str = "usd",
        customer_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Create a payment intent for one-time payment"""
        stripe = self.initialize_stripe()
        if not stripe:
            return None

        try:
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                customer=customer_id,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True}
            )

            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": intent.amount,
                "status": intent.status
            }
        except Exception as e:
            logger.error(f"Failed to create payment intent: {e}")
            return None

    def create_credit_purchase_intent(
        self,
        pack_size: str,
        customer_id: str,
        user_id: str
    ) -> Optional[Dict]:
        """Create payment intent for credit purchase"""

        if pack_size not in self.credit_prices:
            logger.error(f"Invalid credit pack: {pack_size}")
            return None

        amount = self.credit_prices[pack_size]
        credits = int(pack_size.split('_')[1])

        return self.create_payment_intent(
            amount=amount,
            customer_id=customer_id,
            metadata={
                "type": "credit_purchase",
                "user_id": user_id,
                "pack_size": pack_size,
                "credits": credits
            }
        )

    def create_subscription(
        self,
        customer_id: str,
        plan: str,
        trial_days: int = 0
    ) -> Optional[Dict]:
        """Create a subscription"""
        stripe = self.initialize_stripe()
        if not stripe:
            return None

        if plan not in self.subscription_prices:
            logger.error(f"Invalid subscription plan: {plan}")
            return None

        try:
            # Get or create price
            price_id = self._get_or_create_price(plan)
            if not price_id:
                return None

            subscription_params = {
                "customer": customer_id,
                "items": [{"price": price_id}],
                "expand": ["latest_invoice.payment_intent"]
            }

            if trial_days > 0:
                subscription_params["trial_period_days"] = trial_days

            subscription = stripe.Subscription.create(**subscription_params)

            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice else None
            }
        except Exception as e:
            logger.error(f"Failed to create subscription: {e}")
            return None

    def cancel_subscription(self, subscription_id: str, immediately: bool = False) -> bool:
        """Cancel a subscription"""
        stripe = self.initialize_stripe()
        if not stripe:
            return False

        try:
            if immediately:
                stripe.Subscription.delete(subscription_id)
            else:
                stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )

            logger.info(f"Cancelled subscription: {subscription_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False

    def update_subscription(self, subscription_id: str, new_plan: str) -> Optional[Dict]:
        """Update subscription plan"""
        stripe = self.initialize_stripe()
        if not stripe:
            return None

        if new_plan not in self.subscription_prices:
            logger.error(f"Invalid subscription plan: {new_plan}")
            return None

        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            price_id = self._get_or_create_price(new_plan)

            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    "id": subscription["items"]["data"][0].id,
                    "price": price_id
                }]
            )

            return {
                "subscription_id": updated_subscription.id,
                "status": updated_subscription.status,
                "current_period_end": updated_subscription.current_period_end
            }
        except Exception as e:
            logger.error(f"Failed to update subscription: {e}")
            return None

    def _get_or_create_price(self, plan: str) -> Optional[str]:
        """Get or create Stripe price for plan"""
        stripe = self.initialize_stripe()
        if not stripe:
            return None

        # In production, store these price IDs in database or environment variables
        # For now, we'll create them dynamically (not recommended for production)

        price_mapping = {
            "pro_monthly": os.getenv("STRIPE_PRICE_PRO_MONTHLY"),
            "pro_yearly": os.getenv("STRIPE_PRICE_PRO_YEARLY"),
            "enterprise_monthly": os.getenv("STRIPE_PRICE_ENTERPRISE_MONTHLY"),
            "enterprise_yearly": os.getenv("STRIPE_PRICE_ENTERPRISE_YEARLY"),
        }

        # Return existing price ID if configured
        if plan in price_mapping and price_mapping[plan]:
            return price_mapping[plan]

        # Create price if not configured (development only)
        try:
            interval = "year" if "yearly" in plan else "month"
            amount = self.subscription_prices[plan]

            product_name = "Interior AI Pro" if "pro" in plan else "Interior AI Enterprise"

            # Create product if needed
            products = stripe.Product.list(limit=100)
            product = next((p for p in products.data if p.name == product_name), None)

            if not product:
                product = stripe.Product.create(name=product_name)

            # Create price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=amount,
                currency="usd",
                recurring={"interval": interval}
            )

            logger.info(f"Created Stripe price: {price.id} for {plan}")
            return price.id
        except Exception as e:
            logger.error(f"Failed to create price: {e}")
            return None

    def construct_webhook_event(self, payload: bytes, signature: str) -> Optional[Any]:
        """Construct and verify webhook event"""
        stripe = self.initialize_stripe()
        if not stripe:
            return None

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return event
        except ValueError:
            logger.error("Invalid webhook payload")
            return None
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return None

    def handle_webhook_event(self, event: Any) -> Dict[str, Any]:
        """Handle Stripe webhook events"""

        event_type = event["type"]
        data = event["data"]["object"]

        logger.info(f"Processing webhook event: {event_type}")

        handlers = {
            "payment_intent.succeeded": self._handle_payment_success,
            "payment_intent.payment_failed": self._handle_payment_failed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "invoice.paid": self._handle_invoice_paid,
            "invoice.payment_failed": self._handle_invoice_failed,
        }

        handler = handlers.get(event_type)
        if handler:
            return handler(data)

        logger.info(f"Unhandled webhook event type: {event_type}")
        return {"status": "ignored"}

    def _handle_payment_success(self, payment_intent: Dict) -> Dict:
        """Handle successful payment"""
        metadata = payment_intent.get("metadata", {})

        return {
            "status": "success",
            "action": "credit_purchase" if metadata.get("type") == "credit_purchase" else "payment",
            "data": {
                "payment_intent_id": payment_intent["id"],
                "amount": payment_intent["amount"],
                "user_id": metadata.get("user_id"),
                "credits": metadata.get("credits")
            }
        }

    def _handle_payment_failed(self, payment_intent: Dict) -> Dict:
        """Handle failed payment"""
        return {
            "status": "failed",
            "action": "payment_failed",
            "data": {
                "payment_intent_id": payment_intent["id"],
                "error": payment_intent.get("last_payment_error")
            }
        }

    def _handle_subscription_created(self, subscription: Dict) -> Dict:
        """Handle subscription creation"""
        return {
            "status": "success",
            "action": "subscription_created",
            "data": {
                "subscription_id": subscription["id"],
                "customer_id": subscription["customer"],
                "status": subscription["status"],
                "current_period_end": subscription["current_period_end"]
            }
        }

    def _handle_subscription_updated(self, subscription: Dict) -> Dict:
        """Handle subscription update"""
        return {
            "status": "success",
            "action": "subscription_updated",
            "data": {
                "subscription_id": subscription["id"],
                "status": subscription["status"],
                "cancel_at_period_end": subscription.get("cancel_at_period_end", False)
            }
        }

    def _handle_subscription_deleted(self, subscription: Dict) -> Dict:
        """Handle subscription deletion"""
        return {
            "status": "success",
            "action": "subscription_deleted",
            "data": {
                "subscription_id": subscription["id"],
                "customer_id": subscription["customer"]
            }
        }

    def _handle_invoice_paid(self, invoice: Dict) -> Dict:
        """Handle paid invoice"""
        return {
            "status": "success",
            "action": "invoice_paid",
            "data": {
                "invoice_id": invoice["id"],
                "subscription_id": invoice.get("subscription"),
                "amount_paid": invoice["amount_paid"]
            }
        }

    def _handle_invoice_failed(self, invoice: Dict) -> Dict:
        """Handle failed invoice"""
        return {
            "status": "failed",
            "action": "invoice_failed",
            "data": {
                "invoice_id": invoice["id"],
                "subscription_id": invoice.get("subscription"),
                "attempt_count": invoice.get("attempt_count", 0)
            }
        }


# Global instance
payment_service = PaymentService()
