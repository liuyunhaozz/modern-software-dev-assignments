# K-Shot Prompting: Reversing `httpstatus` with `mistral-nemo:12b`

## Task

Get the model to output `sutatsptth` (the letter-reversal of `httpstatus`) using only a system-prompt edit. Test passes if any of 5 runs at `temperature=0.5` matches the expected string exactly after `.strip()`.

## Why this is hard

Letter-level reversal is a known weak spot for tokenizer-based LLMs: `httpstatus` is a small number of tokens, and the model has no native "character" primitive. With temperature 0.5 the output is also noisy across runs.

## Attempts and what each one revealed

### Attempt 1 — generic k-shot with unrelated short words
Examples: `hello → olleh`, `world → dlrow`, `programming → gnimmargorp`, etc., plus a verbal "read right-to-left" instruction.

**Result:** garbled outputs like `tatsuPth`, `stauspoth`, `tatusphtt`. The model partially recovered the `status` suffix but mangled or dropped letters elsewhere. Generic examples didn't transfer to a 10-letter compound word.

### Attempt 2 — compact `input -> output` pairs with `*status` words
Added many "second half = status" examples: `serverstatus → sutatsrevres`, `errorstatus → sutatsrorre`, etc., plus building blocks (`http → ptth`, `status → sutats`).

**Result:** `ptthsutats` (and variants). The model now produced the right *letters* but in the wrong *chunk order* — it reversed each half but kept the halves in original order. This is the classic "compound decomposition" failure: reversing parts independently without reversing the part sequence.

Also caught two of my own typos in this attempt (`ftpstatus → sutatspft` and `smtpstatus → sutatspmts` were both wrong). Bad k-shot examples actively mislead the model.

### Attempt 3 — explicit right-to-left position listing
Restructured every example as three lines:

```
Input: serverstatus
Right-to-left: s, u, t, a, t, s, r, e, v, r, e, s
Output: sutatsrevres
```

The middle line forces the model to "see" the reversal as a sequence of positional reads, not a chunk swap.

**Result:** chunk order fixed (now `sutats...ptth`-ish), but the model still dropped letters: `tatusptth` (9 chars instead of 10). It was getting `tatus` instead of `sutats` — likely confused by the `tt` doubled letter in `http`.

### Attempt 4 — add 10-letter `*status` examples with doubled-letter prefixes
Added examples that mirror `httpstatus`'s exact structure (10 letters, 4-letter prefix + "status", with doubled letters in the prefix):

- `ottpstatus → sutatsptto` (doubled `tt`, same as `httpstatus`)
- `abbpstatus → sutatspbba` (doubled `bb`)
- `xkkystatus → sutatsykkx` (doubled `kk`)
- `pingstatus → sutatsgnip`

Plus a final-line constraint: *"The user's input will be a single 10-letter word ending in 'status'. Every letter must appear exactly once in the output, in reverse order."*

**Result:** `SUCCESS` on the very first run.

## What actually worked, distilled

1. **Match the target's structure precisely in k-shot examples.** Generic `hello → olleh` doesn't transfer. Examples with the same length, same suffix, and same internal patterns (doubled letters) do.
2. **Force position-level reasoning.** The intermediate "Right-to-left: l1, l2, …, ln" line short-circuits the model's tendency to manipulate chunks.
3. **Pin the output format hard.** Single line, no preface, no quotes, no punctuation, no extra whitespace — and a length/count invariant the model can self-check against ("every letter must appear exactly once").
4. **Audit your own examples.** A wrong example in the prompt is worse than no example — the model will pattern-match the broken one.
5. **Diagnose by failure mode, not by retrying.** Each failure type (garbled letters → wrong chunk order → dropped letters → success) pointed at a different fix. Blindly resampling at temperature 0.5 wouldn't have closed the gap.

## Final prompt structure

- One-sentence task ("Reverse the input word letter-by-letter").
- Output-format constraints (single line, no extras).
- One-sentence method ("output is the input read strictly right-to-left").
- ~12 worked examples in 3-line form (`Input` / `Right-to-left` / `Output`), graded from short → long, ending in five 10-letter `*status` examples that match the target's structure.
- Closing constraint: input length, suffix, letter-count invariant, output-only rule.
