#!/usr/bin/env python3
"""
test_animation.py — does the movement do what it is supposed to?
================================================================================

    python test_animation.py

**No robot, no Azure, no chess engine, no add-ons.** It drives a pretend robot
that writes down every command it is given, then reads the list back. It takes
about twenty seconds. Silence means every check passed.

WHAT IT CHECKS

  1. The waiting pose is what it should be — head down at the board, mouth
     closed, head wandering only within the range it was given.
  2. The eyes get there before the head does. That is what makes it look like
     something noticed a thing rather than a machine swivelling.
  3. Blinks happen, close only as far as they were told to, and always open
     again — including when the state changes mid-blink.
  4. **The announce state never sends a single lip command.** This is the
     important one. The lip sync drives the mouth thirty times a second from
     Azure's mouth shapes, and anything else touching those two motors at the
     same time is two programs fighting over one servo. What you get is a
     stuttering mouth and words you cannot lip-read.
  5. Switching state really stops the old movement, rather than leaving it
     running for another second. Two states both driving the head is a twitch
     you cannot explain by reading either one of them, because neither is
     wrong on its own.
  6. A motor that fails does not stop the show.
  7. --no-animation really moves nothing at all.
  8. The motor numbers still match OhbotPi2's.

HOW THE TIMING IS TESTED WITHOUT WAITING ALL DAY

A blink every two to six seconds means watching for half a minute to see a
handful of them. So the timing checks turn those numbers down for a moment
(`faster()` below) and turn them back afterwards. The numbers you actually
ship are checked separately, for being sensible rather than for being fast —
see `check_the_settings_make_sense`.
"""

import ast
import asyncio
import contextlib
import io
import sys
import time

import chess_animation
from chess_animation import (Animator, HEADNOD, HEADTURN, EYETURN, EYETILT,
                             LIDBLINK, TOPLIP, BOTTOMLIP)


MOTOR_NAMES = {HEADNOD: "HEADNOD", HEADTURN: "HEADTURN", EYETURN: "EYETURN",
               EYETILT: "EYETILT", LIDBLINK: "LIDBLINK", TOPLIP: "TOPLIP",
               BOTTOMLIP: "BOTTOMLIP"}


# ── the pretend robot ────────────────────────────────────────────────────────

class FakeRobot:
    """
    Stands in for AsyncOhbotController. Writes down every command instead of
    sending it down a cable.

    `move()` takes a moment on purpose. A version that returned instantly
    would never be caught half way through a command, and being caught half
    way through is exactly the situation check 5 is about.
    """

    def __init__(self, delay=0.004, break_after=None, has_leds=True):
        self.log = []            # (when, motor, position, speed)
        self.colours = []        # (when, (r, g, b))
        self.delay = delay
        self.break_after = break_after   # start failing after N commands
        self.attempts = 0

        # A robot with no LED eyes. The real one accepts the command and the
        # board discards it, so this is the kinder of the two possibilities —
        # `has_leds=False` below is the nastier one, where the call itself
        # blows up.
        self.has_leds = has_leds

    async def move(self, motor, position, speed=5):
        self.attempts += 1
        if self.break_after is not None and self.attempts > self.break_after:
            raise RuntimeError("pretend cable fell out")
        await asyncio.sleep(self.delay)
        self.log.append((time.monotonic(), motor, position, speed))

    async def set_eye_color(self, r, g, b):
        if not self.has_leds:
            raise RuntimeError("pretend robot has no LED eyes")
        await asyncio.sleep(self.delay)
        self.colours.append((time.monotonic(), (r, g, b)))

    # ── reading the log back ─────────────────────────────────────────────────

    def positions(self, motor, since=None):
        return [p for (t, m, p, s) in self.log
                if m == motor and (since is None or t >= since)]

    def commands(self, since=None):
        return [(t, m, p, s) for (t, m, p, s) in self.log
                if since is None or t >= since]

    def eye_colours(self, since=None):
        return [c for (t, c) in self.colours
                if since is None or t >= since]

    def clear(self):
        self.log = []
        self.colours = []


@contextlib.contextmanager
def faster(**overrides):
    """Turn the waiting-about numbers down so a test finishes this decade."""
    was = {name: getattr(chess_animation, name) for name in overrides}
    for name, value in overrides.items():
        setattr(chess_animation, name, value)
    try:
        yield
    finally:
        for name, value in was.items():
            setattr(chess_animation, name, value)


# ── check 1 and 2: the waiting pose ──────────────────────────────────────────

