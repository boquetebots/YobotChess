#!/usr/bin/env python3
"""
check_stockfish.py — is the chess engine installed and working?
================================================================================

Run this BEFORE running chess_server.py. It answers one question in plain
English: can this computer play chess?

    python check_stockfish.py

It finds Stockfish, starts it, asks it for an opening move, and tells you
what happened. If anything is wrong it says what to do about it.

If you have several copies of Stockfish lying about, this also tells you
which one is being used, so there are no surprises later.
"""

import os
import sys

from chess_needs import require, python_cmd
require("chess")

import chess
import chess.engine

from chess_server import find_stockfish, _look_in


def explain_how_to_install():
    here = os.path.dirname(os.path.abspath(__file__))
    print("  Stockfish is a separate program. It is free. It is not")
    print("  something pip installs.")
    print()
    if sys.platform.startswith("win"):
        print("  ON WINDOWS:")
        print()
        print("    1. Go to  https://stockfishchess.org/download/")
        print("    2. Download the Windows version. You get a ZIP file.")
        print("    3. Open the ZIP. Inside is a folder with several files")
        print("       named like  stockfish-windows-x86-64-avx2.exe")
        print("    4. Drag ONE of them into this folder:")
        print()
        print(f"           {here}")
        print()
        print("       Pick the one with the PLAINEST name — the one that")
        print("       ends in just  x86-64.exe  with nothing after it. It is")
        print("       a touch slower than the others but it runs on every")
        print("       computer, and this demo does not need the speed.")
        print()
        print("    5. Run this check again.")
    elif sys.platform == "darwin":
        print("  ON A MAC, in a Terminal window:")
        print()
        print("      brew install stockfish")
    else:
        print("  ON THE RASPBERRY PI, in a Terminal window:")
        print()
        print("      sudo apt install stockfish")
    print()


def main():
    here = os.path.dirname(os.path.abspath(__file__))

    print()
    print("=" * 70)
    print("  Checking the chess engine")
    print("=" * 70)
    print()

    path = find_stockfish()

    if not path:
        print("  NOT FOUND — I could not find Stockfish anywhere.")
        print()
        explain_how_to_install()
        print("=" * 70)
        print()
        return 1

    print(f"  Found it:  {path}")

    # Mention any others, so a surprise later is impossible.
    others = []
    for folder in (here, os.path.join(os.path.expanduser("~"), "Downloads")):
        if os.path.isdir(folder):
            found = _look_in(folder, depth=3)
            if found and os.path.abspath(found) != os.path.abspath(path):
                others.append(found)
    if others:
        print()
        print("  (There are other copies on this computer. The one above is")
        print("   the one being used. The others are ignored.)")

    print()
    print("  Starting it up...")

    try:
        engine = chess.engine.SimpleEngine.popen_uci(path)
    except Exception as exc:
        print()
        print("  IT WOULD NOT START.")
        print()
        print(f"  The computer said: {exc}")
        print()
        print("  The most common cause on Windows is picking a version built")
        print("  for a newer processor than yours. Go back to the ZIP and try")
        print("  the file with the PLAINEST name — the one that is just")
        print("  x86-64 with nothing after it. See STOCKFISH_SETUP.md.")
        print()
        print("=" * 70)
        print()
        return 1

    try:
        name = engine.id.get("name", "Stockfish")
        print(f"  It says it is:  {name}")
        print()
        print("  Asking it for an opening move...")

        board = chess.Board()
        result = engine.play(board, chess.engine.Limit(time=1.0))

        from chess_speech import describe_move
        spoken = describe_move(board, result.move)

        print()
        print(f"  It played:      {board.san(result.move)}")
        print(f"  Robot would say: \"{spoken}\"")
        print()
        print("  ALL GOOD. The engine works.")
        print()
        print(f"  Next:  {python_cmd()} chess_server.py")
        print("         then open  http://localhost:8001/board  in a browser")
    finally:
        engine.quit()

    print()
    print("=" * 70)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
