"""
test_language.py — checks that picking Español actually changes the language.

    python test_language.py

Silence and a final "No problems" means all is well. Runs in about two
seconds and needs nothing plugged in: no robot, no Mac, no Stockfish, no
Azure, no internet.

WHY THIS FILE EXISTS
====================

A whole game was played at the clubhouse with Español showing on the control
bar and the robot speaking English from the first move to the last.

Nothing was broken in the Spanish itself. The language was a START-UP ONLY
setting, like Strength and Pause: chess_server.py read it once from --lang
and never looked again. So moving the dropdown wrote the choice down, told
nobody who was already running, and left the page showing Español while the
English sentence bank carried on. Worst of all, nothing on screen disagreed
with itself, so there was no way to notice until a robot opened its mouth.

The fix has three parts, and this file checks all three:

1. The sentence bank can be swapped WHILE the server is running
   (CommentaryWriter.set_language).
2. The control page hands the change to the running server the moment the
   dropdown moves (chess_show -> chess_server /language).
3. Starting the server fresh still passes --lang, which is the path that was
   always meant to work — it must not be broken by any of the above.

The robot's own half — asking the server which language to speak before
every line — is not checked here, because importing chess_player.py needs
the robot libraries. It is checked by ear with:

    python chess_player.py --say-once "Hola, soy Yobot" --lang es \
        --colour white --voice lester
"""

import sys
import threading
import time
import urllib.request

from chess_needs import require

require("chess", "flask")

import chess

import chess_commentary
import chess_server
import chess_show


PROBLEMS = []


def check(condition, description):
    if condition:
        print(f"  ok    {description}")
    else:
        print(f"  FAIL  {description}")
        PROBLEMS.append(description)


def spanish(sentence):
    """
    Is this sentence Spanish rather than English?

    Not clever, and it does not need to be. Every line in either bank is a
    full sentence about a chess move, so a handful of words that only ever
    appear in one of the two banks separates them completely.
    """
    lowered = " " + sentence.lower() + " "
    return any(word in lowered for word in
               (" peón", " caballo", " alfil", " torre", " dama", " rey",
                " juego ", " jugué ", " mi jugada", " jaque"))


# ─────────────────────────────────────────────────────────────────────────────

def test_the_bank_can_be_swapped_while_running():
    print("\nThe sentence bank, swapped mid-game")

    board = chess.Board()
    move = board.parse_san("e4")

    writer = chess_commentary.CommentaryWriter()
    first = writer.comment_on(board, move)[0]
    check(not spanish(first), f"starts in English: {first!r}")

    writer.set_language("es")
    second = writer.comment_on(board, move)[0]
    check(spanish(second), f"switches to Spanish: {second!r}")

    writer.set_language("en")
    third = writer.comment_on(board, move)[0]
    check(not spanish(third), "switches back to English again")

    check(writer.set_language("Klingon") == "en",
          "a language nobody has heard of falls back to English, not a crash")


def test_polite_mode_survives_a_language_change():
    print("\nPolite mode, across a language change")

    # Polite mode drops the five Sassy lines from each of the fifteen
    # categories. If a language change rebuilt the bank without reapplying
    # it, the sharp lines would come back on — in front of the guest polite
    # mode was put there to protect.
    polite = chess_commentary.CommentaryWriter(polite=True)
    english_sizes = {name: len(lines) for name, lines in polite.templates.items()}
    polite.set_language("es")
    spanish_sizes = {name: len(lines) for name, lines in polite.templates.items()}

    check(all(size == 15 for size in english_sizes.values()),
          "polite English has 15 lines a category, not 20")
    check(all(size == 15 for size in spanish_sizes.values()),
          "polite Spanish still has 15 a category after the switch")