async def check_waiting_pose():
    problems = []
    robot = FakeRobot()
    anim = Animator(robot)

    with faster(WAIT_EYE_LEAD=0.02, WAIT_PAUSE_MIN=0.0, WAIT_PAUSE_MAX=0.02,
                BLINK_GAP_MIN=0.05, BLINK_GAP_MAX=0.15, BLINK_HOLD=0.02):
        await anim.waiting()
        await asyncio.sleep(1.5)
        await anim.stop()

    # The fixed poses, set on the way in.
    nods = robot.positions(HEADNOD)
    if not nods or nods[0] != chess_animation.WAIT_HEAD_NOD:
        problems.append(
            f"waiting should start by putting the head down at "
            f"{chess_animation.WAIT_HEAD_NOD} (looking at the board). "
            f"First head nod command was {nods[:1]}")

    for lip, name in ((TOPLIP, "top"), (BOTTOMLIP, "bottom")):
        lips = robot.positions(lip)
        if not lips or lips[0] != chess_animation.WAIT_LIPS:
            problems.append(
                f"waiting should close the {name} lip to "
                f"{chess_animation.WAIT_LIPS} on the way in. Got {lips[:1]}")

    # The head must only wander inside the range it was given. A head that
    # goes to 9 while the robot is looking down at a board is a head about to
    # hit something.
    for pos in robot.positions(HEADTURN):
        if not (chess_animation.WAIT_TURN_MIN - 0.001 <= pos
                <= chess_animation.WAIT_TURN_MAX + 0.001):
            problems.append(
                f"waiting turned the head to {pos:.2f}, outside the "
                f"{chess_animation.WAIT_TURN_MIN} to "
                f"{chess_animation.WAIT_TURN_MAX} it was given")
            break

    # The head nod stays down. Only the eyes tilt while waiting, so the robot
    # can glance up without lifting its head. The last command is stop()
    # putting everything back to centre, which is not part of waiting.
    while_waiting = [p for p in robot.positions(HEADNOD) if p != 5.0]
    odd = [p for p in while_waiting if p != chess_animation.WAIT_HEAD_NOD]
    if odd:
        problems.append(
            f"the head should stay down at {chess_animation.WAIT_HEAD_NOD} "
            f"for the whole wait — only the eyes tilt. It also went to {odd}")

    if len(robot.positions(EYETILT)) < 3:
        problems.append("the eyes never tilted while waiting")

    return problems


async def check_eyes_lead_the_head():
    """
    Every head turn should be to a place the eyes went first.

    This is the difference between a robot that looks at something and a robot
    that swivels. It is the same three lines of code either way, which is
    exactly why it is worth a check — nothing about the code looks wrong if
    somebody reorders it.
    """
    problems = []
    robot = FakeRobot()
    anim = Animator(robot)

    with faster(WAIT_EYE_LEAD=0.05, WAIT_PAUSE_MIN=0.0, WAIT_PAUSE_MAX=0.02,
                BLINK_GAP_MIN=99, BLINK_GAP_MAX=99):
        await anim.waiting()
        await asyncio.sleep(1.5)
        await anim._switch_to("off")     # leave the log alone, no recentring

    head_turns = [(t, p) for (t, m, p, s) in robot.log if m == HEADTURN]
    eye_turns = [(t, p) for (t, m, p, s) in robot.log if m == EYETURN]

    if len(head_turns) < 2:
        problems.append("the head never turned while waiting")

    for when, where in head_turns:
        looked_first = any(t < when and p == where for t, p in eye_turns)
        if not looked_first:
            problems.append(
                f"the head turned to {where:.2f} without the eyes going "
                f"there first. The eyes are supposed to lead and the head "
                f"to follow — see _wander() in chess_animation.py")
            break

    return problems


# ── check 3: blinking ────────────────────────────────────────────────────────

async def check_blinking():
    problems = []
    robot = FakeRobot()
    anim = Animator(robot)

    with faster(BLINK_GAP_MIN=0.10, BLINK_GAP_MAX=0.20, BLINK_HOLD=0.03,
                WAIT_EYE_LEAD=0.02, WAIT_PAUSE_MIN=0.0, WAIT_PAUSE_MAX=0.02):
        await anim.waiting()
        await asyncio.sleep(2.0)
        await anim._switch_to("off")

    lids = robot.positions(LIDBLINK)
    if len(lids) < 6:
        problems.append(f"barely blinked — only {len(lids)} lid commands in "
                        f"two seconds of fast-forward")

    shuts = [p for p in lids if p != chess_animation.BLINK_OPEN]
    if not shuts:
        problems.append("the lids never closed")
    for p in shuts:
        if p != chess_animation.BLINK_SHUT:
            problems.append(
                f"a blink closed the lids to {p}, not "
                f"{chess_animation.BLINK_SHUT}")
            break

    # Every blink must end with the eyes open again. A robot left standing
    # with its lids half down looks switched off, and the audience will read
    # it as broken rather than as sleepy.
    if lids and lids[-1] != chess_animation.BLINK_OPEN:
        problems.append(
            "the lids were left shut when the animation stopped — the last "
            "lid command was "
            f"{lids[-1]}, not {chess_animation.BLINK_OPEN}")

    return problems


async def check_blink_survives_a_state_change():
    """
    Stop the animation in the middle of a blink, a hundred times over, and
    check the eyes are always open at the end.

    Worth its own check because the natural way to write the blink loop —
    close, wait, open — leaves the eyes shut if the waiting stops in the
    middle. It would show up only when a state change happened to land in
    that 0.15 second window, which is rare enough to be blamed on the robot.
    """
    problems = []

    with faster(BLINK_GAP_MIN=0.0, BLINK_GAP_MAX=0.01, BLINK_HOLD=0.05,
                WAIT_EYE_LEAD=0.02, WAIT_PAUSE_MIN=0.0, WAIT_PAUSE_MAX=0.02):
        for attempt in range(40):
            robot = FakeRobot(delay=0.001)
            anim = Animator(robot)
            await anim.waiting()
            await asyncio.sleep(0.02 + (attempt % 5) * 0.01)
            await anim._switch_to("off")

            lids = robot.positions(LIDBLINK)
            if lids and lids[-1] != chess_animation.BLINK_OPEN:
                problems.append(
                    f"stopped mid-blink and left the eyes shut (lid ended at "
                    f"{lids[-1]}). Happened on attempt {attempt + 1}")
                break

    return problems


