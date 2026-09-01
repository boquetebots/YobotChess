# Playing the robot yourself

A guest sits down, taps a piece on the screen, and plays Lester. The robot
announces its own moves and reacts to theirs — including pouncing when they
give something away.

This is the walkthrough. `SHOW_SETUP.md` covers the ordinary robot-against-
robot match; everything here is on top of that.

---

## Try it with nothing plugged in

Before any of the real setup, you can sit down with the tablet and play:

```
python chess_show.py --demo --human white
```

Open `http://localhost:8080/` and tap a piece. No Stockfish, no robot, no
Azure, no network. The opponent is not really playing chess — it just picks
something legal — because the point of this mode is the **touchscreen**, not
the game. Is the board big enough? Do the squares take a tap first time? Does
the promotion picker land where a thumb can reach it?

Those are questions about the room and the hardware, and none of them should
need an engine and two robots to answer.

To try it as Black instead:

```
python chess_show.py --demo --human black
```

The board turns round so your pieces are at the bottom.

---

## The real thing

One robot, one guest. Lester stays on the Windows PC; Goldie is not involved.

**1. Start the control page.**

```
python chess_show.py
```

Open `http://localhost:8080/`.

**2. On the control bar, set "Playing" to `a person plays White`.**

Two things happen by themselves when you do:

- **Strength drops to `friendly`.** At the old default of `club` a guest loses
  every game, and the next person stops asking for a turn.
- **Polite gets ticked.** See below.

Both are only defaults. Change either if you want.

**3. Press "Start game server", then "New game".**

**4. Start Lester** — his button now reads "Start Lester (black)", because
that is the colour the guest left him. Goldie's button is hidden: only one
robot is used in a guest's game, and it is the one plugged into this computer.

**5. Lester welcomes the room, then waits.** Tap a piece; its legal squares
light up. Tap one of them. That is the whole interface.

To start Lester from a window by hand instead, name the colour AND the voice —
without `--voice` he takes the voice belonging to the colour, so Lester on
Black would come out sounding like Goldie:

```
python chess_player.py --colour black --voice lester
```

---

## Only one robot is used, and it is the one on this computer

**Lester plays the guest whichever colour is left over.** Choose "a person
plays White" and Lester plays Black. Choose Black and he plays White. He keeps
his own voice either way.

Goldie and the Mac are not involved in a guest's game at all. Goldie's Start
button says so if you press it.

The button for Lester shows which side he has taken — "Start Lester (black)" —
because otherwise the button says Lester while the wing opposite says Lester
is Black, and it is not obvious they are the same robot.

> This did not work in the first version. The robot on the desk was wired to
> play White always, so choosing "a person plays White" went looking for
> Goldie on a Mac that was switched off, and nothing moved. The two Start
> buttons are **machines, not colours** — one is the robot here, one is the
> robot on the Mac.

---

## Playing from a tablet

Start `chess_show.py` on the PC as usual. It prints two addresses:

```
      From another one:   http://192.168.50.xx:8080/
      A GUEST'S TABLET:   http://192.168.50.xx:8080/board
```

**Port 8080, not 8000.** Type the second one into the tablet.

**`/board` is fully playable.** The name reads like a spectator view and it is
not one — it is the *guest's* page. Selecting, moving, the promotion picker
and the fullscreen button all work exactly as on the main page.

The only things left off are the **control bar** and the **log panel**: no
Stop all, no strength menu, no mode selector. That is the whole point. On the
full page a guest holding the tablet is one thumb from Stop all, and the bar
reappears on any tap — which is precisely what they are about to do.

The full page at `/` stays on the PC or the projector. `/play` serves the same
thing, in case that is what you remember.

Both can be open at once, on as many devices as you like. Everything either
one shows comes from the server, so they cannot disagree.

**If the tablet cannot reach it, it is almost always Windows Firewall.** The
first time Python opens a port, Windows asks for permission; if that box never
appeared, or was cancelled, the tablet just spins. Allow Python on **Private
networks**.

After that, check the obvious two: both devices on the same wifi, and the
router not running "client isolation" or a guest network — those stop devices
seeing each other at all, and it is better to find that out at home.

