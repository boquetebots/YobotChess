#!/usr/bin/env python3
"""
test_talking_turns.py — do the robots wait for each other to finish?
================================================================================

In the first full two-robot game the chess was right and the turn order was
right, but the two Yobots talked over each other. The server flipped the turn
the moment it handed out a move, so the second robot — which polls twice a
second — started its sentence while the first was still speaking.

The fix was a "speaking floor" in chess_server.py. This file proves it works,
using two pretend robots instead of two real ones.

    python test_talking_turns.py

**No robot, no Stockfish, no network, no Azure account.** It fakes the chess
engine, so it runs anywhere in about ten seconds. Silence means all four
checks passed.

WHAT IT CHECKS

  1. Two robots never speak at the same time.
  2. A robot that stops answering does not freeze the game forever.
  3. The gap between turns is actually observed.
  4. Both closing lines at the end of a game are said one after the other,
     not simultaneously.

Check 2 matters more than it looks. Holding the floor until a robot reports
back is the fix, but it introduces a new way to fail: a robot that crashes or
gets unplugged mid-sentence would hold the floor forever and stop the show
dead. That is worse than the overlap. So the floor expires on its own, and
this test unplugs a robot on purpose to prove it.
"""

import sys
import time
import threading

from chess_needs import require
require("chess")

import chess_server


# ── A pretend chess engine ──────────────────────────────────────────────────
# The real one is a separate program that has to be installed. We only care
# about the talking, not the chess, so a stand-in that returns any legal move
# lets this test run on a machine with no engine at all.

class FakeResult:
    """Stands in for what chess.engine returns from play()."""

    def __init__(self, move, info):
        self.move = move
        self.info = info


class FakeEngine:
    """
    Plays the first legal move it can see, instantly, and calls every
    position dead level.

    A flat evaluation is deliberate: it means nothing ever looks like a
    blunder and nobody ever resigns, so the game runs on predictably and
    this test only measures the thing it is about — who is talking, and
    when. The real Stockfish is exercised by test_commentary.py instead.
    """

    def _level(self):
        import chess
        import chess.engine
        return {"score": chess.engine.PovScore(chess.engine.Cp(0),
                                               chess.WHITE)}

    def play(self, board, limit, **kwargs):
        move = next(iter(board.legal_moves))
        return FakeResult(move, self._level())

    def analyse(self, board, limit, **kwargs):
        return self._level()

    def configure(self, options):
        pass

    def quit(self):
        pass


def fresh_game(gap=0.0):
    """A game object wired to the fake engine, ready to answer requests."""
    game = chess_server.ChessGame("(fake)", think_time=0.0, gap=gap,
                                  resign_at=0, detect_blunders=False)
    game.engine = FakeEngine()
    chess_server.game = game
    return game


def client(colour):
    """A test client for one robot's web server, without the network."""
    app = chess_server.build_app(colour)
    app.config["TESTING"] = True
    return app.test_client()


def ask(c, command="get_move"):
    return c.get(f"/move?command={command}").get_json()


# ── The checks ──────────────────────────────────────────────────────────────

failures = []


def check(name, condition, detail=""):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name}")
        if detail:
            print(f"        {detail}")
        failures.append(name)


# How many separate games the overlap check plays.
#
# ONE ROUND IS NOT ENOUGH, and this is the whole lesson of the bug this file
# was written for. The first version of the speaking floor had a real race in
# it — a few microseconds between the turn flipping and the floor being
# claimed, where the other robot could slip through. It failed on Michael's
# Windows PC and passed on Linux, because whether you hit the window depends
# on how the machine happens to schedule two threads.
#
# A timing bug that appears in one run out of five is not fixed when one run
# comes back clean. Several short rounds, each starting a fresh game, hit the
# handover far more often than one long one.
OVERLAP_ROUNDS = 5


def play_one_round(moves_wanted=12):
    """
    Two robots play a short game, each 'speaking' for a moment.

    Returns the list of overlaps seen and the order robots spoke in.
    """
    fresh_game(gap=0.0)
    clients = {"white": client("white"), "black": client("black")}

    talking = set()          # who is mid-sentence right now
    overlaps = []
    guard = threading.Lock()
    spoken = []
    stop = threading.Event()

    def robot(colour):
        c = clients[colour]
        while not stop.is_set():
            reply = ask(c)
            status = reply.get("status")

            if status == "wait":
                # No sleep here on purpose. Polling as hard as possible
                # maximises the chance of arriving at exactly the wrong
                # microsecond, which is what a race like this needs in order
                # to be caught rather than got away with.
                continue

            if status in ("finished", "game_over"):
                break

            if status == "success":
                with guard:
                    # THE HEART OF THE TEST. If anyone else is already
                    # talking at the moment this robot begins, that is
                    # exactly the fault we set out to fix.
                    if talking:
                        overlaps.append((colour, sorted(talking)))
                    talking.add(colour)
                    spoken.append(colour)

                time.sleep(0.02)          # stand-in for speaking out loud

                with guard:
                    talking.discard(colour)
                ask(c, "done_speaking")
                continue

            break

    threads = [threading.Thread(target=robot, args=(col,), daemon=True)
               for col in ("white", "black")]
    for t in threads:
        t.start()

    deadline = time.time() + 8
    while time.time() < deadline and len(spoken) < moves_wanted:
        time.sleep(0.02)
    stop.set()
    for t in threads:
        t.join(timeout=2)

    return overlaps, spoken


