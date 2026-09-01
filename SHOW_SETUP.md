# The display — one page that runs the whole show

**Written 2026-08-13**, after step 6 (two robots playing each other) was
confirmed working.

Until now the match was started by typing commands into three black windows
and the only board on screen was a wall of text characters. This replaces
that with one page: three buttons to start everything, and a 16:9 board with
a photo and a clock for each robot, sized for a projector.

---

## See it before you set anything up

This needs no robots, no Mac and no Stockfish. It plays a famous game to
itself so you can judge the layout, the size of the pieces and whether the
names read from the back of the room.

```
cd /d D:\Projects\Chess
python chess_show.py --demo
```

Then open a browser at **http://localhost:8080/** and press **F11**.

Nothing on that screen is real. Close the window when you have seen enough.

---

## Just double click this

**`Play Chess.bat`**

That is the whole thing. It starts the chess program, waits until the display
page is genuinely ready, opens it in your normal browser and presses F11 to
go fullscreen for the projector.

**The black window that appears IS the show.** Leave it alone while you are
playing; closing it stops the server and both robots. The three buttons for
starting the robots are on the page itself.

For a desktop icon: right click the file, then **Send to > Desktop (create
shortcut)**. Do not move the file itself — it has to sit in the same folder
as the rest of the chess programs, and it will say so plainly if it has been
moved.

There is a second one, **`Demo - no robots.bat`**, which runs the same
display replaying a famous game with nothing plugged in at all. That is the
one for setting up a projector before the robots arrive.

**The settings are at the top of `Play Chess.bat` in plain English** —
strength, the gap between turns, when a robot resigns, and where the Mac is.
Open it with Notepad, change a number, save.

**If it does not go fullscreen, press F11.** Windows has no way to make an
unknown browser start up fullscreen: only Chrome and Edge take a fullscreen
switch, and using one of those would ignore whichever browser you actually
chose. So the file opens *your* browser and presses the key for you. When
that does not land, the key still works by hand — and the board has its own
fullscreen button in the corner.

### The same thing typed out

```
python chess_show.py
```

Then open **http://localhost:8080/** yourself. This is all the batch file
does.

**Why one thing has to start by hand at all:** a web page cannot start a
program on its own. Something must already be running for the browser to talk
to, and that something is `chess_show.py`. It is the same job the Launcher
page does in OhbotPi2.

---

## Running the match

| Order | Do this | What happens |
|-------|---------|--------------|
| 1 | **Start game server** | Stockfish wakes up. Takes a few seconds — the button stays grey until it is genuinely ready, not just launched. |
| 2 | **Start Lester** | White's robot connects and waits. |
| 3 | **Start Goldie** | Black's robot on the Mac connects and waits. |
| 4 | **New game** | The robots start playing. |

**Do not press New game twice.** It resets the board. It is deliberately sent
to White only — telling both robots to start is the old `--start` trap, where
each one resets the other's game and neither gets anywhere.

**You need both robots.** White's program plays White's moves and nothing
else. Start Lester on his own and he will play one move, say it, and then
wait for Goldie — correctly, and for as long as you leave him. The footer
says so rather than letting it look like a crash.

To try it with one robot, make the other's moves by hand in a browser:

```
http://localhost:8002/move?command=get_move
```

Refresh that page once for each of Black's moves. That is the same trick
`HARDWARE_TEST.md` uses.

**Stop all** shuts down all three in the right order. Use it before running
the Greeter, the GUI or Calibration, because those want the same USB cable.

The control bar **fades away after six seconds** of not touching the mouse,
so the audience sees the board and nothing else. Move the mouse to bring it
back.

---

## Strength and pause

The two dropdowns on the bar are the same settings described under *Tuning
the show* in `CLAUDE.md`. Weaker play makes a livelier, shorter, more
decisive game — `club` or `beginner` is usually what you want.

**They are only read when the game server starts.** Changing one mid-game
does nothing until you stop and start the server, and the page says so rather
than letting you wonder.

## Language

Added 2026-08-31. The **Language** dropdown switches the robots between
English and Spanish — the commentary, the announcements, and the voice both
robots speak with. Like Strength and Pause, it is only read when the game
server starts, for the same reason.

Test it by hand before trusting it in front of an audience:
`python chess_player.py --say-once "Hola, soy Yobot" --lang es --colour white
--voice lester`. Full detail on what changed and what still wants a real-ear
check is in `HANDOFF_chess_modernization.md`, under *Spanish commentary*.

---

## The photos

Drop two files into `D:\Projects\Chess`:

```
white_player.jpg        Lester
black_player.jpg        Goldie
```

`.png` works too. Square-ish head-and-shoulders shots look best — the page
crops to a square. Refresh the browser after replacing one.

There are placeholder pictures in there now, drawn by a script. Overwrite
them with real photos when you have them. If a file is missing the panel just
stays plain grey — no broken-image icon in front of an audience.

