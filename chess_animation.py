#!/usr/bin/env python3
"""
chess_animation.py — how the robots MOVE while they play
================================================================================

The robots could already talk with their mouths moving. Nothing else about
them moved at all: no head turns, no looking at the board, no looking up at
the audience. That is the difference between a talking head and a performer.

This file is the movement, and nothing else. It knows nothing about chess,
nothing about the server, and nothing about what is being said. It has two
jobs:

  WAITING    — the other side is thinking. Head down at the board, eyes and
               head wandering, the occasional blink, mouth shut.

  ANNOUNCING — this robot is speaking. Head up towards the audience, gentle
               movement so it does not look like a broken puppet, blinks,
               and the mouth left strictly alone for the lip sync to drive.

--------------------------------------------------------------------------------
IF YOU WANT TO CHANGE HOW THEY MOVE, EVERYTHING IS AT THE TOP OF THIS FILE
--------------------------------------------------------------------------------

Same idea as `chess_templates.py` being the one place to change what they
*say*. All the numbers live in one block below, each with a line saying what
it does. Change a number, run the test, watch the robot. You do not need to
read the rest of the file.

The numbers mean the same thing as the sliders in the Sequence Builder:

    HEADTURN / EYETURN :  3 = right, 5 = straight ahead, 7 = left
    HEADNOD  / EYETILT :  3 = down,  5 = level,          7 = up
    LIDBLINK           :  0 = shut,  10 = wide open

--------------------------------------------------------------------------------
SEEING IT WITHOUT A ROBOT
--------------------------------------------------------------------------------

    python test_animation.py

That runs a pretend robot and checks every rule below. No robot, no Azure, no
chess engine, no add-ons to install.

With a real robot plugged in, and no chess server needed:

    python chess_player.py --animate-demo

--------------------------------------------------------------------------------
TWO RULES THIS FILE MUST NEVER BREAK
--------------------------------------------------------------------------------

1. **It must never touch the lips while the robot is speaking.** The lip sync
   drives TOPLIP and BOTTOMLIP from Azure's mouth shapes, thirty-odd times a
   second. Anything else sending lip commands at the same time is two programs
   fighting over one motor, and what you get is a mouth that stutters and
   words you cannot read. The mouth is set closed once when the waiting pose
   starts, and never touched again.

2. **It must never stop the show.** A motor that fails, a cable pulled, a
   number typed wrong — none of that may bring down a robot in front of an
   audience. Every movement is wrapped so that a failure prints a line and
   carries on. Animation is decoration; the game is the point.
"""

import asyncio
import random


# ── Which motor is which ─────────────────────────────────────────────────────
#
# These numbers come from yobot_core.py in OhbotPi2. They are repeated here as
# plain numbers ON PURPOSE, so that this file — and its test — can run on a
# computer with no robot code, no pyserial and no OhbotPi2 folder. That is what
# makes `python test_animation.py` work anywhere.
#
# If the OhbotPi2 numbers are ever renumbered, `check_motor_numbers()` at the
# bottom of this file will say so out loud rather than the robot quietly
# nodding when you asked it to blink.

HEADNOD   = 0
HEADTURN  = 1
EYETURN   = 2
LIDBLINK  = 3
TOPLIP    = 4
BOTTOMLIP = 5
EYETILT   = 6


# =============================================================================
#  THE NUMBERS — change these
# =============================================================================

# ── WAITING: the other side is thinking ──────────────────────────────────────

WAIT_HEAD_NOD = 3.0          # head held down, looking at the board
WAIT_TURN_MIN = 3.0          # how far right the head wanders
WAIT_TURN_MAX = 7.0          # how far left the head wanders
WAIT_TILT_MIN = 3.0          # how far down the EYES look
WAIT_TILT_MAX = 7.0          # how far up the eyes look
WAIT_LIPS = 5.0              # mouth closed. 5 is "lips just touching"

WAIT_EYE_SPEED = 10          # eyes are quick — they dart
WAIT_HEAD_SPEED = 2          # the head is slow — it drifts
WAIT_EYE_LEAD = 0.5          # seconds the eyes get there before the head does
WAIT_PAUSE_MIN = 0.0         # how long it holds still between looks
WAIT_PAUSE_MAX = 2.0

# ── ANNOUNCING: this robot is talking ────────────────────────────────────────

