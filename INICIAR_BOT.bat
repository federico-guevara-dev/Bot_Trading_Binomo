@echo off
title ALPHA BOT v3 - Binomo Auto-Detection
color 0B
cls

echo.
echo  ====================================================
echo    ALPHA BOT v3 - Binomo - Deteccion Automatica
echo  ====================================================
echo.

:: Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no encontrado.
    echo  Descargalo de: https://python.org/downloads
    echo  Tilda "Add Python to PATH" al instalar.
    pause
    exit /b 1
)

echo  Python OK.

:: Instalar dependencias faltantes
echo  Verificando dependencias...

python -c "import pyautogui" >nul 2>&1
if errorlevel 1 ( echo  Instalando pyautogui... & python -m pip install pyautogui -q )

python -c "from PIL import Image" >nul 2>&1
if errorlevel 1 ( echo  Instalando pillow... & python -m pip install pillow -q )

python -c "import pytesseract" >nul 2>&1
if errorlevel 1 ( echo  Instalando pytesseract... & python -m pip install pytesseract -q )

python -c "import cv2" >nul 2>&1
if errorlevel 1 ( echo  Instalando opencv... & python -m pip install opencv-python -q )

python -c "import yfinance" >nul 2>&1
if errorlevel 1 ( echo  Instalando yfinance... & python -m pip install yfinance -q )

python -c "import numpy" >nul 2>&1
if errorlevel 1 ( echo  Instalando numpy... & python -m pip install numpy -q )

echo  Dependencias OK.
echo.
echo  IMPORTANTE: Para OCR (lectura de precio en pantalla),
echo  instala Tesseract OCR desde:
echo  https://github.com/UB-Mannheim/tesseract/wiki
echo.
echo  Iniciando bot en 2 segundos...
timeout /t 2 /nobreak >nul

:: Ejecutar en la misma carpeta que el .bat
cd /d "%~dp0"
python bot_trading.py

if errorlevel 1 (
    echo.
    echo  [ERROR] El bot cerro con un error.
    pause
)
