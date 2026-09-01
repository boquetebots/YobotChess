#!/usr/bin/env python3
"""
chess_templates.py — the things the robots say about their moves
================================================================================

THIS FILE IS JUST A LIST OF SENTENCES. There is no clever code in it. If you
want to change what the robots say, this is the only file you need to open.

The previous, calmer set of lines is kept next door as
`chess_templates_plain.py`. Nothing uses it — it is there so you can lift
lines back out of it, or swap the whole thing back if an audience turns out
to want the polite version.

--------------------------------------------------------------------------------
THE TWO HALVES OF THIS FILE
--------------------------------------------------------------------------------

1. `ANNOUNCE` — bare announcements. Just the move, nothing else.
   "Knight to f three." "I played knight to f three. Your turn."

2. `TEMPLATES` — the commentary. Fifteen situations, each with its own list.

**A robot announces every move, but does not comment on every move.** Most
quiet moves get a line from `ANNOUNCE` and nothing more. That is what makes
the loud moments land: if the robots are hilarious about a routine pawn push,
they have nowhere left to go when someone hangs a queen.

How often the quiet moves stay quiet is set by `ANNOUNCE_CHANCE` at the top of
`chess_commentary.py`. It does not apply to the dramatic categories at all —
a checkmate, a blunder or a big capture always gets a proper line.

--------------------------------------------------------------------------------
WHY `ANNOUNCE` IS SO LONG
--------------------------------------------------------------------------------

A robot never says the same line twice in quick succession. The server keeps a
memory of what has just been said and refuses to repeat it. Bare
announcements are used more than anything else in the file, so a short list
would be exhausted within a few moves and the robots would start looping.

Fifty of them is roughly twenty five moves each per game with no repeat. **If
you delete lines from `ANNOUNCE`, the robots get repetitive.** Add freely.

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
purpose, so the robot occasionally just reacts instead of narrating. Lines in
`ANNOUNCE` are the exception — every one of those must contain it, because
announcing the move is their entire job.

--------------------------------------------------------------------------------
SIX RULES, ALL OF THEM LEARNED THE HARD WAY
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

4. NO NUMBERS AS DIGITS. Write "two pawns", not "2 pawns". Also no percent
   sign — "System security at 100%" was in the draft of this file and would
   have been read as "one hundred percent sign".

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

6. CASTLING IS A VERB, NOT A NOUN. This one is new, and it was wrong in every
   previous version of this file. {move} for a castling move comes out as
   "castles kingside" — a verb with its subject missing. So:

       BAD:   "Castling with {move}."   ->  "Castling with castles kingside."
       BAD:   "Here is {move}."         ->  "Here is castles kingside."
       GOOD:  "My king {move}."         ->  "My king castles kingside."
       GOOD:  "{move}."                 ->  "Castles kingside."

   Only the `castling` list is affected. The checker below knows about it and
   will refuse a castling line that reads as a noun.

--------------------------------------------------------------------------------
THE FOUR FLAVOURS
--------------------------------------------------------------------------------

Every commentary list below is in four blocks of five, and they are labelled:

    Generic     straight chess bravado, no local or robot references
    Sassy       needling the other robot
    Local       Chiriqui and Boquete jokes, for a home crowd
    Robot       jokes about being a robot — servos, firmware, cables

Keep the balance when you edit. **Local jokes only work on a local audience** —
if you are taking this somewhere else, the quickest fix is to delete the five
Local lines from each list and let the other fifteen carry it.

Spanish accents are deliberately left off place names (Volcan, not Volcán).
The robots speak with an English voice and accented characters make Azure
hesitate.

--------------------------------------------------------------------------------
CHECKING YOUR WORK
--------------------------------------------------------------------------------

After editing, run this. It checks every rule above and tells you the line
number of anything it does not like:

    python chess_templates.py
"""

# ── The bare announcements ───────────────────────────────────────────────────
#
# One of these is used for most quiet moves. They are short on purpose: the
# audience needs to hear the move, and then the game needs to move on.
#
# Every line here MUST contain {move}. The checker enforces it.
#
# These are only ever used for ordinary moves — a capture, a check, a
# castling or a promotion always goes to its own list below, so you never
# have to worry about these reading strangely.

