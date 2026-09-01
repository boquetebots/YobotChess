"""
chess_show_agent.py — the little listener that lives on the Mac.

WHY THIS EXISTS
===============

The control page runs on the Windows PC. Goldie's robot runs on the Mac.
Pressing a button on the PC cannot start a program on the Mac by itself —
there has to be something already awake over there to receive the message.

This is that something. It does one job: start and stop `chess_player.py`
when the PC asks. It holds no chess knowledge, no API key, and no opinions.

    python3 chess_show_agent.py

Leave the window open. It prints one line per instruction so you can see the
PC talking to it.


YOU DO NOT HAVE TO USE IT
=========================

Everything works without this. If it is not running, the Black button on the
control page simply says it cannot see the Mac, and you start Goldie the way
MAC_SETUP.md describes:

    python3 chess_player.py --colour black --server 192.168.50.100

This only saves you walking over to the Mac.


A NOTE ON SAFETY
================

This accepts instructions over the network, so it is deliberately narrow: it
can start exactly one program, `chess_player.py`, in its own folder, and stop
it again. It cannot be told to run anything else. The colour and the server
address are the only things it takes from the message, and both are checked
before use.

Run it on a home or venue network you trust. It is not built to face the
open internet, and it never needs to.
"""

import argparse
import os
import re
import subprocess
import sys
import threading

from chess_needs import require, python_cmd

require("flask")

from flask import Flask, jsonify, request


HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PORT = 8090

# The address of a machine on the local network, and nothing else. Anything
# that does not look like this is refused rather than passed on.
ADDRESS_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-]{0,60}$")


class Player:
    """Goldie's chess program, and whether it is running."""

    def __init__(self):
        self.process = None
        self.output = []
        self.lock = threading.Lock()

    def running(self):
        return self.process is not None and self.process.poll() is None

    def start(self, colour, server):
        with self.lock:
            if self.running():
                return False, "Goldie is already running."

            command = [python_cmd(), "chess_player.py",
                       "--colour", colour, "--server", server]
            self.output = []
            try:
                self.process = subprocess.Popen(
                    command, cwd=HERE,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1,
                )
            except Exception as exc:
                return False, f"Could not start it: {exc}"

            threading.Thread(target=self._drain, daemon=True).start()
            print(f"  started:  {' '.join(command)}")
            return True, f"Started {colour}, talking to {server}."

    def _drain(self):
        process = self.process
        if process is None or process.stdout is None:
            return
        for line in process.stdout:
            self.output.append(line.rstrip())
            del self.output[:-200]

    def stop(self):
        with self.lock:
            if not self.running():
                self.process = None
                return True, "It was not running."
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # A player that will not quit keeps hold of the robot's USB
                # cable, and nothing else can have it until this lets go.
                self.process.kill()
                self.process.wait(timeout=5)
            self.process = None
            print("  stopped")
            return True, "Stopped."


def main():
    parser = argparse.ArgumentParser(
        description="Lets the control page on the PC start and stop this "
                    "computer's robot.",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"port to listen on (default {DEFAULT_PORT})")
    args = parser.parse_args()

    player = Player()
    app = Flask("chess_show_agent")

    @app.route("/agent/state")
    def state():
        return jsonify({
            "running": player.running(),
            "log": player.output[-12:],
        })

    @app.route("/agent/start", methods=["GET", "POST"])
    def start():
        colour = request.args.get("colour", "black").lower()
        server = request.args.get("server", "").strip()

        if colour not in ("white", "black"):
            return jsonify({"ok": False, "message": "Colour must be white or black."})
        if not ADDRESS_PATTERN.match(server):
            return jsonify({"ok": False,
                            "message": f"That is not an address I will use: {server!r}"})

        ok, message = player.start(colour, server)
        return jsonify({"ok": ok, "message": message})

    @app.route("/agent/stop", methods=["GET", "POST"])
    def stop():
        ok, message = player.stop()
        return jsonify({"ok": ok, "message": message})

    print()
    print("  Waiting for the control page on the PC.")
    print(f"  Listening on port {args.port}. Ctrl-C to stop.")
    print()

    try:
        app.run(host="0.0.0.0", port=args.port, debug=False, threaded=True)
    except KeyboardInterrupt:
        pass
    finally:
        player.stop()


if __name__ == "__main__":
    main()
