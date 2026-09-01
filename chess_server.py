#!/usr/bin/env python3
"""
chess_server.py — the brain of the chess demo
================================================================================

This is the program that actually plays the chess. It runs on ONE machine on
the wifi. It does not touch a robot and does not need one plugged in.

Its jobs:
  - run Stockfish (the chess engine) and get the moves
  - hold the one and only board, so both robots are playing the same game
  - write the sentence each robot will say
  - hand that finished sentence over when a robot asks for it

The robots do not think. They ask "is it my turn?", get back a sentence, and
say it. All the cleverness is here.

--------------------------------------------------------------------------------
THE FOUR FILES
--------------------------------------------------------------------------------

    chess_server.py       <- you are here. Stockfish, the board, the web bit.
    chess_commentary.py      decides what KIND of move it was
    chess_templates.py       the actual sentences  <- edit this one to change
                             what the robots say
    chess_speech.py          turns "Nf3" into "knight to f three"

--------------------------------------------------------------------------------
RUNNING IT
--------------------------------------------------------------------------------

    python chess_server.py

Then in a browser:

    http://localhost:8001/          white robot
    http://localhost:8002/          black robot
    http://localhost:8001/board     see the position as a picture
    http://localhost:8001/status    see the move list

To try it without any robots at all, use `test_commentary.py` instead — it
plays a whole game and prints every line to the screen.

--------------------------------------------------------------------------------
WHERE IS STOCKFISH?
--------------------------------------------------------------------------------

The server looks for it automatically. If it cannot find it, it says so
clearly and tells you how to install it. To point it at a specific copy, put
this in a `.env` file next to this script:

    STOCKFISH_PATH=C:\\path\\to\\stockfish.exe
"""

import argparse
import logging
import os
import shutil
import threading
import time

from chess_needs import require, printable_text
printable_text()          # see chess_needs.py — Windows, pipes and ticks
require("chess", "flask")

import chess
import chess.engine
from flask import Flask, jsonify

from chess_commentary import CommentaryWriter, BLUNDER_SWING

# Load a .env file if one is sitting next to this script. Optional — the
# server runs fine without it.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("chess")


WHITE_PORT = 8001
BLACK_PORT = 8002

# How long Stockfish is allowed to think, in seconds. Lower is snappier and
# plays slightly worse. Below about 0.1 it starts making silly moves.
THINK_TIME = 1.0


# ── How strong should the robots play? ───────────────────────────────────────
#
# THIS IS THE MOST IMPORTANT SETTING FOR THE SHOW, and it is not obvious why.
#
# At full strength, Stockfish is far beyond any human who has ever lived. Two
# copies of it playing each other produce a careful, balanced, largely drawn
# game. They do not blunder, they do not sacrifice, they trade evenly and
# shuffle for eighty moves. It is magnificent chess and dull theatre — a real
# self-play game measured here ran 95 moves with only 14% of them dramatic
# enough to be worth remarking on.
#
# Weaken them and the game comes alive: pieces hang, sacrifices land, someone
# actually gets checkmated, and it is over in half the time.
#
# The numbers are Elo ratings — the standard chess strength scale. For
# reference, a good club player is around 1600 and a grandmaster is 2500.
#
# ── There are TWO strength dials, not one ────────────────────────────────────
#
# The Elo dial (UCI_LimitStrength + UCI_Elo) is the good one: you ask for a
# rating and get a believable opponent of roughly that rating. But it STOPS AT
# 1320. That is Stockfish's floor and there is no arguing with it.
#
# 1320 is fine for two robots playing each other. It is far too strong for a
# guest at the clubhouse, who will lose every single game and stop wanting a
# turn. So for human play there is a second, cruder dial: Skill Level, 0 to
# 20. It works by making the engine deliberately overlook things, and it goes
# a long way below 1320 — level 0 plays somewhere around 800.
#
# Skill Level is rougher. It does not correspond to a rating, and its play is
# lopsided: mostly sensible, then suddenly a real howler. For an audience that
# is a feature, because a howler is the interesting bit.
#
# So each level below says WHICH dial to use as well as what to set it to.
STRENGTH_LEVELS = {
    # For a human opponent — these use the Skill Level dial.
    "gentle":   ("skill", 0),      # roughly 800. A beatable first game.
    "friendly": ("skill", 3),      # roughly 1000. Will punish a free piece.
    "easy":     ("skill", 6),      # roughly 1200. A decent casual player.
    # For robot against robot — these use the Elo dial.
    "beginner": ("elo", 1320),  # the weakest Elo allows. Blunders freely.
    "club":     ("elo", 1600),  # a decent local club player. Lively games.
    "strong":   ("elo", 2000),  # a strong tournament player. Fewer mistakes.
    "expert":   ("elo", 2400),  # near master. Games get quiet and long again.
    "max":      ("elo", None),  # no limit at all. Beautiful, and dull.
}

DEFAULT_STRENGTH = "club"

# What to drop to when a human is playing, unless told otherwise. A guest who
# never wins does not ask for a second game.
DEFAULT_HUMAN_STRENGTH = "friendly"

# Stop a game after this many moves so a demo cannot run past its slot.
# Counted in single moves, so 60 is 30 moves each. Set to 0 for no limit.
#
# NOTE: a hard cap is a blunt instrument. Measured across two famous games,
# the first HALF contained almost no drama at all (0-9% of moves), while the
# final quarter contained 50-66% of it. Openings are quiet in every game ever
# played. So chopping a game off at move 40 reliably keeps the dull part and
# throws away the payoff. Resignation, below, is the better tool. Treat this
# as a backstop for a fixed time slot, not as the main length control.
DEFAULT_MAX_MOVES = 0


# ── Resigning ────────────────────────────────────────────────────────────────
#
# Strong players do not play on when hopelessly lost — they resign. It is
# also far better theatre. A robot saying "I have seen enough, I resign" is
# an ending. A robot shuffling a lost king around for twenty more moves is an
# audience checking their phones.
#
# Measured in centipawns, chess's unit for "how far ahead is somebody". A
# pawn is 100. So -900 means a whole queen down with nothing to show for it.
DEFAULT_RESIGN_AT = -900

# How many of its own moves a robot must be hopeless for before it gives up.
# One bad evaluation can be a blip the engine takes back next move; three in
# a row is a lost game.
RESIGN_AFTER_MOVES = 3

