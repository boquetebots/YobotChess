"""
chess_show.py — the control desk and the audience display, in one program.

WHAT THIS IS FOR
================

Everything else in this project is started by typing commands into black
windows. This is the one thing you double-click. It puts a web page on this
computer with three buttons on it — start the game, start Lester, start
Goldie — and a big 16:9 board for the audience to watch.

    python chess_show.py

Then open a browser at:

    http://localhost:8080/

Press F11 for full screen once the game is running.


THE CHICKEN AND EGG
===================

A web page cannot start a program by itself; something has to already be
running to answer the browser. That something is this file. It is the only
part you start by hand, and it starts everything else for you.

It is the same job the Launcher page does in OhbotPi2.


WHAT IT ACTUALLY STARTS
=======================

    chess_server.py     on this computer  — the brain: Stockfish, the board,
                                            all the commentary
    chess_player.py     on this computer  — White's robot, Lester
    chess_player.py     on the Mac        — Black's robot, Goldie, via the
                                            little listener in
                                            chess_show_agent.py

The Mac is the odd one out. This program cannot reach across the network and
start a program on another machine on its own — nothing over there would be
listening. So a small companion, `chess_show_agent.py`, sits on the Mac doing
nothing but waiting to be told "start Goldie". See SHOW_SETUP.md.

If the Mac agent is not running, everything else still works. You just start
Goldie by hand on the Mac as before, and the Black button reports that it
cannot see the Mac.


WHY THE PAGE ASKS THIS PROGRAM FOR THE BOARD, NOT THE CHESS SERVER
==================================================================

A browser will not let a page loaded from one address fetch data from a
different port — it is a security rule called CORS and it is not optional.
The page is served from port 8080; the chess server lives on 8001.

Rather than loosen that rule, this program fetches the position itself and
passes it on. The page only ever talks to the address it came from, which
needs no special setup, no extra Python add-on, and works the same on every
machine.


NOTHING HERE AFFECTS THE CHESS
==============================

This program starts and stops other programs and reads the position. It never
plays a move, never writes a sentence and never speaks. If it crashes
mid-game the robots carry on without it — you just lose the picture.
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

from chess_needs import require, python_cmd, printable_text

printable_text()          # see chess_needs.py — Windows, pipes and ticks

require("flask")

from flask import Flask, jsonify, request, send_file, send_from_directory


HERE = os.path.dirname(os.path.abspath(__file__))
PAGE_DIR = os.path.join(HERE, "show")

# Where everything lives. White and black have their own chess server ports —
# that is inherited from the old design and is not worth changing. Either one
# can be asked for the position; they share a single game.
DEFAULT_PORT = 8080
WHITE_PORT = 8001
BLACK_PORT = 8002
MAC_AGENT_PORT = 8090

# How long to wait for a reply before giving up. Short on purpose: this runs
# twice a second, and a display that freezes while it waits for a machine
# that has been switched off is worse than a display with a gap in it.
FETCH_TIMEOUT = 1.5
MAC_TIMEOUT = 4.0


# ─────────────────────────────────────────────────────────────────────────────
#  Talking to other programs
# ─────────────────────────────────────────────────────────────────────────────

def fetch_json(url, timeout=FETCH_TIMEOUT):
    """
    Ask another program for something and read the answer.

    Returns None rather than raising if anything at all goes wrong — the
    program is not running yet, the machine is off, the network dropped. The
    display treats "no answer" as "not started", which is what an audience
    would think anyway.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def send_json(url, payload, timeout=FETCH_TIMEOUT):
    """
    Send something to another program and read BOTH the answer and how it
    went — unlike fetch_json above, which quietly turns every failure into
    None.

    That difference matters here. fetch_json is used for the status, where
    "no answer" and "the server said no" mean the same thing to a display:
    show nothing. For a guest's move they mean opposite things. "That is not
    a legal move" needs to reach the board so the square can refuse the tap;
    "the chess server is not running" needs to reach the footer. Collapsing
    the two would leave somebody tapping a board that never responds and no
    way to tell which of the two had happened.

    Gives back (status code, what it said). A status of 0 means nothing
    answered at all.
    """
    data = json.dumps(payload).encode("utf-8")
    request_out = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request_out, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as refused:
        # A refusal IS the answer here — it carries the reason in words.
        try:
            return refused.code, json.loads(refused.read().decode("utf-8"))
        except Exception:
            return refused.code, {"message": "The chess server refused that."}
    except Exception:
        return 0, {"message": "The chess server is not answering."}


