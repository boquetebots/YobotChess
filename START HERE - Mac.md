# START HERE — Mac

A Mac in this system usually drives **the second robot** — Goldie — while the
Windows PC runs the game. It can also run the whole show on its own.

The full two-machine walkthrough, with the firewall commands and the
calibration trap, is **`MAC_SETUP.md`**. This page is the short version.

> **Do I need OhbotPi2 on this machine?** Only if a robot is plugged into it.
> The game, the display and all the test scripts run without it. And chess
> never asks you for an Azure key — it borrows OhbotPi2's. See *What each
> machine actually needs* in `README.md`.

---

## 1. Get the files

```bash
cd ~/Projects
git clone https://github.com/boquetebots/YobotChess.git Chess
cd Chess
```

Putting it in `~/Projects` next to `OhbotPi2` is worth doing — chess looks
there for the robot code without being told.

---

## 2. Run the installer

```bash
bash install.sh
```

It finds OhbotPi2, installs the three Python add-ons into the same Python it
uses, installs Stockfish through Homebrew if you have it, and writes two short
run scripts.

**No Homebrew?** That is fine on a Mac that is only driving a robot — only the
machine running `chess_server.py` needs the engine. Install Homebrew from
<https://brew.sh> if this Mac is going to run the game.

---

## 3. Prove the robot works, on its own

```bash
~/yobot-venv/bin/python3 chess_player.py --say-once
```

One sentence, **with the mouth moving**.

> **Use `~/yobot-venv/bin/python3`, not plain `python3`.** The Mac's own
> Python does not have the robot's packages in it, and the error you get
> says nothing helpful about why. `install.sh` puts the chess add-ons in
> the same place, so this one command has everything. If not, the fault is in OhbotPi2 —
see `HARDWARE_TEST.md`.

---

## 4. Join a game running on the PC

Open **`play-black.sh`** and put the PC's address in the `SERVER` line:

```bash
SERVER="192.168.50.42"
```

Then:

```bash
bash play-black.sh
```

There is also **`chess_show_agent.py`**, which lets the PC's "Start Goldie"
button launch her over the network so you do not have to touch the Mac at
all. `MAC_SETUP.md` covers it.

---

## 5. Or run the whole thing here

```bash
~/yobot-venv/bin/python3 chess_show.py --strength club --gap 0.8
```

Then open <http://localhost:8080/>. With nothing plugged in at all:

```bash
~/yobot-venv/bin/python3 chess_show.py --demo
```

---

## The one that will catch you out

**Each computer keeps its own calibration.** `MotorDefinitionsv21.omd` is
deliberately *not* shared through git — sharing it once handed Goldie
Lester's mouth. Saved robots in `ohbotData/robots/` **are** shared, and
loading the one you want from that library is how a calibration is supposed
to travel between machines.

`MAC_SETUP.md` has the details, including what to do before your next
`git pull` in OhbotPi2.