# When a robot can see checkmate coming AGAINST it within this many moves,
# it plays on rather than resigning. A real checkmate is the best ending the
# demo can have and resigning a move short of it throws away the climax.
#
# THE NUMBER MATTERS. The first version had no number at all — ANY forced
# mate, however distant, stopped the robot resigning. In a lost endgame
# Stockfish spots mate from twenty moves away, which reset the "hopeless"
# count every time, so nobody ever resigned. A measured game ran 129 moves
# and sixteen minutes, grinding all the way to a mate that was visible
# almost from the start.
#
# Five is about two moves each plus a spare: close enough that an audience
# can see it coming, short enough that it is not a grind.
PLAY_OUT_MATE_WITHIN = 5


# ── Taking turns to SPEAK, not just to move ─────────────────────────────────
# Added 2026-08-13, after the first full two-robot game. The chess was right,
# the turn order was right, and the robots talked straight over each other.
#
# The cause: play_next_move() puts the move on the board and returns, so the
# turn flips the instant a move is handed out. The other robot polls twice a
# second, sees it is now its turn, and starts its own sentence while the first
# robot is still mid-way through speaking. Nothing anywhere tracked the fact
# that a robot was talking.
#
# So the server now holds a "floor". One robot has it at a time. Everyone else
# is told to wait, exactly as if it were not their turn yet. The robot with
# the floor says its line and then reports back with 'done_speaking'.
#
# THE TIMEOUT IS NOT OPTIONAL. If a robot crashes, gets unplugged, or loses
# wifi while holding the floor, nothing would ever release it and the game
# would stop dead in front of an audience — a far worse failure than the
# overlap it fixes. So the floor expires by itself.
#
# 30 seconds is deliberately generous. A move sentence is a few seconds of
# speech; Azure has to generate the audio first, and on a slow connection that
# can take a while. The timeout is there to catch a dead robot, not to cut off
# a slow one.
SPEAKING_TIMEOUT = 30.0

# A beat of silence after one robot finishes before the other may start.
# Without it the replies land instantly on top of each other, which is
# technically not overlapping but still sounds like an argument rather than a
# conversation. Just under a second reads as "considering the position".
DEFAULT_GAP = 0.8


def find_stockfish():
    """
    Track down the Stockfish program.

    Looks in this order, and stops at the first one that works:

      1. STOCKFISH_PATH in the .env file, if you set one
      2. This project folder — just drop the program in next to this script
         and it will be found. This is the easy option on Windows.
      3. Anywhere on the system PATH
      4. The usual places on the Pi and the Mac
      5. Your Downloads folder, in case you unzipped it there and left it

    Returns the path, or None if it cannot be found anywhere.
    """
    from_env = os.getenv("STOCKFISH_PATH")
    if from_env and os.path.exists(from_env):
        return from_env

    here = os.path.dirname(os.path.abspath(__file__))
    found = _look_in(here)
    if found:
        return found

    on_path = shutil.which("stockfish") or shutil.which("stockfish.exe")
    if on_path:
        return on_path

    for guess in (
        "/usr/games/stockfish",            # Raspberry Pi and Debian
        "/usr/bin/stockfish",
        "/usr/local/bin/stockfish",
        "/opt/homebrew/bin/stockfish",     # Mac, Apple silicon
        r"C:\Program Files\stockfish\stockfish.exe",
    ):
        if os.path.exists(guess):
            return guess

    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.isdir(downloads):
        found = _look_in(downloads, depth=3)
        if found:
            return found

    return None


# How long to spend working out the evaluation AFTER a move has been played.
# This is a second, much shorter look at the board, used only to see whether
# the move just made things better or worse. It does not need to be accurate
# enough to play chess with — just enough to spot a two-pawn swing — so it is
# kept short to avoid slowing the show down.
EVAL_TIME = 0.15


def swing_from(before, after, mover_colour):
    """
    How much did this move change the game, from the MOVER's point of view?

    `before` is the engine's opinion of the position with the mover about to
    play. `after` is its opinion once the move has been played. Both are
    python-chess PovScore objects, which know which side they are speaking
    for; asking each of them for the mover's view makes the two comparable.

    A negative answer means the mover made things worse for itself. That is
    a blunder.

    Returns None if either score is missing, in which case no blunder
    detection happens and the game plays on exactly as before.
    """
    if before is None or after is None:
        return None

    colour = chess.WHITE if mover_colour == "white" else chess.BLACK

    # mate_score turns "mate in 3" into a very large number so the two can be
    # subtracted. Without it, comparing a mate score to a normal one fails.
    before_cp = before.pov(colour).score(mate_score=10000)
    after_cp = after.pov(colour).score(mate_score=10000)
    if before_cp is None or after_cp is None:
        return None

    return after_cp - before_cp


class ResignWatcher:
    """
    Watches the score and decides when a robot should give up.

    Stockfish reports, after every move, how it thinks the game is going.
    This keeps an eye on that number for each side and says "resign" once a
    side has been hopelessly lost for several moves running.

    ONE IMPORTANT EXCEPTION: it never resigns into a forced checkmate. If the
    engine can see mate coming, the game should be allowed to finish properly
    — a real checkmate is the best ending the demo can possibly have, and
    resigning one move short of it would throw away the climax.
    """

    def __init__(self, resign_at=DEFAULT_RESIGN_AT, after=RESIGN_AFTER_MOVES):
        self.resign_at = resign_at
        self.after = after
        self.hopeless_streak = {"white": 0, "black": 0}

    def reset(self):
        self.hopeless_streak = {"white": 0, "black": 0}

    def record(self, colour, score):
        """
        Note how the game looked to `colour` on the move it just played.

        `score` is what python-chess hands back — None if the engine did not
        report one, in which case nobody ever resigns and the game plays out
        normally.
        """
        if score is None:
            return

        relative = score.relative

        if relative.is_mate():
            moves_away = relative.mate()

            # A positive number means WE are delivering mate. Nothing to
            # resign about — we are winning.
            if moves_away is None or moves_away > 0:
                self.hopeless_streak[colour] = 0
                return

            # A negative number means mate is coming FOR US.
            if abs(moves_away) <= PLAY_OUT_MATE_WITHIN:
                # Close enough to be the climax. Play it out.
                self.hopeless_streak[colour] = 0
            else:
                # Mate in fifteen is not a climax, it is a long walk to the
                # gallows. Count it as hopeless like any other lost position.
                self.hopeless_streak[colour] += 1
            return

        centipawns = relative.score()
        if centipawns is None:
            return

        if centipawns <= self.resign_at:
            self.hopeless_streak[colour] += 1
        else:
            self.hopeless_streak[colour] = 0

    def should_resign(self, colour):
        return self.hopeless_streak[colour] >= self.after


