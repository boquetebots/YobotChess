#!/usr/bin/env python3
"""
test_commentary.py — hear the whole show without any robots
================================================================================

Plays a complete game of chess and prints every single line the robots would
say. No Pi, no Ohbot, no USB cable, no Stockfish needed.

This is how you check the commentary before going anywhere near hardware.
READ THE OUTPUT OUT LOUD. If a line sounds wrong on the page, it will sound
wrong coming out of a robot.

--------------------------------------------------------------------------------
HOW TO RUN IT
--------------------------------------------------------------------------------

    python test_commentary.py                 the Opera Game (short, famous)
    python test_commentary.py --game immortal a game full of sacrifices
    python test_commentary.py --game oddities promotions, castling, en passant
    python test_commentary.py --game all      all three, one after another

    python test_commentary.py --stockfish     let the engine play itself
                                               (needs Stockfish installed)

    python test_commentary.py --stockfish --games 5
                                               play five games and report the
                                               spread. Chess is noisy — one
                                               game tells you very little.

    python test_commentary.py --check         run every game and report only
                                               problems. Say nothing = all good.

The two famous games are used on purpose: they are packed with the things
that used to break — captures by named pieces, checks, castling, and big
sacrifices.
"""

import argparse
import collections
import os
import random
import re
import sys

# Check the chess add-on is installed before going any further, so a missing
# one produces a plain sentence instead of a traceback.
from chess_needs import require
require("chess")

import chess

from chess_commentary import CommentaryWriter, is_dramatic
import chess_templates


# ── Test games ───────────────────────────────────────────────────────────────

GAMES = {
    "opera": {
        "title": "The Opera Game — Morphy vs. Duke of Brunswick, Paris 1858",
        "note": "Short and brutal. Ends in checkmate after a queen sacrifice.",
        "start": None,
        "moves": """
            e4 e5 Nf3 d6 d4 Bg4 dxe5 Bxf3 Qxf3 dxe5 Bc4 Nf6 Qb3 Qe7 Nc3 c6
            Bg5 b5 Nxb5 cxb5 Bxb5+ Nbd7 O-O-O Rd8 Rxd7 Rxd7 Rd1 Qe6 Bxd7+
            Nxd7 Qb8+ Nxb8 Rd8#
        """,
    },
    "immortal": {
        "title": "The Immortal Game — Anderssen vs. Kieseritzky, London 1851",
        "note": "Gives away both rooks, a bishop and the queen. Tests sacrifices.",
        "start": None,
        "moves": """
            e4 e5 f4 exf4 Bc4 Qh4+ Kf1 b5 Bxb5 Nf6 Nf3 Qh6 d3 Nh5 Nh4 Qg5
            Nf5 c6 g4 Nf6 Rg1 cxb5 h4 Qg6 h5 Qg5 Qf3 Ng8 Bxf4 Qf6 Nc3 Bc5
            Nd5 Qxb2 Bd6 Bxg1 e5 Qxa1+ Ke2 Na6 Nxg7+ Kd8 Qf6+ Nxf6 Be7#
        """,
    },
    "oddities": {
        "title": "The awkward squad — set up on purpose",
        "note": "The rare moves neither famous game contains. These are the "
                "ones most likely to come out of a robot sounding wrong.",
        "start": None,
        "scenarios": [
            ("a pawn becomes a queen, and it is mate",
             "7k/1P6/6K1/8/8/8/8/8 w - - 0 1", "b8=Q#"),
            ("a pawn becomes a knight instead, with check",
             "8/4k1P1/8/8/8/8/8/4K3 w - - 0 1", "g8=N+"),
            ("castling, both directions",
             "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1", "O-O O-O-O"),
            ("taking a pawn in passing",
             None, "e4 a6 e5 d5 exd6"),
            ("two knights that could both go to the same square",
             "rnbqkbnr/pppppppp/8/8/5N2/2N5/PPPPPPPP/R1BQKB1R w KQkq - 0 1", "Ncd5"),
            ("two rooks on the same file",
             "4k3/8/8/R7/8/8/8/R3K3 w - - 0 1", "R1a3"),
        ],
    },
}


