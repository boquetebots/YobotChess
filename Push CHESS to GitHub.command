#!/bin/bash
# ============================================================================
#  Push CHESS to GitHub.command
#
#  Sends the CHESS work on this Mac up to GitHub.
#
#  NOTE THE NAME. There is a push_to_github.command in the OhbotPi2 folder
#  too, and it pushes a DIFFERENT project to a DIFFERENT repository. That is
#  exactly what went wrong on 2026-08-26: the OhbotPi2 one was run with a
#  commit message about chess, so OhbotPi2 got the message and YobotChess
#  stayed empty. This file refuses to run anywhere but the chess folder.
#  Double-click it in Finder, or run it in Terminal.
#
#  The FIRST time you run it, it will tell you to make an empty repository on
#  github.com and will then connect this folder to it. Every time after that
#  it just commits whatever has changed and pushes it.
#
#  Safe to run as often as you like. If there is nothing new, it says so.
#
#  Only this Mac folder is touched. To bring a Pi in line afterwards, on the
#  Pi:   cd ~/Projects/Chess  &&  git pull
# ============================================================================

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "  ${GREEN}OK${RESET}    $1"; }
bad()  { echo -e "  ${RED}STOP${RESET}  $1"; }
warn() { echo -e "  ${YELLOW}NOTE${RESET}  $1"; }
hdr()  { echo -e "\n${BOLD}${CYAN}---  $1  --------------------------------${RESET}"; }

REPO="$(cd "$(dirname "$0")" && pwd)"
BRANCH="main"
SUGGESTED_URL="https://github.com/boquetebots/YobotChess.git"

clear
echo ""
echo -e "${BOLD}${CYAN}  Push Yobot Chess to GitHub${RESET}"
echo ""
echo "  Folder: $REPO"
echo ""

cd "$REPO" || { bad "Cannot find $REPO"; read -p "  Press Return to close."; exit 1; }

if [ ! -f chess_server.py ]; then
    bad "This is not the chess folder."
    echo ""
    echo "     There is no chess_server.py here, so this is some other"
    echo "     project - most likely OhbotPi2, which has a push script of"
    echo "     its own. Nothing has been changed."
    echo ""
    echo "     The one you want lives in your Chess folder, next to"
    echo "     'Play a Human.bat'."
    echo ""
    read -p "  Press Return to close."; exit 1
fi

if [ ! -d .git ]; then
    bad "This folder is not set up for git at all."
    echo "     Ask Claude before going further - something has gone missing."
    read -p "  Press Return to close."; exit 1
fi


# ── Is this folder connected to GitHub yet? ─────────────────────────────────
hdr "Checks"

if ! git remote get-url origin >/dev/null 2>&1; then
    echo ""
    echo -e "  ${BOLD}FIRST TIME. Two things to do, in this order.${RESET}"
    echo ""
    echo "  1. In a browser, go to:      https://github.com/new"
    echo ""
    echo "     Owner:        boquetebots"
    echo "     Name:         YobotChess"
    echo "     Public or private - your choice."
    echo ""
    echo -e "     ${BOLD}Leave every tick box EMPTY.${RESET} No README, no .gitignore,"
    echo "     no licence. This folder already has all of that, and a"
    echo "     repository that starts with a file in it will refuse the"
    echo "     first push."
    echo ""
    echo "     Click 'Create repository'."
    echo ""
    echo "  2. Come back here and press Return."
    echo ""
    read -p "  Press Return once the empty repository exists (or Ctrl-C to stop). "
    echo ""
    echo "  Address of the repository you just made."
    echo "  Press Return to accept the one shown."
    echo ""
    read -p "  [$SUGGESTED_URL] " URL
    if [ -z "$URL" ]; then URL="$SUGGESTED_URL"; fi
    git remote add origin "$URL"
    ok "Connected to $URL"
else
    ok "Connected to $(git remote get-url origin)"
fi


# ── Right branch? ───────────────────────────────────────────────────────────
here=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ "$here" != "$BRANCH" ]; then
    warn "This folder is on branch '$here', not '$BRANCH'. Switching."
    git branch -M "$BRANCH" || {
        bad "Could not switch. Ask Claude."
        read -p "  Press Return to close."; exit 1
    }
