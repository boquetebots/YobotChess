#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chess_dropout.py — keeping the show going when the internet does not
================================================================================

ONE JOB: let a robot lose a sentence without losing the game.

Everything in this demo runs on the machine in front of you. Stockfish, the
board, the display, the server, the motors — none of it needs the internet.
**Azure speech is the only thing that does**, and it is needed once per
spoken line.

--------------------------------------------------------------------------------
WHY THIS FILE EXISTS
--------------------------------------------------------------------------------

Found 2026-09-01, while working out whether a phone hotspot would be enough to
run the demo out in the Comarca. It would — the bandwidth is nothing, about
10 to 20 MB for a whole game, and a slow link shows up as a longer pause
before a robot speaks rather than as broken audio, because the sentence is
downloaded in full before any of it is played.

But **one dropped line killed the robot**, and that is a different matter.

The chain: `synthesize_to_file_with_visemes()` in OhbotPi2 raises a plain
RuntimeError when Azure will not answer. `AsyncOhbotController.say()` has a
`finally` but no `except`, so it goes straight through. `speak_and_report()`
in `chess_player.py` is the same shape, so it goes through that too. And the
main game loop only ever caught Ctrl-C. So the exception ran all the way out
of the loop, the robot shut its motors down and the program exited.

From the front of the room that looks exactly like a crash, because it is
one. Worse, the OTHER robot then waits forever — which is correct, documented
behaviour, and means the show is over.

On a desk on wired internet this essentially never happens. On a cell
hotspot it is the likely failure, and one bad moment in a ninety-move game is
all it takes.

--------------------------------------------------------------------------------
THE RULE: A LOST LINE IS A PAUSE, NOT AN ENDING
--------------------------------------------------------------------------------

This is the same rule the speaking floor already follows — see the note on
SPEAKING_TIMEOUT in `chess_server.py`. A robot that cannot speak must cost the
show a silence and nothing more. Nobody in the audience knows which sentence
they did not hear. Everybody knows when the robots stop.

--------------------------------------------------------------------------------
WHY A FAST FAILURE IS RETRIED AND A SLOW ONE IS NOT
--------------------------------------------------------------------------------

This looks inconsistent and is not. The two failures are different animals.

**A fast failure** — Azure answers quickly to say it will not do it — is what
a brief cell dropout looks like. It costs a fraction of a second, the
connection is often back by the time we ask again, and retrying is nearly
free. So we retry once.

**A slow failure** — nothing comes back at all — is NOT retried, and that
matters. The synthesis runs in a background worker that holds a lock, and
giving up waiting for it does not stop it; it carries on until Azure's own
code times out, still holding that lock. A second attempt would queue up
behind the first and time out as well, so retrying a hang buys nothing and
costs another full deadline of a robot standing there saying nothing. One
silence is a pause. Two in a row is a broken machine.

--------------------------------------------------------------------------------
THE NUMBERS, AND THE ONE THAT IS LOAD-BEARING
--------------------------------------------------------------------------------

SPEECH_DEADLINE_SECONDS is a THEATRE setting, not a technical one. A robot
silent for more than a few seconds reads as broken to an audience however
healthy it is inside. Ten seconds is generous for a poor link and short
enough that a lost line still reads as a beat.

**It has to stay well under the server's SPEAKING_TIMEOUT of 30 seconds**,
which is how long the server waits before deciding a silent robot has died
and taking the speaking floor away from it. Deadline times attempts must
come in under that, or a robot could still be politely waiting for Azure at
the moment the server declares it dead and lets the other robot start
talking — and the two would speak over each other, which is the exact bug
the floor was built to fix. `test_dropout.py` checks the two files against
each other so raising one without the other cannot slip through.

--------------------------------------------------------------------------------
TESTING IT
--------------------------------------------------------------------------------

No robot, no Azure, no internet, no chess engine, no add-ons at all:

    python test_dropout.py
