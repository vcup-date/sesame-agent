"""Does carrying the model's reasoning across tool calls change anything measurable?

sesame agent echoes every thinking block back to the model with the next request,
so the plan it made at step one is still in front of it at step nine. The
alternative, and what a harness does when it just appends the tool result and
re-sends, is to drop the reasoning and let the model re-derive its plan from its
own tool calls.

This runs the same task both ways, alternating, and prints what it finds:

    python3 bench/reasoning.py 10

What it found here, on deepseek-v4-flash, over 24 pairs: both ways solve the task
every single time, and on SPEED they are within noise of each other. An early
7-pair run showed carried reasoning a step and ~10% ahead; a 10-pair rerun put
dropped reasoning marginally ahead. That is what noise looks like, and it is why
this file exists instead of a number in the readme.

So the honest claim is the one about continuity, not speed: the model keeps its
plan across the tool boundary. Whether that buys you anything depends on your
model and your task, and this script is here so you can find out for yours rather
than believe a benchmark someone else ran. It would be worth running against a
model whose provider implements interleaved thinking natively; DeepSeek may
simply not do much with the echoed blocks.
"""

import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import shell                                     # noqa: E402
import tools as toolmod                          # noqa: E402
from config import Config                        # noqa: E402

WORK = Path(os.environ.get("TMPDIR", "/tmp")) / "sesame-bench"

TASK = ("This project has a bug and is missing features. Do all of it, one tool call at a time:\n"
        "1. read cart.py and test.py\n"
        "2. fix the discount bug in cart.py\n"
        "3. add a `student` tier at 15% to cart.py\n"
        "4. add asserts to test.py for vip (36.0) and student (38.25)\n"
        "5. run `python3 test.py`, and if it fails, fix it and run it again until it passes\n"
        "6. finally write a one line summary to NOTES.md")

CART = '''"""A shopping cart with tiered discounts."""

RATES = {"standard": 0.0, "member": 0.10, "vip": 0.20}


def subtotal(items):
    return sum(item["price"] * item["qty"] for item in items)


def total(items, tier="standard"):
    discount = RATES.get(tier, 0.0)
    return round(subtotal(items) * discount, 2)      # the bug: that is the discount, not the price
'''

TEST = '''from cart import total

ITEMS = [{"price": 20.0, "qty": 2}, {"price": 5.0, "qty": 1}]

assert total(ITEMS) == 45.0, f"standard: got {total(ITEMS)}, want 45.0"
assert total(ITEMS, "member") == 40.5, f"member: got {total(ITEMS, 'member')}, want 40.5"
print("2 passed")
'''


def fresh():
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True)
    (WORK / "cart.py").write_text(CART)
    (WORK / "test.py").write_text(TEST)


def once(carry):
    fresh()
    os.chdir(WORK)
    cfg = Config()
    api = dict(cfg.api)
    api["interleaved"] = carry

    keep = shell.ECHO_BLOCKS
    if not carry:
        shell.ECHO_BLOCKS = ("text", "tool_use")     # the reasoning is thrown away

    steps = {"n": 0}
    t0 = time.monotonic()
    try:
        result = shell.run(
            transcript=[{"role": "user", "content": TASK}],
            system="You are an agent. Use the tools. Be brief.",
            tools=toolmod.TOOLS,
            budget={"tool_calls": 25, "thinking_tokens": cfg.thinking_budget,
                    "effort": cfg.reasoning_effort, "grace": 2},
            safety=lambda call: {"allow": True},
            on_event=lambda ev: steps.__setitem__(
                "n", steps["n"] + (1 if ev.get("type") == "tool_use" else 0)),
            journal=lambda msg: None,
            api=api,
        )
    finally:
        shell.ECHO_BLOCKS = keep

    secs = time.monotonic() - t0
    solved = subprocess.run([sys.executable, "test.py"], cwd=WORK,
                            capture_output=True, text=True).returncode == 0
    return {"secs": secs, "steps": steps["n"],
            "out": result["spent"].get("output_tokens", 0), "solved": solved}


def main(pairs=7):
    runs = {"carried": [], "dropped": []}
    for i in range(pairs):
        for carry, name in ((True, "carried"), (False, "dropped")):
            r = once(carry)
            runs[name].append(r)
            print(f"pair {i + 1}  {name:8} {r['steps']:2d} calls  {r['secs']:5.1f}s  "
                  f"{r['out']:5d} output tokens  solved={r['solved']}")
    print()
    for name, rs in runs.items():
        print(f"{name:8} median {statistics.median(r['secs'] for r in rs):5.1f}s  "
              f"{statistics.median(r['steps'] for r in rs):.0f} calls  "
              f"{statistics.median(r['out'] for r in rs):.0f} output tokens  "
              f"solved {sum(r['solved'] for r in rs)}/{len(rs)}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 7)