def port_is_open(port, host="127.0.0.1"):
    """Is something listening on this port of this machine?"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.4)
        return probe.connect_ex((host, port)) == 0


# ─────────────────────────────────────────────────────────────────────────────
#  Starting and stopping the programs on THIS computer
# ─────────────────────────────────────────────────────────────────────────────

class LocalProcess:
    """
    One program this computer is running, with a button attached to it.

    Keeps the output in memory so that when something fails to start, the
    page can show the actual reason instead of "it did not work".
    """

    def __init__(self, name, command):
        self.name = name
        self.command = command
        self.process = None
        self.output = []
        self.stopped_on_purpose = True    # so a clean stop is not called a crash
        self._lock = threading.Lock()

    def running(self):
        return self.process is not None and self.process.poll() is None

    def died(self):
        """
        Did this program start and then stop on its own?

        Worth asking separately from "is it running". A program that never
        started and one that started and immediately fell over look identical
        on a button, and the second one is the common problem — the robot's
        cable is held by something else, or a key is missing from .env. The
        page uses this to put the reason on screen rather than leaving
        Michael to guess.
        """
        return (self.process is not None
                and self.process.poll() is not None
                and not self.stopped_on_purpose)

    def start(self, extra=()):
        with self._lock:
            if self.running():
                return True, f"{self.name} is already running."

            self.output = []
            self.stopped_on_purpose = False
            full = list(self.command) + list(extra)
            # ── Both ends of the pipe must agree on UTF-8 ────────────────────
            #
            # This is the other half of the bug described in
            # chess_needs.printable_text(), and it is the half that actually
            # bit. On Windows, a program whose output is CAPTURED rather than
            # shown in a window falls back to the old Windows codepage, which
            # has no tick character in it. Lester therefore worked perfectly
            # when started by hand and died on startup when started from the
            # button on this page — with an error blaming the Azure key.
            #
            # PYTHONIOENCODING tells the child to write UTF-8. encoding= tells
            # us to read UTF-8. errors="replace" on our side means that even a
            # program which somehow writes something else prints a question
            # mark in the log instead of taking the show down.
            child_env = dict(os.environ, PYTHONIOENCODING="utf-8")
            try:
                self.process = subprocess.Popen(
                    full,
                    cwd=HERE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    encoding="utf-8",
                    errors="replace",
                    env=child_env,
                )
            except Exception as exc:
                return False, f"Could not start {self.name}: {exc}"

            # Read whatever it prints in the background. Without this the
            # program eventually stops dead when nobody empties the pipe it
            # is writing into — a classic and very confusing hang.
            threading.Thread(target=self._drain, daemon=True).start()
            return True, f"{self.name} started."

    def _drain(self):
        process = self.process
        if process is None or process.stdout is None:
            return
        for line in process.stdout:
            self.output.append(line.rstrip())
            del self.output[:-200]        # keep only the last 200 lines

    def stop(self):
        with self._lock:
            self.stopped_on_purpose = True
            if not self.running():
                self.process = None
                return True, f"{self.name} was not running."

            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Asked nicely, got ignored. This matters more than it sounds:
                # a chess player left holding the robot's USB cable stops the
                # next one from ever starting.
                self.process.kill()
                self.process.wait(timeout=5)
            self.process = None
            return True, f"{self.name} stopped."

    def tail(self, lines=12):
        return self.output[-lines:]


# ─────────────────────────────────────────────────────────────────────────────
#  Starting and stopping Goldie on the Mac
# ─────────────────────────────────────────────────────────────────────────────

class MacPlayer:
    """
    Black's robot, on the other computer.

    All this does is pass the message along to `chess_show_agent.py` running
    over there. If the Mac is off, asleep, or the agent was never started,
    every method here reports that plainly rather than hanging.
    """

    def __init__(self, address):
        self.address = address        # "192.168.50.20:8090", or None

    @property
    def configured(self):
        return bool(self.address)

    def _ask(self, path, timeout=MAC_TIMEOUT):
        if not self.configured:
            return None
        return fetch_json(f"http://{self.address}{path}", timeout=timeout)

    def state(self):
        if not self.configured:
            return {"reachable": False, "running": False,
                    "note": "No Mac address set — start Goldie on the Mac yourself."}
        answer = self._ask("/agent/state", timeout=2.0)
        if answer is None:
            return {"reachable": False, "running": False,
                    "note": f"Cannot see the Mac at {self.address}."}
        answer["reachable"] = True
        return answer

    def start(self, server_host, gap_args):
        answer = self._ask(
            f"/agent/start?server={server_host}&colour=black"
        )
        if answer is None:
            return False, f"Cannot see the Mac at {self.address}."
        return bool(answer.get("ok")), answer.get("message", "")

    def stop(self):
        answer = self._ask("/agent/stop")
        if answer is None:
            return False, f"Cannot see the Mac at {self.address}."
        return bool(answer.get("ok")), answer.get("message", "")


# ─────────────────────────────────────────────────────────────────────────────
#  The web page and its buttons
# ─────────────────────────────────────────────────────────────────────────────

class PretendGame:
    """
    A fake game, for checking what the display LOOKS like.

    Switched on with `--demo`. It plays a famous game to itself, slowly, with
    the clocks running and the bar moving, so you can judge the size of the
    board and whether the names read from the back of the room — without
    Stockfish, without the robots, and without anything to set up.

    It is not connected to anything. No robot ever sees it.
    """

    # Morphy's Opera House game, 1858. Short, famous, and it ends in a
    # checkmate rather than fizzling out, so the ending is worth watching.
    MOVES = ("e4 e5 Nf3 d6 d4 Bg4 dxe5 Bxf3 Qxf3 dxe5 Bc4 Nf6 Qb3 Qe7 "
             "Nc3 c6 Bg5 b5 Nxb5 cxb5 Bxb5+ Nbd7 O-O-O Rd8 Rxd7 Rxd7 "
             "Rd1 Qe6 Bxd7+ Nxd7 Qb8+ Nxb8 Rd8#").split()

    def __init__(self, seconds_per_move=2.5):
        require("chess")
        import chess as chess_module
        self.chess = chess_module
        self.pace = seconds_per_move
        self.started = time.time()

    def snapshot(self):
        import random

        elapsed = time.time() - self.started
        played = min(len(self.MOVES), int(elapsed / self.pace))

        board = self.chess.Board()
        moves = []
        last_uci = None
        for san in self.MOVES[:played]:
            move = board.parse_san(san)
            last_uci = move.uci()
            board.push(move)
            moves.append(san)

        over = board.is_game_over()
        # Whoever moved last is the one still speaking, for about half of
        # each turn — enough to see the highlight come and go.
        mid_turn = (elapsed % self.pace) < (self.pace * 0.55)
        speaker = None
        if played and not over and mid_turn:
            speaker = "black" if board.turn == self.chess.WHITE else "white"

        # A plausible wander, so the bar and the clocks are not frozen.
        random.seed(played)
        swing = 0 if not played else int(120 * (random.random() - 0.35) * played / 6)

        turn = "white" if board.turn == self.chess.WHITE else "black"
        active = speaker or turn
        used = {"white": 0.0, "black": 0.0}
        for index in range(played):
            used["white" if index % 2 == 0 else "black"] += self.pace
        if not over:
            used[active] += elapsed % self.pace

        return {
            "turn": turn,
            "game_over": over,
            "result": board.result() if over else None,
            "resigned_by": None,
            "move_count": played,
            "moves": moves,
            "spoken": [],
            "fen": board.fen(),
            "last_move": last_uci,
            "speaking": speaker,
            "in_check": board.is_check(),
            "clock": {c: round(t, 1) for c, t in used.items()},
            "eval_cp": swing,
            "started": played > 0,
            # Nobody is playing this one — it is a recording. The board on the
            # page will not accept a tap.
            "human": None,
            "robot_colour": "white",
            "your_move": False,
            "legal_moves": [],
            "polite": False,
        }

    def play_human_move(self, move):
        return (False, "This is the scripted demo — nobody is playing. "
                       "Use --demo --human white to try the board yourself.")


class PretendHumanGame:
    """
    A board you can actually play on, with nothing installed.

    Switched on with `--demo --human white`. There is no Stockfish and no
    robot: the opponent simply plays a legal move at random after a short
    pause. The chess is rubbish, and that is not the point — the point is
    being able to sit down with the tablet and find out whether the squares
    are big enough, whether tapping feels right, and whether a promotion
    picker appears where a thumb can reach it.

    Every one of those is a question about the room and the hardware, not
    about chess, and none of them should require setting up an engine and two
    robots to answer.
    """

    # How long the pretend opponent "thinks" for, in seconds. Long enough to
    # see the board refuse a tap while it is not your turn, which is a state
    # worth looking at.
    REPLY_AFTER = 1.6

    def __init__(self, human="white"):
        require("chess")
        import chess as chess_module
        self.chess = chess_module
        self.human = human
        self.robot = "black" if human == "white" else "white"
        self.board = chess_module.Board()
        self.started = None
        self.waiting_since = None
        self.lock = threading.Lock()

    def _colour_now(self):
        return "white" if self.board.turn == self.chess.WHITE else "black"

    def _let_the_opponent_reply(self):
        """
        If it is the pretend opponent's turn and it has had its little think,
        play something. Done here rather than on a timer so there is no extra
        thread to stop.
        """
        import random

        if self.board.is_game_over():
            return
        if self._colour_now() != self.robot:
            return
        if self.waiting_since is None:
            self.waiting_since = time.time()
            return
        if time.time() - self.waiting_since < self.REPLY_AFTER:
            return

        legal = list(self.board.legal_moves)
        if legal:
            # Prefer a capture when one is going, so the demo board does not
            # look completely aimless while you are testing taps.
            captures = [m for m in legal if self.board.is_capture(m)]
            self.board.push(random.choice(captures or legal))
        self.waiting_since = None

    def play_human_move(self, text):
        with self.lock:
            if self.board.is_game_over():
                return False, "The game has finished."
            if self._colour_now() != self.human:
                return False, "It is not your turn yet."
            try:
                move = self.chess.Move.from_uci(str(text).strip().lower())
            except Exception:
                return False, f"'{text}' is not a move I understand."
            if move not in self.board.legal_moves:
                return False, "That is not a legal move."
            self.board.push(move)
            if self.started is None:
                self.started = time.time()
            self.waiting_since = None
            return True, "Played."

    def snapshot(self):
        with self.lock:
            self._let_the_opponent_reply()

            over = self.board.is_game_over()
            turn = self._colour_now()
            my_turn = (not over) and turn == self.human
            moves = []
            replay = self.chess.Board()
            for move in self.board.move_stack:
                moves.append(replay.san(move))
                replay.push(move)

            return {
                "turn": turn,
                "game_over": over,
                "result": self.board.result() if over else None,
                "resigned_by": None,
                "move_count": len(moves),
                "moves": moves,
                "spoken": [],
                "fen": self.board.fen(),
                "last_move": (self.board.move_stack[-1].uci()
                              if self.board.move_stack else None),
                "speaking": None,
                "in_check": self.board.is_check(),
                "clock": {"white": 0.0, "black": 0.0},
                "eval_cp": 0,
                "started": self.started is not None,
                "human": self.human,
                "robot_colour": self.robot,
                "your_move": my_turn,
                "legal_moves": ([m.uci() for m in self.board.legal_moves]
                                if my_turn else []),
                "polite": False,
            }


def build_app(settings):
    app = Flask("chess_show", static_folder=None)

    # --demo on its own replays a famous game so you can look at the display.
    # --demo with --human gives a board you can actually play on, which is a
    # different thing and the one to use when testing a touchscreen.
    if settings.get("demo") and settings.get("human"):
        pretend = PretendHumanGame(settings["human"])
    elif settings.get("demo"):
        pretend = PretendGame()
    else:
        pretend = None

    python = python_cmd()

    # ── These two are MACHINES, not colours ──────────────────────────────────
    #
    # `white` is the robot plugged into THIS computer (Lester). `black_mac` is
    # the robot on the Mac (Goldie). In an ordinary robot-against-robot game
    # the local one plays white and the Mac one plays black, which is why they
    # were named this way — but that is a coincidence of the usual setup, not
    # a rule.
    #
    # It stopped being true the moment a guest could play. A person playing
    # white leaves BLACK for the robot, and the robot that should take it is
    # still Lester, standing right there on the desk. The first version had
    # the colour baked in here, so choosing "a person plays White" quietly
    # went looking for Goldie on a Mac that was not switched on, and the game
    # never started. The colour is now decided at start time, below.
    server = LocalProcess("The chess server", [python, "chess_server.py"])
    white = LocalProcess("The robot on this computer",
                         [python, "chess_player.py"])
    black_mac = MacPlayer(settings["mac"])

    def robot_colour():
        """Which colour the robot on this computer should play."""
        if settings.get("human") == "white":
            return "black"
        return "white"

    # ── the page itself ──────────────────────────────────────────────────────

    @app.route("/")
    def home():
        return send_from_directory(PAGE_DIR, "index.html")

    @app.route("/board")
    @app.route("/play")
    def guest_board():
        """
        The same page with no control bar — what a guest's tablet opens.

        WHY: the tablet gets the identical page to the one on the desk, which
        means it also gets Stop all, the strength menu and the mode selector.
        The bar hides itself after six seconds of stillness, but ANY tap
        brings it back — and a tap is precisely what a guest is about to do.
        One stray thumb ends the game.

        This is the same file, not a copy. The page looks at the address it
        was opened from and leaves the controls out. Keeping it as one file
        matters: two copies of a chessboard would drift apart, and the one
        nobody tests would be the one the guest is using.

        Both /board and /play work, because it is not worth anybody standing
        in a clubhouse trying to remember which.
        """
        return send_from_directory(PAGE_DIR, "index.html")

    @app.route("/photo/<colour>")
    def photo(colour):
        """
        The picture of one robot.

        Michael drops white_player.jpg and black_player.jpg into the Chess
        folder. .png works too. If neither is there the page falls back to a
        drawn placeholder, so a missing photo never leaves a hole.
        """
        if colour not in ("white", "black"):
            return "", 404
        for extension in ("jpg", "jpeg", "png", "webp"):
            candidate = os.path.join(HERE, f"{colour}_player.{extension}")
            if os.path.exists(candidate):
                return send_file(candidate)
        return "", 404

    # ── what is happening right now ──────────────────────────────────────────

    @app.route("/show/state")
    def state():
        """
        Everything the page needs, in one answer, twice a second.

        The page never talks to the chess server directly — see the note at
        the top of this file about CORS.
        """
        game = None
        if pretend is not None:
            game = pretend.snapshot()
        elif port_is_open(WHITE_PORT):
            game = fetch_json(f"http://127.0.0.1:{WHITE_PORT}/status")

        return jsonify({
            "settings": {
                "strength": settings["strength"],
                "gap": settings["gap"],
                "resign_at": settings["resign_at"],
                "mac": settings["mac"],
                "human": settings.get("human"),
                "polite": bool(settings.get("polite")),
                "lang": settings.get("lang", "en"),
            },
            # Files edited since this window was opened. Almost always empty.
            # When it is not, the page says so in large letters, because
            # every minute spent debugging a fix that is sitting unread on
            # the disk is a minute wasted.
            "stale": files_changed_since_start(),
            "programs": {
                "server": {
                    "running": server.running() or port_is_open(WHITE_PORT),
                    "died": server.died(),
                    "log": server.tail(30),
                },
                "white": {
                    "running": white.running(),
                    "died": white.died(),
                    "log": white.tail(30),
                },
                "black": black_mac.state(),
            },
            "game": game,
        })

    # ── the buttons ──────────────────────────────────────────────────────────

    @app.route("/show/server/<action>", methods=["POST", "GET"])
    def server_button(action):
        if action == "start":
            extra = ["--strength", str(settings["strength"]),
                     "--gap", str(settings["gap"]),
                     "--resign-at", str(settings["resign_at"])]
            # Who is playing is decided when the chess server starts, so
            # changing the mode restarts it. The page says so rather than
            # letting you wonder why the board is still untouchable.
            if settings.get("human"):
                extra += ["--human", str(settings["human"])]
            if settings.get("polite"):
                extra += ["--polite"]
            if settings.get("lang"):
                extra += ["--lang", str(settings["lang"])]
            ok, message = server.start(extra)
            if ok:
                # Stockfish takes a moment to wake up. Waiting here means the
                # page never shows a green light for a server that is not
                # actually answering yet.
                for _ in range(40):
                    if port_is_open(WHITE_PORT):
                        break
                    time.sleep(0.25)
            return jsonify({"ok": ok, "message": message})

        if action == "stop":
            ok, message = server.stop()
            return jsonify({"ok": ok, "message": message})

        return jsonify({"ok": False, "message": "Unknown action."}), 400

    @app.route("/show/white/<action>", methods=["POST", "GET"])
    def white_button(action):
        """
        Start or stop the robot on THIS computer.

        The route is called "white" for historical reasons and because that is
        the colour it plays in the usual game. What it actually means is "the
        robot on this desk", and the colour it is given depends on what the
        guest left it.
        """
        if action == "start":
            colour = robot_colour()
            # --voice keeps it sounding like itself. Without this, Lester
            # playing black would speak in Goldie's voice, because the voice
            # used to be chosen from the colour alone.
            ok, message = white.start(["--colour", colour, "--voice", "lester"])
            if ok and settings.get("human"):
                message = f"Started, playing {colour}."
            return jsonify({"ok": ok, "message": message})
        if action == "stop":
            ok, message = white.stop()
            return jsonify({"ok": ok, "message": message})
        return jsonify({"ok": False, "message": "Unknown action."}), 400

    @app.route("/show/black/<action>", methods=["POST", "GET"])
    def black_button(action):
        """Start or stop the robot on the MAC. Not used in a guest's game."""
        if action == "start":
            if settings.get("human"):
                return jsonify({
                    "ok": False,
                    "message": ("Not needed — a person is playing, so only "
                                "the robot on this computer is used."),
                })
            ok, message = black_mac.start(settings["my_address"], settings["gap"])
            return jsonify({"ok": ok, "message": message})
        if action == "stop":
            ok, message = black_mac.stop()
            return jsonify({"ok": ok, "message": message})
        return jsonify({"ok": False, "message": "Unknown action."}), 400

    @app.route("/show/newgame", methods=["POST", "GET"])
    def new_game():
        """
        Start the game itself.

        This goes to WHITE only, on purpose. `--start` on both robots means
        each one resets the other's game and neither gets anywhere. The same
        trap is why HARDWARE_TEST.md says to use --start on one robot only.
        """
        # "newgame", NOT "start". The difference matters: "start" hands the
        # opening sentence back to whoever asked and gives them the speaking
        # floor. That is right for a robot and wrong for a button — this
        # program cannot speak, so the sentence would vanish and the floor
        # would stay held by a robot that was not talking. The game would
        # then sit there doing nothing. See the note in chess_server.py.
        answer = fetch_json(
            f"http://127.0.0.1:{WHITE_PORT}/move?command=newgame", timeout=8.0
        )
        if answer is None:
            return jsonify({"ok": False,
                            "message": "The chess server is not answering."})
        return jsonify({"ok": True, "message": "New game."})

    @app.route("/show/human_move", methods=["POST"])
    def human_move():
        """
        A guest's move, on its way from the board to the chess server.

        WHY THIS EXISTS AT ALL — do not "simplify" it away.

        The page is served from this program on port 8080. The chess server
        is a different program on port 8001. A browser flatly refuses to let
        a page send anything to a different port from the one it came from.
        That is CORS, it is not optional, and it is the same reason /show/state
        exists rather than the page reading /status for itself.

        So the move comes here and this program passes it on. No extra Python
        add-on, no per-machine setup, works identically on every computer.
        Pointing the board at port 8001 will appear to work when you try it
        and will work on nothing.

        The demo board (--demo) has no chess server behind it, so it plays the
        move on its own pretend board instead. That is what makes it possible
        to sit down and try the touchscreen with no robot and no Stockfish.
        """
        incoming = request.get_json(silent=True) or {}
        move = incoming.get("move")

        if not move:
            return jsonify({"ok": False, "message": "No move was sent."}), 400

        if pretend is not None:
            ok, message = pretend.play_human_move(move)
            return jsonify({"ok": ok, "message": message}), (200 if ok else 400)

        status, answer = send_json(
            f"http://127.0.0.1:{WHITE_PORT}/human_move", {"move": move},
            timeout=8.0)

        if status == 0:
            return jsonify({"ok": False,
                            "message": "The chess server is not answering."}), 503

        return jsonify({
            "ok": status == 200,
            # 409 means "not your turn yet", which is not a mistake by the
            # guest — a tap landing while the robot is still thinking is
            # perfectly normal. The board treats it as "try again", not as
            # "that was wrong", so it must stay distinguishable here.
            "wait": status == 409,
            "message": answer.get("message", ""),
            "move_san": answer.get("move_san"),
        }), (200 if status == 200 else status)

    @app.route("/show/settings", methods=["POST"])
    def change_settings():
        """
        Change strength, gap or resign point.

        These are only read when the chess server starts, so changing them
        while a game is running does nothing until you stop and start it.
        The page says so rather than letting you wonder.
        """
        incoming = request.get_json(silent=True) or {}
        for key in ("strength", "gap", "resign_at", "human", "polite", "lang"):
            if key in incoming:
                settings[key] = incoming[key]

        # "" from a dropdown means robot against robot. Turn it into None here
        # so everything downstream only has to understand one way of saying
        # "nobody is playing by hand".
        if settings.get("human") in ("", "none", "None"):
            settings["human"] = None

        # ── Language is the one setting that does NOT wait for a restart ────
        #
        # It used to, and that cost a whole game: Espanol was showing on this
        # bar, the server had been started in English, and the robot spoke
        # English from the first move to the last with nothing on screen
        # admitting it. So whenever the page mentions a language at all, tell
        # the running server, and never mind whether it looks like a change.
        # Working out whether it "changed" meant trusting this program's own
        # idea of what the server was speaking, and being wrong about that is
        # the entire bug — the page saying the word out loud is the only
        # thing here that is actually evidence.
        #
        # Everything else here really is read only at start-up, so the
        # message below still says "stop and start" for those.
        language_now = None
        if "lang" in incoming and port_is_open(WHITE_PORT):
            answer = fetch_json(
                f"http://127.0.0.1:{WHITE_PORT}/language/{settings.get('lang', 'en')}")
            # If the server is too old to know this route, or did not answer,
            # language_now stays None and the page falls back to telling the
            # person to restart — which is what they had to do before.
            if answer:
                language_now = answer.get("lang")

        return jsonify({"ok": True, "settings": settings,
                        "language_now": language_now,
                        "needs_restart": server.running()})

    # ── tidy up ──────────────────────────────────────────────────────────────

    app.stop_everything = lambda: (white.stop(), black_mac.stop(), server.stop())
    return app