ANNOUNCE_HEAD_NOD = 7.0      # head up, off the board
ANNOUNCE_FACE = 6.0          # where "the audience" is. --face overrides it.
ANNOUNCE_SWAY = 0.5          # how far it drifts either side of those two
ANNOUNCE_SPEED = 2           # slow, so the drift is a drift and not a twitch
ANNOUNCE_HOLD_MIN = 0.4      # seconds between drifts
ANNOUNCE_HOLD_MAX = 0.9
ANNOUNCE_EYES = 5.0          # eyes straight ahead while talking to people

# ── BLINKING: the same in both states ────────────────────────────────────────

BLINK_OPEN = 10.0            # lids up
BLINK_SHUT = 2.0             # how far they close. Not 0 — a soft blink.
BLINK_HOLD = 0.15            # seconds the lids stay down
BLINK_GAP_MIN = 2.0          # random gap between blinks, in seconds
BLINK_GAP_MAX = 6.0

# ── EYE COLOUR: who is winning ───────────────────────────────────────────────
#
# Each colour is (red, green, blue), each channel 0 to 10 — the same scale as
# everything else here. `ohbot.baseColour()` scales them up to 0-255 itself.
#
# While a robot is WAITING, its eyes show how the game is going FOR IT: green
# when it is ahead, amber when the game is level, red when it is losing. The
# number comes from Stockfish, which is already working it out for the bar on
# the display, so this costs nothing and never disagrees with the screen.
#
# While a robot is ANNOUNCING, the eyes go blue. Whatever the position, the
# robot that is talking is the one to look at.
#
# A robot with no LEDs fitted simply ignores all of this. The commands are
# plain serial messages and the board discards them, so there is nothing to
# turn off and nothing to configure — fit the LEDs and they light up.

COLOUR_WINNING  = (0, 10, 0)     # well ahead
COLOUR_LEVEL    = (10, 5, 0)     # nothing in it — amber
COLOUR_LOSING   = (10, 0, 0)     # well behind
COLOUR_ANNOUNCE = (0, 3, 10)     # this robot is speaking — blue
COLOUR_OFF      = (0, 0, 0)      # not playing, or the program has stopped

# How far ahead counts as FULLY green, in hundredths of a pawn. 500 is five
# pawns, or roughly a rook. Anything between level and this is blended, so the
# colour drifts with the game rather than flicking between three states.
#
# Lower it and the eyes react to small advantages; raise it and only a
# thumping lead shows. 200 is what chess_commentary.py calls a blunder.
EVAL_FULL = 500

# Whose point of view. "mine" means each robot shows how ITS OWN game is
# going, so the two of them are usually opposite colours — one green, one red.
# "white" means both show the game from White's side, exactly like the bar on
# the display, so the two robots always match.
EVAL_POINT_OF_VIEW = "mine"

# ── Where everything goes when the robot stops ───────────────────────────────

NEUTRAL_SPEED = 3


def eval_colour(centipawns):
    """
    Turn "how far ahead am I" into an eye colour.

    `centipawns` is from this robot's own point of view: positive means it is
    winning. None means nobody has worked it out yet — before the first move,
    or if the server did not say — and that gets the level colour rather than
    a guess.

    Blended rather than three fixed steps, so a game slipping away shows as a
    colour slipping away.
    """
    if centipawns is None:
        return COLOUR_LEVEL

    # Clamp to the full-colour point, then work out how far along we are.
    reach = max(-EVAL_FULL, min(EVAL_FULL, centipawns)) / float(EVAL_FULL)
    towards = COLOUR_WINNING if reach >= 0 else COLOUR_LOSING
    amount = abs(reach)

    return tuple(
        round(level + (end - level) * amount, 2)
        for level, end in zip(COLOUR_LEVEL, towards)
    )


def eval_from_my_side(centipawns, colour):
    """
    Turn the server's number into this robot's own point of view.

    The server reports the evaluation the way the display wants it: positive
    is good for White, always, whoever is to move. That is right for a bar on
    a screen and wrong for a robot, because a robot playing Black wants to
    know whether *it* is winning.

    This is the one place that flips it, and `EVAL_POINT_OF_VIEW` above
    decides whether it flips at all.
    """
    if centipawns is None:
        return None
    if EVAL_POINT_OF_VIEW == "white":
        return centipawns
    return centipawns if colour == "white" else -centipawns


# =============================================================================
#  The animator
# =============================================================================