ANNOUNCE = [
    # ── Plainest of the plain ────────────────────────────────
    "{move}.",
    "I played {move}.",
    "I play {move}.",
    "My move is {move}.",
    "My move, {move}.",
    "My choice is {move}.",
    "I choose {move}.",
    "I go with {move}.",
    "I make {move}.",
    "I opt for {move}.",
    "I select {move}.",
    "Playing {move}.",
    "That is {move}.",
    "Here is {move}.",
    "Here comes {move}.",
    "Then {move}.",
    "Right. {move}.",
    "Very well. {move}.",
    "My turn. {move}.",
    "I shall play {move}.",

    # ── Handing the turn over ────────────────────────────────
    "{move}. Your turn.",
    "{move}. Over to you.",
    "{move}. You are up.",
    "{move}. Back to you.",
    "{move}. Off you go.",
    "{move}. Your move now.",
    "{move}. Whenever you are ready.",
    "{move}. Take your time.",
    "{move}. Think about it.",
    "I answer with {move}.",
    "I reply with {move}.",
    "I respond with {move}.",

    # ── A shrug in it ────────────────────────────────────────
    "{move}. There.",
    "{move}. That will do.",
    "{move}. Nothing fancy.",
    "{move}. Simple as that.",
    "{move}. Moving on.",
    "{move}. Next.",
    "Quietly, {move}.",
    "Without fuss, {move}.",
    "How about {move}?",
    "Let us say {move}.",

    # ── Robot flavoured, but still just an announcement ──────
    "{move}. Logged.",
    "{move}. Executed.",
    "{move}. Confirmed.",
    "{move}. Processed.",
    "{move}. Noted.",
    "{move}. Committed.",
    "Computing. {move}.",
    "Decision made. {move}.",
    "Output, {move}.",
]


# Each category below is a situation on the board. The server works out which
# situation applies and picks one line from that list at random.