# ─────────────────────────────────────────────────────────────────────────────
#  Is this program older than the files it was started from?
# ─────────────────────────────────────────────────────────────────────────────
#
# Added 2026-08-31, after an afternoon was spent hunting a Spanish bug that
# did not exist. The Language dropdown had been fixed, saved, and checked;
# the display showed the new dropdown and the new warning light; and the show
# still spoke English. The reason was that the black window had been left
# open from hours earlier, so the PROGRAM in memory was from before the fix
# while the PAGE was being read off the disk fresh on every reload. Half of
# it was new and half of it was old, and nothing anywhere said so.
#
# Python has no way to pick up an edited file in a program that is already
# running, and it should not try. But it can notice, and say so.

def files_in_memory():
    """
    Every file from this folder that this running program has loaded, and
    the time it was last saved.

    Only files from THIS folder, because those are the ones that get edited.
    chess_server.py and chess_player.py are not in here and do not need to
    be: they are started fresh, as new programs, every time a button on the
    page is pressed, so they are never out of date.
    """
    found = {}
    for module in list(sys.modules.values()):
        path = getattr(module, "__file__", None)
        if not path:
            continue
        path = os.path.abspath(path)
        if os.path.dirname(path) != HERE:
            continue
        try:
            found[os.path.basename(path)] = os.path.getmtime(path)
        except OSError:
            pass
    return found