# ── check 4: the announce state must not touch the mouth ─────────────────────

async def check_announce_never_touches_the_lips():
    problems = []
    robot = FakeRobot()
    anim = Animator(robot)

    with faster(ANNOUNCE_HOLD_MIN=0.02, ANNOUNCE_HOLD_MAX=0.05,
                BLINK_GAP_MIN=0.05, BLINK_GAP_MAX=0.15, BLINK_HOLD=0.02):
        await anim.waiting()
        await asyncio.sleep(0.3)
        robot.clear()
        await anim.announcing()
        await asyncio.sleep(2.0)
        await anim._switch_to("off")

    lip_commands = (robot.positions(TOPLIP) + robot.positions(BOTTOMLIP))
    if lip_commands:
        problems.append(
            f"THE ANNOUNCE STATE SENT {len(lip_commands)} LIP COMMANDS. It "
            f"must send none at all. While the robot is speaking, the lip "
            f"sync owns TOPLIP and BOTTOMLIP and drives them from Azure's "
            f"mouth shapes. Anything else moving them at the same time is "
            f"two programs fighting over one motor, and the mouth stutters.")

    return problems


async def check_announce_pose():
    problems = []
    robot = FakeRobot()
    anim = Animator(robot, face=6.0)

    with faster(ANNOUNCE_HOLD_MIN=0.02, ANNOUNCE_HOLD_MAX=0.05,
                BLINK_GAP_MIN=99, BLINK_GAP_MAX=99):
        await anim.announcing()
        await asyncio.sleep(1.5)
        await anim._switch_to("off")

    sway = chess_animation.ANNOUNCE_SWAY
    nods = robot.positions(HEADNOD)
    turns = robot.positions(HEADTURN)

    if not nods:
        problems.append("announcing never lifted the head at all")
    if not nods or nods[0] != chess_animation.ANNOUNCE_HEAD_NOD:
        problems.append(
            f"announcing should lift the head to "
            f"{chess_animation.ANNOUNCE_HEAD_NOD} first. Got {nods[:1]}")

    for p in nods:
        if abs(p - chess_animation.ANNOUNCE_HEAD_NOD) > sway + 0.001:
            problems.append(
                f"the head nodded to {p:.2f} while announcing, further than "
                f"{sway} from {chess_animation.ANNOUNCE_HEAD_NOD}")
            break
    for p in turns:
        if abs(p - 6.0) > sway + 0.001:
            problems.append(
                f"the head turned to {p:.2f} while announcing, further than "
                f"{sway} from the 6.0 it was told to face")
            break

    # It has to actually drift. A head pinned at one number with a mouth
    # flapping under it reads as a fault rather than as a style.
    if len(set(nods)) < 2 or len(set(turns)) < 2:
        problems.append(
            "the head held completely still while announcing. It is supposed "
            "to drift a little either side — see _address()")

    # The eyes come back to straight ahead. They were wandering a moment ago.
    if not robot.positions(EYETURN) or \
            robot.positions(EYETURN)[0] != chess_animation.ANNOUNCE_EYES:
        problems.append(
            "announcing should bring the eyes back to straight ahead. A "
            "robot addressing the room while looking at the floor is worse "
            "than one that does not move")

    return problems


async def check_face_setting_is_obeyed():
    """--face has to actually change where the robot looks."""
    problems = []

    for face in (3.5, 6.5):
        robot = FakeRobot()
        anim = Animator(robot, face=face)
        with faster(ANNOUNCE_HOLD_MIN=0.02, ANNOUNCE_HOLD_MAX=0.05,
                    BLINK_GAP_MIN=99, BLINK_GAP_MAX=99):
            await anim.announcing()
            await asyncio.sleep(0.5)
            await anim._switch_to("off")

        turns = robot.positions(HEADTURN)
        if not turns or abs(turns[0] - face) > 0.001:
            problems.append(
                f"--face {face} was ignored: the head went to {turns[:1]} "
                f"instead")

    # And None must mean "the default", not "nowhere". argparse hands over
    # None whenever a caller did not care.
    robot = FakeRobot()
    anim = Animator(robot, face=None)
    with faster(ANNOUNCE_HOLD_MIN=99, BLINK_GAP_MIN=99, BLINK_GAP_MAX=99):
        await anim.announcing()
        await asyncio.sleep(0.2)
        await anim._switch_to("off")
    turns = robot.positions(HEADTURN)
    if not turns or abs(turns[0] - chess_animation.ANNOUNCE_FACE) > 0.001:
        problems.append(
            f"face=None should fall back to the default "
            f"{chess_animation.ANNOUNCE_FACE}, but the head went to "
            f"{turns[:1]}")

    return problems


