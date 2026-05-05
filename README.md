# 🤖 Alpha Bot v3 — Advanced Vision Trading System

**Alpha Bot** es una plataforma de trading automatizado de grado avanzado para Binomo. A diferencia de las versiones anteriores, este sistema utiliza **Inteligencia Visual (OCR)** y **Visión Artificial** para interactuar con el mercado de forma humana, analizando datos directamente de la pantalla en tiempo real.

## 🌟 Características Destacadas
* **Visión Computacional (OCR)**: Lectura automática de saldo, precio actual y resultados de operaciones mediante `Tesseract OCR` y `OpenCV`.
* **Gestión de Capital Inteligente**: Algoritmos profesionales integrados:
    * **Fracción de Kelly**: Optimización de inversión según probabilidad.
    * **Martingala & Anti-Martingala**: Sistemas de progresión configurables.
    * **Interés Fijo**: Para un control de riesgo conservador.
* **Análisis Técnico Pro**: Motor que combina RSI, MACD, Medias Móviles (EMA), Bandas de Bollinger y patrones de velas (Martillo, Estrella Fugaz, etc.).
* **Selector de Región Dinámico**: Herramienta visual para definir áreas de lectura (saldo, precio, botones), garantizando compatibilidad con cualquier resolución de monitor.
* **Dashboard en Tiempo Real**: Interfaz gráfica (GUI) con historial de operaciones, visualización de indicadores y estado del bot.

---

## ⚠️ Advertencia de Riesgo
**El trading de opciones binarias conlleva un alto riesgo de pérdida de capital.** Alpha Bot es una herramienta tecnológica de asistencia y no garantiza beneficios económicos. Se recomienda estrictamente probar el sistema en **Cuenta Demo** para calibrar el OCR y la estrategia antes de operar con fondos reales.

---

## 📋 Requisitos del Sistema
1.  **Python 3.10+** (Añadido al PATH).
2.  **Tesseract OCR**: 
    * Instalar en: `C:\Program Files\Tesseract-OCR\tesseract.exe`.
    * [Descargar aquí](https://github.com/UB-Mannheim/tesseract/wiki).
3.  **Librerías necesarias**:
    ```bash
    pip install pyautogui pillow pytesseract opencv-python yfinance numpy
    ```

## 🚀 Instalación y Uso rápido

### Paso 1 — Configuración
Asegúrate de que tu plataforma de trading esté abierta en Chrome y que el gráfico sea claramente visible.

### Paso 2 — Ejecución
Puedes iniciar el sistema de dos maneras:
* **Opción A**: Doble clic en `INICIAR_BOT.bat` (Verifica dependencias automáticamente).
* **Opción B**: Ejecutar `python bot_trading.py` desde la terminal.

### Paso 3 — Calibración OCR
Al iniciar, utiliza el **Selector de Regiones** para marcar en tu pantalla:
1.  El área donde aparece el saldo.
2.  El área donde se muestra el precio actual.
3.  La ubicación de los botones de "Subir" y "Bajar".

---

## ⚙️ Configuración Personalizada
El archivo `alphabot_config.json` guarda tus coordenadas y preferencias de indicadores automáticamente para que no tengas que configurar el bot en cada inicio.

---
*Desarrollado para la comunidad de trading algorítmico y automatización con Python.*
