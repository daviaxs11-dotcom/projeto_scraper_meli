@echo off
title Scraper Mercado Livre - Python
cd /d "%~dp0"

echo.
echo ==========================================
echo SCRAPER MERCADO LIVRE
echo ==========================================
echo.

python main.py

if errorlevel 1 (
    echo.
    echo O programa terminou com erro.
)

pause
