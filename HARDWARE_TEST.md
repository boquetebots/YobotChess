# Step 4 — the first hardware test

**Goal: get one Yobot to say one sentence with its mouth moving.**

That is the whole target. No chess, no server, no second robot. The 2025 code
never moved the mouth at all, so this single sentence is the biggest
improvement in the project — and everything after it depends on the speech
layer working.

Expect twenty minutes. Most of it is checking things that are probably
already fine.

---

## Before you plug anything in

**Only one program can hold the robot's USB cable at a time.** The Greeter,
the Sequence Builder, Calibration and the chess player all want it, and only
one can have it. If another has it, you will get "robot not found" no matter
how many times you replug the cable.

**Stop the others first.** The Launcher page in OhbotPi2 is the traffic cop —
open it and stop everything before you start.

---

## One-time setup

Two Python add-ons that only a machine with a robot attached needs:

```
py -m pip install pyserial azure-cognitiveservices-speech
```

If the Greeter already talks on this computer, these are installed and you
can skip it. Check with:

```
python chess_needs.py
```

**The speech key.** The robot's voice comes from Microsoft Azure, and the key
lives in a file called `.env` in the **OhbotPi2** folder — not this one:

```
D:\Projects\OhbotPi2\.env
```

It needs these two lines:

```
AZURE_SPEECH_KEY=your_key_here
AZURE_SPEECH_REGION=eastus
```

Again — if the Greeter can talk, this file already exists and works. Nothing
new to do.

---

## The test

Plug the Yobot into the PC. Then, in the Chess folder:

```
python chess_player.py --say-once
```

**Watch the mouth.** You should see:

```
======================================================================
  Yobot — WHITE
======================================================================

  Borrowing robot code from: D:\Projects\OhbotPi2

  Connecting to the robot...
  Robot connected.
  Centring the motors...
  Motors centred.
  Setting up Azure speech...
  Speech ready.

  Saying: "Hello. I am Yobot, and I am about to play some chess.
           Watch my mouth move."

  WATCH THE MOUTH. It should move in time with the words.

  Done.
```

To make it say something else:

```
python chess_player.py --say-once "Testing, one two three."
```

Try the other robot's voice too — Black uses a different, lower voice so the
two do not sound like one machine talking to itself:

```
python chess_player.py --colour black --say-once
```

---

## If it goes wrong

**"ROBOT NOT FOUND"** — almost always another program holding the cable. Stop
the Greeter, the GUI and Calibration on the Launcher page. Then, in order:
check the USB cable at both ends; unplug it, wait, plug it back in; run
again. The serial port sticks sometimes and a replug clears it.

**"I cannot find the OhbotPi2 project"** — it lists everywhere it looked.
Make a file called `.env` in the **Chess** folder with one line:

```
OHBOT_DIR=D:\Projects\OhbotPi2
```

**"AZURE SPEECH WOULD NOT START"** — the key is missing or wrong. See above.
The message tells you which file and which two lines.

**It speaks but the mouth does not move** — this is the interesting failure,
because it means speech works and lip sync does not. Check the top and bottom
lip motors in Calibration first; if they do not move there either, it is
mechanical, not code.

**The mouth moves but there is no sound** — check the Windows output device.
`win_audio_check.py` in OhbotPi2 tests this on its own.

**The first word gets clipped** — Windows powers the sound device down when
idle and swallows the start. `AUDIO_LEAD_IN_MS` in the OhbotPi2 `.env`
handles it; 450 is the tested default. Raise it if words are still cut.

---

## Once the mouth moves

Now add chess. **Two windows.**

Window one — the brain:

```
python chess_server.py --strength club
```

Window two — the robot:

```
python chess_player.py --colour white --start
```

`--start` begins a new game. Use it on **one robot only**, or they will keep
resetting each other's game.

**The robot announces White's opening move and then stops. THAT IS CORRECT.**
It is Black's turn, there is no Black robot, so White waits. It proves the
whole chain works: engine, commentary, network, speech, motors.

It says so while it waits, so you can tell waiting from crashing:

```
    1. Na3      My move is knight to a three. Every piece needs a good square.
  ...waiting for black to move  (10s). This is normal — I am fine.
  ...waiting for black to move  (20s). This is normal — I am fine.
```

Press Ctrl-C to stop. It puts the robot back to neutral and lets go of the
cable on the way out.

### Making Black's move by hand

With only one robot you can still play a whole game — take Black's turns
yourself by opening this in a browser and refreshing it whenever the robot
says it is waiting:

```
http://localhost:8002/move?command=get_move
```

That makes Black's move. The robot will notice within half a second and
reply. Refresh again for the next one. It is a good way to hear a long
stretch of commentary with only one robot on the desk.

To watch the position while it plays:

```
http://localhost:8001/board
```

### Both robots on one PC

You can, if you have two Yobots and two USB cables. Run the server, then two
more windows:

```
python chess_player.py --colour white --start
python chess_player.py --colour black
```

They will play each other and talk. This is the full demo, just on one
computer instead of two Pis.

---

## Moving to the Raspberry Pis

Same program, one extra option. On each Pi, `python3` rather than `python`,
and tell it where the server is:

```
python3 chess_player.py --colour white --server 192.168.50.100
python3 chess_player.py --colour black --server 192.168.50.100
```

Replace the address with whichever machine is running `chess_server.py`.
Find a Windows PC's address with `ipconfig`, a Pi's with `hostname -I`.

**Both robots must point at the same server.** If each Pi runs its own copy
they are playing different games, and the result looks almost plausible while
being nonsense.

On the Pi, the OhbotPi2 code lives at `/home/michael/Projects/Ohbot`, which
`chess_ohbot.py` already knows to look for. The Chess folder needs copying
across, and Stockfish is only needed on the server machine — the robots do
not think.

---

## What comes next

Step 5 in `HANDOFF_chess_modernization.md` — the second robot, then the AI
commentary, then auto-start. But get the mouth moving first. Everything else
is downstream of that.
