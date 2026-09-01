"""
test_show.py — checks the display without a robot, a Mac, or Stockfish.

    python test_show.py

Silence and a final "no problems" means all is well. This runs in about two
seconds and needs nothing plugged in.

WHAT IT IS ACTUALLY GUARDING
============================

Three things that would be embarrassing in front of an audience and are easy
to get subtly wrong:

1. **The clocks charge the right robot.** A clock that charges both at once,
   or charges the wrong one while the other is speaking, looks broken from
   the back of a room even though the chess is fine.

2. **The evaluation bar does not swap sides every move.** Stockfish reports
   its opinion from the point of view of whoever is to move, so the raw
   number flips sign on every single move. Left alone, the bar would swing
   wildly from end to end all game and mean nothing.

3. **The display survives things not being switched on.** The page is asked
   for the state twice a second whether or not the chess server, White or the
   Mac are running. None of those absences may produce an error.
"""

import os
import sys
import time

from chess_needs import require

require("chess", "flask")

import chess
import chess.engine

import chess_server
import chess_show


PROBLEMS = []


def check(condition, description):
    if condition:
        print(f"  ok    {description}")
    else:
        print(f"  FAIL  {description}")
        PROBLEMS.append(description)


def about(value, expected, slack=0.08):
    """Timing is never exact. Close enough is the only fair test."""
    return abs(value - expected) <= slack


# ─────────────────────────────────────────────────────────────────────────────

def test_clocks():
    print("\nThe clocks")

    # A game with no engine. Nothing below asks it to think, so Stockfish is
    # not needed — the moves are pushed on by hand.
    game = chess_server.ChessGame("no-engine-needed", resign_at=0)
    game._settle_clock()          # start the clock on White, whose turn it is

    time.sleep(0.25)              # White is thinking

    game.board.push_san("e4")     # the turn flips to Black the instant this lands
    game.take_floor("white")      # ...but White is the one now speaking

    check(about(game.clock["white"], 0.25),
          "White is charged for its own thinking time")
    check(about(game.clock["black"], 0.0),
          "Black is not charged while White thinks")

    time.sleep(0.25)              # White is speaking, having already moved
    game.release_floor("white")

    check(about(game.clock["white"], 0.50),
          "White is charged for speaking as well as thinking")
    check(about(game.clock["black"], 0.0),
          "Black is still not charged, even though it is now its turn")

    time.sleep(0.25)              # now Black thinks
    game.board.push_san("e5")
    game.take_floor("black")

    check(about(game.clock["black"], 0.25), "Black is charged for its own go")
    check(about(game.clock["white"], 0.50), "White's clock stopped when it finished")

    total = game.clock["white"] + game.clock["black"]
    check(about(total, 0.75, slack=0.12),
          "the two clocks add up to the time actually elapsed, not double it")

    # The end of the game stops both clocks. Otherwise the loser's clock runs
    # on for as long as the display is left up.
    game.game_over = True
    game._settle_clock()
    frozen = dict(game.clock)
    time.sleep(0.2)
    game._settle_clock()
    check(game.clock == frozen, "both clocks stop when the game is over")


def test_evaluation_never_flips():
    print("\nThe evaluation bar")

    game = chess_server.ChessGame("no-engine-needed", resign_at=0)

    # "300 in favour of whoever is to move", said while White is to move.
    game._remember_eval(chess.engine.PovScore(chess.engine.Cp(300), chess.WHITE))
    check(game.eval_cp == 300, "White ahead reads as a positive number")

    # The identical raw number, said while BLACK is to move, means the exact
    # opposite. This is the flip that would otherwise wreck the bar.
    game._remember_eval(chess.engine.PovScore(chess.engine.Cp(300), chess.BLACK))
    check(game.eval_cp == -300,
          "the same raw score from Black's turn reads as Black ahead")

    # Mate is not a number of pawns. It must not come through as zero or as
    # something that leaves the bar sitting in the middle.
    game._remember_eval(chess.engine.PovScore(chess.engine.Mate(3), chess.WHITE))
    check(game.eval_cp > 5000, "mate for White pins the bar to White's end")

    game._remember_eval(chess.engine.PovScore(chess.engine.Mate(-3), chess.WHITE))
    check(game.eval_cp < -5000, "mate against White pins it to the other end")

    before = game.eval_cp
    game._remember_eval(None)
    check(game.eval_cp == before,
          "an engine that did not answer leaves the bar where it was")