# ── Things that would sound wrong coming out of a robot ───────────────────────

TROUBLE = [
    (re.compile(r"\s{2,}"),        "two spaces in a row"),
    # The move now announces check and checkmate by itself. If a template
    # says it too, the robot comes out with "checkmate, check!" — which is
    # exactly what happened the first time this was run.
    (re.compile(r"(?:check(?:mate)?\b.*){2,}"), "the word check said twice"),
    (re.compile(r"\bqueen\b.*\bpromotes to (?:knight|rook|bishop)\b"),
     "a template promising a queen when it was not one"),
    (re.compile(r"[/\\&*_~^<>|]"), "a symbol that gets read out loud"),
    (re.compile(r"\d"),            "a digit that should be a word"),
    (re.compile(r"\bto\s+takes\b"), "the old 'rook to takes e1' bug"),
    (re.compile(r"[a-z]\{"),       "an unfilled placeholder"),
    (re.compile(r"\{move\}"),      "an unfilled placeholder"),
    (re.compile(r"\.\s*[A-Z][a-z]+\s+move is"), "a run-on caused by a missing comma"),
]


def inspect(line):
    """Return a list of reasons this line would sound wrong."""
    return [why for pattern, why in TROUBLE if pattern.search(line)]


# ── Running a game ───────────────────────────────────────────────────────────

def _run_moves(board, moves, writer, quiet):
    """Play a list of moves through the commentary writer."""
    spoken = []
    for san in moves.split():
        colour = "WHITE" if board.turn == chess.WHITE else "BLACK"
        try:
            move = board.parse_san(san)
        except ValueError as exc:
            print(f"  !! the test game itself is wrong at '{san}': {exc}")
            break

        line, played, facts = writer.comment_on(board, move)
        board.push(move)
        spoken.append((colour, played, line, facts))

        if not quiet:
            star = " *" if is_dramatic(facts) else "  "
            print(f"{colour}{star} {played:8s} {line}")
    return spoken


def play_scripted(spec, writer, quiet=False):
    """Play a fixed list of moves, or a set of short scenarios."""
    if not quiet:
        print()
        print("=" * 78)
        print(spec["title"])
        print(spec["note"])
        print("=" * 78)

    spoken = []

    # A bundle of short set-ups, each starting from its own position.
    if "scenarios" in spec:
        for label, fen, moves in spec["scenarios"]:
            if not quiet:
                print(f"\n  {label}")
            board = chess.Board(fen) if fen else chess.Board()
            spoken += _run_moves(board, moves, writer, quiet)
        if not quiet:
            print()
        return spoken

    # A whole game from the starting position.
    board = chess.Board(spec["start"]) if spec["start"] else chess.Board()
    if not quiet:
        print()
        print(writer.game_start_line("white"))
        print(writer.game_start_line("black"))
        print()

    spoken += _run_moves(board, spec["moves"], writer, quiet)

    if not quiet:
        print()
        if board.is_game_over():
            result = board.result()
            loser = "black" if result == "1-0" else "white"
            winner = "white" if result == "1-0" else "black"
            print(writer.game_end_line(result, winner))
            print(writer.game_end_line(result, loser))
        else:
            print("(game left unfinished — this test stops early on purpose)")
        print()

    return spoken


