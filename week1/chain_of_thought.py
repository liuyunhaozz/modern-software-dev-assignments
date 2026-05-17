import os
import re
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = """
You are a careful mathematical reasoner. For every problem, think step by step
before committing to an answer.

Follow this procedure:
1. Restate the problem in your own words so the goal is unambiguous.
2. Identify the relevant mathematical tools (e.g., Euler's theorem, modular
   exponentiation, Chinese Remainder Theorem, repeated squaring).
3. Work through the computation in small, explicit steps. Show every
   intermediate value (e.g., reduce the exponent modulo phi(n), then build up
   powers via repeated squaring, reducing modulo n at each step).
4. Double-check the arithmetic of each step before continuing. If a step looks
   suspicious, redo it.
5. Verify the final result with an independent method when feasible (e.g.,
   compute via a different factorization of the exponent and confirm the two
   results agree).

Formatting rules (strict):
- Write the reasoning as numbered steps.
- The VERY LAST line of your response must be exactly:
  Answer: <number>
  where <number> is a single integer with no units, no words, and no extra
  punctuation. Do not write anything after this line.

Worked example (style only, do not reuse the numbers):
Problem: Compute 7^222 (mod 10).
Step 1: phi(10) = 4 and gcd(7, 10) = 1, so 7^4 = 1 (mod 10).
Step 2: 222 mod 4 = 2.
Step 3: 7^2 = 49 = 9 (mod 10).
Step 4: Verify: 7^4 = 9^2 = 81 = 1 (mod 10). Consistent.
Answer: 9
""".strip()


USER_PROMPT = """
Solve this problem, then give the final answer on the last line as "Answer: <number>".

what is 3^{12345} (mod 100)?
"""


# For this simple example, we expect the final numeric answer only
EXPECTED_OUTPUT = "Answer: 43"


def extract_final_answer(text: str) -> str:
    """Extract the final 'Answer: ...' line from a verbose reasoning trace.

    - Finds the LAST line that starts with 'Answer:' (case-insensitive)
    - Normalizes to 'Answer: <number>' when a number is present
    - Falls back to returning the matched content if no number is detected
    """
    matches = re.findall(r"(?mi)^\s*answer\s*:\s*(.+)\s*$", text)
    if matches:
        value = matches[-1].strip()
        # Prefer a numeric normalization when possible (supports integers/decimals)
        num_match = re.search(r"-?\d+(?:\.\d+)?", value.replace(",", ""))
        if num_match:
            return f"Answer: {num_match.group(0)}"
        return f"Answer: {value}"
    return text.strip()


def test_your_prompt(system_prompt: str) -> bool:
    """Run up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="llama3.1:8b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.3},
        )
        output_text = response.message.content
        final_answer = extract_final_answer(output_text)
        # breakpoint()
        if final_answer.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {final_answer}")
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)
