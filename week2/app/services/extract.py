from __future__ import annotations

import re
from typing import List

from ollama import chat
from pydantic import BaseModel, ValidationError

from ..config import get_settings


BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


# ---------------------------------------------------------------------------
# Typed exception so routers can return the right HTTP status when the LLM
# call fails (Ollama not running, model not pulled, etc.) or returns output
# that doesn't satisfy the schema.
# ---------------------------------------------------------------------------
class LLMExtractionError(RuntimeError):
    """Raised when the Ollama call or its response is unusable."""


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    return _dedupe_preserve_order(extracted)


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen: set[str] = set()
    unique: List[str] = []
    for item in items:
        cleaned = item.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)
    return unique


# ---------------------------------------------------------------------------
# LLM-powered extraction (TODO 1)
# ---------------------------------------------------------------------------
#
# `extract_action_items_llm` mirrors the contract of `extract_action_items`
# (str in -> List[str] out) but delegates the extraction to a local Ollama
# model. It uses Ollama's structured outputs feature so the model is forced
# to return a JSON object matching `ActionItemList`, removing the need for
# brittle text parsing.
#
# Network / parsing failures are surfaced as `LLMExtractionError` so the
# API layer can translate them into a 502/503 response.
#
# See: https://ollama.com/blog/structured-outputs
class ActionItemList(BaseModel):
    items: List[str]


def extract_action_items_llm(text: str, model: str | None = None) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []

    chosen_model = model or get_settings().ollama_model

    system_prompt = (
        "You extract concrete, actionable to-do items from free-form notes. "
        "Return ONLY a JSON object matching the provided schema. "
        "Each item must be a short imperative phrase (e.g. 'Send the report to Alice'). "
        "Do not include explanations, numbering, bullet characters, or duplicates. "
        "If the note contains no actionable items, return an empty list."
    )

    try:
        response = chat(
            model=chosen_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            format=ActionItemList.model_json_schema(),
            options={"temperature": 0},
        )
    except Exception as exc:  # ollama client raises various exception types
        raise LLMExtractionError(f"Ollama call failed: {exc}") from exc

    raw = response["message"]["content"]
    try:
        parsed = ActionItemList.model_validate_json(raw)
    except ValidationError as exc:
        raise LLMExtractionError("Ollama returned malformed JSON") from exc

    return _dedupe_preserve_order(parsed.items)
