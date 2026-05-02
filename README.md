# 🤖 Alpha Bot v1 — Binomo Trading Bot

Alpha Bot es un sistema de trading automatizado diseñado para operar en la plataforma Binomo. A diferencia de otros bots, este utiliza **Visión Computacional (OCR)** para leer directamente el gráfico y los datos de la pantalla, permitiendo un análisis técnico avanzado en tiempo real.

## ✨ Características principales
* **Visión Artificial**: Procesa el precio, saldo y gráficos directamente desde la pantalla.
* **Análisis Técnico**: Soporta 11 indicadores (RSI, MACD, Bandas de Bollinger, Estocástico, Parabolic SAR, ATR, ADX, etc.).
* **Visualización Avanzada**: Gráficos internos con soporte para velas **Heikin Ashi**.
* **Configuración Inteligente**: Archivo `alphabot_config.json` para ajustar coordenadas de pantalla y parámetros de trading.
* **Sistema de Resiliencia**: Detección de recargas de página (F5) y reconexión automática.

---

## ⚠️ Advertencia de Riesgo
**El trading de opciones binarias conlleva un riesgo significativo.** Este bot es una herramienta de automatización y no garantiza beneficios. Úsalo bajo tu propia responsabilidad. Se recomienda probarlo siempre en una **cuenta demo** antes de pasar a real.

---

## 📋 Requisitos Previos

Para que el bot funcione, necesitas tener instalados los siguientes componentes:

1.  **Python 3.10+** (Asegúrate de marcar "Add Python to PATH").
2.  **Tesseract OCR**: 
    * Descárgalo desde [aquí](https://github.com/UB-Mannheim/tesseract/wiki).
    * Instálalo en la ruta por defecto: `C:\Program Files\Tesseract-OCR\tesseract.exe`.

## 🚀 Instalación y Uso

### Paso 1 — Descargar el proyecto
Descarga todos los archivos del repositorio y colócalos en una misma carpeta.

### Paso 2 — Instalar dependencias
Abre una terminal (CMD o PowerShell) en la carpeta del proyecto y ejecuta:
```bash
python instalar.py

Si no tienes instalar.py, puedes instalar las librerías manualmente:

pip install pyautogui pillow pytesseract opencv-python yfinance numpy
```

Ejecución
Tienes dos formas de iniciar el bot:

Opción A (Recomendada): Haz doble clic en el archivo INICIAR_BOT.bat. Este archivo configura automáticamente el entorno.

Opción B (Manual): Ejecuta en la terminal:

```
python bot_trading.py
```

⚙️ Configuración
El bot se basa en el archivo alphabot_config.json. En él podrás:

Configurar las coordenadas x, y de los botones de "Subir" y "Bajar".

Activar o desactivar indicadores específicos.

Ajustar las áreas de la pantalla donde el OCR debe leer el precio y el saldo.

Nota: Asegúrate de que la ventana de trading esté visible y que las coordenadas en el archivo de configuración coincidan con tu resolución de pantalla.