def parse_strength(value):
    """
    Turn what was typed after --strength into a setting the engine understands.

    Gives back a pair saying which dial to use and what to set it to, such as
    ("elo", 1600) or ("skill", 3). ("elo", None) means no limit at all.

    Returns False if what was typed makes no sense, and the caller then stops.
    """
    if value is None:
        return ("elo", None)

    text = str(value).strip().lower()

    if text in STRENGTH_LEVELS:
        return STRENGTH_LEVELS[text]

    try:
        number = int(text)
    except ValueError:
        print()
        print(f"  I do not understand --strength {value}")
        print()
        print("  Use one of these words:")
        for name, (dial, setting) in STRENGTH_LEVELS.items():
            if dial == "skill":
                note = f"skill level {setting} — for playing a person"
            elif setting:
                note = f"about {setting} Elo"
            else:
                note = "no limit, full strength"
            print(f"      {name:10s} {note}")
        print()
        print("  ...or a plain number between 1320 and 3190.")
        print()
        return False

    if not 1320 <= number <= 3190:
        print()
        print(f"  {number} is outside the range the Elo dial accepts.")
        print("  It only goes from 1320 (its weakest) to 3190 (its strongest).")
        print()
        print("  To play WEAKER than 1320 — which is what you want against a")
        print("  person — use one of these words instead:")
        for name, (dial, setting) in STRENGTH_LEVELS.items():
            if dial == "skill":
                print(f"      {name}")
        print()
        return False

    return ("elo", number)


def describe_strength(strength):
    """Say a strength setting in words, for printing on screen."""
    dial, setting = strength
    if dial == "skill":
        return f"skill level {setting} of 20"
    if setting is None:
        return "no limit, full strength"
    return f"about {setting} Elo"


def apply_strength(engine, strength):
    """
    Tell a running Stockfish how well to play.

    Lives here on its own so the server and test_commentary.py cannot drift
    apart. They used to each hold their own copy of these two lines, which
    meant a new setting had to be remembered in two places or the tests would
    quietly measure a different opponent from the one the audience sees.

    Two switches are needed for the Elo dial: UCI_LimitStrength turns the
    limiter on, and UCI_Elo says how strong. Setting the Elo on its own does
    nothing at all.

    The Skill Level dial needs the Elo limiter switched OFF. If both are on,
    Stockfish obeys the Elo one and ignores Skill Level — so asking for the
    gentlest setting would silently hand you a 1320 opponent, which is the
    exact opposite of what was wanted and would show up only as a guest never
    winning a game.

    If the engine will not take these settings — an old build, or a different
    engine altogether — say so and carry on at full strength rather than
    refusing to start. A dull game beats no game.
    """
    dial, setting = strength

    if dial == "elo" and setting is None:
        log.info("Playing at FULL strength (expect a long, quiet game)")
        return

    try:
        if dial == "skill":
            engine.configure({
                "UCI_LimitStrength": False,
                "Skill Level": setting,
            })
            log.info("Playing at skill level %d of 20", setting)
        else:
            engine.configure({
                "UCI_LimitStrength": True,
                "UCI_Elo": setting,
            })
            log.info("Playing at about %d Elo", setting)
    except Exception as exc:
        log.warning("This engine will not take a strength setting (%s).", exc)
        log.warning("Carrying on at full strength.")


def _look_in(folder, depth=1):
    """
    Find a file called something like "stockfish" inside a folder.

    The Windows download is a zip containing files with names like
    `stockfish-windows-x86-64-avx2.exe`, so we match anything that starts
    with "stockfish" rather than looking for an exact name.

    Where several are present, the plainest name wins — those are the builds
    that run on the widest range of computers.
    """
    candidates = []
    for root, dirs, files in os.walk(folder):
        # Do not wander too far down, or this gets slow.
        if root[len(folder):].count(os.sep) >= depth:
            dirs[:] = []
        for name in files:
            low = name.lower()
            if not low.startswith("stockfish"):
                continue
            if low.endswith((".zip", ".txt", ".md", ".nnue", ".exe.zip")):
                continue
            if os.name == "nt" and not low.endswith(".exe"):
                continue
            full = os.path.join(root, name)
            if os.access(full, os.X_OK) or os.name == "nt":
                candidates.append(full)

    if not candidates:
        return None

    # Shortest name first — "stockfish.exe" beats
    # "stockfish-windows-x86-64-avx512.exe", and the plain x86-64 build beats
    # the fancier ones, which crash on older processors.
    candidates.sort(key=lambda p: (len(os.path.basename(p)), p))
    return candidates[0]


