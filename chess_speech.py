#!/usr/bin/env python3
"""
chess_speech.py — turning a chess move into words a robot can say
================================================================================

ONE JOB: take a chess move and give back a sentence a robot can speak, in
English or in Spanish.

    "Nf3"    ->  "knight to f three"            /  "caballo a efe tres"
    "Rxe1"   ->  "rook takes bishop on e one"   /  "torre captura alfil en e uno"
    "O-O"    ->  "castles kingside"             /  "enroca corto"
    "e8=Q+"  ->  "pawn to e eight, promotes to queen, check"
                 "peón a e ocho, corona dama, jaque"

--------------------------------------------------------------------------------
WHY THIS FILE EXISTS
--------------------------------------------------------------------------------

The 2025 version did this by chopping up the text of the move. It looked at
"Rxe1", saw the R at the front, swapped it for "rook to ", then swapped the x
for " takes ". The result was:

    "rook to  takes e1"

Two spaces, and the word the audience actually cares about is missing. Every
capture by a named piece came out broken, and captures happen several times a
minute.

This version never touches the text of the move. It asks the chess library
what piece is moving, where it is going, and what it is capturing. There is
nothing to chop up, so there is nothing to get wrong. The same is true in
Spanish — one piece of logic, walking the same facts, just reading them out
in a different language at the end.

--------------------------------------------------------------------------------
THE ONE THING TO KNOW IF YOU EDIT THIS
--------------------------------------------------------------------------------

`board` must be the position BEFORE the move is played. That is the only way
to find out what piece is standing on the destination square about to be
captured — once the move is played, that piece is gone and the information is
lost forever.

--------------------------------------------------------------------------------
ADDING SPANISH, 2026-08-31
--------------------------------------------------------------------------------

Everything that used to be one dictionary (PIECE_NAMES, DIGIT_WORDS, ...) is
now one dictionary PER LANGUAGE, keyed "en" or "es". `lang="en"` on every
public function keeps every existing call working exactly as it did before —
nothing had to change at any call site that does not care about Spanish.

Unlike English, Spanish has no "a means the article, not the letter" problem
— the Spanish word "a" is a preposition pronounced exactly like the letter's
own name, so there is nothing to work around there. But single letters said
in isolation are still worth spelling out properly ("efe" for f, "hache" for
h) rather than trusting Azure to guess right on a bare letter, the same
caution that produced the "ay" fix for English "a". This has NOT yet been
checked against real hardware in Spanish — do that before a show, the way the
English "a" problem was only found by listening to Lester. If a letter comes
out wrong, fix its spelling in FILE_SPOKEN["es"] below; nothing else needs to
change.

--------------------------------------------------------------------------------
TESTING IT
--------------------------------------------------------------------------------

No robot needed. Run it and it checks itself, in both languages:

    python chess_speech.py
"""

from chess_needs import require
require("chess")

import chess


def _lang(lang):
    """Normalise a language argument. Anything unrecognised is English."""
    return "es" if lang == "es" else "en"


# ── How each piece is announced ──────────────────────────────────────────────
# Edit these if you want different words. "pawn"/"peón" is here for
# completeness but pawns are usually announced by their square alone.

PIECE_NAMES = {
    "en": {
        chess.PAWN:   "pawn",
        chess.KNIGHT: "knight",
        chess.BISHOP: "bishop",
        chess.ROOK:   "rook",
        chess.QUEEN:  "queen",
        chess.KING:   "king",
    },
    "es": {
        chess.PAWN:   "peón",
        chess.KNIGHT: "caballo",
        chess.BISHOP: "alfil",
        chess.ROOK:   "torre",
        chess.QUEEN:  "dama",
        chess.KING:   "rey",
    },
}

# Squares are announced as "e four" / "e cuatro", not "e4". Text-to-speech
# usually gets this right on its own, but spelling it out costs nothing and
# removes any chance of the robot saying "e-four" like a spreadsheet cell.

DIGIT_WORDS = {
    "en": {
        "1": "one", "2": "two", "3": "three", "4": "four",
        "5": "five", "6": "six", "7": "seven", "8": "eight",
    },
    "es": {
        "1": "uno", "2": "dos", "3": "tres", "4": "cuatro",
        "5": "cinco", "6": "seis", "7": "siete", "8": "ocho",
    },
}