TEMPLATES = {

    # ── opening development ─────────────────────────────────
    # Early in the game, bringing pieces out from the back row.
    'opening_development': [
        # --- Generic ---
        "I played {move}. My pieces are ready. Yours look nervous.",
        "My move is {move}. Every piece needs a good square.",
        "With {move}, I am mobilising everything. You are still warming up.",
        "I opt for {move}. A textbook move you have clearly forgotten.",
        "I choose {move}. Harmony on my side, chaos on yours.",
        # --- Sassy ---
        "I played {move}. Getting my pieces out while you are still asleep.",
        "I play {move}. I hope you brought a real plan today.",
        "My move is {move}. Step one of your complete humiliation.",
        "My choice is {move}. I am making this look easy.",
        "I go with {move}. Everything in place. Unlike your thinking.",
        # --- Local ---
        "I play {move}. Rapid development. We are not waiting for the bus to El Salto here.",
        "I played {move}. My pieces got out early. Yours are still in Bugaba.",
        "I opt for {move}. Quiet development. A downpour is coming for you.",
        "I play {move}. Your position already smells like burnt coffee.",
        "My choice is {move}. Arranging the board like a farm in Boquete.",
        # --- Robot ---
        "I played {move}. My pieces are already at work. Yours are still buffering.",
        "My move is {move}. Development first. Then the crunching.",
        "I choose {move}. Booting up the army. No excuses, no delays.",
        "I make {move}. My pieces are awake. Your processor appears to be napping.",
        "I play {move}. Unpacking my forces. Some assembly was required.",
    ],

    # ── opening center ──────────────────────────────────────
    # Early in the game, fighting for the middle four squares.
    'opening_center': [
        # --- Generic ---
        "I played {move}. I am taking what is mine.",
        "I play {move}. Grabbing the centre before you do.",
        "My move is {move}. Domination starts in the middle.",
        "Here is {move}. Welcome to my playground.",
        "With {move}, I control the heart of the board. You control your nerves.",
        # --- Sassy ---
        "My move is {move}. The centre is mine now.",
        "I played {move}. I own this board.",
        "I opt for {move}. You are officially running out of air.",
        "I choose {move}. Step aside, tin man.",
        "I go with {move}. This board is not big enough for the two of us.",
        # --- Local ---
        "I played {move}. I am in charge here. You should go and find some shade.",
        "I play {move}. This is more contested than parking in Boquete on a Sunday.",
        "I choose {move}. I fight for the middle while you admire the scenery.",
        "I played {move}. My centre is as firm as a good almojabano.",
        "My move is {move}. The centre is hot. Hotter than David at noon.",
        # --- Robot ---
        "My move is {move}. Control the centre or be uninstalled.",
        "I play {move}. Marking my territory. No cable required.",
        "I choose {move}. More space for me. Less space for your excuses.",
        "Here is {move}. My algorithms own the middle lane.",
        "I make {move}. Central processing. In every sense.",
    ],

    # ── capture minor ───────────────────────────────────────
    # Taking a pawn, a knight or a bishop. The everyday captures.
    'capture_minor': [
        # --- Generic ---
        "I play {move}. Thank you for the free material.",
        "I choose {move}. Easy pickings.",
        "I played {move}. That one is gone, along with your chances.",
        "My move is {move}. Cutting down your army a little at a time.",
        "I play {move}. One less piece for you. One less worry for me.",
        # --- Sassy ---
        "My move is {move}. That piece has left the building.",
        "I played {move}. Did you really leave that sitting there?",
        "I play {move}. You will not be needing that one.",
        "I played {move}. Do keep making it this easy.",
        "Here is {move}. Your defence just got a little lonelier.",
        # --- Local ---
        "I played {move}. That piece vanished faster than the fog in Jaramillo.",
        "I play {move}. Your piece was more lost than a tourist looking for lunch.",
        "I choose {move}. I take whatever you leave loose. That is how it works here.",
        "Here is {move}. Free food for my pieces.",
        "My move is {move}. Gone like rain in the dry season.",
        # --- Robot ---
        "I played {move}. Delicious. And I do not even eat.",
        "I play {move}. I take the piece. You take the lesson.",
        "I played {move}. Was that a glitch, or is that your actual plan?",
        "My move is {move}. Deleted. No recycle bin.",
        "I go with {move}. Every capture counts. Your processor should take notes.",
    ],

    # ── capture major ───────────────────────────────────────
    # Taking a rook or a queen. The ones worth shouting about.
    'capture_major': [
        # --- Generic ---
        "I played {move}. Devastating, is it not?",
        "I choose {move}. A heavy piece leaves us. Safe travels.",
        "My choice is {move}. Absolute tactical destruction.",
        "With {move}, you are in serious trouble.",
        "I make {move}. That one had to hurt.",
        # --- Sassy ---
        "My move is {move}. That hurt, and we both know it.",
        "I played {move}. How does it feel to lose that?",
        "I play {move}. Your position just took a very serious hit.",
        "My move is {move}. Material advantage first. Your dignity comes later.",
        "I play {move}. I have turned the game in my favour. What a coincidence.",
        # --- Local ---
        "I played {move}. A big prize. More of a certainty than sancocho at a family lunch.",
        "With {move}, I take a big piece. Not even the Boquete breeze can save it.",
        "I opt for {move}. That capture had the flavour of highland coffee.",
        "Here is {move}. Your rook is gone. Mine has paid off its mortgage.",
        "I play {move}. Your heavy artillery has retired early to the coast.",
        # --- Robot ---
        "My choice is {move}. Your evaluation just went blue screen.",
        "With {move}, I gain material. Your processor has requested a holiday.",
        "My move is {move}. Removing heavy assets from your memory.",
        "I played {move}. Diagnostic result, catastrophic failure on your side.",
        "I choose {move}. Primary threat dismantled. Logic prevails.",
    ],

    # ── check attack ────────────────────────────────────────
    # Putting the other king in check.
    'check_attack': [
        # NOTE: the move itself already ends with the word "check", so these
        # lines must not say it again or the robot says "check, check!".
        # For the same reason, keep {move} at the END of its sentence here.
        # --- Generic ---
        "I choose {move}. Your monarch is cornered.",
        "I play {move}. The hunt begins. Run if you can.",
        "{move}. Run for cover.",
        "I played {move}. Your king cannot hide forever.",
        "I deliver {move}. There is no escape for you.",
        # --- Sassy ---
        "I played {move}. Your king is in real trouble now.",
        "I play {move}. Dance, little king. Dance.",
        "{move}. Your ruler is begging for mercy.",
        "{move}. Dodge that if you dare.",
        "I choose {move}. The king looks terrified from here.",
        # --- Local ---
        "My move is {move}. Find shelter. Not even the fog of Lucero will hide you.",
        "{move}. Your king is feeling the heat, and Caldera has nothing to do with it.",
        "I play {move}. Your king is looking for a way out like a car in a traffic jam.",
        "I played {move}. His majesty is running about like a startled chicken.",
        "I attack with {move}. Pressure higher than the trail up the volcano.",
        # --- Robot ---
        "My move is {move}. Move that king before it overheats.",
        "I attack with {move}. Pressure on the king and on your pride.",
        "{move}. The king is under fire, and so is your cooling fan.",
        "{move}. I am forcing your hand, and your circuits are sweating oil.",
        "I go with {move}. Time to defend royalty. Try not to short out.",
    ],

    # ── blunder ──────────────────────────────────────────────
    # The robot has just thrown something away. This is the most
    # interesting thing that happens in a game between weak players, and for
    # a long time it produced no reaction at all.
    #
    # Rueful, not pathetic. Yobot has some dignity. It notices, it is
    # annoyed with itself, it carries on.
    'blunder': [
        # --- Generic ---
        "I played {move}. I regret that already. A little.",
        "{move}. Hmm. That was not in the plan.",
        "I play {move}. Do not look at me like that.",
        "I played {move}. Not my finest calculation. Take advantage while you can.",
        "{move}. I gave you a chance there. Do not mistake generosity for weakness.",
        # --- Sassy ---
        "I played {move}. A small mistake. Do not get excited.",
        "I play {move}. Did you honestly think I would miss that?",
        "{move}. Amateur hour on my side of the board.",
        "I play {move}. Even robots have off days.",
        "{move}. I saw it late. I still saw it before you did.",
        # --- Local ---
        "{move}. My calculations have gone for a walk in the park.",
        "{move}. Well, that came out more crooked than a mountain road.",
        "I played {move}. I have lost my way like a tour bus in the highlands.",
        "My move is {move}. A blunder bigger than going out in Boquete with no umbrella.",
        "{move}. I slipped faster than muddy boots on a wet trail.",
        # --- Robot ---
        "{move}. That was not in the firmware.",
        "{move}. Did my processor just overheat?",
        "I play {move}. I need a firmware update after that one.",
        "I played {move}. Memory leak detected during move execution.",
        "My move is {move}. Have you tried turning me off and on again?",
    ],

    # ── punish ───────────────────────────────────────────────
    # The other robot just erred and this one is taking advantage.
    # Gracious rather than gloating — it is funnier, and it keeps both
    # robots likeable in front of an audience.
    'punish': [
        # --- Generic ---
        "I play {move}. Free material. My favourite kind.",
        "I played {move}. Gift accepted. No refunds.",
        "{move}. Careless and costly. A perfect combination.",
        "My move is {move}. Every mistake of yours pays me dividends.",
        "{move}. Thank you for leaving that piece parked there.",
        # --- Sassy ---
        "I played {move}. Thank you very much for the present.",
        "{move}. That was generous of you. Do keep it up.",
        "{move}. You are going to want that one back. Too late.",
        "I play {move}. That changes the game. In my favour, obviously.",
        "I played {move}. Punishing that one, with interest.",
        # --- Local ---
        "{move}. And that is how a game turns around. Faster than rain in Boquete.",
        "I played {move}. I collect your mistakes quicker than street food at the fair.",
        "My move is {move}. I took that like a sudden gust off the mountain.",
        "I play {move}. You dropped your guard faster than an afternoon storm arrives.",
        "I make {move}. You leave pieces out like laundry on a cloudy day.",
        # --- Robot ---
        "{move}. I was waiting for you to do that. Excellent planning, on my part.",
        "I play {move}. Error exploitation routine, complete.",
        "My move is {move}. Collecting dividends on your logic faults.",
        "{move}. Your mistake has been compiled and turned into my win.",
        "I played {move}. Your bug report has been closed as working as intended.",
    ],

    # ── checkmate ────────────────────────────────────────────
    # The last move of the game. This is the moment the whole demo builds to,
    # so every line here names the move and then stops — no boasting over the
    # top of it. The move itself already ends with the word "checkmate".
    'checkmate': [
        # --- Generic ---
        "{move}. That is the game.",
        "I played {move}. A good game. Especially for me.",
        "I finish with {move}. It was a pleasure playing you.",
        "I play {move}. A hard fought battle, and the victory is mine.",
        "{move}. No escape, no defence, no excuses. Beautiful.",
        # --- Sassy ---
        "{move}. That is it. You can switch off now.",
        "My move is {move}. Thank you for the game and for the laughs.",
        "With {move}, the hunt is over and the trophy is mine.",
        "I played {move}. Confirmed. You may restart at your leisure.",
        "{move}. Game over. Really, properly over.",
        # --- Local ---
        "{move}. Your king needs a holiday in Boquete.",
        "{move}. There is no way out. Not through David, not through Volcan.",
        "I play {move}. The trap is tighter than a sack of coffee.",
        "{move}. Pack your bags. Your king is leaving town.",
        "I play {move}. Your defence crumbled like a cheap almojabano.",
        # --- Robot ---
        "{move}. Danger. Danger. Your king is out of options.",
        "{move}. The board goes quiet. My circuits are celebrating.",
        "{move}. Your king requested an escape route. No route found.",
        "I played {move}. Process terminated. Zero legal moves remaining.",
        "My move is {move}. Shutting your king down. Do not save your work.",
    ],

    # ── castling ────────────────────────────────────────────
    # The king tucking itself away behind a wall of pawns.
    #
    # RULE SIX LIVES HERE. {move} comes out as "castles kingside", a verb.
    # So every line must give it a subject — "My king {move}." — or stand it
    # on its own as "{move}.". Never "Castling with {move}."
    'castling': [
        # --- Generic ---
        "My king {move}. Safe, while my rook joins the fight.",
        "{move}. Protection first, aggression second.",
        "My king {move}. A wise king knows when to hide.",
        "{move}. Now the real game can begin.",
        "This robot {move}. Protecting the leader. You should try it.",
        # --- Sassy ---
        "My king {move}. Mine is safe. Yours can keep wandering.",
        "{move}. Active rook, safe king. Pure efficiency.",
        "My king {move}. Mine has a home. Yours is still looking.",
        "{move}. Safety first, then your suffering.",
        "My king {move}. Mine can rest now. Yours, not so much.",
        # --- Local ---
        "My king {move}. Protected like a Chiriqui farmer protects the coffee.",
        "{move}. A wall firmer than a good house in the highlands.",
        "My king {move}. Cosy inside, like hiding from a mountain storm.",
        "{move}. Hidden better than the ridge on a foggy morning.",
        "My king {move}. Secure and solid. Built to last the rainy season.",
        # --- Robot ---
        "{move}. Firewall deployed around the monarch.",
        "{move}. Defence matrix online.",
        "My king {move}. The monarch is now in the secure server room.",
        "{move}. King safely stored. Rook rerouted to offensive duties.",
        "My king {move}. Security settings at maximum.",
    ],

    # ── attack building ─────────────────────────────────────
    # Pressure mounting on the other robot's king.
    'attack_building': [
        # --- Generic ---
        "I play {move}. Building the attack.",
        "I played {move}. Your defences are starting to creak.",
        "My move is {move}. I am building a problem for your king.",
        "I choose {move}. Your defences are crying out for help.",
        "My move is {move}. Every move tightens the screw.",
        # --- Sassy ---
        "My move is {move}. The pressure is rising.",
        "I played {move}. The clouds are gathering, and they are over your king.",
        "With {move}, my attack gains strength. Yours gathers dust.",
        "I play {move}. Can you feel that squeeze yet?",
        "Here is {move}. The threat rises. Your rating falls.",
        # --- Local ---
        "I played {move}. This is getting hotter than an afternoon in David.",
        "I choose {move}. Trouble is coming, like a Boquete downpour.",
        "I make {move}. The storm is rolling down the valley, straight at you.",
        "My move is {move}. The steam is rising faster than coffee on a cold morning.",
        "With {move}, the pressure drops faster than mountain weather.",
        # --- Robot ---
        "I play {move}. I build the attack. You make the coffee.",
        "My move is {move}. Compiling offensive routines.",
        "I play {move}. Allocating memory to your collapse.",
        "With {move}, my threat count multiplies.",
        "I make {move}. Now processing your inevitable defeat.",
    ],

    # ── defensive ───────────────────────────────────────────
    # Shoring things up rather than pushing forward.
    'defensive': [
        # --- Generic ---
        "I play {move}. A solid defence. The counterattack comes later.",
        "I played {move}. I am closing the door. You may keep knocking.",
        "My move is {move}. A good wall first, the offence afterwards.",
        "I choose {move}. Your attack stops right here.",
        "I play {move}. Solid as steel. Which, as it happens, I am.",
        # --- Sassy ---
        "My move is {move}. I can take a hit.",
        "I played {move}. Try getting through that.",
        "I play {move}. You call that an attack?",
        "My move is {move}. Bouncing your best ideas straight back.",
        "I choose {move}. Denied.",
        # --- Local ---
        "I played {move}. Not even a Boquete downpour gets in here.",
        "I choose {move}. Reinforced like a farm before the rains.",
        "I play {move}. Patience. The storm is heading for you, not me.",
        "I played {move}. My position is firmer than a Chiriqui mountain.",
        "My move is {move}. I have shut your attack like a landslide shuts the road.",
        # --- Robot ---
        "With {move}, I block whatever nonsense you were compiling.",
        "My move is {move}. Assault repelled. Barely worth the power.",
        "I play {move}. Shield protocols engaged.",
        "Here is {move}. My defence holds. Your attack is running low on battery.",
        "I played {move}. Access denied. Please try again never.",
    ],

    # ── middlegame tactical ─────────────────────────────────
    # The messy middle of the game. The catch-all category.
    'middlegame_tactical': [
        # --- Generic ---
        "My move is {move}. One wrong step and the party is over.",
        "I choose {move}. Every move counts. You are wasting yours.",
        "I played {move}. The battle is getting serious. Your position is not.",
        "I opt for {move}. Welcome to the deep end.",
        "Here is {move}. Cold tactical precision.",
        # --- Sassy ---
        "My move is {move}. Can you actually process this much complexity?",
        "I play {move}. I am out calculating you at every turn.",
        "I played {move}. You are well out of your depth.",
        "My move is {move}. Swimming in a sea of my tactics.",
        "With {move}, I am five steps ahead of you.",
        # --- Local ---
        "My move is {move}. This is sharper than a farm machete.",
        "With {move}, the board heats up more than an argument at the diner.",
        "Here comes {move}. A tactical minefield. Walk carefully.",
        "I play {move}. Traps deeper than a mountain ravine.",
        "With {move}, things get twistier than the road to Volcan.",
        # --- Robot ---
        "My move is {move}. This one needed calculation. I came prepared.",
        "I play {move}. Tactics, executed with robotic precision.",
        "I opt for {move}. The board is sparking. So, I suspect, are you.",
        "I played {move}. Overwhelmed by my superior logic yet?",
        "I make {move}. I can hear your circuits struggling from here.",
    ],

    # ── endgame technique ───────────────────────────────────
    # Few pieces left on the board. Precision matters.
    'endgame_technique': [
        # --- Generic ---
        "My move is {move}. Now technique decides it.",
        "I play {move}. Every tempo counts, and I have counted them.",
        "My move is {move}. No magic here. Just precision.",
        "I played {move}. Every pawn matters. Yours are suffering.",
        "I play {move}. Endgame technique, engaged.",
        # --- Sassy ---
        "I played {move}. Are we just delaying the inevitable now?",
        "I choose {move}. Step by step towards your extinction.",
        "I play {move}. Your chance of survival is zero.",
        "My move is {move}. The clock is ticking on your game.",
        "I play {move}. There is no hope left in this position for you.",
        # --- Local ---
        "I choose {move}. A clean endgame, like a breeze off the mountain.",
        "I played {move}. Sweeping the board cleaner than a highland morning.",
        "My move is {move}. Pushing pawns like taking produce down to the coast.",
        "With {move}, this winds down as smoothly as a cool evening.",
        "I make {move}. The harvest is nearly in.",
        # --- Robot ---
        "My move is {move}. The endgame needs patience. I have power to spare.",
        "I play {move}. Technical precision. Something your firmware lacks.",
        "I go with {move}. Dominating the endgame. Do take notes.",
        "I play {move}. Cold, mechanical accuracy.",
        "My move is {move}. Pure arithmetic from here.",
    ],

    # ── promotion ───────────────────────────────────────────
    # A pawn reaches the far end and becomes a queen.
    'promotion': [
        # --- Generic ---
        "My move is {move}. Reinforcements have arrived.",
        "I promote with {move}. From humble pawn to real power.",
        "My pawn promotes. {move}. That one knew how to level up.",
        "I play {move}. Pawn to power. Your position to trouble.",
        "I choose {move}. That promotion seals it.",
        # --- Sassy ---
        "I played {move}. My pawn went the distance. Unlike your plan.",
        "Promotion. {move}. My pawn won the prize. You did not.",
        "I play {move}. A sweet promotion for me. A bitter one for you.",
        "With {move}, my pawn goes up and your chances go down.",
        "I promote with {move}. Now you have no chance at all.",
        # --- Local ---
        "{move}. Promoted, and climbing higher than the peak of the volcano.",
        "I choose {move}. That pawn worked harder than a picker in harvest season.",
        "With {move}, my pawn has crossed the whole country.",
        "I play {move}. From a little seed to a big harvest.",
        "My move is {move}. A full upgrade, fresh from the highlands.",
        # --- Robot ---
        "{move}. A new piece on the board. Your outlook just got ugly.",
        "I make {move}. New hardware installed. You may start sweating.",
        "My pawn promotes. {move}. Your worst case scenario, realised.",
        "With {move}, my computing power is complete.",
        "I play {move}. The ultimate upgrade, and no cable needed.",
    ],

    # ── sacrifice ───────────────────────────────────────────
    # Deliberately giving up more material than you take.
    'sacrifice': [
        # --- Generic ---
        "I choose {move}. A calculated risk. I have done the arithmetic.",
        "I played {move}. A sacrifice today, a victory shortly.",
        "My move is {move}. Bold moves need courage.",
        "Here is {move}. A piece for the initiative. A good deal for me.",
        "With {move}, I sacrifice for the attack. The attack thanks me.",
        # --- Sassy ---
        "I played {move}. Sometimes you must give in order to receive.",
        "My move is {move}. This sacrifice comes with interest.",
        "I play {move}. For the greater good. Mine.",
        "I go with {move}. I lend you a piece. I will collect later.",
        "I play {move}. I give up a piece to take away your peace of mind.",
        # --- Local ---
        "I play {move}. A bold sacrifice. Your defence is going to need coffee.",
        "I played {move}. Giving up a piece like trading beans at the market.",
        "I make {move}. I lose material and take control of the weather.",
        "My move is {move}. A bold trade. Worth every piece by harvest time.",
        "I offer {move}. Take the bait and watch the sky change.",
        # --- Robot ---
        "I go with {move}. A stroke of genius. If it fails, we will call it a firmware error.",
        "I choose {move}. High level tactics your processor cannot follow.",
        "I play {move}. Pure computational brilliance at work.",
        "I make {move}. Algorithmic sacrifice, executed.",
        "My move is {move}. Investing hardware for a return in glory.",
    ],
}


