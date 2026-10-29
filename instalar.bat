@echo off
title Instalacao - Scraper Mercado Livre
cd /d "%~dp0"

echo.
echo ==========================================
echo INSTALANDO DEPENDENCIAS
echo ==========================================
echo.

python -m pip install --upgrade pip
if errorlevel 1 goto erro

python -m pip install -r requirements.txt
if errorlevel 1 goto erro

python -m playwright install chromium
if errorlevel 1 goto erro

echo.
echo ==========================================
echo INSTALACAO CONCLUIDA
echo ==========================================
pause
exit /b 0

:erro
echo.
echo ERRO DURANTE A INSTALACAO.
pause
exit /b 1
