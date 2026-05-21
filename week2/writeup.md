# Week 2 Write-up
Tip: To preview this markdown file
- On Mac, press `Command (⌘) + Shift + V`
- On Windows/Linux, press `Ctrl + Shift + V`

## INSTRUCTIONS

Fill out all of the `TODO`s in this file.

## SUBMISSION DETAILS

Name: **TODO** \
SUNet ID: **TODO** \
Citations: **TODO**

This assignment took me about **TODO** hours to do. 


## YOUR RESPONSES
For each exercise, please include what prompts you used to generate the answer, in addition to the location of the generated response. Make sure to clearly add comments in your code documenting which parts are generated.

### Exercise 1: Scaffold a New Feature
Prompt: 
```
Analyze the existing `extract_action_items()` function in
`week2/app/services/extract.py`. It currently extracts action items using
predefined regex/keyword heuristics.

Implement an LLM-powered alternative called `extract_action_items_llm(text)`
in the same file that:
  - Has the same input/output contract as `extract_action_items` (str -> List[str]).
  - Uses the local Ollama Python client (`ollama.chat`) to call a small
    local model (default `llama3.2`, overridable via the `OLLAMA_MODEL`
    env var or a `model` kwarg).
  - Uses Ollama's structured outputs feature
    (https://ollama.com/blog/structured-outputs) by defining a Pydantic
    `ActionItemList` schema with an `items: List[str]` field and passing
    `ActionItemList.model_json_schema()` as the `format` argument so the
    model is forced to return valid JSON.
  - Validates/parses the response with `ActionItemList.model_validate_json`.
  - Uses a system prompt that asks for short imperative phrases, no
    numbering/bullets, no duplicates, and an empty list when the note
    contains nothing actionable.
  - Sets `temperature=0` for deterministic output.
  - Deduplicates results case-insensitively while preserving order
    (matching the heuristic extractor's behavior).
  - Returns `[]` for empty/whitespace input without calling the model.

Add explanatory comments above the new function and the schema class so a
reader can tell which parts are LLM-generated additions, and keep the
existing heuristic `extract_action_items()` function untouched.
``` 

Generated Code Snippets:
```
week2/app/services/extract.py:
  - Lines 9-10:   added `from pydantic import BaseModel` import
  - Lines 14-15:  added `OLLAMA_MODEL` env-configurable default model constant
  - Lines 18-23:  added `ActionItemList` Pydantic schema for structured output
  - Lines 104-158: added `extract_action_items_llm()` function that calls
                   Ollama with the JSON schema, parses the response, and
                   deduplicates the resulting list
```

### Exercise 2: Add Unit Tests
Prompt: 
```
Write pytest unit tests in `week2/tests/test_extract.py` that exercise
`extract_action_items_llm()` end-to-end against a real local Ollama
model. The goal is to verify the LLM actually pulls action items out of
free-form text — NOT to test the parsing/dedup code path around it. The
tests should mirror the style of the existing
`test_extract_bullets_and_checkboxes` test: feed input, then assert that
the expected concepts appear in the returned list.

Constraints / requirements:
  - Tests call the real `extract_action_items_llm` function (no mocking
    of `ollama.chat`). They require a running Ollama server with the
    configured model pulled.
  - Because LLM output is not perfectly deterministic (wording / casing
    can drift even at temperature=0), assertions should use a small
    case-insensitive substring helper rather than exact-equality
    matches. Add `_contains(items, keyword)` that returns True when any
    item contains `keyword` ignoring case.
  - Cover these cases as separate test functions:
      1. Bullet-list input → the LLM returns at least 3 items and the
         key concepts ("database", "extract endpoint", "tests") appear.
      2. Keyword-prefixed lines (TODO:/ACTION:/NEXT:) plus one stray
         non-actionable sentence → at least 3 items returned, with the
         key concepts ("staging", "design review", "retro") appearing.
      3. Empty and whitespace-only input → returns [].
      4. Prose with no actionable content → returns [].
      5. Mixed prose + bullets → at least 3 items, capturing the CI
         job, the README update, and the expense report.
  - Keep the existing `test_extract_bullets_and_checkboxes` test
    untouched.
  - Add a header comment block above the new tests explaining that
    they hit a real Ollama server and noting the model command
    (`ollama run llama3.1:8b`).
``` 