def test_status_has_what_the_display_needs():
    print("\nWhat the chess server hands out")

    game = chess_server.ChessGame("no-engine-needed", resign_at=0)
    chess_server.game = game
    client = chess_server.build_app("white").test_client()

    answer = client.get("/status").get_json()

    for field in ("fen", "turn", "clock", "eval_cp", "speaking",
                  "last_move", "game_over", "moves", "move_count"):
        check(field in answer, f"/status includes {field}")

    check(set(answer.get("clock", {})) == {"white", "black"},
          "there is a clock for each robot")


def test_the_robots_are_told_who_is_winning():
    """
    The eye colour depends on it.

    A robot's eyes show how the game is going for it — green ahead, amber
    level, red behind — and the number comes back on the same reply it
    already gets every time it asks the server anything. The important word
    is EVERY: the plain "wait" answers carry it too, which is what lets a
    robot's eyes turn green the moment its opponent blunders rather than a
    move later.

    Nothing visible breaks if this field goes missing. The robots would keep
    playing and keep talking, and their eyes would simply sit amber all game
    looking entirely deliberate. That is exactly why it is worth a check.
    """
    print("\nTelling the robots who is winning")

    game = chess_server.ChessGame("no-engine-needed", resign_at=0)
    chess_server.game = game
    white = chess_server.build_app("white").test_client()
    black = chess_server.build_app("black").test_client()

    game.eval_cp = 450

    # Black is not to move, so this is a plain "wait" — the reply that
    # matters most and the easiest one to forget.
    waiting = black.get("/move?command=get_move").get_json()
    check(waiting.get("status") == "wait", "black is told to wait")
    check(waiting.get("eval_cp") == 450,
          "a 'wait' reply still says who is winning")

    # And it is always from White's point of view, whoever asked. The robot
    # flips it to its own side itself; a server that flipped it as well would
    # have both robots glowing the same colour and neither of them right.
    for colour, client_ in (("white", white), ("black", black)):
        game.eval_cp = 450
        reply = client_.get("/move?command=get_move").get_json()
        if reply.get("status") == "wait":
            check(reply.get("eval_cp") == 450,
                  f"the {colour} robot is told +450, not flipped for it")


def test_display_survives_nothing_being_on():
    print("\nThe display with nothing switched on")

    settings = {
        "strength": "club", "gap": 0.8, "resign_at": -900,
        "mac": "", "my_address": "127.0.0.1",
    }
    client = chess_show.build_app(settings).test_client()

    page = client.get("/")
    check(page.status_code == 200, "the display page is served")
    check(b"evalbar" in page.data, "the page contains the evaluation bar")

    state = client.get("/show/state")
    check(state.status_code == 200,
          "the state can be read with the chess server switched off")

    body = state.get_json()
    check(body["game"] is None, "no game is reported when nothing is running")
    check(body["programs"]["server"]["running"] is False,
          "the server is correctly reported as not running")
    check(body["programs"]["black"]["reachable"] is False,
          "an absent Mac is reported plainly rather than hanging")

    # A missing photo must be a quiet 404, not a crash. The page is written to
    # cope; this proves the other end agrees.
    check(client.get("/photo/purple").status_code == 404,
          "asking for a photo that cannot exist is refused politely")

    # Pressing New game with no chess server running is the single most
    # likely mistake at a live setup. It must say so, not fall over.
    answer = client.get("/show/newgame").get_json()
    check(answer["ok"] is False and "not answering" in answer["message"],
          "New game with no server running explains itself")

    # The New game button reloads the page. The board redraws from the server
    # twice a second and USUALLY showed the new game on its own, but usually
    # is not good enough for the one button pressed in front of an audience —
    # a manual refresh always worked where the button sometimes did not.
    #
    # The refusal above is why the reload has to be conditional: reloading
    # after a failure would wipe the message explaining what went wrong, and
    # the button would look like it did nothing at all.
    page = page.data.decode("utf-8")
    check("location.reload()" in page,
          "the New game button reloads the page")
    check("if (!answer || answer.ok === false) return;" in page,
          "...but not when the server refused, so the reason stays readable")