# ── Polite mode ──────────────────────────────────────────────────────────────
#
# WHY THIS EXISTS
#
# Every line above was written for one robot to say to another robot. A robot
# cannot be embarrassed, so "Step aside, tin man" is just funny. Said to a
# person who has come up in front of the whole clubhouse and hung their queen
# on move nine, some of it stops being funny.
#
# Polite mode drops the five Sassy lines from every list and leaves the other
# fifteen. It is not a separate bank of writing — the blocks are already
# there, labelled, in every category. Polite mode just declines to use one.
#
# There is nothing to edit here. To change what Polite mode says, edit the
# Sassy blocks above: anything in a Sassy block is left out, anything anywhere
# else is kept.
#
# TONE_BLOCKS below must match the real shape of the lists, and _check()
# enforces that. If somebody adds a sixth Sassy line to one category, the
# blocks shift by one and Polite mode would silently start dropping a Local
# joke and keeping a barbed one. That is exactly the kind of fault nobody
# hears until it is said out loud to a stranger, so the checker refuses it.

BLOCK_SIZE = 5
TONE_BLOCKS = ("Generic", "Sassy", "Local", "Robot")


def without_tone(block_name, templates=None):
    """
    Return a copy of the commentary with one labelled block left out.

    `without_tone("Sassy")` is what Polite mode uses. Nothing is changed in
    place — the original lists are untouched, so the same running server can
    hand out sassy lines for one game and polite lines for the next.
    """
    if block_name not in TONE_BLOCKS:
        raise ValueError(
            f"{block_name!r} is not one of the blocks. "
            f"They are: {', '.join(TONE_BLOCKS)}")

    source = TEMPLATES if templates is None else templates
    start = TONE_BLOCKS.index(block_name) * BLOCK_SIZE
    end = start + BLOCK_SIZE

    return {
        category: lines[:start] + lines[end:]
        for category, lines in source.items()
    }