class Animator:
    """
    Moves one robot. Hand it the same controller `chess_player.py` speaks
    through, then tell it which state the robot is in.

        anim = Animator(controller)
        await anim.waiting()        # head down, wandering
        await anim.announcing()     # head up, talking
        await anim.stop()           # everything back to centre, tasks ended

    Calling `waiting()` twice in a row is harmless. Switching states always
    stops the previous state's movement before starting the new one — see
    `_switch_to()`, and the note about why that matters.
    """

    def __init__(self, controller, face=ANNOUNCE_FACE, enabled=True):
        self.controller = controller

        # Where this robot looks when it addresses the room. It is a setting
        # rather than a constant because Lester and Goldie will not be sitting
        # at the same angle to the audience, and the fix has to be a number
        # you can change on the day rather than a code edit.
        #
        # None means "use the default". argparse hands over None when a
        # caller did not care, and taking that literally would point the head
        # at nowhere.
        self.face = ANNOUNCE_FACE if face is None else face

        # --no-animation turns the whole thing into a no-op. Worth having: if
        # the movement ever misbehaves five minutes before a show, there is a
        # switch that gets the talking robots back without touching any code.
        self.enabled = enabled

        self.state = "off"
        self._stop = None            # asyncio.Event for the running state
        self._tasks = []
        self._complained = False     # only moan about a broken motor once

        # How the game is going for THIS robot, in hundredths of a pawn.
        # None until the server says. See set_eval().
        self.eval_cp = None
        self._eye_colour = None      # what the LEDs were last actually told

    # ── who is winning ───────────────────────────────────────────────────────

    async def set_eval(self, centipawns):
        """
        Tell the robot how the game is going FOR IT. Positive means winning.

        Called every time the server answers, which is twice a second. The
        colour only actually goes down the cable when it CHANGES — see
        `_set_eyes()`. That matters: the LEDs share the one serial cable with
        every motor, and repainting them twice a second all game would be a
        few thousand pointless messages competing with the lip sync.

        Does nothing visible while the robot is announcing. The eyes are blue
        for as long as it is talking, whatever the position does in the
        meantime, and the new colour appears when it goes back to waiting.
        """
        self.eval_cp = centipawns
        if self.state == "waiting":
            await self._set_eyes(eval_colour(centipawns))

    async def _set_eyes(self, colour):
        """
        Send a colour, but only if it is not the colour already showing.

        Wrapped like every movement is: a robot with no LEDs, or with a loose
        LED cable, must cost the colour and nothing else.
        """
        if not self.enabled or colour == self._eye_colour:
            return
        self._eye_colour = colour
        try:
            await self.controller.set_eye_color(*colour)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if not self._complained:
                self._complained = True
                print(f"  (the eye colour did not take: {exc} — carrying on. "
                      f"The game is unaffected.)")

    # ── the two states ───────────────────────────────────────────────────────

    async def waiting(self):
        """Head down at the board, eyes and head wandering, mouth shut."""
        if not self.enabled or self.state == "waiting":
            return
        await self._switch_to("waiting")

        # Eyes back to how the game is actually going. If this robot has just
        # finished speaking they are blue, and they should not stay blue.
        await self._set_eyes(eval_colour(self.eval_cp))

        # Set the fixed poses once, on the way in. Not inside a loop: a
        # command repeated twice a second fills the motor queue for no gain,
        # and the mouth in particular must be left alone afterwards.
        await self._move(HEADNOD, WAIT_HEAD_NOD, WAIT_HEAD_SPEED)
        await self._move(TOPLIP, WAIT_LIPS, WAIT_EYE_SPEED)
        await self._move(BOTTOMLIP, WAIT_LIPS, WAIT_EYE_SPEED)

        self._start(self._wander, self._blink)

    async def announcing(self):
        """Head up towards the audience, drifting gently, mouth left free."""
        if not self.enabled or self.state == "announcing":
            return
        await self._switch_to("announcing")

        # Blue for as long as it is talking. Whatever the position, the robot
        # that is speaking is the one to look at — and a robot that announces
        # its own checkmate through red eyes is telling the audience two
        # different things at once.
        await self._set_eyes(COLOUR_ANNOUNCE)

        # Eyes back to straight ahead. They were wandering a moment ago, and a
        # robot that addresses the room while looking at the floor is worse
        # than one that does not move at all.
        await self._move(EYETURN, ANNOUNCE_EYES, WAIT_EYE_SPEED)
        await self._move(EYETILT, ANNOUNCE_EYES, WAIT_EYE_SPEED)

        # NOTE: no lip commands here, and none in _address() or _blink().
        # The lip sync owns the mouth from now until the audio stops. See
        # rule 1 at the top of this file.

        self._start(self._address, self._blink)

    async def stop(self):
        """Stop moving and put everything back to neutral."""
        await self._switch_to("off")
        if not self.enabled:
            return
        for motor in (HEADNOD, HEADTURN, EYETURN, EYETILT):
            await self._move(motor, 5.0, NEUTRAL_SPEED)
        await self._move(LIDBLINK, BLINK_OPEN, NEUTRAL_SPEED)
        await self._move(TOPLIP, WAIT_LIPS, NEUTRAL_SPEED)
        await self._move(BOTTOMLIP, WAIT_LIPS, NEUTRAL_SPEED)
        await self._set_eyes(COLOUR_OFF)

    # ── the movements themselves ─────────────────────────────────────────────

    async def _wander(self, stop):
        """
        Waiting. Eyes dart somewhere, the head catches up, eyes recentre.

        THE EYES GOING FIRST IS THE WHOLE TRICK. Move the head on its own and
        it reads as a machine swivelling. Let the eyes arrive first and the
        head follow, and it reads as something that noticed a thing and then
        turned to look at it. It is the same three lines either way. This is
        lifted straight from the Greeter's idle animation in ohbot_chat.py,
        which has had a lot more hours in front of people than this has.

        The head nod stays where `waiting()` put it — down at the board. Only
        the EYES tilt, so the robot can glance up at its opponent without
        lifting its head.
        """
        while not stop.is_set():
            look_at = random.uniform(WAIT_TURN_MIN, WAIT_TURN_MAX)
            tilt_to = random.uniform(WAIT_TILT_MIN, WAIT_TILT_MAX)

            await self._move(EYETURN, look_at, WAIT_EYE_SPEED)
            await self._move(EYETILT, tilt_to, WAIT_EYE_SPEED)

            if await self._sleep(stop, WAIT_EYE_LEAD):
                return

            await self._move(HEADTURN, look_at, WAIT_HEAD_SPEED)
            await self._move(EYETURN, 5.0, WAIT_EYE_SPEED)

            if await self._sleep(stop, random.uniform(WAIT_PAUSE_MIN,
                                                      WAIT_PAUSE_MAX)):
                return

    async def _address(self, stop):
        """
        Announcing. Head up and out, then drifting a little either side.

        A head pinned at exactly one number with a mouth flapping under it
        looks broken — the audience reads it as a fault rather than as a
        style. The drift is deliberately small: half a slider step, slowly.
        It should be the sort of movement you notice only when it stops.
        """
        await self._move(HEADNOD, ANNOUNCE_HEAD_NOD, ANNOUNCE_SPEED)
        await self._move(HEADTURN, self.face, ANNOUNCE_SPEED)

        while not stop.is_set():
            if await self._sleep(stop, random.uniform(ANNOUNCE_HOLD_MIN,
                                                      ANNOUNCE_HOLD_MAX)):
                return
            nod = ANNOUNCE_HEAD_NOD + random.uniform(-ANNOUNCE_SWAY,
                                                     ANNOUNCE_SWAY)
            turn = self.face + random.uniform(-ANNOUNCE_SWAY, ANNOUNCE_SWAY)
            await self._move(HEADNOD, nod, ANNOUNCE_SPEED)
            await self._move(HEADTURN, turn, ANNOUNCE_SPEED)

    async def _blink(self, stop):
        """
        Blinks, on their own timer.

        Separate from everything else on purpose. Tie blinking to the head
        movement and it becomes a rhythm — blink, turn, blink, turn — and a
        rhythm is the one thing that makes a robot look mechanical. On its own
        clock it never quite lines up with anything, which is correct.
        """
        while not stop.is_set():
            if await self._sleep(stop, random.uniform(BLINK_GAP_MIN,
                                                      BLINK_GAP_MAX)):
                return
            await self._move(LIDBLINK, BLINK_SHUT, WAIT_EYE_SPEED)
            if await self._sleep(stop, BLINK_HOLD):
                # Even on the way out, open the lids. A robot left standing
                # with its eyes half shut looks switched off.
                await self._move(LIDBLINK, BLINK_OPEN, WAIT_EYE_SPEED)
                return
            await self._move(LIDBLINK, BLINK_OPEN, WAIT_EYE_SPEED)

    # ── the plumbing ─────────────────────────────────────────────────────────

    def _start(self, *loops):
        """Set the new state's movements running in the background."""
        self._stop = asyncio.Event()
        self._tasks = [asyncio.create_task(loop(self._stop)) for loop in loops]

    async def _switch_to(self, new_state):
        """
        Stop whatever was running, then record the new state.

        THIS HAS TO ACTUALLY WAIT. Setting the stop flag and moving on would
        leave the old state's loops alive for up to a second — long enough to
        send one more command. The result is the two states fighting: the
        waiting loop pulls the head down to the board in the middle of the
        announcement, then the announce loop pulls it back up. On hardware
        that is a twitch nobody can explain by reading either loop, because
        neither one is wrong. `test_animation.py` checks for exactly this.
        """
        if self._stop is not None:
            self._stop.set()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        self._stop = None
        self.state = new_state

    async def _sleep(self, stop, seconds):
        """
        Wait, but wake up early if the state changed. Returns True if we are
        being stopped, so every caller can `return` on the spot.
        """
        try:
            await asyncio.wait_for(stop.wait(), timeout=max(0.0, seconds))
            return True
        except asyncio.TimeoutError:
            return False

    async def _move(self, motor, position, speed):
        """
        Move one motor, and never let it bring the show down.

        See rule 2 at the top. If the cable is pulled mid-game the chess and
        the speech can carry on perfectly well without the head moving, and
        that is a much better failure than a robot that stops. It says so
        once, then stays quiet — a broken motor printing twice a second would
        bury every other message in the log.
        """
        try:
            await self.controller.move(motor, position, speed)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if not self._complained:
                self._complained = True
                print(f"  (a motor did not respond: {exc} — carrying on "
                      f"without animation. The game is unaffected.)")


