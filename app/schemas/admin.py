from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

class DuplicateTransactionSummary(BaseModel):
    id: uuid.UUID
    amount: float
    merchant: str
    transaction_date: datetime
    is_recurring: bool

class DuplicateGroup(BaseModel):
    original: DuplicateTransactionSummary
    duplicates: List[DuplicateTransactionSummary]
    has_anomalous_recurring: bool = False

class DuplicateReportResponse(BaseModel):
    user_id: str
    total_groups: int
    total_duplicates: int
    groups: List[DuplicateGroup]

class DuplicateDeleteRequest(BaseModel):
    transaction_ids: Optional[List[uuid.UUID]] = None

class DuplicateDeleteResponse(BaseModel):
    deleted_count: int
    deleted_ids: List[uuid.UUID]
    dry_run: bool
    message: str