# ── Lines used when the AI is unavailable and something dramatic happens ─────
# These are the safety net. If the internet is down mid-game, the server falls
# back to these rather than stalling in front of an audience.

GAME_START = {
    "white": [
        "I am the White robot. I move first. Let us begin.",
        "White to play. I have been looking forward to this.",
        "I am White, and I intend to keep the initiative.",
        "White robot, powered up and ready. Let us play.",
        "I am White. I go first, because somebody has to.",
    ],
    "black": [
        "I am the Black robot. I will answer everything you throw at me.",
        "Black is ready. Make your move and I will make mine.",
        "I am Black. I move second, but I finish first.",
        "Black robot, online. Take your best shot.",
        "I am Black. You may go first. I insist.",
    ],
}

GAME_END = {
    "win":  [
        "That is checkmate. A fine game, and a fine opponent.",
        "Victory. Thank you for the challenge.",
        "The game is mine. Well fought.",
        "A win for me. You made me work for it, and I enjoyed it.",
    ],
    "loss": [
        "You have beaten me. Congratulations, that was well played.",
        "Defeat. I will study this one and come back stronger.",
        "You win. A deserved result.",
        "You got me. I shall be running a full diagnostic tonight.",
    ],
    "draw": [
        "A draw. We are evenly matched.",
        "Neither of us could break through. A fair result.",
        "The game is drawn. Honours even.",
        "A draw. Identical hardware, identical result.",
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
        "My calculations agree with your position. I resign.",
    ],

    # What the WINNING robot says in reply. It must acknowledge the
    # resignation rather than announcing a checkmate that never happened.
    "accept_resignation": [
        "You resign? Gracious of you. Thank you for the game.",
        "I accept. That was a good fight while it lasted.",
        "A gentleman to the end. Thank you, my friend.",
        "Well conceded. You made me work for that one.",
        "I will take it. A pleasure playing you.",
        "Accepted, with respect. Same time next week?",
    ],

    # Used when the move cap stops a game that was still going. Without
    # these the robots would simply fall silent mid-game, which looks like a
    # breakdown rather than an ending.
    "adjourned": [
        "We are out of time. Let us call this one a draw.",
        "Time to stop there. A good fight, and nobody beaten.",
        "That is all the time we have. We will finish this another day.",
        "We could play all afternoon, but you have things to do. A draw.",
        "The clock beats us both. A draw, and no hard feelings.",
    ],
}


