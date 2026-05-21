from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from .. import db
from ..schemas import ErrorResponse, NoteCreate, NoteResponse


router = APIRouter(
    prefix="/notes",
    tags=["notes"],
    responses={404: {"model": ErrorResponse}},
)


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Persist a new note",
)
def create_note(payload: NoteCreate) -> NoteResponse:
    note_id = db.insert_note(payload.content.strip())
    note = db.get_note(note_id)
    assert note is not None  # row was just inserted
    return NoteResponse(**note)


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Fetch a single note by id",
)
def get_single_note(note_id: int) -> NoteResponse:
    note = db.get_note(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="note not found")
    return NoteResponse(**note)
