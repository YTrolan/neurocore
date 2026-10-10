@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   NeuroCore GUI
echo ============================================
echo.
python -m neurocore.gui
pause
