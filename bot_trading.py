"""
╔══════════════════════════════════════════════════════════╗
║   ALPHA BOT v3 — Binomo · Detección de Pantalla         ║
║   RSI + MACD + EMA + Velas · OCR · PyAutoGUI            ║
║   Saldo OCR · Resultado OCR · Monto Autónomo            ║
╚══════════════════════════════════════════════════════════╝

Instalación:
    pip install pyautogui pillow pytesseract opencv-python yfinance numpy

Tesseract OCR:
    https://github.com/UB-Mannheim/tesseract/wiki  (Windows)
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading, time, random, math, os, re
from datetime import datetime

# ── Tesseract path ─────────────────────────────────────
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ── Imports opcionales ─────────────────────────────────
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

# ── Colores ────────────────────────────────────────────
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
    "gold":    "#fbbf24",
}

# ── Límites de monto ───────────────────────────────────
MONTO_MIN = 1_000
MONTO_MAX = 500_000

# ════════════════════════════════════════════════════════
#   INDICADORES TÉCNICOS
# ════════════════════════════════════════════════════════
def calc_rsi(prices, period=14):
    if len(prices) < period + 1: return 50.0
    gains = losses = 0.0
    for i in range(len(prices) - period, len(prices)):
        d = prices[i] - prices[i - 1]
        if d > 0: gains += d
        else:     losses += abs(d)
    rs = gains / (losses or 1e-9)
    return 100 - 100 / (1 + rs)

def calc_ema(prices, period):
    if len(prices) < period: return prices[-1] if prices else 0.0
    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for p in prices[period:]: ema = p * k + ema * (1 - k)
    return ema

def calc_macd(prices):
    if len(prices) < 26: return 0.0, 0.0
    macd = calc_ema(prices, 12) - calc_ema(prices, 26)
    return macd, macd * 0.9

def calc_bollinger(prices, period=20):
    if len(prices) < period: return None, None, None
    window = prices[-period:]
    mid = sum(window) / period
    std = math.sqrt(sum((x - mid)**2 for x in window) / period)
    return mid - 2*std, mid, mid + 2*std

def detect_candle_pattern(prices):
    if len(prices) < 4: return None
    c1 = prices[-3] - prices[-4]
    c2 = prices[-2] - prices[-3]
    c3 = prices[-1] - prices[-2]
    if c1 < 0 and c2 < 0 and c3 > abs(c1 + c2): return "MARTILLO"
    if c1 > 0 and c2 > 0 and c3 < -abs(c1 + c2): return "ESTRELLA_FUGAZ"
    if c1 > 0 and c2 > 0 and c3 > 0: return "TRES_ALCISTAS"
    if c1 < 0 and c2 < 0 and c3 < 0: return "TRES_BAJISTAS"
    return None

def get_market_condition(prices):
    if len(prices) < 30: return "INDEFINIDO"
    ema10 = calc_ema(prices, 10)
    ema20 = calc_ema(prices, 20)
    precio = prices[-1]
    if ema10 > ema20 and precio > ema20: return "TENDENCIA_ALCISTA"
    elif ema10 < ema20 and precio < ema20: return "TENDENCIA_BAJISTA"
    return "LATERAL"

def get_signal(prices, sentiment=0):
    if len(prices) < 30: return "ESPERAR", 0, "Datos insuficientes"
    rsi = calc_rsi(prices)
    macd, sig = calc_macd(prices)
    ema10 = calc_ema(prices, 10)
    ema26 = calc_ema(prices, 26)
    bb_low, bb_mid, bb_high = calc_bollinger(prices)
    patron = detect_candle_pattern(prices)
    precio = prices[-1]
    bull_score = bear_score = 0
    detalle = []
    if rsi < 30:   bull_score += 1; detalle.append(f"RSI={rsi:.0f}↓")
    elif rsi > 70: bear_score += 1; detalle.append(f"RSI={rsi:.0f}↑")
    if macd > 0:   bull_score += 1; detalle.append("MACD+")
    elif macd < 0: bear_score += 1; detalle.append("MACD-")
    if ema10 > ema26: bull_score += 1; detalle.append("EMA↑")
    else:             bear_score += 1; detalle.append("EMA↓")
    if bb_low and precio < bb_low:   bull_score += 1; detalle.append("BB_bajo")
    elif bb_high and precio > bb_high: bear_score += 1; detalle.append("BB_alto")
    if patron in ("MARTILLO", "TRES_ALCISTAS"):       bull_score += 1; detalle.append(patron)
    elif patron in ("ESTRELLA_FUGAZ", "TRES_BAJISTAS"): bear_score += 1; detalle.append(patron)
    if sentiment > 0: bull_score += 0.5
    if sentiment < 0: bear_score += 0.5
    det_str = " · ".join(detalle)
    if bull_score >= 3 and bull_score > bear_score: return "SUBIR", int(bull_score), det_str
    if bear_score >= 3 and bear_score > bull_score: return "BAJAR", int(bear_score), det_str
    return "ESPERAR", 0, det_str

# ════════════════════════════════════════════════════════
#   OCR GENÉRICO — lee cualquier número de una región
# ════════════════════════════════════════════════════════
def ocr_read_number(x, y, w, h, allow_dot=True, allow_comma=True, scale=3):
    """
    Captura la región (x,y,w,h) y extrae el primer número válido.
    Soporta formatos: 998.839,00  /  998,839.00  /  641.8673
    Devuelve float o None.
    """
    if not PIL_OK or not OCR_OK:
        return None
    try:
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        # Escalar para mejorar OCR
        new_w, new_h = img.width * scale, img.height * scale
        img = img.resize((new_w, new_h), Image.LANCZOS)
        # Escala de grises + contraste
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(4.0)
        img = img.filter(ImageFilter.SHARPEN)
        # Invertir si fondo oscuro
        pixels = list(img.getdata())
        if sum(pixels) / len(pixels) < 128:
            img = img.point(lambda v: 255 - v)
        # OCR
        whitelist = "0123456789"
        if allow_dot:   whitelist += "."
        if allow_comma: whitelist += ","
        cfg = f"--psm 7 -c tessedit_char_whitelist={whitelist}"
        raw = pytesseract.image_to_string(img, config=cfg).strip()
        # Normalizar: formato argentino "998.839,00" → 998839.00
        # Detectar si usa punto-de-miles y coma-decimal (ARS)
        # Patrón: dígitos + punto + 3dígitos + coma + 2dígitos
        m = re.search(r"(\d{1,3}(?:\.\d{3})+),(\d{2})", raw)
        if m:
            integer_part = m.group(1).replace(".", "")
            decimal_part = m.group(2)
            return float(f"{integer_part}.{decimal_part}")
        # Patrón simple: número con punto decimal
        m2 = re.search(r"\d+[\.,]\d+", raw)
        if m2:
            num_str = m2.group(0).replace(",", ".")
            return float(num_str)
        # Solo dígitos
        digits = re.sub(r"[^\d]", "", raw)
        if digits:
            return float(digits)
        return None
    except Exception:
        return None

# ════════════════════════════════════════════════════════
#   DATOS DE MERCADO
# ════════════════════════════════════════════════════════
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

ESTRATEGIAS = {
    "Conservadora": {"min_confianza": 4, "desc": "Solo opera con 4-5/5 indicadores alineados"},
    "Equilibrada":  {"min_confianza": 3, "desc": "Opera con 3+ indicadores alineados"},
    "Agresiva":     {"min_confianza": 2, "desc": "Opera con 2+ indicadores (más riesgo)"},
}

# ════════════════════════════════════════════════════════
#   GESTIÓN DE MONTO AUTÓNOMO
# ════════════════════════════════════════════════════════
def calcular_monto_autonomo(saldo, modo, pct_fijo=2.0, racha_wins=0, racha_losses=0):
    """
    Calcula el monto óptimo según el saldo y modo seleccionado.
    
    Modos:
      - "Fijo":        porcentaje fijo del saldo
      - "Kelly":       fracción de Kelly simplificada (winrate ~55%, payout 82%)
      - "Martingala":  duplica en pérdida (máx x4), resetea en ganancia — RIESGOSO
      - "Anti-Martingala": sube en ganancia, baja en pérdida
    """
    saldo = max(saldo, MONTO_MIN)

    if modo == "Fijo":
        monto = saldo * (pct_fijo / 100)

    elif modo == "Kelly":
        # Kelly = (p*b - q) / b  donde b=0.82 (payout), p=0.55, q=0.45
        p, b = 0.55, 0.82
        q = 1 - p
        kelly = (p * b - q) / b  # ≈ 0.122 = 12.2% del saldo
        kelly = max(0.01, min(kelly, 0.15))  # clamp 1-15%
        monto = saldo * kelly

    elif modo == "Martingala":
        base = saldo * (pct_fijo / 100)
        factor = min(2 ** racha_losses, 4)  # máximo x4
        monto = base * factor

    elif modo == "Anti-Martingala":
        base = saldo * (pct_fijo / 100)
        factor = min(1 + racha_wins * 0.5, 3)  # sube con wins, máx x3
        if racha_losses > 0:
            factor = max(0.5, 1 - racha_losses * 0.2)  # baja con losses
        monto = base * factor

    else:
        monto = saldo * (pct_fijo / 100)

    # Aplicar límites
    monto = max(MONTO_MIN, min(MONTO_MAX, round(monto / 100) * 100))
    return int(monto)

# ════════════════════════════════════════════════════════
#   BOT PRINCIPAL
# ════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════
#   SELECTOR VISUAL DE REGIÓN (tipo Recorte de Windows)
# ════════════════════════════════════════════════════════
class RegionSelector:
    """
    Abre una ventana semitransparente sobre toda la pantalla.
    El usuario arrastra para seleccionar una región rectangular.
    Al soltar devuelve (x, y, w, h) en coordenadas de pantalla.
    
    Uso:
        sel = RegionSelector(callback=mi_funcion, label="Saldo")
        # mi_funcion(x, y, w, h) se llama al confirmar
    """

    OVERLAY_ALPHA  = 0.35          # opacidad del fondo oscuro
    BORDER_COLOR   = "#00d4ff"     # cyan neón para el borde
    FILL_COLOR     = "#00d4ff"     # color del recuadro
    FILL_ALPHA_HEX = "22"          # transparencia del relleno (hex)
    FONT           = ("Segoe UI", 11)
    FONT_BIG       = ("Segoe UI", 14, "bold")

    def __init__(self, callback, label="región", preview_callback=None):
        self.callback         = callback
        self.label            = label
        self.preview_callback = preview_callback
        self.start_x = self.start_y = 0
        self.cur_x   = self.cur_y   = 0
        self.dragging = False
        self.rect_id  = None
        self.info_id  = None
        self.dims_id  = None
        self._build()

    def _build(self):
        # Capturar pantalla completa ANTES de crear la ventana
        if PIL_OK:
            self._screenshot = ImageGrab.grab()
        else:
            self._screenshot = None

        # Ventana fullscreen sin bordes
        self.win = tk.Toplevel()
        self.win.title("")
        self.win.overrideredirect(True)
        self.win.attributes("-fullscreen", True)
        self.win.attributes("-topmost", True)
        self.win.configure(cursor="crosshair")

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()

        # Canvas que cubre toda la pantalla
        self.cv = tk.Canvas(self.win, width=sw, height=sh,
                            highlightthickness=0, cursor="crosshair")
        self.cv.pack(fill="both", expand=True)

        # Fondo: screenshot + overlay oscuro
        if self._screenshot and PIL_OK:
            from PIL import ImageTk, ImageDraw
            # Oscurecer screenshot
            overlay = self._screenshot.copy().convert("RGBA")
            dark = Image.new("RGBA", overlay.size, (0, 0, 0, int(255 * self.OVERLAY_ALPHA)))
            overlay = Image.alpha_composite(overlay, dark).convert("RGB")
            self._bg_img = ImageTk.PhotoImage(overlay)
            self.cv.create_image(0, 0, anchor="nw", image=self._bg_img)
        else:
            self.cv.create_rectangle(0, 0, sw, sh, fill="#000000")
            # Semitransparente si Pillow no está
            self.win.attributes("-alpha", 0.75)

        # Texto de instrucciones (centro superior)
        cy = sh // 2
        self.cv.create_rectangle(sw//2 - 340, 18, sw//2 + 340, 80,
                                 fill="#071428", outline=self.BORDER_COLOR, width=2)
        self.cv.create_text(sw//2, 36, fill=self.BORDER_COLOR,
                            font=self.FONT_BIG,
                            text=f"✂  Seleccionando: {self.label.upper()}")
        self.cv.create_text(sw//2, 60, fill="#94a3b8",
                            font=self.FONT,
                            text="Arrastrá para marcar la región · ESC para cancelar · Enter para confirmar")

        # Eventos
        self.cv.bind("<ButtonPress-1>",   self._on_press)
        self.cv.bind("<B1-Motion>",       self._on_drag)
        self.cv.bind("<ButtonRelease-1>", self._on_release)
        self.win.bind("<Escape>",         lambda e: self._cancel())
        self.win.bind("<Return>",         lambda e: self._confirm())

        self.win.focus_force()

    # ── Dibujo ──────────────────────────────────────────
    def _redraw(self):
        if self.rect_id:  self.cv.delete(self.rect_id)
        if self.info_id:  self.cv.delete(self.info_id)
        if self.dims_id:  self.cv.delete(self.dims_id)

        x1, y1 = min(self.start_x, self.cur_x), min(self.start_y, self.cur_y)
        x2, y2 = max(self.start_x, self.cur_x), max(self.start_y, self.cur_y)
        w = x2 - x1
        h = y2 - y1

        if w < 2 or h < 2:
            return

        # Rectángulo exterior (borde)
        self.rect_id = self.cv.create_rectangle(
            x1, y1, x2, y2,
            outline=self.BORDER_COLOR, width=2,
            fill=""
        )

        # Líneas de la cruz en las esquinas (estilo recorte Windows)
        arm = 16
        corner_col = "#ffffff"
        for cx2, cy2, dx, dy in [(x1,y1,-1,-1),(x2,y1,1,-1),(x1,y2,-1,1),(x2,y2,1,1)]:
            self.cv.create_line(cx2, cy2, cx2+dx*arm, cy2, fill=corner_col, width=2)
            self.cv.create_line(cx2, cy2, cx2, cy2+dy*arm, fill=corner_col, width=2)

        # Dimensiones encima del rectángulo
        label_y = y1 - 22 if y1 > 30 else y2 + 8
        bg_x1, bg_y1 = x1, label_y - 4
        bg_x2, bg_y2 = x1 + 160, label_y + 18
        self.cv.create_rectangle(bg_x1, bg_y1, bg_x2, bg_y2,
                                 fill="#071428", outline=self.BORDER_COLOR, width=1)
        self.dims_id = self.cv.create_text(
            x1 + 8, label_y + 6,
            text=f"{w} × {h}  px",
            fill=self.BORDER_COLOR, font=("Courier", 10, "bold"), anchor="w"
        )

        # Coordenadas absolutas
        info_y = y2 + 26 if y2 + 50 < self.win.winfo_screenheight() else y1 - 40
        self.info_id = self.cv.create_text(
            x1, info_y,
            text=f"x:{x1}  y:{y1}  w:{w}  h:{h}",
            fill="#94a3b8", font=("Courier", 9), anchor="w"
        )

    # ── Eventos ─────────────────────────────────────────
    def _on_press(self, e):
        self.start_x, self.start_y = e.x, e.y
        self.cur_x,   self.cur_y   = e.x, e.y
        self.dragging = True

    def _on_drag(self, e):
        self.cur_x, self.cur_y = e.x, e.y
        self._redraw()

    def _on_release(self, e):
        self.cur_x, self.cur_y = e.x, e.y
        self.dragging = False
        self._redraw()
        # Mostrar botones de confirmar / rehacer
        self._show_action_buttons()

    def _show_action_buttons(self):
        """Muestra botones Confirmar y Rehacer después de soltar el mouse."""
        x1 = min(self.start_x, self.cur_x)
        x2 = max(self.start_x, self.cur_x)
        y2 = max(self.start_y, self.cur_y)
        bw = self.win.winfo_screenwidth()
        bh = self.win.winfo_screenheight()

        # Posición de los botones: debajo del rectángulo o arriba si no hay espacio
        by = y2 + 36 if y2 + 80 < bh else min(self.start_y, self.cur_y) - 56
        bx = min(x2 + 10, bw - 320)

        # Fondo de botones
        self.cv.create_rectangle(bx - 8, by - 8, bx + 310, by + 42,
                                 fill="#071428", outline=self.BORDER_COLOR, width=1)

        # Botón Confirmar
        btn_ok = tk.Button(self.win,
                           text="✔  CONFIRMAR",
                           bg="#22c55e", fg="#fff",
                           font=("Segoe UI", 10, "bold"),
                           relief="flat", padx=14, pady=6,
                           cursor="hand2",
                           command=self._confirm)
        btn_ok.place(x=bx, y=by)

        # Botón Rehacer
        btn_re = tk.Button(self.win,
                           text="↺  REHACER",
                           bg="#0ea5e9", fg="#fff",
                           font=("Segoe UI", 10, "bold"),
                           relief="flat", padx=14, pady=6,
                           cursor="hand2",
                           command=self._restart)
        btn_re.place(x=bx + 164, y=by)

        # Preview OCR en tiempo real si hay callback
        if self.preview_callback and PIL_OK:
            threading.Thread(target=self._run_preview, daemon=True).start()

    def _run_preview(self):
        """Llama al callback de preview con la región seleccionada."""
        x1 = min(self.start_x, self.cur_x)
        y1 = min(self.start_y, self.cur_y)
        w  = abs(self.cur_x - self.start_x)
        h  = abs(self.cur_y - self.start_y)
        if w > 4 and h > 4:
            try:
                self.preview_callback(x1, y1, w, h)
            except Exception:
                pass

    # ── Acciones ────────────────────────────────────────
    def _confirm(self):
        x1 = min(self.start_x, self.cur_x)
        y1 = min(self.start_y, self.cur_y)
        w  = abs(self.cur_x - self.start_x)
        h  = abs(self.cur_y - self.start_y)
        self.win.destroy()
        if w > 4 and h > 4 and self.callback:
            self.callback(x1, y1, w, h)

    def _restart(self):
        """Limpia la selección para que el usuario vuelva a arrastrar."""
        self.start_x = self.start_y = 0
        self.cur_x   = self.cur_y   = 0
        if self.rect_id: self.cv.delete(self.rect_id)
        if self.info_id: self.cv.delete(self.info_id)
        if self.dims_id: self.cv.delete(self.dims_id)
        # Destruir botones
        for w in self.win.winfo_children():
            if isinstance(w, tk.Button):
                w.destroy()

    def _cancel(self):
        self.win.destroy()


def abrir_selector(x_var, y_var, w_var, h_var, label,
                   on_confirm=None, preview_cb=None):
    """
    Función helper: oculta la ventana principal, abre el selector,
    y al confirmar guarda las variables y llama on_confirm.
    """
    def callback(x, y, w, h):
        x_var.set(x)
        y_var.set(y)
        w_var.set(w)
        h_var.set(h)
        if on_confirm:
            on_confirm(x, y, w, h)

    RegionSelector(callback=callback, label=label, preview_callback=preview_cb)


class BinomoBot:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ ALPHA BOT v4 — Binomo · Saldo OCR · Monto Autónomo")
        self.root.configure(bg=C["bg"])
        self.root.geometry("1220x800")
        self.root.minsize(1060, 700)

        # Estado
        self.running          = False
        self.prices           = []
        self.en_operacion     = False
        self.op_tipo          = None
        self.op_entrada       = None
        self.op_fin_time      = None
        self.operaciones      = []
        self.noticia          = NOTICIAS[0]
        self.cooldown_end     = 0
        self.ultimo_precio_ocr  = None
        self.ultimo_saldo_ocr   = None   # ← NUEVO: saldo leído por OCR
        self.ultimo_resultado_ocr = None # ← NUEVO: resultado de operación por OCR
        self.racha_wins       = 0
        self.racha_losses     = 0
        self.ops_hoy          = 0

        # Config vars
        self.monto            = tk.IntVar(value=1000)
        self.monto_modo       = tk.StringVar(value="Fijo")
        self.monto_pct        = tk.DoubleVar(value=2.0)
        self.duracion         = tk.IntVar(value=1)
        self.ganancia_pct     = tk.DoubleVar(value=82.0)
        self.saldo            = tk.DoubleVar(value=13000)
        self.saldo_ocr_activo = tk.BooleanVar(value=True)   # ← leer saldo por OCR
        self.resultado_ocr_activo = tk.BooleanVar(value=True) # ← leer resultado por OCR
        self.estrategia       = tk.StringVar(value="Equilibrada")
        self.usar_ocr         = tk.BooleanVar(value=False)
        self.usar_real        = tk.BooleanVar(value=YFINANCE_OK)
        self.cooldown_seg     = tk.IntVar(value=10)
        self.max_ops_dia      = tk.IntVar(value=20)
        self.stop_loss_pct    = tk.DoubleVar(value=20.0)   # detener si pierde X% del saldo
        self.take_profit_pct  = tk.DoubleVar(value=50.0)   # detener si gana X% del saldo
        self.saldo_inicial_ref = 0.0  # referencia para stop/take

        # Coordenadas botones Binomo (desde tu captura)
        self.x_subir = tk.IntVar(value=1317)
        self.y_subir = tk.IntVar(value=461)
        self.x_bajar = tk.IntVar(value=1406)
        self.y_bajar = tk.IntVar(value=461)

        # OCR precio (región del precio en chart)
        self.ocr_x = tk.IntVar(value=1160)
        self.ocr_y = tk.IntVar(value=448)
        self.ocr_w = tk.IntVar(value=115)
        self.ocr_h = tk.IntVar(value=22)

        # ── OCR SALDO ──────────────────────────────────
        # Saldo en Binomo: esquina superior derecha "998.839,00 Arg$"
        # Posición aproximada en pantalla 1456x816
        self.saldo_ocr_x = tk.IntVar(value=990)
        self.saldo_ocr_y = tk.IntVar(value=138)
        self.saldo_ocr_w = tk.IntVar(value=155)
        self.saldo_ocr_h = tk.IntVar(value=24)

        # ── OCR RESULTADO OPERACIÓN ────────────────────
        # Popup resultado: "1 Crypto IDX  0,00 Arg$" — cerca del icono calendario
        # Posición aproximada: fila inferior izquierda
        self.res_ocr_x = tk.IntVar(value=75)
        self.res_ocr_y = tk.IntVar(value=658)
        self.res_ocr_w = tk.IntVar(value=220)
        self.res_ocr_h = tk.IntVar(value=32)

        self._init_prices()
        self._build_ui()
        self._log("Bot v4 listo. Configurá y presioná ▶ INICIAR.", "i")
        self._check_deps()
        self._ui_loop()

    def _init_prices(self):
        p = 641.0
        for _ in range(60):
            p = sim_price(p)
            self.prices.append(p)

    def _check_deps(self):
        if not PYAUTOGUI_OK: self._log("⚠ pip install pyautogui", "w")
        if not PIL_OK:       self._log("⚠ pip install pillow", "w")
        if not OCR_OK:       self._log("⚠ pip install pytesseract", "w")
        if not YFINANCE_OK:  self._log("⚠ pip install yfinance", "w")
        if not CV2_OK:       self._log("⚠ pip install opencv-python", "w")

    # ══════════════════════════════════════════════════
    #   LECTURA DE SALDO POR OCR
    # ══════════════════════════════════════════════════
    def _leer_saldo_ocr(self):
        """Lee el saldo actual de la pantalla de Binomo."""
        if not self.saldo_ocr_activo.get(): return None
        val = ocr_read_number(
            self.saldo_ocr_x.get(), self.saldo_ocr_y.get(),
            self.saldo_ocr_w.get(), self.saldo_ocr_h.get(),
            allow_dot=True, allow_comma=True
        )
        if val and val >= MONTO_MIN:
            self.ultimo_saldo_ocr = val
            return val
        return None

    # ══════════════════════════════════════════════════
    #   LECTURA DE RESULTADO DE OPERACIÓN POR OCR
    # ══════════════════════════════════════════════════
    def _leer_resultado_ocr(self):
        """
        Lee el popup de resultado de operación.
        Devuelve (ganancia_float, texto_raw) o None.
        El popup muestra: "1 Crypto IDX  0,00 Arg$" o "1 Crypto IDX  +821,82 Arg$"
        """
        if not self.resultado_ocr_activo.get(): return None
        val = ocr_read_number(
            self.res_ocr_x.get(), self.res_ocr_y.get(),
            self.res_ocr_w.get(), self.res_ocr_h.get(),
            allow_dot=True, allow_comma=True
        )
        if val is not None:
            self.ultimo_resultado_ocr = val
            return val
        return None

    # ══════════════════════════════════════════════════
    #   CÁLCULO DE MONTO AUTÓNOMO
    # ══════════════════════════════════════════════════
    def _calcular_monto(self):
        saldo = self.saldo.get()
        modo  = self.monto_modo.get()
        pct   = self.monto_pct.get()
        monto = calcular_monto_autonomo(saldo, modo, pct, self.racha_wins, self.racha_losses)
        self.monto.set(monto)
        return monto

    # ══════════════════════════════════════════════════
    #   UI
    # ══════════════════════════════════════════════════
    def _panel(self, parent, title, **kw):
        return tk.LabelFrame(parent, text=f"  {title}  ",
                             bg=C["panel"], fg=C["muted"],
                             font=("Courier", 8), relief="groove", bd=1, **kw)

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["bg"], pady=7)
        hdr.pack(fill="x", padx=14)
        tk.Label(hdr, text="⚡ ALPHA BOT v4",
                 font=("Courier", 17, "bold"), bg=C["bg"], fg=C["blue"]).pack(side="left")
        tk.Label(hdr, text="  Binomo · Crypto IDX · Saldo OCR · Monto Autónomo",
                 font=("Courier", 9), bg=C["bg"], fg=C["muted"]).pack(side="left")
        self.status_lbl = tk.Label(hdr, text="● DETENIDO",
                                   font=("Courier", 9, "bold"),
                                   bg="#1a0505", fg=C["red"], padx=10, pady=3)
        self.status_lbl.pack(side="right", padx=6)
        bf = tk.Frame(hdr, bg=C["bg"])
        bf.pack(side="right")
        self.btn_start = tk.Button(bf, text="▶  INICIAR", command=self._start,
                                   bg=C["green"], fg="#fff", font=("Courier", 9, "bold"),
                                   relief="flat", padx=12, pady=5, cursor="hand2")
        self.btn_start.pack(side="left", padx=3)
        self.btn_stop = tk.Button(bf, text="■  DETENER", command=self._stop,
                                  bg="#1a0505", fg=C["muted"], font=("Courier", 9, "bold"),
                                  relief="flat", padx=12, pady=5, cursor="hand2", state="disabled")
        self.btn_stop.pack(side="left", padx=3)

        tk.Frame(self.root, bg=C["border"], height=1).pack(fill="x")

        # Notebook
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=C["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=C["panel"], foreground=C["muted"],
                        padding=[12, 5], font=("Courier", 8))
        style.map("TNotebook.Tab",
                  background=[("selected", C["bg"])],
                  foreground=[("selected", C["blue"])])

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=6, pady=4)

        tab_main   = tk.Frame(nb, bg=C["bg"])
        tab_config = tk.Frame(nb, bg=C["bg"])
        tab_ocr    = tk.Frame(nb, bg=C["bg"])
        tab_money  = tk.Frame(nb, bg=C["bg"])

        nb.add(tab_main,   text="  📊 Trading  ")
        nb.add(tab_config, text="  ⚙  Config  ")
        nb.add(tab_ocr,    text="  🔍 Detección  ")
        nb.add(tab_money,  text="  💰 Gestión  ")

        self._build_tab_main(tab_main)
        self._build_tab_config(tab_config)
        self._build_tab_ocr(tab_ocr)
        self._build_tab_money(tab_money)

    # ── Tab principal ──────────────────────────────────
    def _build_tab_main(self, p):
        left = tk.Frame(p, bg=C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(4,2), pady=4)
        right = tk.Frame(p, bg=C["bg"])
        right.configure(width=320)
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
                                   font=("Courier", 11), bg=C["panel"], fg=C["green"])
        self.cambio_lbl.pack(anchor="w")
        self.mercado_lbl = tk.Label(right_pr, text="Mercado: —",
                                    font=("Courier", 9, "bold"),
                                    bg=C["panel"], fg=C["yellow"])
        self.mercado_lbl.pack(anchor="w")
        self.ocr_lbl = tk.Label(right_pr, text="OCR precio: desactivado",
                                font=("Courier", 8), bg=C["panel"], fg=C["muted"])
        self.ocr_lbl.pack(anchor="w")
        self.saldo_ocr_lbl = tk.Label(right_pr, text="OCR saldo: —",
                                      font=("Courier", 8), bg=C["panel"], fg=C["gold"])
        self.saldo_ocr_lbl.pack(anchor="w")

        # Chart
        cf = self._panel(left, "GRÁFICO")
        cf.pack(fill="x", pady=(0,5))
        self.canvas = tk.Canvas(cf, height=120, bg=C["dark"], bd=0, highlightthickness=0)
        self.canvas.pack(fill="x", padx=4, pady=4)

        # Indicadores
        ind = self._panel(left, "INDICADORES TÉCNICOS")
        ind.pack(fill="x", pady=(0,5))
        igrid = tk.Frame(ind, bg=C["panel"])
        igrid.pack(fill="x", padx=10, pady=6)
        self.ind = {}
        specs = [("RSI", C["yellow"]), ("MACD", C["blue"]),
                 ("EMA 10", C["blue"]), ("EMA 26", C["purple"]),
                 ("Bollinger", C["muted"]), ("Patrón", C["text"])]
        for i, (name, color) in enumerate(specs):
            col = (i % 3) * 3
            row = (i // 3) * 2
            tk.Label(igrid, text=name, font=("Courier", 7),
                     bg=C["panel"], fg=C["muted"]).grid(row=row, column=col, sticky="w", padx=8)
            lbl = tk.Label(igrid, text="—", font=("Courier", 10, "bold"),
                           bg=C["panel"], fg=color)
            lbl.grid(row=row+1, column=col, sticky="w", padx=8, pady=(0,4))
            self.ind[name] = lbl

        # Señal
        sf = tk.Frame(ind, bg=C["panel"])
        sf.pack(fill="x", padx=10, pady=(0,8))
        self.señal_lbl = tk.Label(sf, text="⏳  ESPERAR",
                                  font=("Courier", 15, "bold"),
                                  bg=C["panel"], fg=C["yellow"])
        self.señal_lbl.pack(side="left")
        self.conf_lbl = tk.Label(sf, text="", font=("Courier", 9),
                                 bg=C["panel"], fg=C["muted"])
        self.conf_lbl.pack(side="left", padx=12)
        self.detalle_lbl = tk.Label(ind, text="", font=("Courier", 8),
                                    bg=C["panel"], fg=C["muted"],
                                    wraplength=400, justify="left")
        self.detalle_lbl.pack(anchor="w", padx=10, pady=(0,6))

        # Historial
        hf = self._panel(left, "HISTORIAL")
        hf.pack(fill="both", expand=True)
        cols = ("Hora","Tipo","Monto","Entrada","Resultado","Ganancia")
        self.tree = ttk.Treeview(hf, columns=cols, show="headings", height=6, style="Dark.Treeview")
        ws = [70, 65, 80, 80, 90, 90]
        for col, w in zip(cols, ws):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)
        style2 = ttk.Style()
        style2.configure("Dark.Treeview", background=C["dark"], foreground=C["text"],
                         fieldbackground=C["dark"], rowheight=21, font=("Courier", 8))
        style2.configure("Dark.Treeview.Heading", background=C["panel"],
                         foreground=C["muted"], font=("Courier", 8))
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
        self.op_info_lbl  = tk.Label(of, text="", font=("Courier", 8),
                                     bg=C["panel"], fg=C["muted"])
        self.op_info_lbl.pack()
        self.op_timer_lbl = tk.Label(of, text="", font=("Courier", 12, "bold"),
                                     bg=C["panel"], fg=C["blue"])
        self.op_timer_lbl.pack(pady=(2,4))
        # Resultado OCR en vivo
        self.resultado_ocr_lbl = tk.Label(of, text="Resultado OCR: —",
                                          font=("Courier", 8), bg=C["panel"], fg=C["gold"])
        self.resultado_ocr_lbl.pack(pady=(0,8))

        # Capital + Monto autónomo
        cap = self._panel(right, "CAPITAL · MONTO AUTÓNOMO")
        cap.pack(fill="x", pady=(0,5))
        self.saldo_lbl = tk.Label(cap, text="$13.000 ARS",
                                  font=("Courier", 16, "bold"),
                                  bg=C["panel"], fg=C["green"])
        self.saldo_lbl.pack(pady=(6,2))
        self.saldo_ocr_panel_lbl = tk.Label(cap, text="OCR: —",
                                            font=("Courier", 9), bg=C["panel"], fg=C["gold"])
        self.saldo_ocr_panel_lbl.pack()

        # Monto próxima op
        mf = tk.Frame(cap, bg=C["panel"])
        mf.pack(fill="x", padx=10, pady=4)
        tk.Label(mf, text="Próximo monto:", font=("Courier", 8),
                 bg=C["panel"], fg=C["muted"]).pack(side="left")
        self.monto_calc_lbl = tk.Label(mf, text="$1.000",
                                       font=("Courier", 10, "bold"),
                                       bg=C["panel"], fg=C["yellow"])
        self.monto_calc_lbl.pack(side="right")

        # Racha
        rf = tk.Frame(cap, bg=C["panel"])
        rf.pack(fill="x", padx=10, pady=(0,4))
        tk.Label(rf, text="Racha:", font=("Courier", 8),
                 bg=C["panel"], fg=C["muted"]).pack(side="left")
        self.racha_lbl = tk.Label(rf, text="—",
                                  font=("Courier", 9, "bold"), bg=C["panel"], fg=C["muted"])
        self.racha_lbl.pack(side="right")

        self.stats_lbl = tk.Label(cap, text="", font=("Courier", 8),
                                  bg=C["panel"], fg=C["muted"])
        self.stats_lbl.pack(pady=(0,2))
        self.progress = ttk.Progressbar(cap, length=200, mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=(0,8))

        # Sentimiento
        sf2 = self._panel(right, "SENTIMIENTO")
        sf2.pack(fill="x", pady=(0,5))
        self.not_lbl = tk.Label(sf2, text="—", font=("Courier", 8),
                                bg=C["panel"], fg=C["text"], wraplength=290, justify="left")
        self.not_lbl.pack(anchor="w", padx=10, pady=(6,2))
        self.sent_lbl = tk.Label(sf2, text="NEUTRAL",
                                 font=("Courier", 9, "bold"), bg=C["panel"], fg=C["yellow"])
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
                         ("e",C["error"]),("i",C["muted"]),("t","#1e3a5f")]:
            self.log_box.tag_config(tag, foreground=col)

    # ── Tab config ─────────────────────────────────────
    def _build_tab_config(self, p):
        cols = tk.Frame(p, bg=C["bg"])
        cols.pack(fill="both", expand=True, padx=8, pady=8)
        c1 = tk.Frame(cols, bg=C["bg"])
        c1.pack(side="left", fill="both", expand=True, padx=4)
        tf = self._panel(c1, "CONFIGURACIÓN DE TRADING")
        tf.pack(fill="x", pady=(0,8))
        fields = [
            ("Duración op. (min)",     self.duracion,      "int"),
            ("% Ganancia Binomo",      self.ganancia_pct,  "float"),
            ("Saldo inicial (ARS)",    self.saldo,         "float"),
            ("Cooldown entre ops (s)", self.cooldown_seg,  "int"),
            ("Máx. ops por día",       self.max_ops_dia,   "int"),
        ]
        for label, var, _ in fields:
            r = tk.Frame(tf, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=4)
            tk.Label(r, text=label, font=("Courier", 8),
                     bg=C["panel"], fg=C["muted"], width=24, anchor="w").pack(side="left")
            tk.Entry(r, textvariable=var, font=("Courier", 9),
                     bg="#0a1628", fg=C["text"], relief="flat",
                     bd=4, width=8, insertbackground=C["text"]).pack(side="right")

        ef = self._panel(c1, "ESTRATEGIA DE SEÑAL")
        ef.pack(fill="x", pady=(0,8))
        for name, info in ESTRATEGIAS.items():
            r = tk.Frame(ef, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=3)
            tk.Radiobutton(r, text=name, variable=self.estrategia, value=name,
                           font=("Courier", 9, "bold"), bg=C["panel"], fg=C["text"],
                           selectcolor=C["panel"], activebackground=C["panel"],
                           activeforeground=C["blue"], cursor="hand2").pack(side="left")
            tk.Label(r, text=info["desc"], font=("Courier", 7),
                     bg=C["panel"], fg=C["muted"]).pack(side="left", padx=8)
        tk.Checkbutton(ef, text="Usar precios reales (yfinance)",
                       variable=self.usar_real, bg=C["panel"], fg=C["muted"],
                       selectcolor=C["panel"], font=("Courier", 8),
                       activebackground=C["panel"], cursor="hand2").pack(anchor="w", padx=10, pady=6)

        c2 = tk.Frame(cols, bg=C["bg"])
        c2.pack(side="left", fill="both", expand=True, padx=4)
        cf2 = self._panel(c2, "COORDENADAS PYAUTOGUI")
        cf2.pack(fill="x", pady=(0,8))
        tk.Label(cf2,
                 text="Mové el mouse sobre cada botón en Binomo\ny usá 'Detectar' para obtener las coordenadas.",
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"], justify="left"
                 ).pack(anchor="w", padx=10, pady=(8,6))
        for label, xv, yv in [
            ("↑ SUBIR (verde)", self.x_subir, self.y_subir),
            ("↓ BAJAR (rojo)",  self.x_bajar, self.y_bajar),
        ]:
            r = tk.Frame(cf2, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=4)
            tk.Label(r, text=label, font=("Courier", 8, "bold"),
                     bg=C["panel"], fg=C["text"], width=18, anchor="w").pack(side="left")
            tk.Label(r, text="X:", font=("Courier", 8), bg=C["panel"], fg=C["muted"]).pack(side="left")
            tk.Entry(r, textvariable=xv, font=("Courier", 9), bg="#0a1628",
                     fg=C["text"], relief="flat", bd=4, width=6,
                     insertbackground=C["text"]).pack(side="left", padx=2)
            tk.Label(r, text="Y:", font=("Courier", 8), bg=C["panel"], fg=C["muted"]).pack(side="left")
            tk.Entry(r, textvariable=yv, font=("Courier", 9), bg="#0a1628",
                     fg=C["text"], relief="flat", bd=4, width=6,
                     insertbackground=C["text"]).pack(side="left", padx=2)
        tk.Button(cf2, text="✂  Clic sobre botón SUBIR en Binomo",
                  command=lambda: self._detectar("subir"),
                  bg="#0a1628", fg=C["green"], font=("Courier", 8),
                  relief="flat", cursor="hand2", pady=4).pack(fill="x", padx=10, pady=3)
        tk.Button(cf2, text="✂  Clic sobre botón BAJAR en Binomo",
                  command=lambda: self._detectar("bajar"),
                  bg="#0a1628", fg=C["red"], font=("Courier", 8),
                  relief="flat", cursor="hand2", pady=4).pack(fill="x", padx=10, pady=(0,8))
        tf2 = self._panel(c2, "TEST DE CLICKS")
        tf2.pack(fill="x", pady=(0,8))
        r = tk.Frame(tf2, bg=C["panel"])
        r.pack(fill="x", padx=10, pady=8)
        tk.Button(r, text="Test ↑ SUBIR", command=self._click_subir,
                  bg=C["green"], fg="#fff", font=("Courier", 8),
                  relief="flat", cursor="hand2", pady=4).pack(side="left", expand=True, fill="x", padx=(0,4))
        tk.Button(r, text="Test ↓ BAJAR", command=self._click_bajar,
                  bg=C["red"], fg="#fff", font=("Courier", 8),
                  relief="flat", cursor="hand2", pady=4).pack(side="left", expand=True, fill="x")

    # ── Tab OCR ────────────────────────────────────────
    def _build_tab_ocr(self, p):
        main = tk.Frame(p, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=8, pady=8)
        left = tk.Frame(main, bg=C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0,4))
        right = tk.Frame(main, bg=C["bg"])
        right.configure(width=320)
        right.pack_propagate(False)
        right.pack(side="left", fill="y", padx=(4,0))

        # ── OCR PRECIO ──
        ef = self._panel(left, "OCR — PRECIO EN PANTALLA")
        ef.pack(fill="x", pady=(0,8))
        tk.Label(ef,
                 text="Lee el precio del gráfico de Binomo. Región del número grande en pantalla.",
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"], justify="left"
                 ).pack(anchor="w", padx=12, pady=(10,4))
        for label, var in [("X precio", self.ocr_x), ("Y precio", self.ocr_y),
                           ("Ancho", self.ocr_w), ("Alto", self.ocr_h)]:
            r = tk.Frame(ef, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=3)
            tk.Label(r, text=label, font=("Courier", 8), bg=C["panel"],
                     fg=C["muted"], width=16, anchor="w").pack(side="left")
            tk.Entry(r, textvariable=var, font=("Courier", 9), bg="#0a1628",
                     fg=C["text"], relief="flat", bd=4, width=7,
                     insertbackground=C["text"]).pack(side="right")
        tk.Checkbutton(ef, text="Usar OCR para leer precio del gráfico",
                       variable=self.usar_ocr, bg=C["panel"], fg=C["text"],
                       selectcolor=C["panel"], font=("Courier", 9, "bold"),
                       activebackground=C["panel"], cursor="hand2").pack(anchor="w", padx=10, pady=6)
        r2 = tk.Frame(ef, bg=C["panel"])
        r2.pack(fill="x", padx=10, pady=(0,8))
        tk.Button(r2, text="📸 Test OCR precio", command=self._test_ocr,
                  bg=C["blue"], fg="#fff", font=("Courier", 8), relief="flat",
                  cursor="hand2", pady=4).pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(r2, text="✂  Seleccionar región en pantalla", command=self._detectar_region_ocr,
                  bg="#0c2a40", fg=C["blue"], font=("Courier", 8, "bold"), relief="flat",
                  cursor="hand2", pady=4).pack(side="left", fill="x", expand=True)

        # ── OCR SALDO ──
        sf = self._panel(left, "OCR — SALDO DE CUENTA (esquina sup. derecha)")
        sf.pack(fill="x", pady=(0,8))
        tk.Label(sf,
                 text='Lee "998.839,00 Arg$" — región del saldo en Binomo.\n'
                      'Posición pre-cargada según tu captura de pantalla.',
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"], justify="left"
                 ).pack(anchor="w", padx=12, pady=(10,4))
        for label, var in [("X saldo", self.saldo_ocr_x), ("Y saldo", self.saldo_ocr_y),
                           ("Ancho",   self.saldo_ocr_w), ("Alto",    self.saldo_ocr_h)]:
            r = tk.Frame(sf, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=3)
            tk.Label(r, text=label, font=("Courier", 8), bg=C["panel"],
                     fg=C["muted"], width=16, anchor="w").pack(side="left")
            tk.Entry(r, textvariable=var, font=("Courier", 9), bg="#0a1628",
                     fg=C["text"], relief="flat", bd=4, width=7,
                     insertbackground=C["text"]).pack(side="right")
        tk.Checkbutton(sf, text="Actualizar saldo por OCR automáticamente",
                       variable=self.saldo_ocr_activo, bg=C["panel"], fg=C["text"],
                       selectcolor=C["panel"], font=("Courier", 9, "bold"),
                       activebackground=C["panel"], cursor="hand2").pack(anchor="w", padx=10, pady=4)
        r3 = tk.Frame(sf, bg=C["panel"])
        r3.pack(fill="x", padx=10, pady=(0,8))
        tk.Button(r3, text="📸 Test OCR saldo", command=self._test_ocr_saldo,
                  bg=C["gold"], fg="#000", font=("Courier", 8), relief="flat",
                  cursor="hand2", pady=4).pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(r3, text="✂  Seleccionar saldo en pantalla", command=self._detectar_region_saldo,
                  bg="#0a1628", fg=C["gold"], font=("Courier", 8), relief="flat",
                  cursor="hand2", pady=4).pack(side="left", fill="x", expand=True)

        # ── OCR RESULTADO OPERACIÓN ──
        rf2 = self._panel(left, "OCR — RESULTADO OPERACIÓN (popup inferior izq.)")
        rf2.pack(fill="x", pady=(0,8))
        tk.Label(rf2,
                 text='Lee el popup "1 Crypto IDX  0,00 Arg$" después de cada operación.\n'
                      'Aparece cerca del ícono de calendario (izquierda inferior).',
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"], justify="left"
                 ).pack(anchor="w", padx=12, pady=(10,4))
        for label, var in [("X resultado", self.res_ocr_x), ("Y resultado", self.res_ocr_y),
                           ("Ancho",       self.res_ocr_w), ("Alto",        self.res_ocr_h)]:
            r = tk.Frame(rf2, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=3)
            tk.Label(r, text=label, font=("Courier", 8), bg=C["panel"],
                     fg=C["muted"], width=16, anchor="w").pack(side="left")
            tk.Entry(r, textvariable=var, font=("Courier", 9), bg="#0a1628",
                     fg=C["text"], relief="flat", bd=4, width=7,
                     insertbackground=C["text"]).pack(side="right")
        tk.Checkbutton(rf2, text="Leer resultado de operación por OCR",
                       variable=self.resultado_ocr_activo, bg=C["panel"], fg=C["text"],
                       selectcolor=C["panel"], font=("Courier", 9, "bold"),
                       activebackground=C["panel"], cursor="hand2").pack(anchor="w", padx=10, pady=4)
        r4 = tk.Frame(rf2, bg=C["panel"])
        r4.pack(fill="x", padx=10, pady=(0,8))
        tk.Button(r4, text="📸 Test OCR resultado", command=self._test_ocr_resultado,
                  bg=C["purple"], fg="#fff", font=("Courier", 8), relief="flat",
                  cursor="hand2", pady=4).pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(r4, text="✂  Seleccionar resultado en pantalla", command=self._detectar_region_resultado,
                  bg="#0a1628", fg=C["purple"], font=("Courier", 8), relief="flat",
                  cursor="hand2", pady=4).pack(side="left", fill="x", expand=True)

        # Panel derecho — estado deps + preview
        df = self._panel(right, "ESTADO DE DEPENDENCIAS")
        df.pack(fill="x", pady=(0,8))
        for name, ok in [("PyAutoGUI", PYAUTOGUI_OK), ("Pillow/PIL", PIL_OK),
                         ("pytesseract", OCR_OK), ("OpenCV", CV2_OK), ("yfinance", YFINANCE_OK)]:
            r = tk.Frame(df, bg=C["panel"])
            r.pack(fill="x", padx=10, pady=3)
            tk.Label(r, text=name, font=("Courier", 9), bg=C["panel"],
                     fg=C["text"], width=14, anchor="w").pack(side="left")
            tk.Label(r, text="✅ OK" if ok else "❌ falta",
                     font=("Courier", 9, "bold"), bg=C["panel"],
                     fg=C["green"] if ok else C["red"]).pack(side="right")

        pf2 = self._panel(right, "PREVIEW OCR")
        pf2.pack(fill="x", pady=(0,8))
        self.ocr_result_lbl = tk.Label(pf2, text="—", font=("Courier", 12, "bold"),
                                       bg=C["panel"], fg=C["blue"])
        self.ocr_result_lbl.pack(pady=(8,2))
        self.ocr_saldo_result_lbl = tk.Label(pf2, text="Saldo OCR: —",
                                             font=("Courier", 10, "bold"),
                                             bg=C["panel"], fg=C["gold"])
        self.ocr_saldo_result_lbl.pack(pady=2)
        self.ocr_res_result_lbl = tk.Label(pf2, text="Resultado OCR: —",
                                           font=("Courier", 10, "bold"),
                                           bg=C["panel"], fg=C["purple"])
        self.ocr_res_result_lbl.pack(pady=(2,8))
        self.ocr_status_lbl = tk.Label(pf2, text="Sin captura",
                                       font=("Courier", 8), bg=C["panel"], fg=C["muted"])
        self.ocr_status_lbl.pack(pady=(0,8))

        nf = self._panel(right, "REFERENCIA COORDENADAS")
        nf.pack(fill="x")
        tk.Label(nf,
                 text=(
                     "De tu captura de pantalla:\n\n"
                     "  Saldo (sup. der.):\n"
                     "  x:990 y:138 w:155 h:24\n\n"
                     "  Resultado op (inf. izq.):\n"
                     "  x:75 y:658 w:220 h:32\n\n"
                     "  Precio gráfico:\n"
                     "  x:1160 y:448 w:115 h:22\n\n"
                     "  SUBIR: x:1317 y:461\n"
                     "  BAJAR: x:1406 y:461\n\n"
                     "  ⚠ Ajustá si tu resolución\n"
                     "  o zoom es diferente."
                 ),
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"],
                 justify="left").pack(anchor="w", padx=12, pady=10)

    # ── Tab gestión de dinero ──────────────────────────
    def _build_tab_money(self, p):
        main = tk.Frame(p, bg=C["bg"])
        main.pack(fill="both", expand=True, padx=12, pady=12)

        mf = self._panel(main, "MODO DE CÁLCULO DE MONTO")
        mf.pack(fill="x", pady=(0,10))

        tk.Label(mf,
                 text=(
                     "El bot calcula automáticamente cuánto apostar en cada operación\n"
                     "según el saldo actual. Monto mínimo: $1.000  Máximo: $500.000"
                 ),
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"], justify="left"
                 ).pack(anchor="w", padx=12, pady=(10,6))

        modos = [
            ("Fijo",          "Porcentaje fijo del saldo. Simple y seguro."),
            ("Kelly",         "Fracción de Kelly (≈12% del saldo). Optimiza crecimiento."),
            ("Martingala",    "Dobla el monto en cada pérdida (máx x4). RIESGOSO."),
            ("Anti-Martingala","Sube el monto con rachas ganadoras, baja con perdedoras."),
        ]
        for name, desc in modos:
            r = tk.Frame(mf, bg=C["panel"])
            r.pack(fill="x", padx=12, pady=4)
            tk.Radiobutton(r, text=name, variable=self.monto_modo, value=name,
                           font=("Courier", 10, "bold"), bg=C["panel"], fg=C["text"],
                           selectcolor=C["panel"], activebackground=C["panel"],
                           activeforeground=C["blue"], cursor="hand2").pack(side="left")
            tk.Label(r, text=desc, font=("Courier", 8),
                     bg=C["panel"], fg=C["muted"]).pack(side="left", padx=10)

        pf3 = tk.Frame(mf, bg=C["panel"])
        pf3.pack(fill="x", padx=12, pady=(6,10))
        tk.Label(pf3, text="% del saldo (para modo Fijo, base para otros):",
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"]).pack(side="left")
        tk.Entry(pf3, textvariable=self.monto_pct, font=("Courier", 10),
                 bg="#0a1628", fg=C["text"], relief="flat", bd=4, width=6,
                 insertbackground=C["text"]).pack(side="left", padx=8)
        tk.Label(pf3, text="%", font=("Courier", 8),
                 bg=C["panel"], fg=C["muted"]).pack(side="left")

        # Stop Loss / Take Profit
        sf3 = self._panel(main, "STOP LOSS · TAKE PROFIT DIARIO")
        sf3.pack(fill="x", pady=(0,10))
        tk.Label(sf3,
                 text="El bot se detiene automáticamente si se alcanzan estos umbrales\n"
                      "basados en el saldo inicial al arrancar cada sesión.",
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"], justify="left"
                 ).pack(anchor="w", padx=12, pady=(10,6))
        for label, var, col in [
            ("Stop Loss (pérdida máx. %)",    self.stop_loss_pct,    C["red"]),
            ("Take Profit (ganancia máx. %)", self.take_profit_pct,  C["green"]),
        ]:
            r = tk.Frame(sf3, bg=C["panel"])
            r.pack(fill="x", padx=12, pady=4)
            tk.Label(r, text=label, font=("Courier", 9), bg=C["panel"],
                     fg=col, width=32, anchor="w").pack(side="left")
            tk.Entry(r, textvariable=var, font=("Courier", 10),
                     bg="#0a1628", fg=C["text"], relief="flat", bd=4, width=6,
                     insertbackground=C["text"]).pack(side="left", padx=6)
            tk.Label(r, text="%", font=("Courier", 8),
                     bg=C["panel"], fg=C["muted"]).pack(side="left")
        tk.Label(sf3,
                 text=(
                     "Ejemplo: Stop Loss 20% → si el saldo cae 20% desde el inicio, el bot para.\n"
                     "Take Profit 50% → si el saldo sube 50% desde el inicio, el bot para."
                 ),
                 font=("Courier", 7), bg=C["panel"], fg=C["muted"], justify="left"
                 ).pack(anchor="w", padx=12, pady=(0,10))

        # Simulador
        sim = self._panel(main, "SIMULADOR DE MONTO")
        sim.pack(fill="x")
        tk.Label(sim,
                 text="Calculá cuánto apostará el bot con el saldo y modo actuales:",
                 font=("Courier", 8), bg=C["panel"], fg=C["muted"]
                 ).pack(anchor="w", padx=12, pady=(10,6))
        self.sim_result = tk.Label(sim, text="—",
                                   font=("Courier", 14, "bold"),
                                   bg=C["panel"], fg=C["yellow"])
        self.sim_result.pack(pady=4)
        tk.Button(sim, text="🧮 Calcular monto ahora",
                  command=self._simular_monto,
                  bg=C["yellow"], fg="#000",
                  font=("Courier", 9, "bold"), relief="flat",
                  cursor="hand2", pady=6).pack(fill="x", padx=12, pady=(4,12))

    def _simular_monto(self):
        m = calcular_monto_autonomo(
            self.saldo.get(), self.monto_modo.get(),
            self.monto_pct.get(), self.racha_wins, self.racha_losses)
        self.sim_result.config(
            text=f"${m:,} ARS",
            fg=C["yellow"] if m <= 50000 else C["red"])
        self._log(f"🧮 Monto calculado: ${m:,} ARS (modo {self.monto_modo.get()})", "i")

    # ══════════════════════════════════════════════════
    #   ACCIONES
    # ══════════════════════════════════════════════════
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

    # ── Selector visual (tipo Recorte de Windows) ──────
    def _abrir_selector_visual(self, x_var, y_var, w_var, h_var, label, on_done=None):
        """Oculta el bot, abre el selector de pantalla completa, restaura al confirmar."""
        def on_confirm(x, y, w, h):
            x_var.set(x); y_var.set(y)
            w_var.set(w); h_var.set(h)
            self._log(f"✅ [{label}] seleccionado: x={x} y={y} w={w} h={h}", "s")
            # Mostrar preview OCR inmediato
            if on_done:
                self.root.after(300, on_done)

        def preview_cb(x, y, w, h):
            """Preview OCR en tiempo real mientras el usuario confirma."""
            val = ocr_read_number(x, y, w, h)
            if val:
                self._log(f"👁 Preview OCR [{label}]: {val}", "i")

        # Ocultar ventana principal momentáneamente para captura limpia
        self.root.withdraw()
        self.root.after(180, lambda: _do_open())

        def _do_open():
            RegionSelector(callback=on_confirm, label=label, preview_callback=preview_cb)
            # Restaurar ventana principal cuando el selector se cierre
            self.root.after(400, self.root.deiconify)

    def _detectar_region_ocr(self):
        self._abrir_selector_visual(
            self.ocr_x, self.ocr_y, self.ocr_w, self.ocr_h,
            "Precio en gráfico",
            on_done=self._test_ocr
        )

    def _detectar_region_saldo(self):
        self._abrir_selector_visual(
            self.saldo_ocr_x, self.saldo_ocr_y, self.saldo_ocr_w, self.saldo_ocr_h,
            "Saldo de cuenta",
            on_done=self._test_ocr_saldo
        )

    def _detectar_region_resultado(self):
        self._abrir_selector_visual(
            self.res_ocr_x, self.res_ocr_y, self.res_ocr_w, self.res_ocr_h,
            "Resultado de operación",
            on_done=self._test_ocr_resultado
        )

    def _test_ocr(self):
        def _run():
            self._log("Capturando OCR precio...", "i")
            val = ocr_read_number(self.ocr_x.get(), self.ocr_y.get(),
                                  self.ocr_w.get(), self.ocr_h.get())
            if val:
                self._log(f"✅ OCR precio: {val:.4f}", "s")
                self.root.after(0, lambda: self.ocr_result_lbl.config(
                    text=f"Precio: {val:.4f}", fg=C["green"]))
                self.root.after(0, lambda: self.ocr_status_lbl.config(
                    text="OCR precio OK", fg=C["green"]))
            else:
                self._log("❌ OCR precio falló. Ajustá la región.", "e")
                self.root.after(0, lambda: self.ocr_status_lbl.config(
                    text="Fallo OCR precio", fg=C["red"]))
        threading.Thread(target=_run, daemon=True).start()

    def _test_ocr_saldo(self):
        def _run():
            self._log("Capturando OCR saldo...", "i")
            val = ocr_read_number(self.saldo_ocr_x.get(), self.saldo_ocr_y.get(),
                                  self.saldo_ocr_w.get(), self.saldo_ocr_h.get())
            if val:
                self._log(f"✅ OCR saldo: ${val:,.0f} ARS", "s")
                self.root.after(0, lambda: self.ocr_saldo_result_lbl.config(
                    text=f"Saldo OCR: ${val:,.0f}", fg=C["green"]))
                self.root.after(0, lambda: self.saldo.set(val))
            else:
                self._log("❌ OCR saldo falló. Ajustá la región.", "e")
                self.root.after(0, lambda: self.ocr_saldo_result_lbl.config(
                    text="Saldo OCR: fallo", fg=C["red"]))
        threading.Thread(target=_run, daemon=True).start()

    def _test_ocr_resultado(self):
        def _run():
            self._log("Capturando OCR resultado operación...", "i")
            val = ocr_read_number(self.res_ocr_x.get(), self.res_ocr_y.get(),
                                  self.res_ocr_w.get(), self.res_ocr_h.get())
            if val is not None:
                self._log(f"✅ OCR resultado: ${val:,.2f}", "s")
                self.root.after(0, lambda: self.ocr_res_result_lbl.config(
                    text=f"Resultado OCR: ${val:,.2f}", fg=C["green"]))
            else:
                self._log("❌ OCR resultado falló.", "e")
                self.root.after(0, lambda: self.ocr_res_result_lbl.config(
                    text="Resultado OCR: fallo", fg=C["red"]))
        threading.Thread(target=_run, daemon=True).start()

    # ══════════════════════════════════════════════════
    #   CONTROL
    # ══════════════════════════════════════════════════
    def _start(self):
        if self.running: return
        self.running  = True
        self.ops_hoy  = 0
        self.racha_wins = self.racha_losses = 0
        self.saldo_inicial_ref = self.saldo.get()
        self.btn_start.config(state="disabled", bg="#1e293b", fg=C["muted"])
        self.btn_stop.config(state="normal", bg=C["red"], fg="#fff")
        self.status_lbl.config(text="● ACTIVO", bg="#052e16", fg=C["green"])
        self._log("🤖 Bot v4 iniciado — analizando mercado...", "s")
        self._log(f"📊 Modo monto: {self.monto_modo.get()}  |  Saldo ref: ${self.saldo_inicial_ref:,.0f}", "i")
        threading.Thread(target=self._loop, daemon=True).start()

    def _stop(self):
        self.running = False
        self.btn_start.config(state="normal", bg=C["green"], fg="#fff")
        self.btn_stop.config(state="disabled", bg="#1a0505", fg=C["muted"])
        self.status_lbl.config(text="● DETENIDO", bg="#1a0505", fg=C["red"])
        self._log("⏹ Bot detenido", "w")

    # ══════════════════════════════════════════════════
    #   LOOP PRINCIPAL
    # ══════════════════════════════════════════════════
    def _loop(self):
        tick = 0
        last_yf = last_noticia = last_saldo_ocr = 0

        while self.running:
            tick += 1
            now = time.time()

            # 1) Precio
            ocr_price = None
            if self.usar_ocr.get() and PIL_OK and OCR_OK:
                ocr_price = ocr_read_number(
                    self.ocr_x.get(), self.ocr_y.get(),
                    self.ocr_w.get(), self.ocr_h.get())
                if ocr_price:
                    self.ultimo_precio_ocr = ocr_price
                    self.prices.append(ocr_price)
            if not ocr_price:
                if self.usar_real.get() and YFINANCE_OK and (now - last_yf > 60):
                    real = fetch_yfinance()
                    if real:
                        self.prices = real; last_yf = now
                        self._log("📡 yfinance actualizado", "i")
                self.prices.append(sim_price(self.prices[-1] if self.prices else 641.0))
            if len(self.prices) > 200:
                self.prices = self.prices[-200:]

            # 2) Saldo OCR cada 5s
            if now - last_saldo_ocr > 5 and PIL_OK and OCR_OK:
                saldo_leido = self._leer_saldo_ocr()
                if saldo_leido:
                    self.saldo.set(saldo_leido)
                    last_saldo_ocr = now

            # 3) Noticia
            if now - last_noticia > 30:
                self.noticia = random.choice(NOTICIAS)
                last_noticia = now

            # 4) Operación activa
            if self.en_operacion:
                remaining = self.op_fin_time - now if self.op_fin_time else 0
                if remaining > 0:
                    # Intentar leer resultado OCR mientras esperamos
                    if remaining < 5 and PIL_OK and OCR_OK:
                        self._leer_resultado_ocr()
                    time.sleep(1); continue

                # ── Resolver operación ──
                # Primero intentar leer saldo y resultado por OCR
                saldo_post = None
                resultado_ocr = None

                if PIL_OK and OCR_OK:
                    # Esperar 2s a que aparezca el popup de resultado
                    time.sleep(2)
                    resultado_ocr = self._leer_resultado_ocr()
                    saldo_post    = self._leer_saldo_ocr()

                monto  = self.monto.get()
                gpct   = self.ganancia_pct.get() / 100

                if saldo_post and saldo_post != self.saldo.get():
                    # Tenemos saldo real post-operación
                    ganancia = saldo_post - self.saldo.get()
                    gano = ganancia > 0
                    self.saldo.set(saldo_post)
                    self._log(f"💰 Saldo OCR post-op: ${saldo_post:,.0f}  Δ${ganancia:+,.0f}", "s" if gano else "e")
                elif resultado_ocr is not None:
                    # Tenemos el monto del popup (ganancia neta)
                    ganancia = resultado_ocr - monto  # si ganó, resultado > monto; si perdió, 0
                    gano = resultado_ocr > monto * 0.1  # ganó si recibió algo significativo
                    if not gano: ganancia = -monto
                    self.saldo.set(self.saldo.get() + ganancia)
                    self._log(f"📋 Resultado OCR: ${resultado_ocr:,.0f}  →  Δ${ganancia:+,.0f}", "s" if gano else "e")
                else:
                    # Fallback: comparar precio
                    precio_cierre = self.prices[-1]
                    gano = (precio_cierre > self.op_entrada) if self.op_tipo == "SUBIR" \
                           else (precio_cierre < self.op_entrada)
                    ganancia = monto * gpct if gano else -monto
                    self.saldo.set(self.saldo.get() + ganancia)

                # Actualizar racha
                if gano:
                    self.racha_wins  += 1
                    self.racha_losses = 0
                else:
                    self.racha_losses += 1
                    self.racha_wins   = 0

                self.operaciones.append({
                    "hora":      datetime.now().strftime("%H:%M:%S"),
                    "tipo":      self.op_tipo,
                    "monto":     monto,
                    "entrada":   self.op_entrada,
                    "resultado": "✅ GANÓ" if gano else "❌ PERDIÓ",
                    "ganancia":  ganancia,
                })
                self._log(
                    f"{'✅ GANÓ' if gano else '❌ PERDIÓ'}  "
                    f"${ganancia:+,.0f}  |  "
                    f"Saldo: ${self.saldo.get():,.0f}  |  "
                    f"Racha: {'+' if gano else '-'}{self.racha_wins if gano else self.racha_losses}",
                    "s" if gano else "e")
                self.en_operacion = False
                self.op_tipo      = None
                self.op_entrada   = None
                self.cooldown_end = now + self.cooldown_seg.get()
                time.sleep(0.5); continue

            # 5) Cooldown
            if now < self.cooldown_end:
                time.sleep(1); continue

            # 6) Stop Loss / Take Profit diario
            saldo_act = self.saldo.get()
            if self.saldo_inicial_ref > 0:
                cambio_pct = (saldo_act - self.saldo_inicial_ref) / self.saldo_inicial_ref * 100
                if cambio_pct <= -self.stop_loss_pct.get():
                    self._log(f"🛑 STOP LOSS activado: {cambio_pct:.1f}% — bot detenido", "e")
                    self.root.after(0, self._stop); break
                if cambio_pct >= self.take_profit_pct.get():
                    self._log(f"🏆 TAKE PROFIT activado: +{cambio_pct:.1f}% — bot detenido", "s")
                    self.root.after(0, self._stop); break

            # 7) Límite diario
            if self.ops_hoy >= self.max_ops_dia.get():
                if tick % 30 == 0:
                    self._log(f"⚠ Límite diario {self.max_ops_dia.get()} ops alcanzado", "w")
                time.sleep(5); continue

            # 8) Saldo mínimo
            monto_calculado = self._calcular_monto()
            if saldo_act < MONTO_MIN:
                if tick % 20 == 0:
                    self._log(f"⚠ Saldo ${saldo_act:,.0f} < mínimo ${MONTO_MIN:,}", "w")
                time.sleep(2); continue

            # 9) Señal
            min_conf = ESTRATEGIAS[self.estrategia.get()]["min_confianza"]
            señal, conf, detalle = get_signal(self.prices, self.noticia[1])

            if señal != "ESPERAR" and conf >= min_conf:
                dur_seg          = self.duracion.get() * 60
                self.en_operacion = True
                self.op_tipo     = señal
                self.op_entrada  = self.prices[-1]
                self.op_fin_time = now + dur_seg
                self.ops_hoy    += 1
                self._log(
                    f"{'📈' if señal=='SUBIR' else '📉'} {señal}  "
                    f"@ {self.op_entrada:.4f}  conf:{conf}  "
                    f"${monto_calculado:,}  {self.duracion.get()}min  [{self.monto_modo.get()}]  |  {detalle}",
                    "s" if señal == "SUBIR" else "w")
                if señal == "SUBIR": self._click_subir()
                else:                self._click_bajar()

            time.sleep(1)

    # ══════════════════════════════════════════════════
    #   UI LOOP
    # ══════════════════════════════════════════════════
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
        self.cambio_lbl.config(text=f"{'▲' if diff>=0 else '▼'} {abs(diff):.4f}", fg=col)
        cond = get_market_condition(self.prices)
        mc = {"TENDENCIA_ALCISTA":C["green"],"TENDENCIA_BAJISTA":C["red"],
              "LATERAL":C["yellow"],"INDEFINIDO":C["muted"]}
        self.mercado_lbl.config(text=f"Mercado: {cond}", fg=mc.get(cond, C["muted"]))

        if self.usar_ocr.get():
            self.ocr_lbl.config(
                text=f"OCR precio: {self.ultimo_precio_ocr:.4f}" if self.ultimo_precio_ocr else "OCR: leyendo...",
                fg=C["blue"])
        else:
            self.ocr_lbl.config(text="OCR precio: off", fg=C["muted"])

        # Saldo OCR label
        if self.ultimo_saldo_ocr:
            self.saldo_ocr_lbl.config(text=f"OCR saldo: ${self.ultimo_saldo_ocr:,.0f}", fg=C["gold"])
            self.saldo_ocr_panel_lbl.config(text=f"OCR: ${self.ultimo_saldo_ocr:,.0f}", fg=C["gold"])
        else:
            self.saldo_ocr_lbl.config(text="OCR saldo: —", fg=C["muted"])
            self.saldo_ocr_panel_lbl.config(text="OCR: —", fg=C["muted"])

        # Indicadores
        rsi = calc_rsi(self.prices)
        macd, _ = calc_macd(self.prices)
        ema10 = calc_ema(self.prices, 10)
        ema26 = calc_ema(self.prices, 26)
        bb_l, bb_m, bb_h = calc_bollinger(self.prices)
        patron = detect_candle_pattern(self.prices) or "—"
        self.ind["RSI"].config(text=f"{rsi:.1f}",
            fg=C["green"] if rsi < 35 else C["red"] if rsi > 65 else C["yellow"])
        self.ind["MACD"].config(text=f"{macd:.4f}", fg=C["green"] if macd > 0 else C["red"])
        self.ind["EMA 10"].config(text=f"{ema10:.4f}")
        self.ind["EMA 26"].config(text=f"{ema26:.4f}")
        self.ind["Bollinger"].config(text=f"{bb_l:.3f}–{bb_h:.3f}" if bb_l else "—")
        self.ind["Patrón"].config(text=patron,
            fg=C["green"] if patron in ("MARTILLO","TRES_ALCISTAS")
            else C["red"] if patron in ("ESTRELLA_FUGAZ","TRES_BAJISTAS") else C["muted"])

        # Señal
        min_conf = ESTRATEGIAS[self.estrategia.get()]["min_confianza"]
        señal, conf, detalle = get_signal(self.prices, self.noticia[1])
        sc = {"SUBIR":C["green"],"BAJAR":C["red"],"ESPERAR":C["yellow"]}
        si = {"SUBIR":"📈  SUBIR","BAJAR":"📉  BAJAR","ESPERAR":"⏳  ESPERAR"}
        self.señal_lbl.config(text=si[señal], fg=sc[señal])
        self.conf_lbl.config(text=f"Confianza: {conf}/{min_conf}",
            fg=C["green"] if conf >= min_conf else C["yellow"])
        self.detalle_lbl.config(text=detalle)

        # Monto calculado
        monto_calc = self._calcular_monto()
        self.monto_calc_lbl.config(text=f"${monto_calc:,}", fg=C["yellow"])

        # Racha
        if self.racha_wins > 0:
            self.racha_lbl.config(text=f"🔥 +{self.racha_wins} wins", fg=C["green"])
        elif self.racha_losses > 0:
            self.racha_lbl.config(text=f"❄ -{self.racha_losses} losses", fg=C["red"])
        else:
            self.racha_lbl.config(text="—", fg=C["muted"])

        # Operación activa
        if self.en_operacion and self.op_fin_time:
            remaining = max(0, self.op_fin_time - time.time())
            col2 = C["green"] if self.op_tipo == "SUBIR" else C["red"]
            self.op_tipo_lbl.config(
                text=f"{'📈 SUBIR' if self.op_tipo=='SUBIR' else '📉 BAJAR'}", fg=col2)
            self.op_info_lbl.config(
                text=f"Entrada: {self.op_entrada:.4f}  |  Monto: ${self.monto.get():,}", fg=C["muted"])
            mins, secs = divmod(int(remaining), 60)
            self.op_timer_lbl.config(text=f"⏱ {mins:02d}:{secs:02d}", fg=C["blue"])
            # Resultado OCR en vivo
            if self.ultimo_resultado_ocr is not None:
                self.resultado_ocr_lbl.config(
                    text=f"Resultado OCR: ${self.ultimo_resultado_ocr:,.0f}", fg=C["gold"])
            else:
                self.resultado_ocr_lbl.config(text="Resultado OCR: esperando...", fg=C["muted"])
        else:
            self.op_tipo_lbl.config(text="— Esperando señal —", fg=C["muted"])
            self.op_info_lbl.config(text="")
            cd = max(0, self.cooldown_end - time.time())
            self.op_timer_lbl.config(
                text=f"Cooldown: {cd:.0f}s" if cd > 0 else "", fg=C["muted"])
            self.resultado_ocr_lbl.config(text="Resultado OCR: —", fg=C["muted"])

        # Saldo
        sal = self.saldo.get()
        self.saldo_lbl.config(text=f"${sal:,.0f} ARS",
            fg=C["green"] if sal >= MONTO_MIN else C["red"])

        # Stats
        ops = self.operaciones
        if ops:
            wins  = sum(1 for o in ops if o["ganancia"] > 0)
            total = sum(o["ganancia"] for o in ops)
            wr    = wins / len(ops) * 100
            self.stats_lbl.config(
                text=f"Ops: {self.ops_hoy}/{self.max_ops_dia.get()}  WR:{wr:.0f}%  PnL:${total:+,.0f}")
            pnl_pct = (total / max(self.monto.get(),1)) * 10
            self.progress["value"] = max(0, min(100, 50 + pnl_pct))
        else:
            self.stats_lbl.config(text="Sin operaciones aún")

        # Sentimiento
        sc2 = C["green"] if self.noticia[1] > 0 else C["red"] if self.noticia[1] < 0 else C["yellow"]
        st2 = "POSITIVO" if self.noticia[1] > 0 else "NEGATIVO" if self.noticia[1] < 0 else "NEUTRAL"
        self.not_lbl.config(text=self.noticia[0])
        self.sent_lbl.config(text=f"● {st2}", fg=sc2)

        # Historial
        for row in self.tree.get_children(): self.tree.delete(row)
        for op in reversed(self.operaciones[-20:]):
            tag = "win" if op["ganancia"] > 0 else "loss"
            self.tree.insert("", 0, values=(
                op["hora"], op["tipo"], f"${op['monto']:,}",
                f"{op['entrada']:.4f}", op["resultado"], f"${op['ganancia']:+,.0f}"
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
        bb_l, bb_m, bb_h2 = calc_bollinger(data)
        if bb_l:
            self.canvas.create_rectangle(0, yt(bb_h2), w, yt(bb_l), fill="#071e2e", outline="")
        ema10_pts, ema26_pts = [], []
        for i in range(10, len(data)):
            x = i / (len(data)-1) * w
            ema10_pts.extend([x, yt(calc_ema(data[:i+1], 10))])
            ema26_pts.extend([x, yt(calc_ema(data[:i+1], min(26,i+1)))])
        if len(ema10_pts) >= 4:
            self.canvas.create_line(ema10_pts, fill=C["blue"], width=1, smooth=True)
        if len(ema26_pts) >= 4:
            self.canvas.create_line(ema26_pts, fill=C["purple"], width=1, smooth=True)
        for i in range(len(data)-1):
            x1 = i / (len(data)-1) * w
            x2 = (i+1) / (len(data)-1) * w
            c  = C["green"] if data[i+1] >= data[i] else C["red"]
            self.canvas.create_line(x1, yt(data[i]), x2, yt(data[i+1]), fill=c, width=1.8)
        if self.en_operacion and self.op_entrada:
            ye  = yt(self.op_entrada)
            col = C["green"] if self.op_tipo == "SUBIR" else C["red"]
            self.canvas.create_line(0, ye, w, ye, fill=col, dash=(5,4), width=1)
            self.canvas.create_text(4, ye-6, text="ENTRADA", fill=col, font=("Courier", 6), anchor="w")
        self.canvas.create_text(w-4, yt(data[-1]), text=f"{data[-1]:.4f}",
                                fill=C["text"], font=("Courier", 7), anchor="e")


# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app  = BinomoBot(root)
    root.mainloop()