Generated Code Snippets:
```
week2/tests/test_extract.py:
  - Lines 1-3:    imports — `pytest`, `extract_action_items`,
                  `extract_action_items_llm` (mocking imports removed).
  - Lines 6-17:   pre-existing `test_extract_bullets_and_checkboxes` —
                  unchanged.
  - Lines 20-34:  header comment block explaining the live-LLM testing
                  strategy and the case-insensitive substring approach.
  - Lines 37-40:  `_contains(items, keyword)` helper for fuzzy
                  assertions tolerant of LLM wording drift.
  - Lines 43-56:  `test_llm_extract_bullet_list` — bullet input,
                  asserts the LLM returns the three key concepts.
  - Lines 59-73:  `test_llm_extract_keyword_prefixed_lines` —
                  TODO:/ACTION:/NEXT: input plus a stray sentence.
  - Lines 76-78:  `test_llm_extract_empty_input` — empty / whitespace
                  input returns [].
  - Lines 81-85:  `test_llm_extract_no_actionable_content` — prose
                  with no actions returns [].
  - Lines 88-101: `test_llm_extract_mixed_prose_and_bullets` — prose
                  + bullets, asserts CI/README/expense items are
                  captured.

Also updated `week2/app/services/extract.py:15` to default
`OLLAMA_MODEL` to `llama3.1:8b` (the model available locally).

Test run: 6 passed in 8.95s against a live Ollama server
(`llama3.1:8b`).
```

### Exercise 3: Refactor Existing Code for Clarity
Prompt: 
```
Refactor the backend under `week2/app/` to improve clarity along the
four axes the assignment calls out: API contracts/schemas, the database
layer, app lifecycle/configuration, and error handling. Make the changes
minimal and conservative — keep all behavior compatible with the
existing unit tests in `week2/tests/test_extract.py`. Specifically:

1. API contracts / schemas
   - Create a new module `week2/app/schemas.py` with Pydantic
     request/response models: `NoteCreate`, `NoteResponse`,
     `ActionItemResponse`, `ExtractRequest`, `ExtractResponse`,
     `MarkDoneRequest`, `MarkDoneResponse`, `ErrorResponse`.
   - Replace every `Dict[str, Any]` payload in
     `week2/app/routers/notes.py` and
     `week2/app/routers/action_items.py` with the appropriate Pydantic
     model and declare `response_model=...` on every route so the
     OpenAPI document is accurate.
   - The /extract endpoint should return HTTP 201 (a resource was
     created); POST /notes should also return 201.

2. Database layer
   - Refactor `week2/app/db.py`:
       * Add a `connection()` context manager that enables
         `PRAGMA foreign_keys = ON`, commits on clean exit, rolls back
         on exception, and always closes the handle.
       * Move the CREATE TABLE strings into named module-level
         constants and add `ON DELETE CASCADE` to the foreign key.
       * Stop leaking `sqlite3.Row` to callers — every helper should
         return plain dicts (or None) via small adapter functions.
       * Add a `get_action_item(id)` helper for the new 404 path.
       * `mark_action_item_done` should return True/False indicating
         whether a row was actually updated, so the router can return
         404 when the id is missing.
       * `insert_action_items([])` should short-circuit instead of
         opening a connection.

3. App lifecycle / configuration
   - Create `week2/app/config.py` exposing a frozen `Settings`
     dataclass populated from environment variables (loaded via
     python-dotenv) with `app_name`, `data_dir`, `db_path`,
     `frontend_dir`, `ollama_model`. Wrap construction in a
     `@lru_cache`d `get_settings()`.
   - In `week2/app/main.py`, replace the top-level `init_db()` call
     with a FastAPI `lifespan` async context manager so importing
     `app.main` has no side effects.
   - Cache the index HTML on first read instead of reading it from
     disk on every "/" request.
   - Drive paths (db_path, frontend_dir) and the LLM model from
     `get_settings()` rather than hard-coding them.

4. Error handling
   - Define a `LLMExtractionError` exception in
     `week2/app/services/extract.py` and raise it (chaining the
     original cause) when the Ollama call fails or when the model
     returns JSON that doesn't satisfy the `ActionItemList` schema.
   - In `week2/app/main.py`, register a global exception handler
     that maps `LLMExtractionError` to HTTP 502 with a JSON
     `{"detail": ...}` body.
   - In the notes and action-items routers, return HTTP 404 with the
     `ErrorResponse` schema when a referenced id does not exist.
   - Restore the original heuristic extractor as the default for
     POST /action-items/extract (the LLM-powered endpoint belongs in
     TODO 4, as a separate route).

Keep the public function names `extract_action_items` and
`extract_action_items_llm` (and the `extract_action_items_llm(text,
model=None)` signature) unchanged so the existing tests still pass.
Verify by running `poetry run pytest week2/tests/` and by spinning up
the app with `TestClient` to confirm the new 404 / 422 / 201 status
codes are returned.
``` 