# ── a safety check, not a feature ────────────────────────────────────────────

def check_motor_numbers():
    """
    Confirm the motor numbers above still match OhbotPi2's.

    They are copied rather than imported so this file works with no robot
    code present (see the note by the constants). Copied numbers go stale
    silently, and stale ones here would mean asking for a blink and getting a
    nod — a fault that looks like bad animation rather than a wrong number.

    Returns a list of problems. Empty list means all is well. Also returns an
    empty list when OhbotPi2 cannot be found at all, which is the normal case
    on a machine with no robot and is not a problem.
    """
    try:
        import chess_ohbot
        chess_ohbot.add_to_path()
        import ohbot_pi as ohbot
    except Exception:
        return []

    problems = []
    for name, mine in (("HEADNOD", HEADNOD), ("HEADTURN", HEADTURN),
                       ("EYETURN", EYETURN), ("LIDBLINK", LIDBLINK),
                       ("TOPLIP", TOPLIP), ("BOTTOMLIP", BOTTOMLIP),
                       ("EYETILT", EYETILT)):
        theirs = getattr(ohbot, name, None)
        if theirs is not None and theirs != mine:
            problems.append(
                f"{name} is {mine} in chess_animation.py but {theirs} in "
                f"OhbotPi2. Change it here to {theirs}.")
    return problems


