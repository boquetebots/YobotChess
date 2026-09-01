#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_dropout.py — proving the show survives losing the internet
================================================================================

Checks that a robot which cannot speak costs the demo a SILENCE and nothing
more. See `chess_dropout.py` for why that matters and what goes wrong without
it.

Needs nothing at all: no robot, no Azure, no internet, no chess engine, no
pip add-ons. Run it any time:

    python test_dropout.py

--------------------------------------------------------------------------------
WHY SOME OF THESE READ THE SOURCE INSTEAD OF RUNNING IT
--------------------------------------------------------------------------------

`chess_player.py` cannot be imported on a machine with no robot libraries, and
insisting on them would make this test the one nobody runs. So the checks that
concern chess_player.py read it AS CODE with `ast` — the same approach
`test_animation.py` uses for the shutdown order, and for the same reason.

Reading it as code rather than searching the raw text matters: the comments in
these files necessarily quote the very calls being checked for, and a checker
that cannot tell an instruction from a sentence about an instruction is worse
than no checker.

--------------------------------------------------------------------------------
PUTTING THE BUG BACK
--------------------------------------------------------------------------------

A test that has never failed has not been shown to work. The last group of
checks doctors a copy of `chess_player.py` in memory — removing the guard,
removing the floor hand-back — and confirms the source checks above go red on
it. Nothing on disk is touched.
"""

import ast
import asyncio
import io
import os
import re
import sys

import chess_dropout
from chess_dropout import KeepTalking


RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))


def run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


# ── A pretend robot ──────────────────────────────────────────────────────────

class PretendRobot:
    """Stands in for AsyncOhbotController. Says nothing, moves nothing."""

    def __init__(self, behaviour):
        self.behaviour = behaviour          # a list, one entry per attempt
        self.attempts = 0
        self.spoken = []

    async def say(self, text, lip_sync=True, language=None):
        i = min(self.attempts, len(self.behaviour) - 1)
        what = self.behaviour[i]
        self.attempts += 1
        if what == "ok":
            self.spoken.append(text)
            return
        if what == "hang":
            await asyncio.sleep(3600)
            return
        raise RuntimeError("Speech synthesis failed: ResultReason.Canceled")


def guard(**kw):
    """A guard that says nothing to the screen, so the test output stays clean."""
    kw.setdefault("deadline_seconds", 0.2)
    kw.setdefault("announce", lambda *a, **k: None)
    return KeepTalking(**kw)


# ── 1. A line that fails fast is retried, once, and then let go ──────────────

def test_fast_failure_is_retried_once():
    robot = PretendRobot(["fail", "fail"])
    g = guard()
    got = run(g.say(lambda: robot.say("hola"), "hola"))
    check("a line that keeps failing gives up rather than raising", got is False)
    check("a fast failure is retried exactly once (2 attempts)",
          robot.attempts == 2, f"attempts={robot.attempts}")
    check("the lost line is counted", g.lines_lost == 1)


def test_retry_can_succeed():
    robot = PretendRobot(["fail", "ok"])
    g = guard()
    got = run(g.say(lambda: robot.say("hola"), "hola"))
    check("a line that works on the second go is spoken", got is True)
    check("...and it really was spoken", robot.spoken == ["hola"])
    check("...and nothing is counted as lost", g.lines_lost == 0)


# ── 2. A line that HANGS is not retried, because retrying doubles the dead air ─

def test_a_hang_is_not_retried():
    robot = PretendRobot(["hang"])
    g = guard(deadline_seconds=0.2)
    loop = asyncio.new_event_loop()
    started = loop.time()
    got = loop.run_until_complete(g.say(lambda: robot.say("hola"), "hola"))
    took = loop.time() - started
    check("a hung line gives up rather than raising", got is False)
    check("a hang is NOT retried — one attempt only",
          robot.attempts == 1, f"attempts={robot.attempts}")
    check("...so the silence is one deadline, not two",
          took < 0.2 * 1.9, f"took {took:.2f}s with a 0.2s deadline")


# ── 3. Stopping by hand still works ──────────────────────────────────────────

def test_cancellation_is_not_swallowed():
    """Ctrl-C and shutdown must go straight through the guard."""

    class Rude:
        async def say(self, text, lip_sync=True, language=None):
            raise asyncio.CancelledError()

    g = guard()
    try:
        run(g.say(lambda: Rude().say("hola"), "hola"))
    except asyncio.CancelledError:
        check("task cancellation is passed on, not swallowed", True)
        return
    except BaseException as exc:                                   # noqa: BLE001
        check("task cancellation is passed on, not swallowed", False,
              f"got {type(exc).__name__} instead")
        return
    check("task cancellation is passed on, not swallowed", False,
          "the guard returned normally")


# ── 4. Going quiet for several lines says so, once ───────────────────────────

def test_it_says_when_the_internet_has_gone():
    said = []
    g = KeepTalking(deadline_seconds=0.05, announce=said.append)
    robot = PretendRobot(["fail"])
    for _ in range(3):
        run(g.say(lambda: robot.say("hola"), "hola"))
    shouts = sum(1 for line in said if "SILENT FOR" in line)
    check("after three silent lines it names the internet as the cause",
          shouts == 1, f"said it {shouts} times")

    blob = "\n".join(said)
    check("...and says the game is still fine", "still going" in blob)
    check("...and says nothing needs restarting", "restarting" in blob)

    said.clear()
    run(g.say(lambda: PretendRobot(["ok"]).say("hola"), "hola"))
    run(g.say(lambda: PretendRobot(["fail"]).say("hola"), "hola"))
    check("a line getting through resets the count",
          g.consecutive_failures == 1, f"count={g.consecutive_failures}")


# ── 5. The deadline has to stay under the server's floor timeout ─────────────

def test_deadline_fits_inside_the_speaking_floor():
    """
    The server takes the speaking floor away from a robot that has said
    nothing for SPEAKING_TIMEOUT seconds. If this guard could still be
    politely waiting for Azure at that moment, the other robot would be told
    to go ahead and the two would talk over each other — the exact fault the
    floor exists to prevent.

    Checked across the two files rather than trusting a number copied into
    one of them, so raising one without the other cannot slip through.
    """
    try:
        text = io.open("chess_server.py", encoding="utf-8").read()
    except OSError:
        check("chess_server.py can be read for its floor timeout", False)
        return
    found = re.search(r"^SPEAKING_TIMEOUT\s*=\s*([0-9.]+)", text, re.M)
    if not found:
        check("SPEAKING_TIMEOUT found in chess_server.py", False)
        return
    floor = float(found.group(1))
    worst = chess_dropout.SPEECH_DEADLINE_SECONDS * (
        1 + chess_dropout.RETRIES_AFTER_A_FAST_FAILURE)
    check("worst-case wait stays inside the server's speaking floor",
          worst < floor, f"worst {worst:.0f}s vs floor {floor:.0f}s")


# ── 6. chess_player.py actually goes through the guard ───────────────────────

def player_source():
    return io.open("chess_player.py", encoding="utf-8").read()


def find_function(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


def calls_in(node):
    """Every call in this function, as readable text like 'controller.say'."""
    out = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            out.append(call_name(sub))
    return [c for c in out if c]


def call_name(call):
    f = call.func
    if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
        return f"{f.value.id}.{f.attr}"
    if isinstance(f, ast.Name):
        return f.id
    return None


def awaited_calls(node):
    """Only the calls this function AWAITS.

    The distinction is the whole point here. `controller.say(...)` still
    appears inside the lambda handed to the guard, and must — that lambda is
    how the guard makes the attempt. What must never happen again is awaiting
    it DIRECTLY, with nothing to catch a failure. A checker that cannot tell
    those two apart would refuse the correct file.
    """
    out = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Await) and isinstance(sub.value, ast.Call):
            out.append(call_name(sub.value))
    return [c for c in out if c]


def check_player_source(source, label="chess_player.py", record=True):
    """Returns a list of (name, ok) so the doctored copies below can reuse it."""
    found = []
    tree = ast.parse(source)

    for name in ("speak", "speak_and_report"):
        fn = find_function(tree, name)
        if fn is None:
            found.append((f"{label}: {name}() exists", False))
            continue
        calls = calls_in(fn)
        found.append((f"{label}: {name}() speaks through the guard",
                      "KEEP_TALKING.say" in calls))
        found.append((f"{label}: {name}() never awaits controller.say directly",
                      "controller.say" not in awaited_calls(fn)))

    fn = find_function(tree, "speak_and_report")
    released = False
    if fn is not None:
        for sub in ast.walk(fn):
            if isinstance(sub, ast.Try):
                for node in sub.finalbody:
                    for call in ast.walk(node):
                        if (isinstance(call, ast.Call)
                                and isinstance(call.func, ast.Name)
                                and call.func.id == "ask_server"
                                and any(isinstance(a, ast.Constant)
                                        and a.value == "done_speaking"
                                        for a in call.args)):
                            released = True
    found.append((f"{label}: the floor is handed back in a finally, "
                  f"so a failed line cannot silence the other robot", released))

    if record:
        for name, ok in found:
            check(name, ok)
    return found


def test_player_goes_through_the_guard():
    check_player_source(player_source())


# ── 7. Put each bug back and watch the checks go red ─────────────────────────

def test_the_checks_actually_catch_the_bugs():
    """Nothing on disk is touched — the source is doctored in memory only."""
    source = player_source()

    # Bug one: speak straight at the robot again, with no guard.
    broken = source.replace(
        """        return await KEEP_TALKING.say(
            lambda: controller.say(text, lip_sync=True, language=language),
            text)""",
        """        await controller.say(text, lip_sync=True, language=language)""")
    caught = [ok for name, ok in check_player_source(broken, record=False)
              if "through the guard" in name or "never awaits" in name]
    check("removing the guard makes the source checks fail",
          caught and not all(caught), f"results {caught}")

    # Bug two: stop handing the speaking floor back.
    broken = source.replace('ask_server(base_url, "done_speaking", timeout=3)',
                            "pass")
    caught = [ok for name, ok in check_player_source(broken, record=False)
              if "floor is handed back" in name]
    check("removing the floor hand-back makes its check fail",
          caught and not any(caught), f"results {caught}")

    # And the clean file still passes, so the checks are not simply broken.
    check("the real file passes every source check",
          all(ok for _, ok in check_player_source(source, record=False)))


# ── Run them all ─────────────────────────────────────────────────────────────

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if here:
        os.chdir(here)

    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()

    width = max(len(n) for n, _, _ in RESULTS)
    failures = 0
    for name, ok, detail in RESULTS:
        print(f"{'OK  ' if ok else 'FAIL'} {name:{width}s}"
              + (f"   {detail}" if detail and not ok else ""))
        if not ok:
            failures += 1

    print()
    if failures:
        print(f"{failures} of {len(RESULTS)} checks FAILED")
        return 1
    print(f"All {len(RESULTS)} checks passed. "
          "A lost sentence costs a pause, not the show.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
