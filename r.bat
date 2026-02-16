@echo off
TITLE Network Scanner v1.0
COLOR 0A

echo.
echo Network Scanner v1.0
echo.
echo Made by: That IT Guy
echo.

python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python not found!
    echo Install from: https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist "n.py" (
    echo [!] n.py not found!
    echo Run from project folder
    pause
    exit /b 1
)

echo.
echo [*] Checking dependencies...

pip show requests >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Installing requests...
    pip install requests
)

pip show paramiko >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Installing paramiko...
    pip install paramiko
)

pip show wmi >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Installing wmi...
    pip install wmi
)

pip show pywinrm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Installing pywinrm...
    pip install pywinrm
)

echo [*] Dependencies ready!

if not exist "logs" mkdir logs

echo.
echo [*] Starting scanner...
echo [*] Press Ctrl+C to stop
echo.

:MENU
echo.
echo Choose:
echo 1. Quick scan
echo 2. Continuous monitor
echo 3. Health check
echo 4. Test alerts
echo 5. Exit
echo.
set /p choice="Option (1-5): "

if "%choice%"=="1" goto QUICK
if "%choice%"=="2" goto MONITOR
if "%choice%"=="3" goto HEALTH
if "%choice%"=="4" goto TEST
if "%choice%"=="5" exit /b 0

echo [!] Invalid choice
goto MENU

:QUICK
echo.
echo [*] Scanning...
python n.py
echo.
echo [*] Done!
pause
goto MENU

:MONITOR
echo.
echo [*] Monitoring started
echo [*] Scans every 5 minutes
python n.py
pause
goto MENU

:HEALTH
echo.
echo [*] Health check...
python -c "from h import H; import json; h = H(); print(json.dumps(h.local(), indent=2))"
pause
goto MENU

:TEST
echo.
echo [*] Testing alerts...
python a.py
pause
goto MENU

if not "%1"=="" (
    if "%1"=="scan" goto QUICK
    if "%1"=="monitor" goto MONITOR
    if "%1"=="health" goto HEALTH
)

echo.
pause