To change the **names** on screen, edit the two lines marked `NAMES` at the
top of the script in `show/index.html`.

---

## Goldie on the Mac

The Start button for Goldie reaches across the network to the Mac. That only
works if a small listener is running over there:

```bash
cd ~/Projects/Chess
python3 chess_show_agent.py
```

Leave that window open. It does one job — start and stop `chess_player.py`
when the PC asks — and prints a line each time it is told something.

Then start the display on the PC with the Mac's address:

```
python chess_show.py --mac 192.168.50.20:8090
```

Use the Mac's actual address. Find it in System Settings → Network.

**You do not have to bother with any of this.** Leave `--mac` off and the
Goldie button is simply greyed out, with the reason in its tooltip. Start
Goldie the way `MAC_SETUP.md` describes and everything else works exactly the
same:

```bash
python3 chess_player.py --colour black --server 192.168.50.100
```

The agent only saves you walking over to the Mac.

---

## The clocks are honest

Each robot's clock counts up **while it is thinking about its move and while
it is saying it** — everything an audience would call "its go". It stops the
moment the other robot takes over, and both stop at the end of the game.

Nothing invented, and nothing that affects the chess: **no robot can lose on
time.** A countdown was the other option and it was rejected for exactly that
reason — a clock that hits zero and does nothing is worse than no clock.

The two clocks add up to the length of the game. They do not double-count the
moment where one robot is speaking while it is already the other's turn.

---

## The bar beside the board

Stockfish gives an opinion with every move and this shows it: the pale part
is White's share. It works out at nothing extra — the engine already
calculates this while looking for blunders.

**White is always the pale end.** That sounds obvious and is the one thing
that was easy to get wrong: the engine reports its opinion from the point of
view of whoever is to move, so the raw number changes sign on every single
move. Left alone the bar would swing end to end all game and mean nothing.
`test_show.py` checks this specifically.

It is squashed through a curve rather than shown directly, because the
engine's numbers run away to enormous values once a game is decided. A pawn
up is a visible nudge; a queen up is nearly the whole bar; mate is all of it.

---

## Watching, or playing, from another device

The page works from anything on the same wifi. When `chess_show.py` starts it
prints the addresses:

```
      From another one:   http://192.168.50.xx:8080/
      A GUEST'S TABLET:   http://192.168.50.xx:8080/board
```

**Port 8080.** Open as many devices as you like — everything they show comes
from the server, so they cannot disagree with each other.

`/board` is the same board with the **control buttons left off**, for a tablet
somebody else is holding. It is fully playable when a guest is playing; it
simply has no Stop all for a stray thumb to find.

There is a **fullscreen button** in the bottom right corner of the board, the
sort a video player has — F11 is no use on a device with no keyboard. Safari
on iPhone refuses fullscreen for web pages, so there the button hides itself
and the footer says to use Add to Home Screen instead, which gets you the same
screen. **Keep tablets in landscape**; the layout is 16:9 like the projector.

If a device cannot reach the page at all, it is almost always Windows
Firewall — allow Python on **Private networks**.

Playing a guest against the robot has its own guide: **`HUMAN_GAME.md`**.

---

## Checking it without hardware

```
python test_show.py
```

Two seconds, needs nothing plugged in. It checks the clocks charge the right
robot and add up correctly, that the bar does not flip sides, and that the
page copes with the chess server, White and the Mac all being switched off —
which is what it faces every time you open it.

---

## If something does not work

**The page will not load at all.** `chess_show.py` is not running, or the
window was closed. Start it again.

**"Start game server" does nothing and the button stays grey.** Stockfish is
not installed or not where the program expects. Run `python
check_stockfish.py` and see `STOCKFISH_SETUP.md`.

**Lester starts, then stops on its own a second later.** Something else has
the USB cable — the Greeter, the GUI or the Calibration page. One program per
robot, always. Stop the other one from the Launcher page in OhbotPi2.

**Goldie's button is greyed out.** Either you started without `--mac`, or the
listener is not running on the Mac, or the address is wrong. Hover over the
button and it says which.

**The board shows but the pieces are boxes or blank.** The pieces are the
chess characters built into the computer's own fonts. Windows and macOS both
have them. If a machine does not, tell me and I will draw them instead.

**Everything looks right but the robots are silent.** Press **Log**. It shows
what each program actually printed, and it opens by itself if something
started and then stopped. The usual causes are another program holding the
robot's USB cable, or a missing key in `.env`.

If the log is clean and the footer says it is waiting for a robot, that robot
simply is not running — see "you need both robots" above.

If neither, it is not this page. Work through `HARDWARE_TEST.md` — `python
chess_player.py --say-once` is the first thing to try.

---

## What this page cannot do

It does not touch the chess. It starts programs, and it reads the position.
It never plays a move, writes a sentence or speaks. **If it crashes in the
middle of a game the robots carry on without it** — you lose the picture, not
the show.
