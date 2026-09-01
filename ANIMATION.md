# Making the robots move

Until now the robots spoke and their mouths moved, and nothing else about them
did. No head turns, no looking at the board, no looking up at the audience.
That is the difference between a talking head and a performer.

There are now two states, and a robot is always in exactly one of them.

**Waiting** — the other side is thinking. Head down at the board, eyes darting
about with the head drifting after them, an occasional blink, mouth shut, and
**the eyes showing how the game is going for this robot** — green when it is
ahead, amber when it is level, red when it is losing.

**Announcing** — this robot is speaking. Head up towards the audience,
drifting gently so it does not look like a broken puppet, blinks, **eyes
blue**, and the mouth left strictly alone for the lip sync to drive.

The chess, the commentary, the display and the speaking floor are untouched.
The only change to the server is that it now says who is winning on every
reply a robot gets — a number it was already working out for the bar on the
display.

**A robot with no LED eyes ignores all the colour.** The commands are plain
serial messages and the board discards them. There is nothing to switch off
and nothing to configure: fit LEDs and they light up.

---

## Try it

**With no robot, no Azure and nothing installed:**

```
python test_animation.py
```

Takes about twenty seconds. It drives a pretend robot that writes down every
command it is given, then reads the list back. Silence means all is well.

**With a real robot, but no chess server and no speech:**

```
python chess_player.py --animate-demo
```

Half a minute of waiting pose, then the announce pose, then back. This is the
one to use when tuning — running a whole game to see whether the head is a bit
too far left would take an afternoon.

**With a real robot, speaking:**

```
python chess_player.py --say-once
```

The head should come up off the board to say the sentence and go back down
afterwards.

---

## Changing how they move

**Everything is at the top of `chess_animation.py`,** in one block, each
number with a line saying what it does. Same idea as `chess_templates.py`
being the one place to change what they *say*. Change a number, run
`--animate-demo`, watch. You do not need to read the rest of the file.

The numbers mean the same as the sliders in the Sequence Builder:

| Motor | 3 | 5 | 7 |
|-------|---|---|---|
| `HEADTURN`, `EYETURN` | right | straight ahead | left |
| `HEADNOD`, `EYETILT` | down | level | up |
| `LIDBLINK` | — | — | 0 shut, 10 wide open |

### The waiting numbers

| Setting | Now | What it does |
|---------|-----|--------------|
| `WAIT_HEAD_NOD` | 3 | how far down the head sits. This is "looking at the board" |
| `WAIT_TURN_MIN` / `MAX` | 3 / 7 | how far left and right the head wanders |
| `WAIT_TILT_MIN` / `MAX` | 3 / 7 | how far the EYES look up and down. The head stays put |
| `WAIT_LIPS` | 5 | mouth closed. 5 is where the lips just touch |
| `WAIT_EYE_LEAD` | 0.5s | how long the eyes get there before the head follows |
| `WAIT_PAUSE_MIN` / `MAX` | 0 / 2s | how long it holds still between looks |

### The announcing numbers

| Setting | Now | What it does |
|---------|-----|--------------|
| `ANNOUNCE_HEAD_NOD` | 7 | head up, off the board |
| `ANNOUNCE_FACE` | 6 | where the audience is. `--face` overrides it |
| `ANNOUNCE_SWAY` | 0.5 | how far it drifts either side of those two |
| `ANNOUNCE_HOLD_MIN` / `MAX` | 0.4 / 0.9s | how often it drifts |

### Blinking, the same in both states

| Setting | Now | What it does |
|---------|-----|--------------|
| `BLINK_OPEN` | 10 | lids up |
| `BLINK_SHUT` | 2 | how far they close. Not 0 — a soft blink |
| `BLINK_GAP_MIN` / `MAX` | 2 / 6s | random gap between blinks |
| `BLINK_HOLD` | 0.15s | how long the lids stay down |

### The eye colours

| Setting | Now | What it does |
|---------|-----|--------------|
| `COLOUR_WINNING` | 0, 10, 0 | well ahead — green |
| `COLOUR_LEVEL` | 10, 5, 0 | nothing in it — amber |
| `COLOUR_LOSING` | 10, 0, 0 | well behind — red |
| `COLOUR_ANNOUNCE` | 0, 3, 10 | this robot is speaking — blue |
| `EVAL_FULL` | 500 | how big a lead counts as fully green, in hundredths of a pawn. 500 is about a rook |
| `EVAL_POINT_OF_VIEW` | `mine` | `mine` = each robot shows its own fortunes. `white` = both match the bar on the display |

Each colour is red, green and blue, each from 0 to 10. To see the whole range
printed out without running anything:

```
python chess_animation.py
```

**Lower `EVAL_FULL` and the eyes react to small advantages; raise it and only
a thumping lead shows.** It is the dial to turn if the colours look either
hysterical or dead.