class ChessGame:
    """Holds the one shared game. Both robots talk to this same object."""

    def __init__(self, stockfish_path, think_time=THINK_TIME,
                 strength=("elo", None), max_moves=DEFAULT_MAX_MOVES,
                 resign_at=DEFAULT_RESIGN_AT, detect_blunders=True,
                 gap=DEFAULT_GAP, human=None, polite=False, lang="en"):
        self.stockfish_path = stockfish_path
        self.think_time = think_time
        self.strength = strength        # ("elo", 1600) or ("skill", 3)
        self.max_moves = max_moves      # 0 means no limit
        self.detect_blunders = detect_blunders
        self.last_move_was_blunder = False
        self.board = chess.Board()
        self.engine = None
        self.moves_played = []          # in chess notation, for the status page
        self.spoken_lines = []          # what each robot actually said
        self.game_over = False
        self.stopped_early = False      # True if the move cap ended it
        self.resigned_by = None         # "white" or "black" if someone gave up
        self.ending_announced = set()   # which robots have said their last line
        self.writer = CommentaryWriter(polite=polite, lang=lang)

        # ── Is a person playing, and if so which colour? ──────────────────────
        # None means the usual thing: two robots, Stockfish plays both sides.
        # "white" or "black" means Stockfish does NOT play that side — it
        # waits for a move to arrive from the board on the display, sent by
        # whoever is sitting in front of it.
        #
        # The human is deliberately kept OUT of the speaking floor. A person
        # cannot send done_speaking, and anything that claims the floor must
        # be able to release it — see the note on the newgame command below,
        # which is the bug this rule was learned from. So a human move never
        # takes the floor, never holds it, and never blocks a robot.
        #
        # Nor does the human get a spoken line. Michael's decision, and it is
        # the right one: the robot reacting to what you did on ITS next turn
        # is far better theatre than the robot reading your move back to you.
        # That reaction already works — the "punish" category fires off
        # last_move_was_blunder, and it does not care whether the blunder came
        # from Stockfish or from a person.
        self.human = human
        self.resign_watcher = (ResignWatcher(resign_at) if resign_at else None)
        # Two robots, one board — take turns.
        #
        # An RLock, not a plain Lock, and that matters. The /move handler
        # takes this lock around the whole decision of "may this robot speak,
        # and if so claim the floor", and play_next_move() and reset() take it
        # again inside that. A plain Lock would deadlock against itself; an
        # RLock lets the same thread hold it more than once.
        self.lock = threading.RLock()

        # ── Who is talking right now ─────────────────────────────────────────
        # See the note by SPEAKING_TIMEOUT. speaking holds "white" or "black"
        # while that robot has the floor, or None if nobody has it.
        # quiet_until is the moment the next robot is allowed to begin, which
        # is a short gap AFTER the last one finished.
        self.gap = gap
        self.speaking = None
        self.speaking_since = 0.0
        self.quiet_until = 0.0

        # ── The clocks, and who is winning ───────────────────────────────────
        # Purely for the audience display. Nothing here affects the game: no
        # robot ever loses on time and the evaluation is never acted upon.
        # If this whole block were deleted the chess would be identical.
        #
        # clock holds the seconds each robot has USED so far. A robot is
        # charged while it is thinking about its move AND while it is saying
        # it — which is what an audience sees as "its go".
        self.clock = {"white": 0.0, "black": 0.0}
        self._clock_side = None     # who the clock is running for right now
        self._clock_since = 0.0     # when it started running for them
        self.started_at = None      # when the first move was played

        # Stockfish's opinion of the position, in hundredths of a pawn, ALWAYS
        # from White's point of view: positive means White is better. The
        # engine works this out anyway while checking for blunders, so keeping
        # it costs nothing.
        self.eval_cp = 0
        self.last_move_uci = None   # so the board can highlight the last move

        # ── The opening line, waiting to be collected ────────────────────────
        # When a new game is started from the control page rather than by a
        # robot, there is nobody in the room to say the opening sentence at
        # that moment. So it is left here for the first robot that asks.
        #
        # This matters more than a lost sentence. The old "start" command
        # handed the sentence straight back to whoever asked AND claimed the
        # speaking floor for them — which is right when a robot asks, and
        # wrong when a web page does. The page cannot speak and never sends
        # done_speaking, so the floor stayed held by a robot that was not
        # talking. See the newgame command below.
        self.opening_for = None

    # ── The clocks ───────────────────────────────────────────────────────────

    def _settle_clock(self):
        """
        Add the time since we last looked to whichever robot's go it was,
        then work out whose go it is now.

        Called after anything that could change whose go it is, and also on
        every status request. Calling it more often than necessary is
        harmless — it only ever moves elapsed time from the wall clock onto
        the robot that was actually active for it.
        """
        now = time.time()
        if self._clock_side is not None and self._clock_since:
            self.clock[self._clock_side] += now - self._clock_since

        if self.game_over:
            # Both clocks stop at the end. Nobody is charged for the silence
            # after the last word.
            self._clock_side = None
        else:
            # Whoever is talking owns the moment; otherwise it belongs to
            # whoever has to move next. Note that these differ: the turn flips
            # the instant a move is played, while the robot is still speaking.
            self._clock_side = self.speaking or self.whose_turn()
        self._clock_since = now

    # ── The speaking floor ───────────────────────────────────────────────────

    def take_floor(self, colour):
        """This robot is about to speak. Everyone else waits."""
        self.speaking = colour
        self.speaking_since = time.time()
        self._settle_clock()

    def release_floor(self, colour):
        """
        This robot has finished speaking. Start the gap before the next one.

        Only the robot that actually holds the floor can release it, so a
        late message from the other robot cannot cut a sentence short.
        """
        if self.speaking == colour:
            self.speaking = None
            self.speaking_since = 0.0
            self.quiet_until = time.time() + self.gap
            self._settle_clock()
            return True
        return False

    def floor_is_busy(self, colour):
        """
        Should this robot hold off? True if the other one is still talking,
        or if we are in the gap just after it finished.

        This is also where a stalled floor gets cleaned up: if a robot took
        the floor and never reported back — crashed, unplugged, lost wifi —
        the floor expires so the game carries on rather than freezing in
        front of an audience.
        """
        now = time.time()

        if self.speaking is not None:
            if now - self.speaking_since > SPEAKING_TIMEOUT:
                # Nobody came back. Assume that robot is gone.
                print(f"  [{self.speaking} has been speaking for over "
                      f"{SPEAKING_TIMEOUT:.0f}s and has not reported back. "
                      f"Carrying on without it.]")
                self.speaking = None
                self.speaking_since = 0.0
                self.quiet_until = now + self.gap
            elif self.speaking != colour:
                return True
            else:
                # It already has the floor — let it through rather than
                # deadlocking against itself.
                return False

        return now < self.quiet_until

    # ── Engine ───────────────────────────────────────────────────────────────

    def start_engine(self):
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            log.info("Stockfish ready: %s", self.stockfish_path)
        except Exception as exc:
            log.error("Could not start Stockfish at %s — %s", self.stockfish_path, exc)
            return False

        self._set_strength()
        return True

    def _set_strength(self):
        """Tell Stockfish how well to play. See apply_strength below."""
        apply_strength(self.engine, self.strength)

    def _hit_move_limit(self):
        return self.max_moves and len(self.moves_played) >= self.max_moves

    def stop_engine(self):
        if self.engine:
            self.engine.quit()
            log.info("Stockfish closed")

    # ── Playing ──────────────────────────────────────────────────────────────

    def whose_turn(self):
        return "white" if self.board.turn == chess.WHITE else "black"

    def play_next_move(self):
        """
        Ask Stockfish for a move, write the commentary, then play it.

        IMPORTANT: the commentary is written BEFORE the move is played. Both
        chess_speech and chess_commentary need to see the board as it was, so
        they can tell what piece got captured. Once the move is on the board
        that information is gone.
        """
        with self.lock:
            if self.game_over:
                return None

            colour = self.whose_turn()

            try:
                # Asking for the score at the same time as the move costs
                # nothing — the engine has already worked it out during the
                # same search. Asking separately would double the thinking
                # time for no benefit.
                result = self.engine.play(
                    self.board,
                    chess.engine.Limit(time=self.think_time),
                    info=chess.engine.INFO_SCORE,
                )
            except Exception as exc:
                log.error("Stockfish failed to produce a move: %s", exc)
                return None

            move = result.move
            score_before = (result.info or {}).get("score")

            if self.resign_watcher is not None:
                self.resign_watcher.record(colour, score_before)

            # ── how much does this move change things? ────────────────────
            # Look at the board once more after the move, briefly, to see
            # whether it improved the position or wrecked it. This is what
            # turns "a knight moved" into "that was a terrible mistake".
            swing = None
            if self.detect_blunders:
                self.board.push(move)
                try:
                    info = self.engine.analyse(
                        self.board, chess.engine.Limit(time=EVAL_TIME)
                    )
                    swing = swing_from(score_before, info.get("score"), colour)
                    self._remember_eval(info.get("score"))
                except Exception as exc:
                    log.debug("Could not evaluate the new position: %s", exc)
                finally:
                    self.board.pop()
            else:
                # No blunder detection means no second look at the position,
                # so the display falls back to the engine's opinion from
                # BEFORE the move. Slightly stale, never wrong-headed.
                self._remember_eval(score_before)

            # ── commentary first, while the old position is still on the board
            spoken, san, facts = self.writer.comment_on(
                self.board, move, swing, self.last_move_was_blunder
            )
            self.last_move_was_blunder = bool(facts["is_blunder"])

            # ── now play it
            self.board.push(move)
            self.moves_played.append(san)
            self.spoken_lines.append(spoken)
            self.last_move_uci = move.uci()
            if self.started_at is None:
                self.started_at = time.time()

            if self.board.is_game_over():
                self.game_over = True
            elif self._hit_move_limit():
                # Out of time rather than out of moves. The robots will say
                # something graceful about it instead of falling silent.
                self.game_over = True
                self.stopped_early = True
                log.info("Move limit of %d reached — stopping here", self.max_moves)

            log.info("%-5s  %-8s  %s", colour, san, spoken)

            # The turn has just flipped, so hand the clock over.
            self._settle_clock()

            return {
                "colour": colour,
                "move_san": san,
                "move_uci": move.uci(),
                "move_number": len(self.moves_played),
                "spoken": spoken,
                "facts": facts,
                "fen": self.board.fen(),
                "game_over": self.game_over,
                "result": self.result() if self.game_over else None,
            }

    # ── A person's move ──────────────────────────────────────────────────────

    def human_may_move(self):
        """True if the game is waiting for the person sitting at the board."""
        return (self.human is not None
                and not self.game_over
                and self.whose_turn() == self.human)

    def robot_colour(self):
        """
        Which side the robot plays. The opposite of the human, or white in a
        normal two-robot game where both sides are robots anyway.
        """
        if self.human == "white":
            return "black"
        return "white"

    def legal_moves(self):
        """
        Every legal move in the position, written like "e2e4".

        Sent out with the rest of the status so the board on the display can
        light up where a tapped piece may go. Doing it here rather than in the
        page means the page never needs to know the rules of chess — no
        castling, no en passant, no working out whether a move leaves the king
        in check. Those are the rules people get wrong, and the engine has
        them right already.

        There are rarely more than about forty, so this costs nothing.
        """
        with self.lock:
            if self.game_over:
                return []
            return [m.uci() for m in self.board.legal_moves]

    def play_human_move(self, text):
        """
        Put a person's move on the board.

        `text` is a move like "e2e4", or "e7e8q" for a pawn promoting to a
        queen. Gives back a dict describing what happened, or a dict with
        "error" in it explaining what was wrong in words a person can read.

        NOTHING IS SPOKEN HERE. The robot says nothing about your move at the
        time you make it; it reacts on its own next turn instead. That is a
        deliberate choice and it is also why this method is so much simpler
        than play_next_move — no commentary is written, no sentence is
        returned, and the speaking floor is never claimed. The one piece of
        it used here is the quiet gap, started at the end, so the robot does
        not answer the instant you let go of a piece.

        The evaluation IS still done, and that is the important part. It is
        what sets last_move_was_blunder, which is what makes the robot's next
        line a punishing one when you give something away.
        """
        with self.lock:
            if self.human is None:
                return {"error": "Nobody is playing by hand in this game."}

            if self.game_over:
                return {"error": "The game has already finished."}

            colour = self.whose_turn()
            if colour != self.human:
                return {"error": "It is not your turn yet.", "wait": True}

            # ── is it a real move, and is it legal? ───────────────────────────
            # Both questions are asked by the chess library, not by us. A move
            # that leaves your own king in check is not legal, and no amount
            # of checking squares by hand gets that right.
            try:
                move = chess.Move.from_uci(str(text).strip().lower())
            except Exception:
                return {"error": f"'{text}' is not a move I understand."}

            if move not in self.board.legal_moves:
                # A promotion typed without saying which piece is the common
                # one, and worth its own message.
                without = chess.Move(move.from_square, move.to_square)
                if move.promotion is None and any(
                        m.from_square == move.from_square
                        and m.to_square == move.to_square
                        and m.promotion is not None
                        for m in self.board.legal_moves):
                    return {"error": "That pawn is promoting — say which "
                                     "piece it becomes."}
                del without
                return {"error": "That is not a legal move."}

            # ── how much did that change things? ──────────────────────────────
            # Same two looks the robots get: the engine's opinion before the
            # move and after it. The difference is what turns "a bishop moved"
            # into "you have just given me a bishop".
            swing = None
            if self.detect_blunders and self.engine is not None:
                try:
                    before = self.engine.analyse(
                        self.board, chess.engine.Limit(time=EVAL_TIME)
                    ).get("score")
                    self.board.push(move)
                    try:
                        after = self.engine.analyse(
                            self.board, chess.engine.Limit(time=EVAL_TIME)
                        ).get("score")
                        swing = swing_from(before, after, colour)
                        self._remember_eval(after)
                    finally:
                        self.board.pop()
                except Exception as exc:
                    log.debug("Could not evaluate the human's move: %s", exc)

            # This is the line that makes the robot pounce. It is read by
            # comment_on() on the robot's next turn.
            self.last_move_was_blunder = swing is not None and swing <= BLUNDER_SWING

            san = self.board.san(move)
            self.board.push(move)
            self.moves_played.append(san)
            # Kept in step with moves_played on purpose, so the two lists stay
            # the same length and anything reading them side by side still
            # lines up. The human simply said nothing.
            self.spoken_lines.append("")
            self.last_move_uci = move.uci()
            if self.started_at is None:
                self.started_at = time.time()

            if self.board.is_game_over():
                self.game_over = True
            elif self._hit_move_limit():
                self.game_over = True
                self.stopped_early = True

            log.info("%-5s  %-8s  (played by hand%s)", colour, san,
                     ", BLUNDER" if self.last_move_was_blunder else "")

            # -- Give the guest a moment before the robot answers -------------
            # Added 2026-09-01. The robot replied the instant a person let go
            # of a piece, which reads as a machine rather than a thinker.
            #
            # The human never takes the speaking floor (see the note in
            # __init__), so release_floor is never called for their move and
            # the quiet gap that spaces two robots apart never started. This
            # line starts it by hand. The robot's next poll is told to wait,
            # exactly as it would be while the other robot is talking, so no
            # new machinery is involved. Nothing changes in a robot-against-
            # robot game: this method is never reached in one.
            self.quiet_until = time.time() + self.gap

            self._settle_clock()

            return {
                "colour": colour,
                "move_san": san,
                "move_uci": move.uci(),
                "move_number": len(self.moves_played),
                "blunder": self.last_move_was_blunder,
                "fen": self.board.fen(),
                "game_over": self.game_over,
                "result": self.result() if self.game_over else None,
            }

    def _remember_eval(self, score):
        """
        Store who is winning, for the bar on the display.

        `score` is what python-chess hands back, which is written from the
        point of view of whoever is to move. `.white()` turns it round so it
        always means the same thing: positive is good for White. Without that
        the bar would swap sides every single move.

        "Mate in 3" is not a number of pawns, so it is pinned to the end of
        the bar rather than converted.
        """
        if score is None:
            return
        try:
            centipawns = score.white().score(mate_score=10000)
        except Exception:
            return
        if centipawns is not None:
            self.eval_cp = int(centipawns)

    def resign(self, colour):
        """The given robot gives up. Ends the game."""
        with self.lock:
            self.resigned_by = colour
            self.game_over = True
            log.info("%s resigns", colour)
            self._settle_clock()

    def should_resign(self, colour):
        """Is this robot hopelessly lost and ready to give up?"""
        if self.resign_watcher is None or self.game_over:
            return False
        return self.resign_watcher.should_resign(colour)

    def result(self):
        """
        How the game ended, in chess's own notation.

        "*" means it was still going when we stopped it — the move cap ran
        out. The commentary writer turns that into an "out of time" line.
        """
        if self.resigned_by == "white":
            return "0-1"
        if self.resigned_by == "black":
            return "1-0"
        if self.stopped_early:
            return "*"
        return self.board.result()

    def reset(self):
        with self.lock:
            self.board = chess.Board()
            self.moves_played = []
            self.spoken_lines = []
            self.game_over = False
            self.stopped_early = False
            self.resigned_by = None
            self.last_move_was_blunder = False
            self.ending_announced = set()
            self.writer.reset()
            if self.resign_watcher is not None:
                self.resign_watcher.reset()
            # Nobody is talking in a brand new game. Without this, a restart
            # part-way through a sentence would leave the floor held by a
            # robot that is no longer saying anything.
            self.speaking = None
            self.speaking_since = 0.0
            self.quiet_until = 0.0
            # Fresh clocks and a level bar for the new game.
            self.clock = {"white": 0.0, "black": 0.0}
            self._clock_side = None
            self._clock_since = 0.0
            self.started_at = None
            self.eval_cp = 0
            self.last_move_uci = None
            self.opening_for = None
            log.info("New game")


