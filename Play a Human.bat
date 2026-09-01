@echo off
title Yobot Chess - a guest plays the robot

REM ===========================================================================
REM  Play a Human.bat - double click this when someone wants a turn
REM ===========================================================================
REM
REM  ONE laptop, ONE robot, ONE guest. This is the everyday setup.
REM
REM  It starts the game, opens the board on this screen and goes fullscreen.
REM  The guest taps a piece, taps where it should go, and the robot answers -
REM  out loud, with its mouth moving.
REM
REM  Nothing else is needed. No second computer, no network, no Mac, no Pi.
REM
REM  THIS BLACK WINDOW IS THE SHOW. Leave it alone while you are playing.
REM  Closing it stops everything.
REM
REM  For two robots playing EACH OTHER, use "Play Chess.bat" instead.
REM
REM  ---------------------------------------------------------------------
REM  SETTINGS - change these and save. Nothing else to edit.
REM  ---------------------------------------------------------------------

REM  Which colour the GUEST plays. white or black.
REM  White moves first, which is what most people expect. The robot takes
REM  whichever colour is left.
set GUEST=white

REM  How hard the robot tries. friendly, beginner, club, strong, expert, max,
REM  or a number from 1320 to 3190.
REM
REM  LEAVE THIS ALONE unless you have a reason. "friendly" is deliberate: at
REM  club strength a guest loses every single game, and the next person stops
REM  asking for a turn. Friendly still punishes a free piece, so winning
REM  means something.
set STRENGTH=friendly

REM  ---------------------------------------------------------------------
REM  Nothing below here needs changing.
REM  ---------------------------------------------------------------------

cd /d "%~dp0"

REM  Which command runs Python on this computer. Some machines have "python",
REM  some only have "py". Written out longhand on purpose - the tidier
REM  one-line version using ^&^& is wrong, because cmd splits the line before
REM  the "if" has been decided.
set PY=
where python >nul 2>&1
if not errorlevel 1 set PY=python
if not "%PY%"=="" goto have_python
where py >nul 2>&1
if not errorlevel 1 set PY=py
:have_python
if "%PY%"=="" goto no_python

if not exist chess_show.py goto wrong_folder

echo.
echo  ======================================================================
echo    Yobot Chess - a guest plays the robot
echo  ======================================================================
echo.
echo    Starting up. The board will appear on this screen in a moment.
echo.
echo    The guest plays: %STRENGTH% robot, guest has %GUEST%
echo.
echo    WHAT TO DO WHEN THE PAGE OPENS:
echo.
echo       1. Press "Start game server"
echo       2. Press "New game"
echo       3. Press the robot's Start button
echo.
echo    Then hand it over. Tap a piece, tap where it goes.
echo.
echo    LEAVE THIS WINDOW OPEN while you are playing.
echo    Closing it stops the game.
echo.

REM  Open the browser in the background, once the page is actually up.
REM
REM  It has to WAIT. Opening the browser straight away gives "cannot reach
REM  this page", because Stockfish takes a few seconds to wake up - and the
REM  natural reaction to that is to think the whole thing is broken.
REM
REM  Then F11, which is the same key you would press yourself. Windows has no
REM  way to make an unknown browser start up fullscreen, so this opens YOUR
REM  browser and presses the key. If it does not take, press F11 yourself -
REM  that is all it is doing.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "$stop=(Get-Date).AddSeconds(90); $up=$false; while((Get-Date) -lt $stop) { try { $c=New-Object Net.Sockets.TcpClient('127.0.0.1',8080); $c.Close(); $up=$true; break } catch { Start-Sleep -Milliseconds 400 } }; if ($up) { Start-Process 'http://localhost:8080/'; Start-Sleep -Seconds 4; (New-Object -ComObject WScript.Shell).SendKeys('{F11}') }"

%PY% chess_show.py --human %GUEST% --polite --strength %STRENGTH%

REM  If we get here the program has stopped, one way or another. Hold the
REM  window open so whatever it printed can still be read - a window that
REM  vanishes takes the explanation with it.
echo.
echo  ======================================================================
echo    The chess program has stopped.
echo  ======================================================================
echo.
echo    If that was not you closing it, whatever went wrong is printed
echo    above this line.
echo.
pause
goto end

:no_python
echo.
echo  ======================================================================
echo    PYTHON IS NOT INSTALLED ON THIS COMPUTER
echo  ======================================================================
echo.
echo    Nothing here can run without it. Get it from:
echo.
echo        https://www.python.org/downloads/
echo.
echo    When the installer asks, TICK THE BOX that says
echo    "Add Python to PATH". Without that tick this file will
echo    still not find it.
echo.
pause
goto end

:wrong_folder
echo.
echo  ======================================================================
echo    I CANNOT FIND THE CHESS PROGRAM
echo  ======================================================================
echo.
echo    I looked in:
echo        %CD%
echo.
echo    ...and there is no chess_show.py there. This file has to sit in
echo    the same folder as the rest of the chess programs. If you moved
echo    it or made a copy somewhere else, move it back - or make a
echo    SHORTCUT to it instead, which can live anywhere.
echo.
pause

:end
