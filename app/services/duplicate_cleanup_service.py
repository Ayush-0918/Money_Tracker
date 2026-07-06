import uuid
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from app.models.transaction import Transaction
from app.models.deleted_transaction import DeletedTransaction
from app.schemas.admin import (
    DuplicateGroup,
    DuplicateTransactionSummary,
    DuplicateReportResponse,
    DuplicateDeleteResponse,
)

logger = logging.getLogger(__name__)


async def detect_duplicates_for_user(db: AsyncSession, user_id: uuid.UUID) -> List[DuplicateGroup]:
    # Fetch all transactions for the user ordered by date
    stmt = select(Transaction).where(Transaction.user_id == user_id).order_by(Transaction.transaction_date)
    result = await db.execute(stmt)
    transactions = result.scalars().all()

    groups: List[DuplicateGroup] = []

    if not transactions:
        return groups

    # Grouping logic (O(N) iteration)
    # We maintain a list of active groups
    active_groups: List[List[Transaction]] = []

    for tx in transactions:
        added_to_group = False
        for group in active_groups:
            # Check against the first item in the group
            base = group[0]
            if tx.amount == base.amount and tx.merchant.lower() == base.merchant.lower():
                time_diff = abs((tx.transaction_date - base.transaction_date).total_seconds())
                if time_diff <= 120:
                    group.append(tx)
                    added_to_group = True
                    break

        if not added_to_group:
            active_groups.append([tx])

    # Filter out singletons (no duplicates)
    for group in active_groups:
        if len(group) > 1:
            # Determine the "original"
            # Priority 1: is_recurring == True
            # Priority 2: Earliest created_at (we use transaction_date as proxy if created_at isn't available, but we can just use the first item since it's sorted)

            # Sort group: recurring first, then earliest date
            group_sorted = sorted(group, key=lambda t: (not t.is_recurring, t.transaction_date))

            original = group_sorted[0]

            # PROTECT SUBSCRIPTIONS:
            # Only non-recurring transactions can be considered duplicates.
            # If a transaction is recurring, it is tied to a subscription record.
            # Deleting it could break the subscription reference or cause cascade deletes.
            duplicates = [d for d in group_sorted[1:] if not d.is_recurring]
            anomalous_recurring = any(d.is_recurring for d in group_sorted[1:])

            if duplicates or anomalous_recurring:
                groups.append(
                    DuplicateGroup(
                        original=DuplicateTransactionSummary(
                            id=original.id,
                            amount=float(original.amount),
                            merchant=original.merchant,
                            transaction_date=original.transaction_date,
                            is_recurring=original.is_recurring,
                        ),
                        duplicates=[
                            DuplicateTransactionSummary(
                                id=d.id,
                                amount=float(d.amount),
                                merchant=d.merchant,
                                transaction_date=d.transaction_date,
                                is_recurring=d.is_recurring,
                            )
                            for d in duplicates
                        ],
                        has_anomalous_recurring=anomalous_recurring,
                    )
                )

    return groups


async def get_duplicate_report(db: AsyncSession, user_id: Optional[uuid.UUID] = None) -> DuplicateReportResponse:
    if user_id:
        groups = await detect_duplicates_for_user(db, user_id)
        total_dups = sum(len(g.duplicates) for g in groups)
        return DuplicateReportResponse(
            user_id=str(user_id), total_groups=len(groups), total_duplicates=total_dups, groups=groups
        )
    else:
        # If no user_id, fetch all unique users
        stmt = select(Transaction.user_id).distinct()
        result = await db.execute(stmt)
        user_ids = result.scalars().all()

        all_groups = []
        for uid in user_ids:
            all_groups.extend(await detect_duplicates_for_user(db, uid))

        total_dups = sum(len(g.duplicates) for g in all_groups)
        return DuplicateReportResponse(
            user_id="ALL", total_groups=len(all_groups), total_duplicates=total_dups, groups=all_groups
        )


async def delete_duplicates(
    db: AsyncSession, user_id: Optional[uuid.UUID], confirm: bool, specific_ids: Optional[List[uuid.UUID]] = None
) -> DuplicateDeleteResponse:

    # 1. Get the report to find duplicates
    report = await get_duplicate_report(db, user_id)

    # Extract IDs to delete
    to_delete_ids = []
    to_delete_records = []

    for group in report.groups:
        for dup in group.duplicates:
            if specific_ids is None or dup.id in specific_ids:
                to_delete_ids.append(dup.id)
                to_delete_records.append(dup)

    if not to_delete_ids:
        return DuplicateDeleteResponse(
            deleted_count=0, deleted_ids=[], dry_run=not confirm, message="No duplicates found to delete."
        )

    if len(to_delete_ids) > 500:
        logger.warning("Attempted to delete %s duplicates, limiting to 500", len(to_delete_ids))
        to_delete_ids = to_delete_ids[:500]
        to_delete_records = to_delete_records[:500]

    if not confirm:
        return DuplicateDeleteResponse(
            deleted_count=len(to_delete_ids),
            deleted_ids=to_delete_ids,
            dry_run=True,
            message=f"Dry run. Would delete {len(to_delete_ids)} duplicates. Use ?confirm=true to execute.",
        )

    # 2. Actual Deletion (Fetch full records to backup)
    stmt = select(Transaction).where(Transaction.id.in_(to_delete_ids))
    result = await db.execute(stmt)
    full_transactions = result.scalars().all()

    # Create backup records
    backups = []
    for tx in full_transactions:
        # Find the original ID from the group
        orig_id = None
        for group in report.groups:
            if tx.id in [d.id for d in group.duplicates]:
                orig_id = group.original.id
                break

        if tx.is_recurring:
            # Safety mechanism: log a high severity warning, or you could skip deletion
            logger.critical("Deleting a transaction that was marked as recurring! ID: %s", tx.id)

        backup = DeletedTransaction(
            original_transaction_id=orig_id or tx.id,
            user_id=tx.user_id,
            amount=tx.amount,
            merchant=tx.merchant,
            transaction_date=tx.transaction_date,
            source=tx.source,
            raw_text=tx.raw_text,
            reason="duplicate_cleanup",
        )
        backups.append(backup)

    db.add_all(backups)

    # Delete from main table
    del_stmt = delete(Transaction).where(Transaction.id.in_(to_delete_ids))
    await db.execute(del_stmt)

    await db.commit()

    logger.info("Deleted %s duplicate transactions (Backed up to deleted_transactions_log)", len(to_delete_ids))

    return DuplicateDeleteResponse(
        deleted_count=len(to_delete_ids),
        deleted_ids=to_delete_ids,
        dry_run=False,
        message=f"Successfully deleted {len(to_delete_ids)} duplicates and backed them up.",
    )
