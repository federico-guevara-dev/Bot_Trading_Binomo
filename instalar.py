# ╔══════════════════════════════════════════════╗
# ║     ALPHA BOT — Instrucciones de instalación ║
# ╚══════════════════════════════════════════════╝

# 1) INSTALACIÓN RÁPIDA
# Ejecutá este archivo directamente:
#     python instalar.py

import subprocess, sys

paquetes = [
    "pyautogui",
    "yfinance",
    "pandas",
    "numpy",
    "requests",
    "pillow",
]

print("📦 Instalando dependencias del bot...\n")
for pkg in paquetes:
    print(f"  → {pkg}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

print("\n✅ Todo instalado. Ahora ejecutá:")
print("   python bot_trading.py\n")