# ── The a-file problem (English only) ────────────────────────────────────────
# Heard on real hardware 2026-08-13: the robots said "knight to UH three"
# instead of "knight to AY three".
#
# A lone "a" in an ENGLISH sentence is the English article, and that is how
# Azure reads it — "uh". Every other file letter is safe, because a lone "b",
# "c", "e" and so on are not English words, so Azure spells them out as
# letters and gets them right. Only "a" is ambiguous, and Azure always
# guesses the wrong one in English.
#
# The fix is to spell it the way it sounds. "ay" is a word Azure knows and
# says as /eɪ/, which is exactly the letter name we want.
#
# WHY IT IS DONE HERE and not in the Azure pronunciation table in OhbotPi2:
# that table matches whole words, so an entry for "a" would change every
# article in every sentence the robot ever says — "uh knight" would become
# "AY knight". This file knows the difference, because here an "a" is always
# a square on a chessboard and never an article.
#
# SPANISH DOES NOT HAVE THIS PROBLEM. The Spanish word "a" is a preposition
# pronounced exactly like the letter's own name, so a bare "a" already comes
# out right. Spanish spells out every file letter by its full letter name
# instead ("efe" for f, "hache" for h) for the same reason chess players
# reading a game aloud do — a single stray consonant is easy to mishear on a
# quiet PA system, a whole letter name is not.
FILE_SPOKEN = {
    "en": {
        "a": "ay",   # the only one that needs help
        "b": "b", "c": "c", "d": "d",
        "e": "e", "f": "f", "g": "g", "h": "h",
    },
    "es": {
        "a": "a", "b": "be", "c": "ce", "d": "de",
        "e": "e", "f": "efe", "g": "ge", "h": "hache",
    },
}

FILE_WORDS = {
    "en": {letter: f"{spoken}-file" for letter, spoken in FILE_SPOKEN["en"].items()},
    "es": {letter: f"columna {spoken}" for letter, spoken in FILE_SPOKEN["es"].items()},
}


def say_square(square, lang="en", spell_digits=True):
    """Turn a square number into spoken words.

    e4 -> 'e four' / 'e cuatro'      a3 -> 'ay three' / 'a tres'
    """
    lang = _lang(lang)
    name = chess.square_name(square)          # e.g. "e4"
    letter, digit = name[0], name[1]
    if spell_digits:
        return f"{FILE_SPOKEN[lang][letter]} {DIGIT_WORDS[lang][digit]}"
    return name


def describe_move(board, move, lang="en", name_the_victim=True, spell_digits=True):
    """
    Describe one chess move in plain words.

    board            the position BEFORE the move is played
    move             the move itself
    lang             "en" or "es". Anything else is treated as English.
    name_the_victim  say "takes rook on e one" / "captura torre en e uno"
                     instead of just naming the square. Better theatre — the
                     audience hears what was lost.
    spell_digits     say "e four" instead of "e4"

    Returns a string like "queen takes rook on d five, check" or
    "dama captura torre en d cinco, jaque".
    """
    lang = _lang(lang)

    # ── Castling is a special case and reads as its own phrase ───────────────
    if board.is_kingside_castling(move):
        phrase = "castles kingside" if lang == "en" else "enroca corto"
        return _add_check_suffix(board, move, phrase, lang)
    if board.is_queenside_castling(move):
        phrase = "castles queenside" if lang == "en" else "enroca largo"
        return _add_check_suffix(board, move, phrase, lang)

    moving_piece = board.piece_at(move.from_square)
    if moving_piece is None:
        # Should never happen with a legal move, but never crash the show.
        return "makes a move" if lang == "en" else "hace un movimiento"

    mover = PIECE_NAMES[lang][moving_piece.piece_type]
    destination = say_square(move.to_square, lang, spell_digits)

    # ── Is this a capture, and of what? ──────────────────────────────────────
    if board.is_capture(move):
        if board.is_en_passant(move):
            # The captured pawn is NOT on the destination square, which is
            # exactly the trap the old code fell into.
            if lang == "en":
                phrase = f"{mover} takes on {destination}, en passant"
            else:
                phrase = f"{mover} captura al paso en {destination}"
        else:
            victim_piece = board.piece_at(move.to_square)
            victim = (PIECE_NAMES[lang][victim_piece.piece_type]
                      if victim_piece else None)
            if lang == "en":
                if name_the_victim and victim:
                    phrase = f"{mover} takes {victim} on {destination}"
                else:
                    phrase = f"{mover} takes {destination}"
            else:
                if name_the_victim and victim:
                    phrase = f"{mover} captura {victim} en {destination}"
                else:
                    phrase = f"{mover} captura en {destination}"
    else:
        # A quiet move. Only add "on b" style detail when it is genuinely
        # needed to tell two identical pieces apart.
        disambiguation = _disambiguation(board, move, moving_piece, lang)
        if lang == "en":
            if disambiguation:
                phrase = f"{mover} {disambiguation} to {destination}"
            else:
                phrase = f"{mover} to {destination}"
        else:
            if disambiguation:
                phrase = f"{mover} {disambiguation} a {destination}"
            else:
                phrase = f"{mover} a {destination}"

    # ── Promotion ────────────────────────────────────────────────────────────
    if move.promotion:
        if lang == "en":
            phrase += f", promotes to {PIECE_NAMES[lang][move.promotion]}"
        else:
            phrase += f", corona {PIECE_NAMES[lang][move.promotion]}"

    return _add_check_suffix(board, move, phrase, lang)


