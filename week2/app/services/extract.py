from __future__ import annotations

import os
import re
from typing import List
import json
from typing import Any
from ollama import chat
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Default Ollama model used for LLM-powered extraction. Override via env var.
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")


# Pydantic schema for Ollama structured outputs: a JSON object containing
# an array of action item strings. Using a Pydantic model lets us pass the
# model's JSON schema directly to Ollama via the `format` parameter, then
# validate/parse the LLM's response in a single step.
class ActionItemList(BaseModel):
    items: List[str]


BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


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
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


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
# See: https://ollama.com/blog/structured-outputs
def extract_action_items_llm(text: str, model: str | None = None) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []

    chosen_model = model or OLLAMA_MODEL

    system_prompt = (
        "You extract concrete, actionable to-do items from free-form notes. "
        "Return ONLY a JSON object matching the provided schema. "
        "Each item must be a short imperative phrase (e.g. 'Send the report to Alice'). "
        "Do not include explanations, numbering, bullet characters, or duplicates. "
        "If the note contains no actionable items, return an empty list."
    )

    print("system_prompt: ", system_prompt)
    print("text: ", text)

    response = chat(
        model=chosen_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        # Pass the JSON schema of our Pydantic model so Ollama constrains
        # the model output to a valid JSON object with an `items` array.
        format=ActionItemList.model_json_schema(),
        options={"temperature": 0},
    )

    raw = response["message"]["content"]
    parsed = ActionItemList.model_validate_json(raw)

    print("response: ", response)
    print("parsed: ", parsed)

    # Deduplicate (case-insensitive) while preserving order — same contract
    # as the heuristic extractor above.
    seen: set[str] = set()
    unique: List[str] = []
    for item in parsed.items:
        cleaned = item.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(cleaned)
    return unique
