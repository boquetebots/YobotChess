#!/usr/bin/env bash
# =============================================================================
#  install.sh - first time setup on a Raspberry Pi or a Mac
# =============================================================================
#
#  Run it once, from inside this folder:
#
#      bash install.sh
#
#  It does four things:
#
#    1. Finds the OhbotPi2 project, which is where the motors and the voice
#       come from. Chess has no robot code of its own, on purpose.
#    2. Installs the three Python add-ons chess needs - into the SAME Python
#       that OhbotPi2 uses, which on a Pi is a virtual environment. Putting
#       them anywhere else is the classic way to get "no module named chess"
#       from a robot that is otherwise working perfectly.
#    3. Installs Stockfish, the engine that actually plays the chess.
#    4. Writes two short scripts, "play white" and "play black", with the
#       right computer names already filled in.
#
#  Safe to run again. Anything already done is skipped.
# =============================================================================

set -u

BOLD=$'\033[1m'; RESET=$'\033[0m'
GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; CYAN=$'\033[36m'

ok()   { echo "  ${GREEN}OK${RESET}    $1"; }
warn() { echo "  ${YELLOW}NOTE${RESET}  $1"; }
err()  { echo "  ${RED}STOP${RESET}  $1"; }
hdr()  { echo; echo "${BOLD}${CYAN}---  $1  ---------------------------------------${RESET}"; }

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

echo
echo "${BOLD}${CYAN}"
echo "  ======================================================"
echo "     Yobot Chess - setting up this computer"
echo "  ======================================================"
echo "${RESET}"
echo "  Folder: $HERE"
echo

if [ ! -f "$HERE/chess_player.py" ]; then
    err "This is not the chess folder - chess_player.py is not here."
    echo "        Move install.sh back into the chess folder and try again."
    exit 1
fi

# Which machine are we on? Only used to pick the right install command.
case "$(uname -s)" in
    Darwin) PLATFORM="mac" ;;
    Linux)  PLATFORM="linux" ;;
    *)      PLATFORM="other" ;;
esac


# =============================================================================
#  1. Find OhbotPi2
# =============================================================================
hdr "1 of 4: finding the OhbotPi2 project"

OHBOT_DIR=""
for CANDIDATE in \
    "${OHBOT_DIR_OVERRIDE:-}" \
    "$HOME/Projects/Ohbot" \
    "$HOME/Projects/OhbotPi2" \
    "/Volumes/Projects/Ohbot" \
    "$(dirname "$HERE")/OhbotPi2" \
    "$(dirname "$HERE")/Ohbot"
do
    [ -z "$CANDIDATE" ] && continue
    if [ -f "$CANDIDATE/yobot_core.py" ] && [ -f "$CANDIDATE/ohbot_pi.py" ] && [ -f "$CANDIDATE/ohbot_azure.py" ]; then
        OHBOT_DIR="$(cd "$CANDIDATE" && pwd)"
        break
    fi
done

if [ -n "$OHBOT_DIR" ]; then
    ok "OhbotPi2 is at $OHBOT_DIR"
else
    warn "Could not find OhbotPi2 on this computer."
    echo
    echo "        That is fine if this machine is only going to run the game"
    echo "        and the display. It is NOT fine if a robot is plugged in"
    echo "        here - without it there is no motor control and no voice."
    echo
    echo "        To fix it later, put one line in a file called .env in this"
    echo "        folder, with your real path:"
    echo
    echo "            OHBOT_DIR=$HOME/Projects/Ohbot"
    echo
fi


# =============================================================================
#  2. The Python add-ons - into the SAME Python the robot uses
# =============================================================================
hdr "2 of 4: the Python add-ons"

PYTHON=""
VENV_NOTE=""

if [ -n "$OHBOT_DIR" ] && [ -x "$OHBOT_DIR/venv/bin/python3" ]; then
    # The Raspberry Pi. OhbotPi2 keeps its own Python inside the project.
    PYTHON="$OHBOT_DIR/venv/bin/python3"
    VENV_NOTE="OhbotPi2's own Python"
elif [ -x "$HOME/yobot-venv/bin/python3" ]; then
    # The Mac. Its Yobot environment lives in the home folder instead, which
    # is what OhbotPi2's Mac guide sets up. Getting this wrong is the classic
    # "no module named chess" on a robot that is otherwise perfectly healthy.
    PYTHON="$HOME/yobot-venv/bin/python3"
    VENV_NOTE="the Mac's yobot-venv"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="$(command -v python3)"
    VENV_NOTE="the system Python"
else
    err "Python 3 is not installed."
    echo "        On a Pi:  sudo apt install python3 python3-pip -y"
    echo "        On a Mac: install it from https://www.python.org/downloads/"
    exit 1
fi

ok "Using $VENV_NOTE"
echo "        $PYTHON"
echo

