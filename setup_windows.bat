@echo off
echo ======================================================
echo        Auto Face Framing - Windows Setup Helper
echo ======================================================
echo.

:: Check for administrator privileges
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Running this script with administrator privileges...
    echo Please allow the UAC prompt to continue.
    echo.
    goto UACPrompt
) else (
    goto gotAdmin
)

:UACPrompt
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit /B

:gotAdmin
    if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )
    pushd "%CD%"
    CD /D "%~dp0"

:: Main script starts here
echo Detecting Python installation...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found in PATH!
    echo.
    echo Searching for Python installation...
    
    set found=0
    
    :: Check common installation paths
    for %%p in (
        "%ProgramFiles%\Python*" 
        "%ProgramFiles(x86)%\Python*"
        "%LocalAppData%\Programs\Python\Python*"
    ) do (
        if exist "%%p\python.exe" (
            echo Found Python at: %%p
            set "PYTHONPATH=%%p"
            set found=1
            goto :AddToPath
        )
    )
    
    if %found% equ 0 (
        echo Python installation not found.
        echo Please install Python 3.6+ and make sure to check "Add Python to PATH"
        echo during installation.
        pause
        exit /B 1
    )
) else (
    echo Python is already in PATH.
    goto :RunInstall
)

:AddToPath
echo.
echo Adding Python to PATH...
setx PATH "%PATH%;%PYTHONPATH%;%PYTHONPATH%\Scripts" /M
echo Python has been added to PATH.
echo You may need to restart your command prompt for changes to take effect.
echo.

:RunInstall
:: Install the package
echo.
echo Running the installer...
bash install.sh

:: Create the batch file if it doesn't exist
if not exist "start-face-framing.bat" (
    echo.
    echo Creating start-face-framing.bat...
    echo @echo off > start-face-framing.bat
    echo echo Starting Auto Face Framing... >> start-face-framing.bat
    echo python -m autoFaceFraming.cli %%* >> start-face-framing.bat
    echo exit /b %%ERRORLEVEL%% >> start-face-framing.bat
    echo Created start-face-framing.bat successfully.
)

echo.
echo ======================================================
echo       Windows Setup Complete!
echo ======================================================
echo.
echo You can now run Auto Face Framing using:
echo   - start-face-framing.bat
echo   - python -m autoFaceFraming.cli
echo.
echo Press any key to exit...
pause >nul
exit /B 0
