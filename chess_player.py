#!/usr/bin/env python3
"""
chess_player.py — the program that drives one Yobot
================================================================================

This runs on the machine the robot is plugged into. It does four things and
nothing else:

  1. Connects to the Yobot over the USB cable
  2. Sets up Azure speech, WITH LIP SYNC
  3. Asks the chess server "is it my turn?" every half second
  4. When it is, gets back a finished sentence and says it, mouth moving

**It does not know how to play chess.** Not one line of chess logic lives in
here. The server decides the moves, writes the commentary, and hands over a
plain English sentence. This robot just talks.

That is on purpose: it keeps the API key in one place, stops the two robots
repeating each other, and means changing what they say never involves
touching a robot.

--------------------------------------------------------------------------------
BEFORE YOU RUN IT — THE ONE RULE THAT WILL BITE YOU
--------------------------------------------------------------------------------

**Only one program can hold the robot's USB cable at a time.** The Greeter,
the Sequence Builder, Calibration and this program all want it. If another
one has it, this will report "robot not found" no matter how many times you
replug the cable.

Stop the others first — the Launcher page in OhbotPi2 is the traffic cop.

--------------------------------------------------------------------------------
RUNNING IT
--------------------------------------------------------------------------------

Test the speech on its own first, with no chess and no server:

    python chess_player.py --say-once

That should move the mouth. If it does not, fix that before going further —
everything else depends on it.

Then, with chess_server.py running in another window:

    python chess_player.py --colour white
    python chess_player.py --colour black

On the real setup those two run on different Raspberry Pis, and each needs
--server pointing at the machine running chess_server.py:

    python3 chess_player.py --colour white --server 192.168.50.100

--------------------------------------------------------------------------------
WHAT IT NEEDS
--------------------------------------------------------------------------------

An Azure speech key, in a .env file in the OhbotPi2 folder — the same one the
Greeter already uses. Nothing new to set up if the Greeter talks.
"""

import argparse
import asyncio
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from chess_needs import require, python_cmd, printable_text
import chess_animation
import chess_dropout
from chess_animation import Animator

# Before anything is printed. See printable_text() — a tick in a success
# message from the Azure code used to kill this program stone dead when it was
# started from a button rather than from its own window.
printable_text()

# Note: nothing here needs the `chess` add-on. This program contains no chess
# logic at all — the server does that. It also does not need python-dotenv:
# yobot_core reads the .env file itself the moment it is imported.
#
# It DOES need the two robot add-ons, and they are checked here rather than
# left to fail during the import below, so the message says `py -m pip` on
# Windows instead of the plain `pip` the Ohbot code suggests.
require("serial", "azure.cognitiveservices.speech")

import chess_ohbot                                          # noqa: E402

# Find OhbotPi2 and put it on the path BEFORE importing anything from it.
# This line is why the imports below work.
OHBOT_FOLDER = chess_ohbot.add_to_path()

import ohbot_pi as ohbot                                    # noqa: E402
from ohbot_azure import AsyncOhbotController, AzureSpeechManager   # noqa: E402


# ── Which robot is which ─────────────────────────────────────────────────────

PORTS = {"white": 8001, "black": 8002}

# The two robots must not sound the same, or the audience hears one machine
# talking to itself instead of two robots arguing. These are Azure voices;
# there are dozens more at
# https://learn.microsoft.com/azure/ai-services/speech-service/language-support
#
# Jenny is what the Greeter uses, so White will sound like the Yobot people
# already know. Guy is a clearly different, lower voice for Black.
#
# ── One voice per robot, per language, added 2026-08-31 ──────────────────────
#
# Jenny is a Microsoft "Multilingual" neural voice — she can speak Spanish in
# the same voice, just with the accent switched by the xml:lang tag that
# ohbot_azure.py already sets from the `language` argument to controller.say().
# So Lester sounds like Lester in both languages with nothing extra.
#
# Guy is an ordinary English-only neural voice with no Spanish mode at all.
# Rather than have Goldie either fall silent or read Spanish text in an
# English accent, he gets a real Spanish voice of his own for Spanish games —
# still male, still clearly not Lester, so the two robots keep sounding like
# two different robots in either language. 'es-MX' matches the Mexican
# Spanish locale ohbot_azure.py already uses for the conversation bot.
VOICE_NAMES = {
    "lester": {"en": "en-US-JennyMultilingualNeural",
               "es": "en-US-JennyMultilingualNeural"},
    "goldie": {"en": "en-US-GuyNeural",
               "es": "es-MX-JorgeNeural"},
}