def test_no_overlap():
    """Several separate games, checking nobody ever speaks over anybody."""
    print()
    print(f"1. {OVERLAP_ROUNDS} games, nobody talks over anybody")
    print("-" * 70)

    all_overlaps = []
    all_spoken = []
    bad_order = []

    for round_number in range(1, OVERLAP_ROUNDS + 1):
        overlaps, spoken = play_one_round()
        all_overlaps.extend(overlaps)
        all_spoken.append(spoken)

        # White, black, white, black... a repeat means someone spoke twice in
        # a row, which would mean the board and the floor disagree.
        if not all(a != b for a, b in zip(spoken, spoken[1:])):
            bad_order.append((round_number, spoken))

        print(f"  round {round_number}: {len(spoken):2d} turns, "
              f"{len(overlaps)} overlap(s)")

    total_turns = sum(len(s) for s in all_spoken)

    check("nobody spoke while another robot was speaking",
          not all_overlaps,
          f"{len(all_overlaps)} overlap(s) across {OVERLAP_ROUNDS} games: "
          f"{all_overlaps[:3]}")

    check("both robots got turns in every round",
          all(len(set(s)) == 2 and len(s) >= 4 for s in all_spoken),
          f"turns per round: {[len(s) for s in all_spoken]}")

    check("turns alternated properly",
          not bad_order,
          f"out of order in round(s): {bad_order[:2]}")

    print(f"        ({total_turns} turns taken in total)")


def test_dead_robot_does_not_freeze_the_game():
    """
    A robot takes the floor and never reports back — unplugged, crashed, off
    the wifi. The other robot must eventually carry on regardless.
    """
    print()
    print("2. A robot that stops answering does not freeze the show")
    print("-" * 70)

    game = fresh_game(gap=0.0)
    white, black = client("white"), client("black")

    reply = ask(white)
    check("white got a move to speak", reply.get("status") == "success")

    # White now holds the floor and never sends done_speaking.
    check("black is told to wait while white talks",
          ask(black).get("status") == "wait")

    # Wind the clock back rather than waiting thirty real seconds.
    game.speaking_since = time.time() - (chess_server.SPEAKING_TIMEOUT + 1)

    reply = ask(black)
    check("black carries on once the floor times out",
          reply.get("status") == "success",
          f"black got {reply.get('status')!r} instead")


def test_gap_is_observed():
    """The pause between turns should actually happen."""
    print()
    print("3. The gap between turns is real")
    print("-" * 70)

    gap = 0.4
    fresh_game(gap=gap)
    white, black = client("white"), client("black")

    ask(white)                       # white takes the floor
    ask(white, "done_speaking")      # and finishes
    released_at = time.time()

    check("black must wait during the gap",
          ask(black).get("status") == "wait")

    # Poll until black is allowed to speak, then see how long that took.
    while time.time() - released_at < gap + 1:
        if ask(black).get("status") == "success":
            break
        time.sleep(0.02)
    waited = time.time() - released_at

    check("black waited roughly the gap before speaking",
          gap * 0.8 <= waited <= gap + 0.5,
          f"waited {waited:.2f}s, expected about {gap}s")


def test_both_endings_are_sequenced():
    """
    At the end both robots say a closing line. They must take turns over
    that too — it is the moment an audience is most likely to be listening.
    """
    print()
    print("4. The two closing lines do not land on top of each other")
    print("-" * 70)

    game = fresh_game(gap=0.0)
    white, black = client("white"), client("black")

    game.game_over = True

    first = ask(white)
    check("white gets a closing line",
          first.get("status") == "game_over" and first.get("speak"))

    check("black waits rather than speaking at the same time",
          ask(black).get("status") == "wait")

    ask(white, "done_speaking")

    second = ask(black)
    check("black gets its closing line once white has finished",
          second.get("status") == "game_over" and second.get("speak"),
          f"black got {second.get('status')!r}")


def main():
    print()
    print("=" * 70)
    print("  Do the robots wait for each other to finish speaking?")
    print("=" * 70)

    test_no_overlap()
    test_dead_robot_does_not_freeze_the_game()
    test_gap_is_observed()
    test_both_endings_are_sequenced()

    print()
    print("=" * 70)
    if failures:
        print(f"  {len(failures)} CHECK(S) FAILED:")
        for name in failures:
            print(f"      {name}")
        print()
        print("  The robots would talk over each other. Do not run the demo")
        print("  until this passes.")
        print("=" * 70)
        print()
        return 1

    print("  All checks passed. The robots take turns to speak.")
    print("=" * 70)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