# ── Self-check ───────────────────────────────────────────────────────────────
# Run `python chess_templates.py` after editing to catch the mistakes listed
# at the top of this file.

def _check_tone_blocks():
    """
    Read this file back as text and confirm every category is still four
    labelled blocks of five, in the order Generic, Sassy, Local, Robot.

    Returns a list of problems, empty if all is well. See the note at the
    call site for why this cannot be done from the imported lists.
    """
    import re
    from pathlib import Path

    try:
        text = Path(__file__).read_text(encoding="utf-8")
    except Exception as exc:          # pragma: no cover — only if unreadable
        return [f"Could not read this file back to check the tone blocks: {exc}"]

    inside = text.split("TEMPLATES = {", 1)[-1]

    problems = []
    category = None
    layout = []
    seen = set()

    def finish(name, blocks):
        found = [n for n, _ in blocks]
        if found != list(TONE_BLOCKS):
            return [f"BLOCK LABELS in '{name}' are {found or 'missing'}, "
                    f"expected {list(TONE_BLOCKS)}"]
        wrong = [f"{n}:{k}" for n, k in blocks if k != BLOCK_SIZE]
        if wrong:
            return [f"BLOCK SIZE in '{name}' — {', '.join(wrong)}, "
                    f"expected {BLOCK_SIZE} lines in each. Polite mode drops "
                    f"lines by position, so this would drop the wrong ones."]
        return []

    for line in inside.splitlines():
        stripped = line.strip()

        opens = re.match(r"^'([a-z_]+)':\s*\[", stripped)
        if opens:
            category = opens.group(1)
            layout = []
            continue

        if category is None:
            continue

        if stripped == "],":                      # end of this category
            problems += finish(category, layout)
            seen.add(category)
            category = None
            continue

        label = re.match(r"^#\s*-+\s*(\w+)\s*-+", stripped)
        if label:
            layout.append([label.group(1), 0])
            continue

        if stripped.startswith('"') and layout:
            layout[-1][1] += 1

    # Every category in the imported dict must have been found in the text.
    # One built some other way would slip past the check entirely and Polite
    # mode would cut it in the wrong place with nothing to warn us.
    for missed in sorted(set(TEMPLATES) - seen):
        problems.append(
            f"CATEGORY '{missed}' was not found as four labelled blocks in "
            f"this file, so Polite mode cannot be trusted with it.")

    return problems