"""

import asyncio


# ── How long to wait for one sentence ────────────────────────────────────────
# See the note above. This is a show setting. Raise it if you would rather
# have the line late than not at all; lower it if a stall looks worse to you
# than a missing joke. Keep DEADLINE x (1 + RETRIES) below the server's
# SPEAKING_TIMEOUT.
SPEECH_DEADLINE_SECONDS = 10.0

# How many extra goes to give a line that failed FAST. Slow failures are
# never retried, whatever this says — see the docstring.
RETRIES_AFTER_A_FAST_FAILURE = 1

# After this many lost lines in a row, say plainly that the internet is the
# problem. Two robots quietly playing perfect chess in total silence is the
# most confusing thing this program can do, and the cause is not guessable
# from the front of a room.
SHOUT_AFTER_THIS_MANY_IN_A_ROW = 3


class KeepTalking:
    """
    Speaks a line, and never lets a speech failure stop the game.

    `announce` is where the notes go. It is print() in the real program, and
    the display page shows what each program printed behind its Log button —
    so anything said here reaches Michael at the back of the room without him
    going to find a terminal window.
    """

    def __init__(self,
                 deadline_seconds=SPEECH_DEADLINE_SECONDS,
                 retries=RETRIES_AFTER_A_FAST_FAILURE,
                 shout_after=SHOUT_AFTER_THIS_MANY_IN_A_ROW,
                 announce=print):
        self.deadline_seconds = deadline_seconds
        self.retries = retries
        self.shout_after = shout_after
        self.announce = announce

        # Counted so the program can say something useful rather than just
        # falling quiet. Reset by the first line that gets through.
        self.consecutive_failures = 0
        self.lines_lost = 0
        self.attempts_made = 0

    async def say(self, make_attempt, text=""):
        """
        Try to speak one line. Returns True if it was spoken, False if not.

        NEVER RAISES for a speech problem — that is the whole point of the
        file. Ctrl-C and task cancellation still go through untouched, so
        stopping the show by hand works exactly as it did.

        `make_attempt` must be a function that returns a FRESH coroutine each
        time it is called. It cannot be a single coroutine object, because a
        coroutine can only be awaited once and the retry needs a second one.
        In `chess_player.py` it is:

            lambda: controller.say(text, lip_sync=True, language=lang)
        """
        goes_left = self.retries + 1

        while goes_left > 0:
            goes_left -= 1
            self.attempts_made += 1

            try:
                await asyncio.wait_for(make_attempt(),
                                       timeout=self.deadline_seconds)

            except asyncio.CancelledError:
                # Ctrl-C, or the program shutting down. Not a speech fault,
                # and it must not be swallowed or the robot would refuse to
                # stop. (KeyboardInterrupt is not an Exception either, so it
                # sails past the catch-all below on its own.)
                raise

            except (asyncio.TimeoutError, TimeoutError):
                # Nothing came back. Do NOT retry — see the docstring. On
                # Python 3.11 and later these two are the same class; both
                # are named so this behaves the same on the Pi's older
                # Python, and so it is caught BEFORE the catch-all, since
                # a modern TimeoutError is an ordinary Exception.
                self._lost(text, "Azure did not answer within "
                                 f"{self.deadline_seconds:.0f} seconds")
                return False

            except Exception as problem:                     # noqa: BLE001
                # A fast, definite refusal — the usual shape of a brief
                # dropout. Worth one more go.
                if goes_left:
                    self.announce(f"  (speech failed, trying that line once "
                                  f"more — {problem})")
                    continue
                self._lost(text, str(problem))
                return False

            else:
                self.consecutive_failures = 0
                return True

        return False

    def _lost(self, text, why):
        """Note a line that will not be heard, and carry on."""
        self.consecutive_failures += 1
        self.lines_lost += 1

        self.announce(f"  (no speech that time, carrying on — {why})")
        if text:
            self.announce(f"      not spoken: {text}")

        # Exactly at the threshold, so this is said once per outage rather
        # than on every line for the rest of the game. The next line that
        # gets through resets the count, so a second outage says it again.
        if self.consecutive_failures == self.shout_after:
            for line in self.internet_warning():
                self.announce(line)

    def internet_warning(self):
        """
        What to print when the robot has gone quiet several times running.

        Written for somebody standing at the back of a room with an audience
        in front of them, not for a programmer reading a log afterwards.
        """
        return [
            "",
            "  " + "-" * 66,
            f"  SILENT FOR {self.consecutive_failures} LINES IN A ROW.",
            "",
            "  The chess is fine and the game is still going. What has",
            "  stopped is the connection to Azure, and that is the only",
            "  thing in this whole demo that needs the internet.",
            "",
            "  Check the hotspot. The robots will start talking again by",
            "  themselves the moment it comes back — nothing needs",
            "  restarting.",
            "  " + "-" * 66,
            "",
        ]