def _play_one_engine_game(engine, writer, think, max_moves, resign_at, quiet):
    """
    Play a single Stockfish-versus-Stockfish game.

    Returns (spoken lines, a short description of how it ended).
    """
    import chess.engine
    from chess_server import ResignWatcher, swing_from, EVAL_TIME

    board = chess.Board()
    spoken = []
    watcher = ResignWatcher(resign_at) if resign_at else None
    resigned_by = None
    last_was_blunder = False

    if not quiet:
        print(writer.game_start_line("white"))
        print(writer.game_start_line("black"))
        print()

    while not board.is_game_over():
        if max_moves and len(spoken) >= max_moves:
            break

        colour = "WHITE" if board.turn == chess.WHITE else "BLACK"

        if watcher and watcher.should_resign(colour.lower()):
            resigned_by = colour.lower()
            break

        played_result = engine.play(board, chess.engine.Limit(time=think),
                                    info=chess.engine.INFO_SCORE)
        move = played_result.move
        score_before = (played_result.info or {}).get("score")
        if watcher:
            watcher.record(colour.lower(), score_before)

        # A second, brief look after the move, to see whether it helped
        # or hurt. This is what spots a blunder.
        board.push(move)
        try:
            after = engine.analyse(board, chess.engine.Limit(time=EVAL_TIME))
            swing = swing_from(score_before, after.get("score"), colour.lower())
        except Exception:
            swing = None
        board.pop()

        line, played, facts = writer.comment_on(
            board, move, swing, last_was_blunder)
        last_was_blunder = bool(facts["is_blunder"])
        board.push(move)
        spoken.append((colour, played, line, facts))
        if not quiet:
            star = " *" if is_dramatic(facts) else "  "
            print(f"{colour}{star} {played:8s} {line}")

    # ── how did it end? ──────────────────────────────────────────────────────
    if resigned_by:
        result = "0-1" if resigned_by == "white" else "1-0"
        ending = f"{resigned_by} resigned"
    elif board.is_checkmate():
        result = board.result()
        ending = "checkmate"
    elif board.is_game_over():
        result = board.result()
        ending = "drawn"
    else:
        result = "*"
        ending = f"hit the {max_moves}-move cap"

    if not quiet:
        print()
        print(writer.game_end_line(result, "white", resigned_by))
        print(writer.game_end_line(result, "black", resigned_by))
        print()
        print(f"{ending.capitalize()}. Result: {result}")

    return spoken, ending


def play_with_engine(writer, think=0.05, max_moves=0, strength=("elo", None),
                     resign_at=-900, games=1):
    """
    Let Stockfish play itself. Needs Stockfish installed.

    With `games` above one, plays several and reports the SPREAD rather than
    printing every move. Chess is a noisy business — one game tells you very
    little about whether a setting is any good.
    """
    import chess.engine
    from chess_server import find_stockfish, apply_strength, describe_strength

    path = find_stockfish()
    if not path:
        print("Stockfish is not installed, so --stockfish cannot run.")
        print("The scripted games below need no engine at all — just leave")
        print("off the --stockfish option.")
        return []

    print()
    print("=" * 78)
    print(f"Stockfish playing itself  ({os.path.basename(path)})")
    print(f"Strength: {describe_strength(strength)}"
          f"   Move limit: {max_moves or 'none'}"
          f"   Resigns: {'yes' if resign_at else 'no'}")
    if games > 1:
        print(f"Playing {games} games to see how much they vary.")
    print("=" * 78)
    print()

    everything = []
    rounds = []

    with chess.engine.SimpleEngine.popen_uci(path) as engine:
        # Shared with the real server on purpose. These used to be two
        # separate copies of the same two lines, which meant the tests could
        # quietly measure a different opponent from the one the audience gets.
        apply_strength(engine, strength)

        for number in range(1, games + 1):
            writer.reset()
            spoken, ending = _play_one_engine_game(
                engine, writer, think, max_moves, resign_at, quiet=(games > 1))
            rounds.append((number, spoken, ending))
            everything += spoken

            if games > 1:
                drama = sum(1 for *_, f in spoken if is_dramatic(f))
                mins, secs = divmod(int(speaking_time(spoken)), 60)
                pct = drama * 100 // len(spoken) if spoken else 0
                print(f"  game {number:2d}   {len(spoken):3d} moves   "
                      f"{mins:2d}:{secs:02d}   {pct:2d}% drama   {ending}")

    if games > 1:
        _spread(rounds)

    # One list per game, not one big list. The writer forgets what it has
    # said between games, so a line reused in a later game is correct
    # behaviour and must not be reported as a repeat.
    return [spoken for _, spoken, _ in rounds]