def test_the_board_a_guest_can_play_on():
    print("\nThe board a guest plays on")

    settings = {
        "strength": "friendly", "gap": 0.8, "resign_at": -900,
        "mac": "", "my_address": "127.0.0.1",
        "demo": True, "human": "white", "polite": True,
    }
    client = chess_show.build_app(settings).test_client()

    page = client.get("/")
    check(b"promote-choices" in page.data,
          "the page carries a promotion picker")
    check(b"touch-action" in page.data,
          "the board switches off the tablet's double-tap zoom")

    game = client.get("/show/state").get_json()["game"]
    check(game["human"] == "white", "the page is told a person plays white")
    check(game["your_move"] is True, "...and that it is their move")
    check(len(game["legal_moves"]) == 20,
          "...and given the twenty opening moves")

    # A move sent the way the page sends it.
    good = client.post("/show/human_move", json={"move": "e2e4"})
    check(good.status_code == 200 and good.get_json()["ok"] is True,
          "a legal move sent from the page is played")

    after = client.get("/show/state").get_json()["game"]
    check(after["moves"] == ["e4"], "...and appears on the board")
    check(after["your_move"] is False,
          "...after which the board stops accepting taps")

    bad = client.post("/show/human_move", json={"move": "h1h8"})
    check(bad.status_code != 200 and bad.get_json()["ok"] is False,
          "an impossible move is refused")

    nothing = client.post("/show/human_move", json={})
    check(nothing.status_code == 400, "an empty move is refused")

    # The settings the page can change must reach the chess server's command
    # line, or the mode selector would appear to work and change nothing.
    client.post("/show/settings", json={"human": "black", "polite": False})
    echoed = client.get("/show/state").get_json()["settings"]
    check(echoed["human"] == "black", "the mode selector is remembered")
    check(echoed["polite"] is False, "the polite switch is remembered")

    # "" from the dropdown means robot against robot, and must not become the
    # string "" on a command line, where it would be a colour nobody has.
    client.post("/show/settings", json={"human": ""})
    echoed = client.get("/show/state").get_json()["settings"]
    check(echoed["human"] is None,
          "choosing robot v robot clears the human, rather than sending a blank")

    # ── the guest's tablet ────────────────────────────────────────────────
    # Same page, no control bar. A guest holding the tablet is one thumb away
    # from Stop all otherwise, and the bar comes back on any tap — which is
    # exactly what they are about to do.
    for address in ("/board", "/play"):
        tablet = client.get(address)
        check(tablet.status_code == 200, f"{address} serves the board")
        check(tablet.data == page.data,
              f"{address} is the SAME file as the main page, not a copy")

    check(b"GUEST_TABLET" in page.data,
          "the page can tell it is on a guest's tablet")
    check(b"#stage.guest #bar" in page.data,
          "...and leaves the controls out when it is")

    # ── full screen on a phone or tablet ──────────────────────────────────
    # F11 is no use on a device with no keyboard, and the browser's own
    # toolbars eat enough of a phone screen to squeeze the board.
    check(b'id="b-full"' in page.data,
          "there is a fullscreen button")
    check(b"#stage.nofull #b-full" in page.data,
          "...which hides itself where the browser cannot do it at all")
    check(b"Add to Home Screen" in page.data,
          "...and says what to do instead on an iPhone")

    # On a phone, 100vh includes the strip the toolbars sit over, so the
    # bottom of the board hides underneath them. dvh is what is really
    # visible. Kept alongside the vh version, not instead of it, so an older
    # browser behaves exactly as it did before.
    check(b"100dvh" in page.data,
          "the stage is measured against what is actually visible")
    check(b"height: min(56.25vw, 100vh)" in page.data,
          "...with the old measurement left in place for older browsers")

    # And a normal display, with no guest, must be untouched by all of this.
    plain = chess_show.build_app({
        "strength": "club", "gap": 0.8, "resign_at": -900,
        "mac": "", "my_address": "127.0.0.1", "demo": True,
    }).test_client()
    scripted = plain.get("/show/state").get_json()["game"]
    check(scripted["human"] is None,
          "the ordinary demo still says nobody is playing by hand")
    check(scripted["legal_moves"] == [],
          "...and offers no squares to tap")
    refused = plain.post("/show/human_move", json={"move": "e2e4"})
    check(refused.status_code == 400,
          "...and will not accept a move")