Generated/Modified Code Snippets:
```
New files:
  - week2/app/schemas.py (entire file)
      * Pydantic request/response models for every endpoint plus
        `ErrorResponse`.
  - week2/app/config.py (entire file)
      * `Settings` dataclass + `get_settings()` reading
        APP_NAME / DATA_DIR / DB_PATH / FRONTEND_DIR / OLLAMA_MODEL
        from env (via python-dotenv).

Refactored files:
  - week2/app/db.py (entire file rewritten)
      * Lines 21-39:   SQL moved into `_CREATE_NOTES_TABLE` /
                       `_CREATE_ACTION_ITEMS_TABLE` constants;
                       `ON DELETE CASCADE` added.
      * Lines 46-65:   new `connection()` context manager — enables
                       `PRAGMA foreign_keys = ON`, commits/rolls back
                       around the block, always closes.
      * Lines 67-71:   `init_db()` now goes through `connection()`.
      * Lines 76-87:   `_note_row` / `_action_item_row` adapters so
                       callers never see `sqlite3.Row`.
      * Lines 92-115:  notes helpers (`insert_note`, `list_notes`,
                       `get_note`) return plain dicts / None.
      * Lines 120-152: action-item helpers — `insert_action_items`
                       short-circuits on empty input;
                       `get_action_item` added; `mark_action_item_done`
                       now returns bool (rowcount > 0).
  - week2/app/main.py (entire file rewritten)
      * Lines 14-20:   `lifespan` async context manager replaces the
                       import-time `init_db()` call.
      * Lines 23-24:   app constructed from `settings.app_name` with
                       `lifespan=lifespan`.
      * Lines 30-36:   global `LLMExtractionError` -> 502 handler.
      * Lines 41-50:   index HTML cached after first read; path comes
                       from `settings.frontend_dir`.
      * Lines 56-60:   static mount uses `settings.frontend_dir`.
  - week2/app/routers/notes.py (entire file rewritten)
      * Switched to `NoteCreate` / `NoteResponse` models.
      * POST /notes now returns HTTP 201.
      * GET /notes/{id} returns 404 + `ErrorResponse` for missing ids.
  - week2/app/routers/action_items.py (entire file rewritten)
      * Switched to `ExtractRequest` / `ExtractResponse` /
        `MarkDoneRequest` / `MarkDoneResponse` / `ActionItemResponse`.
      * POST /action-items/extract returns 201 and goes through a
        shared `_persist_extraction()` helper (sets up TODO 4 nicely).
      * POST /action-items/{id}/done returns 404 when the id is missing.
      * Restored heuristic `extract_action_items` import; LLM endpoint
        is deferred to TODO 4.
  - week2/app/services/extract.py (substantial rewrite)
      * Lines 8-10:   `ValidationError` import + new `get_settings`
                      import (model name now read from settings).
      * Lines 22-25:  `LLMExtractionError` typed exception.
      * Lines 89-101: pulled deduplication into a shared
                      `_dedupe_preserve_order` helper used by both
                      heuristic and LLM paths.
      * Lines 118-153: LLM call wrapped in try/except that raises
                      `LLMExtractionError` on Ollama errors and on
                      Pydantic validation failures (chaining the cause).

Verification:
  - `poetry run pytest week2/tests/` — 6 passed in 7.88s.
  - TestClient smoke checks: empty body → 422, happy path → 201
    with structured items, missing note id → 404 / "note not found",
    bad mark-done id → 404 / "action item not found", good mark-done
    id → 200 / {"id": …, "done": true}.
```


### Exercise 4: Use Agentic Mode to Automate a Small Task
Prompt: 
```
TODO
``` 

Generated Code Snippets:
```
TODO: List all modified code files with the relevant line numbers.
```


### Exercise 5: Generate a README from the Codebase
Prompt: 
```
TODO
``` 

Generated Code Snippets:
```
TODO: List all modified code files with the relevant line numbers.
```


## SUBMISSION INSTRUCTIONS
1. Hit a `Command (⌘) + F` (or `Ctrl + F`) to find any remaining `TODO`s in this file. If no results are found, congratulations – you've completed all required fields. 
2. Make sure you have all changes pushed to your remote repository for grading.
3. Submit via Gradescope. 