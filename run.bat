@echo off
cd /d "%~dp0"
if "%~1"=="BCM_HIDDEN" goto :run
set "VBS=%TEMP%\bcm_run_%RANDOM%.vbs"
> "%VBS%" echo Set s = CreateObject("WScript.Shell"^)
>> "%VBS%" echo s.Run "cmd /c ""%~f0"" BCM_HIDDEN", 0, False
cscript //nologo "%VBS%" >nul 2>&1
del "%VBS%" >nul 2>&1
exit /b

:run
if not exist ".venv\Scripts\pythonw.exe" (
    py -3.11 -m venv .venv
    if errorlevel 1 goto :error
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)
rem Dung pythonw THAT (GUI subsystem, khong console) cua interpreter goc,
rem kem PYTHONPATH tro vao site-packages cua venv.
set "PYHOME="
for /f "tokens=1,* delims== " %%a in ('findstr /b "home" ".venv\pyvenv.cfg"') do set "PYHOME=%%b"
set "PYW=%PYHOME%\pythonw.exe"
if not exist "%PYW%" set "PYW=%~dp0.venv\Scripts\pythonw.exe"
set "PYTHONPATH=%~dp0.venv\Lib\site-packages"
set "VBS=%TEMP%\bcm_app_%RANDOM%.vbs"
> "%VBS%" echo Set s = CreateObject("WScript.Shell"^)
>> "%VBS%" echo s.Run """%PYW%"" main.py", 1, False
cscript //nologo "%VBS%" >nul 2>&1
del "%VBS%" >nul 2>&1
exit /b 0

:error
echo.
echo Khong the khoi dong Benj Cursor Maker.
pause
exit /b 1
