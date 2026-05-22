# 🤖 Alpha Bot v6 — Precision IA & Vision System

**Alpha Bot v6** es el pináculo de la automatización táctica para Binomo. Esta versión introduce mejoras críticas en la estabilidad del entorno y en la captura visual, integrando soporte nativo para el escalado de pantalla del sistema operativo (`ctypes`), lo que garantiza una calibración de coordenadas milimétrica y libre de fallos por resolución.

## 💎 Características Principales (v6)
* **Ajuste de Precisión DPI**: Soporte avanzado que previene desajustes de coordenadas en pantallas con escalados de Windows activos.
* **Gráficos Heikin Ashi**: Sistema de suavizado de tendencia visual para aislar el ruido del mercado y mejorar las lecturas del gráfico en vivo.
* **Suite de 9 Indicadores**: Análisis simultáneo en tiempo real (RSI, MACD, Bandas de Bollinger, Estocástico, Parabolic SAR, ATR, ADX, CCI, Awesome Oscillator y Momentum).
* **Monto Autónomo con Escritura Dinámica**: Gestión inteligente del riesgo (Criterio de Kelly / Martingala) con automatización de teclado para tipear el monto exacto en el bloque operativo de la plataforma.
* **Estructura Persistente**: Configuración guardada automáticamente en un archivo local `config_bot.json` para agilizar los arranques diarios.

## 🛠 Instalación y Requisitos
1. Contar con **Python 3.10+** y **Tesseract OCR** instalados y añadidos correctamente a las variables de entorno (`PATH`).
2. Instalar el paquete de librerías requerido:
   ```bash
   pip install pyautogui pillow pytesseract opencv-python yfinance numpy

🚀 Guía de Operación Rápida
Calibrar Regiones: Ejecuta el bot y marca las áreas correspondientes al Saldo, Precio actual y la caja de texto para la edición del Monto.

Establecer Parámetros: Ajusta tu Stop Loss, Take Profit y la estrategia de gestión financiera en el panel gráfico integrado.

Producción: Inicia el bot para que procese de forma combinada los indicadores técnicos y ejecute órdenes de alta probabilidad.

⚠️ Advertencia de Riesgo
Este desarrollo posee carácter estrictamente académico y de investigación de lógica algorítmico-computacional. Operar opciones binarias conlleva un riesgo elevado de pérdida de capital. Valida siempre el rendimiento general y el comportamiento del OCR en Cuenta Demo antes de interactuar en escenarios reales.

Desarrollado con Python y Visión Artificial para la automatización avanzada.
