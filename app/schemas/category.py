"""
app/schemas/category.py
─────────────────────────────────────────────────────────────────────────────
Pydantic schemas for Categories.
"""

from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    display_name: str
    icon: Optional[str] = None
    color: Optional[str] = None
    sort_order: int
    system: bool
    parent_category_id: Optional[UUID] = None
