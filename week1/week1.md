# Week 1 — How Each Prompting Technique Improves LLM Performance

A survey of six prompting techniques, each addressing a specific failure mode in base-model behavior. Implementations target local models via Ollama (`mistral-nemo:12b`, `llama3.1:8b`), but the mechanisms generalize.

## 1. K-shot prompting — `k_shot_prompting.py`

**Mechanism:** include `k` worked input→output examples in the prompt so the model conditions on the demonstrated pattern rather than its prior.

**How to use it:**
1. Identify the input/output shape of the task.
2. Write 3–10 demonstrations that match the target's structure (length, suffix, internal patterns), not just the task in the abstract.
3. Put the demonstrations in the system prompt, then the real input in the user prompt.
4. Audit your examples — a typo in a demonstration will be faithfully reproduced.

**Simple example:**
```
System:
Classify sentiment as positive or negative. Output one word only.

Input: I loved the movie.
Output: positive

Input: The food was cold and bland.
Output: negative

Input: This is the best book I have read all year.
Output: positive

User:
Input: The service was rude and slow.
Output:
```
→ `negative`

**How it improves performance:**
- **Bypasses tokenizer blind spots** for character-level tasks like letter reversal where the model has no native "character" primitive.
- **Replaces ambiguous instructions with a learned mapping.** Examples define the operation by extension, not intension.
- **Anchors output format.** Every example doubles as a format demonstration.
- **Performance scales with example similarity, not example count.** Adding mismatched examples can degrade performance.
- **Intermediate-step examples** (e.g., `Right-to-left: t, a, c` between input and output) force position-level reasoning and prevent chunk-level shortcuts.

## 2. Chain-of-thought — `chain_of_thought.py`

**Mechanism:** instruct the model to emit explicit intermediate reasoning steps before committing to a final answer.

**How to use it:**
1. In the system prompt, lay out a numbered procedure ("Step 1: ... Step 2: ...").
2. Name the relevant tools/techniques by name where applicable.
3. Add a self-verification step ("check the result with an independent method").
4. Pin a strict final-line format so downstream parsing isn't broken by the verbose reasoning.

**Simple example:**
```
System:
Solve the problem step by step. The very last line must be "Answer: <number>".

User:
Roger has 5 tennis balls. He buys 2 more cans of tennis balls.
Each can has 3 balls. How many tennis balls does he have now?
```
Model:
```
Step 1: Roger starts with 5 balls.
Step 2: 2 cans × 3 balls = 6 new balls.
Step 3: 5 + 6 = 11.
Answer: 11
```

**How it improves performance:**
- **Allocates compute to multi-step problems.** Intermediate tokens let the model carry partial state.
- **Decomposes the problem into independently-checkable units.**
- **Naming tools by name raises tool selection accuracy** more than "think carefully" ever will.
- **Built-in verification catches arithmetic slips.**
- **Strict final-line formatting** keeps the verbosity from breaking the parser.

## 3. Tool calling — `tool_calling.py`

**Mechanism:** expose external capabilities (file I/O, computation, APIs) to the model by having it emit a structured invocation that an executor runs.

**How to use it:**
1. Describe each tool in the system prompt: name, purpose, arguments, types, defaults.
2. Specify a strict output contract — typically a single JSON object with `tool` and `args` keys.
3. Include one concrete example invocation so the model has a syntactic template.
4. Parse the model's output, dispatch to the matching function, and (in multi-turn settings) feed the result back as a new message.

**Simple example:**
```
System:
You have one tool:
  add(a: int, b: int) -> int
Output ONLY a single JSON object: {"tool": "add", "args": {"a": ..., "b": ...}}.
No prose, no code fences.

User:
What is 17 + 25?
```
Model: `{"tool": "add", "args": {"a": 17, "b": 25}}` → executor runs `add(17, 25)` → `42`.

**How it improves performance:**
- **Replaces hallucination with execution.** Tasks that need real data or exact computation get real data and exact computation.
- **Externalizes capabilities the model lacks** — code execution, current data, statefulness.
- **For models without a native tool API,** schema lives entirely in the system prompt; output strictness is what makes the executor reliable.
- **A clear trigger phrase** removes ambiguity about *whether* to call the tool.
- **Composes with everything else** — foundation for agents, RAG retrieval, and reflexion loops.

## 4. Self-consistency — `self_consistency_prompting.py`

**Mechanism:** sample `N` independent reasoning traces at non-zero temperature and majority-vote over the final answers.

**How to use it:**
1. Write a CoT-style prompt with a strict final-line answer format.
2. Run it `N` times (commonly 5–20) at higher temperature (~1.0) for trace diversity.
3. Extract the final answer from each run with a regex.
4. Return the most common answer.

