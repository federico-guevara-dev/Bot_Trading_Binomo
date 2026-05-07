# 🤖 Alpha Bot v4 — Professional Vision Trading System

**Alpha Bot v4** es un ecosistema de trading algorítmico de alto rendimiento. A diferencia de otros bots, este sistema utiliza **Inteligencia Visual** para "leer" la plataforma de trading como lo haría un humano, eliminando la necesidad de APIs externas y permitiendo una ejecución precisa basada en lo que sucede en pantalla en tiempo real.

## 🚀 Innovaciones de la v4
* **Gestión de Monto Autónoma**: El bot ahora decide cuánto invertir basándose en el **Criterio de Kelly**, Martingala inteligente o gestión de interés fijo.
* **Lectura Dinámica de Saldo**: Integración total con `Tesseract OCR` para actualizar el capital disponible y los resultados de cada operación automáticamente.
* **Análisis Técnico de 360°**: 
    * **Indicadores**: RSI, MACD, Medias Móviles (EMA 10/26) y Bandas de Bollinger.
    * **Acción del Precio**: Detección de patrones de velas (Martillo, Estrella Fugaz, etc.).
    * **Filtro de Noticias**: Simulación de impacto fundamental para evitar mercados volátiles.
* **Interfaz Gráfica Pro**: GUI desarrollada en `Tkinter` con gráficos en tiempo real, historial de operaciones y selector de regiones manual para máxima compatibilidad.

## 📋 Requisitos Previos
1.  **Python 3.10+** (Instalado con la opción "Add to PATH").
2.  **Tesseract OCR**: Motor de reconocimiento de texto esencial para la lectura de precios y saldo.
3.  **Librerías principales**: 
    ```bash
    pip install pyautogui pillow pytesseract opencv-python yfinance numpy
    ```

## ⚡ Guía de Inicio
1.  **Configura Binomo**: Abre la plataforma en tu navegador y asegúrate de que el gráfico sea visible.
2.  **Ejecuta el Bot**: Inicia `INICIAR_BOT.bat` o `python bot_trading_v4.py`.
3.  **Calibra el Visor**: Utiliza el selector integrado para marcar las áreas de:
    * 💰 Saldo de la cuenta.
    * 📈 Precio del activo.
    * 🔴/🟢 Botones de operación.
4.  **Operación**: Ajusta tu estrategia de riesgo en el panel y presiona "Iniciar".

## ⚙️ Arquitectura del Sistema
El bot se autogestiona mediante un archivo `alphabot_config.json`, permitiendo que tus coordenadas y configuraciones de indicadores se guarden para la siguiente sesión, optimizando el tiempo de arranque.

---

## ⚠️ Descargo de Responsabilidad
**El trading de opciones binarias implica un riesgo significativo de pérdida.** Alpha Bot v4 es un software de automatización creado con fines educativos. Se recomienda encarecidamente utilizarlo en **Cuentas Demo** para validar la estrategia. El desarrollador no se hace responsable por pérdidas financieras derivadas del uso de esta herramienta.

---
*Desarrollado con Python y Visión Artificial para la nueva generación de traders algorítmicos.*