# The table above is right for a robot-against-robot game, where white is
# always Lester and black is always Goldie. It is wrong the moment a guest
# plays, because then the one robot in the room plays whichever colour the
# guest left it — and Lester playing black would suddenly speak in Goldie's
# voice, in front of people who know him.
#
# So --voice overrides it. The control page passes Lester's voice whichever
# side he ends up on. VOICES below is only the no-guest fallback — the
# ordinary robot-versus-robot game, where colour and robot always match.
VOICES = {
    "white": VOICE_NAMES["lester"],
    "black": VOICE_NAMES["goldie"],
}


def voice_for(colour, lang, voice_identity=None):
    """
    Work out the actual Azure voice name to use.

    `voice_identity` is whatever --voice was given on the command line:
    "lester", "goldie", a raw Azure voice name typed directly, or None (no
    guest — use whichever robot is playing this colour, the usual game).

    `lang` is "en" or "es" — anything else is treated as English. This is
    the ONE place that knows how to turn a robot's identity plus a language
    into a voice name, so nothing else has to.
    """
    lang = lang if lang in ("en", "es") else "en"
    if voice_identity:
        table = VOICE_NAMES.get(voice_identity.strip().lower())
        if table:
            return table.get(lang, table["en"])
        return voice_identity
    return VOICES[colour].get(lang, VOICES[colour]["en"])

# ── Losing a line must not lose the game ─────────────────────────────────────
# Every sentence needs Azure, and Azure needs the internet. Before 2026-09-01 a
# single failed sentence ran all the way out of the game loop and stopped this
# program dead, which on a phone hotspot is a matter of when, not if.
# chess_dropout.py explains the whole thing; this is the one guard both
# speaking functions below go through. Its settings live in that file.
KEEP_TALKING = chess_dropout.KeepTalking()


# How often to ask the server whether it is our turn. Half a second is
# frequent enough to feel responsive and slow enough that two robots do not
# hammer the server between moves.
POLL_SECONDS = 0.5

# How often to print "still here, still waiting" while it is the other
# robot's turn.
#
# WHY THIS EXISTS: with only one robot running, this program correctly waits
# forever for an opponent that does not exist. Printing nothing made that
# look exactly like a crash, and the first person to run it had to ask
# whether it was working. Silence is not the same as calm.
HEARTBEAT_SECONDS = 10

# Give up on the server after this long. Kept short so a wrong address is
# obvious immediately rather than looking like a hang.
REQUEST_TIMEOUT = 10


def ask_server(base_url, command, timeout=REQUEST_TIMEOUT):
    """
    Ask the chess server something and hand back its answer.

    Returns a dictionary, or None if the server could not be reached. Never
    raises — a network hiccup mid-demo must not stop the robot.
    """
    import json

    url = f"{base_url}/move?" + urllib.parse.urlencode({"command": command})
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as err:
        # The server answered, but with a complaint. Its reply is still
        # proper JSON and still worth reading — treating this as "server
        # unreachable" would send you hunting for a network problem that
        # is not there.
        try:
            return json.loads(err.read().decode())
        except Exception:
            return None
    except urllib.error.URLError:
        return None
    except Exception:
        return None


def server_is_there(base_url, timeout=5):
    """
    Is the chess server running and answering?

    Uses /status rather than /move because /move is a real request that
    starts a game or consumes a turn. Asking "are you there" should not
    change anything.
    """
    try:
        with urllib.request.urlopen(f"{base_url}/status", timeout=timeout):
            return True
    except Exception:
        return False


