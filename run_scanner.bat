@echo off
TITLE Network Inventory Scanner v1.0
COLOR 0A

echo.
echo ========================================
echo    Network Inventory Scanner v1.0
echo    Made by: That IT Guy (c) 2024
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found! Please install Python 3.7+ first
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if we're in the right directory
if not exist "network_scanner.py" (
    echo [ERROR] network_scanner.py not found!
    echo Make sure you're running this from the project folder
    pause
    exit /b 1
)

:: Install required packages (commented out for now)
echo [*] Checking dependencies...
pip install requests >nul 2>&1
pip install paramiko >nul 2>&1
pip install wmi >nul 2>&1
pip install pywinrm >nul 2>&1

if %ERRORLEVEL% NEQ 0 (
    echo [!] Some packages might be missing, but we'll try anyway...
)

:: Check if config exists
if not exist "config.json" (
    echo [!] No config.json found, using default settings
    echo [!] You should edit config.json to set your webhooks and network range
)

:: Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

echo.
echo [*] Starting network scanner...
echo [*] Press Ctrl+C to stop scanning
echo [*] Logs will be saved to logs/
echo.
echo [*] Make sure you have:
echo     - Updated config.json with your network settings
echo     - Set up Discord/Slack webhooks if you want alerts
echo     - Configured device credentials for health checks
echo.

:: Main menu - let user choose what to do
:MENU
echo.
echo What do you want to do?
echo 1. Quick network scan (one-time)
echo 2. Continuous monitoring (scans every 5 minutes)
echo 3. Health check only
echo 4. Test alerts
echo 5. View last scan results
echo 6. Exit
echo.
set /p choice="Choose option (1-6): "

if "%choice%"=="1" goto QUICKSCAN
if "%choice%"=="2" goto MONITOR
if "%choice%"=="3" goto HEALTHCHECK
if "%choice%"=="4" goto TESTALERTS
if "%choice%"=="5" goto VIEWRESULTS
if "%choice%"=="6" exit /b 0

echo [!] Invalid choice, try again
goto MENU

:QUICKSCAN
echo.
echo [*] Running quick network scan...
echo [*] This might take a few minutes depending on your network size
python network_scanner.py
echo.
echo [*] Scan complete! Check the JSON files for results
pause
goto MENU

:MONITOR
echo.
echo [*] Starting continuous monitoring...
echo [*] Scanning every 5 minutes (configurable in config.json)
echo [*] Press Ctrl+C to stop monitoring
echo [*] Running in background - you can close this window
python network_scanner.py
pause
goto MENU

:HEALTHCHECK
echo.
echo [*] Running health checks on known devices...
echo [*] This requires proper credentials in config.json
python -c "from health_checker import HealthChecker; import json; hc = HealthChecker(); print(json.dumps(hc.check_local_device(), indent=2))"
pause
goto MENU

:TESTALERTS
echo.
echo [*] Testing alert system...
echo [*] Make sure your webhooks are configured in config.json
python alert_system.py
pause
goto MENU

:VIEWRESULTS
echo.
echo [*] Looking for recent scan results...
dir /b network_inventory_*.json > temp_results.txt 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [!] No scan results found yet
    goto MENU
)

echo [*] Recent scan results:
type temp_results.txt
echo.
del temp_results.txt >nul 2>&1

set /p filename="Enter filename to view (or press Enter to go back): "
if "%filename%"=="" goto MENU

if exist "%filename%" (
    echo.
    echo [*] Contents of %filename%:
    type "%filename%"
) else (
    echo [!] File not found: %filename%
)
pause
goto MENU

:: Auto-run mode (if started with parameters)
if not "%1"=="" (
    echo [*] Auto-run mode detected: %1
    if "%1"=="scan" goto QUICKSCAN
    if "%1"=="monitor" goto MONITOR
    if "%1"=="health" goto HEALTHCHECK
    echo [!] Unknown auto-run parameter: %1
)

echo.
echo [*] Done! Check the logs folder for detailed logs
echo [*] Network inventory files are saved as network_inventory_YYYYMMDD_HHMMSS.json
echo.
pause