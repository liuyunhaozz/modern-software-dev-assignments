"""Pydantic request/response models.

Centralizing API schemas here gives FastAPI strong typing, automatic
validation, and a clean OpenAPI document. Routers should depend on
these models instead of `Dict[str, Any]` payloads.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ---------- Notes ----------------------------------------------------------


class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Raw note text.")


class NoteResponse(BaseModel):
    id: int
    content: str
    created_at: str


# ---------- Action items ---------------------------------------------------


class ActionItemResponse(BaseModel):
    id: int
    note_id: Optional[int] = None
    text: str
    done: bool = False
    created_at: Optional[str] = None


class ExtractRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Free-form note text.")
    save_note: bool = Field(
        default=False,
        description="If true, persist the note alongside the extracted items.",
    )


class ExtractResponse(BaseModel):
    note_id: Optional[int] = None
    items: List[ActionItemResponse]


class MarkDoneRequest(BaseModel):
    done: bool = True


class MarkDoneResponse(BaseModel):
    id: int
    done: bool


# ---------- Errors ---------------------------------------------------------


class ErrorResponse(BaseModel):
    detail: str