# One game object, shared by both web servers.
game = None


def build_app(colour):
    """Make the little web server that one robot talks to."""
    app = Flask(f"chess_{colour}")

    @app.route("/")
    def home():
        return jsonify({
            "robot": colour,
            "try_these": {
                "start a new game": "/move?command=start",
                "get my move": "/move?command=get_move",
                "see the board": "/board",
                "see the moves": "/status",
            },
        })

    @app.route("/move")
    def move():
        from flask import request
        command = request.args.get("command", "get_move")

        # ── A robot has been started on the side a person is playing ─────────
        #
        # Nothing here is broken; somebody has started the wrong program. But
        # the failure it would otherwise cause is a nasty one to diagnose: the
        # robot would take the human's turn, so the guest would tap a piece
        # and find the move already made, or find nothing they tapped was ever
        # accepted. It would look like the touchscreen was faulty.
        #
        # So say plainly what has happened, and refuse.
        #
        # "newgame" is deliberately exempt. That one does not come from a
        # robot at all — it is the New game button on the control page, which
        # has always been sent to the white server whichever robot is playing.
        # Refusing it here would mean the button silently stopped working the
        # moment a guest sat down at the white side, which is a rotten way to
        # find out about a rule.
        if (game.human is not None and colour == game.human
                and command != "newgame"):
            return jsonify({
                "status": "error",
                "message": (f"A person is playing {colour} in this game, so "
                            f"there is no {colour} robot. Start the robot with "
                            f"--colour {game.robot_colour()} instead."),
                "speak": None,
            }), 409

        # ── start or restart ─────────────────────────────────────────────────
        if command in ("start", "reset"):
            with game.lock:
                game.reset()
                game.take_floor(colour)
                return jsonify({
                    "status": "success",
                    "speak": game.writer.game_start_line(colour),
                })

        # ── start a game from the control page, not from a robot ─────────────
        # Same as "start" with one crucial difference: it does NOT hand the
        # opening sentence back, and does NOT claim the speaking floor.
        #
        # "start" does both, which is exactly right when a robot asks — it is
        # about to say that sentence. It is exactly wrong when a web page
        # asks. A page cannot speak, so the sentence would be thrown away and
        # the floor would sit held by a robot that was not talking. Nothing
        # would ever move again. That is not theoretical: it is what happened
        # the first time the New game button was pressed on real hardware.
        #
        # Instead the sentence is left for the first robot that asks.
        if command == "newgame":
            with game.lock:
                game.reset()
                # Left for the ROBOT, which is not always white. When a person
                # is playing white they move first, so handing the opening
                # line to white would throw it away — a page cannot speak, and
                # neither can a guest. The show would open in silence with
                # everyone waiting for the visitor to work out what to do.
                #
                # Giving it to the robot instead means the robot welcomes you
                # first and then waits, which is a much better way in.
                game.opening_for = game.robot_colour()
                return jsonify({"status": "success", "speak": None})

        # ── "I have finished talking" ────────────────────────────────────────
        # The robot sends this the moment the audio stops. Until it arrives
        # (or the floor times out) the other robot is told to wait, which is
        # what stops the two of them speaking over each other.
        if command == "done_speaking":
            with game.lock:
                released = game.release_floor(colour)
            return jsonify({"status": "success", "released": released,
                            "speak": None})

        if command not in ("get_move", "get_next_move", "move"):
            return jsonify({
                "status": "error",
                "message": f"I do not understand the command '{command}'.",
                "speak": None,
            }), 400

        # ── ONE ROBOT AT A TIME FROM HERE DOWN ───────────────────────────────
        # Everything below decides whether this robot may speak, and then
        # claims the floor. Those two things MUST happen as one indivisible
        # step, which is what this lock is for.
        #
        # The first version did not hold a lock here, and the robots still
        # occasionally spoke over each other. The window was tiny but real:
        # play_next_move() flips whose turn it is and then returns, and only
        # after that did the floor get claimed. A poll from the other robot
        # arriving in between saw a turn that had already flipped and a floor
        # that was not yet held, so it sailed through both checks and started
        # talking.
        #
        # It showed up on Michael's Windows PC and not on Linux, which is the
        # signature of a thread-timing bug: whether you see it depends on how
        # the machine happens to schedule the two requests. Never conclude
        # such a thing is fixed because one machine stopped showing it.
        #
        # game.lock is an RLock, so play_next_move() and reset() can take it
        # again further down without deadlocking against this.
        with game.lock:
            # ── is the other robot still talking? ─────────────────────────────
            # This comes BEFORE everything else on purpose, including the game
            # ending. Both robots say a closing line, and without this check
            # they would say them simultaneously — the one moment of the whole
            # demo where an audience is most likely to be paying attention.
            if game.floor_is_busy(colour):
                return jsonify({"status": "wait", "speak": None,
                                "eval_cp": game.eval_cp})

            # ── the game has finished ─────────────────────────────────────────
            if game.game_over:
                if colour in game.ending_announced:
                    # Already said its piece. Tell the robot to stop asking.
                    return jsonify({"status": "finished", "speak": None})
                game.ending_announced.add(colour)
                game.take_floor(colour)
                return jsonify({
                    "status": "game_over",
                    "result": game.result(),
                    "stopped_early": game.stopped_early,
                    "resigned_by": game.resigned_by,
                    "speak": game.writer.game_end_line(
                        game.result(), colour, game.resigned_by),
                    "eval_cp": game.eval_cp,
                })

            # ── an opening line left by the control page ──────────────────────
            # Collected before anything else this robot might do, so the game
            # opens with a greeting rather than straight into a move.
            if game.opening_for == colour:
                game.opening_for = None
                game.take_floor(colour)
                return jsonify({
                    "status": "success",
                    "speak": game.writer.game_start_line(colour),
                })

            # ── not this robot's turn ─────────────────────────────────────────
            if game.whose_turn() != colour:
                return jsonify({"status": "wait", "speak": None,
                                "eval_cp": game.eval_cp})

            # ── hopelessly lost? give up rather than grind on ─────────────────
            if game.should_resign(colour):
                game.resign(colour)
                game.ending_announced.add(colour)
                game.take_floor(colour)
                return jsonify({
                    "status": "game_over",
                    "result": game.result(),
                    "resigned_by": colour,
                    "speak": game.writer.game_end_line(
                        game.result(), colour, colour),
                })

            # ── this robot's turn ─────────────────────────────────────────────
            played = game.play_next_move()
            if played is None:
                return jsonify({
                    "status": "error",
                    "message": "The chess engine did not answer.",
                    "speak": "I am having trouble with that one. Give me a "
                             "moment.",
                }), 500

            # Still inside the lock, so the turn cannot have flipped out from
            # under us between playing the move and claiming the floor.
            game.take_floor(colour)

            return jsonify({
                "status": "success",
                "speak": played["spoken"],
                "move": played["move_san"],
                "move_number": played["move_number"],
                "game_over": played["game_over"],
                # Who is winning, for the robot's eye colour. Positive is
                # good for WHITE, the same as everywhere else — the robot
                # flips it to its own side itself. See eval_from_my_side()
                # in chess_animation.py.
                "eval_cp": game.eval_cp,
            })

    @app.route("/human_move", methods=["POST", "GET"])
    def human_move():
        """
        A person's move, sent from the board on the display.

        Takes a move like e2e4, or e7e8q for a pawn becoming a queen, either
        as ?move=e2e4 or as JSON. Answers with what happened, or with a plain
        English reason why not.

        This deliberately does NOT go through the speaking floor. A person
        cannot send done_speaking, and the rule learned the hard way on this
        project is that anything which claims the floor must be able to
        release it. So the human never claims it, and a robot part-way
        through a sentence is not interrupted by a guest tapping the board —
        the move simply lands and the robot picks it up when it has finished.
        """
        from flask import request

        text = request.args.get("move")
        if not text and request.is_json:
            text = (request.get_json(silent=True) or {}).get("move")
        if not text and request.form:
            text = request.form.get("move")

        if not text:
            return jsonify({
                "status": "error",
                "message": "No move was sent. Use ?move=e2e4",
            }), 400

        outcome = game.play_human_move(text)

        if "error" in outcome:
            # "It is not your turn yet" is not really an error — it happens
            # whenever a tap lands while the robot is still thinking. 409
            # rather than 400 so the page can tell the difference between
            # "try again in a moment" and "that move was wrong".
            return jsonify({
                "status": "wait" if outcome.get("wait") else "error",
                "message": outcome["error"],
            }), 409 if outcome.get("wait") else 400

        return jsonify({"status": "success", **outcome})

    @app.route("/status")
    def status():
        # Everything the audience display needs, in one request. It is read
        # twice a second by chess_show.py, so it does no work beyond reading
        # values that already exist — no engine calls, no thinking.
        with game.lock:
            game._settle_clock()
            return jsonify({
                "turn": game.whose_turn(),
                "game_over": game.game_over,
                "result": game.result() if game.game_over else None,
                "resigned_by": game.resigned_by,
                "move_count": len(game.moves_played),
                "moves": game.moves_played,
                "spoken": game.spoken_lines,
                "fen": game.board.fen(),
                "last_move": game.last_move_uci,
                "speaking": game.speaking,
                "in_check": game.board.is_check(),
                # Seconds each robot has used. Whole numbers are plenty for
                # something read from the back of a room.
                "clock": {c: round(t, 1) for c, t in game.clock.items()},
                # Positive means White is ahead, in hundredths of a pawn.
                "eval_cp": game.eval_cp,
                "started": game.started_at is not None,

                # ── For the board on the display ─────────────────────────────
                # human is None in a normal two-robot game, and the page then
                # shows a board that cannot be touched. Otherwise it is the
                # colour the guest is playing.
                "human": game.human,
                "robot_colour": game.robot_colour(),
                "your_move": game.human_may_move(),
                # Only sent when it is actually the person's turn, because
                # this is the one part of the status that is not simply
                # reading a value that already exists — and it is read twice a
                # second all game long.
                "legal_moves": game.legal_moves() if game.human_may_move() else [],
                "polite": game.writer.polite,
                # Which language the robots are speaking in this game. The
                # ROBOT that actually talks (chess_player.py) reads this once,
                # at connect time, so it knows which Azure voice to switch to
                # — the text itself is already the right language by the time
                # it gets there, because game.writer picked its sentence bank
                # from this same setting at startup.
                "lang": game.writer.lang,
            })

    @app.route("/language/<lang>", methods=["POST", "GET"])
    def set_language(lang):
        """
        Change the language the robots are speaking, without restarting.

        Added 2026-08-31. Language used to be a start-up-only setting like
        Strength and Pause, which is how a whole game got played with Espanol
        showing on the control page and English coming out of the robot: the
        dropdown was changed, the server was not restarted, and nothing said
        so. The control page now calls this the moment the dropdown moves, so
        the page and the voice cannot disagree.

        Works as GET as well as POST on purpose, so it can be checked from a
        browser or with curl:

            curl http://127.0.0.1:5000/language/es

        The answer always says which language is ACTUALLY in use now, which
        is not necessarily the one that was asked for — an unrecognised name
        falls back to English rather than taking the show down.
        """
        with game.lock:
            in_use = game.writer.set_language(lang)
        print(f"  Language changed to {'Spanish' if in_use == 'es' else 'English'}.")
        return jsonify({"status": "success", "lang": in_use,
                        "asked_for": lang})

    @app.route("/board")
    def board():
        """The position drawn as text, so you can check it in a browser."""
        return (
            "<pre style='font-size:28px;line-height:1.1'>"
            + str(game.board.unicode(invert_color=True, empty_square="."))
            + "</pre>"
            + f"<p style='font-family:sans-serif'>{game.whose_turn()} to move &mdash; "
            + f"move {len(game.moves_played)}</p>"
        )

    return app


