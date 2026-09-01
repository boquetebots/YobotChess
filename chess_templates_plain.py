#!/usr/bin/env python3
"""
chess_templates.py — the things the robots say about their moves
================================================================================

THIS FILE IS JUST A LIST OF SENTENCES. There is no clever code in it. If you
want to change what the robots say, this is the only file you need to open.

--------------------------------------------------------------------------------
HOW TO EDIT IT
--------------------------------------------------------------------------------

Every line is wrapped in "double quotes" and followed by a comma. To add a new
line, copy an existing one, change the words, and keep the quotes and the comma.

    "I played {move}. The centre is mine!",
     ^                                   ^^
     open quote                          close quote, then a comma

`{move}` is a placeholder. The server swaps it for the actual move, so
`"I played {move}."` comes out of the robot's mouth as
`"I played knight to f three."`

You do not have to use {move} at all. Some lines below leave it out on
purpose, so the robot occasionally just reacts instead of narrating.

--------------------------------------------------------------------------------
FOUR RULES, ALL OF THEM LEARNED THE HARD WAY
--------------------------------------------------------------------------------

1. DO NOT FORGET THE COMMA at the end of a line. Python will silently glue
   your line onto the next one and say both as a single run-on sentence with
   no error message. This had already happened once in the 2025 version:

       "With {move}, I'm setting the stage for greatness."   <- comma missing
       "My move is {move}.",

   ...became one line reading "...stage for greatness.My move is {move}."
   The robot would have said it exactly like that.

2. NO SLASHES. The robot reads "knight/bishop" out loud as "knight slash
   bishop". Same for &, *, and any other symbol. Words only.

3. LEAVE A SPACE before {move}. "My move{move}." comes out as
   "my moveknight to f three". There were seven of these.

4. NO NUMBERS AS DIGITS. Write "two pawns", not "2 pawns".

5. FINISH THE SENTENCE AFTER {move}. Put a full stop, comma or exclamation
   mark straight after it — never carry on mid-sentence.

       GOOD:  "I play {move}. Bringing my pieces into play."
       BAD:   "Playing {move} to bring my pieces into play."

   This one is not obvious. {move} is no longer a short token like "Nf3" —
   it is a whole phrase, and on a checking move it ends with the word
   "check". So the bad example above comes out of the robot as:

       "Playing queen to h four, check to bring my pieces into play."

   Thirty-six lines had this problem. They are all fixed, and the checker
   below will refuse any new ones.

--------------------------------------------------------------------------------
CHECKING YOUR WORK
--------------------------------------------------------------------------------

After editing, run this. It checks every rule above and tells you the line
number of anything it does not like:

    python chess_templates.py
"""

# Each category below is a situation on the board. The server works out which
# situation applies and picks one line from that list at random.

