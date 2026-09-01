"""
test_human.py — checks a person can play the robot, with nothing plugged in.

    python test_human.py

Silence and a final "no problems" means all is well. It runs in about two
seconds and needs no robot, no browser, and no Stockfish. Where a chess engine
is needed to judge a move, a pretend one is used that gives whatever answer
the test wants — which is better than the real one anyway, because a test that
depends on what Stockfish happens to think today is a test that will start
failing for no reason.

WHAT IT IS ACTUALLY GUARDING
============================

1. **The board only accepts legal moves, from the right person, at the right
   time.** A guest tapping squares is the one part of this whole show that
   takes instructions from a stranger. Everything it is sent must be checked.

2. **A human move is silent.** The robot says nothing when you move. It reacts
   on its own next turn instead. If a human move ever produced a spoken line
   the robot would be reading your own moves back to you, which was the thing
   Michael specifically did not want.

3. **A human never touches the speaking floor.** This is the important one.
   The rule this project learned the hard way is that anything which claims
   the floor must be able to release it — a web page cannot, and neither can
   a person, so a held floor would never come back and the show would stop
   dead. See the note on the newgame command in chess_server.py, which is the
   bug that taught it.

4. **The robot still pounces on a mistake.** The whole point of playing a
   robot rather than a phone app. If the reaction stopped working, everything
   would still look fine — the game would play correctly and dully — so
   nothing but a test would ever catch it.

PUTTING THE BUGS BACK
=====================

A test that has never failed has not been shown to work. Each of these has
been checked by breaking the thing it guards:

  - let play_human_move accept a move when it is not that colour's turn
        -> "a move out of turn is refused" fails
  - have play_human_move call take_floor(colour)
        -> three floor checks fail
  - have play_human_move append a spoken line
        -> "a human move says nothing" fails
  - stop play_human_move setting last_move_was_blunder
        -> "the robot pounces on a human blunder" fails
"""

import sys

from chess_needs import require

require("chess", "flask")

import chess
import chess.engine

import chess_server
import chess_templates
from chess_commentary import CommentaryWriter


PROBLEMS = []


def check(condition, description):
    if condition:
        print(f"  ok    {description}")
    else:
        print(f"  FAIL  {description}")
        PROBLEMS.append(description)


# ─────────────────────────────────────────────────────────────────────────────
# A pretend chess engine
# ─────────────────────────────────────────────────────────────────────────────

class PretendEngine:
    """
    Stands in for Stockfish so these tests need nothing installed.

    `scores` is a list of numbers in hundredths of a pawn, always from White's
    point of view, handed out one per look at the board. That is how the test
    decides what counts as a blunder rather than leaving it to whatever the
    real engine thinks this week.

    When asked to play, it plays the first legal move it can see. Terrible
    chess, entirely predictable, which is what a test wants.
    """

    def __init__(self, scores=()):
        self.scores = list(scores)
        self.asked = 0

    def _next_score(self):
        if self.asked < len(self.scores):
            value = self.scores[self.asked]
        else:
            value = self.scores[-1] if self.scores else 0
        self.asked += 1
        return chess.engine.PovScore(chess.engine.Cp(value), chess.WHITE)

    def analyse(self, board, limit, **kwargs):
        return {"score": self._next_score()}

    def play(self, board, limit, info=None, **kwargs):
        move = next(iter(board.legal_moves))
        return chess.engine.PlayResult(
            move, None, info={"score": self._next_score()})

    def quit(self):
        pass


def new_game(human="white", engine=None, polite=False, **kwargs):
    """A game object wired up for testing, with no real engine behind it."""
    game = chess_server.ChessGame("no-engine-needed", human=human,
                                  resign_at=0, polite=polite, **kwargs)
    game.engine = engine
    return game


def client_for(game, colour):
    """A pretend browser talking to one of the game's two web servers."""
    chess_server.game = game
    return chess_server.build_app(colour).test_client()


# ─────────────────────────────────────────────────────────────────────────────