def test_the_local_robot_takes_whichever_colour_is_left():
    """
    The bug from the first "a person plays White" game, 2026-08-14.

    The robot on the desk was hard-wired to play white. A guest playing white
    leaves BLACK for the robot — and the display went looking for that robot
    on the Mac, which was not switched on. Nothing moved, and no button on the
    page would have helped, because the one that starts the robot standing
    right there had been hidden.

    The rule this encodes: **the two Start buttons are machines, not colours.**
    """
    print("\nWhich robot plays which colour")

    started = {}

    def build(human):
        settings = {
            "strength": "friendly", "gap": 0.8, "resign_at": -900,
            "mac": "", "my_address": "127.0.0.1", "human": human,
        }
        app = chess_show.build_app(settings)
        return app.test_client()

    real_popen = chess_show.subprocess.Popen

    def watch(*args, **kwargs):
        started["command"] = list(args[0])
        # Run something harmless instead of the real robot.
        return real_popen([sys.executable, "-c", "pass"], **kwargs)

    for human, expected in (("white", "black"), ("black", "white"), (None, "white")):
        started.clear()
        client = build(human)
        chess_show.subprocess.Popen = watch
        try:
            client.post("/show/white/start")
        finally:
            chess_show.subprocess.Popen = real_popen

        command = started.get("command", [])
        pairs = dict(zip(command, command[1:]))
        who = f"a person plays {human}" if human else "robot v robot"
        check(pairs.get("--colour") == expected,
              f"{who}: the robot on this computer is started as {expected}")
        check(pairs.get("--voice") == "lester",
              f"{who}: ...and keeps its own voice rather than the colour's")
        client.post("/show/white/stop")

    # The Mac is not wanted at all in a guest's game, and pressing its button
    # must say so rather than silently trying and failing.
    client = build("white")
    answer = client.post("/show/black/start").get_json()
    check(answer["ok"] is False and "person is playing" in answer["message"],
          "the Mac's button explains that it is not needed for a guest game")

    # And the page must not hide the button that starts the local robot.
    page = client.get("/").data.decode("utf-8")
    check("NAME_LOCAL" in page,
          "the page knows the local robot by name, not only by colour")
    check('if (local) local.style.display = "";' in page,
          "the local robot's Start button is never hidden")


def test_a_tick_in_a_message_cannot_kill_a_robot():
    """
    Lester's startup, 2026-08-14: connected, centred, set up Azure, then died
    with "AZURE SPEECH WOULD NOT START: 'charmap' codec can't encode character
    '\\u2705'". Azure was completely fine. \\u2705 is the tick that Azure's own
    code prints to say it had started SUCCESSFULLY.

    Windows Python does not write UTF-8 by default, and when its output is
    CAPTURED rather than shown in a window it falls back to a codepage with no
    tick in it. So the robot worked when started by hand and died when started
    from the button on the display — and the error blamed the speech key.

    This reproduces the same conditions on any machine by asking for the old
    Windows codepage explicitly. Removing either half of the fix — the
    encoding on the pipe, or PYTHONIOENCODING in the child's environment —
    makes this fail.
    """
    print("\nA decorative character in a message")

    was = os.environ.get("PYTHONIOENCODING")
    os.environ["PYTHONIOENCODING"] = "cp1252"      # pretend to be Windows
    try:
        child = chess_show.LocalProcess("tick test", [
            sys.executable, "-c",
            "print('\\u2705 Azure Speech initialized'); print('ready')",
        ])
        started, _ = child.start()
        check(started, "a program that prints a tick can be started")

        for _ in range(40):
            if not child.running():
                break
            time.sleep(0.05)

        printed = "\n".join(child.tail(10))
        check("ready" in printed,
              "it runs to the end instead of dying on the tick")
        check("✅" in printed,
              "and the tick arrives intact in the log")
        check(child.process.poll() == 0,
              "it finishes cleanly, so nothing reports it as crashed")

        # ── the other half of the fix, which cannot be proved by running ────
        # There are two ends to this pipe. The check above proves the CHILD
        # writes UTF-8. Proving that WE read it as UTF-8 only shows up on
        # Windows, because Linux and macOS read UTF-8 by default whatever we
        # ask for — so removing that half breaks Michael's PC and nothing
        # else, which is precisely the kind of fault that gets shipped.
        #
        # So look at how the pipe is actually asked for, rather than at what
        # comes out of it.
        opened = {}
        real_popen = chess_show.subprocess.Popen

        def watch(*args, **kwargs):
            opened.update(kwargs)
            return real_popen(*args, **kwargs)

        chess_show.subprocess.Popen = watch
        try:
            watched = chess_show.LocalProcess(
                "encoding test", [sys.executable, "-c", "pass"])
            watched.start()
            for _ in range(40):
                if not watched.running():
                    break
                time.sleep(0.05)
        finally:
            chess_show.subprocess.Popen = real_popen

        check(opened.get("encoding") == "utf-8",
              "the pipe is opened asking for UTF-8, which is what Windows needs")
        check(opened.get("errors") == "replace",
              "an odd character prints as a question mark instead of crashing")
        check(opened.get("env", {}).get("PYTHONIOENCODING") == "utf-8",
              "and the child is told to write UTF-8 too")
    finally:
        if was is None:
            os.environ.pop("PYTHONIOENCODING", None)
        else:
            os.environ["PYTHONIOENCODING"] = was