def _spread(rounds):
    """Show how much the games varied, so one result is not read as a trend."""
    lengths = [len(s) for _, s, _ in rounds]
    minutes = [speaking_time(s) / 60 for _, s, _ in rounds]
    dramas = [sum(1 for *_, f in s if is_dramatic(f)) * 100 // len(s)
              for _, s, _ in rounds if s]
    endings = collections.Counter(e for _, _, e in rounds)

    print()
    print("-" * 78)
    print("HOW MUCH DID THEY VARY?")
    print()
    print(f"  moves    {min(lengths):3d} to {max(lengths):3d}"
          f"   (middle {sorted(lengths)[len(lengths)//2]})")
    print(f"  minutes  {min(minutes):4.1f} to {max(minutes):4.1f}"
          f"  (middle {sorted(minutes)[len(minutes)//2]:.1f})")
    if dramas:
        print(f"  drama    {min(dramas):3d}% to {max(dramas):3d}%"
              f"  (middle {sorted(dramas)[len(dramas)//2]}%)")
    print()
    print("  endings:")
    for ending, count in endings.most_common():
        print(f"     {count:2d} x  {ending}")
    print()
    print("  Chess is noisy. If the range above is wide, a single game tells")
    print("  you almost nothing — judge a setting on the middle value.")


# ── Reporting ────────────────────────────────────────────────────────────────

# Roughly how fast a text-to-speech voice gets through words, at a
# comfortable listening pace.
WORDS_PER_SECOND = 2.6

# Everything that happens between one robot finishing and the next starting.
# The first version of this only allowed two seconds and was flattering the
# real pace — it left out the part where Azure has to actually generate the
# audio, which is a round trip to Microsoft's servers on every single line.
OVERHEAD_PER_MOVE = (
    1.0     # Stockfish thinking (the --think setting)
    + 1.0   # Azure turning the sentence into a sound file
    + 0.3   # the Pi asking the server and getting an answer
    + 1.0   # the robot turning its head, and a beat before it speaks
)


def speaking_time(spoken):
    """Roughly how long this game would take to perform, in seconds."""
    words = sum(len(line.split()) for _, _, line, _ in spoken)
    return words / WORDS_PER_SECOND + len(spoken) * OVERHEAD_PER_MOVE


def _template_matchers():
    """
    Build a way of asking "which template produced this sentence?"

    Comparing finished sentences is not enough, and this was found the hard
    way. "My move is pawn takes pawn on e five. Deleted. No recycle bin." and
    "My move is knight takes bishop on d seven. Deleted. No recycle bin." are
    two different sentences, so a plain comparison called them fine — but the
    audience hears the same joke twice, which is the thing we actually care
    about.

    So each template becomes a pattern with the move replaced by "anything",
    and the finished line is matched back against it.

    Longest template first, because "{move}." would otherwise match every
    sentence in the file.
    """
    import re
    everything = list(chess_templates.ANNOUNCE)
    for lines in chess_templates.TEMPLATES.values():
        everything += lines

    matchers = []
    for template in sorted(set(everything), key=len, reverse=True):
        pattern = re.escape(template).replace(r"\{move\}", "(?:.+?)")
        matchers.append((re.compile(pattern + r"\Z", re.IGNORECASE), template))
    return matchers


def which_template(line, matchers):
    """The template a spoken line came from, or None if we cannot tell."""
    for pattern, template in matchers:
        if pattern.match(line):
            return template
    return None


