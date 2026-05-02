"""
╔══════════════════════════════════════════════════════════╗
║   ALPHA BOT v3 — Binomo · Detección de Pantalla         ║
║   RSI + MACD + EMA + Velas · OCR · PyAutoGUI            ║
║   Auto-detección de mercado · Ejecución automática      ║
╚══════════════════════════════════════════════════════════╝

Instalación:
    pip install pyautogui pillow pytesseract opencv-python yfinance numpy

Tesseract OCR (para leer precio de pantalla):
    https://github.com/UB-Mannheim/tesseract/wiki  (Windows)
    Instalar y agregar al PATH, o poner ruta abajo en TESSERACT_PATH
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading, time, random, math, os, sys
from datetime import datetime

# ── Tesseract path (ajustar si es necesario) ──────────
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ── Imports opcionales ────────────────────────────────
try:
    import pyautogui
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False

try:
    from PIL import Image, ImageGrab, ImageEnhance, ImageFilter
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    import pytesseract
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    OCR_OK = True
except ImportError:
    OCR_OK = False

try:
    import cv2, numpy as np
    CV2_OK = True
except ImportError:
    CV2_OK = False

try:
    import yfinance as yf
    YFINANCE_OK = True
except ImportError:
    YFINANCE_OK = False

# ── Colores ───────────────────────────────────────────
C = {
    "bg":      "#040d1a",
    "panel":   "#071428",
    "border":  "#0e2a3a",
    "text":    "#e2e8f0",
    "muted":   "#475569",
    "green":   "#22c55e",
    "red":     "#ef4444",
    "yellow":  "#f59e0b",
    "blue":    "#0ea5e9",
    "purple":  "#6366f1",
    "success": "#86efac",
    "warn":    "#fcd34d",
    "error":   "#fca5a5",
    "dark":    "#020914",
}

# ════════════════════════════════════════════════════
#   INDICADORES TÉCNICOS
# ════════════════════════════════════════════════════
def calc_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0
    gains = losses = 0.0
    for i in range(len(prices) - period, len(prices)):
        d = prices[i] - prices[i - 1]
        if d > 0: gains += d
        else:     losses += abs(d)
    rs = gains / (losses or 1e-9)
    return 100 - 100 / (1 + rs)

def calc_ema(prices, period):
    if len(prices) < period:
        return prices[-1] if prices else 0.0
    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for p in prices[period:]:
        ema = p * k + ema * (1 - k)
    return ema

def calc_macd(prices):
    if len(prices) < 26: return 0.0, 0.0
    macd = calc_ema(prices, 12) - calc_ema(prices, 26)
    # Signal: EMA 9 del MACD (aproximado)
    signal = macd * 0.9
    return macd, signal

def calc_bollinger(prices, period=20):
    if len(prices) < period:
        return None, None, None
    window = prices[-period:]
    mid = sum(window) / period
    std = math.sqrt(sum((x - mid)**2 for x in window) / period)
    return mid - 2*std, mid, mid + 2*std

def detect_candle_pattern(prices):
    """Detecta patrones de velas simples."""
    if len(prices) < 4:
        return None
    # Últimas 3 velas (simuladas como diferencias)
    c1 = prices[-3] - prices[-4]
    c2 = prices[-2] - prices[-3]
    c3 = prices[-1] - prices[-2]
    # Martillo (reversal alcista): caída + caída + subida fuerte
    if c1 < 0 and c2 < 0 and c3 > abs(c1 + c2):
        return "MARTILLO"
    # Estrella fugaz (reversal bajista): subida + subida + bajada fuerte
    if c1 > 0 and c2 > 0 and c3 < -abs(c1 + c2):
        return "ESTRELLA_FUGAZ"
    # Tres velas alcistas
    if c1 > 0 and c2 > 0 and c3 > 0:
        return "TRES_ALCISTAS"
    # Tres velas bajistas
    if c1 < 0 and c2 < 0 and c3 < 0:
        return "TRES_BAJISTAS"
    return None

def get_market_condition(prices):
    """Evalúa condición del mercado: TENDENCIA_ALCISTA, TENDENCIA_BAJISTA, LATERAL."""
    if len(prices) < 30:
        return "INDEFINIDO"
    ema10 = calc_ema(prices, 10)
    ema20 = calc_ema(prices, 20)
    ema50 = calc_ema(prices[-50:] if len(prices) >= 50 else prices, min(50, len(prices)))
    precio = prices[-1]
    if ema10 > ema20 and precio > ema20:
        return "TENDENCIA_ALCISTA"
    elif ema10 < ema20 and precio < ema20:
        return "TENDENCIA_BAJISTA"
    return "LATERAL"

def get_signal(prices, sentiment=0):
    """
    Señal combinada: RSI + MACD + EMA + Bollinger + Patrón de velas.
    Devuelve: ("SUBIR"|"BAJAR"|"ESPERAR", confianza 0-5, detalle)
    """
    if len(prices) < 30:
        return "ESPERAR", 0, "Datos insuficientes"

    rsi         = calc_rsi(prices)
    macd, sig   = calc_macd(prices)
    ema10       = calc_ema(prices, 10)
    ema26       = calc_ema(prices, 26)
    bb_low, bb_mid, bb_high = calc_bollinger(prices)
    patron      = detect_candle_pattern(prices)
    precio      = prices[-1]
    cond        = get_market_condition(prices)

    bull_score = 0
    bear_score = 0
    detalle    = []

    # RSI
    if rsi < 30:
        bull_score += 1; detalle.append(f"RSI={rsi:.0f}↓sobreventa")
    elif rsi > 70:
        bear_score += 1; detalle.append(f"RSI={rsi:.0f}↑sobrecompra")

    # MACD
    if macd > 0:
        bull_score += 1; detalle.append("MACD+")
    elif macd < 0:
        bear_score += 1; detalle.append("MACD-")

    # EMA cruce
    if ema10 > ema26:
        bull_score += 1; detalle.append("EMA↑")
    else:
        bear_score += 1; detalle.append("EMA↓")

    # Bollinger
    if bb_low and precio < bb_low:
        bull_score += 1; detalle.append("BB_bajo")
    elif bb_high and precio > bb_high:
        bear_score += 1; detalle.append("BB_alto")

    # Patrón velas
    if patron in ("MARTILLO", "TRES_ALCISTAS"):
        bull_score += 1; detalle.append(patron)
    elif patron in ("ESTRELLA_FUGAZ", "TRES_BAJISTAS"):
        bear_score += 1; detalle.append(patron)

    # Sentimiento
    if sentiment > 0: bull_score += 0.5
    if sentiment < 0: bear_score += 0.5

    det_str = " · ".join(detalle)

    if bull_score >= 3 and bull_score > bear_score:
        return "SUBIR", int(bull_score), det_str
    if bear_score >= 3 and bear_score > bull_score:
        return "BAJAR", int(bear_score), det_str
    return "ESPERAR", 0, det_str

# ════════════════════════════════════════════════════
#   DETECCIÓN DE PRECIO EN PANTALLA (OCR)
# ════════════════════════════════════════════════════
class ScreenReader:
    def __init__(self):
        self.region = None  # (x, y, w, h) región del precio en pantalla

    def set_region(self, x, y, w, h):
        self.region = (x, y, w, h)

    def capture_price(self):
        """Captura la región y extrae el precio con OCR."""
        if not PIL_OK or not OCR_OK or not self.region:
            return None
        try:
            x, y, w, h = self.region
            screenshot = ImageGrab.grab(bbox=(x, y, x+w, y+h))
            # Preprocesamiento para mejorar OCR
            img = screenshot.convert("L")
            img = ImageEnhance.Contrast(img).enhance(3.0)
            img = img.filter(ImageFilter.SHARPEN)
            # Invertir si fondo oscuro
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            if avg < 128:
                img = img.point(lambda x: 255 - x)
            text = pytesseract.image_to_string(
                img, config="--psm 7 -c tessedit_char_whitelist=0123456789.")
            text = text.strip().replace(" ", "").replace(",", ".")
            # Extraer número
            num = ""
            for c in text:
                if c.isdigit() or c == ".":
                    num += c
            return float(num) if num else None
        except Exception:
            return None

    def capture_screenshot_region(self):
        """Devuelve imagen PIL de la región para preview."""
        if not PIL_OK or not self.region:
            return None
        try:
            x, y, w, h = self.region
            return ImageGrab.grab(bbox=(x, y, x+w, y+h))
        except Exception:
            return None

screen_reader = ScreenReader()

# ════════════════════════════════════════════════════
#   DATOS DE MERCADO
# ════════════════════════════════════════════════════
def sim_price(prev):
    return max(600.0, prev + (random.random() - 0.495) * 0.5)

def fetch_yfinance():
    if not YFINANCE_OK: return None
    try:
        data = yf.download("BTC-USD", period="1d", interval="1m", progress=False)
        if data.empty: return None
        closes = list(data["Close"].dropna().astype(float))
        mn, mx = min(closes), max(closes)
        rng = mx - mn or 1
        return [640 + (p - mn) / rng * 4 - 2 for p in closes[-120:]]
    except Exception:
        return None

NOTICIAS = [
    ("Crypto IDX en tendencia alcista fuerte",    1),
    ("Volumen alto, momentum positivo",           1),
    ("Ruptura de resistencia confirmada",         1),
    ("Presión bajista, velas rojas consecutivas",-1),
    ("Ruptura de soporte detectada",             -1),
    ("Mercado lateral sin tendencia clara",       0),
    ("Alta volatilidad, señales mixtas",          0),
    ("Rebote desde mínimos confirmado",           1),
    ("Divergencia bajista en RSI",               -1),
]

# ════════════════════════════════════════════════════
#   ESTRATEGIAS DISPONIBLES
# ════════════════════════════════════════════════════
ESTRATEGIAS = {
    "Conservadora":  {"min_confianza": 4, "desc": "Solo opera con 4-5/5 indicadores alineados"},
    "Equilibrada":   {"min_confianza": 3, "desc": "Opera con 3+ indicadores alineados"},
    "Agresiva":      {"min_confianza": 2, "desc": "Opera con 2+ indicadores (más ops, más riesgo)"},
}

# ════════════════════════════════════════════════════
#   BOT PRINCIPAL
# ════════════════════════════════════════════════════
class BinomoBot:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ ALPHA BOT v3 — Binomo · Auto-Detección")
        self.root.configure(bg=C["bg"])
        self.root.geometry("1180x760")
        self.root.minsize(1000, 680)

        # Estado
        self.running       = False
        self.prices        = []
        self.en_operacion  = False
        self.op_tipo       = None
        self.op_entrada    = None
        self.op_fin_time   = None
        self.operaciones   = []
        self.noticia       = NOTICIAS[0]
        self.cooldown_end  = 0
        self.mercado       = "INDEFINIDO"
        self.ultimo_precio_ocr = None

        # Config vars
        self.monto         = tk.IntVar(value=1000)
        self.duracion      = tk.IntVar(value=1)
        self.ganancia_pct  = tk.DoubleVar(value=82.0)
        self.saldo         = tk.DoubleVar(value=13000)
        self.estrategia    = tk.StringVar(value="Equilibrada")
        self.usar_ocr      = tk.BooleanVar(value=False)
        self.usar_real     = tk.BooleanVar(value=YFINANCE_OK)
        self.cooldown_seg  = tk.IntVar(value=10)
        self.max_ops_dia   = tk.IntVar(value=20)
        self.ops_hoy       = 0

        # Coords Binomo (de la captura del usuario)
        self.x_subir = tk.IntVar(value=1317)
        self.y_subir = tk.IntVar(value=461)
        self.x_bajar = tk.IntVar(value=1406)
        self.y_bajar = tk.IntVar(value=461)

        # OCR región
        self.ocr_x = tk.IntVar(value=1240)
        self.ocr_y = tk.IntVar(value=490)
        self.ocr_w = tk.IntVar(value=140)
        self.ocr_h = tk.IntVar(value=22)

        self._init_prices()
        self._build_ui()
        self._log("Bot listo. Configurá y presioná ▶ INICIAR.", "i")
        self._check_deps()
        self._ui_loop()

    def _init_prices(self):
        p = 641.0
        for _ in range(60):
            p = sim_price(p)
            self.prices.append(p)

    def _check_deps(self):
        if not PYAUTOGUI_OK:
            self._log("⚠ PyAutoGUI faltante → pip install pyautogui", "w")
        if not PIL_OK:
            self._log("⚠ Pillow faltante → pip install pillow", "w")
        if not OCR_OK:
            self._log("⚠ pytesseract faltante → pip install pytesseract", "w")
        if not YFINANCE_OK:
            self._log("⚠ yfinance faltante → pip install yfinance", "w")

    # ══════════════════════════════════════════════
    #   CONSTRUCCIÓN DE UI
    # ══════════════════════════════════════════════
    def _panel(self, parent, title, **kw):
        return tk.LabelFrame(parent, text=f"  {title}  ",
                             bg=C["panel"], fg=C["muted"],
                             font=("Courier", 8), relief="groove", bd=1, **kw)

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"], pady=7)
        hdr.pack(fill="x", padx=14)

        tk.Label(hdr, text="⚡ ALPHA BOT v3",
                 font=("Courier", 17, "bold"),
                 bg=C["bg"], fg=C["blue"]).pack(side="left")
        tk.Label(hdr, text="  Binomo · Crypto IDX · Auto-Detección",
                 font=("Courier", 9), bg=C["bg"], fg=C["muted"]).pack(side="left")

        self.status_lbl = tk.Label(hdr, text="● DETENIDO",
                                   font=("Courier", 9, "bold"),
                                   bg="#1a0505", fg=C["red"], padx=10, pady=3)
        self.status_lbl.pack(side="right", padx=6)

        bf = tk.Frame(hdr, bg=C["bg"])
        bf.pack(side="right")
        self.btn_start = tk.Button(bf, text="▶  INICIAR",
                                   command=self._start,
                                   bg=C["green"], fg="#fff",
                                   font=("Courier", 9, "bold"),
                                   relief="flat", padx=12, pady=5, cursor="hand2")
        self.btn_start.pack(side="left", padx=3)
        self.btn_stop = tk.Button(bf, text="■  DETENER",
                                  command=self._stop,
                                  bg="#1a0505", fg=C["muted"],
                                  font=("Courier", 9, "bold"),
                                  relief="flat", padx=12, pady=5,
                                  cursor="hand2", state="disabled")
        self.btn_stop.pack(side="left", padx=3)

        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")

        # Notebook (tabs)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",       background=C["bg"], borderwidth=0)
        style.configure("TNotebook.Tab",   background=C["panel"], foreground=C["muted"],
                        padding=[12, 5], font=("Courier", 8))
        style.map("TNotebook.Tab",
                  background=[("selected", C["bg"])],
                  foreground=[("selected", C["blue"])])

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=6, pady=4)

        tab_main   = tk.Frame(nb, bg=C["bg"])
        tab_config = tk.Frame(nb, bg=C["bg"])
        tab_ocr    = tk.Frame(nb, bg=C["bg"])

        nb.add(tab_main,   text="  📊 Trading  ")
        nb.add(tab_config, text="  ⚙  Config  ")
        nb.add(tab_ocr,    text="  🔍 Detección  ")

        self._build_tab_main(tab_main)
        self._build_tab_config(tab_config)
        self._build_tab_ocr(tab_ocr)

    # ── Tab principal ────────────────────────────────
    def _build_tab_main(self, p):
        left = tk.Frame(p, bg=C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(4,2), pady=4)
        right = tk.Frame(p, bg=C["bg"])
        right.configure(width=310)
        right.pack_propagate(False)
        right.pack(side="left", fill="y", padx=(2,4), pady=4)

        # Precio + mercado
        pf = self._panel(left, "PRECIO · CRYPTO IDX")
        pf.pack(fill="x", pady=(0,5))
        pr = tk.Frame(pf, bg=C["panel"])
        pr.pack(fill="x", padx=10, pady=8)
        self.precio_lbl = tk.Label(pr, text="641.0000",
                                   font=("Courier", 28, "bold"),
                                   bg=C["panel"], fg=C["green"])
        self.precio_lbl.pack(side="left")
        right_pr = tk.Frame(pr, bg=C["panel"])
        right_pr.pack(side="left", padx=14)
        self.cambio_lbl = tk.Label(right_pr, text="▲ 0.0000",
                                   font=("Courier", 11),
                                   bg=C["panel"], fg=C["green"])
        self.cambio_lbl.pack(anchor="w")
        self.mercado_lbl = tk.Label(right_pr, text="Mercado: —",
                                    font=("Courier", 9, "bold"),
                                    bg=C["panel"], fg=C["yellow"])
        self.mercado_lbl.pack(anchor="w")
        self.ocr_lbl = tk.Label(right_pr, text="OCR: desactivado",
                                font=("Courier", 8),
                                bg=C["panel"], fg=C["muted"])
        self.ocr_lbl.pack(anchor="w")

        # Chart
        cf = self._panel(left, "GRÁFICO")
        cf.pack(fill="x", pady=(0,5))
        self.canvas = tk.Canvas(cf, height=120, bg=C["dark"],
                                bd=0, highlightthickness=0)
        self.canvas.pack(fill="x", padx=4, pady=4)

        # Indicadores
        ind = self._panel(left, "INDICADORES TÉCNICOS")
        ind.pack(fill="x", pady=(0,5))
        igrid = tk.Frame(ind, bg=C["panel"])
        igrid.pack(fill="x", padx=10, pady=6)
        self.ind = {}
        specs = [
            ("RSI",      C["yellow"]), ("MACD",    C["blue"]),
            ("EMA 10",   C["blue"]),   ("EMA 26",  C["purple"]),
            ("Bollinger",C["muted"]),  ("Patrón",  C["text"]),
        ]
        for i, (name, color) in enumerate(specs):
            col = (i % 3) * 3
            row = (i // 3) * 2
            tk.Label(igrid, text=name, font=("Courier", 7),
                     bg=C["panel"], fg=C["muted"]).grid(
                row=row, column=col, sticky="w", padx=8)
            lbl = tk.Label(igrid, text="—",
                           font=("Courier", 10, "bold"),
                           bg=C["panel"], fg=color)
            lbl.grid(row=row+1, column=col, sticky="w", padx=8, pady=(0,4))
            self.ind[name] = lbl

        # Señal + confianza
        sf = tk.Frame(ind, bg=C["panel"])
        sf.pack(fill="x", padx=10, pady=(0,8))
        self.señal_lbl = tk.Label(sf, text="⏳  ESPERAR",
                                  font=("Courier", 15, "bold"),
                                  bg=C["panel"], fg=C["yellow"])
        self.señal_lbl.pack(side="left")
        self.conf_lbl = tk.Label(sf, text="",
                                 font=("Courier", 9),
                                 bg=C["panel"], fg=C["muted"])
        self.conf_lbl.pack(side="left", padx=12)
        self.detalle_lbl = tk.Label(ind, text="",
                                    font=("Courier", 8),
                                    bg=C["panel"], fg=C["muted"],
                                    wraplength=400, justify="left")
        self.detalle_lbl.pack(anchor="w", padx=10, pady=(0,6))

        # Historial
        hf = self._panel(left, "HISTORIAL")
        hf.pack(fill="both", expand=True)
        cols = ("Hora","Tipo","Monto","Entrada","Resultado","Ganancia")
        self.tree = ttk.Treeview(hf, columns=cols, show="headings",
                                 height=6, style="Dark.Treeview")
        ws = [70, 65, 75, 80, 90, 80]
        for col, w in zip(cols, ws):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

        style = ttk.Style()
        style.configure("Dark.Treeview",
                        background=C["dark"], foreground=C["text"],
                        fieldbackground=C["dark"], rowheight=21,
                        font=("Courier", 8))
        style.configure("Dark.Treeview.Heading",
                        background=C["panel"], foreground=C["muted"],
                        font=("Courier", 8))
        self.tree.tag_configure("win",  foreground=C["green"])
        self.tree.tag_configure("loss", foreground=C["red"])

        # ── Panel derecho ──
        # Operación activa
        of = self._panel(right, "OPERACIÓN ACTIVA")
        of.pack(fill="x", pady=(0,5))
        self.op_tipo_lbl  = tk.Label(of, text="— Esperando señal —",
                                     font=("Courier", 13, "bold"),
                                     bg=C["panel"], fg=C["muted"])
        self.op_tipo_lbl.pack(pady=(8,2))
        self.op_info_lbl  = tk.Label(of, text="",
                                     font=("Courier", 8),
                                     bg=C["panel"], fg=C["muted"])
        self.op_info_lbl.pack()
        self.op_timer_lbl = tk.Label(of, text="",
                                     font=("Courier", 12, "bold"),
                                     bg=C["panel"], fg=C["blue"])
        self.op_timer_lbl.pack(pady=(2,8))

        # Capital
        cap = self._panel(right, "CAPITAL")
        cap.pack(fill="x", pady=(0,5))
        self.saldo_lbl = tk.Label(cap, text="$13.000 ARS",
                                  font=("Courier", 16, "bold"),
                                  bg=C["panel"], fg=C["green"])
        self.saldo_lbl.pack(pady=6)
        self.stats_lbl = tk.Label(cap, text="",
                                  font=("Courier", 8),
                                  bg=C["panel"], fg=C["muted"])
        self.stats_lbl.pack(pady=(0,4))

        # Barra de rendimiento
        self.progress = ttk.Progressbar(cap, length=200, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0,8))

        # Sentimiento
        sf2 = self._panel(right, "SENTIMIENTO")
        sf2.pack(fill="x", pady=(0,5))
        self.not_lbl  = tk.Label(sf2, text="—", font=("Courier", 8),
                                 bg=C["panel"], fg=C["text"],
                                 wraplength=280, justify="left")
        self.not_lbl.pack(anchor="w", padx=10, pady=(6,2))
        self.sent_lbl = tk.Label(sf2, text="NEUTRAL",
                                 font=("Courier", 9, "bold"),
                                 bg=C["panel"], fg=C["yellow"])
        self.sent_lbl.pack(anchor="w", padx=10, pady=(0,8))

        # Log
        lf = self._panel(right, "LOG DEL SISTEMA")
        lf.pack(fill="both", expand=True)
        self.log_box = scrolledtext.ScrolledText(
            lf, height=12, bg=C["dark"], fg=C["muted"],
            font=("Courier", 8), relief="flat",
            state="disabled", insertbackground=C["text"])
        self.log_box.pack(fill="both", expand=True, padx=4, pady=4)
        for tag, col in [("s",C["success"]),("w",C["warn"]),
                         ("e",C["error"]), ("i",C["muted"]),
                         ("t","#1e3a5f")]:
            self.log_box.tag_config(tag, foreground=col)

    # ── Tab config ───────────────────────────────────
    def _build_tab_config(self, p):
        cols = tk.Frame(p, bg=C["bg"])
        cols.pack(fill="both", expand=True, padx=8, pady=8)

        # Col 1: Trading
        c1 = tk.Frame(cols, bg=C["bg"])
        c1.pack(side="left", fill="both", expand=True, padx=4)

        tf = self._panel(c1, "CONFIGURACIÓN DE TRADING")
        tf.pack(fill="x", pady=(0,8))

        fields = [
            ("Monto por op. (ARS)",  self.monto,       "int"),
            ("Duración op. (min)",   self.duracion,     "int"),
            ("% Ganancia Binomo",    self.ganancia_pct, "float"),
            ("Saldo inicial (ARS)",  self.saldo,        "float"),
            ("Cooldown entre ops (s)",self.cooldown_seg,"int"),
            ("Máx. ops por día",     self.max_ops_dia,  "int"),
        ]
        for label, var, _ in fields:
            r = tk.Frame(tf, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=4)
            tk.Label(r, text=label, font=("Courier", 8),
                     bg=C["panel"], fg=C["muted"],
                     width=24, anchor="w").pack(side="left")
            tk.Entry(r, textvariable=var, font=("Courier", 9),
                     bg="#0a1628", fg=C["text"], relief="flat",
                     bd=4, width=8,
                     insertbackground=C["text"]).pack(side="right")

        # Estrategia
        ef = self._panel(c1, "ESTRATEGIA")
        ef.pack(fill="x", pady=(0,8))
        for name, info in ESTRATEGIAS.items():
            r = tk.Frame(ef, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=3)
            tk.Radiobutton(r, text=name,
                           variable=self.estrategia, value=name,
                           font=("Courier", 9, "bold"),
                           bg=C["panel"], fg=C["text"],
                           selectcolor=C["panel"],
                           activebackground=C["panel"],
                           activeforeground=C["blue"],
                           cursor="hand2").pack(side="left")
            tk.Label(r, text=info["desc"], font=("Courier", 7),
                     bg=C["panel"], fg=C["muted"]).pack(side="left", padx=8)

        tk.Checkbutton(ef, text="Usar precios reales (yfinance)",
                       variable=self.usar_real,
                       bg=C["panel"], fg=C["muted"],
                       selectcolor=C["panel"],
                       font=("Courier", 8),
                       activebackground=C["panel"],
                       cursor="hand2").pack(anchor="w", padx=10, pady=6)

        # Col 2: Coordenadas
        c2 = tk.Frame(cols, bg=C["bg"])
        c2.pack(side="left", fill="both", expand=True, padx=4)

        cf2 = self._panel(c2, "COORDENADAS PYAUTOGUI")
        cf2.pack(fill="x", pady=(0,8))

        tk.Label(cf2,
                 text="Mové el mouse sobre cada botón en Binomo\ny usá 'Detectar' para obtener las coordenadas.",
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"],
                 justify="left").pack(anchor="w", padx=10, pady=(8,6))

        for label, xv, yv in [
            ("↑ SUBIR (verde)", self.x_subir, self.y_subir),
            ("↓ BAJAR (rojo)",  self.x_bajar, self.y_bajar),
        ]:
            r = tk.Frame(cf2, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=4)
            tk.Label(r, text=label, font=("Courier", 8, "bold"),
                     bg=C["panel"], fg=C["text"],
                     width=18, anchor="w").pack(side="left")
            tk.Label(r, text="X:", font=("Courier", 8),
                     bg=C["panel"], fg=C["muted"]).pack(side="left")
            tk.Entry(r, textvariable=xv, font=("Courier", 9),
                     bg="#0a1628", fg=C["text"], relief="flat",
                     bd=4, width=6,
                     insertbackground=C["text"]).pack(side="left", padx=2)
            tk.Label(r, text="Y:", font=("Courier", 8),
                     bg=C["panel"], fg=C["muted"]).pack(side="left")
            tk.Entry(r, textvariable=yv, font=("Courier", 9),
                     bg="#0a1628", fg=C["text"], relief="flat",
                     bd=4, width=6,
                     insertbackground=C["text"]).pack(side="left", padx=2)

        tk.Button(cf2, text="📍 Detectar posición SUBIR (5s)",
                  command=lambda: self._detectar("subir"),
                  bg="#0a1628", fg=C["green"],
                  font=("Courier", 8), relief="flat",
                  cursor="hand2", pady=4
                  ).pack(fill="x", padx=10, pady=3)
        tk.Button(cf2, text="📍 Detectar posición BAJAR (5s)",
                  command=lambda: self._detectar("bajar"),
                  bg="#0a1628", fg=C["red"],
                  font=("Courier", 8), relief="flat",
                  cursor="hand2", pady=4
                  ).pack(fill="x", padx=10, pady=(0,8))

        # Test
        tf2 = self._panel(c2, "TEST DE CLICKS")
        tf2.pack(fill="x", pady=(0,8))
        tk.Label(tf2,
                 text="Probá que los clicks lleguen al botón correcto.",
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"]
                 ).pack(anchor="w", padx=10, pady=(8,4))
        r = tk.Frame(tf2, bg=C["panel"])
        r.pack(fill="x", padx=10, pady=(0,8))
        tk.Button(r, text="Test ↑ SUBIR",
                  command=self._click_subir,
                  bg=C["green"], fg="#fff",
                  font=("Courier", 8), relief="flat",
                  cursor="hand2", pady=4).pack(side="left", expand=True, fill="x", padx=(0,4))
        tk.Button(r, text="Test ↓ BAJAR",
                  command=self._click_bajar,
                  bg=C["red"], fg="#fff",
                  font=("Courier", 8), relief="flat",
                  cursor="hand2", pady=4).pack(side="left", expand=True, fill="x")

    # ── Tab OCR / detección ──────────────────────────
    def _build_tab_ocr(self, p):
        main = tk.Frame(p, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=8, pady=8)

        left = tk.Frame(main, bg=C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0,4))
        right = tk.Frame(main, bg=C["bg"])
        right.configure(width=320)
        right.pack_propagate(False)
        right.pack(side="left", fill="y", padx=(4,0))

        # Explicación
        ef = self._panel(left, "DETECCIÓN AUTOMÁTICA DE PRECIO (OCR)")
        ef.pack(fill="x", pady=(0,8))
        tk.Label(ef,
                 text=(
                     "El bot puede leer el precio directamente de la pantalla de Binomo\n"
                     "usando OCR (reconocimiento óptico de caracteres).\n\n"
                     "Pasos:\n"
                     "  1. Abrí Binomo en el navegador\n"
                     "  2. Usá 'Detectar región del precio' para marcar dónde está el número\n"
                     "  3. Activá 'Usar OCR' y el bot leerá el precio en tiempo real\n\n"
                     "Si OCR no está disponible, el bot usa precios de yfinance o simulados."
                 ),
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"],
                 justify="left").pack(anchor="w", padx=12, pady=10)

        # Región OCR
        rf = self._panel(left, "REGIÓN DEL PRECIO EN PANTALLA")
        rf.pack(fill="x", pady=(0,8))

        for label, var in [
            ("X (píxel izquierdo)",  self.ocr_x),
            ("Y (píxel superior)",   self.ocr_y),
            ("Ancho (px)",           self.ocr_w),
            ("Alto (px)",            self.ocr_h),
        ]:
            r = tk.Frame(rf, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=3)
            tk.Label(r, text=label, font=("Courier", 8),
                     bg=C["panel"], fg=C["muted"],
                     width=22, anchor="w").pack(side="left")
            tk.Entry(r, textvariable=var, font=("Courier", 9),
                     bg="#0a1628", fg=C["text"], relief="flat",
                     bd=4, width=7,
                     insertbackground=C["text"]).pack(side="right")

        tk.Checkbutton(rf, text="Usar OCR para leer precio real de pantalla",
                       variable=self.usar_ocr,
                       bg=C["panel"], fg=C["text"],
                       selectcolor=C["panel"],
                       font=("Courier", 9, "bold"),
                       activebackground=C["panel"],
                       cursor="hand2").pack(anchor="w", padx=10, pady=8)

        r2 = tk.Frame(rf, bg=C["panel"])
        r2.pack(fill="x", padx=10, pady=(0,8))
        tk.Button(r2, text="📸 Capturar y testear OCR",
                  command=self._test_ocr,
                  bg=C["blue"], fg="#fff",
                  font=("Courier", 8), relief="flat",
                  cursor="hand2", pady=4).pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(r2, text="🎯 Detectar región con mouse",
                  command=self._detectar_region_ocr,
                  bg="#0a1628", fg=C["blue"],
                  font=("Courier", 8), relief="flat",
                  cursor="hand2", pady=4).pack(side="left", fill="x", expand=True)

        # Estado deps
        df = self._panel(right, "ESTADO DE DEPENDENCIAS")
        df.pack(fill="x", pady=(0,8))
        deps = [
            ("PyAutoGUI",   PYAUTOGUI_OK),
            ("Pillow/PIL",  PIL_OK),
            ("pytesseract", OCR_OK),
            ("OpenCV",      CV2_OK),
            ("yfinance",    YFINANCE_OK),
        ]
        for name, ok in deps:
            r = tk.Frame(df, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=3)
            tk.Label(r, text=name, font=("Courier", 9),
                     bg=C["panel"], fg=C["text"],
                     width=14, anchor="w").pack(side="left")
            tk.Label(r,
                     text="✅ instalado" if ok else "❌ faltante",
                     font=("Courier", 9, "bold"),
                     bg=C["panel"],
                     fg=C["green"] if ok else C["red"]).pack(side="right")

        tk.Label(df, text="Para instalar lo que falta:",
                 font=("Courier", 7), bg=C["panel"], fg=C["muted"]
                 ).pack(anchor="w", padx=10, pady=(8,2))
        tk.Label(df,
                 text="pip install pyautogui pillow\npytesseract opencv-python yfinance",
                 font=("Courier", 7), bg=C["panel"], fg=C["blue"]
                 ).pack(anchor="w", padx=10, pady=(0,8))

        # OCR preview
        pf = self._panel(right, "PREVIEW OCR")
        pf.pack(fill="x", pady=(0,8))
        self.ocr_result_lbl = tk.Label(pf,
                                       text="—",
                                       font=("Courier", 12, "bold"),
                                       bg=C["panel"], fg=C["blue"])
        self.ocr_result_lbl.pack(pady=8)
        self.ocr_status_lbl = tk.Label(pf, text="Sin captura",
                                       font=("Courier", 8),
                                       bg=C["panel"], fg=C["muted"])
        self.ocr_status_lbl.pack(pady=(0,8))

        # Notas Binomo
        nf = self._panel(right, "COORDENADAS BINOMO (REFERENCIA)")
        nf.pack(fill="x")
        tk.Label(nf,
                 text=(
                     "Según tu captura de pantalla:\n\n"
                     "  Precio en pantalla:\n"
                     "  ≈ x:1240  y:490  w:140  h:22\n\n"
                     "  Botón SUBIR (verde ↑):\n"
                     "  ≈ x:1416  y:378\n\n"
                     "  Botón BAJAR (rojo ↓):\n"
                     "  ≈ x:1516  y:378\n\n"
                     "  Ajustá según tu resolución."
                 ),
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"],
                 justify="left").pack(anchor="w", padx=12, pady=10)

    # ══════════════════════════════════════════════
    #   ACCIONES
    # ══════════════════════════════════════════════
    def _log(self, msg, tipo="i"):
        def _do():
            self.log_box.config(state="normal")
            ts = datetime.now().strftime("%H:%M:%S")
            self.log_box.insert("end", ts + "  ", "t")
            self.log_box.insert("end", msg + "\n", tipo)
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.root.after(0, _do)

    def _click_subir(self):
        if not PYAUTOGUI_OK:
            self._log("Simulado: clic ↑ SUBIR", "w"); return
        try:
            pyautogui.click(self.x_subir.get(), self.y_subir.get())
            self._log(f"🖱 Clic ↑ SUBIR ({self.x_subir.get()},{self.y_subir.get()})", "s")
        except Exception as e:
            self._log(f"Error clic SUBIR: {e}", "e")

    def _click_bajar(self):
        if not PYAUTOGUI_OK:
            self._log("Simulado: clic ↓ BAJAR", "w"); return
        try:
            pyautogui.click(self.x_bajar.get(), self.y_bajar.get())
            self._log(f"🖱 Clic ↓ BAJAR ({self.x_bajar.get()},{self.y_bajar.get()})", "w")
        except Exception as e:
            self._log(f"Error clic BAJAR: {e}", "e")

    def _detectar(self, which):
        def _run():
            if not PYAUTOGUI_OK:
                self._log("PyAutoGUI no instalado", "e"); return
            btn = "SUBIR" if which == "subir" else "BAJAR"
            self._log(f"Mové el mouse al botón {btn}... (5s)", "w")
            for i in range(5, 0, -1):
                x, y = pyautogui.position()
                self._log(f"  [{i}s] ({x}, {y})", "i")
                time.sleep(1)
            x, y = pyautogui.position()
            if which == "subir":
                self.root.after(0, lambda: self.x_subir.set(x))
                self.root.after(0, lambda: self.y_subir.set(y))
            else:
                self.root.after(0, lambda: self.x_bajar.set(x))
                self.root.after(0, lambda: self.y_bajar.set(y))
            self._log(f"✅ {btn} → ({x}, {y}) guardado", "s")
        threading.Thread(target=_run, daemon=True).start()

    def _detectar_region_ocr(self):
        def _run():
            if not PYAUTOGUI_OK:
                self._log("PyAutoGUI no instalado", "e"); return
            self._log("Mové el mouse a la esquina superior-izquierda del precio (5s)...", "w")
            time.sleep(5)
            x1, y1 = pyautogui.position()
            self._log(f"Punto 1: ({x1},{y1}). Ahora mové a la esquina inferior-derecha (5s)...", "w")
            time.sleep(5)
            x2, y2 = pyautogui.position()
            w = abs(x2 - x1)
            h = abs(y2 - y1)
            self.root.after(0, lambda: self.ocr_x.set(min(x1,x2)))
            self.root.after(0, lambda: self.ocr_y.set(min(y1,y2)))
            self.root.after(0, lambda: self.ocr_w.set(max(w, 20)))
            self.root.after(0, lambda: self.ocr_h.set(max(h, 10)))
            self._log(f"✅ Región OCR: x={min(x1,x2)} y={min(y1,y2)} w={w} h={h}", "s")
        threading.Thread(target=_run, daemon=True).start()

    def _test_ocr(self):
        def _run():
            screen_reader.set_region(
                self.ocr_x.get(), self.ocr_y.get(),
                self.ocr_w.get(), self.ocr_h.get())
            self._log("Capturando pantalla para OCR...", "i")
            result = screen_reader.capture_price()
            if result:
                self._log(f"✅ OCR leyó: {result}", "s")
                self.root.after(0, lambda: self.ocr_result_lbl.config(
                    text=f"{result:.4f}", fg=C["green"]))
                self.root.after(0, lambda: self.ocr_status_lbl.config(
                    text="OCR exitoso", fg=C["green"]))
            else:
                self._log("❌ OCR no pudo leer el precio. Ajustá la región.", "e")
                self.root.after(0, lambda: self.ocr_result_lbl.config(
                    text="—", fg=C["red"]))
                self.root.after(0, lambda: self.ocr_status_lbl.config(
                    text="Fallo OCR — ajustá región", fg=C["red"]))
        threading.Thread(target=_run, daemon=True).start()

    # ══════════════════════════════════════════════
    #   CONTROL BOT
    # ══════════════════════════════════════════════
    def _start(self):
        if self.running: return
        self.running    = True
        self.ops_hoy    = 0
        self.btn_start.config(state="disabled", bg="#1e293b", fg=C["muted"])
        self.btn_stop.config(state="normal", bg=C["red"], fg="#fff")
        self.status_lbl.config(text="● ACTIVO", bg="#052e16", fg=C["green"])
        self._log("🤖 Bot iniciado — analizando mercado...", "s")
        threading.Thread(target=self._loop, daemon=True).start()

    def _stop(self):
        self.running = False
        self.btn_start.config(state="normal", bg=C["green"], fg="#fff")
        self.btn_stop.config(state="disabled", bg="#1a0505", fg=C["muted"])
        self.status_lbl.config(text="● DETENIDO", bg="#1a0505", fg=C["red"])
        self._log("⏹ Bot detenido", "w")

    # ══════════════════════════════════════════════
    #   LOOP PRINCIPAL
    # ══════════════════════════════════════════════
    def _loop(self):
        tick       = 0
        last_yf    = 0
        last_noticia = 0

        while self.running:
            tick += 1
            now = time.time()

            # 1) Precio: OCR > yfinance > simulado
            ocr_price = None
            if self.usar_ocr.get() and PIL_OK and OCR_OK:
                screen_reader.set_region(
                    self.ocr_x.get(), self.ocr_y.get(),
                    self.ocr_w.get(), self.ocr_h.get())
                ocr_price = screen_reader.capture_price()
                if ocr_price:
                    self.ultimo_precio_ocr = ocr_price
                    self.prices.append(ocr_price)

            if not ocr_price:
                if self.usar_real.get() and YFINANCE_OK and (now - last_yf > 60):
                    real = fetch_yfinance()
                    if real:
                        self.prices = real
                        last_yf = now
                        self._log("📡 Precios yfinance actualizados", "i")
                self.prices.append(sim_price(self.prices[-1] if self.prices else 641.0))

            if len(self.prices) > 200:
                self.prices = self.prices[-200:]

            # 2) Noticia cada ~30s
            if now - last_noticia > 30:
                self.noticia = random.choice(NOTICIAS)
                last_noticia = now

            # 3) Si hay operación activa, esperar
            if self.en_operacion:
                remaining = self.op_fin_time - now if self.op_fin_time else 0
                if remaining > 0:
                    time.sleep(1)
                    continue
                # Resolver
                precio_cierre = self.prices[-1]
                if self.op_tipo == "SUBIR":
                    gano = precio_cierre > self.op_entrada
                else:
                    gano = precio_cierre < self.op_entrada
                monto   = self.monto.get()
                gpct    = self.ganancia_pct.get() / 100
                ganancia = monto * gpct if gano else -monto
                self.saldo.set(self.saldo.get() + ganancia)
                self.operaciones.append({
                    "hora":     datetime.now().strftime("%H:%M:%S"),
                    "tipo":     self.op_tipo,
                    "monto":    monto,
                    "entrada":  self.op_entrada,
                    "resultado":"✅ GANÓ" if gano else "❌ PERDIÓ",
                    "ganancia": ganancia,
                })
                self._log(
                    f"{'✅ GANÓ' if gano else '❌ PERDIÓ'} "
                    f"${ganancia:+,.0f}  "
                    f"entrada:{self.op_entrada:.4f} cierre:{precio_cierre:.4f}",
                    "s" if gano else "e")
                self.en_operacion = False
                self.op_tipo      = None
                self.op_entrada   = None
                self.cooldown_end = now + self.cooldown_seg.get()
                time.sleep(0.5)
                continue

            # 4) Cooldown
            if now < self.cooldown_end:
                time.sleep(1)
                continue

            # 5) Límite diario
            if self.ops_hoy >= self.max_ops_dia.get():
                if tick % 30 == 0:
                    self._log(f"⚠ Límite diario de {self.max_ops_dia.get()} ops alcanzado", "w")
                time.sleep(5)
                continue

            # 6) Saldo suficiente
            if self.saldo.get() < self.monto.get():
                if tick % 20 == 0:
                    self._log(f"⚠ Saldo ${self.saldo.get():,.0f} insuficiente", "w")
                time.sleep(2)
                continue

            # 7) Señal
            min_conf = ESTRATEGIAS[self.estrategia.get()]["min_confianza"]
            señal, conf, detalle = get_signal(self.prices, self.noticia[1])

            if señal != "ESPERAR" and conf >= min_conf:
                dur_seg         = self.duracion.get() * 60
                self.en_operacion = True
                self.op_tipo      = señal
                self.op_entrada   = self.prices[-1]
                self.op_fin_time  = now + dur_seg
                self.ops_hoy     += 1

                self._log(
                    f"{'📈' if señal=='SUBIR' else '📉'} {señal} "
                    f"@ {self.op_entrada:.4f}  conf:{conf}  "
                    f"${self.monto.get():,}  {self.duracion.get()}min  |  {detalle}",
                    "s" if señal == "SUBIR" else "w")

                if señal == "SUBIR":
                    self._click_subir()
                else:
                    self._click_bajar()

            time.sleep(1)

    # ══════════════════════════════════════════════
    #   UI LOOP
    # ══════════════════════════════════════════════
    def _ui_loop(self):
        try: self._update_ui()
        except Exception: pass
        self.root.after(700, self._ui_loop)

    def _update_ui(self):
        if not self.prices: return
        precio = self.prices[-1]
        prev   = self.prices[-2] if len(self.prices) > 1 else precio
        diff   = precio - prev
        col    = C["green"] if diff >= 0 else C["red"]

        self.precio_lbl.config(text=f"{precio:.4f}", fg=col)
        self.cambio_lbl.config(
            text=f"{'▲' if diff>=0 else '▼'} {abs(diff):.4f}", fg=col)

        # Mercado
        cond = get_market_condition(self.prices)
        mc = {"TENDENCIA_ALCISTA": C["green"],
              "TENDENCIA_BAJISTA": C["red"],
              "LATERAL":           C["yellow"],
              "INDEFINIDO":        C["muted"]}
        self.mercado_lbl.config(text=f"Mercado: {cond}", fg=mc.get(cond, C["muted"]))

        # OCR info
        if self.usar_ocr.get():
            ocr_txt = f"OCR: {self.ultimo_precio_ocr:.4f}" if self.ultimo_precio_ocr else "OCR: leyendo..."
            self.ocr_lbl.config(text=ocr_txt, fg=C["blue"])
        else:
            self.ocr_lbl.config(text="OCR: desactivado", fg=C["muted"])

        # Indicadores
        rsi       = calc_rsi(self.prices)
        macd, _   = calc_macd(self.prices)
        ema10     = calc_ema(self.prices, 10)
        ema26     = calc_ema(self.prices, 26)
        bb_l, bb_m, bb_h = calc_bollinger(self.prices)
        patron    = detect_candle_pattern(self.prices) or "—"

        self.ind["RSI"].config(
            text=f"{rsi:.1f}",
            fg=C["green"] if rsi < 35 else C["red"] if rsi > 65 else C["yellow"])
        self.ind["MACD"].config(
            text=f"{macd:.4f}",
            fg=C["green"] if macd > 0 else C["red"])
        self.ind["EMA 10"].config(text=f"{ema10:.4f}")
        self.ind["EMA 26"].config(text=f"{ema26:.4f}")
        bb_txt = f"{bb_l:.3f}–{bb_h:.3f}" if bb_l else "—"
        self.ind["Bollinger"].config(text=bb_txt)
        self.ind["Patrón"].config(
            text=patron,
            fg=C["green"] if patron in ("MARTILLO","TRES_ALCISTAS")
            else C["red"] if patron in ("ESTRELLA_FUGAZ","TRES_BAJISTAS")
            else C["muted"])

        # Señal
        min_conf = ESTRATEGIAS[self.estrategia.get()]["min_confianza"]
        señal, conf, detalle = get_signal(self.prices, self.noticia[1])
        sc = {"SUBIR": C["green"], "BAJAR": C["red"], "ESPERAR": C["yellow"]}
        si = {"SUBIR": "📈  SUBIR", "BAJAR": "📉  BAJAR", "ESPERAR": "⏳  ESPERAR"}
        self.señal_lbl.config(text=si[señal], fg=sc[señal])
        self.conf_lbl.config(
            text=f"Confianza: {conf}/{min_conf}",
            fg=C["green"] if conf >= min_conf else C["yellow"])
        self.detalle_lbl.config(text=detalle)

        # Operación activa
        if self.en_operacion and self.op_fin_time:
            remaining = max(0, self.op_fin_time - time.time())
            col2 = C["green"] if self.op_tipo == "SUBIR" else C["red"]
            self.op_tipo_lbl.config(
                text=f"{'📈 SUBIR' if self.op_tipo=='SUBIR' else '📉 BAJAR'}",
                fg=col2)
            self.op_info_lbl.config(
                text=f"Entrada: {self.op_entrada:.4f}  |  Monto: ${self.monto.get():,}",
                fg=C["muted"])
            mins, secs = divmod(int(remaining), 60)
            self.op_timer_lbl.config(text=f"⏱ {mins:02d}:{secs:02d}", fg=C["blue"])
        else:
            self.op_tipo_lbl.config(text="— Esperando señal —", fg=C["muted"])
            self.op_info_lbl.config(text="")
            cd = max(0, self.cooldown_end - time.time())
            self.op_timer_lbl.config(
                text=f"Cooldown: {cd:.0f}s" if cd > 0 else "",
                fg=C["muted"])

        # Saldo y stats
        sal = self.saldo.get()
        self.saldo_lbl.config(
            text=f"${sal:,.0f} ARS",
            fg=C["green"] if sal >= self.monto.get() else C["red"])
        ops = self.operaciones
        if ops:
            wins  = sum(1 for o in ops if o["ganancia"] > 0)
            total = sum(o["ganancia"] for o in ops)
            wr    = wins / len(ops) * 100
            self.stats_lbl.config(
                text=f"Ops hoy: {self.ops_hoy}/{self.max_ops_dia.get()}  "
                     f"WinRate: {wr:.0f}%  PnL: ${total:+,.0f}")
            pnl_pct = (total / self.monto.get()) * 10  # visual
            self.progress["value"] = max(0, min(100, 50 + pnl_pct))
        else:
            self.stats_lbl.config(text="Sin operaciones aún")

        # Sentimiento
        sc2 = C["green"] if self.noticia[1] > 0 else \
              C["red"]   if self.noticia[1] < 0 else C["yellow"]
        st2 = "POSITIVO" if self.noticia[1] > 0 else \
              "NEGATIVO" if self.noticia[1] < 0 else "NEUTRAL"
        self.not_lbl.config(text=self.noticia[0])
        self.sent_lbl.config(text=f"● {st2}", fg=sc2)

        # Historial
        for row in self.tree.get_children():
            self.tree.delete(row)
        for op in reversed(self.operaciones[-20:]):
            tag = "win" if op["ganancia"] > 0 else "loss"
            self.tree.insert("", 0, values=(
                op["hora"], op["tipo"],
                f"${op['monto']:,}",
                f"{op['entrada']:.4f}",
                op["resultado"],
                f"${op['ganancia']:+,.0f}"
            ), tags=(tag,))

        self._draw_chart()

    def _draw_chart(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width() or 500
        h = 120
        data = self.prices[-100:]
        if len(data) < 2: return
        mn, mx = min(data), max(data)
        rng = mx - mn or 0.01

        def yt(v): return h - 6 - ((v - mn) / rng) * (h - 12)

        # Bollinger visual
        bb_l, bb_m, bb_h2 = calc_bollinger(data)
        if bb_l:
            ybb_h = yt(bb_h2)
            ybb_l = yt(bb_l)
            self.canvas.create_rectangle(0, ybb_h, w, ybb_l,
                                         fill="#071e2e", outline="")

        # EMA lines
        ema10_pts, ema26_pts = [], []
        for i in range(10, len(data)):
            x = i / (len(data)-1) * w
            ema10_pts.extend([x, yt(calc_ema(data[:i+1], 10))])
            ema26_pts.extend([x, yt(calc_ema(data[:i+1], min(26,i+1)))])
        if len(ema10_pts) >= 4:
            self.canvas.create_line(ema10_pts, fill=C["blue"], width=1, smooth=True)
        if len(ema26_pts) >= 4:
            self.canvas.create_line(ema26_pts, fill=C["purple"], width=1, smooth=True)

        # Precio
        for i in range(len(data)-1):
            x1 = i / (len(data)-1) * w
            x2 = (i+1) / (len(data)-1) * w
            c  = C["green"] if data[i+1] >= data[i] else C["red"]
            self.canvas.create_line(x1, yt(data[i]), x2, yt(data[i+1]),
                                    fill=c, width=1.8)

        # Línea de entrada
        if self.en_operacion and self.op_entrada:
            ye  = yt(self.op_entrada)
            col = C["green"] if self.op_tipo == "SUBIR" else C["red"]
            self.canvas.create_line(0, ye, w, ye, fill=col, dash=(5,4), width=1)
            self.canvas.create_text(4, ye-6, text="ENTRADA",
                                    fill=col, font=("Courier", 6), anchor="w")

        # Precio actual
        self.canvas.create_text(w-4, yt(data[-1]),
                                text=f"{data[-1]:.4f}",
                                fill=C["text"], font=("Courier", 7), anchor="e")


# ══════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app  = BinomoBot(root)
    root.mainloop()