def test_the_server_can_be_told_mid_game():
    print("\nThe chess server, told while a game is running")

    chess_server.game = chess_server.ChessGame("no-engine-needed", lang="en")
    app = chess_server.build_app("white")
    client = app.test_client()

    check(client.get("/status").get_json()["lang"] == "en",
          "/status reports English to begin with")

    answer = client.get("/language/es").get_json()
    check(answer["lang"] == "es", "/language/es says it is now Spanish")
    check(client.get("/status").get_json()["lang"] == "es",
          "/status agrees — this is what the display reads")
    check(chess_server.game.writer.lang == "es",
          "and the writer really did change bank, not just the label")

    nonsense = client.get("/language/pirate").get_json()
    check(nonsense["lang"] == "en" and nonsense["asked_for"] == "pirate",
          "a typo falls back to English and says what it was asked for")


def test_the_dropdown_reaches_a_running_server():
    print("\nThe control page, with the server already running")

    # This is the exact path that failed at the clubhouse: the server is
    # already up, and the dropdown moves. A real chess server on the real
    # port, spoken to over real HTTP — the point of this test is the wiring
    # between two programs, so faking either end would check nothing.
    chess_server.game = chess_server.ChessGame("no-engine-needed", lang="en")
    server_app = chess_server.build_app("white")
    threading.Thread(
        target=lambda: server_app.run(host="127.0.0.1",
                                      port=chess_show.WHITE_PORT,
                                      debug=False, threaded=True),
        daemon=True,
    ).start()

    for _ in range(40):
        if chess_show.port_is_open(chess_show.WHITE_PORT):
            break
        time.sleep(0.1)
    check(chess_show.port_is_open(chess_show.WHITE_PORT),
          "the pretend chess server came up")

    settings = {"strength": "club", "gap": 0.8, "resign_at": -900, "mac": "",
                "my_address": "127.0.0.1", "demo": False, "human": None,
                "polite": False, "lang": "en"}
    page = chess_show.build_app(settings).test_client()

    answer = page.post("/show/settings", json={"lang": "es"}).get_json()
    check(answer["language_now"] == "es",
          "the page is told, out loud, that it is now speaking Spanish")
    check(chess_server.game.writer.lang == "es",
          "the RUNNING server changed language with no restart at all")

    state = page.get("/show/state").get_json()
    check(state["game"]["lang"] == "es",
          "the display reads Spanish back from the server, not the dropdown")

    page.post("/show/settings", json={"lang": "en"})
    check(chess_server.game.writer.lang == "en", "and back again")


def test_starting_fresh_still_passes_the_language():
    print("\nStarting the server from cold")

    # The old path, which was always correct and must stay correct: the
    # language is handed over on the command line when the server starts.
    started_with = {}

    def remember(self, extra=()):
        started_with[self.name] = list(self.command) + list(extra)
        return True, "pretend"

    real_start, real_running = (chess_show.LocalProcess.start,
                                chess_show.LocalProcess.running)
    real_port_open = chess_show.port_is_open
    chess_show.LocalProcess.start = remember
    chess_show.LocalProcess.running = lambda self: False
    chess_show.port_is_open = lambda port: False
    try:
        settings = {"strength": "club", "gap": 0.8, "resign_at": -900,
                    "mac": "", "my_address": "127.0.0.1", "demo": False,
                    "human": None, "polite": False, "lang": "en"}
        page = chess_show.build_app(settings).test_client()
        page.post("/show/settings", json={"lang": "es", "human": "black",
                                          "polite": True})
        page.get("/show/server/start")
        command = " ".join(next(iter(started_with.values())))
        check("--lang es" in command,
              f"the server is started with --lang es: {command}")
    finally:
        chess_show.LocalProcess.start = real_start
        chess_show.LocalProcess.running = real_running
        chess_show.port_is_open = real_port_open


def main():
    print()
    print("Checking that the Language switch actually changes the language.")

    test_the_bank_can_be_swapped_while_running()
    test_polite_mode_survives_a_language_change()
    test_the_server_can_be_told_mid_game()
    test_the_dropdown_reaches_a_running_server()
    test_starting_fresh_still_passes_the_language()

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
