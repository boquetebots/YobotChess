#!/usr/bin/env python3
"""
chess_commentary.py — deciding what a robot says about a move
================================================================================

TWO JOBS:

  1. Look at a move and work out what KIND of move it was — a quiet
     development move, a big capture, a check, a sacrifice.
  2. Pick a sentence from `chess_templates.py` that suits it.

The sentences themselves live in `chess_templates.py`. If you want to change
what the robots SAY, edit that file, not this one. This file only decides
WHICH list to pull from.

--------------------------------------------------------------------------------
THREE BUGS FROM THE 2025 VERSION, FIXED HERE
--------------------------------------------------------------------------------

1. IT NAMED THE WRONG PIECE AS THE VICTIM.
   The old code decided how big a capture was by looking for the letter Q or
   R in the move text. But in "Qxd5" the Q is the piece DOING the taking, not
   the piece being taken. So a queen grabbing a defenceless pawn was
   announced as a huge capture: "Material advantage is mine!" over a pawn.
   Now we ask the board what was actually standing on that square.

2. IT CHECKED THE WRONG KING.
   `_is_position_under_attack` was meant to notice "I am building an attack
   on the other king". It ran after the move had been played, when the board
   had already flipped to the other player, so it counted attackers on the
   robot's OWN king. It was reporting danger to itself as aggression.

3. FIFTEEN SENTENCES WERE UNREACHABLE.
   The bank has a `sacrifice` category with fifteen lines in it. Nothing in
   the old code ever chose that category, so not one of them could ever be
   spoken. Sacrifice detection is wired up below.
"""

import random

from chess_needs import require
require("chess")

import chess

from chess_speech import describe_move
import chess_templates
import chess_templates_es

# Which module supplies the sentence banks for each language. "en" keeps
# working exactly as it always did; "es" is the Spanish twin added
# 2026-08-31. Anything not in this dict falls back to English rather than
# crashing the show over a typo in a --lang argument.
TEMPLATE_MODULES = {
    "en": chess_templates,
    "es": chess_templates_es,
}


# What each piece is worth. The standard chess values — a queen is worth
# about nine pawns, a rook five, and so on. Used to tell a big capture from
# a small one.
PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,      # the king is never captured, so it has no trade value
}

# A capture worth this much or more counts as a "major" capture — a rook or
# a queen. Lower the number if you want the robots to get excited more often.
MAJOR_CAPTURE_VALUE = 5

# ── How much did this move change the game? ──────────────────────────────────
#
# Everything above is a list of chess EVENTS — a capture, a check, castling.
# That was the only signal available at first, and it has a blind spot: it
# treats castling (routine) as interesting and treats throwing away a bishop
# (the single most interesting thing that happens between weak players) as
# nothing at all.
#
# Stockfish tells us, in centipawns, how well it thinks each side is doing.
# Comparing that number before and after a move says whether the move
# actually changed anything. That is what a human commentator reacts to.
#
# Measured in centipawns: 100 is one pawn.
BLUNDER_SWING = -200      # gave away two pawns' worth or more
MISTAKE_SWING = -100      # gave away about a pawn

# Note the neat side effect: a SOUND sacrifice is the best move on the board,
# so the evaluation barely moves and it is correctly not called a blunder.
# An unsound one tanks the evaluation and is. The engine sorts out the
# difference between brilliance and carelessness for us.

# How much material a robot must be giving away for it to count as a
# sacrifice rather than a normal exchange. Two points is roughly "a knight
# for a pawn".
SACRIFICE_MARGIN = 2


# ── Announcing versus commenting ─────────────────────────────────────────────
#
# A robot ANNOUNCES every move. It does not COMMENT on every move.
#
# That distinction is the difference between a show and a lecture. If both
# robots produce a witty paragraph about a routine pawn push, then by the time
# somebody actually hangs a queen there is nowhere left to go — the audience
# has been at full volume for twenty minutes and has stopped listening. Quiet
# moves need to be quiet so the loud ones land.
#
# So on a quiet move the robot mostly just says the move, from the ANNOUNCE
# list in chess_templates.py, and says nothing else.

# How often a QUIET move gets a bare announcement instead of a comment.
# 0.0 = comment on everything, like the old behaviour.
# 1.0 = never comment on a quiet move at all.
# Two thirds means roughly one quiet move in three still gets a remark, so the
# robots keep some personality between the big moments.
ANNOUNCE_CHANCE = 0.66