# ── check 5: switching state really stops the old movement ───────────────────

async def check_switching_stops_the_old_state():
    """
    THE BUG THIS EXISTS FOR. Setting the stop flag and carrying on would leave
    the previous state's loops alive for up to a second — long enough to send
    one more command. Then the waiting loop pulls the head down to the board
    in the middle of the announcement and the announce loop pulls it back up.

    On hardware that is a twitch nobody can account for by reading either
    loop, because neither loop is wrong. It is the handover that is wrong.

    Checked two ways. The first is exact: after switching, none of the old
    state's tasks may still be pending. The second is what an audience would
    actually see: switch back and forth thirty times and look for a single
    command that belongs to the state we just left.
    """
    problems = []

    # ── the exact one ────────────────────────────────────────────────────────
    #
    # _switch_to is called directly, and the tasks are counted on the very
    # next line with nothing awaited in between. That is the point: if the
    # handover only ASKS the old loops to stop, they are still running at
    # this instant, and the check fails every single time rather than once in
    # a hundred runs. Going through announcing() instead would let its own
    # first few movements give the old loops time to tidy themselves up, and
    # the check would pass while the bug was still there.
    robot = FakeRobot()
    anim = Animator(robot)
    with faster(WAIT_EYE_LEAD=0.02, WAIT_PAUSE_MIN=0.0, WAIT_PAUSE_MAX=0.02,
                BLINK_GAP_MIN=0.05, BLINK_GAP_MAX=0.10, BLINK_HOLD=0.02):
        await anim.waiting()
        await asyncio.sleep(0.3)
        old_tasks = list(anim._tasks)
        await anim._switch_to("announcing")
        still_going = [t for t in old_tasks if not t.done()]
        if still_going:
            problems.append(
                f"{len(still_going)} of the waiting state's movements were "
                f"still running the moment the state changed. _switch_to() "
                f"has to WAIT for them to finish, not just ask them to stop")
        await anim._switch_to("off")

    # ── the one an audience would notice ─────────────────────────────────────
    with faster(WAIT_EYE_LEAD=0.01, WAIT_PAUSE_MIN=0.0, WAIT_PAUSE_MAX=0.01,
                ANNOUNCE_HOLD_MIN=0.01, ANNOUNCE_HOLD_MAX=0.02,
                BLINK_GAP_MIN=0.02, BLINK_GAP_MAX=0.05, BLINK_HOLD=0.01):
        robot = FakeRobot(delay=0.002)
        anim = Animator(robot)
        sway = chess_animation.ANNOUNCE_SWAY

        for _ in range(30):
            await anim.waiting()
            await asyncio.sleep(0.05)
            await anim.announcing()
            robot.clear()
            await asyncio.sleep(0.05)

            # Anything from the waiting loop landing here is the bug.
            strays = [p for p in robot.positions(HEADNOD)
                      if abs(p - chess_animation.ANNOUNCE_HEAD_NOD) > sway + 0.001]
            strays += [p for p in robot.positions(HEADTURN)
                       if abs(p - anim.face) > sway + 0.001]
            strays += [p for p in robot.positions(EYETURN)
                       if p != chess_animation.ANNOUNCE_EYES]
            strays += [p for p in robot.positions(EYETILT)
                       if p != chess_animation.ANNOUNCE_EYES]
            if strays:
                problems.append(
                    f"a movement from the WAITING state arrived after the "
                    f"switch to announcing: {strays[:4]}. The two states are "
                    f"fighting over the same motors")
                break

        await anim._switch_to("off")

    return problems


# ── the eyes: who is winning ─────────────────────────────────────────────────