**Simple example:**
```
Prompt (run 5×, T=1.0):
"A shirt costs $20 and is on 25% off. What is the final price?
Reason step by step, then end with 'Answer: <number>'."

Run 1 → Answer: 15
Run 2 → Answer: 15
Run 3 → Answer: 16    (arithmetic slip)
Run 4 → Answer: 15
Run 5 → Answer: 15

Majority vote → 15  ✓
```

**How it improves performance:**
- **Trades latency for reliability.** Errors across traces are uncorrelated; the correct path is shared.
- **Higher temperature counterintuitively raises post-vote accuracy** by increasing path diversity.
- **Requires a canonical answer form** so the vote compares like-for-like.
- **Stacks on chain-of-thought** — CoT generates candidates, self-consistency selects.
- **Diminishing returns past ~10 samples**; cannot fix systematic bias.

## 5. Retrieval-Augmented Generation — `rag.py`

**Mechanism:** at query time, retrieve relevant documents from an external corpus and inject them into the prompt as grounding context.

**How to use it:**
1. Build (or load) a corpus of documents.
2. Implement a retriever — keyword overlap for narrow corpora, embedding similarity for broader ones.
3. At query time, retrieve the top-`k` documents for the user's question.
4. Inject them into the prompt as a `Context:` block, with strict "use ONLY this context" instructions.
5. Generate the answer grounded in the retrieved snippets.

**Simple example:**
```
Corpus snippet retrieved:
"The company's refund policy allows returns within 30 days of purchase
 with original receipt."

System: Answer using ONLY the provided context. If the answer isn't there,
say "I don't know."

User:
Context:
- The company's refund policy allows returns within 30 days of purchase
  with original receipt.

Question: How long do I have to return an item?
```
→ `30 days from the date of purchase, with the original receipt.`

**How it improves performance:**
- **Grounds output in authoritative sources** instead of the model's prior.
- **Decouples knowledge from weights** — docs can change without retraining.
- **Quality of retrieval bounds quality of generation.** Boosting the query with domain vocabulary helps when phrasing differs from the docs.
- **Strict grounding language matters.** "Use ONLY" + "verbatim" prevents the model from falling back to plausible-but-wrong defaults.
- **Validate by required snippets, not exact strings** for code-generation tasks.

## 6. Reflexion — `reflexion.py`

**Mechanism:** generate an initial solution, evaluate it against tests/critics, then feed the failure signal back into a second generation pass.

**How to use it:**
1. Generate an initial solution with a minimal system prompt.
2. Run it against tests or a critic; collect failures *with diagnostics* (not just pass/fail).
3. Build a reflexion context: previous code + failing cases + diagnostic info.
4. Re-prompt the model to reflect on the failures and rewrite the solution.
5. Repeat until passing or until a max-iteration budget is hit.

**Simple example:**
```
Task: write add_evens(nums) that sums the even numbers in nums.

Attempt 1:
  def add_evens(nums):
      return sum(nums)

Test: add_evens([1, 2, 3, 4]) → expected 6, got 10. Diagnostic:
"Function summed all numbers; did not filter for evens."

Reflexion prompt → "Your previous version summed every number. The task
requires filtering to even numbers (n % 2 == 0) before summing."

Attempt 2:
  def add_evens(nums):
      return sum(n for n in nums if n % 2 == 0)   ✓
```

**How it improves performance:**
- **Converts error signals into context.** The second pass has strictly more information than the first.
- **Compensates for underspecified initial prompts** — the spec emerges from failures.
- **Most effective when feedback is diagnostic, not binary.** "Failed" is weak signal; "failed because X" is actionable.
- **Bounded by iteration count** — diminishing returns kick in fast.
- **Conceptual basis for agentic coding workflows** — closest single-shot analog to "run the tests and read the output."

## Cross-cutting principles

- **Each technique addresses a distinct failure mode:** k-shot fixes pattern matching, CoT fixes multi-step reasoning, tool calling fixes capability gaps, self-consistency fixes stochastic errors, RAG fixes knowledge gaps, reflexion fixes specification gaps. They compose — agentic systems use all six.
- **Format discipline is a force multiplier.** Strict output contracts (single line, fenced block, exact regex, raw JSON) let downstream evaluators see correct answers when the model produces them.
- **Temperature is technique-dependent.** Low (0.0–0.3) for tool calling, RAG, and CoT where the single best trace is wanted. High (~1.0) for self-consistency where trace diversity drives accuracy.
- **The model is rarely the bottleneck.** Most performance gains come from removing degrees of freedom — through examples, structured procedures, retrieved context, executable tools, redundant sampling, or error-driven retries — rather than from changing the underlying model.