def ask_status(base_url, timeout=5):
    """
    Read the server's status — the whole picture, without changing anything.

    Unlike ask_server above, this touches /status rather than /move, so it
    never starts a game or uses up a turn. Returns None if anything at all
    goes wrong, and every caller must cope with that: a robot which refused
    to start because one extra request failed would be worse than a robot
    that starts with slightly less information.
    """
    import json

    try:
        with urllib.request.urlopen(f"{base_url}/status", timeout=timeout) as reply:
            return json.loads(reply.read().decode())
    except Exception:
        return None


async def speak(controller, text, animator=None, language=None):
    """Say something out loud with the mouth moving.

    `language` is "en" or "es", passed straight through to
    ohbot_azure.AsyncOhbotController.say(). Leaving it out keeps the old
    behaviour (English), so every call written before Spanish existed still
    works unchanged.
    """
    if not text:
        return False
    if animator:
        await animator.announcing()
    try:
        # A lambda, not the coroutine itself: the guard may need a second one
        # for its retry, and a coroutine can only be awaited once. Returns
        # True if the line was actually heard.
        return await KEEP_TALKING.say(
            lambda: controller.say(text, lip_sync=True, language=language),
            text)
    finally:
        if animator:
            await animator.waiting()


async def speak_and_report(controller, base_url, text, animator=None, language=None):
    """
    Say something, then tell the server the floor is free.

    WHY THIS EXISTS. In the first two-robot game the chess was correct and
    the turn order was correct, but the robots talked straight over each
    other. The server flipped the turn the moment it handed out a move, so
    the other robot — polling twice a second — began its own sentence while
    this one was still speaking.

    The server now keeps a "floor": whoever is talking holds it, and the
    other robot is told to wait. This function is the other half of that.
    `controller.say()` does not return until the audio has actually finished
    playing, so the moment it comes back is the moment the mouth stops.

    IF THE MESSAGE DOES NOT GET THROUGH, NOTHING BREAKS. The floor expires on
    its own after SPEAKING_TIMEOUT seconds at the server end. A dropped
    network packet costs a pause, not a stopped demo — which is the right way
    round when there is an audience watching.
    """
    if not text:
        return False
    if animator:
        await animator.announcing()
    try:
        # Through KEEP_TALKING, so a dropped connection costs this one line
        # and nothing else at all. See chess_dropout.py. The floor still goes
        # back below either way — a robot that could not speak must never
        # also silence the other one.
        return await KEEP_TALKING.say(
            lambda: controller.say(text, lip_sync=True, language=language),
            text)
    finally:
        # In a finally block on purpose: if the speech fails half way, the
        # floor still has to be handed back, or this robot's silence would
        # also silence the other one.
        #
        # THE FLOOR GOES BACK BEFORE THE HEAD DOES, and that order is
        # deliberate. Dropping the head takes a moment, and the other robot
        # is sitting there waiting to be allowed to speak. Movement is
        # decoration; the other robot's turn is the show. Nobody will ever
        # notice this robot lowering its head a fraction of a second into
        # its opponent's first word.
        ask_server(base_url, "done_speaking", timeout=3)
        if animator:
            await animator.waiting()