fi
ok "On branch $BRANCH"


# ── Has GitHub moved ahead of us? ───────────────────────────────────────────
if git ls-remote --exit-code origin "$BRANCH" >/dev/null 2>&1; then
    git fetch origin "$BRANCH" --quiet
    remote_head=$(git rev-parse "origin/$BRANCH" 2>/dev/null)
    base=$(git merge-base HEAD "origin/$BRANCH" 2>/dev/null)
    if [ -n "$remote_head" ] && [ "$remote_head" != "$base" ]; then
        bad "GitHub has changes this Mac does not have."
        echo ""
        echo "     Pushing now would either be refused or would bury someone"
        echo "     else's work. Get this Mac up to date first:"
        echo ""
        echo "         cd \"$REPO\" && git pull --rebase"
        echo ""
        echo "     If that complains, stop and ask Claude."
        echo ""
        read -p "  Press Return to close."; exit 1
    fi
    ok "GitHub has nothing this Mac is missing"
else
    ok "Nothing on GitHub yet - this will be the first push"
fi


# ── Anything to commit? ─────────────────────────────────────────────────────
hdr "What has changed"

git add -A .

if git diff --cached --quiet; then
    ok "Nothing new to commit"
else
    git --no-pager diff --cached --stat
    echo ""
    echo "  Describe this change in a few words."
    echo "  Press Return on its own to use today's date."
    echo ""
    read -p "  Message: " MSG
    if [ -z "$MSG" ]; then MSG="Chess updates $(date '+%Y-%m-%d')"; fi
    git commit -q -m "$MSG" || {
        bad "The commit failed - the reason is above."
        read -p "  Press Return to close."; exit 1
    }
    ok "Committed: $MSG"
fi


# ── Push ────────────────────────────────────────────────────────────────────
hdr "Sending to GitHub"

# Everything the push says goes into a file as well as onto the screen.
# A Terminal window that gets closed takes the error with it, and the error
# is the only thing that says WHY. The file survives.
LOG="$REPO/last push log.txt"
{
  echo "Push attempted: $(date)"
  echo "Repository:     $(git remote get-url origin)"
  echo "Branch:         $BRANCH"
  echo "Commit:         $(git rev-parse HEAD)"
  echo "----------------------------------------------------------------"
} > "$LOG"

git push -u origin "$BRANCH" 2>&1 | tee -a "$LOG"
PUSH_STATUS=${PIPESTATUS[0]}

# NOT "if git push | tee" - that reports whether TEE worked, which it always
# does, so a failed push would look like a success. PIPESTATUS asks git.
if [ "$PUSH_STATUS" -eq 0 ]; then
    echo ""
    echo -e "  ${GREEN}${BOLD}DONE.${RESET}"
    echo ""
    echo "  On a Pi, to pick this up:"
    echo ""
    echo "      cd ~/Projects/Chess && git pull"
    echo ""
    echo "  First time on a Pi:"
    echo ""
    echo "      cd ~/Projects && git clone $(git remote get-url origin) Chess"
    echo "      cd Chess && bash install.sh"
    echo ""
else
    echo ""
    bad "The push was refused. What it said is printed above."
    echo ""
    echo "  It is also saved, so nothing is lost when this window closes:"
    echo "      last push log.txt   (in this folder)"
    echo ""
    echo "  Show that file to Claude and it can say exactly what happened."
    echo ""
    echo "  The usual causes:"
    echo ""
    echo "    - GitHub asked who you are and this window could not answer."
    echo "      Run it once in Terminal instead of double-clicking, so you"
    echo "      can type your username and token."
    echo ""
    echo "    - The repository does not exist yet, or the name is spelled"
    echo "      differently. Check github.com."
    echo ""
    echo "    - A file over 100 MB got in. GitHub refuses those outright."
    echo "      Stockfish is the only thing here big enough to do that, and"
    echo "      .gitignore should be keeping it out. Check with:"
    echo "          git ls-files | xargs -I{} du -h {} | sort -rh | head"
    echo ""
fi

echo ""
read -p "  Press Return to close. "
