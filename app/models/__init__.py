"""
app/models/__init__.py
─────────────────────────────────────────────────────────────────────────────
Re-exports all ORM models so that Alembic's env.py can import them via:
    from app.models import Base, User, Transaction, Subscription

This ensures all model metadata is registered with Base before migrations run.
"""

from app.models.base import Base, TimestampMixin, new_uuid
from app.models.user import User
from app.models.transaction import Transaction
from app.models.deleted_transaction import DeletedTransaction
from app.models.subscription import Subscription
from app.models.category import Category
from app.models.merchant import Merchant, MerchantAlias, MerchantRule, UserOverride, LearningEvent
from app.models.budget import Budget
from app.models.family import FamilyWallet, FamilyMember, SharedExpense
from app.models.dream import Dream
from app.models.notification import DeviceToken, Notification

__all__ = [
    "Base",
    "TimestampMixin",
    "new_uuid",
    "User",
    "Transaction",
    "DeletedTransaction",
    "Subscription",
    "Category",
    "Merchant",
    "MerchantAlias",
    "MerchantRule",
    "UserOverride",
    "LearningEvent",
    "Budget",
    "FamilyWallet",
    "FamilyMember",
    "SharedExpense",
    "Dream",
    "DeviceToken",
    "Notification",
]
