@echo off
setlocal
cd /d "%~dp0"

echo ===================================================
echo   RhythmType - Register .osz and .osu Associations
echo ===================================================
echo.

set "TARGET=%~dp0RhythmType.bat"

:: 1. Register file types in HKCU (User-scoped, no admin required)
reg add "HKCU\Software\Classes\RhythmType.Beatmap\shell\open\command" /ve /t REG_SZ /d "\"%TARGET%\" \"%%1\"" /f >nul 2>&1
reg add "HKCU\Software\Classes\.osz" /ve /t REG_SZ /d "RhythmType.Beatmap" /f >nul 2>&1
reg add "HKCU\Software\Classes\.osu" /ve /t REG_SZ /d "RhythmType.Beatmap" /f >nul 2>&1

:: 2. Register Applications entry for Open With menu
reg add "HKCU\Software\Classes\Applications\RhythmType.bat\shell\open\command" /ve /t REG_SZ /d "\"%TARGET%\" \"%%1\"" /f >nul 2>&1
reg add "HKCU\Software\Classes\Applications\RhythmType.bat\SupportedTypes" /v ".osz" /t REG_SZ /d "" /f >nul 2>&1
reg add "HKCU\Software\Classes\Applications\RhythmType.bat\SupportedTypes" /v ".osu" /t REG_SZ /d "" /f >nul 2>&1

echo [OK] Registered file associations for RhythmType!
echo.
echo NOTE for Windows 10/11:
echo If double-clicking an .osz file still opens osu!:
echo   1. Right-click any .osz or .osu file
echo   2. Click "Open with" -> "Choose another app"
echo   3. Select "RhythmType.bat" (or browse to %TARGET%)
echo   4. Check "Always use this app to open .osz files"
echo.
pause