# Which situations count as quiet. Everything NOT in this list — a capture, a
# check, a blunder, a sacrifice, a promotion, castling, checkmate — always
# gets a proper line, no matter what ANNOUNCE_CHANCE is set to.
#
# Castling is deliberately absent. It is dull chess, but the ANNOUNCE lines
# would break its grammar: the move reads as "castles kingside", so
# "I played castles kingside" is not English. Rule six in chess_templates.py.
QUIET_CATEGORIES = {
    "opening_development",
    "opening_center",
    "attack_building",
    "defensive",
    "middlegame_tactical",
    "endgame_technique",
}


def analyse_move(board, move, swing=None, opponent_blundered=False):
    """
    Look at a move and describe what sort of move it is.

    `board` must be the position BEFORE the move is played — the same rule as
    chess_speech.py, and for the same reason. Once the move is played we can
    no longer see what was captured.

    `swing` is how much this move changed Stockfish's opinion of the game,
    in centipawns, FROM THE MOVER'S POINT OF VIEW. Negative means the move
    made things worse for the player who made it. Leave it as None when
    there is no engine — everything still works, there is just no blunder
    detection.

    `opponent_blundered` says whether the move before this one was a
    blunder, so this robot can react to it rather than ignore it.

    Returns a plain dictionary of facts. Nothing in here knows or cares about
    what the robot will say; that decision happens further down.
    """
    mover = board.piece_at(move.from_square)
    mover_value = PIECE_VALUES[mover.piece_type] if mover else 0

    # ── What did we take, if anything? ───────────────────────────────────────
    captured_value = 0
    if board.is_capture(move):
        if board.is_en_passant(move):
            captured_value = PIECE_VALUES[chess.PAWN]
        else:
            victim = board.piece_at(move.to_square)
            captured_value = PIECE_VALUES[victim.piece_type] if victim else 0

    facts = {
        "is_capture":     board.is_capture(move),
        "captured_value": captured_value,
        "is_castling":    board.is_castling(move),
        "is_promotion":   move.promotion is not None,
        "move_number":    board.fullmove_number,
        "phase":          _phase(board),
        "swing":          swing,
        "is_blunder":     swing is not None and swing <= BLUNDER_SWING,
        "is_mistake":     swing is not None and swing <= MISTAKE_SWING,
        "punishing":      bool(opponent_blundered),
    }

    # ── Everything below needs the move actually played ──────────────────────
    board.push(move)
    try:
        facts["is_check"] = board.is_check()
        facts["is_checkmate"] = board.is_checkmate()
        facts["game_over"] = board.is_game_over()

        # Are we massing pieces around the OTHER king? After the push it is
        # the opponent's turn, so the opponent's king is `board.king(board.turn)`
        # and we are `not board.turn`. This is the line the old version had
        # backwards.
        enemy_king = board.king(board.turn)
        if enemy_king is None:
            facts["building_attack"] = False
        else:
            attackers = board.attackers(not board.turn, enemy_king)
            facts["building_attack"] = len(attackers) > 1

        # ── Sacrifice ────────────────────────────────────────────────────
        # A sacrifice is deliberately handing over more material than you
        # get back. Two things have to be true:
        #
        #   1. You are down on the deal  (gave a knight, took a pawn)
        #   2. Something CHEAPER than the piece you moved can take it
        #
        # Point 2 is what separates a sacrifice from an ordinary trade. A
        # queen sitting where a pawn can take it is a sacrifice. A knight
        # sitting where only the enemy queen can take it is not — that is
        # just a piece doing its job.
        #
        # The first version of this file left point 2 out, and every quiet
        # developing move that happened to be in the line of an enemy queen
        # got announced as a heroic sacrifice. In the Opera Game, black
        # playing knight to f six — a completely normal move — was
        # introduced as "a worthy sacrifice indeed".
        giving_up = mover_value - captured_value
        cheapest_attacker = _cheapest_attacker(board, move.to_square)
        facts["is_sacrifice"] = (
            giving_up >= SACRIFICE_MARGIN
            and cheapest_attacker is not None
            and cheapest_attacker < mover_value
            and not facts["is_checkmate"]
        )
    finally:
        board.pop()      # always put the board back exactly as we found it

    return facts


