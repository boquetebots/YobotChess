@echo off
title Yobot Chess

REM ===========================================================================
REM  Play Chess.bat - double click this to run the show
REM ===========================================================================
REM
REM  It starts the chess program, waits until the display page is genuinely
REM  ready, opens it in your normal browser and puts it fullscreen.
REM
REM  THIS BLACK WINDOW IS THE SHOW. Leave it alone while you are playing.
REM  Closing it stops everything - the server and both robots.
REM
REM  The three buttons for starting the robots are on the page itself.
REM
REM  ---------------------------------------------------------------------
REM  SETTINGS - change the numbers below and save. Nothing else to edit.
REM  ---------------------------------------------------------------------

REM  How strong the robots play. beginner, club, strong, expert, max, or a
REM  number from 1320 to 3190. Weaker is better for an audience: pieces hang,
REM  sacrifices land, somebody actually gets checkmated.
set STRENGTH=club

REM  Seconds of silence between one robot finishing and the other starting.
REM  Raise it if they sound rushed, lower it if the game drags.
set GAP=0.8

REM  How far behind a robot must be before it gives up, in hundredths of a
REM  pawn. -900 is about a queen down. This is the main control on how long
REM  a game lasts. Use 0 to turn resigning off.
set RESIGN=-900

REM  Where the Mac is, so the "Start Goldie" button on the page can launch
REM  her over the network. Delete the word REM from the next line and put the
REM  Mac's real address in. Leave it as it is to start Goldie by hand.
REM set MAC=192.168.50.20

REM  ---------------------------------------------------------------------
REM  Nothing below here needs changing.
REM  ---------------------------------------------------------------------

cd /d "%~dp0"

REM  Which command runs Python on this computer. Some machines have "python",
REM  some only have "py". Checking is quicker than explaining the difference.
REM  Written out longhand on purpose. The one-line version of this using &&
REM  looks tidier and is wrong: cmd splits the line before the "if" is
REM  decided, so the second half can run when the first half never did.
set PY=
where python >nul 2>&1
if not errorlevel 1 set PY=python
if not "%PY%"=="" goto have_python
where py >nul 2>&1
if not errorlevel 1 set PY=py
:have_python
if "%PY%"=="" goto no_python

if not exist chess_show.py goto wrong_folder

set EXTRA=
if not "%MAC%"=="" set EXTRA=--mac %MAC%

echo.
echo  ======================================================================
echo    Yobot Chess
echo  ======================================================================
echo.
echo    Starting up. The board will appear in your browser in a moment.
echo.
echo    Strength: %STRENGTH%    Gap: %GAP%s    Resigns at: %RESIGN%
if not "%MAC%"=="" echo    Goldie's Mac: %MAC%
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
REM  way to make an unknown browser start up fullscreen: only Chrome and Edge
REM  take a fullscreen switch, and using one of those would ignore whichever
REM  browser you actually chose. So this opens YOUR browser and presses the
REM  key. If it does not take, press F11 yourself - that is all it is doing.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "$stop=(Get-Date).AddSeconds(90); $up=$false; while((Get-Date) -lt $stop) { try { $c=New-Object Net.Sockets.TcpClient('127.0.0.1',8080); $c.Close(); $up=$true; break } catch { Start-Sleep -Milliseconds 400 } }; if ($up) { Start-Process 'http://localhost:8080/'; Start-Sleep -Seconds 4; (New-Object -ComObject WScript.Shell).SendKeys('{F11}') }"

%PY% chess_show.py --strength %STRENGTH% --gap %GAP% --resign-at %RESIGN% %EXTRA%

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
