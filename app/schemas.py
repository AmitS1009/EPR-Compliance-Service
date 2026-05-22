import re
from datetime import datetime
from typing import Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PLASTIC_CATEGORIES = {"rigid_plastic", "flexible_plastic", "multilayer_plastic"}


class DeclarationCreate(BaseModel):
    producer_id: str = Field(..., min_length=1)
    month: str
    declared_quantities_kg: Dict[str, float]

    model_config = ConfigDict(extra="forbid")

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
            raise ValueError("month must be in YYYY-MM format")
        return value

    @model_validator(mode="after")
    def validate_quantities(self) -> "DeclarationCreate":
        categories = set(self.declared_quantities_kg)
        if categories != PLASTIC_CATEGORIES:
            missing = sorted(PLASTIC_CATEGORIES - categories)
            extra = sorted(categories - PLASTIC_CATEGORIES)
            parts = []
            if missing:
                parts.append(f"missing categories: {', '.join(missing)}")
            if extra:
                parts.append(f"unsupported categories: {', '.join(extra)}")
            raise ValueError("; ".join(parts))
        for category, kg in self.declared_quantities_kg.items():
            if kg < 0:
                raise ValueError(f"{category} cannot be negative")
        return self


class StoredDeclaration(DeclarationCreate):
    record_id: str
    created_at: datetime


class CategoryReconciliation(BaseModel):
    category: str
    declared_kg: float
    procured_kg: float
    difference_kg: float
    difference_percent: float | None
    flagged: bool
    status: Literal["within_tolerance", "over_declared", "under_declared"]


class SummaryResponse(BaseModel):
    producer_id: str
    month: str
    tolerance_percent: float
    reconciliation: List[CategoryReconciliation]
    narrative: str
    llm_provider: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)

    model_config = ConfigDict(extra="forbid")


class Citation(BaseModel):
    document: str
    section: str
    score: float


class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]
    llm_provider: str
