"""
╔══════════════════════════════════════════════════════════════════╗
║   ALPHA BOT v5 — Binomo · IA Avanzada · Heikin Ashi            ║
║   9 Indicadores OCR · Monto autónomo · Escritura de monto      ║
║   RSI·MACD·BB·Stochastic·ParSAR·ATR·ADX·CCI·AO·Momentum       ║
╚══════════════════════════════════════════════════════════════════╝

pip install pyautogui pillow pytesseract opencv-python yfinance numpy
Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading, time, random, math, os, re, json
from datetime import datetime
from collections import deque

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

try:
    import pyautogui; pyautogui.FAILSAFE=True; pyautogui.PAUSE=0.04
    PYAUTOGUI_OK=True
except: PYAUTOGUI_OK=False

try:
    from PIL import Image, ImageGrab, ImageEnhance, ImageFilter, ImageTk
    PIL_OK=True
except: PIL_OK=False

try:
    import pytesseract
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd=TESSERACT_PATH
    OCR_OK=True
except: OCR_OK=False

try:
    import cv2, numpy as np; CV2_OK=True
except: CV2_OK=False

try:
    import yfinance as yf; YFINANCE_OK=True
except: YFINANCE_OK=False

# ══ Colores ══════════════════════════════════════════════
C={
    "bg":"#040d1a","panel":"#071428","panel2":"#091830",
    "border":"#0e2a3a","border2":"#1a3a50",
    "text":"#e2e8f0","muted":"#475569","dim":"#2d3f55",
    "green":"#22c55e","red":"#ef4444","yellow":"#f59e0b",
    "blue":"#0ea5e9","purple":"#6366f1","cyan":"#06b6d4",
    "orange":"#f97316","pink":"#ec4899",
    "success":"#86efac","warn":"#fcd34d","error":"#fca5a5",
    "dark":"#020914","gold":"#fbbf24","teal":"#14b8a6",
}
MONTO_MIN=1_000; MONTO_MAX=500_000

# ══════════════════════════════════════════════════════════
#   INDICADORES TÉCNICOS AVANZADOS
# ══════════════════════════════════════════════════════════
def calc_sma(p,n):
    if len(p)<n: return p[-1] if p else 0.0
    return sum(p[-n:])/n

def calc_ema(p,n):
    if len(p)<n: return p[-1] if p else 0.0
    k=2/(n+1); e=sum(p[:n])/n
    for x in p[n:]: e=x*k+e*(1-k)
    return e

def calc_rsi(p,n=14):
    if len(p)<n+1: return 50.0
    g=l=0.0
    for i in range(len(p)-n,len(p)):
        d=p[i]-p[i-1]
        if d>0: g+=d
        else: l+=abs(d)
    rs=g/(l or 1e-9)
    return 100-100/(1+rs)

def calc_macd(p):
    if len(p)<26: return 0.0,0.0,0.0
    macd=calc_ema(p,12)-calc_ema(p,26)
    hist=[]
    for i in range(9,len(p)):
        m=calc_ema(p[:i+1],12)-calc_ema(p[:i+1],26)
        hist.append(m)
    sig=calc_ema(hist,9) if len(hist)>=9 else macd*0.9
    return macd,sig,macd-sig

def calc_bollinger(p,n=20,k=2):
    if len(p)<n: return None,None,None
    w=p[-n:]; mid=sum(w)/n
    std=math.sqrt(sum((x-mid)**2 for x in w)/n)
    return mid-k*std,mid,mid+k*std

def calc_stochastic(p,n=14,sm=3):
    if len(p)<n: return 50.0,50.0
    w=p[-n:]; lo,hi=min(w),max(w)
    k=((p[-1]-lo)/(hi-lo or 1e-9))*100
    ks=[((p[max(0,i-n+1):i+1][-1]-min(p[max(0,i-n+1):i+1]))
         /(max(p[max(0,i-n+1):i+1])-min(p[max(0,i-n+1):i+1]) or 1e-9))*100
        for i in range(max(0,len(p)-sm-n),len(p))]
    d=sum(ks[-sm:])/sm if len(ks)>=sm else k
    return k,d

def calc_atr(p,n=14):
    if len(p)<n+1: return 0.0
    trs=[abs(p[i]-p[i-1]) for i in range(len(p)-n,len(p))]
    return sum(trs)/n

def calc_cci(p,n=20):
    if len(p)<n: return 0.0
    w=p[-n:]; m=sum(w)/n
    md=sum(abs(x-m) for x in w)/n
    return (p[-1]-m)/(0.015*md or 1e-9)

def calc_adx(p,n=14):
    """Simplified ADX using price momentum proxy."""
    if len(p)<n*2: return 25.0
    ups=dn=0.0
    for i in range(len(p)-n,len(p)):
        diff=p[i]-p[i-1]
        if diff>0: ups+=diff
        else: dn+=abs(diff)
    di_plus=(ups/(ups+dn or 1e-9))*100
    di_minus=(dn/(ups+dn or 1e-9))*100
    dx=abs(di_plus-di_minus)/(di_plus+di_minus or 1e-9)*100
    return dx

def calc_awesome_oscillator(p):
    if len(p)<34: return 0.0
    m5=calc_sma(p,5); m34=calc_sma(p,34)
    return m5-m34

def calc_momentum(p,n=10):
    if len(p)<n+1: return 0.0
    return ((p[-1]-p[-n-1])/(p[-n-1] or 1e-9))*100

def calc_parabolic_sar(p,af_start=0.02,af_max=0.2):
    """Simplified Parabolic SAR."""
    if len(p)<10: return p[-1],True
    bull=True; sar=p[0]; ep=p[0]; af=af_start
    for i in range(1,len(p)):
        prev_sar=sar
        sar=sar+af*(ep-sar)
        if bull:
            if p[i]>ep: ep=p[i]; af=min(af+af_start,af_max)
            if p[i]<sar:
                bull=False; sar=ep; ep=p[i]; af=af_start
        else:
            if p[i]<ep: ep=p[i]; af=min(af+af_start,af_max)
            if p[i]>sar:
                bull=True; sar=ep; ep=p[i]; af=af_start
    return sar,bull

def heikin_ashi(opens,highs,lows,closes):
    """Convert OHLC to Heikin Ashi candles."""
    if not opens: return []
    ha=[]
    prev_c=closes[0]; prev_o=opens[0]
    for i in range(len(closes)):
        ha_c=(opens[i]+highs[i]+lows[i]+closes[i])/4
        ha_o=(prev_o+prev_c)/2
        ha_h=max(highs[i],ha_o,ha_c)
        ha_l=min(lows[i],ha_o,ha_c)
        ha.append((ha_o,ha_h,ha_l,ha_c))
        prev_o=ha_o; prev_c=ha_c
    return ha

# ── Heikin Ashi pattern analysis ──
def analyze_heikin_ashi(ha_candles):
    """
    Analiza patrones de velas Heikin Ashi.
    Retorna (señal, fuerza, descripcion)
    """
    if len(ha_candles)<5: return "NEUTRO",0,"Datos insuf."
    bull_count=sum(1 for c in ha_candles[-5:] if c[3]>c[0])
    bear_count=5-bull_count
    # Sombras (indicio de reversión)
    last=ha_candles[-1]
    body=abs(last[3]-last[0])
    upper_shadow=last[1]-max(last[0],last[3])
    lower_shadow=min(last[0],last[3])-last[2]
    if bull_count>=4:
        if upper_shadow>body*0.5: return "ALERTA_REVERSIÓN_BAJISTA",2,"HA: 4 alcistas + sombra sup"
        return "ALCISTA",bull_count,"HA: tendencia alcista fuerte"
    elif bear_count>=4:
        if lower_shadow>body*0.5: return "ALERTA_REVERSIÓN_ALCISTA",2,"HA: 4 bajistas + sombra inf"
        return "BAJISTA",bear_count,"HA: tendencia bajista fuerte"
    return "NEUTRO",0,"HA: sin tendencia clara"

# ── Motor de señal avanzado con ML-like scoring ──
def get_signal_advanced(prices,ha_candles=None,sentiment=0,
                        enabled_indicators=None,ocr_values=None):
    """
    Sistema de puntuación multi-indicador.
    Cada indicador aporta puntos ponderados.
    Retorna (dirección, score_total, max_score, detalle_dict)
    """
    if enabled_indicators is None:
        enabled_indicators={k:True for k in
            ["RSI","MACD","BB","Stoch","ParSAR","ATR","ADX","CCI","AO","Mom","HA"]}
    if len(prices)<30:
        return "ESPERAR",0,10,"Datos insuficientes"

    bull=0.0; bear=0.0; total_w=0.0
    det={}

    rsi=calc_rsi(prices)
    macd,sig,hist=calc_macd(prices)
    bb_l,bb_m,bb_h=calc_bollinger(prices)
    stk,std_=calc_stochastic(prices)
    atr=calc_atr(prices)
    cci=calc_cci(prices)
    adx=calc_adx(prices)
    ao=calc_awesome_oscillator(prices)
    mom=calc_momentum(prices)
    par_sar,sar_bull=calc_parabolic_sar(prices)
    ema10=calc_ema(prices,10); ema26=calc_ema(prices,26)
    precio=prices[-1]
    avg_price=sum(prices[-20:])/20
    volatility_ok=atr<avg_price*0.005  # ATR < 0.5% del precio = bajo ruido

    # ── RSI (peso 2.0) ──
    if enabled_indicators.get("RSI"):
        w=2.0; total_w+=w
        if rsi<25:   bull+=w; det["RSI"]=f"{rsi:.1f} ↓↓ SOBREVENTA"
        elif rsi<35: bull+=w*0.7; det["RSI"]=f"{rsi:.1f} ↓ bajo"
        elif rsi>75: bear+=w; det["RSI"]=f"{rsi:.1f} ↑↑ SOBRECOMPRA"
        elif rsi>65: bear+=w*0.7; det["RSI"]=f"{rsi:.1f} ↑ alto"
        else: det["RSI"]=f"{rsi:.1f} neutro"

    # ── MACD (peso 2.5) ──
    if enabled_indicators.get("MACD"):
        w=2.5; total_w+=w
        if macd>0 and hist>0:   bull+=w; det["MACD"]=f"MACD={macd:.5f} ↑"
        elif macd>0 and hist<=0: bull+=w*0.4; det["MACD"]=f"MACD+ débil"
        elif macd<0 and hist<0: bear+=w; det["MACD"]=f"MACD={macd:.5f} ↓"
        elif macd<0 and hist>=0: bear+=w*0.4; det["MACD"]=f"MACD- débil"
        else: det["MACD"]="MACD neutro"

    # ── Bollinger Bands (peso 1.5) ──
    if enabled_indicators.get("BB") and bb_l:
        w=1.5; total_w+=w
        bb_width=(bb_h-bb_l)/(bb_m or 1e-9)
        if precio<bb_l:          bull+=w; det["BB"]=f"< Lower({bb_l:.4f}) ↑"
        elif precio>bb_h:        bear+=w; det["BB"]=f"> Upper({bb_h:.4f}) ↓"
        elif precio<bb_m*0.9998: bull+=w*0.3; det["BB"]="centro-bajo"
        elif precio>bb_m*1.0002: bear+=w*0.3; det["BB"]="centro-alto"
        else: det["BB"]="BB centro"
        if bb_width<0.001: det["BB"]+=" [squeeze→break]"

    # ── Stochastic (peso 1.8) ──
    if enabled_indicators.get("Stoch"):
        w=1.8; total_w+=w
        if stk<20 and std_<20:   bull+=w; det["Stoch"]=f"K={stk:.0f} D={std_:.0f} ↑↑"
        elif stk<30:             bull+=w*0.5; det["Stoch"]=f"K={stk:.0f} bajo"
        elif stk>80 and std_>80: bear+=w; det["Stoch"]=f"K={stk:.0f} D={std_:.0f} ↓↓"
        elif stk>70:             bear+=w*0.5; det["Stoch"]=f"K={stk:.0f} alto"
        # Cruce K>D = alcista, K<D = bajista
        if stk>std_: bull+=w*0.2
        else: bear+=w*0.2
        det.setdefault("Stoch",f"K={stk:.0f}")

    # ── Parabolic SAR (peso 1.5) ──
    if enabled_indicators.get("ParSAR"):
        w=1.5; total_w+=w
        if sar_bull:  bull+=w; det["ParSAR"]=f"SAR↑ ({par_sar:.5f})"
        else:         bear+=w; det["ParSAR"]=f"SAR↓ ({par_sar:.5f})"

    # ── ATR filtro (peso 0.5) — solo filtra, no da dirección ──
    if enabled_indicators.get("ATR"):
        w=0.5; total_w+=w
        det["ATR"]=f"{atr:.6f} {'OK' if volatility_ok else 'ALTO'}"
        if not volatility_ok:
            bull*=0.85; bear*=0.85  # penalizar en alta volatilidad

    # ── ADX (peso 1.2) — fuerza de tendencia ──
    if enabled_indicators.get("ADX"):
        w=1.2; total_w+=w
        if adx>30:   det["ADX"]=f"{adx:.0f} tendencia fuerte"
        elif adx>20: det["ADX"]=f"{adx:.0f} tendencia moderada"
        else:        det["ADX"]=f"{adx:.0f} sin tendencia"
        # Amplifica señales si hay tendencia fuerte
        if adx>30:
            if bull>bear: bull+=w*0.5
            elif bear>bull: bear+=w*0.5

    # ── CCI (peso 1.3) ──
    if enabled_indicators.get("CCI"):
        w=1.3; total_w+=w
        if cci<-100:   bull+=w; det["CCI"]=f"{cci:.0f} ↑↑ sob.venta"
        elif cci<-50:  bull+=w*0.5; det["CCI"]=f"{cci:.0f} ↑ bajo"
        elif cci>100:  bear+=w; det["CCI"]=f"{cci:.0f} ↓↓ sob.compra"
        elif cci>50:   bear+=w*0.5; det["CCI"]=f"{cci:.0f} ↓ alto"
        else: det["CCI"]=f"{cci:.0f} neutro"

    # ── Awesome Oscillator (peso 1.0) ──
    if enabled_indicators.get("AO"):
        w=1.0; total_w+=w
        prev_ao=calc_awesome_oscillator(prices[:-1]) if len(prices)>34 else 0
        if ao>0 and ao>prev_ao:   bull+=w; det["AO"]=f"{ao:.6f} ↑"
        elif ao<0 and ao<prev_ao: bear+=w; det["AO"]=f"{ao:.6f} ↓"
        else: det["AO"]=f"{ao:.6f} ~"

    # ── Momentum (peso 1.0) ──
    if enabled_indicators.get("Mom"):
        w=1.0; total_w+=w
        if mom>0.5:    bull+=w; det["Mom"]=f"+{mom:.2f}% ↑"
        elif mom<-0.5: bear+=w; det["Mom"]=f"{mom:.2f}% ↓"
        else: det["Mom"]=f"{mom:.2f}% ~"

    # ── Heikin Ashi (peso 2.0) ──
    if enabled_indicators.get("HA") and ha_candles and len(ha_candles)>=5:
        w=2.0; total_w+=w
        ha_sig,ha_str,ha_desc=analyze_heikin_ashi(ha_candles)
        if ha_sig=="ALCISTA":             bull+=w*(ha_str/5)
        elif ha_sig=="BAJISTA":           bear+=w*(ha_str/5)
        elif ha_sig=="ALERTA_REVERSIÓN_ALCISTA": bull+=w*0.5
        elif ha_sig=="ALERTA_REVERSIÓN_BAJISTA": bear+=w*0.5
        det["HA"]=ha_desc

    # ── EMA cruce (peso 1.5) ──
    total_w+=1.5
    if ema10>ema26: bull+=1.5; det["EMA"]="10>26 ↑"
    else:           bear+=1.5; det["EMA"]="10<26 ↓"

    # ── Sentiment ──
    if sentiment>0: bull+=1.0
    elif sentiment<0: bear+=1.0

    # ── Consenso ──
    score=bull-bear
    pct=bull/(total_w or 1)*100

    if pct>=65 and bull>bear*1.4: return "SUBIR",bull,total_w,det
    if pct<=35 and bear>bull*1.4: return "BAJAR",bear,total_w,det
    return "ESPERAR",max(bull,bear),total_w,det

# ══════════════════════════════════════════════════════════
#   OCR
# ══════════════════════════════════════════════════════════
def ocr_read_number(x,y,w,h,scale=3):
    if not PIL_OK or not OCR_OK: return None
    try:
        img=ImageGrab.grab(bbox=(x,y,x+w,y+h))
        img=img.resize((img.width*scale,img.height*scale),Image.LANCZOS)
        img=img.convert("L")
        img=ImageEnhance.Contrast(img).enhance(4.5)
        img=img.filter(ImageFilter.SHARPEN)
        px=list(img.getdata())
        if sum(px)/len(px)<128: img=img.point(lambda v:255-v)
        cfg="--psm 7 -c tessedit_char_whitelist=0123456789.,"
        raw=pytesseract.image_to_string(img,config=cfg).strip()
        m=re.search(r"(\d{1,3}(?:\.\d{3})+),(\d{2})",raw)
        if m: return float(m.group(1).replace(".","") + "." + m.group(2))
        m2=re.search(r"\d+[\.,]\d+",raw)
        if m2: return float(m2.group(0).replace(",","."))
        d=re.sub(r"[^\d]","",raw)
        return float(d) if d else None
    except: return None

def ocr_pixel_color(x,y):
    """Lee color RGB de un pixel de pantalla."""
    if not PIL_OK: return None
    try:
        img=ImageGrab.grab(bbox=(x,y,x+1,y+1))
        return img.getpixel((0,0))
    except: return None

# ══════════════════════════════════════════════════════════
#   UTILIDADES
# ══════════════════════════════════════════════════════════
def sim_price(prev):
    return max(600.0,prev+(random.random()-0.495)*0.4)

def fetch_yfinance():
    if not YFINANCE_OK: return None
    try:
        d=yf.download("BTC-USD",period="1d",interval="1m",progress=False)
        if d.empty: return None
        c=list(d["Close"].dropna().astype(float))
        mn,mx=min(c),max(c); r=mx-mn or 1
        return [640+(p-mn)/r*4-2 for p in c[-150:]]
    except: return None

NOTICIAS=[
    ("Crypto IDX: ruptura alcista confirmada",1),
    ("Momentum positivo, volumen creciente",1),
    ("EMA cruzadas al alza — señal compra",1),
    ("Parabolic SAR girado alcista",1),
    ("Presión bajista intensa, velas rojas",-1),
    ("Ruptura de soporte — señal venta",-1),
    ("RSI en divergencia bajista",-1),
    ("Mercado lateral, baja volatilidad",0),
    ("Señales mixtas, esperar confirmación",0),
    ("ADX bajo — sin tendencia definida",0),
]

ESTRATEGIAS={
    "Conservadora":{"min_pct":68,"desc":"Opera solo con 68%+ consenso alcista/bajista"},
    "Equilibrada": {"min_pct":60,"desc":"Opera con 60%+ consenso"},
    "Agresiva":    {"min_pct":52,"desc":"Opera con 52%+ consenso (más riesgo)"},
}

def calcular_monto(saldo,modo,pct=2.0,rw=0,rl=0):
    saldo=max(saldo,MONTO_MIN)
    if   modo=="Fijo":        m=saldo*(pct/100)
    elif modo=="Kelly":       m=saldo*max(0.01,min(0.15,(0.55*0.82-0.45)/0.82))
    elif modo=="Martingala":  m=saldo*(pct/100)*min(2**rl,4)
    elif modo=="Anti-Mart.":
        f=min(1+rw*0.5,3) if rw>0 else max(0.5,1-rl*0.2)
        m=saldo*(pct/100)*f
    else: m=saldo*(pct/100)
    return int(max(MONTO_MIN,min(MONTO_MAX,round(m/100)*100)))

# ══════════════════════════════════════════════════════════
#   SELECTOR VISUAL (tipo Recorte de Windows)
# ══════════════════════════════════════════════════════════
class RegionSelector:
    BC="#00d4ff"
    def __init__(self,callback,label="región",preview_cb=None):
        self.cb=callback; self.label=label; self.pcb=preview_cb
        self.sx=self.sy=self.cx=self.cy=0
        self.rid=self.iid=self.did=None
        self._build()

    def _build(self):
        self._ss=ImageGrab.grab() if PIL_OK else None
        self.win=tk.Toplevel()
        self.win.title("")
        self.win.overrideredirect(True)
        self.win.attributes("-fullscreen",True)
        self.win.attributes("-topmost",True)
        self.win.configure(cursor="crosshair")
        sw=self.win.winfo_screenwidth()
        sh=self.win.winfo_screenheight()
        self.cv=tk.Canvas(self.win,width=sw,height=sh,
                          highlightthickness=0,cursor="crosshair")
        self.cv.pack(fill="both",expand=True)
        if self._ss and PIL_OK:
            from PIL import ImageDraw
            ov=self._ss.copy().convert("RGBA")
            dk=Image.new("RGBA",ov.size,(0,0,0,100))
            ov=Image.alpha_composite(ov,dk).convert("RGB")
            self._bgi=ImageTk.PhotoImage(ov)
            self.cv.create_image(0,0,anchor="nw",image=self._bgi)
        else:
            self.cv.create_rectangle(0,0,sw,sh,fill="#000000")
            self.win.attributes("-alpha",0.7)
        # Instrucciones
        self.cv.create_rectangle(sw//2-360,14,sw//2+360,78,
                                 fill="#071428",outline=self.BC,width=2)
        self.cv.create_text(sw//2,34,fill=self.BC,
                            font=("Segoe UI",14,"bold"),
                            text=f"✂  Seleccionando: {self.label.upper()}")
        self.cv.create_text(sw//2,58,fill="#94a3b8",
                            font=("Segoe UI",11),
                            text="Arrastrá para marcar · ESC=cancelar · Enter=confirmar")
        self.cv.bind("<ButtonPress-1>",self._press)
        self.cv.bind("<B1-Motion>",self._drag)
        self.cv.bind("<ButtonRelease-1>",self._release)
        self.win.bind("<Escape>",lambda e:self.win.destroy())
        self.win.bind("<Return>",lambda e:self._confirm())
        self.win.focus_force()

    def _redraw(self):
        for id_ in [self.rid,self.iid,self.did]:
            if id_: self.cv.delete(id_)
        x1,y1=min(self.sx,self.cx),min(self.sy,self.cy)
        x2,y2=max(self.sx,self.cx),max(self.sy,self.cy)
        w,h=x2-x1,y2-y1
        if w<2 or h<2: return
        self.rid=self.cv.create_rectangle(x1,y1,x2,y2,
                                          outline=self.BC,width=2,fill="")
        arm=16;cc="#ffffff"
        for cx_,cy_,dx,dy in [(x1,y1,-1,-1),(x2,y1,1,-1),(x1,y2,-1,1),(x2,y2,1,1)]:
            self.cv.create_line(cx_,cy_,cx_+dx*arm,cy_,fill=cc,width=2)
            self.cv.create_line(cx_,cy_,cx_,cy_+dy*arm,fill=cc,width=2)
        ly=y1-22 if y1>30 else y2+8
        self.cv.create_rectangle(x1,ly-4,x1+170,ly+18,fill="#071428",outline=self.BC,width=1)
        self.did=self.cv.create_text(x1+8,ly+6,
                                     text=f"{w} × {h}  px  ({x1},{y1})",
                                     fill=self.BC,font=("Courier",10,"bold"),anchor="w")
        iy=y2+26 if y2+50<self.win.winfo_screenheight() else y1-40
        self.iid=self.cv.create_text(x1,iy,
                                     text=f"x:{x1}  y:{y1}  w:{w}  h:{h}",
                                     fill="#94a3b8",font=("Courier",9),anchor="w")

    def _press(self,e): self.sx,self.sy=e.x,e.y; self.cx,self.cy=e.x,e.y
    def _drag(self,e):  self.cx,self.cy=e.x,e.y; self._redraw()
    def _release(self,e):
        self.cx,self.cy=e.x,e.y; self._redraw()
        bh=self.win.winfo_screenheight()
        bw=self.win.winfo_screenwidth()
        y2=max(self.sy,self.cy)
        x2=max(self.sx,self.cx)
        by=y2+36 if y2+80<bh else min(self.sy,self.cy)-56
        bx=min(x2+10,bw-320)
        self.cv.create_rectangle(bx-8,by-8,bx+310,by+42,
                                 fill="#071428",outline=self.BC,width=1)
        tk.Button(self.win,text="✔  CONFIRMAR",bg="#22c55e",fg="#fff",
                  font=("Segoe UI",10,"bold"),relief="flat",padx=14,pady=6,
                  cursor="hand2",command=self._confirm).place(x=bx,y=by)
        tk.Button(self.win,text="↺  REHACER",bg="#0ea5e9",fg="#fff",
                  font=("Segoe UI",10,"bold"),relief="flat",padx=14,pady=6,
                  cursor="hand2",command=self._restart).place(x=bx+164,y=by)
        if self.pcb and PIL_OK:
            threading.Thread(target=self._preview,daemon=True).start()

    def _preview(self):
        x1,y1=min(self.sx,self.cx),min(self.sy,self.cy)
        w,h=abs(self.cx-self.sx),abs(self.cy-self.sy)
        if w>4 and h>4:
            try: self.pcb(x1,y1,w,h)
            except: pass

    def _confirm(self):
        x1,y1=min(self.sx,self.cx),min(self.sy,self.cy)
        w,h=abs(self.cx-self.sx),abs(self.cy-self.sy)
        self.win.destroy()
        if w>4 and h>4: self.cb(x1,y1,w,h)

    def _restart(self):
        self.sx=self.sy=self.cx=self.cy=0
        for id_ in [self.rid,self.iid,self.did]:
            if id_: self.cv.delete(id_)
        for w in self.win.winfo_children():
            if isinstance(w,tk.Button): w.destroy()

# ══════════════════════════════════════════════════════════
#   BOT PRINCIPAL
# ══════════════════════════════════════════════════════════
class BinomoBot:
    def __init__(self,root):
        self.root=root
        self.root.title("⚡ ALPHA BOT v6 — Binomo · IA Avanzada · Heikin Ashi")
        self.root.configure(bg=C["bg"])
        self.root.geometry("1280x820")
        self.root.minsize(1100,720)

        # Estado
        self.running=False
        self.prices=deque(maxlen=300)
        self.ha_candles=[]
        self.opens=deque(maxlen=300)
        self.en_op=False
        self.op_tipo=None; self.op_entrada=None; self.op_fin=None
        self.operaciones=[]; self.noticia=NOTICIAS[0]
        self.cooldown_end=0
        self.ultimo_saldo_ocr=None; self.ultimo_resultado_ocr=None
        self.ultimo_precio_ocr=None
        self.racha_w=0; self.racha_l=0
        self.ops_hoy=0; self.saldo_ref=0.0

        # ── IntVars para regiones OCR ──
        def mkRegion(x,y,w,h):
            return [tk.IntVar(value=x),tk.IntVar(value=y),
                    tk.IntVar(value=w),tk.IntVar(value=h)]

        # Precio gráfico
        self.r_precio=mkRegion(1160,448,115,22)
        # Saldo cuenta
        self.r_saldo=mkRegion(990,138,155,24)
        # Resultado operación (popup inferior izq)
        self.r_resultado=mkRegion(75,658,220,32)
        # Campo de monto (donde el usuario escribe el monto en Binomo)
        self.r_monto_campo=mkRegion(1300,215,120,36)
        # Botones SUBIR/BAJAR
        self.x_subir=tk.IntVar(value=1317); self.y_subir=tk.IntVar(value=461)
        self.x_bajar=tk.IntVar(value=1406); self.y_bajar=tk.IntVar(value=461)

        # Regiones indicadores OCR (pixel color)
        self.ind_regions={
            "RSI_val":    mkRegion(0,0,60,20),
            "MACD_val":   mkRegion(0,0,60,20),
            "BB_upper":   mkRegion(0,0,80,20),
            "Stoch_K":    mkRegion(0,0,60,20),
            "ATR_val":    mkRegion(0,0,60,20),
            "CCI_val":    mkRegion(0,0,60,20),
            "ADX_val":    mkRegion(0,0,60,20),
            "AO_val":     mkRegion(0,0,60,20),
            "Mom_val":    mkRegion(0,0,60,20),
        }

        # Habilitados
        self.ind_enabled={
            "RSI":tk.BooleanVar(value=True),
            "MACD":tk.BooleanVar(value=True),
            "BB":tk.BooleanVar(value=True),
            "Stoch":tk.BooleanVar(value=True),
            "ParSAR":tk.BooleanVar(value=True),
            "ATR":tk.BooleanVar(value=True),
            "ADX":tk.BooleanVar(value=True),
            "CCI":tk.BooleanVar(value=True),
            "AO":tk.BooleanVar(value=True),
            "Mom":tk.BooleanVar(value=True),
            "HA":tk.BooleanVar(value=True),
        }
        # OCR detecciones habilitadas
        self.ocr_enabled={
            "precio":   tk.BooleanVar(value=False),
            "saldo":    tk.BooleanVar(value=True),
            "resultado":tk.BooleanVar(value=True),
            "monto":    tk.BooleanVar(value=True),  # escritura de monto
        }

        # Config
        self.duracion=tk.IntVar(value=1)
        self.ganancia_pct=tk.DoubleVar(value=82.0)
        self.saldo=tk.DoubleVar(value=752100)
        self.estrategia=tk.StringVar(value="Equilibrada")
        self.usar_real=tk.BooleanVar(value=YFINANCE_OK)
        self.cooldown_seg=tk.IntVar(value=8)
        self.max_ops=tk.IntVar(value=25)
        self.sl_pct=tk.DoubleVar(value=20.0)
        self.tp_pct=tk.DoubleVar(value=60.0)
        self.monto_modo=tk.StringVar(value="Fijo")
        self.monto_pct=tk.DoubleVar(value=2.0)
        self.monto=tk.IntVar(value=1000)
        self.usar_ocr_precio=self.ocr_enabled["precio"]

        self._init_prices()
        self._build_ui()
        self._log("⚡ ALPHA BOT v6 listo. Configurá indicadores y presioná ▶","i")
        self._check_deps()
        self._ui_loop()

    def _init_prices(self):
        p=641.0
        for _ in range(80):
            nxt=sim_price(p)
            self.prices.append(nxt)
            self.opens.append(p)
            p=nxt
        self._recalc_ha()

    def _recalc_ha(self):
        p=list(self.prices); o=list(self.opens)
        n=len(p)
        if n<2: return
        highs=[max(o[i],p[i])+abs(p[i]-o[i])*0.1 for i in range(n)]
        lows=[min(o[i],p[i])-abs(p[i]-o[i])*0.1 for i in range(n)]
        self.ha_candles=heikin_ashi(o,highs,lows,p)

    def _panel(self,parent,title,**kw):
        return tk.LabelFrame(parent,text=f"  {title}  ",
                             bg=C["panel"],fg=C["muted"],
                             font=("Courier",8),relief="groove",bd=1,**kw)

    # ════════════════════════════════════════════════════
    #   UI
    # ════════════════════════════════════════════════════
    def _build_ui(self):
        # Header
        hdr=tk.Frame(self.root,bg=C["bg"],pady=6)
        hdr.pack(fill="x",padx=12)
        tk.Label(hdr,text="⚡ ALPHA BOT",font=("Courier",16,"bold"),
                 bg=C["bg"],fg=C["blue"]).pack(side="left")
        tk.Label(hdr,text="  v6 · Binomo · IA Avanzada · Heikin Ashi · 11 Indicadores",
                 font=("Courier",8),bg=C["bg"],fg=C["muted"]).pack(side="left")
        self.status_lbl=tk.Label(hdr,text="● DETENIDO",font=("Courier",9,"bold"),
                                 bg="#1a0505",fg=C["red"],padx=10,pady=3)
        self.status_lbl.pack(side="right",padx=6)
        bf=tk.Frame(hdr,bg=C["bg"])
        bf.pack(side="right")
        self.btn_start=tk.Button(bf,text="▶  INICIAR",command=self._start,
                                 bg=C["green"],fg="#fff",font=("Courier",9,"bold"),
                                 relief="flat",padx=12,pady=5,cursor="hand2")
        self.btn_start.pack(side="left",padx=3)
        self.btn_stop=tk.Button(bf,text="■  DETENER",command=self._stop,
                                bg="#1a0505",fg=C["muted"],font=("Courier",9,"bold"),
                                relief="flat",padx=12,pady=5,cursor="hand2",state="disabled")
        self.btn_stop.pack(side="left",padx=3)
        tk.Frame(self.root,bg=C["border"],height=1).pack(fill="x")

        # Notebook
        st=ttk.Style(); st.theme_use("clam")
        st.configure("TNotebook",background=C["bg"],borderwidth=0)
        st.configure("TNotebook.Tab",background=C["panel"],foreground=C["muted"],
                     padding=[10,5],font=("Courier",8))
        st.map("TNotebook.Tab",
               background=[("selected",C["bg"])],foreground=[("selected",C["blue"])])
        nb=ttk.Notebook(self.root)
        nb.pack(fill="both",expand=True,padx=6,pady=4)
        tabs={}
        for key,lbl in [("main","📊 Trading"),("detect","🔍 Detección"),
                        ("indicators","📈 Indicadores"),("money","💰 Gestión"),
                        ("config","⚙ Config")]:
            f=tk.Frame(nb,bg=C["bg"])
            nb.add(f,text=f"  {lbl}  ")
            tabs[key]=f
        self._build_main(tabs["main"])
        self._build_detect(tabs["detect"])
        self._build_indicators(tabs["indicators"])
        self._build_money(tabs["money"])
        self._build_config(tabs["config"])

    # ── Tab Trading ──────────────────────────────────────
    def _build_main(self,p):
        left=tk.Frame(p,bg=C["bg"])
        left.pack(side="left",fill="both",expand=True,padx=(4,2),pady=4)
        right=tk.Frame(p,bg=C["bg"])
        right.configure(width=330); right.pack_propagate(False)
        right.pack(side="left",fill="y",padx=(2,4),pady=4)

        # Precio
        pf=self._panel(left,"PRECIO · CRYPTO IDX · Heikin Ashi")
        pf.pack(fill="x",pady=(0,4))
        pr=tk.Frame(pf,bg=C["panel"]); pr.pack(fill="x",padx=10,pady=6)
        self.precio_lbl=tk.Label(pr,text="641.0000",
                                 font=("Courier",26,"bold"),bg=C["panel"],fg=C["green"])
        self.precio_lbl.pack(side="left")
        rp=tk.Frame(pr,bg=C["panel"]); rp.pack(side="left",padx=12)
        self.cambio_lbl=tk.Label(rp,text="▲ 0.0000",font=("Courier",10),
                                 bg=C["panel"],fg=C["green"])
        self.cambio_lbl.pack(anchor="w")
        self.ha_lbl=tk.Label(rp,text="HA: —",font=("Courier",9,"bold"),
                             bg=C["panel"],fg=C["yellow"])
        self.ha_lbl.pack(anchor="w")
        self.saldo_ocr_lbl=tk.Label(rp,text="Saldo OCR: —",font=("Courier",8),
                                    bg=C["panel"],fg=C["gold"])
        self.saldo_ocr_lbl.pack(anchor="w")

        # Chart
        cf=self._panel(left,"GRÁFICO HEIKIN ASHI + INDICADORES")
        cf.pack(fill="x",pady=(0,4))
        self.canvas=tk.Canvas(cf,height=130,bg=C["dark"],bd=0,highlightthickness=0)
        self.canvas.pack(fill="x",padx=4,pady=4)

        # Indicadores grid
        igf=self._panel(left,"INDICADORES (11)")
        igf.pack(fill="x",pady=(0,4))
        self.ind_labels={}
        igrid=tk.Frame(igf,bg=C["panel"]); igrid.pack(fill="x",padx=8,pady=6)
        specs=[
            ("RSI",C["yellow"]),("MACD",C["blue"]),("BB",C["cyan"]),
            ("Stoch",C["purple"]),("ParSAR",C["teal"]),("ATR",C["muted"]),
            ("ADX",C["orange"]),("CCI",C["pink"]),("AO",C["green"]),
            ("Mom",C["gold"]),("HA",C["blue"]),
        ]
        for i,(name,col) in enumerate(specs):
            c_=i%4; r_=i//4
            tk.Label(igrid,text=name,font=("Courier",7),
                     bg=C["panel"],fg=C["muted"]).grid(row=r_*2,column=c_,sticky="w",padx=8)
            lbl=tk.Label(igrid,text="—",font=("Courier",9,"bold"),
                         bg=C["panel"],fg=col)
            lbl.grid(row=r_*2+1,column=c_,sticky="w",padx=8,pady=(0,4))
            self.ind_labels[name]=lbl

        # Señal principal
        sf=tk.Frame(igf,bg=C["panel"]); sf.pack(fill="x",padx=10,pady=(0,6))
        self.señal_lbl=tk.Label(sf,text="⏳  ESPERAR",font=("Courier",16,"bold"),
                                bg=C["panel"],fg=C["yellow"])
        self.señal_lbl.pack(side="left")
        self.conf_bar_frame=tk.Frame(sf,bg=C["panel"]); self.conf_bar_frame.pack(side="left",padx=14)
        self.conf_pct_lbl=tk.Label(self.conf_bar_frame,text="0%",font=("Courier",12,"bold"),
                                   bg=C["panel"],fg=C["muted"])
        self.conf_pct_lbl.pack()
        self.conf_sub_lbl=tk.Label(self.conf_bar_frame,text="consenso",font=("Courier",7),
                                   bg=C["panel"],fg=C["muted"])
        self.conf_sub_lbl.pack()

        # Historial
        hf=self._panel(left,"HISTORIAL")
        hf.pack(fill="both",expand=True)
        cols=("Hora","Dir","Monto","Entrada","Result","Δ Saldo","Señal%")
        self.tree=ttk.Treeview(hf,columns=cols,show="headings",height=5,style="Dark.Treeview")
        ws=[68,60,80,90,85,80,60]
        for col,w in zip(cols,ws):
            self.tree.heading(col,text=col); self.tree.column(col,width=w,anchor="center")
        self.tree.pack(fill="both",expand=True,padx=4,pady=4)
        ts=ttk.Style()
        ts.configure("Dark.Treeview",background=C["dark"],foreground=C["text"],
                     fieldbackground=C["dark"],rowheight=20,font=("Courier",8))
        ts.configure("Dark.Treeview.Heading",background=C["panel"],
                     foreground=C["muted"],font=("Courier",8))
        self.tree.tag_configure("win",foreground=C["green"])
        self.tree.tag_configure("loss",foreground=C["red"])

        # Panel derecho
        of=self._panel(right,"OPERACIÓN ACTIVA")
        of.pack(fill="x",pady=(0,4))
        self.op_tipo_lbl=tk.Label(of,text="— Esperando señal —",
                                  font=("Courier",13,"bold"),bg=C["panel"],fg=C["muted"])
        self.op_tipo_lbl.pack(pady=(6,2))
        self.op_info_lbl=tk.Label(of,text="",font=("Courier",8),bg=C["panel"],fg=C["muted"])
        self.op_info_lbl.pack()
        self.op_timer_lbl=tk.Label(of,text="",font=("Courier",12,"bold"),
                                   bg=C["panel"],fg=C["blue"])
        self.op_timer_lbl.pack(pady=(2,2))
        self.res_ocr_lbl=tk.Label(of,text="Resultado OCR: —",font=("Courier",8),
                                  bg=C["panel"],fg=C["gold"])
        self.res_ocr_lbl.pack(pady=(0,6))

        capf=self._panel(right,"CAPITAL")
        capf.pack(fill="x",pady=(0,4))
        self.saldo_lbl=tk.Label(capf,text="$752.100 ARS",font=("Courier",15,"bold"),
                                bg=C["panel"],fg=C["green"])
        self.saldo_lbl.pack(pady=(5,2))
        self.saldo_ocr_panel=tk.Label(capf,text="OCR: —",font=("Courier",8),
                                      bg=C["panel"],fg=C["gold"])
        self.saldo_ocr_panel.pack()
        mrow=tk.Frame(capf,bg=C["panel"]); mrow.pack(fill="x",padx=10,pady=4)
        tk.Label(mrow,text="Próximo monto:",font=("Courier",8),
                 bg=C["panel"],fg=C["muted"]).pack(side="left")
        self.monto_calc_lbl=tk.Label(mrow,text="$1.000",font=("Courier",11,"bold"),
                                     bg=C["panel"],fg=C["yellow"])
        self.monto_calc_lbl.pack(side="right")
        self.racha_lbl=tk.Label(capf,text="—",font=("Courier",9,"bold"),
                                bg=C["panel"],fg=C["muted"])
        self.racha_lbl.pack(pady=(0,2))
        self.stats_lbl=tk.Label(capf,text="",font=("Courier",8),
                                bg=C["panel"],fg=C["muted"])
        self.stats_lbl.pack()
        self.progress=ttk.Progressbar(capf,length=200,mode="determinate")
        self.progress.pack(fill="x",padx=10,pady=(2,8))

        notf=self._panel(right,"SENTIMIENTO")
        notf.pack(fill="x",pady=(0,4))
        self.not_lbl=tk.Label(notf,text="—",font=("Courier",8),bg=C["panel"],
                              fg=C["text"],wraplength=300,justify="left")
        self.not_lbl.pack(anchor="w",padx=10,pady=(6,2))
        self.sent_lbl=tk.Label(notf,text="NEUTRAL",font=("Courier",9,"bold"),
                               bg=C["panel"],fg=C["yellow"])
        self.sent_lbl.pack(anchor="w",padx=10,pady=(0,8))

        lf=self._panel(right,"LOG")
        lf.pack(fill="both",expand=True)
        self.log_box=scrolledtext.ScrolledText(lf,height=10,bg=C["dark"],fg=C["muted"],
                                               font=("Courier",8),relief="flat",
                                               state="disabled",insertbackground=C["text"])
        self.log_box.pack(fill="both",expand=True,padx=4,pady=4)
        for tag,col in [("s",C["success"]),("w",C["warn"]),("e",C["error"]),
                        ("i",C["muted"]),("t","#1e3a5f")]:
            self.log_box.tag_config(tag,foreground=col)

    # ── Tab Detección ─────────────────────────────────────
    def _build_detect(self,p):
        # Scrollable frame
        canv=tk.Canvas(p,bg=C["bg"],highlightthickness=0)
        sb=ttk.Scrollbar(p,orient="vertical",command=canv.yview)
        sf=tk.Frame(canv,bg=C["bg"])
        sf.bind("<Configure>",lambda e:canv.configure(scrollregion=canv.bbox("all")))
        canv.create_window((0,0),window=sf,anchor="nw")
        canv.configure(yscrollcommand=sb.set)
        canv.pack(side="left",fill="both",expand=True,padx=6,pady=6)
        sb.pack(side="right",fill="y")

        def make_region_block(parent,title,reg_vars,ocr_key,
                              ocr_label,test_fn,color,note=""):
            """Genera un bloque de configuración de región con toggle."""
            f=self._panel(parent,title)
            f.pack(fill="x",pady=(0,8),padx=4)

            # Toggle ON/OFF
            top=tk.Frame(f,bg=C["panel"]); top.pack(fill="x",padx=10,pady=(8,4))
            var=self.ocr_enabled.get(ocr_key)
            if var:
                tk.Checkbutton(top,text=f"Habilitado",variable=var,
                               bg=C["panel"],fg=C["text"],
                               selectcolor=C["panel"],font=("Courier",9,"bold"),
                               activebackground=C["panel"],cursor="hand2").pack(side="left")
            if note:
                tk.Label(top,text=note,font=("Courier",7),
                         bg=C["panel"],fg=C["muted"]).pack(side="left",padx=8)

            # Coords
            coords=tk.Frame(f,bg=C["panel"]); coords.pack(fill="x",padx=10,pady=2)
            lbl_names=["X","Y","Ancho","Alto"]
            for i,(lv,ln) in enumerate(zip(reg_vars,lbl_names)):
                tk.Label(coords,text=ln+":",font=("Courier",8),
                         bg=C["panel"],fg=C["muted"],width=6,anchor="e").grid(
                    row=0,column=i*2,padx=2,pady=2)
                tk.Entry(coords,textvariable=lv,font=("Courier",9),
                         bg="#0a1628",fg=C["text"],relief="flat",bd=3,width=6,
                         insertbackground=C["text"]).grid(row=0,column=i*2+1,padx=2)

            # Botones
            btnf=tk.Frame(f,bg=C["panel"]); btnf.pack(fill="x",padx=10,pady=(4,8))
            tk.Button(btnf,text="✂  Seleccionar en pantalla",
                      bg="#0c2a40",fg=color,font=("Courier",8,"bold"),
                      relief="flat",cursor="hand2",pady=4,
                      command=lambda rv=reg_vars,k=ocr_key,c=color,tf=test_fn:
                      self._open_selector(rv,k,tf)).pack(side="left",fill="x",expand=True,padx=(0,4))
            tk.Button(btnf,text="📸 Test OCR",
                      bg=color,fg="#000" if color==C["gold"] else "#fff",
                      font=("Courier",8),relief="flat",cursor="hand2",pady=4,
                      command=test_fn).pack(side="left",fill="x",expand=True)
            return f

        # Precio
        make_region_block(sf,"PRECIO EN GRÁFICO",self.r_precio,"precio",
                          "Precio","",self._test_precio,C["blue"],
                          "Se leerá con OCR cada tick")
        # Saldo
        make_region_block(sf,"SALDO DE CUENTA (sup. der.)",self.r_saldo,"saldo",
                          "Saldo","",self._test_saldo,C["gold"],
                          "Ej: 998.839,00 Arg$")
        # Resultado op
        make_region_block(sf,"RESULTADO OPERACIÓN (popup inf. izq.)",self.r_resultado,
                          "resultado","","",self._test_resultado,C["purple"],
                          "Aparece cerca del calendario tras cada operación")
        # Campo monto
        make_region_block(sf,"CAMPO DE MONTO (donde escribir en Binomo)",
                          self.r_monto_campo,"monto","","",self._test_monto_campo,
                          C["yellow"],"El bot hará clic aquí, borrará y escribirá el monto")

        # Botones SUBIR/BAJAR
        bf2=self._panel(sf,"BOTONES SUBIR / BAJAR")
        bf2.pack(fill="x",pady=(0,8),padx=4)
        for label,xv,yv,col,which in [
            ("↑ SUBIR (verde)",self.x_subir,self.y_subir,C["green"],"subir"),
            ("↓ BAJAR (rojo)", self.x_bajar,self.y_bajar,C["red"],  "bajar"),
        ]:
            r=tk.Frame(bf2,bg=C["panel"]); r.pack(fill="x",padx=10,pady=4)
            tk.Label(r,text=label,font=("Courier",9,"bold"),
                     bg=C["panel"],fg=C["text"],width=18,anchor="w").pack(side="left")
            for lbl2,var in [("X:",xv),("Y:",yv)]:
                tk.Label(r,text=lbl2,font=("Courier",8),
                         bg=C["panel"],fg=C["muted"]).pack(side="left",padx=(6,0))
                tk.Entry(r,textvariable=var,font=("Courier",9),
                         bg="#0a1628",fg=C["text"],relief="flat",bd=3,width=6,
                         insertbackground=C["text"]).pack(side="left",padx=2)
            tk.Button(r,text="📍 Detectar (5s)",bg="#0a1628",fg=col,
                      font=("Courier",8),relief="flat",cursor="hand2",
                      command=lambda w=which:self._detectar(w)).pack(side="right",padx=4)
            tk.Button(r,text=f"Test {label[:6]}",bg=col,fg="#fff",
                      font=("Courier",8),relief="flat",cursor="hand2",
                      command=(self._click_subir if which=="subir" else self._click_bajar)
                      ).pack(side="right")

    # ── Tab Indicadores ──────────────────────────────────
    def _build_indicators(self,p):
        left=tk.Frame(p,bg=C["bg"]); left.pack(side="left",fill="both",expand=True,padx=8,pady=8)
        right=tk.Frame(p,bg=C["bg"])
        right.configure(width=340); right.pack_propagate(False)
        right.pack(side="left",fill="y",padx=(0,8),pady=8)

        en_f=self._panel(left,"INDICADORES ACTIVOS — activá/desactivá individualmente")
        en_f.pack(fill="x",pady=(0,8))
        tk.Label(en_f,
                 text="El bot usa solo los indicadores marcados. Desactivá los que no tengas en Binomo.",
                 font=("Courier",8),bg=C["panel"],fg=C["muted"],justify="left"
                 ).pack(anchor="w",padx=12,pady=(10,6))

        ind_info={
            "RSI":    ("RSI",    C["yellow"], "Sobrecompra/sobreventa (peso 2.0)"),
            "MACD":   ("MACD",   C["blue"],   "Cambio de tendencia, histograma (peso 2.5)"),
            "BB":     ("Bollinger Bands",C["cyan"], "Volatilidad y extremos de precio (peso 1.5)"),
            "Stoch":  ("Stochastic",C["purple"],"Confirma RSI, muy útil en lateral (peso 1.8)"),
            "ParSAR": ("Parabolic SAR",C["teal"],"Dirección de tendencia en tiempo real (peso 1.5)"),
            "ATR":    ("ATR",    C["muted"],  "Filtra entradas en alta volatilidad (peso 0.5)"),
            "ADX":    ("ADX",    C["orange"], "Fuerza de tendencia — amplifica señales (peso 1.2)"),
            "CCI":    ("CCI",    C["pink"],   "Detecta reversiones extremas (peso 1.3)"),
            "AO":     ("Awesome Osc",C["green"],"Momentum de corto vs largo plazo (peso 1.0)"),
            "Mom":    ("Momentum",C["gold"],  "Velocidad/aceleración del precio (peso 1.0)"),
            "HA":     ("Heikin Ashi",C["blue"],"Patrón de velas suavizadas (peso 2.0) ⭐ RECOMENDADO"),
        }
        for key,(name,col,desc) in ind_info.items():
            r=tk.Frame(en_f,bg=C["panel"]); r.pack(fill="x",padx=10,pady=3)
            cb=tk.Checkbutton(r,text=f"{name}",variable=self.ind_enabled[key],
                              bg=C["panel"],fg=col,selectcolor=C["panel"],
                              font=("Courier",9,"bold"),activebackground=C["panel"],
                              cursor="hand2",width=16,anchor="w")
            cb.pack(side="left")
            tk.Label(r,text=desc,font=("Courier",8),bg=C["panel"],fg=C["muted"]
                     ).pack(side="left",padx=6)

        # Grafico type note
        gf=self._panel(left,"TIPO DE GRÁFICO RECOMENDADO")
        gf.pack(fill="x",pady=(0,8))
        tk.Label(gf,
                 text=(
                     "⭐  Activá HEIKIN ASHI en Binomo:\n"
                     "     Tipo de gráfico → Heikin Ashi\n\n"
                     "    Las velas Heikin Ashi suavizan el ruido y hacen\n"
                     "    tendencias más claras. Ideal para opciones binarias.\n\n"
                     "   También activá en Binomo:\n"
                     "     ✅ RSI  ✅ MACD  ✅ Bollinger Bands\n"
                     "     ✅ Stochastic  ✅ Parabolic SAR  ✅ ATR\n"
                     "     ✅ ADX  ✅ CCI  ✅ Awesome Oscillator\n\n"
                     "   El bot calcula todos los indicadores internamente.\n"
                     "   La lectura OCR de valores de indicadores es opcional\n"
                     "   y se configura en el tab Detección."
                 ),
                 font=("Courier",9),bg=C["panel"],fg=C["text"],justify="left"
                 ).pack(anchor="w",padx=16,pady=12)

        # Derecho — pesos y explicación
        wf=self._panel(right,"SISTEMA DE PUNTUACIÓN")
        wf.pack(fill="x",pady=(0,8))
        tk.Label(wf,
                 text=(
                     "El bot asigna puntos ponderados:\n\n"
                     "  MACD     ████████  2.5\n"
                     "  RSI      ███████   2.0\n"
                     "  Heikin A ███████   2.0\n"
                     "  Stoch    ██████    1.8\n"
                     "  BB       █████     1.5\n"
                     "  Parab.   █████     1.5\n"
                     "  EMA Cruz █████     1.5\n"
                     "  CCI      ████      1.3\n"
                     "  ADX      ████      1.2\n"
                     "  AO       ███       1.0\n"
                     "  Momentum ███       1.0\n"
                     "  ATR      █         0.5\n\n"
                     "  ≥65% alcista → SUBIR\n"
                     "  ≤35% alcista → BAJAR\n"
                     "  resto → ESPERAR"
                 ),
                 font=("Courier",9),bg=C["panel"],fg=C["muted"],justify="left"
                 ).pack(anchor="w",padx=14,pady=10)

        sf2=self._panel(right,"ESTRATEGIA DE ENTRADA")
        sf2.pack(fill="x")
        for name,info in ESTRATEGIAS.items():
            r=tk.Frame(sf2,bg=C["panel"]); r.pack(fill="x",padx=10,pady=4)
            tk.Radiobutton(r,text=name,variable=self.estrategia,value=name,
                           font=("Courier",9,"bold"),bg=C["panel"],fg=C["text"],
                           selectcolor=C["panel"],activebackground=C["panel"],
                           activeforeground=C["blue"],cursor="hand2").pack(side="left")
            tk.Label(r,text=info["desc"],font=("Courier",7),
                     bg=C["panel"],fg=C["muted"]).pack(side="left",padx=6)

    # ── Tab Gestión ───────────────────────────────────────
    def _build_money(self,p):
        main=tk.Frame(p,bg=C["bg"]); main.pack(fill="both",expand=True,padx=12,pady=12)
        mf=self._panel(main,"MODO DE CÁLCULO DE MONTO AUTÓNOMO")
        mf.pack(fill="x",pady=(0,10))
        tk.Label(mf,
                 text="El bot calcula el monto según saldo real (OCR) y modo elegido.\n"
                      "Mínimo: $1.000 ARS  |  Máximo: $500.000 ARS",
                 font=("Courier",8),bg=C["panel"],fg=C["muted"],justify="left"
                 ).pack(anchor="w",padx=12,pady=(10,6))
        for name,desc in [
            ("Fijo","Porcentaje fijo del saldo"),
            ("Kelly","Fracción de Kelly matemática (~12%)"),
            ("Martingala","Dobla en pérdida, máx x4 — RIESGOSO"),
            ("Anti-Mart.","Sube con wins, baja con losses"),
        ]:
            r=tk.Frame(mf,bg=C["panel"]); r.pack(fill="x",padx=12,pady=3)
            tk.Radiobutton(r,text=name,variable=self.monto_modo,value=name,
                           font=("Courier",10,"bold"),bg=C["panel"],fg=C["text"],
                           selectcolor=C["panel"],activebackground=C["panel"],
                           cursor="hand2").pack(side="left")
            tk.Label(r,text=desc,font=("Courier",8),
                     bg=C["panel"],fg=C["muted"]).pack(side="left",padx=10)
        pr=tk.Frame(mf,bg=C["panel"]); pr.pack(fill="x",padx=12,pady=(4,10))
        tk.Label(pr,text="% del saldo:",font=("Courier",8),
                 bg=C["panel"],fg=C["muted"]).pack(side="left")
        tk.Entry(pr,textvariable=self.monto_pct,font=("Courier",10),
                 bg="#0a1628",fg=C["text"],relief="flat",bd=4,width=6,
                 insertbackground=C["text"]).pack(side="left",padx=8)
        tk.Label(pr,text="%",font=("Courier",8),
                 bg=C["panel"],fg=C["muted"]).pack(side="left")

        sf3=self._panel(main,"STOP LOSS / TAKE PROFIT DIARIO")
        sf3.pack(fill="x",pady=(0,10))
        for lbl2,var,col in [("Stop Loss % (pérdida máx.)",self.sl_pct,C["red"]),
                             ("Take Profit % (ganancia máx.)",self.tp_pct,C["green"])]:
            r=tk.Frame(sf3,bg=C["panel"]); r.pack(fill="x",padx=12,pady=4)
            tk.Label(r,text=lbl2,font=("Courier",9),bg=C["panel"],
                     fg=col,width=30,anchor="w").pack(side="left")
            tk.Entry(r,textvariable=var,font=("Courier",10),bg="#0a1628",
                     fg=C["text"],relief="flat",bd=4,width=6,
                     insertbackground=C["text"]).pack(side="left",padx=6)
            tk.Label(r,text="%",font=("Courier",8),bg=C["panel"],fg=C["muted"]).pack(side="left")

        simf=self._panel(main,"SIMULADOR")
        simf.pack(fill="x")
        self.sim_res=tk.Label(simf,text="—",font=("Courier",14,"bold"),
                              bg=C["panel"],fg=C["yellow"])
        self.sim_res.pack(pady=6)
        tk.Button(simf,text="🧮 Calcular monto ahora",
                  command=self._simular_monto,bg=C["yellow"],fg="#000",
                  font=("Courier",9,"bold"),relief="flat",cursor="hand2",pady=6
                  ).pack(fill="x",padx=12,pady=(0,12))

    # ── Tab Config ─────────────────────────────────────────
    def _build_config(self,p):
        cols=tk.Frame(p,bg=C["bg"]); cols.pack(fill="both",expand=True,padx=8,pady=8)
        c1=tk.Frame(cols,bg=C["bg"]); c1.pack(side="left",fill="both",expand=True,padx=4)
        tf=self._panel(c1,"TRADING")
        tf.pack(fill="x",pady=(0,8))
        for lbl2,var in [("Duración op. (min)",self.duracion),
                         ("% Ganancia Binomo",self.ganancia_pct),
                         ("Saldo inicial ARS",self.saldo),
                         ("Cooldown (seg)",self.cooldown_seg),
                         ("Máx. ops/día",self.max_ops)]:
            r=tk.Frame(tf,bg=C["panel"]); r.pack(fill="x",padx=10,pady=4)
            tk.Label(r,text=lbl2,font=("Courier",8),bg=C["panel"],
                     fg=C["muted"],width=22,anchor="w").pack(side="left")
            tk.Entry(r,textvariable=var,font=("Courier",9),bg="#0a1628",
                     fg=C["text"],relief="flat",bd=4,width=8,
                     insertbackground=C["text"]).pack(side="right")
        tk.Checkbutton(tf,text="Usar precios reales (yfinance)",
                       variable=self.usar_real,bg=C["panel"],fg=C["muted"],
                       selectcolor=C["panel"],font=("Courier",8),
                       activebackground=C["panel"],cursor="hand2"
                       ).pack(anchor="w",padx=10,pady=6)

        df=self._panel(c1,"DEPENDENCIAS")
        df.pack(fill="x")
        for name,ok in [("PyAutoGUI",PYAUTOGUI_OK),("Pillow",PIL_OK),
                        ("pytesseract",OCR_OK),("OpenCV",CV2_OK),("yfinance",YFINANCE_OK)]:
            r=tk.Frame(df,bg=C["panel"]); r.pack(fill="x",padx=10,pady=3)
            tk.Label(r,text=name,font=("Courier",9),bg=C["panel"],
                     fg=C["text"],width=14,anchor="w").pack(side="left")
            tk.Label(r,text="✅ OK" if ok else "❌ falta",
                     font=("Courier",9,"bold"),bg=C["panel"],
                     fg=C["green"] if ok else C["red"]).pack(side="right")

    # ════════════════════════════════════════════════════
    #   SELECTOR VISUAL
    # ════════════════════════════════════════════════════
    def _open_selector(self,reg_vars,ocr_key,test_fn):
        labels={
            "precio":"Precio en gráfico","saldo":"Saldo de cuenta",
            "resultado":"Resultado operación","monto":"Campo de monto (escritura)",
        }
        label=labels.get(ocr_key,ocr_key)
        def on_confirm(x,y,w,h):
            reg_vars[0].set(x); reg_vars[1].set(y)
            reg_vars[2].set(w); reg_vars[3].set(h)
            self._log(f"✅ [{label}]: x={x} y={y} w={w} h={h}","s")
            self.root.after(400,test_fn)
        def pcb(x,y,w,h):
            v=ocr_read_number(x,y,w,h)
            if v: self._log(f"👁 Preview [{label}]: {v}","i")
        self.root.withdraw()
        self.root.after(200,lambda: self._do_selector(on_confirm,label,pcb))

    def _do_selector(self,cb,label,pcb):
        RegionSelector(callback=cb,label=label,preview_callback=pcb)
        self.root.after(500,self.root.deiconify)

    # ════════════════════════════════════════════════════
    #   OCR TESTS
    # ════════════════════════════════════════════════════
    def _test_precio(self):
        def _r():
            v=ocr_read_number(*[x.get() for x in self.r_precio])
            if v: self._log(f"✅ OCR precio: {v:.4f}","s")
            else: self._log("❌ OCR precio falló","e")
        threading.Thread(target=_r,daemon=True).start()

    def _test_saldo(self):
        def _r():
            v=ocr_read_number(*[x.get() for x in self.r_saldo])
            if v:
                self._log(f"✅ OCR saldo: ${v:,.0f}","s")
                self.root.after(0,lambda:self.saldo.set(v))
            else: self._log("❌ OCR saldo falló","e")
        threading.Thread(target=_r,daemon=True).start()

    def _test_resultado(self):
        def _r():
            v=ocr_read_number(*[x.get() for x in self.r_resultado])
            if v: self._log(f"✅ OCR resultado: ${v:,.2f}","s")
            else: self._log("❌ OCR resultado falló","e")
        threading.Thread(target=_r,daemon=True).start()

    def _test_monto_campo(self):
        def _r():
            v=ocr_read_number(*[x.get() for x in self.r_monto_campo])
            if v: self._log(f"✅ OCR campo monto: ${v:,.0f}","s")
            else: self._log("⚠ Campo monto vacío o sin número (OK si está en 0)","w")
        threading.Thread(target=_r,daemon=True).start()

    # ════════════════════════════════════════════════════
    #   ESCRITURA DE MONTO EN BINOMO
    # ════════════════════════════════════════════════════
    def _escribir_monto_en_binomo(self,monto):
        """
        1. Clic en el campo de monto
        2. Seleccionar todo (Ctrl+A)
        3. Escribir el nuevo monto
        4. Verificar con OCR que quedó bien
        5. Si falló, reintentar una vez
        """
        if not self.ocr_enabled["monto"].get():
            return True  # skip, asumir OK
        if not PYAUTOGUI_OK:
            self._log("⚠ PyAutoGUI no disponible, monto no escrito","w")
            return False

        cx=self.r_monto_campo[0].get()+self.r_monto_campo[2].get()//2
        cy=self.r_monto_campo[1].get()+self.r_monto_campo[3].get()//2

        for intento in range(2):
            try:
                # Clic para enfocar el campo
                pyautogui.click(cx,cy)
                time.sleep(0.15)
                # Seleccionar todo el contenido
                pyautogui.hotkey("ctrl","a")
                time.sleep(0.1)
                # Escribir el monto (sin puntos ni comas — Binomo acepta entero)
                pyautogui.typewrite(str(monto),interval=0.04)
                time.sleep(0.2)
                # Verificar con OCR
                if PIL_OK and OCR_OK:
                    leido=ocr_read_number(*[x.get() for x in self.r_monto_campo])
                    if leido and abs(leido-monto)<monto*0.05:
                        self._log(f"✅ Monto escrito: ${monto:,} (OCR confirmó: ${leido:,.0f})","s")
                        return True
                    elif leido:
                        self._log(f"⚠ Monto OCR={leido:,.0f} esperado={monto:,}, reintento {intento+1}","w")
                        continue
                    else:
                        self._log(f"✅ Monto escrito: ${monto:,} (sin confirmación OCR)","s")
                        return True
                else:
                    self._log(f"✅ Monto escrito: ${monto:,}","s")
                    return True
            except Exception as ex:
                self._log(f"⚠ Error escribiendo monto: {ex}","e")
        self._log(f"❌ No se pudo escribir el monto ${monto:,}","e")
        return False

    # ════════════════════════════════════════════════════
    #   ACCIONES
    # ════════════════════════════════════════════════════
    def _log(self,msg,tipo="i"):
        def _do():
            self.log_box.config(state="normal")
            ts=datetime.now().strftime("%H:%M:%S")
            self.log_box.insert("end",ts+"  ","t")
            self.log_box.insert("end",msg+"\n",tipo)
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.root.after(0,_do)

    def _check_deps(self):
        for name,ok in [("pyautogui",PYAUTOGUI_OK),("pillow",PIL_OK),
                        ("pytesseract",OCR_OK),("opencv",CV2_OK),("yfinance",YFINANCE_OK)]:
            if not ok: self._log(f"⚠ pip install {name}","w")

    def _click_subir(self):
        if not PYAUTOGUI_OK: self._log("Sim: clic ↑ SUBIR","w"); return
        try:
            pyautogui.click(self.x_subir.get(),self.y_subir.get())
            self._log(f"🖱 Clic ↑ SUBIR ({self.x_subir.get()},{self.y_subir.get()})","s")
        except Exception as e: self._log(f"Error SUBIR: {e}","e")

    def _click_bajar(self):
        if not PYAUTOGUI_OK: self._log("Sim: clic ↓ BAJAR","w"); return
        try:
            pyautogui.click(self.x_bajar.get(),self.y_bajar.get())
            self._log(f"🖱 Clic ↓ BAJAR ({self.x_bajar.get()},{self.y_bajar.get()})","w")
        except Exception as e: self._log(f"Error BAJAR: {e}","e")

    def _detectar(self,which):
        def _r():
            if not PYAUTOGUI_OK: self._log("PyAutoGUI no instalado","e"); return
            btn="SUBIR" if which=="subir" else "BAJAR"
            self._log(f"Mové el mouse al botón {btn}... (5s)","w")
            for i in range(5,0,-1):
                x,y=pyautogui.position()
                self._log(f"  [{i}s] ({x},{y})","i"); time.sleep(1)
            x,y=pyautogui.position()
            if which=="subir":
                self.root.after(0,lambda:self.x_subir.set(x))
                self.root.after(0,lambda:self.y_subir.set(y))
            else:
                self.root.after(0,lambda:self.x_bajar.set(x))
                self.root.after(0,lambda:self.y_bajar.set(y))
            self._log(f"✅ {btn} → ({x},{y})","s")
        threading.Thread(target=_r,daemon=True).start()

    def _simular_monto(self):
        m=calcular_monto(self.saldo.get(),self.monto_modo.get(),
                         self.monto_pct.get(),self.racha_w,self.racha_l)
        self.sim_res.config(text=f"${m:,} ARS",
                            fg=C["yellow"] if m<=50000 else C["red"])
        self._log(f"🧮 Monto simulado: ${m:,} (modo {self.monto_modo.get()})","i")

    def _calcular_monto(self):
        m=calcular_monto(self.saldo.get(),self.monto_modo.get(),
                         self.monto_pct.get(),self.racha_w,self.racha_l)
        self.monto.set(m); return m

    # ════════════════════════════════════════════════════
    #   CONTROL
    # ════════════════════════════════════════════════════
    def _start(self):
        if self.running: return
        self.running=True; self.ops_hoy=0
        self.racha_w=self.racha_l=0
        self.saldo_ref=self.saldo.get()
        self.btn_start.config(state="disabled",bg="#1e293b",fg=C["muted"])
        self.btn_stop.config(state="normal",bg=C["red"],fg="#fff")
        self.status_lbl.config(text="● ACTIVO",bg="#052e16",fg=C["green"])
        self._log(f"⚡ Bot v6 iniciado | Saldo: ${self.saldo.get():,.0f} | "
                  f"Modo: {self.monto_modo.get()} | "
                  f"Estrategia: {self.estrategia.get()}","s")
        threading.Thread(target=self._loop,daemon=True).start()

    def _stop(self):
        self.running=False
        self.btn_start.config(state="normal",bg=C["green"],fg="#fff")
        self.btn_stop.config(state="disabled",bg="#1a0505",fg=C["muted"])
        self.status_lbl.config(text="● DETENIDO",bg="#1a0505",fg=C["red"])
        self._log("⏹ Bot detenido","w")

    # ════════════════════════════════════════════════════
    #   LOOP PRINCIPAL
    # ════════════════════════════════════════════════════
    def _loop(self):
        tick=0; last_yf=last_not=last_saldo=0
        while self.running:
            tick+=1; now=time.time()

            # Precio
            ocr_p=None
            if self.ocr_enabled["precio"].get() and PIL_OK and OCR_OK:
                ocr_p=ocr_read_number(*[x.get() for x in self.r_precio])
                if ocr_p: self.ultimo_precio_ocr=ocr_p

            if not ocr_p:
                if self.usar_real.get() and YFINANCE_OK and now-last_yf>60:
                    real=fetch_yfinance()
                    if real:
                        for pr in real[-20:]:
                            self.prices.append(pr); self.opens.append(pr)
                        last_yf=now; self._log("📡 yfinance actualizado","i")
                prev=list(self.prices)[-1] if self.prices else 641.0
                nxt=sim_price(prev)
                self.prices.append(nxt); self.opens.append(prev)

            # Heikin Ashi
            if tick%3==0: self._recalc_ha()

            # Saldo OCR cada 6s
            if self.ocr_enabled["saldo"].get() and now-last_saldo>6 and PIL_OK and OCR_OK:
                sv=ocr_read_number(*[x.get() for x in self.r_saldo])
                if sv and sv>=MONTO_MIN:
                    self.saldo.set(sv); self.ultimo_saldo_ocr=sv
                    last_saldo=now

            # Noticia
            if now-last_not>30:
                self.noticia=random.choice(NOTICIAS); last_not=now

            # ── Operación activa ──
            if self.en_op:
                rem=self.op_fin-now if self.op_fin else 0
                if rem>0:
                    if rem<5 and PIL_OK and OCR_OK:
                        v=ocr_read_number(*[x.get() for x in self.r_resultado])
                        if v: self.ultimo_resultado_ocr=v
                    time.sleep(1); continue

                # Resolver operación
                time.sleep(2)  # esperar popup
                saldo_post=None; res_ocr=None
                if self.ocr_enabled["resultado"].get() and PIL_OK and OCR_OK:
                    res_ocr=ocr_read_number(*[x.get() for x in self.r_resultado])
                if self.ocr_enabled["saldo"].get() and PIL_OK and OCR_OK:
                    saldo_post=ocr_read_number(*[x.get() for x in self.r_saldo])

                monto=self.monto.get()
                saldo_ant=self.saldo.get()

                if saldo_post and abs(saldo_post-saldo_ant)>10:
                    # Ganancia real = diferencia de saldo
                    ganancia=saldo_post-saldo_ant
                    gano=ganancia>0
                    self.saldo.set(saldo_post)
                    self._log(f"💰 Saldo OCR: ${saldo_post:,.0f}  Δ=${ganancia:+,.0f}",
                              "s" if gano else "e")
                elif res_ocr is not None:
                    # El popup muestra el total recibido
                    ganancia=res_ocr-monto
                    gano=res_ocr>monto*0.1
                    if not gano: ganancia=-monto
                    self.saldo.set(saldo_ant+ganancia)
                    self._log(f"📋 Resultado OCR: ${res_ocr:,.0f}  Δ=${ganancia:+,.0f}",
                              "s" if gano else "e")
                else:
                    # Fallback: comparar precio
                    p_now=list(self.prices)[-1]
                    gano=((p_now>self.op_entrada) if self.op_tipo=="SUBIR"
                          else (p_now<self.op_entrada))
                    ganancia=monto*(self.ganancia_pct.get()/100) if gano else -monto
                    self.saldo.set(saldo_ant+ganancia)
                    self._log(f"{'✅' if gano else '❌'} Fallback precio: Δ=${ganancia:+,.0f}",
                              "s" if gano else "e")

                if gano: self.racha_w+=1; self.racha_l=0
                else:    self.racha_l+=1; self.racha_w=0

                self.operaciones.append({
                    "hora":datetime.now().strftime("%H:%M:%S"),
                    "tipo":self.op_tipo,"monto":monto,
                    "entrada":self.op_entrada,
                    "resultado":"✅ GANÓ" if gano else "❌ PERDIÓ",
                    "ganancia":ganancia,"senal_pct":getattr(self,"_last_pct",0)
                })
                self.en_op=False; self.op_tipo=None
                self.cooldown_end=now+self.cooldown_seg.get()
                time.sleep(0.3); continue

            if now<self.cooldown_end: time.sleep(1); continue

            # Stop/Take
            sal=self.saldo.get()
            if self.saldo_ref>0:
                chg=(sal-self.saldo_ref)/self.saldo_ref*100
                if chg<=-self.sl_pct.get():
                    self._log(f"🛑 STOP LOSS {chg:.1f}%","e")
                    self.root.after(0,self._stop); break
                if chg>=self.tp_pct.get():
                    self._log(f"🏆 TAKE PROFIT +{chg:.1f}%","s")
                    self.root.after(0,self._stop); break

            if self.ops_hoy>=self.max_ops.get():
                time.sleep(5); continue
            if sal<MONTO_MIN: time.sleep(2); continue

            # Señal
            prices_list=list(self.prices)
            enabled={k:v.get() for k,v in self.ind_enabled.items()}
            señal,score,max_score,det=get_signal_advanced(
                prices_list,self.ha_candles,self.noticia[1],enabled)
            self._last_pct=round(score/max_score*100,1) if max_score else 0

            min_pct=ESTRATEGIAS[self.estrategia.get()]["min_pct"]
            if señal!="ESPERAR" and self._last_pct>=min_pct:
                monto=self._calcular_monto()
                # ── ESCRIBIR MONTO EN BINOMO ──
                ok_monto=self._escribir_monto_en_binomo(monto)
                if not ok_monto and self.ocr_enabled["monto"].get():
                    self._log("⚠ Monto no confirmado, op cancelada","w")
                    time.sleep(2); continue

                dur_seg=self.duracion.get()*60
                self.en_op=True; self.op_tipo=señal
                self.op_entrada=prices_list[-1]
                self.op_fin=now+dur_seg; self.ops_hoy+=1
                self._log(
                    f"{'📈' if señal=='SUBIR' else '📉'} {señal}  "
                    f"@ {self.op_entrada:.4f}  ${monto:,}  "
                    f"{self.duracion.get()}min  {self._last_pct:.0f}%  |  "
                    +str(det)[:80],
                    "s" if señal=="SUBIR" else "w")
                if señal=="SUBIR": self._click_subir()
                else:              self._click_bajar()

            time.sleep(1)

    # ════════════════════════════════════════════════════
    #   UI LOOP
    # ════════════════════════════════════════════════════
    def _ui_loop(self):
        try: self._update_ui()
        except: pass
        self.root.after(600,self._ui_loop)

    def _update_ui(self):
        if not self.prices: return
        pr=list(self.prices); precio=pr[-1]
        prev=pr[-2] if len(pr)>1 else precio
        diff=precio-prev; col=C["green"] if diff>=0 else C["red"]
        self.precio_lbl.config(text=f"{precio:.4f}",fg=col)
        self.cambio_lbl.config(text=f"{'▲' if diff>=0 else '▼'} {abs(diff):.4f}",fg=col)

        if self.ha_candles:
            ha_sig,_,ha_desc=analyze_heikin_ashi(self.ha_candles)
            hc={"ALCISTA":C["green"],"BAJISTA":C["red"],
                "ALERTA_REVERSIÓN_ALCISTA":C["yellow"],
                "ALERTA_REVERSIÓN_BAJISTA":C["yellow"]}.get(ha_sig,C["muted"])
            self.ha_lbl.config(text=f"HA: {ha_sig}",fg=hc)

        if self.ultimo_saldo_ocr:
            self.saldo_ocr_lbl.config(text=f"OCR saldo: ${self.ultimo_saldo_ocr:,.0f}",fg=C["gold"])
            self.saldo_ocr_panel.config(text=f"OCR: ${self.ultimo_saldo_ocr:,.0f}",fg=C["gold"])
        else:
            self.saldo_ocr_lbl.config(text="OCR saldo: —",fg=C["muted"])
            self.saldo_ocr_panel.config(text="OCR: —",fg=C["muted"])

        # Indicadores
        rsi=calc_rsi(pr)
        macd,sig,hist=calc_macd(pr)
        bb_l,bb_m,bb_h=calc_bollinger(pr)
        stk,std_=calc_stochastic(pr)
        atr=calc_atr(pr)
        cci=calc_cci(pr)
        adx=calc_adx(pr)
        ao=calc_awesome_oscillator(pr)
        mom=calc_momentum(pr)
        par,pbull=calc_parabolic_sar(pr)
        ema10=calc_ema(pr,10); ema26=calc_ema(pr,26)

        vals={
            "RSI":(f"{rsi:.1f}",C["green"] if rsi<35 else C["red"] if rsi>65 else C["yellow"]),
            "MACD":(f"{macd:.5f}",C["green"] if macd>0 else C["red"]),
            "BB":(f"{bb_l:.3f}–{bb_h:.3f}" if bb_l else "—",C["cyan"]),
            "Stoch":(f"K={stk:.0f} D={std_:.0f}",
                     C["green"] if stk<30 else C["red"] if stk>70 else C["yellow"]),
            "ParSAR":(f"{'↑' if pbull else '↓'} {par:.4f}",
                      C["green"] if pbull else C["red"]),
            "ATR":(f"{atr:.6f}",C["muted"]),
            "ADX":(f"{adx:.0f}",C["orange"] if adx>25 else C["muted"]),
            "CCI":(f"{cci:.0f}",C["green"] if cci<-100 else C["red"] if cci>100 else C["muted"]),
            "AO":(f"{ao:.5f}",C["green"] if ao>0 else C["red"]),
            "Mom":(f"{mom:+.2f}%",C["green"] if mom>0 else C["red"]),
            "HA":("—",C["muted"]),
        }
        if self.ha_candles:
            hs,hstr,_=analyze_heikin_ashi(self.ha_candles)
            vals["HA"]=(f"{hs}({hstr})",C["green"] if "ALCISTA" in hs else
                        C["red"] if "BAJISTA" in hs else C["yellow"])
        for name,(txt,c) in vals.items():
            if name in self.ind_labels:
                self.ind_labels[name].config(text=txt,fg=c)

        # Señal
        enabled={k:v.get() for k,v in self.ind_enabled.items()}
        señal,score,max_score,det=get_signal_advanced(pr,self.ha_candles,
                                                       self.noticia[1],enabled)
        pct=round(score/max_score*100,1) if max_score else 0
        sc={"SUBIR":C["green"],"BAJAR":C["red"],"ESPERAR":C["yellow"]}
        si={"SUBIR":"📈  SUBIR","BAJAR":"📉  BAJAR","ESPERAR":"⏳  ESPERAR"}
        self.señal_lbl.config(text=si[señal],fg=sc[señal])
        self.conf_pct_lbl.config(text=f"{pct:.0f}%",
                                 fg=C["green"] if pct>=60 else C["yellow"] if pct>=50 else C["red"])

        # Monto
        mc=self._calcular_monto()
        self.monto_calc_lbl.config(text=f"${mc:,}",fg=C["yellow"])

        # Racha
        if self.racha_w>0: self.racha_lbl.config(text=f"🔥 +{self.racha_w} wins",fg=C["green"])
        elif self.racha_l>0: self.racha_lbl.config(text=f"❄ -{self.racha_l} losses",fg=C["red"])
        else: self.racha_lbl.config(text="—",fg=C["muted"])

        # Op activa
        if self.en_op and self.op_fin:
            rem=max(0,self.op_fin-time.time())
            col2=C["green"] if self.op_tipo=="SUBIR" else C["red"]
            self.op_tipo_lbl.config(text=f"{'📈 SUBIR' if self.op_tipo=='SUBIR' else '📉 BAJAR'}",fg=col2)
            self.op_info_lbl.config(text=f"Entrada:{self.op_entrada:.4f}  Monto:${self.monto.get():,}")
            m2,s2=divmod(int(rem),60)
            self.op_timer_lbl.config(text=f"⏱ {m2:02d}:{s2:02d}",fg=C["blue"])
            if self.ultimo_resultado_ocr:
                self.res_ocr_lbl.config(text=f"Resultado OCR: ${self.ultimo_resultado_ocr:,.0f}",fg=C["gold"])
        else:
            self.op_tipo_lbl.config(text="— Esperando señal —",fg=C["muted"])
            self.op_info_lbl.config(text=""); self.op_timer_lbl.config(text="")
            self.res_ocr_lbl.config(text="Resultado OCR: —",fg=C["muted"])

        # Saldo
        sal=self.saldo.get()
        self.saldo_lbl.config(text=f"${sal:,.0f} ARS",
                              fg=C["green"] if sal>=MONTO_MIN else C["red"])

        # Stats
        ops=self.operaciones
        if ops:
            wins=sum(1 for o in ops if o["ganancia"]>0)
            total=sum(o["ganancia"] for o in ops)
            wr=wins/len(ops)*100
            self.stats_lbl.config(
                text=f"Ops:{self.ops_hoy}/{self.max_ops.get()}  WR:{wr:.0f}%  PnL:${total:+,.0f}")
            self.progress["value"]=max(0,min(100,50+(total/max(sal,1))*100))

        # Sentimiento
        sc2=C["green"] if self.noticia[1]>0 else C["red"] if self.noticia[1]<0 else C["yellow"]
        self.not_lbl.config(text=self.noticia[0])
        self.sent_lbl.config(text=f"● {'POSITIVO' if self.noticia[1]>0 else 'NEGATIVO' if self.noticia[1]<0 else 'NEUTRAL'}",fg=sc2)

        # Historial
        for row in self.tree.get_children(): self.tree.delete(row)
        for op in reversed(self.operaciones[-20:]):
            self.tree.insert("","0",values=(
                op["hora"],op["tipo"],f"${op['monto']:,}",
                f"{op['entrada']:.4f}",op["resultado"],
                f"${op['ganancia']:+,.0f}",f"{op.get('senal_pct',0):.0f}%"
            ),tags=("win" if op["ganancia"]>0 else "loss",))

        self._draw_chart()

    def _draw_chart(self):
        self.canvas.delete("all")
        w=self.canvas.winfo_width() or 560; h=130
        # Usar Heikin Ashi si está disponible
        if self.ha_candles and len(self.ha_candles)>5:
            data=[c[3] for c in self.ha_candles[-100:]]  # close HA
            is_ha=True
        else:
            data=list(self.prices)[-100:]
            is_ha=False
        if len(data)<2: return
        mn,mx=min(data),max(data); rng=mx-mn or 0.01
        yt=lambda v:h-6-((v-mn)/rng)*(h-12)
        # Bollinger
        bb_l,bb_m,bb_h2=calc_bollinger(data)
        if bb_l:
            self.canvas.create_rectangle(0,yt(bb_h2),w,yt(bb_l),fill="#071e2e",outline="")
            self.canvas.create_line(0,yt(bb_m),w,yt(bb_m),fill="#1a3a50",dash=(4,4),width=1)
        # EMA
        ema10_pts=[]; ema26_pts=[]
        for i in range(10,len(data)):
            x=i/(len(data)-1)*w
            ema10_pts.extend([x,yt(calc_ema(data[:i+1],10))])
            ema26_pts.extend([x,yt(calc_ema(data[:i+1],min(26,i+1)))])
        if len(ema10_pts)>=4:
            self.canvas.create_line(ema10_pts,fill=C["blue"],width=1,smooth=True)
        if len(ema26_pts)>=4:
            self.canvas.create_line(ema26_pts,fill=C["purple"],width=1,smooth=True)
        # Velas HA o línea
        if is_ha and len(self.ha_candles)>=5:
            ha=self.ha_candles[-100:]
            cw=max(2,w//len(ha)-1)
            for i,c in enumerate(ha):
                x=int(i/(len(ha)-1)*w) if len(ha)>1 else w//2
                col=C["green"] if c[3]>=c[0] else C["red"]
                y1_=yt(c[1]); y2_=yt(c[2])
                yo=yt(c[0]); yc=yt(c[3])
                self.canvas.create_line(x,y1_,x,y2_,fill=col,width=1)
                self.canvas.create_rectangle(x-cw//2,min(yo,yc),
                                             x+cw//2,max(yo,yc),
                                             fill=col,outline="")
        else:
            for i in range(len(data)-1):
                x1=i/(len(data)-1)*w; x2=(i+1)/(len(data)-1)*w
                col=C["green"] if data[i+1]>=data[i] else C["red"]
                self.canvas.create_line(x1,yt(data[i]),x2,yt(data[i+1]),fill=col,width=1.8)
        # Línea de entrada
        if self.en_op and self.op_entrada:
            ye=yt(self.op_entrada)
            col=C["green"] if self.op_tipo=="SUBIR" else C["red"]
            self.canvas.create_line(0,ye,w,ye,fill=col,dash=(5,4),width=1)
        # Precio actual
        self.canvas.create_text(w-4,yt(data[-1]),text=f"{data[-1]:.4f}",
                                fill=C["text"],font=("Courier",7),anchor="e")
        lbl="Heikin Ashi" if is_ha else "Precio"
        self.canvas.create_text(6,8,text=lbl,fill=C["muted"],font=("Courier",7),anchor="w")

if __name__=="__main__":
    root=tk.Tk()
    app=BinomoBot(root)
    root.mainloop()
