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
TODO
``` 

Generated/Modified Code Snippets:
```
TODO: List all modified code files with the relevant line numbers. (We anticipate there may be multiple scattered changes here – just produce as comprehensive of a list as you can.)
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