def _disambiguation(board, move, moving_piece, lang="en"):
    """
    Work out whether we need to say WHICH piece moved.

    If both knights can reach d2, "knight to d two" is ambiguous and a
    listener following on a real board will lose track. In that case we say
    "knight on b-file to d two" / "caballo de la columna be a de dos".

    Most of the time no extra words are needed, and we return "" so the
    announcement stays short.
    """
    lang = _lang(lang)
    if moving_piece.piece_type in (chess.PAWN, chess.KING):
        return ""   # only ever one king; pawns are named by their file already

    # Find other pieces of the same type that could also land on this square.
    rivals = [
        other.from_square
        for other in board.legal_moves
        if other.to_square == move.to_square
        and other.from_square != move.from_square
        and board.piece_at(other.from_square) is not None
        and board.piece_at(other.from_square).piece_type == moving_piece.piece_type
        and board.piece_at(other.from_square).color == moving_piece.color
    ]

    if not rivals:
        return ""

    from_file = chess.square_file(move.from_square)
    from_rank = chess.square_rank(move.from_square)

    # Prefer naming the file ("the knight on the b-file"), which is how
    # chess players actually speak. Fall back to the rank if the file does
    # not separate them.
    if all(chess.square_file(r) != from_file for r in rivals):
        letter = chess.square_name(move.from_square)[0]
        return (f"on the {FILE_WORDS['en'][letter]}" if lang == "en"
                else f"de la {FILE_WORDS['es'][letter]}")

    if all(chess.square_rank(r) != from_rank for r in rivals):
        digit = chess.square_name(move.from_square)[1]
        return (f"on rank {DIGIT_WORDS['en'][digit]}" if lang == "en"
                else f"de la fila {DIGIT_WORDS['es'][digit]}")

    # Extremely rare (three queens). Name the whole square.
    square = say_square(move.from_square, lang)
    return f"on {square}" if lang == "en" else f"de {square}"


def _add_check_suffix(board, move, phrase, lang="en"):
    """Add ', check' / ', jaque', or ', checkmate' / ', jaque mate'."""
    lang = _lang(lang)
    board.push(move)
    try:
        if board.is_checkmate():
            return phrase + (", checkmate" if lang == "en" else ", jaque mate")
        if board.is_check():
            return phrase + (", check" if lang == "en" else ", jaque")
        return phrase
    finally:
        board.pop()   # always put the board back, even if something goes wrong


def describe_san(board, san, **kwargs):
    """Convenience: describe a move written the normal way, like 'Nf3'."""
    return describe_move(board, board.parse_san(san), **kwargs)