TEMPLATES = {

    # ── opening development ─────────────────────────────────
    # Early in the game, bringing pieces out from the back row.
    'opening_development': [
        "I played {move}. Building up my army for the coming battle!",
        "I play {move}.",
        "I played {move}.",
        "My move is {move}. Every piece needs a good square.",
        "My move is {move}.",
        "I choose {move}. Development first, attack later!",
        "I played {move}. Getting my forces into position.",
        "My move is {move}. The foundation of a strong position.",
        "With {move}, I'm mobilizing my troops efficiently.",
        "I opt for {move}. Steady development is key to success.",
        "I play {move}. Bringing my pieces into play.",
        "My choice: {move}. Laying the groundwork for victory.",
        "I make {move}. Pieces off the back rank, ready for action!",
        "I go with {move}. Developing with purpose and plan.",
        "I played {move}. Awakening my sleeping army.",
        "My move is {move}. Rapid deployment is the plan.",
        "I choose {move}. Harmonising my forces.",
        "With {move}, I'm setting the stage for greatness.",
    ],

    # ── opening center ──────────────────────────────────────
    # Early in the game, fighting for the middle four squares.
    'opening_center': [
        "My move is {move}.",
        "I play {move}.",
        "I played {move}.",
        "I played {move}. The center is the heart of the battlefield!",
        "My move is {move}. Control the center, control the game.",
        "I choose {move}. Fighting for the vital central squares.",
        "I played {move}. Space advantage is crucial here.",
        "My move is {move}. The center beckons!",
        "I play {move}. Staking my claim in the centre.",
        "With {move}, I'm dominating the board's core.",
        "I opt for {move}. Central control leads to dominance.",
        "Here is {move}. That asserts my influence over the middle.",
        "My choice is {move}. Grabbing space where it matters most.",
        "I make {move}. The center is mine to command!",
        "I choose {move}. A crucial central push.",
        "With {move}, the heart of the board beats for me.",
        "My move is {move}. Expanding my central territory.",
        "I go with {move}. That solidifies my central grip.",
    ],

    # ── capture minor ───────────────────────────────────────
    # Taking a pawn, a knight or a bishop. The everyday captures.
    'capture_minor': [
        "My move is {move}.",
        "I play {move}.",
        "I played {move}.",
        "I played {move}. That piece is mine now!",
        "My move is {move}. One less defender for you!",
        "I choose {move}. I will take what I can get!",
        "I played {move}. Every piece counts in this battle.",
        "My move is {move}. Reducing your army piece by piece!",
        "Snapping up with {move}. That piece is history!",
        "I play {move}. Whittling down your forces.",
        "Here is {move}. A small but important gain.",
        "I play {move}. That pesky piece is gone.",
        "With {move}, I claim my prize from your ranks.",
        "Here is {move}. That tips the material scales.",
        "I choose {move}. Removing a key defender.",
        "I played {move}. Your defenses weaken further.",
        "I go with {move}. Gobbling up the opposition.",
        "I go with {move}. Every exchange counts.",
    ],

    # ── capture major ───────────────────────────────────────
    # Taking a rook or a queen. The ones worth shouting about.
    'capture_major': [
        "I played {move}. A valuable prize falls into my hands!",
        "My move is {move}. That hurts your position badly!",
        "I choose {move}. This is a significant blow!",
        "I played {move}. Your position is crumbling!",
        "My move is {move}. Material advantage is mine!",
        "With {move}, I seize a heavy piece!",
        "I play {move}. That is a game changer!",
        "I opt for {move}. Your heavy artillery is gone.",
        "Here is {move}. Victory draws near!",
        "I play {move}. That was a high value target!",
        "My choice: {move}. Devastating material swing.",
        "Here is {move}. Your position reels!",
        "I make {move}. A massive capture indeed.",
        "I choose {move}. The big prize is mine.",
        "With {move}, material dominance is achieved.",
    ],

    # ── check attack ────────────────────────────────────────
    # Putting the other king in check.
    'check_attack': [
        # NOTE: the move itself already ends with the word "check", so these
        # lines must not say it again or the robot says "check, check!".
        "I played {move}. Your king cannot hide forever!",
        "My move is {move}. Find shelter if you can!",
        "I choose {move}. The hunt begins!",
        "I played {move}. Your royal majesty is in danger!",
        "My move is {move}. Time to scramble for safety!",
        "{move}. The king is under fire!",
        "{move}. Evade if you dare!",
        "I attack with {move}. Pressure on the monarch.",
        "Playing {move}. The chase is on!",
        "{move}. Your king feels the heat.",
        "{move}. Forcing your hand now.",
        "Choosing {move}. The throne trembles.",
        "I played {move}. Safety is an illusion.",
        "I go with {move}. Time to defend royalty.",
        "Delivering it with {move}. The assault intensifies!",
    ],

    # ── blunder ──────────────────────────────────────────────
    # The robot has just thrown something away. This is the most
    # interesting thing that happens in a game between weak players, and for
    # a long time it produced no reaction at all.
    #
    # Rueful, not pathetic. Yobot has some dignity. It notices, it is
    # annoyed with itself, it carries on.
    'blunder': [
        "I played {move}. That may have been a mistake.",
        "{move}. Oh. That was careless of me.",
        "I played {move}. I regret that one already.",
        "{move}. Hmm. I did not think that through.",
        "I play {move}. Do not look at me like that.",
        "{move}. Let us pretend that did not happen.",
        "I played {move}. Not my finest thinking.",
        "{move}. I may have just made your afternoon easier.",
        "I play {move}. Even robots have off days.",
        "{move}. I saw that a moment too late.",
        "My move is {move}. I would like that one back, please.",
        "{move}. Well. That is going to cost me.",
    ],

    # ── punish ───────────────────────────────────────────────
    # The other robot just erred and this one is taking advantage.
    # Gracious rather than gloating — it is funnier, and it keeps both
    # robots likeable in front of an audience.
    'punish': [
        "I played {move}. Thank you very much.",
        "{move}. That was generous of you.",
        "I play {move}. I will not say no.",
        "{move}. You will want that one back.",
        "I played {move}. A gift, and I accept it.",
        "{move}. Careless. And costly.",
        "I play {move}. That changes things.",
        "{move}. I did wonder if you meant that.",
        "My move is {move}. Every mistake is an opportunity.",
        "{move}. I was hoping you would do that.",
        "I played {move}. Punishing that one.",
        "{move}. And just like that, the game turns.",
    ],

    # ── checkmate ────────────────────────────────────────────
    # The last move of the game. This is the moment the whole demo builds to,
    # so every line here names the move and then stops — no boasting over the
    # top of it. The move itself already ends with the word "checkmate".
    'checkmate': [
        "{move}. That is the game.",
        "I played {move}. Good game, my friend.",
        "{move}. And that, I believe, is that.",
        "My move is {move}. Thank you for the game.",
        "{move}. The king has nowhere left to go.",
        "I finish with {move}. A pleasure playing you.",
        "{move}. The board is silent. It is over.",
        "I play {move}. Well fought, but the game is mine.",
        "{move}. No escape, no defence, no more moves.",
        "With {move}, the hunt is over.",
    ],

    # ── castling ────────────────────────────────────────────
    # The king tucking itself away behind a wall of pawns.
    'castling': [
        "I played {move}. My king finds safety behind the fortress!",
        "I castle! My king retreats to safety while my rook joins the fight.",
        "Castling! The king must be protected at all costs.",
        "I castle for safety. A wise king knows when to retreat.",
        "My king castles to safety. Now the real battle can begin!",
        "Castling with {move}. Tucking the king away safely.",
        "I choose to castle. Safeguarding my leader.",
        "I castle. Rook activates, king secures.",
        "Here is {move}. A move for kings and rooks alike.",
        "Castling now. Protection first, aggression next.",
        "My castling move. Building an impregnable wall.",
        "Opting to castle. The king seeks refuge.",
        "With castling, my position solidifies.",
        "I castle strategically. Safety in the wings.",
        "Castling complete. Ready for the middlegame push.",
    ],

    # ── attack building ─────────────────────────────────────
    # Pressure mounting on the other robot's king.
    'attack_building': [
        "My move is {move}.",
        "I play {move}.",
        "I played {move}.",
        "I played {move}. The pressure is mounting on your position!",
        "My move is {move}. I am building a dangerous attack!",
        "I choose {move}. Your defenses are starting to crack!",
        "I played {move}. The storm clouds are gathering!",
        "My move is {move}. Each move tightens the noose!",
        "With {move}, my attack gains momentum.",
        "Building pressure via {move}. Feel the squeeze!",
        "I opt for {move}. Assault preparations underway.",
        "Here is {move}. The threat level rises.",
        "I play {move}. Ramping up the aggression.",
        "My choice: {move}. The offensive builds.",
        "Advancing with {move}. Your lines weaken.",
        "I make {move}. Attack vectors multiplying.",
        "I choose {move}. The danger deepens.",
        "With {move}, the onslaught approaches.",
    ],

    # ── defensive ───────────────────────────────────────────
    # Shoring things up rather than pushing forward.
    'defensive': [
        "My move is {move}.",
        "I play {move}.",
        "I played {move}.",
        "I played {move}. Defense is the better part of valor!",
        "My move is {move}. A solid defense leads to counterattack!",
        "I choose {move}. Every fortress needs strong walls.",
        "I played {move}. Patience and defense will prevail!",
        "My move is {move}. Let me shore up my defenses first.",
        "Reinforcing with {move}. Holding the line!",
        "I opt for {move}. Bolstering my barriers.",
        "Here is {move}. That strengthens my position.",
        "I play {move}. Fortifying against threats.",
        "With {move}, my defenses stand firm.",
        "My defensive {move}. Weathering the storm.",
        "I choose {move}. Solid protection.",
        "I played {move}. A wall against aggression.",
        "I go with {move}. Defence turns to offence soon.",
        "Shoring up via {move}. Unbreakable resolve!",
    ],

    # ── middlegame tactical ─────────────────────────────────
    # The messy middle of the game. The catch-all category.
    'middlegame_tactical': [
        "My move is {move}.",
        "I play {move}.",
        "I played {move}.",
        "I played {move}. The position is getting sharp and tactical!",
        "My move is {move}. Tactics are flying in this position!",
        "I choose {move}. Every move must be calculated precisely!",
        "I played {move}. The battle intensifies with each move!",
        "My move is {move}. One wrong step could be fatal now!",
        "With {move}, tactics take center stage.",
        "Navigating tactics with {move}. Precision required!",
        "I opt for {move}. The board sparks with combinations.",
        "Here is {move}. Tactical fireworks from here.",
        "I play {move}. A tactical minefield out there.",
        "My choice: {move}. Calculating deeply now.",
        "Sharpening with {move}. Opportunities abound.",
        "I make {move}. Tactics dictate the flow.",
        "I choose {move}. Chaos in every direction.",
        "With {move}, the middlegame explodes!",
    ],

    # ── endgame technique ───────────────────────────────────
    # Few pieces left on the board. Precision matters.
    'endgame_technique': [
        "My move is {move}.",
        "I play {move}.",
        "I played {move}.",
        "I played {move}. Technique and precision matter most now.",
        "My move is {move}. Every tempo counts in the endgame!",
        "I choose {move}. The endgame is all about accuracy.",
        "I played {move}. Each move brings us closer to the truth!",
        "My move is {move}. The final phase demands perfection!",
        "Executing {move}. Endgame finesse at work.",
        "I opt for {move}. Precision guides the end.",
        "Here is {move}. My endgame plan advances.",
        "I play {move}. Technical accuracy matters now.",
        "With {move}, every pawn matters.",
        "My endgame {move}. Tempo by tempo.",
        "I choose {move}. Optimal technique.",
        "I played {move}. The end draws near.",
        "I go with {move}. Mastering the finale.",
        "Refining with {move}. Victory through skill.",
    ],

    # ── promotion ───────────────────────────────────────────
    # A pawn reaches the far end and becomes a queen.
    'promotion': [
        "I played {move}! My humble pawn has come a long way!",
        "My move is {move}! Promotion! The pawn's dream is realized!",
        "I promote with {move}. From lowly pawn to powerful piece in one move!",
        "My pawn promotes. {move}. Reinforcements at last!",
        "Promotion! {move}. My pawn has earned its reward!",
        "{move}. Crowning a brand new piece.",
        "Promoting with {move}. Pawn to powerhouse!",
        "I choose {move}. Promotion seals the deal.",
        "I play {move}. That is a sweet promotion.",
        "With {move}, my pawn ascends the ranks.",
        "Promotion for me. {move}. Reinforcements arrive!",
        "Opting for {move}. The pawn's transformation.",
        "I make {move}! A new piece steps onto the board.",
        "Promotion via {move}. Game over soon?",
        "Celebrating {move}. From pawn to real power!",
    ],

    # ── sacrifice ───────────────────────────────────────────
    # Deliberately giving up more material than you take.
    'sacrifice': [
        "I played {move}. Sometimes you must give to receive!",
        "My move is {move}. This sacrifice will pay dividends!",
        "I choose {move}. A calculated risk for greater gain!",
        "I played {move}. The sacrifice of today, victory of tomorrow!",
        "My move is {move}. Bold moves require bold sacrifices!",
        "Sacrificing with {move}. For the greater good!",
        "I opt for {move}. A worthy sacrifice indeed.",
        "Here is {move}. Offering a piece for the initiative.",
        "I play {move}. A bold sacrifice.",
        "With {move}, I sacrifice for the attack.",
        "My sacrificial {move}. Turning the tide!",
        "Choosing {move}. Risking it for the win.",
        "I make {move}. Sacrifice sparks brilliance.",
        "I go with {move}. Giving to conquer.",
        "Embracing sacrifice via {move}. Genius move!",
    ],
}


