@echo off
title Yobot Chess - first time setup

REM ===========================================================================
REM  SETUP.bat - run this ONCE on a Windows PC, before the first game
REM ===========================================================================
REM
REM  It does two jobs:
REM
REM     1. Installs the three Python add-ons this project needs.
REM     2. Downloads Stockfish, the chess engine that actually plays.
REM
REM  Stockfish is not part of this download. It is a separate 114 MB program
REM  and GitHub refuses to carry anything that big, so it is fetched here
REM  instead. You need to be online for this one run. After that the chess
REM  show works with no internet at all, except for the robot voices.
REM
REM  Safe to run again. Anything already done is skipped.
REM
REM ===========================================================================

setlocal

REM  Work out where the project is. Beside me first, then one level up, so
REM  this still works if the file gets moved into a subfolder or dragged out.
set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"
set "PROJ=%HERE%"
if not exist "%PROJ%\chess_server.py" (
    for %%I in ("%HERE%\..") do set "PROJ=%%~fI"
)
if not exist "%PROJ%\chess_server.py" goto wrong_folder

cd /d "%PROJ%"

echo.
echo  ======================================================================
echo    Yobot Chess - first time setup
echo  ======================================================================
echo.
echo    Folder: %PROJ%
echo.

REM ---------------------------------------------------------------------------
REM  Which command runs Python on this computer. Some machines have "python",
REM  some only have "py". Written out longhand on purpose - the tidier
REM  one-line version using ^&^& is wrong, because cmd splits the line before
REM  the "if" has been decided.
REM ---------------------------------------------------------------------------
set PY=
where python >nul 2>&1
if not errorlevel 1 set PY=python
if not "%PY%"=="" goto have_python
where py >nul 2>&1
if not errorlevel 1 set PY=py
:have_python
if "%PY%"=="" goto no_python

echo    Python found: %PY%
echo.


REM ---------------------------------------------------------------------------
REM  STEP 1 - the Python add-ons
REM ---------------------------------------------------------------------------
echo  ----------------------------------------------------------------------
echo    Step 1 of 2: installing the Python add-ons
echo  ----------------------------------------------------------------------
echo.
echo    This downloads three small things: the chess rules, the little web
echo    server, and the bit that reads settings out of a file.
echo.

%PY% -m pip install --upgrade pip
%PY% -m pip install -r "%PROJ%\requirements.txt"
if errorlevel 1 goto pip_failed

echo.
echo    Add-ons installed.
echo.


REM ---------------------------------------------------------------------------
REM  STEP 2 - Stockfish
REM ---------------------------------------------------------------------------
echo  ----------------------------------------------------------------------
echo    Step 2 of 2: the chess engine
echo  ----------------------------------------------------------------------
echo.

REM  Already here? Then there is nothing to do. The chess program looks for
REM  anything in this folder whose name starts with "stockfish", so a file
REM  you downloaded by hand counts too.
if exist "%PROJ%\stockfish.exe" goto engine_ready
dir /b "%PROJ%\stockfish*.exe" >nul 2>&1
if not errorlevel 1 goto engine_ready

echo    Downloading Stockfish. It is about 50 MB zipped, so this can take
echo    a couple of minutes on a slow connection. Please wait.
echo.

set "SFURL=https://github.com/official-stockfish/Stockfish/releases/download/sf_18/stockfish-windows-x86-64-avx2.zip"
set "SFZIP=%TEMP%\yobot-stockfish.zip"
set "SFDIR=%TEMP%\yobot-stockfish"

:download_engine
powershell -NoProfile -Command "$ProgressPreference='SilentlyContinue'; try { Invoke-WebRequest -Uri '%SFURL%' -OutFile '%SFZIP%' -UseBasicParsing } catch { exit 1 }"
if errorlevel 1 goto download_failed

powershell -NoProfile -Command "try { Remove-Item -LiteralPath '%SFDIR%' -Recurse -Force -ErrorAction SilentlyContinue; Expand-Archive -LiteralPath '%SFZIP%' -DestinationPath '%SFDIR%' -Force } catch { exit 1 }"
if errorlevel 1 goto unzip_failed

