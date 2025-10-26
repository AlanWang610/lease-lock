@echo off
REM Lock Daemon Runner Script for Windows

REM Check if .env file exists
if exist ".env" (
    echo Loading environment from .env file...
    for /f "usebackq tokens=1,2 delims==" %%a in (".env") do (
        if not "%%a"=="" if not "%%a:~0,1%"=="#" (
            set "%%a=%%b"
        )
    )
)

REM Check if LEASE_REGISTRY_ID is set
if "%LEASE_REGISTRY_ID%"=="" (
    echo Error: LEASE_REGISTRY_ID environment variable is required
    echo Set it in your environment or create a .env file with:
    echo LEASE_REGISTRY_ID=your_contract_id_here
    pause
    exit /b 1
)

echo Starting Lock Daemon...
echo Contract ID: %LEASE_REGISTRY_ID%
echo RPC Endpoint: %STELLAR_RPC%
echo.

REM Run the daemon
python iot_lock_daemon.py

pause