def _cheapest_attacker(board, square):
    """
    Of all the enemy pieces that could capture on this square, what is the
    least valuable one worth?

    Call this with the move already played, so "enemy" means the side about
    to move. Returns None if nothing can capture there.

    The king is treated as expensive (ten) rather than free. A king can only
    capture something undefended, so letting it count as a cheap attacker
    would label every defended piece a sacrifice.
    """
    attackers = board.attackers(board.turn, square)
    if not attackers:
        return None

    values = []
    for attacker_square in attackers:
        piece = board.piece_at(attacker_square)
        if piece is None:
            continue
        values.append(10 if piece.piece_type == chess.KING
                      else PIECE_VALUES[piece.piece_type])
    return min(values) if values else None


def _phase(board):
    """Opening, middlegame or endgame — decided by how much is still on."""
    pieces_left = len(board.piece_map())
    if board.fullmove_number <= 8:
        return "opening"
    if pieces_left <= 12:
        return "endgame"
    return "middlegame"


def choose_category(facts):
    """
    Pick which list of sentences to draw from.

    Order matters: the most dramatic thing that is true wins. Checkmate beats
    a capture, a capture beats a quiet developing move.
    """
    if facts["is_checkmate"]:
        return "checkmate"          # the last move of the game beats everything
    if facts["is_promotion"]:
        return "promotion"

    # A blunder outranks nearly everything. It is the moment the game turned,
    # and a robot that has just dropped a rook should say so rather than
    # calmly reporting "material advantage is mine" about the pawn it took on
    # the way. Note this sits ABOVE sacrifice on purpose: a sound sacrifice
    # does not move the evaluation, so it never lands here.
    if facts["is_blunder"]:
        return "blunder"
    if facts["punishing"]:
        return "punish"

    if facts["is_sacrifice"]:
        return "sacrifice"
    if facts["is_castling"]:
        return "castling"
    if facts["is_check"]:
        return "check_attack"
    if facts["is_capture"] and facts["captured_value"] >= MAJOR_CAPTURE_VALUE:
        return "capture_major"
    if facts["is_capture"]:
        return "capture_minor"
    if facts["phase"] == "opening":
        # Alternate between the two opening flavours so the first few moves
        # do not all sound the same.
        return "opening_center" if facts["move_number"] % 2 == 0 else "opening_development"
    if facts["phase"] == "endgame":
        return "endgame_technique"
    if facts["building_attack"]:
        return "attack_building"
    if random.random() < 0.3:
        return "defensive"
    return "middlegame_tactical"


def is_dramatic(facts):
    """
    Is this a moment worth spending an AI call on?

    Used from step 7 of the plan onwards. Until the AI is wired in, nothing
    calls this — but the rule lives here so there is one place to tune it.

    The first version of this was a list of chess events, which meant
    castling — utterly routine — counted, while throwing away a bishop did
    not. Where an engine evaluation is available, a real turning point now
    counts too.
    """
    return (
        facts["is_checkmate"]
        or facts["is_promotion"]
        or facts["is_blunder"]
        or facts["punishing"]
        or facts["is_sacrifice"]
        or facts["is_check"]
        or (facts["is_capture"] and facts["captured_value"] >= MAJOR_CAPTURE_VALUE)
    )