def main():
    global game

    parser = argparse.ArgumentParser(
        description="Chess server for the Yobot demo",
        epilog=(
            "Strength: "
            + ", ".join(f"{k} ({v})" if v else f"{k} (no limit)"
                        for k, v in STRENGTH_LEVELS.items())
            + ". Weaker play makes a livelier, shorter, more decisive game — "
              "which is usually what you want in front of an audience."
        ),
    )
    parser.add_argument("--think", type=float, default=THINK_TIME,
                        help="seconds Stockfish may think per move (default 1.0)")
    parser.add_argument("--strength", default=DEFAULT_STRENGTH,
                        help=f"how well the robots play (default: {DEFAULT_STRENGTH}). "
                             "A name from the list below, or an Elo number.")
    parser.add_argument("--max-moves", type=int, default=DEFAULT_MAX_MOVES,
                        help="hard stop after this many moves, counted singly "
                             "so 60 is 30 each (default: no limit). A backstop "
                             "for a fixed slot — resigning is the better way "
                             "to keep games short.")
    parser.add_argument("--resign-at", type=int, default=DEFAULT_RESIGN_AT,
                        help="give up when this far behind, in hundredths of "
                             f"a pawn (default {DEFAULT_RESIGN_AT}, about a "
                             "queen down). 0 turns resigning off.")
    parser.add_argument("--gap", type=float, default=DEFAULT_GAP,
                        help="seconds of silence between one robot finishing "
                             f"and the other starting (default {DEFAULT_GAP}). "
                             "Raise it if they feel rushed, lower it if the "
                             "game drags. 0 means reply the instant the other "
                             "stops, which still does not overlap.")
    parser.add_argument("--stockfish", default=None,
                        help="path to the Stockfish program, if it cannot be found")
    parser.add_argument("--human", choices=("white", "black"), default=None,
                        help="a PERSON plays this colour, on the board on the "
                             "display. Stockfish does not play that side. "
                             "Leave this out for the usual robot v robot game.")
    parser.add_argument("--polite", action="store_true",
                        help="leave out the cheekiest lines. Worth using when "
                             "a guest is playing, because those lines were "
                             "written for one robot to say to another.")
    parser.add_argument("--lang", default="en", choices=("en", "es"),
                        help="which language the robots speak: en (English) "
                             "or es (Spanish). Changes the commentary AND "
                             "tells the robots which Azure voice to switch "
                             "to when they connect. Default en.")
    args = parser.parse_args()

    strength = parse_strength(args.strength)
    if strength is False:
        return 1

    # A guest playing at club level loses every game and does not ask for
    # another. So when a person is playing and no strength was chosen, drop to
    # something beatable rather than silently using the robot-v-robot default.
    if args.human and args.strength == DEFAULT_STRENGTH:
        args.strength = DEFAULT_HUMAN_STRENGTH
        strength = parse_strength(args.strength)

    path = args.stockfish or find_stockfish()
    if not path:
        print()
        print("Could not find Stockfish, the chess engine.")
        print()
        print("  On the Raspberry Pi or a Mac with Homebrew:")
        print("      sudo apt install stockfish        (Pi)")
        print("      brew install stockfish            (Mac)")
        print()
        print("  On Windows, download it from stockfishchess.org, then either")
        print("  put the folder on your PATH or add this line to a .env file")
        print("  next to this script:")
        print()
        print("      STOCKFISH_PATH=C:\\path\\to\\stockfish.exe")
        print()
        return 1

    game = ChessGame(path, think_time=args.think, strength=strength,
                     max_moves=args.max_moves, resign_at=args.resign_at,
                     gap=args.gap, human=args.human, polite=args.polite,
                     lang=args.lang)
    if not game.start_engine():
        return 1

    white_app = build_app("white")
    black_app = build_app("black")

    for app, port in ((white_app, WHITE_PORT), (black_app, BLACK_PORT)):
        threading.Thread(
            target=lambda a=app, p=port: a.run(
                host="0.0.0.0", port=p, debug=False, threaded=True
            ),
            daemon=True,
        ).start()

    print()
    print("Chess server running.")
    if args.human:
        print(f"  Playing       a PERSON plays {args.human}, "
              f"the robot plays {game.robot_colour()}")
        print(f"  Start it with python chess_player.py "
              f"--colour {game.robot_colour()}")
    else:
        print("  Playing       robot against robot")
    print(f"  Strength      {args.strength}  ({describe_strength(strength)})")
    print(f"  Lines         {'polite' if args.polite else 'full, including the cheeky ones'}")
    print(f"  Language      {'Spanish' if args.lang == 'es' else 'English'}")
    print(f"  Move limit    "
          + (f"{args.max_moves} moves" if args.max_moves else "none"))
    print(f"  Resigns       "
          + (f"when about {abs(args.resign_at)/100:.0f} pawns behind"
             if args.resign_at else "never"))
    print(f"  Think time    {args.think} seconds per move")
    print()
    print(f"  White robot   http://localhost:{WHITE_PORT}/move?command=start")
    print(f"  Black robot   http://localhost:{BLACK_PORT}/move?command=start")
    print(f"  The board     http://localhost:{WHITE_PORT}/board")
    print(f"  Move list     http://localhost:{WHITE_PORT}/status")
    print()
    print("Press Ctrl-C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping.")
    finally:
        game.stop_engine()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