async def check_eye_colour_follows_the_game():
    """
    Green when this robot is ahead, amber when level, red when behind.

    The numbers are checked by direction rather than by exact value, because
    the exact values are Michael's to change and a test that pins them down
    would fail every time he adjusted a colour — which is the opposite of
    useful. What must stay true is that winning is greener than losing.
    """
    problems = []
    a = chess_animation

    winning = a.eval_colour(a.EVAL_FULL)
    ahead = a.eval_colour(200)
    level = a.eval_colour(0)
    behind = a.eval_colour(-200)
    losing = a.eval_colour(-a.EVAL_FULL)

    if winning != a.COLOUR_WINNING:
        problems.append(f"a full lead should give exactly COLOUR_WINNING, "
                        f"got {winning}")
    if losing != a.COLOUR_LOSING:
        problems.append(f"a full deficit should give exactly COLOUR_LOSING, "
                        f"got {losing}")
    if level != a.COLOUR_LEVEL:
        problems.append(f"a level game should give exactly COLOUR_LEVEL, "
                        f"got {level}")

    # Green goes up as the game goes well, red goes up as it goes badly.
    if not (losing[1] <= behind[1] <= level[1] <= ahead[1] <= winning[1]):
        problems.append(
            f"the green channel does not rise as the game improves: "
            f"{losing[1]} {behind[1]} {level[1]} {ahead[1]} {winning[1]}")
    if not (winning[0] <= ahead[0] <= level[0] <= behind[0] <= losing[0]):
        problems.append(
            f"the red channel does not rise as the game gets worse: "
            f"{winning[0]} {ahead[0]} {level[0]} {behind[0]} {losing[0]}")

    # A partial lead must give a partial colour. Three fixed steps would jump
    # from amber to green the moment the game tipped, which reads as a fault
    # rather than as a game going well. The point of blending is that a game
    # slipping away shows as a colour slipping away.
    half_up = a.eval_colour(a.EVAL_FULL // 2)
    half_down = a.eval_colour(-a.EVAL_FULL // 2)
    if half_up in (a.COLOUR_LEVEL, a.COLOUR_WINNING):
        problems.append(
            f"being half way to a winning lead gives {half_up}, which is "
            f"already one of the fixed colours. The colour is supposed to "
            f"blend between them rather than jump")
    if half_down in (a.COLOUR_LEVEL, a.COLOUR_LOSING):
        problems.append(
            f"being half way to a lost game gives {half_down}, which is "
            f"already one of the fixed colours. It should blend")

    # Beyond the full-colour point it must not keep going and run off the end
    # of the scale. Mate is reported as 10000, twenty times EVAL_FULL.
    for mate in (10000, -10000):
        for channel in a.eval_colour(mate):
            if not 0 <= channel <= 10:
                problems.append(
                    f"an evaluation of {mate} (which is how mate is "
                    f"reported) gave {a.eval_colour(mate)} — outside the 0 "
                    f"to 10 the LEDs accept")
                break

    # Nobody has worked it out yet. Before the first move there is no
    # evaluation, and guessing would mean the eyes lie for the opening.
    if a.eval_colour(None) != a.COLOUR_LEVEL:
        problems.append("an unknown evaluation should show the level colour, "
                        f"not {a.eval_colour(None)}")

    # ── the point of view ────────────────────────────────────────────────────
    # The server always reports positive as good for WHITE, because that is
    # what the bar on the display needs. Get this flip wrong and the losing
    # robot glows green all game — which would look completely deliberate and
    # be entirely backwards.
    was = a.EVAL_POINT_OF_VIEW
    try:
        a.EVAL_POINT_OF_VIEW = "mine"
        if a.eval_from_my_side(300, "white") != 300:
            problems.append("White being 3 pawns up should read as +300 to "
                            "the White robot")
        if a.eval_from_my_side(300, "black") != -300:
            problems.append(
                "White being 3 pawns up should read as -300 to the BLACK "
                "robot. Without that flip the losing robot glows green")
        if a.eval_from_my_side(None, "black") is not None:
            problems.append("an unknown evaluation must stay unknown")

        a.EVAL_POINT_OF_VIEW = "white"
        if a.eval_from_my_side(300, "black") != 300:
            problems.append(
                "with EVAL_POINT_OF_VIEW set to 'white' both robots should "
                "show the same thing as the bar on the display")
    finally:
        a.EVAL_POINT_OF_VIEW = was

    return problems


async def check_the_eyes_change_in_a_real_game():
    problems = []
    a = chess_animation
    robot = FakeRobot()
    anim = Animator(robot)

    with faster(WAIT_EYE_LEAD=0.02, WAIT_PAUSE_MIN=0.0, WAIT_PAUSE_MAX=0.02,
                BLINK_GAP_MIN=99, BLINK_GAP_MAX=99,
                ANNOUNCE_HOLD_MIN=0.02, ANNOUNCE_HOLD_MAX=0.05):
        await anim.waiting()
        await anim.set_eval(600)             # winning
        winning_now = robot.eye_colours()[-1:]
        await anim.set_eval(-600)            # thrown it away
        losing_now = robot.eye_colours()[-1:]

        robot.clear()
        await anim.announcing()
        await asyncio.sleep(0.3)
        speaking = robot.eye_colours()

        # The game moves on while it is still talking. The eyes must not.
        await anim.set_eval(900)
        await asyncio.sleep(0.2)
        still_speaking = robot.eye_colours()

        robot.clear()
        await anim.waiting()
        back = robot.eye_colours()
        await anim.stop()
        ended = robot.eye_colours()

    if winning_now != [a.COLOUR_WINNING]:
        problems.append(f"waiting on a won game should show "
                        f"{a.COLOUR_WINNING}, got {winning_now}")
    if losing_now != [a.COLOUR_LOSING]:
        problems.append(f"waiting on a lost game should show "
                        f"{a.COLOUR_LOSING}, got {losing_now}")
    if speaking != [a.COLOUR_ANNOUNCE]:
        problems.append(f"announcing should turn the eyes "
                        f"{a.COLOUR_ANNOUNCE}, got {speaking}")
    if still_speaking != [a.COLOUR_ANNOUNCE]:
        problems.append(
            f"the eyes changed colour while the robot was still speaking: "
            f"{still_speaking}. Blue has to hold for the whole sentence — "
            f"a robot announcing its own checkmate while its eyes turn red "
            f"is telling the audience two things at once")
    if back != [a.COLOUR_WINNING]:
        problems.append(
            f"going back to waiting should show the game as it now stands "
            f"({a.COLOUR_WINNING} after that last swing), got {back}")
    if ended[-1:] != [a.COLOUR_OFF]:
        problems.append(f"the eyes should go out when the program stops, "
                        f"ended on {ended[-1:]}")

    return problems


async def check_the_cable_is_not_flooded():
    """
    The colour must only be sent when it CHANGES.

    set_eval() is called on every answer from the server, which is twice a
    second for the whole game. The LEDs share the one serial cable with every
    motor and with the lip sync, so repainting them on every poll would be a
    few thousand pointless messages, all of them competing with the mouth.
    """
    problems = []
    robot = FakeRobot()
    anim = Animator(robot)

    with faster(WAIT_EYE_LEAD=99, BLINK_GAP_MIN=99, BLINK_GAP_MAX=99):
        await anim.waiting()
        robot.clear()
        for _ in range(200):             # a hundred seconds of polling
            await anim.set_eval(120)
        repeats = len(robot.eye_colours())
        await anim._switch_to("off")

    if repeats > 1:
        problems.append(
            f"the same colour was sent {repeats} times over. It must only go "
            f"down the cable when it actually changes — see _set_eyes()")

    return problems


async def check_no_leds_cannot_stop_the_show():
    """
    Lester has no LED eyes. Neither he nor anything else may notice.

    The real robot accepts the command and its board throws it away, so this
    tests the nastier case: the call itself failing. A missing pair of LEDs
    must cost the colour and nothing else.
    """
    problems = []
    robot = FakeRobot(has_leds=False)
    anim = Animator(robot)

    said = io.StringIO()
    try:
        with contextlib.redirect_stdout(said):
            with faster(WAIT_EYE_LEAD=0.02, WAIT_PAUSE_MIN=0.0,
                        WAIT_PAUSE_MAX=0.02, BLINK_GAP_MIN=0.05,
                        BLINK_GAP_MAX=0.1, BLINK_HOLD=0.02,
                        ANNOUNCE_HOLD_MIN=0.02, ANNOUNCE_HOLD_MAX=0.05):
                await anim.waiting()
                await anim.set_eval(300)
                await asyncio.sleep(0.3)
                await anim.announcing()
                await asyncio.sleep(0.3)
                await anim.waiting()
                await asyncio.sleep(0.2)
                await anim.stop()
    except Exception as exc:
        problems.append(
            f"a robot with no LED eyes brought the animation down: {exc!r}. "
            f"Lester has no LEDs — this is not a hypothetical")

    # Everything else must have carried on regardless.
    if not robot.positions(HEADTURN):
        problems.append("a robot with no LED eyes never moved its head "
                        "either. The colour is the only thing that should "
                        "be missing")

    if said.getvalue().count("eye colour did not take") > 1:
        problems.append(
            "a robot with no LEDs complained more than once. Once is help; "
            "once per move fills the log for the whole game")

    return problems


# ── check 6, 7, 8: it must never stop the show ───────────────────────────────

async def check_a_broken_motor_does_not_stop_anything():
    """
    A cable pulled mid-game must cost the head movement and nothing else. The
    chess and the speech can carry on perfectly well without a robot nodding,
    and that is a far better failure in front of people than a robot that
    stops.
    """
    problems = []
    robot = FakeRobot(break_after=3)
    anim = Animator(robot)

    # The complaint it prints is expected, and catching it here keeps this
    # test silent when all is well — as well as proving the complaint only
    # happens once. A broken motor printing twice a second would bury every
    # other message in the log, which during a show is the log you need.
    said = io.StringIO()
    try:
        with contextlib.redirect_stdout(said):
            with faster(WAIT_EYE_LEAD=0.02, WAIT_PAUSE_MIN=0.0,
                        WAIT_PAUSE_MAX=0.02, BLINK_GAP_MIN=0.02,
                        BLINK_GAP_MAX=0.05, BLINK_HOLD=0.01):
                await anim.waiting()
                await asyncio.sleep(0.4)
                await anim.announcing()
                await asyncio.sleep(0.4)
                await anim.waiting()
                await asyncio.sleep(0.2)
                await anim.stop()
    except Exception as exc:
        problems.append(
            f"a failing motor brought the animation down: {exc!r}. Every "
            f"movement is supposed to be wrapped so this can never happen")

    complaints = said.getvalue().count("did not respond")
    if complaints == 0:
        problems.append("a motor failed and nothing said so. It must not "
                        "stop the show, but it must not be silent either")
    elif complaints > 1:
        problems.append(
            f"a broken motor complained {complaints} times. Once is help; "
            f"once per movement buries every other message in the log")

    return problems


async def check_no_animation_moves_nothing():
    problems = []
    robot = FakeRobot()
    anim = Animator(robot, enabled=False)

    with faster(WAIT_EYE_LEAD=0.02, WAIT_PAUSE_MIN=0.0, WAIT_PAUSE_MAX=0.02,
                BLINK_GAP_MIN=0.02, BLINK_GAP_MAX=0.05):
        await anim.waiting()
        await asyncio.sleep(0.4)
        await anim.announcing()
        await asyncio.sleep(0.4)
        await anim.stop()

    if robot.log:
        moved = {MOTOR_NAMES.get(m, m) for (t, m, p, s) in robot.log}
        problems.append(
            f"--no-animation still moved {sorted(moved)}. It is the "
            f"get-out-of-jail switch and has to move nothing at all")

    return problems


async def check_stop_puts_everything_back():
    problems = []
    robot = FakeRobot()
    anim = Animator(robot)

    with faster(WAIT_EYE_LEAD=0.02, WAIT_PAUSE_MIN=0.0, WAIT_PAUSE_MAX=0.02,
                BLINK_GAP_MIN=0.02, BLINK_GAP_MAX=0.05, BLINK_HOLD=0.01):
        await anim.waiting()
        await asyncio.sleep(0.4)
        await anim.stop()
        after_stop = time.monotonic()
        await asyncio.sleep(0.4)

    for motor in (HEADNOD, HEADTURN, EYETURN, EYETILT):
        ended_at = robot.positions(motor)
        if not ended_at or ended_at[-1] != 5.0:
            problems.append(
                f"{MOTOR_NAMES[motor]} was left at {ended_at[-1:]} instead of "
                f"centred at 5 when the animation stopped")
    if robot.positions(LIDBLINK)[-1:] != [chess_animation.BLINK_OPEN]:
        problems.append("the eyes were not left open when the animation "
                        "stopped")

    late = robot.commands(since=after_stop)
    if late:
        problems.append(
            f"{len(late)} commands were still being sent after stop() "
            f"returned. Nothing may be left running — the controller's "
            f"queues get shut down straight afterwards, and a command posted "
            f"to a queue nobody is emptying waits for room that never comes. "
            f"That is a program which finishes the game and then never exits")

    return problems


# ── check 9: the numbers as shipped ──────────────────────────────────────────

def check_the_settings_make_sense():
    """
    The timing checks above run with the numbers turned right down. So these
    read the numbers that actually ship, and ask whether a person could
    watch them.
    """
    problems = []
    a = chess_animation

    for name in ("WAIT_HEAD_NOD", "WAIT_TURN_MIN", "WAIT_TURN_MAX",
                 "WAIT_TILT_MIN", "WAIT_TILT_MAX", "WAIT_LIPS",
                 "ANNOUNCE_HEAD_NOD", "ANNOUNCE_FACE", "ANNOUNCE_EYES",
                 "BLINK_OPEN", "BLINK_SHUT"):
        value = getattr(a, name)
        if not 0 <= value <= 10:
            problems.append(
                f"{name} is {value}. Every position is a slider from 0 to 10 "
                f"— anything outside that is silently clipped, so the robot "
                f"will not go where the number says")

    if a.WAIT_TURN_MIN >= a.WAIT_TURN_MAX:
        problems.append("WAIT_TURN_MIN must be smaller than WAIT_TURN_MAX")
    if a.WAIT_TILT_MIN >= a.WAIT_TILT_MAX:
        problems.append("WAIT_TILT_MIN must be smaller than WAIT_TILT_MAX")
    if a.BLINK_SHUT >= a.BLINK_OPEN:
        problems.append("BLINK_SHUT has to be lower than BLINK_OPEN, or a "
                        "blink opens the eyes wider instead of closing them")
    if a.BLINK_GAP_MIN >= a.BLINK_GAP_MAX:
        problems.append("BLINK_GAP_MIN must be smaller than BLINK_GAP_MAX")
    if not 0.2 <= a.BLINK_GAP_MIN:
        problems.append(f"BLINK_GAP_MIN is {a.BLINK_GAP_MIN} seconds. Faster "
                        f"than about one blink every fifth of a second reads "
                        f"as a fault rather than as life")
    for name in ("COLOUR_WINNING", "COLOUR_LEVEL", "COLOUR_LOSING",
                 "COLOUR_ANNOUNCE", "COLOUR_OFF"):
        colour = getattr(a, name)
        if len(colour) != 3 or not all(0 <= c <= 10 for c in colour):
            problems.append(
                f"{name} is {colour}. Each colour is three numbers — red, "
                f"green and blue — each from 0 to 10")

    if a.EVAL_FULL <= 0:
        problems.append("EVAL_FULL is how big a lead counts as fully green. "
                        "It has to be a positive number of centipawns")
    if a.EVAL_POINT_OF_VIEW not in ("mine", "white"):
        problems.append(
            f"EVAL_POINT_OF_VIEW is {a.EVAL_POINT_OF_VIEW!r}. It has to be "
            f"'mine' (each robot shows its own fortunes) or 'white' (both "
            f"match the bar on the display)")

    if a.COLOUR_WINNING == a.COLOUR_LOSING:
        problems.append("winning and losing are the same colour, so the eyes "
                        "say nothing at all")

    if a.BLINK_GAP_MAX > 60:
        problems.append(f"BLINK_GAP_MAX is {a.BLINK_GAP_MAX} seconds — most "
                        f"of an audience will never see a blink")

    # The announce drift must not be so wide that the two states overlap.
    # If it were, "which state is this robot in" would stop being readable
    # from the position of its head, and so would half these checks.
    if abs(a.ANNOUNCE_HEAD_NOD - a.WAIT_HEAD_NOD) <= a.ANNOUNCE_SWAY:
        problems.append(
            f"the announce head nod ({a.ANNOUNCE_HEAD_NOD}) drifts by "
            f"{a.ANNOUNCE_SWAY}, which reaches the waiting nod "
            f"({a.WAIT_HEAD_NOD}). Lifting the head off the board has to be "
            f"a movement the audience can see")

    return problems


def check_motor_numbers():
    """
    Are the copied motor numbers still OhbotPi2's?

    Its own output is swallowed. Looking for OhbotPi2 prints a friendly
    explanation when the folder is not there, which is completely normal on a
    machine with no robot — and this test is supposed to be silent when all
    is well.
    """
    with contextlib.redirect_stdout(io.StringIO()):
        return chess_animation.check_motor_numbers()


def check_the_shutdown_order():
    """
    In chess_player.py, the animation must be stopped BEFORE the controller.

    THIS ORDER IS NOT TIDINESS. Every movement is posted to a queue inside the
    controller, and those queues hold ten commands. `controller.stop()` shuts
    down the workers that empty them. An animation loop still running at that
    point posts an eleventh command to a queue nobody is emptying, and waits
    for room that is never coming.

    Measured, with the queues deliberately small: stopping the animator first
    exits every time, stopping the controller first hangs and never exits at
    all. What Michael would see is a game that finishes, says goodbye, prints
    "robot released" — and then just sits there with the cable still held, so
    the next thing he starts reports "robot not found". Two symptoms, neither
    of them pointing at shutdown.

    It is checked by reading the file rather than by running it, for the same
    reason test_show.py checks how Popen is called: getting a real deadlock to
    happen on demand needs the queues full at exactly the wrong moment, which
    is precisely why it would survive testing and turn up during a show.
    """
    problems = []
    try:
        with open("chess_player.py", encoding="utf-8") as f:
            source = f.read()
    except OSError:
        return []          # not run from the project folder; not a problem

    # Read it as CODE, not as text. The first version of this check searched
    # the raw characters and failed on the correct file, because the comment
    # explaining the order necessarily mentions controller.stop() first.
    # A checker that cannot tell an instruction from a sentence about an
    # instruction is worse than none.
    shut_down = None
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and \
                node.name == "shut_down":
            shut_down = node
            break

    if shut_down is None:
        problems.append("shut_down() has gone from chess_player.py")
        return problems

    order = []
    for node in ast.walk(shut_down):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "stop" \
                and isinstance(node.func.value, ast.Name):
            order.append((node.lineno, node.func.value.id))
    order.sort()
    names = [who for _, who in order]

    stops_animator = names.index("animator") if "animator" in names else -1
    stops_controller = names.index("controller") if "controller" in names else -1

    if stops_animator < 0:
        problems.append(
            "shut_down() in chess_player.py no longer stops the animator. "
            "The movement loops would be left running after the robot has "
            "been released")
    elif stops_controller < 0:
        problems.append("shut_down() no longer stops the controller")
    elif stops_animator > stops_controller:
        problems.append(
            "shut_down() in chess_player.py stops the controller BEFORE the "
            "animator. That way round hangs: the movement loops post to "
            "queues nobody is emptying any more and wait forever. The "
            "program finishes the game and then never exits, still holding "
            "the cable")

    return problems


# ── running the lot ──────────────────────────────────────────────────────────

async def run_all():
    checks = [
        ("the waiting pose", check_waiting_pose()),
        ("the eyes leading the head", check_eyes_lead_the_head()),
        ("blinking", check_blinking()),
        ("blinking through a state change", check_blink_survives_a_state_change()),
        ("announcing never touching the lips",
         check_announce_never_touches_the_lips()),
        ("the announce pose", check_announce_pose()),
        ("the --face setting", check_face_setting_is_obeyed()),
        ("switching states cleanly", check_switching_stops_the_old_state()),
        ("the eye colours themselves", check_eye_colour_follows_the_game()),
        ("the eyes through a game", check_the_eyes_change_in_a_real_game()),
        ("not flooding the cable with colours",
         check_the_cable_is_not_flooded()),
        ("a robot with no LED eyes", check_no_leds_cannot_stop_the_show()),
        ("surviving a broken motor",
         check_a_broken_motor_does_not_stop_anything()),
        ("--no-animation", check_no_animation_moves_nothing()),
        ("stopping cleanly", check_stop_puts_everything_back()),
    ]

    problems = []
    for name, coro in checks:
        found = await coro
        if found:
            problems.append((name, found))

    for name, found in (("the settings as shipped", check_the_settings_make_sense()),
                        ("the shutdown order", check_the_shutdown_order()),
                        ("the motor numbers", check_motor_numbers())):
        if found:
            problems.append((name, found))

    return problems


def main():
    started = time.monotonic()
    problems = asyncio.run(run_all())
    took = time.monotonic() - started

    if not problems:
        print(f"All animation checks passed in {took:.0f} seconds. "
              f"Nothing to report.")
        return 0

    print()
    print("=" * 70)
    print("  PROBLEMS WITH THE ANIMATION")
    print("=" * 70)
    for name, found in problems:
        print()
        print(f"  {name}:")
        for line in found:
            print(f"    - {line}")
    print()
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(0)