def test_only_legal_moves():
    print("\nWhat the board will and will not accept")

    game = new_game(human="white")

    check(game.play_human_move("e2e4").get("move_san") == "e4",
          "a legal opening move is accepted")

    check("error" in game.play_human_move("e7e5"),
          "a move for the robot's pieces is refused")

    game2 = new_game(human="white")
    check("error" in game2.play_human_move("e2e5"),
          "a move that piece cannot make is refused")
    check("error" in game2.play_human_move("banana"),
          "something that is not a move at all is refused")
    check("error" in game2.play_human_move(""),
          "an empty move is refused")
    check(len(game2.moves_played) == 0,
          "none of those refusals put anything on the board")

    # A king may not walk into check. This is the rule people get wrong when
    # they try to work out legal moves by hand, which is why the page never
    # does — it is told the legal moves by the chess library.
    game3 = new_game(human="white")
    game3.board.set_fen("4k3/8/8/8/8/8/8/4K2r w - - 0 1")
    check("error" in game3.play_human_move("e1f1"),
          "a king may not move into check")

    print("\nWhose turn it is")

    game4 = new_game(human="white")
    game4.board.push_san("e4")          # now it is the robot's turn
    outcome = game4.play_human_move("e7e5")
    check(outcome.get("wait") is True,
          "a move out of turn is refused, and says to wait")
    check(len(game4.moves_played) == 0,
          "the out-of-turn move did not land on the board")

    print("\nPromotion")

    game5 = new_game(human="white")
    game5.board.set_fen("8/4P3/8/8/8/8/8/4K2k w - - 0 1")
    vague = game5.play_human_move("e7e8")
    check("error" in vague and "which piece" in vague["error"],
          "promoting without saying which piece explains what is missing")
    named = game5.play_human_move("e7e8q")
    check(named.get("move_san", "").startswith("e8=Q"),
          "promoting to a named piece works")


def test_a_human_move_is_silent():
    print("\nA human move says nothing")

    game = new_game(human="white")
    outcome = game.play_human_move("e2e4")

    check("speak" not in outcome,
          "nothing is handed back for a robot to say")
    check(game.spoken_lines == [""],
          "a human move adds no spoken line")
    check(len(game.spoken_lines) == len(game.moves_played),
          "the move list and the spoken list stay the same length")


def test_the_floor_is_never_claimed():
    print("\nThe speaking floor")

    game = new_game(human="white")
    game.play_human_move("e2e4")

    check(game.speaking is None,
          "a human move does not claim the floor")

    # The harder case: the robot is part-way through a sentence when the guest
    # taps the board. The move must land without cutting the robot off, and
    # without stealing the floor from it.
    game2 = new_game(human="white")
    game2.take_floor("black")
    game2.play_human_move("e2e4")

    check(game2.speaking == "black",
          "a human move while the robot is speaking leaves the floor with it")
    check(len(game2.moves_played) == 1,
          "...and the move still lands")

    # And a human can never release a floor it does not hold.
    check(game2.release_floor("white") is False,
          "the human's colour cannot release the robot's floor")


def test_no_robot_on_the_human_side():
    print("\nStarting a robot on the wrong side")

    game = new_game(human="white")
    reply = client_for(game, "white").get("/move?command=get_move")

    check(reply.status_code == 409,
          "a robot asking to play the human's side is turned away")
    check("no white robot" in reply.get_json().get("message", ""),
          "...and told plainly why")
    check(len(game.moves_played) == 0,
          "...and no move was played on the guest's behalf")

    # ...but the New game button must still work. It has always been sent to
    # the WHITE server whichever robot is playing, so a blanket refusal would
    # have quietly broken the button for every game where a guest plays white.
    newgame = client_for(game, "white").get("/move?command=newgame")
    check(newgame.status_code == 200,
          "the New game button still works on the guest's side")

    # The robot's own side still works normally.
    game2 = new_game(human="white", engine=PretendEngine([0]))
    game2.board.push_san("e4")
    reply2 = client_for(game2, "black").get("/move?command=get_move")
    check(reply2.status_code == 200 and reply2.get_json().get("speak"),
          "the robot's own side still gets a move and a line to say")