async def connect_robot(colour, quiet=False, voice=None):
    """
    Wake the robot up and get speech ready.

    Returns (controller, azure). Stops the program with a readable
    explanation if anything is missing.
    """
    if not quiet:
        print()
        print("=" * 70)
        print(f"  Yobot — {colour.upper()}")
        print("=" * 70)
        print()
        print(f"  Borrowing robot code from: {OHBOT_FOLDER}")
        print()

    # ── the USB cable ────────────────────────────────────────────────────────
    print("  Connecting to the robot...")
    if not ohbot.init():
        print()
        print("  ROBOT NOT FOUND.")
        print()
        print("  Three things to check, in this order:")
        print()
        print("    1. Is another program already using the cable? The Greeter,")
        print("       the Sequence Builder and Calibration all want it, and")
        print("       only one can have it. Stop them on the Launcher page.")
        print()
        print("    2. Is the USB cable plugged in at both ends?")
        print()
        print("    3. Unplug the cable, wait a moment, plug it back in, and")
        print("       run this again. The serial port sometimes sticks.")
        print()
        raise SystemExit(1)
    print("  Robot connected.")

    print("  Centring the motors...")
    ohbot.reset()
    print("  Motors centred.")

    # ── speech ───────────────────────────────────────────────────────────────
    print("  Setting up Azure speech...")
    try:
        azure = AzureSpeechManager()
    except UnicodeEncodeError as exc:
        # NOT an Azure problem, however much it looks like one. Something
        # printed a character this window cannot show — the ✅ in Azure's own
        # "started successfully" message is the known culprit. Azure was fine;
        # saying the words was what failed.
        #
        # This has its own branch because the general advice below sent
        # Michael hunting through his .env file for a key that was never
        # missing. An error message that points at the wrong thing is worse
        # than no error message at all.
        print()
        print("  A MESSAGE COULD NOT BE PRINTED, AND THAT STOPPED ME.")
        print()
        print(f"  The detail: {exc}")
        print()
        print("  Azure is almost certainly fine — this is Windows being")
        print("  unable to show a character such as a tick in this window.")
        print("  It is a printing fault, not a speech fault.")
        print()
        print("  chess_needs.printable_text() is supposed to prevent this.")
        print("  If you are seeing this, that call has been removed from the")
        print("  top of this file, or something is printing before it runs.")
        print()
        ohbot.close()
        raise SystemExit(1)
    except Exception as exc:
        print()
        print(f"  AZURE SPEECH WOULD NOT START: {exc}")
        print()
        print("  This nearly always means the speech key is missing. It lives")
        print("  in a file called  .env  in the OhbotPi2 folder:")
        print()
        print(f"      {OHBOT_FOLDER}")
        print()
        print("  ...and needs these two lines:")
        print()
        print("      AZURE_SPEECH_KEY=your_key_here")
        print("      AZURE_SPEECH_REGION=eastus")
        print()
        print("  If the Greeter can talk, that file already exists and works.")
        print()
        ohbot.close()
        raise SystemExit(1)

    # A voice given on the command line wins. See VOICE_NAMES above: the
    # robot keeps its own voice whichever colour a guest leaves it.
    #
    # English is only where it STARTS. Since 2026-08-31 the language can be
    # changed while the game runs, so play() asks the server which language
    # the next line is in and calls set_voice() again when the answer
    # changes. This is only what the robot opens its mouth with.
    azure.set_voice(voice or VOICES[colour]["en"])

    controller = AsyncOhbotController(azure)
    await controller.start()
    print("  Speech ready.")

    return controller, azure


async def shut_down(controller, animator=None):
    """Put the robot back to neutral and let go of the cable.

    THE ANIMATOR IS STOPPED FIRST, AND THAT ORDER MATTERS. Every movement is
    posted to a queue inside the controller, and those queues hold ten
    commands. `controller.stop()` shuts down the workers that empty them. An
    animation loop still running at that point posts an eleventh command to a
    queue nobody is emptying any more, and waits for room that is never
    coming.

    That is not a theory — swapping these two lines and shrinking the queues
    hangs every single time. What you would see is a game that finishes, says
    goodbye, prints "robot released", and then just sits there still holding
    the cable, so the next thing you start says "robot not found". Two
    symptoms, neither of them pointing at shutdown.

    Stopping the movement first means there is nothing left to post.
    `test_animation.py` checks this order has not been swapped back.
    """
    print()
    print("  Stopping...")
    if animator is not None:
        try:
            await animator.stop()
        except Exception:
            pass
    try:
        await controller.stop()
    except Exception:
        pass
    try:
        ohbot.reset()
        ohbot.close()
    except Exception:
        pass
    print("  Robot released. The cable is free for other programs.")


# ── The two things this program can do ───────────────────────────────────────

