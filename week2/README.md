# Action Item Extractor

A minimal FastAPI + SQLite app that turns free-form notes into a checklist of
action items. Two extraction strategies are supported:

- **Heuristic** — regex/keyword matching on bullets (`-`, `*`, `1.`),
  checkbox markers (`[ ]`, `[todo]`), and keyword prefixes (`TODO:`,
  `ACTION:`, `NEXT:`). Fast, deterministic, no external dependencies.
- **LLM-powered** — calls a local [Ollama](https://ollama.com) model
  (default `llama3.1:8b`) and uses Ollama's structured-output feature so
  the model returns JSON validated against a Pydantic schema.

Notes and extracted items are persisted to a SQLite file at `data/app.db`.
A minimal vanilla-JS frontend at `/` lets you paste notes, extract action
items via either strategy, tick them off, and list previously saved notes.

## Project layout

```
week2/
├── app/
│   ├── main.py              # FastAPI app, lifespan, exception handlers
│   ├── config.py            # Settings dataclass (env-driven via dotenv)
│   ├── db.py                # SQLite connection ctx manager + helpers
│   ├── schemas.py           # Pydantic request/response models
│   ├── routers/
│   │   ├── notes.py         # /notes endpoints
│   │   └── action_items.py  # /action-items endpoints
│   └── services/
│       └── extract.py       # extract_action_items + extract_action_items_llm
├── frontend/
│   └── index.html           # Single-page UI (Extract, Extract LLM, List Notes)
├── tests/
│   └── test_extract.py      # Pytest tests for both extractors
├── data/
│   └── app.db               # SQLite database (auto-created on startup)
└── README.md
```

## Setup

Prerequisites: Python 3.12, Conda, Poetry, and (for LLM extraction)
[Ollama](https://ollama.com).

From the **repository root** (one level above this directory):

```bash
conda activate cs146s
poetry install --no-interaction
```

For LLM extraction, pull a model:

```bash
ollama pull llama3.1:8b
ollama serve     # starts the local server on http://localhost:11434
```

### Configuration

`app/config.py` reads the following environment variables (a `.env` file
at the project root is picked up automatically via python-dotenv):

| Variable        | Default                        | Purpose                                |
|-----------------|--------------------------------|----------------------------------------|
| `APP_NAME`      | `Action Item Extractor`        | OpenAPI title                          |
| `DATA_DIR`      | `week2/data`                   | Directory holding `app.db`             |
| `DB_PATH`       | `week2/data/app.db`            | SQLite database file                   |
| `FRONTEND_DIR`  | `week2/frontend`               | Static files + `index.html`            |
| `OLLAMA_MODEL`  | `llama3.1:8b`                  | Ollama model used by the LLM extractor |

## Run

From the **repository root**:

```bash
poetry run uvicorn week2.app.main:app --reload
```

Then open <http://127.0.0.1:8000/>. The interactive OpenAPI docs are at
<http://127.0.0.1:8000/docs>.

## API

All request and response bodies are JSON. Schemas live in
`app/schemas.py`.

### Notes — `app/routers/notes.py`

| Method & path        | Body              | Returns              | Description                          |
|----------------------|-------------------|----------------------|--------------------------------------|
| `POST /notes`        | `NoteCreate`      | `201 NoteResponse`   | Persist a new note.                  |
| `GET /notes`         | —                 | `200 List[NoteResponse]` | List all notes, newest first.    |
| `GET /notes/{id}`    | —                 | `200 NoteResponse` / `404 ErrorResponse` | Fetch a single note. |

### Action items — `app/routers/action_items.py`

| Method & path                          | Body              | Returns                            | Description                                                  |
|----------------------------------------|-------------------|------------------------------------|--------------------------------------------------------------|
| `POST /action-items/extract`           | `ExtractRequest`  | `201 ExtractResponse`              | Extract action items with the **heuristic** extractor.       |
| `POST /action-items/extract-llm`       | `ExtractRequest`  | `201 ExtractResponse` / `502 ErrorResponse` | Extract action items with the **LLM** extractor (Ollama). 502 if Ollama is unavailable or returns malformed JSON. |
| `GET /action-items`                    | —                 | `200 List[ActionItemResponse]`     | List action items, optionally filtered by `?note_id=`.       |
| `POST /action-items/{id}/done`         | `MarkDoneRequest` | `200 MarkDoneResponse` / `404 ErrorResponse` | Mark an action item as done or undo it.            |

`ExtractRequest` looks like:

```json
{
  "text": "TODO: deploy staging\n- email Alice",
  "save_note": true
}
```

When `save_note` is `true` the raw text is also persisted as a note and
the returned action items reference it via `note_id`.

### Example

```bash
curl -X POST http://127.0.0.1:8000/action-items/extract-llm \
     -H 'Content-Type: application/json' \
     -d '{"text": "- buy milk\n- call Bob", "save_note": true}'
```

## Frontend

`frontend/index.html` is a single static page with three actions:

- **Extract** — heuristic extraction via `/action-items/extract`.
- **Extract LLM** — LLM extraction via `/action-items/extract-llm`.
- **List Notes** — fetches `/notes` and renders each saved note.

Ticking the checkbox next to an extracted item POSTs to
`/action-items/{id}/done` so the state persists in the database.

## Database

SQLite, single file at `data/app.db`. The schema is created on app
startup via the FastAPI `lifespan` (see `app/main.py`).

```sql
notes(id, content, created_at)
action_items(id, note_id, text, done, created_at)
  -- note_id is nullable; FK -> notes(id) ON DELETE CASCADE
```

`PRAGMA foreign_keys = ON` is enforced on every connection (SQLite's
default is OFF). Every DB helper opens a short-lived connection through
the `connection()` context manager in `app/db.py`, which commits on
clean exit and rolls back on exception.

## Tests

From the **repository root**:

```bash
poetry run pytest week2/tests/ -v
```

The suite covers both extractors:

- `test_extract_bullets_and_checkboxes` — the heuristic extractor on
  mixed bullets / checkboxes / numbered lists.
- `test_llm_extract_*` (5 tests) — call the real `extract_action_items_llm`
  end-to-end against a running Ollama server and verify the LLM actually
  pulls action items out of bullet lists, keyword-prefixed lines, empty
  input, prose with no actions, and mixed prose + bullets.

The LLM tests require Ollama to be running locally with the configured
model pulled. Set `OLLAMA_MODEL` to override the default `llama3.1:8b`.

## Error handling

- `422` — request body fails Pydantic validation (e.g. missing `text`).
- `404` — referenced note or action item id does not exist.
- `502` — the LLM extractor raised `LLMExtractionError` (Ollama
  unreachable, model not pulled, or response did not satisfy the
  `ActionItemList` schema). The original cause is chained for logging.