REM  The zip has the program somewhere inside a folder of its own. Find it,
REM  and bring it - and any brain file beside it - out to where we want it.
powershell -NoProfile -Command "$e = Get-ChildItem -LiteralPath '%SFDIR%' -Recurse -Filter 'stockfish*.exe' | Select-Object -First 1; if (-not $e) { exit 1 }; Copy-Item $e.FullName -Destination '%PROJ%\stockfish.exe' -Force; Get-ChildItem -LiteralPath $e.DirectoryName -Filter '*.nnue' | ForEach-Object { Copy-Item $_.FullName -Destination '%PROJ%' -Force }"
if errorlevel 1 goto unzip_failed

if not exist "%PROJ%\stockfish.exe" goto unzip_failed

REM  Does it actually run on THIS computer? The fast build needs a modern
REM  processor. On an older one Windows kills it the instant it starts, and
REM  the only symptom later would be a chess game that never begins.
echo quit | "%PROJ%\stockfish.exe" >nul 2>&1
if not errorlevel 1 goto engine_ready

if not "%SFURL%"=="https://github.com/official-stockfish/Stockfish/releases/download/sf_18/stockfish-windows-x86-64.zip" goto try_slower_build
goto engine_wont_run

:try_slower_build
echo.
echo    That build will not run on this processor. Trying the one that
echo    works on every 64-bit PC instead.
echo.
del "%PROJ%\stockfish.exe" >nul 2>&1
set "SFURL=https://github.com/official-stockfish/Stockfish/releases/download/sf_18/stockfish-windows-x86-64.zip"
goto download_engine


:engine_ready
echo.
echo    Chess engine ready.
echo.
echo  ----------------------------------------------------------------------
echo    Checking it over
echo  ----------------------------------------------------------------------
echo.
%PY% "%PROJ%\check_stockfish.py"

echo.
echo  ======================================================================
echo    SETUP FINISHED
echo  ======================================================================
echo.
echo    To play, double click:    Play Chess.bat
echo    To try it with no robots: Demo - no robots.bat
echo.
echo    The robots themselves also need the OhbotPi2 project on this
echo    computer - that is where their motors and their voice come from.
echo    See "START HERE - Windows.md" if you have not set that up yet.
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
echo    still not find it. Then run SETUP.bat again.
echo.
pause
goto end


:pip_failed
echo.
echo  ======================================================================
echo    THE ADD-ONS WOULD NOT INSTALL
echo  ======================================================================
echo.
echo    Whatever went wrong is printed above this line. The usual causes:
echo.
echo      - no internet connection
echo      - a company or school network blocking the download
echo      - Python installed for "all users" and this window not being
echo        run as administrator
echo.
echo    You can try it by hand in this window:
echo.
echo        %PY% -m pip install chess flask python-dotenv
echo.
pause
goto end


:download_failed
echo.
echo  ======================================================================
echo    COULD NOT DOWNLOAD THE CHESS ENGINE
echo  ======================================================================
echo.
echo    This step needs the internet. If you are offline, or something is
echo    blocking github.com, you can fetch it yourself on any computer:
echo.
echo        https://stockfishchess.org/download/windows/
echo.
echo    Unzip it, find the file whose name starts with "stockfish" and ends
echo    in .exe, and drop that file into:
echo.
echo        %PROJ%
echo.
echo    That is all it needs. The chess program looks in its own folder
echo    first, so it will be found without any further setting up.
echo.
pause
goto end


:unzip_failed
echo.
echo  ======================================================================
echo    THE DOWNLOAD ARRIVED BUT WOULD NOT UNPACK
echo  ======================================================================
echo.
echo    The half-finished download is at:
echo        %SFZIP%
echo.
echo    Try unzipping that by hand - right click, Extract All - then copy
echo    the file starting with "stockfish" and ending ".exe" into:
echo        %PROJ%
echo.
pause
goto end


:engine_wont_run
echo.
echo  ======================================================================
echo    THE CHESS ENGINE WILL NOT START ON THIS COMPUTER
echo  ======================================================================
echo.
echo    Both builds were tried and neither ran. That is unusual and it
echo    normally means antivirus software has quarantined the file - a
echo    freshly downloaded .exe with no publisher is exactly what they
echo    look for.
echo.
echo    Check the antivirus quarantine list for "stockfish", and allow it.
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
echo        %HERE%
echo        %HERE%\..
echo.
echo    ...and neither has chess_server.py in it. This file needs to sit in
echo    the chess folder, or in a folder directly inside it. If you moved
echo    it somewhere else, move it back - or make a SHORTCUT instead,
echo    which can live anywhere.
echo.
pause

:end
endlocal