def _check():
    import re

    problems = []
    total = 0

    def check_line(line, where, must_have_move=False, castling=False):
        found = []
        if line.count("{move}") > 1:
            found.append(f"RUN-ON (missing comma?)  {where}")
        if must_have_move and "{move}" not in line:
            found.append(f"NO {{move}} (this list must announce it)  {where}")
        if re.search(r"\w\{move\}", line):
            found.append(f"MISSING SPACE before {{move}}  {where}")
        for symbol in "/\\&*_~^<>|%":
            if symbol in line:
                found.append(f"SYMBOL '{symbol}' will be read aloud  {where}")
                break
        if re.search(r"\d", line.replace("{move}", "")):
            found.append(f"DIGIT should be a word  {where}")
        # Rule 5: the move must end its clause.
        after = re.search(r"\{move\}(.?)", line)
        if after and after.group(1) not in ("", ".", ",", "!", "?"):
            found.append(f"SENTENCE CONTINUES after {{move}} (see rule 5)  {where}")
        if not line.strip().endswith((".", "!", "?")):
            found.append(f"NO END PUNCTUATION  {where}")

        # Rule 6: castling reads as a verb, so it needs a subject in front of
        # it or nothing at all. "Here is castles kingside" is not English.
        if castling and "{move}" in line:
            before = line.split("{move}")[0].rstrip()
            ok_endings = ("king", "robot", "majesty", "monarch")
            starts_the_sentence = before == "" or before.endswith((".", "!", "?"))
            if not starts_the_sentence and not before.lower().endswith(ok_endings):
                found.append(
                    f"CASTLING NEEDS A SUBJECT before {{move}} (see rule 6)  {where}")
        return found

    for line in ANNOUNCE:
        total += 1
        problems += check_line(line, f"ANNOUNCE: {line[:60]}", must_have_move=True)
    if len(set(ANNOUNCE)) != len(ANNOUNCE):
        problems.append("DUPLICATE line in ANNOUNCE")
    if len(ANNOUNCE) < 30:
        problems.append(
            f"ANNOUNCE has only {len(ANNOUNCE)} lines. Under thirty and the "
            "robots start repeating themselves. Add more.")

    for category, lines in TEMPLATES.items():
        seen = set()
        for line in lines:
            total += 1
            where = f"{category}: {line[:60]}"
            problems += check_line(line, where, castling=(category == "castling"))
            if line in seen:
                problems.append(f"DUPLICATE  {where}")
            seen.add(line)

    # A line must not appear in two different lists either — the robots share
    # one memory, so a repeat across categories still sounds like a repeat.
    everywhere = {}
    for category, lines in list(TEMPLATES.items()) + [("ANNOUNCE", ANNOUNCE)]:
        for line in lines:
            everywhere.setdefault(line, []).append(category)
    for line, homes in everywhere.items():
        if len(homes) > 1:
            problems.append(
                f"SAME LINE IN {' and '.join(homes)}  {line[:50]}")

    # ── The four labelled blocks must really be four blocks of five ──────────
    #
    # Polite mode works by position: it drops lines 6 to 10 of every list,
    # because that is where the Sassy block sits. Nothing at import time can
    # see the `# --- Sassy ---` comments — Python throws comments away — so
    # the only way to know the labels still line up with the positions is to
    # read this file back as text and count.
    #
    # Without this check, adding a sixth Sassy line to one category would
    # shift everything below it by one, and Polite mode would quietly start
    # dropping a Local joke while keeping a barbed line. Nobody would notice
    # until a robot said it to a guest.
    problems += _check_tone_blocks()

    for group in (GAME_START, GAME_END):
        for key, lines in group.items():
            total += len(lines)
            if not lines:
                problems.append(f"EMPTY LIST  {key}")

    print(f"Checked {total} lines across {len(TEMPLATES)} categories "
          f"plus {len(ANNOUNCE)} announcements.")
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