def test_the_opening_line_goes_to_the_robot():
    print("\nWho speaks first")

    # The guest plays White and so moves first. If the opening line were left
    # for White it would never be collected, and the show would open in
    # silence with a stranger being stared at.
    game = new_game(human="white", engine=PretendEngine([0]))
    client = client_for(game, "black")
    client.get("/move?command=newgame")

    check(game.opening_for == "black",
          "the opening line is left for the robot, not the guest")

    reply = client.get("/move?command=get_move").get_json()
    check(bool(reply.get("speak")),
          "the robot greets the room before anybody has moved")
    check(len(game.moves_played) == 0,
          "...and it is still the guest's move")


def test_what_the_board_page_is_told():
    print("\nWhat the display is told")

    game = new_game(human="white", engine=PretendEngine([0]))
    client = client_for(game, "black")

    state = client.get("/status").get_json()
    check(state["human"] == "white", "the page is told a person plays white")
    check(state["robot_colour"] == "black", "...and that the robot plays black")
    check(state["your_move"] is True, "...and that it is the guest's move")
    check(len(state["legal_moves"]) == 20,
          "the twenty opening moves are offered to the board")
    check("e2e4" in state["legal_moves"], "...including e2e4")

    game.board.push_san("e4")          # now the robot's turn
    state = client.get("/status").get_json()
    check(state["your_move"] is False, "after moving, it is not the guest's turn")
    check(state["legal_moves"] == [],
          "no legal moves are offered while the robot is thinking")

    # A normal two-robot game must be unchanged by all of this.
    plain = new_game(human=None)
    state = client_for(plain, "white").get("/status").get_json()
    check(state["human"] is None, "a robot v robot game says nobody is playing")
    check(state["legal_moves"] == [],
          "...and offers no legal moves to anybody")


def test_the_endpoint():
    print("\nSending a move from the page")

    game = new_game(human="white")
    client = client_for(game, "white")

    good = client.post("/human_move?move=e2e4")
    check(good.status_code == 200 and good.get_json()["move_san"] == "e4",
          "a legal move posted from the page is played")

    game2 = new_game(human="white")
    client2 = client_for(game2, "white")
    bad = client2.post("/human_move?move=e2e5")
    check(bad.status_code == 400, "an illegal move comes back as a refusal")

    game2.board.push_san("e4")
    early = client2.post("/human_move?move=d7d5")
    check(early.status_code == 409,
          "a move out of turn is told to wait, not told it was wrong")

    missing = client2.post("/human_move")
    check(missing.status_code == 400, "no move at all is a refusal")

    # JSON as well as the query string, since the page will use JSON.
    game3 = new_game(human="white")
    as_json = client_for(game3, "white").post("/human_move",
                                              json={"move": "d2d4"})
    check(as_json.status_code == 200 and game3.moves_played == ["d4"],
          "a move sent as JSON works too")


def test_the_game_can_end():
    print("\nEnding the game")

    # Fool's mate, with the guest delivering it. A guest beating the robot in
    # front of the room is the best possible outcome of the whole exercise,
    # and it must end cleanly rather than leaving the robot waiting.
    game = new_game(human="black")
    # After 1. f3 e5 2. g4 — the robot has opened the two worst squares in
    # front of its own king, and it is the guest's move.
    game.board.set_fen(
        "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2")
    outcome = game.play_human_move("d8h4")

    check(outcome.get("game_over") is True, "checkmate by the guest ends the game")
    check(game.result() == "0-1", "...with the guest recorded as the winner")
    check(game.play_human_move("a7a6").get("error"),
          "...and no further moves are accepted")


def test_the_robot_pounces():
    print("\nThe robot reacts to a mistake")

    # Equal, then the guest does something awful: four pawns' worth worse for
    # White in one move. Well past the two-pawn line that counts as a blunder.
    game = new_game(human="white", engine=PretendEngine([0, -400, -400]))
    game.play_human_move("e2e4")

    check(game.last_move_was_blunder is True,
          "a bad human move is spotted as a blunder")

    # Now the robot's turn. Its line should be a punishing one.
    played = game.play_next_move()
    punish_tails = {t.split("{move}")[-1].strip()
                    for t in chess_templates.TEMPLATES["punish"]}
    said = played["spoken"]
    check(any(tail and tail in said for tail in punish_tails),
          f"the robot pounces on a human blunder — it said: {said}")

    # And the opposite: a quiet, sensible move must NOT be treated as one.
    calm = new_game(human="white", engine=PretendEngine([0, 10, 10]))
    calm.play_human_move("e2e4")
    check(calm.last_move_was_blunder is False,
          "a reasonable human move is not called a blunder")