PIPFLAGS=""
if [ "$VENV_NOTE" = "the system Python" ] && [ "$PLATFORM" = "linux" ]; then
    # Recent Raspberry Pi OS refuses to install into the system Python
    # unless you say you meant it. Inside a virtual environment this flag
    # is neither needed nor allowed, which is why it is decided here.
    PIPFLAGS="--break-system-packages"
fi

if "$PYTHON" -m pip install $PIPFLAGS -r "$HERE/requirements.txt"; then
    ok "chess, flask and python-dotenv installed"
else
    err "The add-ons would not install - the reason is printed above."
    echo "        You can try it by hand:"
    echo "            $PYTHON -m pip install $PIPFLAGS chess flask python-dotenv"
    exit 1
fi


# =============================================================================
#  3. Stockfish
# =============================================================================
hdr "3 of 4: the chess engine"

if command -v stockfish >/dev/null 2>&1; then
    ok "Stockfish is already installed: $(command -v stockfish)"
elif [ "$PLATFORM" = "linux" ]; then
    echo "  Installing Stockfish. This asks for your password."
    echo
    if sudo apt-get install -y stockfish; then
        ok "Stockfish installed"
    else
        warn "apt could not install it. Try:  sudo apt update"
        warn "then run this script again."
    fi
elif [ "$PLATFORM" = "mac" ]; then
    if command -v brew >/dev/null 2>&1; then
        if brew install stockfish; then
            ok "Stockfish installed"
        else
            warn "brew could not install it."
        fi
    else
        warn "Homebrew is not installed, so Stockfish cannot be fetched here."
        echo
        echo "        Either install Homebrew from https://brew.sh and run this"
        echo "        again, or skip it: a Mac that is only driving a robot"
        echo "        does not need the engine at all. Only the machine running"
        echo "        chess_server.py does."
    fi
else
    warn "Unknown system - install Stockfish yourself, then re-run this."
fi


# =============================================================================
#  4. The two little run scripts
# =============================================================================
hdr "4 of 4: scripts for starting a robot"

# Where the game is running. On the machine that runs chess_server.py this is
# itself; on a second robot's machine it is the first one's name or address.
SERVER_GUESS="localhost"

make_runner() {
    COLOUR="$1"
    FILE="$HERE/play-$COLOUR.sh"
    if [ -f "$FILE" ]; then
        warn "play-$COLOUR.sh already exists - leaving your copy alone"
        return
    fi
    cat > "$FILE" <<RUNNER
#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  play-$COLOUR.sh - start THIS robot, playing $COLOUR
# ---------------------------------------------------------------------------
#
#  Run it with:   bash play-$COLOUR.sh
#
#  SETTING: which computer is running the game. Put its name or its address
#  between the quotes. "localhost" means this same computer.
SERVER="$SERVER_GUESS"

#  ---------------------------------------------------------------------------
#  Nothing below here needs changing.
cd "\$(dirname "\$0")"
exec "$PYTHON" chess_player.py --colour $COLOUR --server "\$SERVER" "\$@"
RUNNER
    chmod +x "$FILE"
    ok "wrote play-$COLOUR.sh"
}

make_runner white
make_runner black

# And one for the display on its own, replaying a famous game with nothing
# plugged in. Same reason as the runners: it saves anyone having to work out
# which of this computer's several Pythons is the right one.
if [ -f "$HERE/demo.sh" ]; then
    warn "demo.sh already exists - leaving your copy alone"
else
    cat > "$HERE/demo.sh" <<DEMO
#!/usr/bin/env bash
# ---------------------------------------------------------------------------
#  demo.sh - the audience display, replaying a famous game.
#  No robots, no chess engine, nothing plugged in.
#
#      bash demo.sh
#
#  Then open  http://localhost:8080/  in a browser. Ctrl-C here to stop.
# ---------------------------------------------------------------------------
cd "\$(dirname "\$0")"
exec "$PYTHON" chess_show.py --demo "\$@"
DEMO
    chmod +x "$HERE/demo.sh"
    ok "wrote demo.sh"
fi


# =============================================================================
#  Done
# =============================================================================
echo
echo "${BOLD}${GREEN}"
echo "  ======================================================"
echo "     FINISHED"
echo "  ======================================================"
echo "${RESET}"
echo "  See the display with nothing plugged in:"
echo
echo "      bash demo.sh          then open http://localhost:8080/"
echo
echo "  Check the engine found itself:"
echo
echo "      $PYTHON check_stockfish.py"
echo
echo "  Make this robot say one sentence, with its mouth moving. No game,"
echo "  no server, nothing else plugged in:"
echo
echo "      $PYTHON chess_player.py --say-once"
echo
echo "  Then, to join a game running on another computer, open play-white.sh"
echo "  or play-black.sh, put that computer's name in the SERVER line, and:"
echo
echo "      bash play-white.sh"
echo
echo "  The full walkthrough is in \"START HERE - Raspberry Pi.md\"."
echo