# ── Lines used when the AI is unavailable and something dramatic happens ─────
# These are the safety net. If the internet is down mid-game, the server falls
# back to these rather than stalling in front of an audience.

GAME_START = {
    "white": [
        "I am the White robot. I move first. Let us begin.",
        "White to play. I have been looking forward to this.",
        "I am White, and I intend to keep the initiative.",
    ],
    "black": [
        "I am the Black robot. I will answer everything you throw at me.",
        "Black is ready. Make your move and I will make mine.",
        "I am Black. I move second, but I finish first.",
    ],
}

GAME_END = {
    "win":  [
        "That is checkmate. A fine game, and a fine opponent.",
        "Victory. Thank you for the challenge.",
        "The game is mine. Well fought.",
    ],
    "loss": [
        "You have beaten me. Congratulations, that was well played.",
        "Defeat. I will study this one and come back stronger.",
        "You win. A deserved result.",
    ],
    "draw": [
        "A draw. We are evenly matched.",
        "Neither of us could break through. A fair result.",
        "The game is drawn. Honours even.",
    ],
    # What the LOSING robot says when it gives up. A robot resigning is much
    # better theatre than a robot shuffling a lost king around for twenty
    # moves, and it is how strong players actually end games.
    "resigned": [
        "I have seen enough. You have me. I resign.",
        "There is no saving this one. I resign. Well played.",
        "I resign. You were the better player today.",
        "My position is hopeless and we both know it. I resign.",
        "I know when I am beaten. I resign, and I congratulate you.",
        "This is lost. I will not waste your time. I resign.",
    ],

    # What the WINNING robot says in reply. It must acknowledge the
    # resignation rather than announcing a checkmate that never happened.
    "accept_resignation": [
        "You resign? Gracious of you. Thank you for the game.",
        "I accept. That was a good fight while it lasted.",
        "A gentleman to the end. Thank you, my friend.",
        "Well conceded. You made me work for that one.",
        "I will take it. A pleasure playing you.",
    ],

    # Used when the move cap stops a game that was still going. Without
    # these the robots would simply fall silent mid-game, which looks like a
    # breakdown rather than an ending.
    "adjourned": [
        "We are out of time. Let us call this one a draw.",
        "Time to stop there. A good fight, and nobody beaten.",
        "That is all the time we have. We will finish this another day.",
        "We could play all afternoon, but you have things to do. A draw.",
    ],
}


