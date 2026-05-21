from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, status

from .. import db
from ..schemas import (
    ActionItemResponse,
    ErrorResponse,
    ExtractRequest,
    ExtractResponse,
    MarkDoneRequest,
    MarkDoneResponse,
)
from ..services.extract import extract_action_items, extract_action_items_llm


router = APIRouter(
    prefix="/action-items",
    tags=["action-items"],
    responses={404: {"model": ErrorResponse}},
)


def _persist_extraction(text: str, items: List[str], save_note: bool) -> ExtractResponse:
    """Shared post-extraction persistence used by every /extract* endpoint."""
    note_id: Optional[int] = db.insert_note(text) if save_note else None
    ids = db.insert_action_items(items, note_id=note_id)
    return ExtractResponse(
        note_id=note_id,
        items=[
            ActionItemResponse(id=i, note_id=note_id, text=t)
            for i, t in zip(ids, items)
        ],
    )


@router.post(
    "/extract",
    response_model=ExtractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Extract action items using the heuristic extractor",
)
def extract(payload: ExtractRequest) -> ExtractResponse:
    text = payload.text.strip()
    items = extract_action_items(text)
    return _persist_extraction(text, items, payload.save_note)


# TODO 4: LLM-powered extraction endpoint. Mirrors /extract but delegates
# extraction to Ollama. `LLMExtractionError` raised by the service layer is
# caught by the global handler in main.py and mapped to HTTP 502.
@router.post(
    "/extract-llm",
    response_model=ExtractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Extract action items using the LLM extractor (Ollama)",
)
def extract_llm(payload: ExtractRequest) -> ExtractResponse:
    text = payload.text.strip()
    items = extract_action_items_llm(text)
    return _persist_extraction(text, items, payload.save_note)


@router.get(
    "",
    response_model=List[ActionItemResponse],
    summary="List action items, optionally filtered by note",
)
def list_all(note_id: Optional[int] = None) -> List[ActionItemResponse]:
    rows = db.list_action_items(note_id=note_id)
    return [ActionItemResponse(**r) for r in rows]


@router.post(
    "/{action_item_id}/done",
    response_model=MarkDoneResponse,
    summary="Mark an action item as done (or undo it)",
)
def mark_done(action_item_id: int, payload: MarkDoneRequest) -> MarkDoneResponse:
    updated = db.mark_action_item_done(action_item_id, payload.done)
    if not updated:
        raise HTTPException(status_code=404, detail="action item not found")
    return MarkDoneResponse(id=action_item_id, done=payload.done)
