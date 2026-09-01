# Yobot Chess

**The usual setup: one laptop, one robot, one guest.** Someone sits down, taps
a piece on the screen and plays the robot. It announces its own moves out loud,
comments on theirs, pounces when they give something away, and moves its head,
eyes and mouth while it talks. A Stockfish engine picks the moves.

**Or two robots play each other**, which is the thing to project at a room.
That needs a second computer for the second robot.

Either way there is a 16:9 display with the board, a photo and a clock for each
side, and a bar showing who is winning.

---

## New here? Open one file

| Your computer | Open |
|---|---|
| Windows PC | **`START HERE - Windows.md`** |
| Raspberry Pi | **`START HERE - Raspberry Pi.md`** |
| Mac | **`START HERE - Mac.md`** |

---

## See it with nothing plugged in

After the setup step in your START HERE file:

```
Windows:     double click  "Demo - no robots.bat"
Mac and Pi:  bash demo.sh          (install.sh writes it for you)
```

---

## The two setups

| | What you need | Start it with |
|---|---|---|
| **A guest plays the robot** | one laptop, one robot | `Play a Human.bat` |
| **Two robots play each other** | a laptop *and* a Pi or a Mac, one robot each | `Play Chess.bat` |

The first needs no network at all — it never leaves the laptop. The second does,
because one computer can only hold one robot's cable.

Then open <http://localhost:8080/>.

---

## How the pieces fit together

```
        THE MACHINE RUNNING THE GAME              EACH ROBOT'S MACHINE
        ────────────────────────────              ────────────────────
        chess_server.py                           chess_player.py
          Stockfish, the one shared board,   ◄──►   asks "what do I say?",
          all the commentary                        says it with lip sync,
                                                    and animates the robot
        chess_show.py
          the control desk and the                (no chess knowledge here
          audience display, port 8080              at all - on purpose)
```

**One server, always.** Both robots must talk to the same `chess_server.py`.
If each machine runs its own, they are playing two different games — and the
result looks almost plausible, which is what makes it nasty.

White is port 8001, Black is 8002, the display is 8080.

---

---

## What each machine actually needs

Not every computer needs everything. It depends on what that machine is doing.

| This machine… | Needs Python + the add-ons | Needs Stockfish | Needs OhbotPi2 installed and working |
|---|---|---|---|
| Runs the game and the display | yes | **yes** | no |
| Drives a robot | yes | no | **yes** |
| Does both (the usual Windows PC) | yes | **yes** | **yes** |
| Just the demo, nothing plugged in | yes | no | no |

**Only `chess_player.py` reaches into OhbotPi2.** The server, the display, the
commentary, the templates and every one of the `test_*.py` files run on their
own — which is why you can set the whole show up and watch a full game before a
robot is anywhere near it.

### And the Azure key?

**Chess never asks you for one.** It has no key of its own and no key of its own
to lose. When `chess_player.py` starts, it hands over to OhbotPi2's code, which
reads OhbotPi2's `.env` — the same key that makes the Greeter talk.

So: if the robot can already say hello from OhbotPi2, chess will speak. If it
cannot, fix that there first. There is nothing to set up on this side.

The `.env` file *in the chess folder* is a different thing entirely, and
optional. It holds only two settings, neither of them secret:

```
OHBOT_DIR=D:\Projects\OhbotPi2
STOCKFISH_PATH=C:\somewhere\stockfish.exe
```

You need it only if either of those is somewhere unusual.

## Two projects, not one

This is the chess show. The robot itself — motors, Azure voice, lip sync,
calibration — lives in **OhbotPi2**:

<https://github.com/boquetebots/OhbotPi>

Chess borrows that code rather than keeping a second copy, so a fix in one
place fixes both. A machine with a robot plugged in needs both projects. A
machine only running the game and the display needs only this one.

---

## The files worth knowing about

| File | What it is |
|---|---|
| `Play a Human.bat` | **The everyday one.** A guest plays the robot on this laptop. Two settings at the top, in plain English. |
| `Play Chess.bat` | Two robots playing each other. Needs a second computer. |
| `chess_templates.py` | **What the robots say.** Plain data with a built-in checker. This is nearly always the file you want. |
| `chess_animation.py` | **How the robots move.** Every number is in one block at the top. |
| `chess_server.py` | The engine, the board, the commentary. |
| `chess_player.py` | Drives one robot. Contains no chess logic at all. |
| `chess_show.py` | The control desk and the audience display. |
| `show/index.html` | The display page. Edit the `NAMES` lines to rename the robots on screen. |

---

## The other guides

| Guide | Covers |
|---|---|
| `SHOW_SETUP.md` | The display and its three buttons |
| `HUMAN_GAME.md` | Letting a guest play a robot on a tablet |
| `MAC_SETUP.md` | Two robots on two computers |
| `HARDWARE_TEST.md` | Why a robot is silent, or still, or talking with its mouth shut |
| `ANIMATION.md` | Tuning how they move |
| `STOCKFISH_SETUP.md` | The chess engine, by hand |

---

## Stockfish is not in this download

It is a separate 114 MB program and GitHub refuses any single file that big.

- **Windows** — `SETUP.bat` fetches it for you.
- **Raspberry Pi** — `sudo apt install stockfish`
- **Mac** — `brew install stockfish`

`install.sh` does it for you on the Pi and the Mac. Details in
`STOCKFISH_SETUP.md`.

---

## Requires

Python 3, plus three add-ons (`chess`, `flask`, `python-dotenv`) that the
setup scripts install. Robots are optional — every part of this runs and can
be tested with nothing plugged in.