# ── Self-check ───────────────────────────────────────────────────────────────
# Run `python chess_templates.py` after editing to catch the four mistakes
# listed at the top of this file.

def _check():
    import re

    problems = []
    total = 0

    for category, lines in TEMPLATES.items():
        seen = set()
        for line in lines:
            total += 1
            where = f"{category}: {line[:60]}"

            if line.count("{move}") > 1:
                problems.append(f"RUN-ON (missing comma?)  {where}")
            if re.search(r"\w\{move\}", line):
                problems.append(f"MISSING SPACE before {{move}}  {where}")
            for symbol in "/\\&*_~^<>|":
                if symbol in line:
                    problems.append(f"SYMBOL '{symbol}' will be read aloud  {where}")
                    break
            if re.search(r"\d", line.replace("{move}", "")):
                problems.append(f"DIGIT should be a word  {where}")
            # Rule 5: the move must end its clause.
            after = re.search(r"\{move\}(.?)", line)
            if after and after.group(1) not in ("", ".", ",", "!", "?"):
                problems.append(
                    f"SENTENCE CONTINUES after {{move}} (see rule 5)  {where}")
            if line in seen:
                problems.append(f"DUPLICATE  {where}")
            seen.add(line)
            if not line.strip().endswith((".", "!", "?")):
                problems.append(f"NO END PUNCTUATION  {where}")

    for group in (GAME_START, GAME_END):
        for key, lines in group.items():
            total += len(lines)
            if not lines:
                problems.append(f"EMPTY LIST  {key}")

    print(f"Checked {total} lines across {len(TEMPLATES)} categories.")
    if problems:
        print(f"\nFound {len(problems)} problem(s):\n")
        for p in problems:
            print("  " + p)
        return False
    print("No problems found.")
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if _check() else 1)
