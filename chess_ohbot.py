#!/usr/bin/env python3
"""
chess_ohbot.py — borrowing the robot code from OhbotPi2
================================================================================

The Chess project does NOT contain its own robot code. Motor control, Azure
speech and lip sync all live in the OhbotPi2 project and are shared from
there. That is deliberate: one copy, fixed in one place, rather than two
copies that quietly drift apart.

This little file's only job is finding that folder and putting it where
Python can see it.

You never run this file directly. `chess_player.py` uses it.

--------------------------------------------------------------------------------
WHERE IT LOOKS
--------------------------------------------------------------------------------

In order, stopping at the first one that exists:

  1. OHBOT_DIR in a .env file next to this script
  2. ../OhbotPi2, ../OhbotPi and ../Ohbot — the folder NEXT TO this one,
     and the -main versions of those names, which is what GitHub's
     "Download ZIP" button makes if nobody renames the folder
  3. C:\\Projects\\OhbotPi2 and C:\\Projects\\OhbotPi   (a normal Windows install)
  4. D:\\Projects\\OhbotPi2                      (Michael's own PC)
  5. /home/michael/Projects/Ohbot                (the Raspberry Pis)
  6. /Volumes/Projects/Ohbot                     (a Pi mounted on a Mac)

**Why "OhbotPi" is in that list as well as "OhbotPi2".** The folder is called
OhbotPi2 on Michael's machines, but the GitHub repository it comes from is
called OhbotPi — so a plain `git clone` on a new computer produces a folder
named OhbotPi and nothing here would have recognised it. Found 2026-09-01,
the night before a fresh install at the clubhouse, by cloning the repo and
looking at what the folder was actually called.

**Looking next door comes second on purpose.** It is the only entry that
needs no drive letter and no user name, so it is right on every machine as
long as the two project folders sit side by side — which is how every setup
guide here tells you to install them. The named paths below it are
conveniences for machines already set up that way, not requirements. A new
Windows PC will not have a D: drive at all, which is exactly why it cannot
be the thing this relies on.

If none of those exist it says so in plain English rather than throwing an
import error at you.
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# The files we borrow. If these are not all present, the folder we found is
# not the right one — better to say so now than to fail halfway through.
REQUIRED = ["yobot_core.py", "ohbot_pi.py", "ohbot_azure.py"]


def candidate_folders():
    here = os.path.dirname(os.path.abspath(__file__))
    parent = os.path.dirname(here)
    return [
        os.getenv("OHBOT_DIR"),
        os.path.join(parent, "OhbotPi2"),
        os.path.join(parent, "OhbotPi"),      # what a fresh git clone makes
        os.path.join(parent, "OhbotPi2-main"),  # what GitHub's Download ZIP
        os.path.join(parent, "OhbotPi-main"),   # makes, if nobody renamed it
        os.path.join(parent, "Ohbot"),
        r"C:\Projects\OhbotPi2",
        r"C:\Projects\OhbotPi",
        r"D:\Projects\OhbotPi2",
        "/home/michael/Projects/Ohbot",
        "/Volumes/Projects/Ohbot",
    ]


def find_ohbot_folder():
    """Return the OhbotPi2 folder, or None if it cannot be found."""
    for folder in candidate_folders():
        if not folder:
            continue
        if all(os.path.exists(os.path.join(folder, f)) for f in REQUIRED):
            return os.path.abspath(folder)
    return None


def explain_and_stop():
    """Say what is missing and how to fix it, then stop."""
    here = os.path.dirname(os.path.abspath(__file__))
    print()
    print("=" * 70)
    print("  I cannot find the OhbotPi2 project.")
    print("=" * 70)
    print()
    print("  The chess robots borrow their motor control and their speech")
    print("  from OhbotPi2 rather than having their own copy. So that folder")
    print("  has to be somewhere I can see it.")
    print()
    print("  I looked in these places:")
    for folder in candidate_folders():
        if folder:
            mark = "exists but is missing files" if os.path.isdir(folder) else "not there"
            print(f"      {folder}   ({mark})")
    print()
    print("  To point me at it, make a file called  .env  in this folder:")
    print()
    print(f"      {os.path.join(here, '.env')}")
    print()
    print("  ...containing one line, with your real path:")
    print()
    print(r"      OHBOT_DIR=C:\Projects\OhbotPi2")
    print()
    print("  The folder must contain yobot_core.py, ohbot_pi.py and")
    print("  ohbot_azure.py.")
    print()
    print("=" * 70)
    print()
    raise SystemExit(1)


def add_to_path():
    """
    Put the OhbotPi2 folder on Python's list of places to look for code.

    Returns the folder. Stops the program with a readable message if it is
    not there.
    """
    folder = find_ohbot_folder()
    if folder is None:
        explain_and_stop()

    if folder not in sys.path:
        sys.path.insert(0, folder)

    # The Ohbot code reads its calibration and its .env relative to wherever
    # it is, so it needs to be the working folder. Without this the robot
    # moves to the wrong positions, or refuses to move at all.
    os.chdir(folder)

    return folder


if __name__ == "__main__":
    found = find_ohbot_folder()
    if found:
        print(f"Found the OhbotPi2 project at:\n    {found}")
    else:
        explain_and_stop()
