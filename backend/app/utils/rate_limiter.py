import redis
from datetime import datetime, timedelta
from typing import Optional
from app.core.config import settings
from app.models.user import User, SubscriptionTier
from app.core.exceptions import RateLimitException


class RateLimiter:
    """Redis-based rate limiter"""

    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get_daily_limit(self, user: Optional[User]) -> int:
        """Get daily transformation limit based on subscription tier"""
        if not user:
            return 3  # Anonymous users: 3 per day

        tier_limits = {
            SubscriptionTier.FREE: settings.RATE_LIMIT_FREE_DAILY,
            SubscriptionTier.PRO: settings.RATE_LIMIT_PRO_DAILY,
            SubscriptionTier.ENTERPRISE: settings.RATE_LIMIT_ENTERPRISE_DAILY,
        }

        return tier_limits.get(user.subscription_tier, 5)

    def check_rate_limit(self, user: Optional[User], ip_address: str) -> dict:
        """
        Check if user/IP has exceeded rate limit

        Returns dict with:
        - allowed: bool
        - remaining: int
        - reset_at: datetime
        - limit: int
        """
        # Get identifier (user ID or IP)
        identifier = str(user.id) if user else f"ip:{ip_address}"

        # Get daily limit
        daily_limit = self.get_daily_limit(user)

        # Redis key for today
        today = datetime.utcnow().date()
        key = f"ratelimit:{identifier}:{today}"

        # Get current count
        current_count = self.redis_client.get(key)
        current_count = int(current_count) if current_count else 0

        # Calculate reset time (midnight UTC)
        tomorrow = today + timedelta(days=1)
        reset_at = datetime.combine(tomorrow, datetime.min.time())

        # Check limit
        remaining = max(0, daily_limit - current_count)
        allowed = current_count < daily_limit

        return {
            "allowed": allowed,
            "remaining": remaining,
            "reset_at": reset_at,
            "limit": daily_limit,
            "current": current_count
        }

    def increment_usage(self, user: Optional[User], ip_address: str) -> None:
        """Increment usage counter"""
        identifier = str(user.id) if user else f"ip:{ip_address}"
        today = datetime.utcnow().date()
        key = f"ratelimit:{identifier}:{today}"

        # Increment counter
        self.redis_client.incr(key)

        # Set expiry for midnight tomorrow (if new key)
        if self.redis_client.ttl(key) == -1:  # No expiry set
            tomorrow = today + timedelta(days=1)
            seconds_until_midnight = (
                datetime.combine(tomorrow, datetime.min.time()) - datetime.utcnow()
            ).total_seconds()
            self.redis_client.expire(key, int(seconds_until_midnight))


# Global rate limiter instance
rate_limiter = RateLimiter()
