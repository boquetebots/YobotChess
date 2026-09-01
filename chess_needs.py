#!/usr/bin/env python3
"""
chess_needs.py — checks the extra bits of Python are installed
================================================================================

Python on its own does not know how to play chess. It needs an add-on called
`chess`, and the server needs one called `flask`. These are free, they install
in one command, and you only ever do it once per machine.

Every program in this project asks this file to check first, so that a missing
add-on produces a sentence you can act on instead of a wall of red text.

You do not need to run this file yourself, but you can:

    python chess_needs.py
"""

import sys


# What each add-on is called when you install it, and what it is for.
INSTALL_NAMES = {
    "chess": ("chess", "knowing the rules of chess"),
    "flask": ("flask", "letting the robots talk to the server over wifi"),
    "dotenv": ("python-dotenv", "reading API keys out of the .env file"),

    # Only needed on a machine with a robot plugged into it. The chess
    # server and all the tests run without these.
    "serial": ("pyserial", "talking to the robot down the USB cable"),
    "azure.cognitiveservices.speech": (
        "azure-cognitiveservices-speech",
        "the robot's voice and the lip sync"),
}


def printable_text():
    """
    Make it safe to print a tick, an arrow or a box-drawing line on Windows.

    ── THE BUG THIS EXISTS FOR, 2026-08-14 ──────────────────────────────────

    Lester connected, centred his motors, set up Azure — and then died with:

        AZURE SPEECH WOULD NOT START: 'charmap' codec can't encode
        character '\\u2705' in position 0

    Azure was completely fine. `\\u2705` is the ✅ that ohbot_azure.py prints to
    say Azure had STARTED SUCCESSFULLY. The success message was what crashed.

    Windows Python does not use UTF-8 by default. When output goes to a real
    console window it usually copes, but when another program captures the
    output through a pipe — which is exactly what the Start buttons on the
    control page do — Python falls back to the old Windows codepage, and that
    codepage has no tick in it. So the robot worked perfectly when started by
    hand in its own window and died when started from the button. That is a
    horrible thing to debug, because the difference is invisible.

    This says "use UTF-8, and if a character still will not go, print a
    question mark rather than bringing the program down". A robot must never
    be stopped by a decoration in a message.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            # Very old Python, or a stream that cannot be reconfigured. Not
            # worth failing over — the worst case is the bug we started with.
            pass


def python_cmd():
    """
    What you type to run a Python program on THIS computer.

    Windows calls it `python`. The Raspberry Pi and the Mac call it `python3`
    — on those, plain `python` is either missing or is the ancient version 2.
    Getting this wrong is a confusing five minutes for someone who is not a
    programmer, so every message this project prints works it out rather than
    guessing.
    """
    return "python" if sys.platform.startswith("win") else "python3"


def _install_command(packages):
    """The right install line for whichever computer this is."""
    names = " ".join(packages)
    if sys.platform.startswith("win"):
        return f"py -m pip install {names}"
    return f"pip3 install {names}"


def require(*modules):
    """
    Check the listed add-ons are installed. If any are missing, explain what
    to type and stop, rather than letting Python throw a traceback.
    """
    missing = []
    for module in modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)

    if not missing:
        return

    packages = [INSTALL_NAMES.get(m, (m, ""))[0] for m in missing]

    print()
    print("=" * 70)
    print("  Something Python needs is not installed yet.")
    print("=" * 70)
    print()
    for module in missing:
        package, purpose = INSTALL_NAMES.get(module, (module, ""))
        print(f"  Missing: {package}")
        if purpose:
            print(f"           (this is the part that handles {purpose})")
    print()
    print("  To fix it, copy this line, paste it into the same window you")
    print("  just used, and press Enter:")
    print()
    print(f"      {_install_command(packages)}")
    print()
    print("  It downloads in a few seconds. You only have to do this once on")
    print("  this computer. Then run what you were running again.")
    print()
    print("=" * 70)
    print()
    raise SystemExit(1)


if __name__ == "__main__":
    require("chess", "flask", "dotenv")
    print("Everything this project needs is installed.")
