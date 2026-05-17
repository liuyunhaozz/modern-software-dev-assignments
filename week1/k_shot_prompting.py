import os
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = """Reverse the input word letter-by-letter. Output ONLY the reversed word on a single line — no quotes, no labels, no punctuation, no explanation, no leading/trailing whitespace.

Method: the output is the input read strictly right-to-left. The leftmost input letter becomes the LAST output letter. The rightmost input letter becomes the FIRST output letter.

Worked examples (the middle line shows the right-to-left reading; the final line is the only thing you would output):

Input: cat
Right-to-left: t, a, c
Output: tac

Input: hello
Right-to-left: o, l, l, e, h
Output: olleh

Input: keyboard
Right-to-left: d, r, a, o, b, y, e, k
Output: draobyek

Input: assistant
Right-to-left: t, n, a, t, s, i, s, s, a
Output: tnatsissa

Input: programming
Right-to-left: g, n, i, m, m, a, r, g, o, r, p
Output: gnimmargorp

Input: localhost
Right-to-left: t, s, o, h, l, a, c, o, l
Output: tsohlacol

Input: serverstatus
Right-to-left: s, u, t, a, t, s, r, e, v, r, e, s
Output: sutatsrevres

Input: smtpstatus
Right-to-left: s, u, t, a, t, s, p, t, m, s
Output: sutatsptms

Input: ftpstatus
Right-to-left: s, u, t, a, t, s, p, t, f
Output: sutatsptf

Input: ottpstatus
Right-to-left: s, u, t, a, t, s, p, t, t, o
Output: sutatsptto

Input: abbpstatus
Right-to-left: s, u, t, a, t, s, p, b, b, a
Output: sutatspbba

Input: xkkystatus
Right-to-left: s, u, t, a, t, s, y, k, k, x
Output: sutatsykkx

Input: pingstatus
Right-to-left: s, u, t, a, t, s, g, n, i, p
Output: sutatsgnip

The user's input will be a single 10-letter word ending in "status". Do the right-to-left reading mentally — every letter must appear exactly once in the output, in reverse order — and output ONLY the final reversed word. No preface, no explanation, no quotes, no punctuation, no extra whitespace."""

USER_PROMPT = """
Reverse the order of letters in the following word. Only output the reversed word, no other text:

httpstatus
"""


EXPECTED_OUTPUT = "sutatsptth"


def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="mistral-nemo:12b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.5},
        )
        output_text = response.message.content.strip()

        if output_text.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {output_text}")
    return False


if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)