class CommentaryWriter:
    """
    Writes the line each robot speaks.

    ONE of these is shared by both robots, on purpose. It remembers what was
    said recently, so white cannot deliver a line and have black immediately
    repeat it back. That shared memory is the whole reason this lives on the
    server and not on the Pis.
    """

    # How many recent lines to remember and refuse to repeat.
    #
    # `None` means "everything said so far this game". That is the setting
    # you want, and it is the default.
    #
    # It used to be twelve — a rolling window of the last twelve lines. That
    # is not the same thing at all, and the difference was audible. A window
    # of twelve means a joke used at move eight is allowed back at move
    # thirty. In testing, "Deleted. No recycle bin." was used twice in one
    # short game, and ten-odd lines came round again in a long one. Widening
    # the window to thirty did not fix it; it only moved the problem later,
    # because any window smaller than the game will eventually let something
    # back in.
    #
    # Remembering the whole game costs a list of a few hundred short strings
    # and removes the problem outright. `reset()` empties it between games,
    # which is right — nobody in the room heard yesterday's game.
    REMEMBER_THE_WHOLE_GAME = None

    def __init__(self, memory_size=REMEMBER_THE_WHOLE_GAME, announce_chance=None,
                 announce_memory=REMEMBER_THE_WHOLE_GAME, polite=False, lang="en"):
        # ── Which language ───────────────────────────────────────────────────
        # Added 2026-08-31. Picks which module's sentence banks this writer
        # draws from — chess_templates (English) or chess_templates_es
        # (Spanish). Everything below that used to say "chess_templates"
        # says "self._bank" instead, and that is the only change; the whole
        # rest of this class has no idea which language it is running.
        # set_language() below does this, and can do it AGAIN later while
        # the server is running. See the comment on that method.

        # ── Polite mode ──────────────────────────────────────────────────────
        # Every line in the bank was written for one robot to say to another
        # robot, which cannot take offence. Aimed at a guest who has just hung
        # their queen in front of the whole clubhouse, the sharper ones stop
        # being funny. Polite mode leaves out the five Sassy lines in each
        # category and uses the other fifteen.
        #
        # Fifteen instead of twenty means a category runs dry sooner in a long
        # game. That is already handled: a category with nothing unused left
        # falls back to a bare announcement rather than repeating a joke.
        #
        # without_tone() lives in chess_templates.py, but it takes any
        # templates dict as an argument — chess_templates.py's own TEMPLATES
        # by default, or this writer's chosen bank's TEMPLATES here — so the
        # Spanish bank gets Polite mode for free, with no code of its own.
        self.polite = polite
        self.recent = []
        self.recent_announcements = []
        self.set_language(lang)
        self.memory_size = memory_size

        # The bare announcements get their OWN memory, separate from the
        # commentary. They have to: they are used several times more often
        # than anything else, so sharing one list would flush every witty line
        # out of the memory within a couple of moves and the robots would
        # start repeating their jokes while never repeating "your turn".
        self.recent_announcements = []
        self.announce_memory = announce_memory
        self.announce_chance = (
            ANNOUNCE_CHANCE if announce_chance is None else announce_chance)

    def set_language(self, lang):
        """
        Switch which language this writer talks in, WHILE IT IS RUNNING.

        Added 2026-08-31, after a real game was played with Espanol picked on
        the control page and the robots spoke English from first move to
        last. The language used to be decided once, when chess_server.py
        started, so choosing it on the page without restarting the server
        silently did nothing at all — and nothing on screen said so. Now the
        page can change it mid-game and this is the one place that has to
        know how.

        Anything unrecognised becomes English rather than raising, because a
        typo in a language name must never stop a show. Returns the language
        actually in use, so the caller can report what really happened
        instead of what it asked for.
        """
        self.lang = lang if lang in TEMPLATE_MODULES else "en"
        self._bank = TEMPLATE_MODULES[self.lang]

        # Polite mode is applied here rather than in __init__ so that it
        # survives a language change. Without this line, switching to Spanish
        # mid-game would quietly turn the sharp lines back on in front of the
        # guest polite mode was protecting.
        bank_templates = (self._bank.TEMPLATES if self.lang == "en"
                          else self._bank.TEMPLATES_ES)
        self.templates = (chess_templates.without_tone("Sassy", templates=bank_templates)
                          if self.polite else bank_templates)
        self.announcements = (self._bank.ANNOUNCE if self.lang == "en"
                              else self._bank.ANNOUNCE_ES)

        # What has already been said was said in the OTHER language, so it is
        # no use as a "do not say this again" list any more.
        self.recent = []
        self.recent_announcements = []
        return self.lang

    def reset(self):
        """Forget what has been said. Called at the start of a new game."""
        self.recent = []
        self.recent_announcements = []

    def comment_on(self, board, move, swing=None, opponent_blundered=False):
        """
        The main entry point.

        `board` is the position BEFORE the move.

        `swing` and `opponent_blundered` come from the engine and are
        optional — without them everything still works, there is simply no
        blunder detection. That is what happens when a scripted test game is
        replayed with no engine running.

        Returns a tuple of:
            spoken sentence, the move in chess notation, the facts dictionary
        """
        facts = analyse_move(board, move, swing, opponent_blundered)
        spoken_move = describe_move(board, move, lang=self.lang)
        category = choose_category(facts)

        # Some sentences in the bank do not mention the move at all — lines
        # like "I castle! My king retreats to safety." That is fine most of
        # the time and stops the robots sounding like a chess clock.
        #
        # But it is NOT fine when the move gives check or ends the game. The
        # word "checkmate" lives inside the spoken move, so a template that
        # leaves the move out would swallow it, and the robot would announce
        # the winning move of the game without mentioning that it had won.
        # This actually happened in testing.
        must_say_move = facts["is_check"] or facts["is_checkmate"]

        if self._should_just_announce(category):
            template = self._pick_announcement()
        else:
            template = self._pick(category, must_say_move)

        sentence = template.format(move=spoken_move)

        # Many lines now START with {move} — "knight to f three. Your turn." —
        # so the finished sentence begins with a lower case letter. It sounds
        # identical either way, but it looks wrong in the log window on the
        # display page, so tidy it here.
        sentence = sentence[:1].upper() + sentence[1:]

        return sentence, board.san(move), facts

    def _should_just_announce(self, category):
        """
        Should the robot skip the commentary and simply say the move?

        Only ever true for the quiet categories. A capture, a check, a
        blunder or a checkmate always gets its proper line — those are the
        moments the whole show is built around.
        """
        if category not in QUIET_CATEGORIES:
            return False
        return random.random() < self.announce_chance

    def _pick_announcement(self):
        """One bare announcement, avoiding the last twenty used."""
        return self._choose(
            self.announcements, self.recent_announcements, self.announce_memory)

    def _pick(self, category, must_say_move=False):
        """Choose a sentence, avoiding anything said in the last few moves."""
        options = self.templates.get(category) or self.templates["middlegame_tactical"]

        if must_say_move:
            with_move = [t for t in options if "{move}" in t]
            # Every category has at least one line containing {move}, but if
            # someone edits them all out, fall back rather than crash.
            options = with_move or ["I played {move}."]

        # ── When a category runs dry ──────────────────────────────────────
        #
        # Each list holds twenty lines. In a long, bloody game one category
        # can be called on far more than twenty times — a hundred and forty
        # move game with captures flying produces forty visits to
        # `capture_minor` alone. There is then no unused joke left.
        #
        # The old behaviour was to start the list again, so the audience
        # heard the same gag twice. Saying the move and nothing else is a
        # much better way to run out: it sounds like a robot getting on with
        # the game, not a robot repeating itself.
        #
        # Castling is the exception, and only for grammar — see rule six in
        # chess_templates.py. An exhausted castling list loops, which costs
        # nothing, because a game contains at most two castling moves.
        if category != "castling" and not [t for t in options if t not in self.recent]:
            return self._pick_announcement()

        return self._choose(options, self.recent, self.memory_size)

    def _choose(self, options, memory, memory_size):
        """
        Pick one line at random, skipping anything in `memory`, and remember
        it. `memory` is edited in place, so the caller keeps its own list.
        """
        fresh = [t for t in options if t not in memory]

        # If we have worked through everything available, start again rather
        # than falling silent.
        if not fresh:
            fresh = options
            memory[:] = [r for r in memory if r not in options]

        chosen = random.choice(fresh)
        memory.append(chosen)
        if memory_size is not None and len(memory) > memory_size:
            memory[:] = memory[-memory_size:]
        return chosen

    def game_start_line(self, colour):
        game_start = (self._bank.GAME_START if self.lang == "en"
                      else self._bank.GAME_START_ES)
        return random.choice(game_start[colour])

    def game_end_line(self, result, colour, resigned_by=None):
        """
        result is chess's own notation:
            "1-0"      white won
            "0-1"      black won
            "1/2-1/2"  drawn
            "*"        the game was still going when we stopped it, which
                       happens when the move cap runs out

        resigned_by is "white", "black" or None. A resignation needs its own
        lines: the winner must not announce a checkmate that never happened,
        and the loser should concede rather than simply report a loss.
        """
        game_end = (self._bank.GAME_END if self.lang == "en"
                   else self._bank.GAME_END_ES)

        if resigned_by is not None:
            outcome = "resigned" if colour == resigned_by else "accept_resignation"
            return random.choice(game_end[outcome])

        if result == "1-0":
            outcome = "win" if colour == "white" else "loss"
        elif result == "0-1":
            outcome = "win" if colour == "black" else "loss"
        elif result == "*":
            outcome = "adjourned"
        else:
            outcome = "draw"
        return random.choice(game_end[outcome])
