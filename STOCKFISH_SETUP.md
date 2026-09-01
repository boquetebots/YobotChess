# Installing Stockfish — the chess engine

Stockfish is the program that actually decides the moves. It is free, it is
open source, and it is the strongest chess player in the world by a wide
margin. The robots do not think about chess at all — Stockfish does that, and
they just talk about it.

**Latest version: Stockfish 18, released January 2026.**

It is **not** something `pip install` can fetch. It is a separate program, and
each computer needs its own copy. This takes about two minutes.

---

## Windows

**1.** Go to <https://stockfishchess.org/download/> and download the Windows
version. You get a ZIP file.

**2.** Open the ZIP. Inside is a folder containing several files with names
like:

```
stockfish-windows-x86-64.exe             <- use this one
stockfish-windows-x86-64-avx2.exe
stockfish-windows-x86-64-bmi2.exe
stockfish-windows-x86-64-avx512.exe
```

They are all the same chess player. The difference is which shortcuts they
take advantage of in your processor. The fancier ones are faster, but they
crash on computers that do not have those features.

**Pick the one with the plainest name** — `stockfish-windows-x86-64.exe`, with
nothing after the `x86-64`. It runs on everything. The speed difference does
not matter here: the robots need about a second per move, and even the slow
build gives you a far stronger player than any human in the room.

**3.** Drag that one file into your Chess folder:

```
C:\Projects\Chess
```

That is all. You do not have to install anything, edit anything, or tell the
program where it is. It looks in its own folder first, on purpose, because
this is the least fiddly way to do it.

**4.** Check it worked:

```
python check_stockfish.py
```

You should see `ALL GOOD. The engine works.` and a sample opening move.

---

## Raspberry Pi

```
sudo apt install stockfish
```

It lands in `/usr/games/stockfish` and is found automatically.

Note that on the Pi you type **`python3`**, not `python`. Every command in
this file is written for Windows; add the `3` when you are on a Pi or a Mac.

---

## Mac

```
brew install stockfish
```

---

## Putting it somewhere else

If you would rather keep it elsewhere, put the full path in a file called
`.env` in the Chess folder:

```
STOCKFISH_PATH=C:\Tools\stockfish\stockfish-windows-x86-64.exe
```

That file is also where API keys will live later. Never put keys in the code
itself.

---

## Where it looks

`check_stockfish.py` and `chess_server.py` search in this order and stop at
the first hit:

1. `STOCKFISH_PATH` in your `.env` file
2. **The Chess project folder** — the easy option
3. Anywhere on the system PATH
4. `/usr/games/stockfish` and the other usual Pi and Mac locations
5. Your Downloads folder, in case you unzipped it and left it there

If several copies turn up, it takes the one with the shortest filename —
which is the most compatible build — and `check_stockfish.py` tells you
which one it chose, so there are no surprises.

---

## When it goes wrong

**"Could not find Stockfish"** — the file is not anywhere it looks. The
likeliest cause is that the ZIP was never actually unzipped. On Windows,
double-clicking a ZIP lets you *look inside* without extracting anything;
you have to drag the file out. Check the file really is sitting in
`C:\Projects\Chess` on its own.

**"IT WOULD NOT START"** — usually the wrong build for your processor. Go
back to the ZIP and use the plainest `x86-64` name. If you already did, try
one of the others.

**Windows SmartScreen blocks it** — Stockfish is not signed by Microsoft, so
Windows may warn about an unrecognised app. It is a well-known open-source
program from the official site. Choose "More info" and then "Run anyway" if
you are comfortable; download it only from
<https://stockfishchess.org/download/>.

**It works but the robots are slow** — that is the thinking time, not the
engine. Lower it:

```
python chess_server.py --think 0.3
```

Anything below about 0.1 seconds starts making genuinely silly moves.

---

## What you do NOT need it for

These three run with nothing but the `chess` add-on, no engine at all:

```
python test_commentary.py
python chess_speech.py
python chess_templates.py
```

That is deliberate. All the commentary work can be checked and tuned before
anyone installs anything.

---

Sources: [Stockfish official download](https://stockfishchess.org/download/) ·
[Stockfish 18 release notes](https://stockfishchess.org/blog/2026/stockfish-18/)