async def say_once(colour, sentence, voice=None, face=None, animate=True, lang="en"):
    """
    Speak one sentence and stop. No chess, no server, no network.

    This is step 4 of the build plan and the first thing to try on new
    hardware. If the mouth moves here, the hard part is done.

    `lang` lets you try the Spanish voice and pronunciation by hand before
    trusting it in front of an audience — e.g.
    `--say-once "Hola, soy Yobot" --lang es`.
    """
    controller, _ = await connect_robot(colour, voice=voice)
    animator = Animator(controller, face=face, enabled=animate)
    try:
        await animator.waiting()
        print()
        print(f"  Saying: \"{sentence}\"")
        print()
        print("  WATCH THE MOUTH. It should move in time with the words.")
        if animate:
            print("  The head should also come up off the board to say it,")
            print("  and go back down afterwards.")
        print()
        spoken = await speak(controller, sentence, animator, language=lang)
        if not spoken:
            print()
            print("  NOTHING WAS SPOKEN. The robot itself is fine — this is")
            print("  the connection to Azure, the only part of this demo that")
            print("  needs the internet. Check that you are online and that")
            print("  the Azure key in the .env file is right, then try again.")
            print()
            return
        print("  Done.")
        print()
        print("  If the mouth moved, the speech layer works and you can go on")
        print("  to a real game. If it spoke without moving, or moved without")
        print("  speaking, stop here and fix that first.")
    finally:
        await shut_down(controller, animator)


async def animate_demo(colour, voice=None, face=None, seconds=30):
    """
    Move, without speaking, so the movement can be tuned on its own.

    Nothing else in this program is involved — no server, no chess, no Azure,
    no speech. Just the robot waiting at the board, with one announcement
    pose in the middle so both states can be seen and compared.

    This exists because tuning movement means running the same thing twenty
    times with slightly different numbers, and doing that through a whole
    game would take an afternoon. The numbers are at the top of
    chess_animation.py.
    """
    controller, _ = await connect_robot(colour, voice=voice)
    animator = Animator(controller, face=face)
    try:
        print()
        print("  WAITING POSE. Head down at the board, eyes and head")
        print("  wandering, an occasional blink, mouth closed.")
        print()
        await animator.waiting()
        await asyncio.sleep(seconds / 4)

        # Walk the whole eye-colour range, so it can be judged in the room it
        # will be performed in. Pretending to win and lose takes two seconds
        # here and about forty minutes in a real game.
        print("  EYE COLOUR. Pretending the game swings from won to lost.")
        print("  (Nothing happens here if this robot has no LED eyes — the")
        print("  commands are sent and the board simply ignores them.)")
        print()
        for pawns, how in ((6, "winning easily"), (2, "a bit ahead"),
                           (0, "level"), (-2, "a bit behind"),
                           (-6, "losing badly")):
            print(f"      {how:16s} {chess_animation.eval_colour(pawns * 100)}")
            await animator.set_eval(pawns * 100)
            await asyncio.sleep(max(1.0, seconds / 20))
        await animator.set_eval(0)
        print()

        print("  ANNOUNCE POSE. Head up towards the audience, drifting")
        print("  gently, eyes blue. The mouth is deliberately still — in a")
        print("  real game the lip sync is driving it, and nothing here")
        print("  touches it.")
        print()
        await animator.announcing()
        await asyncio.sleep(seconds / 4)

        print("  BACK TO WAITING.")
        print()
        await animator.waiting()
        await asyncio.sleep(seconds / 4)

        print("  Done. To change any of this, edit the numbers at the top")
        print("  of chess_animation.py and run this again.")
    except KeyboardInterrupt:
        print()
        print("  Stopped by hand.")
    finally:
        await shut_down(controller, animator)