def files_changed_since_start():
    """
    Which of those files have been SAVED since this program started.

    A second of slack, because file times are not always exact to the moment
    and a false alarm in front of an audience is its own kind of failure.
    """
    now = files_in_memory()
    return sorted(name for name, saved in now.items()
                  if name in LOADED_WHEN_STARTED
                  and saved > LOADED_WHEN_STARTED[name] + 1)


LOADED_WHEN_STARTED = files_in_memory()


def my_own_address():
    """
    This computer's address on the network, as the Mac would have to type it.

    Found by asking the operating system which network card it would use to
    reach the outside world, which is far more reliable than looking up the
    computer's own name.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            return probe.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def main():
    parser = argparse.ArgumentParser(
        description="The control desk and audience display for the robot "
                    "chess match.",
        epilog="Start this, then open http://localhost:8080/ in a browser.",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"port for the display page (default {DEFAULT_PORT})")
    parser.add_argument("--mac", default=os.environ.get("MAC_AGENT", ""),
                        help="where the Mac's listener is, as address:port, "
                             f"e.g. 192.168.50.20:{MAC_AGENT_PORT}. Leave it "
                             "out and you start Goldie on the Mac by hand.")
    parser.add_argument("--strength", default="club",
                        help="how well the robots play (default club)")
    parser.add_argument("--gap", type=float, default=0.8,
                        help="seconds of silence between the robots (default 0.8)")
    parser.add_argument("--resign-at", type=int, default=-900,
                        help="how far behind before a robot gives up "
                             "(default -900). 0 turns resigning off.")
    parser.add_argument("--demo", action="store_true",
                        help="play a pretend game to the screen so you can "
                             "check how the display looks. Needs no robots, "
                             "no Mac and no Stockfish. The buttons still "
                             "work but the picture ignores them.")
    parser.add_argument("--human", choices=("white", "black"), default=None,
                        help="a PERSON plays this colour, on the board on the "
                             "display. With --demo as well you get a board you "
                             "can play on with nothing installed at all, which "
                             "is the way to try the touchscreen.")
    parser.add_argument("--polite", action="store_true",
                        help="leave out the cheekiest lines, which is worth "
                             "doing when a guest is playing")
    parser.add_argument("--lang", default="en", choices=("en", "es"),
                        help="which language the robots speak: en or es "
                             "(default en). The control bar has a dropdown "
                             "for this too — this flag only sets where it "
                             "starts.")
    args = parser.parse_args()

    mac = args.mac.strip()
    if mac and ":" not in mac:
        mac = f"{mac}:{MAC_AGENT_PORT}"

    settings = {
        "strength": args.strength,
        "gap": args.gap,
        "resign_at": args.resign_at,
        "mac": mac,
        "my_address": my_own_address(),
        "demo": args.demo,
        "human": args.human,
        "polite": args.polite,
        "lang": args.lang,
    }

    # ── is a copy of this already running? ──────────────────────────────────
    #
    # Added 2026-08-31, and it cost a whole evening to learn why it is
    # needed. An old copy of this program was left running with no visible
    # window. Starting a new one could not take the port, so the new one fell
    # over — while the browser carried on showing the OLD one, serving a
    # months-old program behind a page read fresh off the disk. Everything
    # looked completely normal. Killing Python in Task Manager did not find
    # it either.
    #
    # Flask's own error for this is "OSError: [WinError 10048] Only one usage
    # of each socket address...", which tells Michael nothing and appears in
    # a window that is about to scroll. So it is caught here instead, and the
    # answer that actually works is printed in words.
    if port_is_open(args.port):
        print()
        print("  ======================================================================")
        print("    THE CHESS SHOW IS ALREADY RUNNING")
        print("  ======================================================================")
        print()
        print(f"    Something is already answering on port {args.port}, so this copy")
        print("    cannot start. It is almost certainly an older copy of this")
        print("    program, left running from earlier.")
        print()
        print("    That matters more than it sounds: the browser page would keep")
        print("    working, served by the OLD program, and any change made since")
        print("    it started would appear to have done nothing at all.")
        print()
        print("    TO FIX IT:")
        print()
        print("      Look for another black window titled 'Yobot Chess' and close")
        print("      it, on every screen. If there is none, open Task Manager")
        print("      (Ctrl+Shift+Esc), go to the DETAILS tab, and end every")
        print("      python.exe AND pythonw.exe. If that still does not do it,")
        print("      restart the computer — that always works.")
        print()
        print(f"    To check whether it is really gone, open  http://localhost:{args.port}/")
        print("    in a browser. Nothing should load.")
        print()
        return 1

    app = build_app(settings)

    print()
    if args.demo and args.human:
        print(f"  DEMO MODE — you play {args.human} on the board on screen.")
        print("  The opponent is not Stockfish and not a robot; it just plays")
        print("  something legal. This is for trying the touchscreen, not the")
        print("  chess.")
        print()
    elif args.demo:
        print("  DEMO MODE — a pretend game, so you can see how it looks.")
        print("  Nothing on screen is real and no robot is involved.")
        print()
    elif args.human:
        print(f"  A person plays {args.human}. Press Start game server, then")
        print("  New game, and tap the board to move.")
        print()
    print("  The chess show is ready.")
    print()
    print(f"      On this computer:   http://localhost:{args.port}/")
    print(f"      From another one:   http://{settings['my_address']}:{args.port}/")
    print()
    print("      A GUEST'S TABLET, with no control buttons on it:")
    print(f"                          http://{settings['my_address']}:{args.port}/board")
    print()
    print("      If the tablet cannot reach it, it is almost always Windows")
    print("      Firewall. Allow Python on PRIVATE networks and try again.")
    print()
    if mac:
        print(f"      Goldie on the Mac:  {mac}")
    else:
        print("      No Mac address given, so the Black button is switched")
        print("      off. Start Goldie on the Mac yourself, or restart this")
        print(f"      with  --mac 192.168.50.20:{MAC_AGENT_PORT}")
    print()
    print("  Press F11 in the browser for full screen. Ctrl-C here to stop.")
    print()

    try:
        app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        # Never leave a robot's cable held by a program nobody can see.
        print("\n  Stopping everything...")
        app.stop_everything()
        print("  Done.")


if __name__ == "__main__":
    # sys.exit so that a refusal to start (a port already in use) leaves a
    # non-zero exit code behind it, rather than looking like a clean finish.
    sys.exit(main())
