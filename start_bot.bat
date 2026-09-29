@echo off
title Xartech Telegram Bot
color 0A
echo ========================================================
echo        XARTECH CLIENT VISIT TELEGRAM BOT LAUNCHER
echo ========================================================
echo.
echo Checking Python environment...
python -c "import telegram, openpyxl, reportlab, PIL; print('All libraries verified!')" 2>nul
if %errorlevel% neq 0 (
    echo Installing missing requirements...
    pip install -r requirements.txt
)

echo.
echo Starting Xartech Bot...
echo Press CTRL + C to stop the bot.
echo ========================================================
python bot.py
pause
