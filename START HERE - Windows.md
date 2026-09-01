# START HERE — Windows

The everyday setup is **one laptop, one robot, one guest**. The laptop runs the
chess engine, the robot and the board on screen. Someone sits down, taps a
piece, and plays the robot — which answers out loud, with its mouth moving.

No second computer. No network. No Mac, no Pi.

Two robots playing *each other* is also possible and is further down this page.
Start here.

> **Do I need OhbotPi2 on this machine?** Yes, if a robot is plugged into it —
> that is where the motors and the voice live. The game, the board and all the
> test scripts run without it. And chess never asks you for an Azure key; it
> borrows OhbotPi2's. See *What each machine actually needs* in `README.md`.

---

## 1. Python

Open a Command Prompt and type:

```
python --version
```

A version number means you are fine — go to step 2.

"Not recognised" means it is not installed. Get it from
<https://www.python.org/downloads/>. **When the installer asks, tick the box
that says "Add Python to PATH."** Without that tick nothing here will find it.

---

## 2. Run SETUP.bat

Double click **`SETUP.bat`**. Once, ever.

It installs the three Python add-ons and downloads Stockfish — the program that
actually plays the chess. Stockfish is 114 MB and is not part of this download,
because GitHub refuses any single file that big, so the setup fetches it
instead. **You need to be online for this one run.** After that the whole thing
works offline except for the robot's voice.

Give it a couple of minutes. It checks the engine over at the end and tells you
what it found.

> Antivirus software sometimes eats a freshly downloaded `.exe` with no
> publisher. If setup says the engine will not start, look in the quarantine
> list for "stockfish" and allow it.

---

## 3. Try it with nothing plugged in

Double click **`Demo - no robots.bat`**.

Your browser should open on a chess board, 16:9, with a photo and a clock for
each side, replaying a famous game. That proves Python, the engine, the game
and the display all work — before hardware is anywhere near it.

Close the black window to stop.

---

## 4. Check the robot

A robot plugged into this laptop needs the **OhbotPi2** project on this same
laptop. That is where the motors, the Azure voice and the lip sync come from —
chess has none of its own.

Chess looks for it in these places, in order, and stops at the first one
holding `yobot_core.py`, `ohbot_pi.py` and `ohbot_azure.py`:

1. `OHBOT_DIR` in a file called `.env` next to the chess programs
2. `%USERPROFILE%\Projects\Ohbot` and `%USERPROFILE%\Projects\OhbotPi2`
3. `C:\Projects\OhbotPi2`
4. a folder called `OhbotPi2` or `Ohbot` next to this one

If yours is somewhere else, make a plain text file called `.env` in this
folder with one line in it:

```
OHBOT_DIR=C:\Projects\OhbotPi2
```

Now make the robot say one sentence — no chess, no game, no second computer:

```
python chess_player.py --say-once
```

**Watch the mouth, not just the sound.** If it talks with its mouth shut, or
says nothing at all, the fault is on the OhbotPi2 side and `HARDWARE_TEST.md`
is the walkthrough for it. Sort that out before going on; everything else is
downstream.

---

## 5. Play a guest

Double click **`Play a Human.bat`**.

The board opens on this screen and goes fullscreen. Then, on the control bar:

1. **Start game server**
2. **New game**
3. **Start** the robot — its button says which colour it has taken

The robot welcomes the room and waits. Hand the laptop over. **Tap a piece —
its legal squares light up. Tap one of them.** That is the entire interface;
nobody needs telling twice.

**Leave the black window open while you are playing.** Closing it stops
everything.

### Two settings, at the top of the file

Open `Play a Human.bat` in Notepad. There are exactly two:

- **`GUEST`** — which colour the guest plays. `white` moves first, which is
  what people expect. The robot takes the other one.
- **`STRENGTH`** — leave this alone unless you have a reason. `friendly` is
  deliberate. At club strength a guest loses *every* game and the next person
  stops asking for a turn. Friendly still punishes a free piece, so winning
  means something.

`HUMAN_GAME.md` has the rest: playing as Black, why only one robot is used, and
how to hand the board to a tablet instead of the laptop screen.

---

## Two robots playing each other

The original show, and still the better thing to project at a room. It needs a
**second computer** with the second robot plugged into it — a Pi or a Mac —
because one machine can only hold one robot's cable.

| Machine | Runs |
|---|---|
| This laptop | the game, the display, and robot number one |
| A Pi or a Mac | robot number two |

Double click **`Play Chess.bat`** on this laptop, and follow
**`START HERE - Raspberry Pi.md`** or **`MAC_SETUP.md`** on the other machine.

The settings at the top of `Play Chess.bat` are how strong they play, how long
they pause between turns, and how far behind one has to be before it resigns.

> The second machine has to be able to reach this laptop on ports **8001** and
> **8002**. Windows blocks incoming connections by default, so this is the step
> that catches people. `MAC_SETUP.md` has the exact command. **The guest game
> in step 5 needs none of this** — it never leaves the laptop.

---

## Where to go next

| I want to… | Read |
|---|---|
| The guest game in full | `HUMAN_GAME.md` |
| Understand the display and its buttons | `SHOW_SETUP.md` |
| Set up the second robot | `START HERE - Raspberry Pi.md` or `MAC_SETUP.md` |
| Change what the robots say | `chess_templates.py` — plain text with a built-in checker |
| Change how they move | the block of numbers at the top of `chess_animation.py` |
| Work out why a robot is silent or still | `HARDWARE_TEST.md` |

---

## The one that catches everybody

**Only one program can hold the robot's cable.** The Greeter, the GUI, the
calibration page and the chess player all want the same USB port, and only one
can have it. Stop the others first — the Launcher page in OhbotPi2 is the
traffic cop.