### Getting the whole screen

There is a **fullscreen button** in the bottom right corner of the board — the
sort a video player has. F11 is no use on something with no keyboard. Press it
once to fill the screen, again to come back.

**Keep the tablet in landscape.** The board is laid out 16:9, the same shape
as the projector, so turning a phone upright leaves it small and squashed.
Landscape is the way round it is designed for.

**The iPhone is the exception, and Apple's fault.** Safari on iPhone allows
fullscreen for video only and flatly refuses it for a web page. So on an
iPhone the button hides itself and the footer says what to do instead: **Add
to Home Screen**. That opens the page with no address bar and no toolbars,
which is the same result by a different road — and it is worth doing on any
tablet anyway, because it also stops a guest wandering off to another website
mid-game.

---

## Which colour should the guest play?

**White** is the default and means the guest moves first.

The one thing to know is that the show would otherwise open in silence, with a
visitor being stared at while they work out what to do. So the robot delivers
its opening greeting **before** the first move and then waits. Nobody has to
fill the gap.

**Black** is on the same menu. The robot moves first, which is a livelier
start, but the guest is then answering rather than choosing.

---

## Strength

The first three settings are the ones a person can actually beat:

| Setting | Roughly | Who it suits |
|---------|---------|--------------|
| `gentle` | 800 | someone who has just learned the moves |
| `friendly` | 1000 | a casual player. **The default for a guest.** |
| `easy` | 1200 | somebody who plays a bit |
| `beginner` | 1320 | already stronger than most club players |

Everything from `beginner` up is the old list, unchanged, and is what two
robots play each other at.

There is a reason for the split. Stockfish's normal strength dial refuses to
go below 1320 — that is its floor and there is no arguing with it. The three
gentle settings use a different, cruder dial that makes the engine deliberately
overlook things. Its play is lopsided: mostly sensible, then a real howler.
For an audience the howler is the interesting part.

---

## Polite

The commentary was written for one robot to say to another robot, and a robot
cannot be embarrassed. "Step aside, tin man" is funny between Lester and
Goldie. Said to a guest who has just hung their queen in front of the whole
clubhouse, it is not.

**Polite leaves out the cheekiest fifth of the lines** and uses the rest. It
is ticked automatically when you switch to a human opponent. Untick it if you
know the person and the room.

It is not a separate script. Every commentary list in `chess_templates.py` is
four labelled blocks of five — Generic, Sassy, Local, Robot — and Polite mode
simply declines to use the Sassy block. **To change what Polite mode says,
edit the Sassy blocks**: anything in one is left out, anything anywhere else
is kept.

---

## The robot does not announce your move

It says nothing at all when you move. It reacts on **its own next turn**,
along with its own move:

```
you           Bc5
Lester   Nf3  I played knight to f three. Punishing that one.
```

That is deliberate. A robot reading your own move back to you is a robot
narrating; a robot reacting to what you did is a robot playing you. The
machinery was already there — it is exactly how the two robots react to each
other — and it does not care whether the mistake came from Stockfish or from
a person.

---

## Checking it without a guest

```
python test_human.py
```

Runs in about two seconds. No robot, no browser, no Stockfish. It checks that
the board takes only legal moves from the right person at the right time, that
your move stays silent, that a person never takes the speaking floor, and that
the robot still pounces on a mistake.

---

## Things that catch people out

**Do not start a robot on the guest's side.** The server refuses and says so,
which is the useful behaviour: without it the robot would quietly take the
guest's turns, and the room would blame the touchscreen.

**Changing "Playing" needs the game server restarted.** Who is playing is
decided when the server starts. The bar tells you when a change is waiting.

**The board is only tappable on the guest's turn.** A tap while the robot is
thinking gives a brief red flash and "Not your turn yet". That is not an
error — it happens constantly and is meant to be ignored.

**One robot cannot be beaten on time.** The clocks count time *used*, not time
left, for both the robot and the guest. Nobody loses on the clock.

**The guest can win.** At `gentle` or `friendly`, fairly often. The robot
resigns rather than grinding on in a lost position, which gives the game a
proper ending — and a guest who beats a robot in front of the room is the best
outcome this whole thing has.
