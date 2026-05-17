import os
import re
from typing import List, Callable
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 5

DATA_FILES: List[str] = [
    os.path.join(os.path.dirname(__file__), "data", "api_docs.txt"),
]


def load_corpus_from_files(paths: List[str]) -> List[str]:
    corpus: List[str] = []
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    corpus.append(f.read())
            except Exception as exc:
                corpus.append(f"[load_error] {p}: {exc}")
        else:
            corpus.append(f"[missing_file] {p}")
    return corpus


# Load corpus from external files (simple API docs). If missing, fall back to inline snippet
CORPUS: List[str] = load_corpus_from_files(DATA_FILES)

QUESTION = (
    "Write a Python function `fetch_user_name(user_id: str, api_key: str) -> str` that calls the documented API "
    "to fetch a user by id and returns only the user's name as a string."
)


YOUR_SYSTEM_PROMPT = (
    "You are a precise Python coding assistant. "
    "Use ONLY the API details provided in the user's Context block; do not invent endpoints, headers, or response fields. "
    "If the context specifies a Base URL, endpoint path, authentication header, or response schema, use them verbatim. "
    "Produce a single self-contained Python function that uses the `requests` library, "
    "sends the documented authentication header, calls response.raise_for_status() for non-200 responses, "
    "and returns only the requested field as a string. "
    "Respond with a single fenced ```python code block containing the imports and the function, and nothing else."
)


# For this simple example
# For this coding task, validate by required snippets rather than exact string
REQUIRED_SNIPPETS = [
    "def fetch_user_name(",
    "requests.get",
    "/users/",
    "X-API-Key",
    "return",
]


def YOUR_CONTEXT_PROVIDER(corpus: List[str]) -> List[str]:
    """Retrieve documents relevant to the QUESTION via simple keyword overlap scoring."""
    query_terms = {t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]+", QUESTION) if len(t) > 2}
    # Always-useful API vocabulary so doc snippets describing endpoints/auth score well.
    query_terms.update({"api", "endpoint", "header", "auth", "base", "url", "users"})

    scored: List[tuple] = []
    for doc in corpus:
        doc_terms = {t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]+", doc)}
        overlap = len(query_terms & doc_terms)
        if overlap > 0:
            scored.append((overlap, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_docs = [doc for _, doc in scored[:3]]
    return top_docs if top_docs else list(corpus)


def make_user_prompt(question: str, context_docs: List[str]) -> str:
    if context_docs:
        context_block = "\n".join(f"- {d}" for d in context_docs)
    else:
        context_block = "(no context provided)"
    return (
        f"Context (use ONLY this information):\n{context_block}\n\n"
        f"Task: {question}\n\n"
        "Requirements:\n"
        "- Use the documented Base URL and endpoint.\n"
        "- Send the documented authentication header.\n"
        "- Raise for non-200 responses.\n"
        "- Return only the user's name string.\n\n"
        "Output: A single fenced Python code block with the function and necessary imports.\n"
    )


def extract_code_block(text: str) -> str:
    """Extract the last fenced Python code block, or any fenced code block, else return text."""
    # Try ```python ... ``` first
    m = re.findall(r"```python\n([\s\S]*?)```", text, flags=re.IGNORECASE)
    if m:
        return m[-1].strip()
    # Fallback to any fenced code block
    m = re.findall(r"```\n([\s\S]*?)```", text)
    if m:
        return m[-1].strip()
    return text.strip()


def test_your_prompt(
    system_prompt: str, context_provider: Callable[[List[str]], List[str]]
) -> bool:
    """Run up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT."""
    context_docs = context_provider(CORPUS)
    user_prompt = make_user_prompt(QUESTION, context_docs)

    # breakpoint()

    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.0},
        )
        output_text = response.message.content
        code = extract_code_block(output_text)
        missing = [s for s in REQUIRED_SNIPPETS if s not in code]
        if not missing:
            print(output_text)
            print("SUCCESS")
            return True
        else:
            print("Missing required snippets:")
            for s in missing:
                print(f"  - {s}")
            print("Generated code:\n" + code)
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT, YOUR_CONTEXT_PROVIDER)