def summarise(games):
    """
    `games` is a list of games, each a list of spoken lines.

    It has to be split up by game rather than being one long list, because
    the writer forgets everything between games. A line used in game one and
    again in game three is not a repeat — nobody in the room heard both.
    """
    spoken = [line for game in games for line in game]
    total = len(spoken)
    dramatic = sum(1 for *_, facts in spoken if is_dramatic(facts))

    # Repeated TEMPLATES, not repeated sentences. See _template_matchers.
    matchers = _template_matchers()
    announcements = set(chess_templates.ANNOUNCE)

    duplicated = []
    announce_repeats = 0
    for game in games:
        used = [which_template(line, matchers) for _, _, line, _ in game]
        for template, n in collections.Counter(t for t in used if t).items():
            if n < 2:
                continue
            if template in announcements:
                # A bare announcement coming round twice is fine, and in a
                # long game it is unavoidable — there are fifty of them and
                # games run past a hundred moves. Nobody notices hearing
                # "your turn" twice. They very much notice hearing the same
                # joke twice, which is what the list below is for.
                announce_repeats += n - 1
            else:
                duplicated.append((n, template))

    problems = []
    for colour, played, line, _ in spoken:
        for why in inspect(line):
            problems.append((colour, played, line, why))

    print("-" * 78)
    print(f"{total} moves spoken.")
    if total:
        seconds = speaking_time(spoken)
        minutes, secs = divmod(int(seconds), 60)
        print(f"About {minutes} min {secs:02d} sec of performance "
              f"— that is how long an audience would be watching.")
        print(f"{dramatic} of them ({dramatic * 100 // total}%) would trigger an "
              f"AI line once step 7 is done.")
    if duplicated:
        print(f"{len(duplicated)} comment(s) used twice in the same game:")
        for n, line in sorted(duplicated, reverse=True)[:5]:
            print(f"    {n}x  {line}")
    else:
        print("No comment was used twice in the same game.")
    if announce_repeats:
        print(f"({announce_repeats} bare announcement(s) came round again. "
              f"That is expected in a long game and is not a problem.)")

    if problems:
        print()
        print(f"{len(problems)} line(s) would sound wrong:")
        for colour, played, line, why in problems:
            print(f"    [{why}]  {colour} {played}: {line}")
    else:
        print("Nothing found that would sound wrong.")
    print("-" * 78)

    return len(problems)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--game", default="opera",
                        choices=list(GAMES) + ["all"],
                        help="which test game to play")
    parser.add_argument("--stockfish", action="store_true",
                        help="let the engine play itself instead")
    parser.add_argument("--strength", default="club",
                        help="with --stockfish: how well to play. gentle, "
                             "friendly, easy, beginner, club, strong, expert, "
                             "max, or an Elo number. Weaker means livelier. "
                             "Default: club.")
    parser.add_argument("--polite", action="store_true",
                        help="leave out the cheekiest lines, as when a guest "
                             "is playing")
    parser.add_argument("--max-moves", type=int, default=0,
                        help="with --stockfish: hard stop after this many "
                             "moves (default: no limit)")
    parser.add_argument("--games", type=int, default=1,
                        help="with --stockfish: play this many games and "
                             "report the spread instead of printing every "
                             "move. Use 5 or more to tell a real difference "
                             "from luck.")
    parser.add_argument("--resign-at", type=int, default=-900,
                        help="with --stockfish: give up when this far behind, "
                             "in hundredths of a pawn (default -900, about a "
                             "queen down). 0 to never resign.")
    parser.add_argument("--think", type=float, default=0.1,
                        help="with --stockfish: seconds of thinking per move")
    parser.add_argument("--check", action="store_true",
                        help="run everything quietly and report only problems")
    parser.add_argument("--seed", type=int, default=None,
                        help="fix the randomness so runs are repeatable")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    writer = CommentaryWriter(polite=args.polite)
    # A list of games, each of which is a list of spoken lines.
    everything = []

    if args.stockfish:
        from chess_server import parse_strength
        strength = parse_strength(args.strength)
        if strength is False:
            return 1
        everything += play_with_engine(writer, think=args.think,
                                       max_moves=args.max_moves,
                                       strength=strength,
                                       resign_at=args.resign_at,
                                       games=args.games)
    elif args.check:
        for name, spec in GAMES.items():
            writer.reset()
            everything.append(play_scripted(spec, writer, quiet=True))
    else:
        names = list(GAMES) if args.game == "all" else [args.game]
        for name in names:
            writer.reset()
            everything.append(play_scripted(GAMES[name], writer))

    problems = summarise(everything)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