if __name__ == "__main__":
    print()
    print("chess_animation.py — the movement settings")
    print()
    print(f"  Waiting:   head nod {WAIT_HEAD_NOD}, head turns "
          f"{WAIT_TURN_MIN} to {WAIT_TURN_MAX}, lips {WAIT_LIPS}")
    print(f"  Announcing: head nod {ANNOUNCE_HEAD_NOD}, head turn "
          f"{ANNOUNCE_FACE}, drifting {ANNOUNCE_SWAY} either side")
    print(f"  Blinks:    lids {BLINK_OPEN} down to {BLINK_SHUT}, every "
          f"{BLINK_GAP_MIN} to {BLINK_GAP_MAX} seconds")
    print()
    print("  Eye colour, as red/green/blue out of 10:")
    full = f"{EVAL_FULL / 100:.0f}"
    for label, colour in (
            (f"winning by {full} pawns or more", eval_colour(EVAL_FULL)),
            ("winning by 2 pawns", eval_colour(200)),
            ("level", eval_colour(0)),
            ("losing by 2 pawns", eval_colour(-200)),
            (f"losing by {full} pawns or more", eval_colour(-EVAL_FULL)),
            ("announcing a move", COLOUR_ANNOUNCE)):
        print(f"    {label:<30s} {colour}")
    print()
    print(f"  Shown from: {'this robot' if EVAL_POINT_OF_VIEW == 'mine' else 'White'}"
          f"'s point of view")
    print()
    trouble = check_motor_numbers()
    if trouble:
        for line in trouble:
            print(f"  PROBLEM: {line}")
    else:
        print("  Motor numbers check out.")
    print()
    print("  To test the movement itself:  python test_animation.py")
    print()
