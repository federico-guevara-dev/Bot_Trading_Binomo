# 🤖 Alpha Bot v5 — Advanced IA & Vision System

**Alpha Bot v5** es la versión más potente y completa hasta la fecha. Se ha transformado en una estación de trading profesional que combina **Visión Artificial**, **Análisis de Velas Heikin Ashi** y una suite de **9 indicadores técnicos** para operar en Binomo con precisión quirúrgica.

## 💎 Novedades de la v5
* **Gráficos Heikin Ashi**: Implementación de velas de tendencia para un análisis visual más limpio y menos ruidoso.
* **Super-Suite de Indicadores**: 
    * RSI, MACD, Bandas de Bollinger, Estocástico.
    * Parabolic SAR, ATR, ADX, CCI, Awesome Oscillator y Momentum.
* **Monto Autónomo con Escritura**: El bot no solo decide cuánto invertir (Kelly/Martingala), sino que **escribe automáticamente el monto** en la plataforma mediante teclado simulado.
* **Persistencia de Datos**: Guardado automático de configuraciones, ROI (regiones de interés) y parámetros en `config_bot.json`.
* **Motor OCR de Alta Precisión**: Lectura mejorada de saldo, precio y confirmación de resultados para evitar errores de red o lag.

## 🛠 Instalación y Requisitos
1. **Python 3.10+** y **Tesseract OCR** (Añadidos al PATH).
2. Instala el ecosistema de librerías:
   ```bash
   pip install pyautogui pillow pytesseract opencv-python yfinance numpy