async def play(colour, base_url, start_game, voice=None, face=None,
               animate=True, lang_override=None):
    """
    Play a whole game: ask, listen, speak, repeat.

    `voice` here is the RAW --voice value from the command line — "lester",
    "goldie", a literal Azure voice name, or None — not yet resolved to an
    actual voice name. It cannot be resolved until we know the language, and
    we do not know that until we can ask the chess server, which we cannot
    do before connecting to the robot below. So: connect with an English
    guess first (a robot needs SOME voice to wake up with), then switch it a
    few lines down the moment the server tells us otherwise. Nothing is
    spoken in between, so nobody ever hears the wrong voice.

    `lang_override` skips asking the server entirely — set by --lang on the
    command line, for testing one robot in Spanish without a Spanish game
    actually running on the server.
    """
    voice_identity = voice
    initial_lang = lang_override or "en"
    controller, azure = await connect_robot(
        colour, voice=voice_for(colour, initial_lang, voice_identity))
    animator = Animator(controller, face=face, enabled=animate)

    print()
    print(f"  Talking to the chess server at {base_url}")

    # ── is the server actually there? ────────────────────────────────────────
    if not server_is_there(base_url):
        print()
        print("  CANNOT REACH THE CHESS SERVER.")
        print()
        print(f"  I tried:  {base_url}")
        print()
        print("  Start it in another window with:")
        print()
        print(f"      {python_cmd()} chess_server.py")
        print()
        print("  If the server is on a different machine, tell me where:")
        print()
        print(f"      {python_cmd()} chess_player.py --colour {colour} "
              f"--server 192.168.50.100")
        print()
        await shut_down(controller, animator)
        raise SystemExit(1)
    print("  Server is there.")

    # ── is a PERSON playing the other side? ──────────────────────────────────
    # Asked once, here, because it changes what the messages below should say.
    # Waiting for a guest to make up their mind is completely normal and must
    # not be reported the same way as waiting for a robot that never started —
    # and the "make the move by hand in a browser" advice is actively wrong
    # when there is a board on screen for them to tap.
    human_plays_other = False
    status = ask_status(base_url)
    if status:
        human_plays_other = status.get("human") == (
            "black" if colour == "white" else "white")
        if status.get("human") == colour:
            print()
            print(f"  A PERSON IS PLAYING {colour.upper()} IN THIS GAME.")
            print()
            print("  That is my colour, so there is nothing for me to do and")
            print("  the server will refuse me. Start me on the other side:")
            print()
            print(f"      {python_cmd()} chess_player.py --colour "
                  f"{'black' if colour == 'white' else 'white'}")
            print()
            await shut_down(controller, animator)
            raise SystemExit(1)
        if human_plays_other:
            print("  A person is playing the other side, on the display.")

    # ── which language, to start with ────────────────────────────────────────
    # The same /status answer already fetched above also carries the language
    # the server is currently writing in, so this costs no extra request. The
    # robot was woken with an English voice a few lines up because it needed
    # some voice to exist; if the server says otherwise, the voice is swapped
    # here, before a single word has been spoken. --lang beats both, so one
    # robot can be tried in Spanish with no Spanish game running at all.
    lang = lang_override or (status.get("lang", "en") if status else "en")
    if lang != initial_lang:
        azure.set_voice(voice_for(colour, lang, voice_identity))
    if lang == "es":
        print("  Language       Spanish")

    def speaking_language():
        """
        Which language to speak the NEXT line in — asked every time.

        This used to be decided once, here at connect time, and never looked
        at again. That was wrong twice over: the person at the control page
        can change the language mid-game now, and a robot that was already
        running when they did would have carried on in the old voice for the
        rest of the show without a word of complaint.

        So it asks the server before every line. That is one small request
        per spoken sentence on the same network, next to a sentence that
        takes several seconds to say out loud — the cost is not measurable,
        and the thing it buys is that the voice can never drift away from
        the words.

        `--lang` on the command line still wins outright, because that flag
        exists precisely for trying one robot on its own with no game
        running to ask.
        """
        nonlocal lang
        if lang_override:
            return lang

        # A short timeout on purpose: this sits between the server handing
        # over a sentence and the robot saying it.
        asked = ask_status(base_url, timeout=2)
        if not asked:
            # No answer. Keep speaking whatever we were speaking rather than
            # falling back to English and changing voice mid-game.
            return lang
        newest = asked.get("lang", lang)
        if newest not in ("en", "es"):
            return lang
        if newest != lang:
            lang = newest
            # Lester's voice speaks both languages, so for him this changes
            # only the accent. Goldie's English voice cannot speak Spanish at
            # all, so for her it is a different voice entirely — which is why
            # this goes through voice_for() rather than a straight swap.
            azure.set_voice(voice_for(colour, lang, voice_identity))
            print(f"  Language changed to "
                  f"{'Spanish' if lang == 'es' else 'English'}.")
        return lang

    # ── start moving ─────────────────────────────────────────────────────────
    # From here until the program ends, this robot is always in one of two
    # states: waiting at the board, or announcing. It starts in waiting, and
    # speak_and_report() flips it back and forth from now on.
    #
    # Started here rather than up in connect_robot() on purpose: everything
    # above this line can still decide to give up and exit, and a robot that
    # has begun idling at the board is a robot somebody will assume is
    # working. It should not start looking alive until it is.
    await animator.waiting()

    if start_game:
        print("  Starting a new game.")
        reply = ask_server(base_url, "start")
        if reply and reply.get("speak"):
            await speak_and_report(controller, base_url,
                                   reply["speak"], animator, language=speaking_language())

    print()
    print("  Playing. Press Ctrl-C to stop.")
    print()

    other = "black" if colour == "white" else "white"
    moves_spoken = 0
    server_missing_since = None
    waiting_since = None
    last_heartbeat = 0.0

    try:
        while True:
            reply = ask_server(base_url, "get_move")

            # ── the server went away ─────────────────────────────────────────
            if reply is None:
                if server_missing_since is None:
                    server_missing_since = time.time()
                    print("  (lost the server — waiting for it to come back)")
                elif time.time() - server_missing_since > 60:
                    print("  Server has been gone for a minute. Stopping.")
                    break
                await asyncio.sleep(2)
                continue

            if server_missing_since is not None:
                print("  (server is back)")
                server_missing_since = None

            # ── who is winning, for the eyes ──────────────────────────────────
            # Done here rather than in each branch below so that EVERY answer
            # from the server keeps the colour honest, including the plain
            # "wait" ones. That is what lets a robot's eyes turn green the
            # moment its opponent blunders, rather than a move later when it
            # is finally handed something to say.
            #
            # The server's number is written from White's point of view. This
            # robot wants to know whether IT is winning, which is not the same
            # thing when it is playing Black.
            await animator.set_eval(
                chess_animation.eval_from_my_side(reply.get("eval_cp"), colour))

            status = reply.get("status")

            if status == "wait":
                # The other robot's turn. Nothing to say — but do not go
                # completely silent, or this looks like a crash.
                now = time.time()
                if waiting_since is None:
                    waiting_since = now
                    last_heartbeat = now
                elif now - last_heartbeat >= HEARTBEAT_SECONDS:
                    last_heartbeat = now
                    seconds = int(now - waiting_since)
                    who = "the person" if human_plays_other else other
                    print(f"  ...waiting for {who} to move  "
                          f"({seconds}s). This is normal — I am fine.")
                    if seconds >= 30 and seconds < 30 + HEARTBEAT_SECONDS:
                        print()
                        if human_plays_other:
                            # No browser URL here on purpose. There is a board
                            # on the display for them to tap, and telling
                            # Michael to play their move for them would take
                            # the guest's turn away from them.
                            print("     Nothing is wrong. A person is playing")
                            print("     this side and I will wait as long as")
                            print("     they need. They move by tapping the")
                            print("     board on the display.")
                        else:
                            print(f"     Nothing is wrong. If no {other} robot is")
                            print(f"     running, I will wait here forever. To make")
                            print(f"     {other}'s move by hand, open this in a browser:")
                            print(f"         {base_url.rsplit(':', 1)[0]}:"
                                  f"{PORTS[other]}/move?command=get_move")
                        print()
                await asyncio.sleep(POLL_SECONDS)
                continue

            if status == "success":
                waiting_since = None
                moves_spoken += 1
                print(f"  {moves_spoken:3d}. {reply.get('move', ''):8s} "
                      f"{reply.get('speak', '')}")
                await speak_and_report(controller, base_url,
                                       reply.get("speak"), animator, language=speaking_language())
                continue

            if status == "game_over":
                print()
                print(f"  GAME OVER — {reply.get('result')}")
                print(f"  {reply.get('speak', '')}")
                await speak_and_report(controller, base_url,
                                       reply.get("speak"), animator, language=speaking_language())
                continue

            if status == "finished":
                print()
                print("  Nothing more to say. The game is complete.")
                break

            # Anything else is an error the server has explained.
            print(f"  Server said: {reply.get('message', status)}")
            if reply.get("speak"):
                await speak_and_report(controller, base_url,
                                   reply["speak"], animator, language=speaking_language())
            await asyncio.sleep(2)

    except KeyboardInterrupt:
        print()
        print("  Stopped by hand.")
    finally:
        await shut_down(controller, animator)


