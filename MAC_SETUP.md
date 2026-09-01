# Step 6 — Black on the Mac, White on Windows

**Written 2026-08-13**, straight after lip sync was confirmed working.

Two robots, two computers, one game.

| Machine | Runs | Robot |
|---------|------|-------|
| Windows PC | `chess_server.py` (the brain) **and** White's player | Lester |
| Mac | Black's player only | Goldie |

**The Windows PC is running the game.** It holds Stockfish, the one shared
board and all the commentary. The Mac holds no chess knowledge at all — it
asks the PC "what do I say?" and says it. That is deliberate: one board, one
Azure key, and no chance of the two robots playing different games.

No new code was needed for this. `chess_server.py` already listens on the
whole network, not just its own machine.

---

## The one thing that will catch you out

**Each computer must keep its own calibration.** The file that says how far
each motor can move — `ohbotData/MotorDefinitionsv21.omd` — was being shared
through git until 13 August. That meant a push from Windows followed by a
pull on the Mac would have handed Goldie *Lester's* mouth.

That is now fixed: the file is in `.gitignore` and no longer tracked. But the
fix has one sharp edge the first time you pull it.

> **On the Mac and on the Pi, before your next `git pull`:**
> make a spare copy of the live calibration, because the pull will delete it.
>
> ```bash
> cd ~/Projects/OhbotPi2/ohbotData
> cp MotorDefinitionsv21.omd MotorDefinitionsv21.SAVED.omd
> ```
>
> After pulling, either copy it back, or better, just load the robot you want
> from the shared library (step 5 below) — which is the whole point of the
> change.

Saved robots in `ohbotData/robots/` are **still shared**, on purpose. That
library is how a calibration gets from one machine to another. What is no
longer shared is *which robot this particular computer is currently holding*.

---

## Part one — on the Windows PC

### 1. Fix EyeTurn

The live settings on Windows have EyeTurn frozen at Min 510, Max 510 — the
same fault the bottom lip had. Lester's eyes cannot look left or right.

The *saved* `Lester.omd` is fine, so this only affects the live file. Open the
calibration page and redo **EyeTurn only** — motors you don't mark are left
completely alone by the save.

**Type `Lester` in the robot name box when you save.** Last time it was left
blank, which is why the good numbers never reached the profile.

Then check it:

```
cd /d D:\Projects\OhbotPi2
python check_motors.py
```

Every motor should say `ok`. This does not block the chess — it only affects
the eyes — but it is two minutes now versus a puzzle later.

### 2. Find the PC's address on your network

```
ipconfig
```

Look for **IPv4 Address** under your active adapter — something like
`192.168.50.42`. Write it down. The Mac needs it.

If it starts `169.254.` the PC is not really on the network; check the wifi
or cable.

### 3. Let the Mac through the Windows firewall

Windows blocks incoming connections by default, so without this the Mac will
sit there saying it cannot reach the server. Open **Command Prompt as
Administrator** (right-click it, "Run as administrator") and paste:

```
netsh advfirewall firewall add rule name="Chess robots" dir=in action=allow protocol=TCP localport=8001-8002
```

You do this once, ever. It opens only those two ports, only for local
connections.

---

## Part two — on the Mac

### 4. Get the Chess folder across

**The Chess project is not in git** — there is no repository and no remote,
unlike OhbotPi2. So it has to be copied by hand. Any of these is fine:

- AirDrop the whole `Chess` folder from the PC (simplest if both are nearby)
- A USB stick
- Over the network, from the Mac:
  ```bash
  scp -r michael@<windows-ip>:/d/Projects/Chess ~/Projects/Chess
  ```

Put it at `~/Projects/Chess`. Leave out `stockfish-windows-x86-64-avx2.exe` —
it is a Windows program and the Mac has no use for it. The Mac never thinks
about chess.

### 5. Tell the Mac which OhbotPi2 to use

This matters more than it looks. `chess_ohbot.py` searches several places for
the robot code, and **it checks `/Volumes/Projects/Ohbot` — the Pi's shared
folder — before the Mac's own copy.** If that share happens to be mounted,
the Mac will quietly run off the Pi's code and, worse, the Pi's calibration.

Pin it down. Make a file called `.env` inside `~/Projects/Chess` containing
one line:

```
OHBOT_DIR=/Users/michael/Projects/OhbotPi2
```

Check it took:

```bash
cd ~/Projects/Chess
~/yobot-venv/bin/python3 chess_ohbot.py
```

It prints the folder it found. Make sure that is the Mac's own path and not
`/Volumes/...`.

### 6. Add the two missing Python packages

The Mac already has a Yobot environment from `SETUP_MacOS.md` at
`~/yobot-venv`, with pyserial, flask and the Azure speech package in it.
Chess needs two more:

```bash
~/yobot-venv/bin/pip install chess python-dotenv
```

Then confirm:

```bash
cd ~/Projects/Chess
~/yobot-venv/bin/python3 chess_needs.py
```

**Always run with `~/yobot-venv/bin/python3`, never plain `python3`.** Plain
`python3` is the Mac's own Python and does not have any of these packages.
That is the trick from `SETUP_MacOS.md` and it still applies here.

### 7. Make the Mac hold Goldie

The Mac's live calibration must be Goldie's, not whatever it had before.
Check what is there now:

```bash
cd ~/Projects/OhbotPi2
python3 check_motors.py
```

The heading says which robot was last loaded. If it is not Goldie, load her —
either from the Launcher page in a browser, or:

```bash
python3 -c "import robot_profiles; print(robot_profiles.load_profile('Goldie'))"
```

Then check again:

```bash
python3 check_motors.py
```

Goldie's profile is known good — all eight motors have travel, and both lips
have a proper centre recorded (TopLip 340, BottomLip 570). If anything says
FROZEN, stop and fix it before going near the chess.

### 8. Make Goldie talk, on her own

Plug Goldie into the Mac. No server, no chess, no network:

```bash
cd ~/Projects/Chess
~/yobot-venv/bin/python3 chess_player.py --colour black --say-once
```

**Watch the mouth.** Both lips, moving with the words, in Black's voice —
which is Guy, lower than White's Jenny, so the two robots don't sound like
one machine talking to itself.

Do not move on until this works. Everything after it depends on it.

---

## Part three — the game

**Three windows, in this order.** The server must be up before either robot.

**Windows, window 1 — the brain:**

```
cd /d D:\Projects\Chess
python chess_server.py --strength club
```

**Windows, window 2 — White:**

```
cd /d D:\Projects\Chess
python chess_player.py --colour white --start
```

**Mac, Terminal — Black:**

```bash
cd ~/Projects/Chess
~/yobot-venv/bin/python3 chess_player.py --colour black --server <windows-ip>
```

Put the real address in place of `<windows-ip>`.

**`--start` goes on White only.** If both robots start a game they keep
resetting each other's and the result is nonsense that looks almost
plausible.

Watch the board from either machine:

```
http://<windows-ip>:8001/board
```

Ctrl-C on each robot when you have had enough. It puts the robot back to
neutral and lets go of the cable on the way out.

---

## When it goes wrong

**Black says it cannot reach the server** — in order: is `chess_server.py`
actually running on the PC; is the address right (`ipconfig` again, addresses
change); did the firewall rule in step 3 get added. Quick test from the Mac,
which needs nothing but a browser:

```
http://<windows-ip>:8001/board
```

If that shows a chessboard, the network is fine and the problem is elsewhere.

**Black waits forever saying "waiting for white to move"** — that message is
correct behaviour, not a crash. It means White has not moved. Check White's
window on the PC. If White never started, it is missing `--start`.

**Both robots talk but they are playing different games** — they are pointed
at different servers. There must be exactly one `chess_server.py` running,
and both robots must name it. If you left a second copy running on the Mac,
stop it.

**"ROBOT NOT FOUND" on the Mac** — something else has the cable. On the Mac
that is usually `yobot_mac.py` or a Greeter session still running. Close it.
Then unplug the USB, wait, plug it back in.

**Goldie's mouth moves oddly** — check step 7 again. The most likely cause is
the Mac holding the wrong robot's calibration, and the most likely reason for
that is a `git pull` since you last loaded her.

**The first word gets clipped** — that is a Windows-only problem
(`AUDIO_LEAD_IN_MS`). The Mac does not have it. If it happens on White, raise
the number in the Windows `.env`.

---

## What this proves

When both robots play a full game, talking in turn, step 6 is done and the
demo exists. What is left is step 7 — the AI commentary for dramatic moments,
with a fallback so a dropped connection never stalls a live audience — and
step 8, making it all start by itself.

See `HANDOFF_chess_modernization.md` for both.