def test_new_game_button_does_not_hold_the_floor():
    """
    The bug that stopped the first real game dead, 2026-08-13.

    The button used to send "start", which is the command a ROBOT sends. That
    command hands back the opening sentence and claims the speaking floor for
    whoever asked, because a robot is about to say it. A web page cannot say
    anything and never reports back, so the floor sat held by a robot that
    was silent, and the clock ticked away with nothing happening.

    Symptom on the day: White's clock counting up, no moves, no speech.
    """
    print("\nThe New game button")

    game = chess_server.ChessGame("no-engine-needed", resign_at=0)
    chess_server.game = game
    client = chess_server.build_app("white").test_client()

    answer = client.get("/move?command=newgame").get_json()
    check(answer["status"] == "success", "a new game can be started from a button")
    check(answer["speak"] is None,
          "the button is not handed a sentence it cannot say")
    check(game.speaking is None,
          "no robot is left holding the floor after the button is pressed")
    check(game.floor_is_busy("white") is False,
          "White is free to speak straight away")
    check(game.floor_is_busy("black") is False,
          "Black is free to speak straight away")

    # The opening line is not lost — it is waiting for the first robot that
    # asks, which is the whole point of doing it this way.
    reply = client.get("/move?command=get_move").get_json()
    check(reply["status"] == "success" and reply["speak"],
          "the first robot to ask is given the opening line")
    check(game.speaking == "white",
          "and it takes the floor properly, because it really is speaking")
    check("move" not in reply,
          "the opening line is a greeting, not a move")

    client.get("/move?command=done_speaking")
    check(game.speaking is None, "the floor is released when it stops talking")

    # Second time round there is no greeting left, so it gets on with the game.
    game2 = chess_server.ChessGame("no-engine-needed", resign_at=0)
    chess_server.game = game2
    client2 = chess_server.build_app("white").test_client()
    client2.get("/move?command=newgame")
    client2.get("/move?command=get_move")
    check(game2.opening_for is None, "the opening line is only handed out once")


def test_it_notices_its_own_program_is_out_of_date():
    print("\nNoticing that the program in memory is older than the disk")

    # Python cannot reload a file it is already running. This is the check
    # that at least makes it say so — added after an afternoon was lost to a
    # Spanish fix that had been saved, and checked, and was simply not
    # running, because the black window had been open since before it was
    # written. The page is read off the disk on every refresh, so it looked
    # completely new while the program underneath it was hours old.
    #
    # No file is touched here. Pretending this program started long ago is
    # the same test and cannot leave anything behind.
    check("chess_show.py" in chess_show.files_in_memory(),
          "it knows chess_show.py is one of its own files")
    check(chess_show.files_changed_since_start() == [],
          "nothing looks out of date when nothing is")

    remembered = chess_show.LOADED_WHEN_STARTED
    chess_show.LOADED_WHEN_STARTED = {name: when - 3600
                                      for name, when in remembered.items()}
    try:
        check("chess_show.py" in chess_show.files_changed_since_start(),
              "a file saved since start-up is named")

        settings = {"strength": "club", "gap": 0.8, "resign_at": -900,
                    "mac": "", "my_address": "127.0.0.1", "demo": True,
                    "human": None, "polite": False, "lang": "en"}
        page = chess_show.build_app(settings).test_client()
        state = page.get("/show/state").get_json()
        check("chess_show.py" in state.get("stale", []),
              "and the display is told, so it can say so in large letters")
    finally:
        chess_show.LOADED_WHEN_STARTED = remembered

    check(chess_show.files_changed_since_start() == [],
          "and it goes quiet again once the program is up to date")


def main():
    print()
    print("Checking the chess display. No robot, no Mac and no Stockfish needed.")

    test_clocks()
    test_evaluation_never_flips()
    test_status_has_what_the_display_needs()
    test_the_robots_are_told_who_is_winning()
    test_new_game_button_does_not_hold_the_floor()
    test_display_survives_nothing_being_on()
    test_the_board_a_guest_can_play_on()
    test_the_local_robot_takes_whichever_colour_is_left()
    test_a_tick_in_a_message_cannot_kill_a_robot()
    test_it_notices_its_own_program_is_out_of_date()

    print()
    if PROBLEMS:
        print(f"{len(PROBLEMS)} problem(s):")
        for problem in PROBLEMS:
            print(f"  - {problem}")
        print()
        sys.exit(1)

    print("No problems.")
    print()


if __name__ == "__main__":
    main()