**`EVAL_POINT_OF_VIEW` is the one to know about.** As it stands, each robot
shows its own game, so the two of them are usually *opposite* colours — one
green, one red. That is the point: you can see who is winning by looking at
the robots rather than the screen. If it ever reads as "that one is broken",
setting it to `white` makes both robots show the same thing as the display's
bar and they always match.

---

## Two settings on the command line

**`--face`** — where this robot looks when it announces a move.

```
python chess_player.py --colour white --face 6.5
```

It is a setting rather than a fixed number because Lester and Goldie will not
be sitting at the same angle to the audience, and the fix has to be something
you can change on the day.

**`--no-animation`** — talk without moving anything but the mouth.

```
python chess_player.py --colour white --no-animation
```

The get-out-of-jail switch. If the movement misbehaves five minutes before a
show, this puts the demo back to exactly how it was last week.

---

## Four things worth knowing before changing any of it

### The announce state must never touch the lips

This is the important one. While a robot is speaking, the lip sync drives
`TOPLIP` and `BOTTOMLIP` from Azure's mouth shapes, thirty-odd times a second.
Anything else sending lip commands at the same moment is two programs fighting
over one servo, and what comes out is a mouth that stutters and words nobody
can lip-read.

So the mouth is closed once, on the way into the waiting state, and never
touched again by anything in `chess_animation.py`. `test_animation.py` counts
lip commands during an announcement and expects zero.

### Switching state has to WAIT for the old movement to stop

Setting a flag and carrying on would leave the previous state's loops alive
for up to a second — long enough to send one more command. Then the waiting
loop pulls the head down to the board in the middle of the announcement and
the announce loop pulls it back up.

On hardware that is a twitch you cannot account for by reading either loop,
because neither loop is wrong. It is the handover that is wrong. Taking the
`await` out of `_switch_to()` makes two checks fail, which is the only way to
know they work.

### The animation is stopped before the cable is released, and that order is load-bearing

Every movement is posted to a queue inside the controller, and those queues
hold ten commands. Stopping the controller shuts down the workers that empty
them — and an animation loop still running at that point posts an eleventh
command to a queue nobody is emptying, then waits for room that never comes.

Swapping those two lines in `shut_down()` and shrinking the queues hangs
**every single time**. What you would actually see is a game that finishes,
says goodbye, prints "robot released" — and then sits there still holding the
cable, so the next thing you start says "robot not found". Two symptoms,
neither one pointing at shutdown.

`test_animation.py` reads `chess_player.py` and refuses the wrong order. It
reads it as code rather than as text, because the comment explaining the order
has to mention the two calls in the opposite sequence.

### The colour only goes down the cable when it changes

`set_eval()` is called on every answer from the server, which is twice a
second for the whole game. The LEDs share the one serial cable with all eight
motors and with the lip sync, so repainting them on every poll would be a few
thousand pointless messages competing with the mouth. `_set_eyes()` remembers
what the eyes were last actually told and says nothing when it has not
changed.

### Blue holds for the whole sentence

The position can move while a robot is still talking — the turn flips the
instant a move is played, and the opponent's evaluation lands before this
robot has finished its line. The eyes must not follow it. A robot announcing
its own checkmate while its eyes turn red is telling the audience two
different things at once. `set_eval()` stores the new number and shows it
when the robot goes back to waiting.

### The evaluation has to be flipped for Black

The server reports it the way the display needs — positive is good for White,
always. A robot wants to know whether *it* is winning, which is not the same
thing when it is playing Black. `eval_from_my_side()` is the one place that
flips it.

Get this wrong and the losing robot glows green all game, which would look
completely deliberate. Nothing would break, nobody would get an error, and the
demo would simply be lying.

### Nothing here may ever stop the show

A motor that fails, a cable pulled, a number typed wrong, **a robot with no
LED eyes** — none of that may bring down a robot in front of people. Every
movement and every colour is wrapped so a failure prints one line and carries
on. Animation is decoration; the game is the point. The test pulls the cable
on purpose half way through, and runs a whole sequence on a robot whose LEDs
throw an error every time they are touched, and checks the head still moves
and the game still runs.

---

## What is not built

**They do not look at each other, and they do not look at the board they are
actually playing on.** The waiting head wanders at random. It does not know
where the pieces are, which square was just played, or where the other robot
is sitting.

**They do not react with anything but words and a slow colour change.** A
blunder shifts the eyes towards red over the following moves, but nothing
happens at the moment it lands. The commentary already knows which moments
are dramatic — `is_dramatic()` in `chess_commentary.py` — and the server
could hand a mood across with the sentence, so a robot could flash red on a
blunder, look away, or lean in on a checkmate. The plumbing for it now exists:
the reply the robot gets already carries one piece of game state, and a
second would go the same way.

**There is no animation while a guest is thinking.** A human takes far longer
over a move than Stockfish does, so that is the state an audience will see
most of. It currently gets the same wandering as any other wait.