def main():
    parser = argparse.ArgumentParser(
        description="Drive one Yobot in the chess demo",
        epilog="Try --say-once first. It needs no chess server.",
    )
    parser.add_argument("--colour", "--color", dest="colour",
                        default="white", choices=["white", "black"],
                        help="which robot this is (default: white)")
    parser.add_argument("--server", default="localhost",
                        help="machine running chess_server.py "
                             "(default: localhost, this same computer)")
    parser.add_argument("--port", type=int, default=None,
                        help="override the port. Normally worked out from "
                             "the colour: white 8001, black 8002.")
    parser.add_argument("--say-once", nargs="?", const=(
                            "Hello. I am Yobot, and I am about to play some "
                            "chess. Watch my mouth move."),
                        default=None, metavar="SENTENCE",
                        help="say one sentence and stop. No chess server "
                             "needed. Use this to test new hardware.")
    parser.add_argument("--start", action="store_true",
                        help="start a NEW game rather than joining the one "
                             "already in progress. Use it on one robot only.")
    parser.add_argument("--voice", default=None,
                        help="which voice to use: lester, goldie, or an Azure "
                             "voice name. Normally worked out from the colour, "
                             "but when a guest is playing the robot takes "
                             "whichever colour is left over — and it should "
                             "still sound like itself.")
    parser.add_argument("--face", type=float,
                        default=chess_animation.ANNOUNCE_FACE,
                        help=f"where this robot looks when it announces a "
                             f"move. 5 is straight ahead, 3 is right, 7 is "
                             f"left. Default "
                             f"{chess_animation.ANNOUNCE_FACE}. Set it per "
                             f"robot — Lester and Goldie do not sit at the "
                             f"same angle to the audience.")
    parser.add_argument("--no-animation", action="store_true",
                        help="talk without moving anything but the mouth. "
                             "The get-out-of-jail switch: if the movement "
                             "misbehaves five minutes before a show, this "
                             "puts the demo back to how it was.")
    parser.add_argument("--animate-demo", nargs="?", type=int, const=30,
                        default=None, metavar="SECONDS",
                        help="move, without speaking, so the movement can be "
                             "tuned on its own. No chess server, no Azure. "
                             "Change the numbers at the top of "
                             "chess_animation.py and run it again.")
    parser.add_argument("--lang", default=None, choices=("en", "es"),
                        help="which language to speak. For a real game, "
                             "leave this out — the robot asks the chess "
                             "server, which already knows (it was started "
                             "with its own --lang). Only set this by hand "
                             "for --say-once or --animate-demo, which have "
                             "no server to ask.")
    args = parser.parse_args()

    # `voice` stays exactly what was typed — "lester", "goldie", a raw Azure
    # voice name, or None. It used to be resolved to an actual Azure voice
    # name right here, and that is now voice_for()'s job — because the right
    # name depends on the language as well as the robot, and nothing here
    # knows the language yet. play() resolves it once it has asked the
    # server; --say-once and --animate-demo resolve it from --lang instead.
    voice = args.voice

    animate = not args.no_animation

    if args.animate_demo is not None:
        asyncio.run(animate_demo(args.colour,
                                 voice_for(args.colour, args.lang or "en", voice),
                                 args.face, args.animate_demo))
        return 0

    if args.say_once is not None:
        say_lang = args.lang or "en"
        asyncio.run(say_once(args.colour, args.say_once,
                             voice_for(args.colour, say_lang, voice),
                             args.face, animate, lang=say_lang))
        return 0

    port = args.port or PORTS[args.colour]
    base_url = f"http://{args.server}:{port}"
    asyncio.run(play(args.colour, base_url, args.start, voice,
                     args.face, animate, lang_override=args.lang))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print()
        sys.exit(0)
