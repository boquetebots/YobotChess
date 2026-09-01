@echo off
title Yobot Chess - demo

REM ===========================================================================
REM  Demo - no robots.bat
REM ===========================================================================
REM
REM  The same display, playing a famous game to itself. Nothing on the screen
REM  is real and nothing needs to be plugged in - no robots, no Mac, no
REM  Stockfish, no Azure, no internet.
REM
REM  For showing people what it looks like, checking the board reads from the
REM  back of the room, and setting up a projector before the robots arrive.
REM
REM  Closing this window stops it.

cd /d "%~dp0"

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
echo    Yobot Chess - DEMO
echo  ======================================================================
echo.
echo    Nothing on this screen is real. No robot is connected and no
echo    chess engine is running - it is replaying a famous game.
echo.
echo    LEAVE THIS WINDOW OPEN. Closing it stops the demo.
echo.

start "" /b powershell -NoProfile -WindowStyle Hidden -Command "$stop=(Get-Date).AddSeconds(90); $up=$false; while((Get-Date) -lt $stop) { try { $c=New-Object Net.Sockets.TcpClient('127.0.0.1',8080); $c.Close(); $up=$true; break } catch { Start-Sleep -Milliseconds 400 } }; if ($up) { Start-Process 'http://localhost:8080/'; Start-Sleep -Seconds 4; (New-Object -ComObject WScript.Shell).SendKeys('{F11}') }"

%PY% chess_show.py --demo

echo.
echo    The demo has stopped.
echo.
pause
goto end

:no_python
echo.
echo    PYTHON IS NOT INSTALLED ON THIS COMPUTER.
echo.
echo    Get it from https://www.python.org/downloads/ and TICK THE BOX
echo    that says "Add Python to PATH" when the installer asks.
echo.
pause
goto end

:wrong_folder
echo.
echo    I cannot find chess_show.py in:
echo        %CD%
echo.
echo    This file has to sit in the same folder as the chess programs.
echo    Make a SHORTCUT to it if you want it somewhere else.
echo.
pause

:end
