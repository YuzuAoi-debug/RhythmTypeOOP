@echo off
setlocal
cd /d "%~dp0"

:: Launch game passing any command line arguments (such as clicked .osz or .osu file)
python main.py %*