# ── Self-test ────────────────────────────────────────────────────────────────
# Run `python chess_speech.py` and it checks its own work. These are the
# exact cases the old version got wrong, plus their Spanish equivalents.

def _self_test():
    checks = []

    def check(setup, san, expected, lang="en"):
        """setup is either a list of moves to play, or a FEN position string."""
        if isinstance(setup, str):
            board = chess.Board(setup)
        else:
            board = chess.Board()
            for m in setup:
                board.push_san(m)
        got = describe_san(board, san, lang=lang)
        checks.append((f"[{lang}] {san}", expected, got, got == expected))

    # ── English (unchanged from before Spanish was added) ────────────────────
    check([], "e4", "pawn to e four")
    check([], "Nf3", "knight to f three")
    check([], "a4", "pawn to ay four")
    check([], "a3", "pawn to ay three")
    check([], "Na3", "knight to ay three")
    check(["e4", "e5", "Nf3", "Nc6", "Bb5", "a6", "Ba4", "b5"], "Bb3",
          "bishop to b three")
    check(["e4", "d5"], "exd5", "pawn takes pawn on d five")
    check(["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"], "Bxc6",
          "bishop takes knight on c six")
    check(["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5"], "O-O", "castles kingside")
    check(["f4", "e5", "g4"], "Qh4", "queen to h four, checkmate")
    check("rnbqkbnr/pppppppp/8/8/5N2/2N5/PPPPPPPP/R1BQKB1R w KQkq - 0 1", "Ncd5",
          "knight on the c-file to d five")
    check("4k3/8/8/R7/8/8/8/R3K3 w - - 0 1", "R1a3",
          "rook on rank one to ay three")
    check([], "Nc3", "knight to c three")
    check("4k3/P7/8/8/8/8/8/4K3 w - - 0 1", "a8=Q",
          "pawn to ay eight, promotes to queen, check")
    check(["e4", "a6", "e5", "d5"], "exd6", "pawn takes on d six, en passant")

    # ── Spanish ────────────────────────────────────────────────────────────
    check([], "e4", "peón a e cuatro", "es")
    check([], "Nf3", "caballo a efe tres", "es")
    check([], "a4", "peón a a cuatro", "es")
    check([], "Na3", "caballo a a tres", "es")
    check(["e4", "d5"], "exd5", "peón captura peón en de cinco", "es")
    check(["e4", "e5", "Nf3", "Nc6", "Bb5", "a6"], "Bxc6",
          "alfil captura caballo en ce seis", "es")
    check(["e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5"], "O-O", "enroca corto", "es")
    check(["e4", "e5", "Nf3", "Nc6", "Bb5"], "a6", "peón a a seis", "es")
    check([], "d4", "peón a de cuatro", "es")
    check(["f4", "e5", "g4"], "Qh4", "dama a hache cuatro, jaque mate", "es")
    check("rnbqkbnr/pppppppp/8/8/5N2/2N5/PPPPPPPP/R1BQKB1R w KQkq - 0 1", "Ncd5",
          "caballo de la columna ce a de cinco", "es")
    check("4k3/8/8/R7/8/8/8/R3K3 w - - 0 1", "R1a3",
          "torre de la fila uno a a tres", "es")
    check("4k3/P7/8/8/8/8/8/4K3 w - - 0 1", "a8=Q",
          "peón a a ocho, corona dama, jaque", "es")
    check(["e4", "a6", "e5", "d5"], "exd6", "peón captura al paso en de seis", "es")
    check(["e4", "e5", "Bc4", "Nc6", "Qh5", "Nf6"], "Qxf7",
          "dama captura peón en efe siete, jaque mate", "es")

    width = max(len(c[0]) for c in checks)
    failures = 0
    for label, expected, got, ok in checks:
        mark = "OK  " if ok else "FAIL"
        print(f"{mark} {label:{width}s} -> {got}")
        if not ok:
            print(f"{'':{width+6}s}expected: {expected}")
            failures += 1

    print()
    if failures:
        print(f"{failures} of {len(checks)} checks FAILED")
    else:
        print(f"All {len(checks)} checks passed.")
    return failures == 0


if __name__ == "__main__":
    import sys
    sys.exit(0 if _self_test() else 1)
