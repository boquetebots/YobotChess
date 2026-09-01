# START HERE — Raspberry Pi

A Pi in this system is a **player controller**. It drives one robot: it asks
the game "what do I say and how do I move?", says it with the mouth moving,
and animates the head and eyes between turns.

**The Pi holds no chess knowledge at all.** No board, no engine, no rules.
That lives on whichever machine is running `chess_server.py`, and it is
deliberate — one board, one game, no chance of the two robots quietly playing
different games.

A Pi *can* run the whole show if you want it to. It just usually doesn't.

---

## Before you start

> **Do I need OhbotPi2 on this machine?** Only if a robot is plugged into it.
> The game, the display and all the test scripts run without it. And chess
> never asks you for an Azure key — it borrows OhbotPi2's. See *What each
> machine actually needs* in `README.md`.


**The Pi needs the OhbotPi2 project on it already, and working.** That is
where the motors, the voice and the lip sync come from. If the robot cannot
say hello yet, stop here and get that going first:

<https://github.com/boquetebots/OhbotPi>

You also need to know the **name or address of the computer running the
game** — usually the Windows PC. On a Tailscale network the name is enough
(`pibot`, `lester-pc`); otherwise get its address with `ipconfig` on Windows
or `hostname -I` on a Pi.

---

## 1. Get the files onto the Pi

Log in over SSH, then:

```bash
cd ~/Projects
git clone https://github.com/boquetebots/YobotChess.git Chess
cd Chess
```

Later on, to pick up any changes:

```bash
cd ~/Projects/Chess
git pull
```

---

## 2. Run the installer

```bash
bash install.sh
```

It finds OhbotPi2, installs the three Python add-ons **into the same Python
that OhbotPi2 uses**, installs Stockfish, and writes two short run scripts.

> **Why "the same Python" matters.** OhbotPi2 on a Pi runs inside a virtual
> environment — its own private Python at `~/Projects/Ohbot/venv`. If the
> chess add-ons get installed into the *system* Python instead, you get
> "no module named chess" from a robot that is otherwise perfectly healthy,
> and nothing about the message tells you why. The installer handles this;
> it is only a problem if you install by hand.

The installer asks for your password once, for Stockfish.

---

## 3. Prove the robot works, on its own

No game, no server, no other computer:

```bash
~/Projects/Ohbot/venv/bin/python3 chess_player.py --say-once
```

It should say one sentence **with its mouth moving**. If the mouth stays shut
or the robot stays silent, the fault is in OhbotPi2, not here — see
`HARDWARE_TEST.md`.

You can also watch it move with no speech and no chess at all:

```bash
~/Projects/Ohbot/venv/bin/python3 chess_player.py --animate-demo
```

And see the audience display with nothing plugged in at all:

```bash
bash demo.sh
```

Then open `http://THE-PI-NAME:8080/` from any browser on the network.

---

## 4. Point it at the game

Open **`play-white.sh`** (or `play-black.sh`) in a text editor. One line needs
changing:

```bash
SERVER="localhost"
```

Put the name or address of the computer running the game between the quotes.
Save.

Then start the robot:

```bash
bash play-white.sh
```

Do this on each robot's machine, one colour each. Start the game from the
display's buttons, or from the machine running the server.

> **`--start` goes on ONE robot only.** If both send it they reset each
> other's game and nothing ever gets past the first move.

---

## 5. Firewall

The Pi has to be able to reach the server's ports **8001** (white) and
**8002** (black). Pis do not normally block outgoing connections, so this is
almost always a setting on the *other* machine — Windows blocks incoming
connections by default. `MAC_SETUP.md` has the exact command for opening it.

Test it from the Pi before blaming anything else:

```bash
curl http://THE-SERVER-NAME:8001/state
```

Some JSON means the network is fine. A hang or "connection refused" means the
server is not running, or the firewall is in the way.

---

## Running two robots from two Pis

That is the normal setup once you have two. Each Pi runs its own
`chess_player.py`, both pointing at the **same** server:

| Machine | Runs |
|---|---|
| PC (or one of the Pis) | `chess_server.py` and `chess_show.py` |
| Pi number one | `bash play-white.sh` |
| Pi number two | `bash play-black.sh` |

---

## Starting automatically

There is no systemd service for chess, on purpose. The chess player competes
with the Greeter for the robot's one serial cable, so a chess service that
started at boot would fight the robot's normal job every time. Start it when
you want a game, stop it when you are done.

If you do want one later, copy the pattern from OhbotPi2's user services —
they run with no `sudo`, which is the whole trick.

---

## Where to go next

| I want to… | Read |
|---|---|
| Understand the display and its buttons | `SHOW_SETUP.md` |
| Let a guest play against a robot | `HUMAN_GAME.md` |
| Change what the robots say | `chess_templates.py` |
| Change how the robots move | the numbers at the top of `chess_animation.py` |
| Work out why a robot is silent or still | `HARDWARE_TEST.md` |