def test_polite_mode():
    print("\nPolite mode")

    sassy = set()
    for lines in chess_templates.TEMPLATES.values():
        sassy |= set(lines[chess_templates.BLOCK_SIZE:chess_templates.BLOCK_SIZE * 2])

    polite = CommentaryWriter(polite=True)
    every_polite_line = {line for lines in polite.templates.values()
                         for line in lines}

    check(not (every_polite_line & sassy),
          "not one sassy line survives into polite mode")
    check(all(len(lines) == chess_templates.BLOCK_SIZE * 3
              for lines in polite.templates.values()),
          "fifteen lines are left in every category")

    normal = CommentaryWriter(polite=False)
    check(any(line in sassy
              for lines in normal.templates.values() for line in lines),
          "the sassy lines are still there in the normal game")
    check(len(chess_templates.TEMPLATES["punish"]) == chess_templates.BLOCK_SIZE * 4,
          "the original bank was not modified by any of this")

    # And the server actually passes the setting through.
    game = new_game(human="white", polite=True)
    check(game.writer.polite is True, "--polite reaches the commentary writer")


def test_strength_dials():
    print("\nStrength settings")

    check(chess_server.parse_strength("gentle") == ("skill", 0),
          "gentle uses the skill dial, which goes below 1320")
    check(chess_server.parse_strength("club") == ("elo", 1600),
          "club still uses the Elo dial")
    check(chess_server.parse_strength("max") == ("elo", None),
          "max means no limit")
    check(chess_server.parse_strength("1800") == ("elo", 1800),
          "a plain number is still an Elo rating")
    check(chess_server.parse_strength("nonsense") is False,
          "a word that is not a level is refused")
    check(chess_server.parse_strength("900") is False,
          "a number below the Elo floor is refused, with advice")

    # The two dials must not be switched on together. Stockfish obeys the Elo
    # one and ignores Skill Level, so asking for the gentlest setting would
    # silently hand the guest a 1320 opponent — visible only as a person who
    # never wins.
    class Recorder:
        def __init__(self):
            self.settings = {}

        def configure(self, values):
            self.settings.update(values)

    skill = Recorder()
    chess_server.apply_strength(skill, ("skill", 0))
    check(skill.settings.get("Skill Level") == 0,
          "the skill level is actually set")
    check(skill.settings.get("UCI_LimitStrength") is False,
          "...and the Elo limiter is switched OFF so it is not overridden")

    elo = Recorder()
    chess_server.apply_strength(elo, ("elo", 1600))
    check(elo.settings.get("UCI_Elo") == 1600, "the Elo is set")
    check(elo.settings.get("UCI_LimitStrength") is True,
          "...and the limiter is switched on, or it would be ignored")

    # An engine that refuses the settings must not stop the show.
    class Awkward:
        def configure(self, values):
            raise RuntimeError("this engine has never heard of that")

    try:
        chess_server.apply_strength(Awkward(), ("skill", 3))
        check(True, "an engine that refuses a strength setting does not crash")
    except Exception:
        check(False, "an engine that refuses a strength setting does not crash")


def main():
    print("Checking a person can play the robot. Nothing needs to be plugged in.")

    test_only_legal_moves()
    test_a_human_move_is_silent()
    test_the_floor_is_never_claimed()
    test_no_robot_on_the_human_side()
    test_the_opening_line_goes_to_the_robot()
    test_what_the_board_page_is_told()
    test_the_endpoint()
    test_the_game_can_end()
    test_the_robot_pounces()
    test_polite_mode()
    test_strength_dials()

    print()
    if PROBLEMS:
        print(f"{len(PROBLEMS)} problem(s):")
        for problem in PROBLEMS:
            print("  " + problem)
        return 1

    print("No problems found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
