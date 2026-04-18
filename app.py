"""
╔══════════════════════════════════════════════════════════════════════╗
║   台股 AI 狙擊手 Pro MAX  v4.0                                       ║
║   全自動排程 | 基本面融合 | 新聞情緒 | 三段播報 | 複合評分引擎        ║
╚══════════════════════════════════════════════════════════════════════╝

安裝依賴：
    pip install streamlit yfinance pandas numpy requests plotly \
                apscheduler twstock beautifulsoup4 lxml

執行：
    streamlit run taiwan_stock_pro_v4.py
"""

# ═══════════════════════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════════════════════
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib3
import datetime
import time
import json
import re
import threading
from dataclasses import dataclass, field
from typing import Optional
from bs4 import BeautifulSoup

# APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ═══════════════════════════════════════════════════════
# 頁面配置
# ═══════════════════════════════════════════════════════
st.set_page_config(
    page_title="台股 AI 狙擊手 Pro MAX",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700;900&family=JetBrains+Mono:wght@300;400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
.stApp { background: #060b14; }
.main .block-container { padding: 1.2rem 1.8rem; max-width: 100%; }

/* ── HERO ── */
.hero-wrap {
    background: linear-gradient(135deg, #060b14 0%, #0d1528 50%, #060b14 100%);
    border: 1px solid rgba(0,255,136,0.15);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.hero-wrap::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(ellipse at 30% 50%, rgba(0,255,136,0.04) 0%, transparent 60%),
                radial-gradient(ellipse at 70% 50%, rgba(77,159,255,0.04) 0%, transparent 60%);
    pointer-events: none;
}
.hero-title {
    font-size: 2.2rem; font-weight: 900; letter-spacing: -0.04em;
    background: linear-gradient(135deg, #00ff88 0%, #4d9fff 45%, #a855f7 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    line-height: 1.1; margin-bottom: 4px;
}
.hero-sub {
    font-family: 'JetBrains Mono', monospace; font-size: 0.68rem;
    color: #4a6080; letter-spacing: 0.18em; text-transform: uppercase;
}
.hero-live {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(0,255,136,0.08); border: 1px solid rgba(0,255,136,0.2);
    border-radius: 20px; padding: 4px 12px;
    font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: #00ff88;
}
.hero-live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #00ff88; animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50% { opacity:0.4; transform:scale(0.8); }
}

/* ── 統計卡 ── */
.kpi-grid { display: grid; grid-template-columns: repeat(6,1fr); gap: 10px; margin-bottom: 18px; }
.kpi-card {
    background: #0d1528; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 14px 16px; position: relative; overflow: hidden;
}
.kpi-card::after {
    content:''; position:absolute; bottom:0; left:0; right:0; height:2px;
}
.kpi-card.g::after { background: linear-gradient(90deg,#00ff88,transparent); }
.kpi-card.r::after { background: linear-gradient(90deg,#ff3b6b,transparent); }
.kpi-card.y::after { background: linear-gradient(90deg,#ffd93d,transparent); }
.kpi-card.b::after { background: linear-gradient(90deg,#4d9fff,transparent); }
.kpi-card.p::after { background: linear-gradient(90deg,#a855f7,transparent); }
.kpi-card.w::after { background: linear-gradient(90deg,#e8edf5,transparent); }
.kpi-label {
    font-family:'JetBrains Mono',monospace; font-size:0.6rem;
    color:#4a6080; text-transform:uppercase; letter-spacing:0.15em; margin-bottom:6px;
}
.kpi-val { font-size:1.7rem; font-weight:900; line-height:1; color:#e8edf5; }
.kpi-val.g { color:#00ff88; } .kpi-val.r { color:#ff3b6b; }
.kpi-val.y { color:#ffd93d; } .kpi-val.b { color:#4d9fff; }

/* ── 徽章 ── */
.badge { display:inline-block; font-weight:700; font-size:0.65rem;
         padding:2px 9px; border-radius:20px; letter-spacing:0.08em; }
.badge-buy  { background:linear-gradient(135deg,#00ff88,#00cc6a); color:#021a0d; }
.badge-watch{ background:linear-gradient(135deg,#ffd93d,#e6a800); color:#1a1000; }
.badge-hot  { background:linear-gradient(135deg,#ff3b6b,#cc1a44); color:#fff; }

/* ── 評分環 ── */
.score-ring {
    display:inline-flex; align-items:center; justify-content:center;
    width:44px; height:44px; border-radius:50%;
    border:2px solid; font-family:'JetBrains Mono',monospace;
    font-size:0.85rem; font-weight:700;
}
.score-high  { border-color:#00ff88; color:#00ff88; background:rgba(0,255,136,0.08); }
.score-mid   { border-color:#ffd93d; color:#ffd93d; background:rgba(255,217,61,0.08); }
.score-low   { border-color:#ff3b6b; color:#ff3b6b; background:rgba(255,59,107,0.08); }

/* ── 排程狀態 ── */
.sched-card {
    background:#0d1528; border:1px solid rgba(77,159,255,0.2);
    border-radius:12px; padding:14px 18px; margin-bottom:12px;
}
.sched-row { display:flex; justify-content:space-between; align-items:center; margin:4px 0; }
.sched-label { font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#4a6080; }
.sched-val   { font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#4d9fff; }

/* ── 新聞卡 ── */
.news-item {
    border-left:3px solid rgba(255,255,255,0.1); padding:8px 14px; margin:6px 0;
    background:rgba(255,255,255,0.02); border-radius:0 8px 8px 0;
    transition: all 0.2s;
}
.news-item:hover { border-left-color:#4d9fff; background:rgba(77,159,255,0.05); }
.news-item.pos { border-left-color:#00ff88; }
.news-item.neg { border-left-color:#ff3b6b; }
.news-title { font-size:0.85rem; color:#c8d4e8; margin-bottom:3px; }
.news-meta  { font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#4a6080; }

/* ── 基本面格 ── */
.fund-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:10px 0; }
.fund-cell {
    background:#111d30; border:1px solid rgba(255,255,255,0.05);
    border-radius:8px; padding:10px 12px;
}
.fund-key { font-family:'JetBrains Mono',monospace; font-size:0.6rem; color:#4a6080;
            text-transform:uppercase; letter-spacing:0.1em; margin-bottom:3px; }
.fund-val { font-size:0.95rem; font-weight:700; color:#e8edf5; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background:#07101f !important;
    border-right:1px solid rgba(255,255,255,0.05) !important; }
section[data-testid="stSidebar"] label {
    font-family:'JetBrains Mono',monospace !important;
    color:#4a6080 !important; font-size:0.7rem !important;
    text-transform:uppercase; letter-spacing:0.1em;
}

/* ── Buttons ── */
.stButton>button[kind="primary"] {
    background:linear-gradient(135deg,#00ff88,#00cc6a) !important;
    color:#021a0d !important; font-weight:900 !important;
    font-size:0.95rem !important; height:48px !important;
    border:none !important; border-radius:10px !important;
    letter-spacing:0.05em !important;
}
.stButton>button[kind="primary"]:hover {
    box-shadow:0 6px 24px rgba(0,255,136,0.35) !important;
    transform:translateY(-1px) !important;
}
.stButton>button:not([kind="primary"]) {
    background:#0d1528 !important; color:#e8edf5 !important;
    border:1px solid rgba(255,255,255,0.1) !important; border-radius:8px !important;
}
.stProgress>div>div>div { background:linear-gradient(90deg,#00ff88,#4d9fff) !important; }
hr { border-color:rgba(255,255,255,0.06) !important; }
[data-testid="metric-container"] {
    background:#0d1528; border:1px solid rgba(255,255,255,0.06);
    border-radius:10px; padding:12px !important;
}
.streamlit-expanderHeader {
    background:#0d1528 !important; border:1px solid rgba(255,255,255,0.06) !important;
    border-radius:10px !important; font-weight:600 !important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# SESSION STATE 初始化
# ═══════════════════════════════════════════════════════
def ss_init():
    defaults = {
        "scan_results": [],
        "scan_meta": {},
        "scheduler": None,
        "sched_running": False,
        "sched_log": [],       # 排程執行紀錄
        "last_scan_time": None,
        "next_scan_time": None,
        "auto_webhook": "",
        "scan_params": {},
        "scan_codes": [],
        "discord_history": [],  # Discord 推播歷史
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

ss_init()

# ═══════════════════════════════════════════════════════
# 股票清單
# ═══════════════════════════════════════════════════════
@st.cache_data(ttl=86400)
def get_all_stock_names() -> dict:
    names = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in [
        "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
    ]:
        try:
            r = requests.get(url, headers=headers, timeout=15, verify=False)
            if r.status_code == 200:
                for item in r.json():
                    c = item.get("Code", "")
                    if len(c) == 4 and c.isdigit():
                        names[c] = item.get("Name", c)
        except Exception:
            pass
    try:
        r2 = requests.get(
            "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes",
            headers=headers, timeout=15, verify=False
        )
        if r2.status_code == 200:
            for item in r2.json():
                c = item.get("SecuritiesCompanyCode", "")
                if c and len(c) == 4 and c.isdigit():
                    names[c] = item.get("CompanyName", c)
    except Exception:
        pass
    if not names:
        names = {"2330": "台積電", "2317": "鴻海", "2454": "聯發科",
                 "2308": "台達電", "2382": "廣達", "2303": "聯電"}
    return names

STOCK_DICT = get_all_stock_names()
ALL_CODES  = sorted(STOCK_DICT.keys())

# ═══════════════════════════════════════════════════════
# 資料結構
# ═══════════════════════════════════════════════════════
@dataclass
class Fundamentals:
    pe:           Optional[float] = None   # 本益比
    pb:           Optional[float] = None   # 股價淨值比
    eps_ttm:      Optional[float] = None   # EPS (TTM)
    eps_growth:   Optional[float] = None   # EPS 年成長率 %
    rev_mom:      Optional[float] = None   # 營收月增率 %
    rev_yoy:      Optional[float] = None   # 營收年增率 %
    gross_margin: Optional[float] = None   # 毛利率 %
    op_margin:    Optional[float] = None   # 營業利益率 %
    dividend_yield: Optional[float] = None # 殖利率 %
    payout_ratio:   Optional[float] = None # 配息比率 %
    fund_score:   float = 0.0              # 基本面評分 (0~100)
    news:         list  = field(default_factory=list)  # 新聞列表

@dataclass
class ScanResult:
    code:        str
    name:        str
    signal:      str        # BUY / WATCH
    tech_score:  float      # 技術面分數 0~100
    fund_score:  float      # 基本面分數 0~100
    total_score: float      # 綜合分數 0~100
    price:       float
    change_pct:  float
    vol_ratio:   float
    stop:        float
    target:      float
    rr_ratio:    float
    win_rate:    float
    avg_return:  float
    trades:      int
    bb_pos:      float
    rsi_s:       float
    rsi_l:       float
    fundamentals: Fundamentals = field(default_factory=Fundamentals)
    df:          pd.DataFrame = field(default_factory=pd.DataFrame)

# ═══════════════════════════════════════════════════════
# 基本面資料抓取
# ═══════════════════════════════════════════════════════
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fundamentals(code: str) -> Fundamentals:
    """從 Yahoo Finance + 公開資訊站抓取基本面"""
    f = Fundamentals()
    try:
        ticker = yf.Ticker(f"{code}.TW")
        info   = ticker.info

        # PE / PB
        f.pe = info.get("trailingPE")
        f.pb = info.get("priceToBook")

        # EPS TTM
        f.eps_ttm = info.get("trailingEps")

        # EPS 成長率（用 forwardEps vs trailingEps 估算）
        fwd = info.get("forwardEps")
        ttm = info.get("trailingEps")
        if fwd and ttm and ttm != 0:
            f.eps_growth = (fwd / ttm - 1) * 100

        # 毛利率 / 營業利益率
        gm = info.get("grossMargins")
        om = info.get("operatingMargins")
        f.gross_margin = gm * 100 if gm else None
        f.op_margin    = om * 100 if om else None

        # 殖利率 / 配息比率
        dy = info.get("dividendYield")
        pr = info.get("payoutRatio")
        f.dividend_yield = dy * 100 if dy else None
        f.payout_ratio   = pr * 100 if pr else None

        # 評分（各指標正常範圍給分）
        score = 0.0
        weights = 0.0

        def add(val, low, high, w, reverse=False):
            nonlocal score, weights
            if val is None: return
            norm = (val - low) / (high - low)
            norm = max(0.0, min(1.0, norm))
            if reverse: norm = 1 - norm
            score += norm * w; weights += w

        add(f.pe,            8, 25, 20, reverse=True)  # PE 低較好
        add(f.pb,            0.5, 3, 15, reverse=True)  # PB 低較好
        add(f.eps_growth,   -10, 30, 20)
        add(f.gross_margin,  20, 60, 15)
        add(f.op_margin,      5, 30, 15)
        add(f.dividend_yield, 2,  8, 15)

        f.fund_score = (score / weights * 100) if weights > 0 else 50.0

    except Exception:
        f.fund_score = 50.0

    return f

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_revenue(code: str) -> tuple:
    """從公開資訊觀測站抓月營收"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = (f"https://mops.twse.com.tw/nas/t21/sii/t21sc03_{datetime.datetime.now().year}"
               f"_{datetime.datetime.now().month-1:02d}_0.htm")
        r = requests.get(url, headers=headers, timeout=10, verify=False)
        r.encoding = "big5"
        soup = BeautifulSoup(r.text, "lxml")
        for row in soup.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) > 8 and cols[0].text.strip() == code:
                def pct(s):
                    s = s.strip().replace(",", "").replace("%", "")
                    try: return float(s)
                    except: return None
                mom = pct(cols[6].text)  # 月增率
                yoy = pct(cols[7].text)  # 年增率
                return mom, yoy
    except Exception:
        pass
    return None, None

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_news(code: str, name: str) -> list:
    """從 Yahoo 財經新聞抓取最新新聞（含情緒標記）"""
    articles = []
    pos_kw = ["利多", "獲利", "成長", "創新高", "漲", "大單", "法人買超", "營收增", "EPS 增"]
    neg_kw = ["利空", "虧損", "下修", "跌", "減少", "停工", "裁員", "法人賣超", "下修財測"]

    try:
        ticker = yf.Ticker(f"{code}.TW")
        news   = ticker.news or []
        for n in news[:8]:
            title = n.get("title", "")
            ts    = n.get("providerPublishTime", 0)
            dt    = datetime.datetime.fromtimestamp(ts).strftime("%m/%d %H:%M") if ts else ""
            link  = n.get("link", "#")
            sentiment = "neu"
            if any(k in title for k in pos_kw): sentiment = "pos"
            if any(k in title for k in neg_kw): sentiment = "neg"
            articles.append({"title": title, "time": dt, "link": link, "sentiment": sentiment})
    except Exception:
        pass
    return articles

# ═══════════════════════════════════════════════════════
# 技術指標（向量化）
# ═══════════════════════════════════════════════════════
BATCH_SIZE = 50

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_batch(codes_tuple: tuple) -> pd.DataFrame:
    tickers = [f"{c}.TW" for c in codes_tuple]
    try:
        df = yf.download(tickers, period="1y", interval="1d",
                         group_by="ticker", threads=True,
                         progress=False, timeout=30)
        return df
    except Exception:
        return pd.DataFrame()

def get_single_df(raw: pd.DataFrame, code: str) -> Optional[pd.DataFrame]:
    ticker = f"{code}.TW"
    try:
        if isinstance(raw.columns, pd.MultiIndex):
            if ticker in raw.columns.get_level_values(0):
                sub = raw[ticker].dropna(subset=["Close"])
                return sub if len(sub) >= 60 else None
        else:
            if "Close" in raw.columns:
                sub = raw.dropna(subset=["Close"])
                return sub if len(sub) >= 60 else None
    except Exception:
        pass
    return None

def rsi_ewm(s: pd.Series, period: int) -> pd.Series:
    delta = s.diff()
    up    = delta.clip(lower=0)
    dn    = (-delta).clip(lower=0)
    gain  = up.ewm(com=period-1, adjust=False).mean()
    loss  = dn.ewm(com=period-1, adjust=False).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)

def calc_indicators(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    df = df.copy()
    c  = df["Close"].squeeze()

    # Bollinger
    ma  = c.rolling(p["bb_period"]).mean()
    std = c.rolling(p["bb_period"]).std(ddof=0)
    df["MA"]    = ma
    df["Upper"] = ma + p["bb_std"] * std
    df["Lower"] = ma - p["bb_std"] * std
    df["pct_b"] = (c - df["Lower"]) / (df["Upper"] - df["Lower"])

    # RSI
    df["RSI_S"] = rsi_ewm(c, p["rsi_short"])
    df["RSI_L"] = rsi_ewm(c, p["rsi_long"])

    # MACD
    ema_f = c.ewm(span=12, adjust=False).mean()
    ema_s = c.ewm(span=26, adjust=False).mean()
    df["MACD"]    = ema_f - ema_s
    df["MACD_sig"]= df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"]= df["MACD"] - df["MACD_sig"]

    # ATR
    h, l = df["High"].squeeze(), df["Low"].squeeze()
    tr   = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    df["ATR"]     = tr.ewm(span=14, adjust=False).mean()

    # Volume
    df["Vol_MA"]  = df["Volume"].rolling(20).mean()
    df["Vol_Ratio"]= df["Volume"] / df["Vol_MA"]

    # 動能
    df["Mom5"]    = c.pct_change(5) * 100
    df["Mom20"]   = c.pct_change(20) * 100

    return df

# ═══════════════════════════════════════════════════════
# 訊號 + 技術評分引擎
# ═══════════════════════════════════════════════════════
def generate_signal_score(df: pd.DataFrame, p: dict) -> Optional[dict]:
    if len(df) < 60:
        return None

    last  = df.iloc[-1]
    N     = p["grace"]
    score = 0.0

    # ── 技術評分（共 10 條件，每條 10 分）──
    conds = {}

    # 1. %B 低位（近 N 日觸碰超賣）
    pb_min = df["pct_b"].iloc[-N:].min()
    conds["pct_b_low"] = pb_min < p["pct_b"]

    # 2. RSI 黃金交叉（近 N 日內）
    cross = any(
        df["RSI_S"].iloc[i-1] <= df["RSI_L"].iloc[i-1] and
        df["RSI_S"].iloc[i]   >  df["RSI_L"].iloc[i]
        for i in range(-N, 0)
    )
    conds["rsi_cross"] = cross

    # 3. 量能放大
    conds["vol_surge"] = float(last["Vol_Ratio"]) >= p["vol_mult"]

    # 4. MACD 方向（多頭）
    conds["macd_bull"] = bool(last["MACD"] > last["MACD_sig"])

    # 5. MACD Histogram 放大（動能增強）
    if len(df) >= 2:
        conds["macd_hist_grow"] = bool(df["MACD_hist"].iloc[-1] > df["MACD_hist"].iloc[-2])
    else:
        conds["macd_hist_grow"] = False

    # 6. 收盤站回 MA
    conds["above_ma"] = bool(last["Close"] > last["MA"])

    # 7. RSI 短期未過熱（< 75）
    conds["rsi_not_hot"] = bool(last["RSI_S"] < 75)

    # 8. 短期動能正向
    conds["mom5_pos"] = bool(last["Mom5"] > 0)

    # 9. 中期動能轉正
    conds["mom20_pos"] = bool(last["Mom20"] > -5)

    # 10. ATR 收縮後放大（爆發前兆）
    if len(df) >= 10:
        atr_now  = float(df["ATR"].iloc[-1])
        atr_prev = float(df["ATR"].iloc[-10:-1].mean())
        conds["atr_expand"] = atr_now > atr_prev * 0.9
    else:
        conds["atr_expand"] = False

    tech_score = sum(conds.values()) / len(conds) * 100

    # ── 訊號判定 ──
    must_buy   = conds["pct_b_low"] and conds["rsi_cross"]
    must_watch = conds["pct_b_low"]

    if must_buy and tech_score >= 60:
        signal = "BUY"
    elif must_watch and tech_score >= 30:
        signal = "WATCH"
    else:
        return None

    return {"signal": signal, "tech_score": tech_score, "conds": conds}

# ═══════════════════════════════════════════════════════
# 回測（含停損/停利）
# ═══════════════════════════════════════════════════════
def backtest(df: pd.DataFrame, p: dict) -> dict:
    wins, returns = 0, []
    hold   = p.get("hold_days", 10)
    sl_pct = p.get("stop_loss_pct", 0.05)
    tp_pct = p.get("take_profit_pct", 0.10)

    for i in range(40, len(df) - hold - 1):
        pb_ok = df["pct_b"].iloc[i-5:i].min() < p["pct_b"]
        rs_cross = (df["RSI_S"].iloc[i-1] <= df["RSI_L"].iloc[i-1] and
                    df["RSI_S"].iloc[i]   >  df["RSI_L"].iloc[i])
        if not (pb_ok and rs_cross):
            continue

        entry = float(df["Close"].iloc[i])
        sl    = entry * (1 - sl_pct)
        tp    = entry * (1 + tp_pct)
        ret   = None

        for j in range(1, hold + 1):
            lo = float(df["Low"].iloc[i+j])
            hi = float(df["High"].iloc[i+j])
            if lo <= sl: ret = -sl_pct; break
            if hi >= tp: ret = tp_pct;  break

        if ret is None:
            ret = float(df["Close"].iloc[i+hold]) / entry - 1

        returns.append(ret)
        if ret > 0: wins += 1

    n = len(returns)
    if n == 0:
        return {"win_rate": 0.0, "avg_return": 0.0, "trades": 0, "sharpe": 0.0}

    arr    = np.array(returns)
    sharpe = arr.mean() / (arr.std() + 1e-9) * np.sqrt(252 / hold)
    return {"win_rate": wins/n*100, "avg_return": arr.mean()*100,
            "trades": n, "sharpe": sharpe}

# ═══════════════════════════════════════════════════════
# 單一股票完整分析
# ═══════════════════════════════════════════════════════
def analyze_one(code: str, raw_df: pd.DataFrame, p: dict,
                fetch_fund: bool = True) -> Optional[ScanResult]:
    df = get_single_df(raw_df, code)
    if df is None:
        return None
    try:
        df = calc_indicators(df, p)
    except Exception:
        return None

    sig = generate_signal_score(df, p)
    if sig is None:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    price      = float(last["Close"])
    change_pct = (price / float(prev["Close"]) - 1) * 100
    vol_ratio  = float(last["Vol_Ratio"]) if not np.isnan(last["Vol_Ratio"]) else 0
    stop       = float(last["Lower"])
    target     = float(last["Upper"])
    rr         = (target - price) / max(price - stop, 0.01)

    bt = backtest(df, p)

    # 基本面（可選，耗時較長）
    fund = Fundamentals()
    news = []
    if fetch_fund:
        try:
            fund = fetch_fundamentals(code)
            mom, yoy = fetch_revenue(code)
            fund.rev_mom = mom
            fund.rev_yoy = yoy
            news = fetch_news(code, STOCK_DICT.get(code, code))
            fund.news = news
        except Exception:
            pass

    # 綜合評分（技術 60% + 基本面 40%）
    total_score = sig["tech_score"] * 0.6 + fund.fund_score * 0.4

    return ScanResult(
        code=code, name=STOCK_DICT.get(code, code),
        signal=sig["signal"],
        tech_score=round(sig["tech_score"], 1),
        fund_score=round(fund.fund_score, 1),
        total_score=round(total_score, 1),
        price=round(price, 2), change_pct=round(change_pct, 2),
        vol_ratio=round(vol_ratio, 2),
        stop=round(stop, 2), target=round(target, 2),
        rr_ratio=round(rr, 2),
        win_rate=round(bt["win_rate"], 1),
        avg_return=round(bt["avg_return"], 2),
        trades=bt["trades"],
        bb_pos=round(float(last["pct_b"]), 3),
        rsi_s=round(float(last["RSI_S"]), 1),
        rsi_l=round(float(last["RSI_L"]), 1),
        fundamentals=fund, df=df
    )

# ═══════════════════════════════════════════════════════
# Discord 推播（三種播報模式）
# ═══════════════════════════════════════════════════════
def _disc_color(signal, score):
    if signal == "BUY" and score >= 75: return 0x00ff88
    if signal == "BUY":                 return 0x00cc6a
    return 0xffd93d

def build_payload_morning(results: list) -> dict:
    """早盤播報：精簡清單 + 今日重點觀察"""
    buy_r = [r for r in results if r.signal == "BUY"]
    now   = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")

    fields = []
    for r in sorted(buy_r, key=lambda x: -x.total_score)[:8]:
        fs  = r.fundamentals
        row = (
            f"`{r.code}` **{r.name}**  "
            f"現價 `{r.price}`  "
            f"目標 `{r.target}`  停損 `{r.stop}`\n"
            f"綜合分 `{r.total_score:.0f}`  勝率 `{r.win_rate:.1f}%`  "
            f"量比 `{r.vol_ratio:.1f}x`  "
            f"PE `{fs.pe:.1f}` " if fs.pe else ""
        )
        fields.append({"name": f"{'💎' if r.total_score>=75 else '📈'} {r.code} {r.name}",
                        "value": row[:1024], "inline": False})

    return {
        "username": "🌅 AI 狙擊手｜早盤播報",
        "embeds": [{
            "title": f"🌅 早盤掃描戰報｜{now}",
            "description": (
                f"> 📡 掃描 **{len(results)}** 檔  "
                f"｜ BUY **{len(buy_r)}** 檔  "
                f"｜ 平均勝率 **{np.mean([r.win_rate for r in buy_r]):.1f}%**\n"
                if buy_r else "> 今日無 BUY 訊號\n"
            ),
            "color": 0x4d9fff,
            "fields": fields[:8],
            "footer": {"text": "台股 AI 狙擊手 Pro MAX v4.0 · 早盤播報"},
            "timestamp": datetime.datetime.utcnow().isoformat()
        }]
    }

def build_payload_intraday(results: list) -> dict:
    """盤中播報：即時訊號提醒"""
    new_buy = [r for r in results if r.signal == "BUY"]
    now = datetime.datetime.now().strftime("%H:%M")
    embeds = [{
        "title": f"⚡ 盤中即時訊號｜{now}",
        "description": f"掃描到 **{len(new_buy)}** 個 BUY 訊號",
        "color": 0xffd93d,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }]
    for r in sorted(new_buy, key=lambda x: -x.total_score)[:5]:
        chg_icon = "🔺" if r.change_pct >= 0 else "🔻"
        embeds.append({
            "title": f"⚡ {r.code} {r.name}",
            "color": _disc_color(r.signal, r.total_score),
            "fields": [
                {"name": "價格", "value": f"```\n現價  {r.price}\n{chg_icon}漲跌  {r.change_pct:+.2f}%\n目標  {r.target}\n停損  {r.stop}\n```", "inline": True},
                {"name": "量能", "value": f"```\n量比  {r.vol_ratio:.2f}x\n%B   {r.bb_pos:.3f}\nRSI  {r.rsi_s:.1f}/{r.rsi_l:.1f}\n```", "inline": True},
                {"name": "評分", "value": f"```\n綜合  {r.total_score:.1f}\n技術  {r.tech_score:.1f}\n基本  {r.fund_score:.1f}\n勝率  {r.win_rate:.1f}%\n```", "inline": True},
            ],
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
    return {"username": "⚡ AI 狙擊手｜盤中播報", "embeds": embeds[:5]}

def build_payload_close(results: list, meta: dict) -> dict:
    """收盤播報：完整戰報 + 基本面 + 新聞"""
    buy_r  = [r for r in results if r.signal == "BUY"]
    top5   = sorted(buy_r, key=lambda x: -x.total_score)[:5]
    now    = datetime.datetime.now().strftime("%Y/%m/%d")
    embeds = []

    # 摘要
    avg_wr  = np.mean([r.win_rate for r in buy_r]) if buy_r else 0
    avg_rr  = np.mean([r.rr_ratio for r in buy_r]) if buy_r else 0
    embeds.append({
        "title": f"📊 收盤完整戰報｜{now}",
        "description": (
            f"```yaml\n"
            f"掃描標的: {meta.get('total',0):>6}\n"
            f"BUY 訊號: {len(buy_r):>6}\n"
            f"平均勝率: {avg_wr:>5.1f}%\n"
            f"平均盈虧: {avg_rr:>5.2f}x\n"
            f"掃描耗時: {meta.get('elapsed',0):>5.0f}s\n"
            f"```"
        ),
        "color": 0x4d9fff,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "footer": {"text": "台股 AI 狙擊手 Pro MAX v4.0 · 收盤戰報"}
    })

    # 個股詳細（含基本面）
    for r in top5:
        f = r.fundamentals
        wr_bar = "█" * int(r.win_rate/10) + "░" * (10-int(r.win_rate/10))
        news_text = ""
        for n in f.news[:3]:
            icon = "🟢" if n["sentiment"]=="pos" else ("🔴" if n["sentiment"]=="neg" else "⚪")
            news_text += f"{icon} {n['title'][:40]}…\n"

        fund_text = ""
        if f.pe:           fund_text += f"PE {f.pe:.1f}  "
        if f.pb:           fund_text += f"PB {f.pb:.2f}  "
        if f.eps_growth:   fund_text += f"EPS成長 {f.eps_growth:+.1f}%  "
        if f.gross_margin: fund_text += f"毛利 {f.gross_margin:.1f}%  "
        if f.op_margin:    fund_text += f"營益 {f.op_margin:.1f}%  "
        if f.dividend_yield: fund_text += f"殖利率 {f.dividend_yield:.1f}%  "
        if f.rev_mom:      fund_text += f"\n月增率 {f.rev_mom:+.1f}%  "
        if f.rev_yoy:      fund_text += f"年增率 {f.rev_yoy:+.1f}%"

        embed = {
            "title": f"{'💎' if r.total_score>=75 else '📈'} {r.code} {r.name}  綜合 {r.total_score:.0f}分",
            "color": _disc_color(r.signal, r.total_score),
            "fields": [
                {"name": "📊 技術面",
                 "value": f"```diff\n+ 現價  {r.price}\n+ 目標  {r.target}\n- 停損  {r.stop}\n  盈虧比 {r.rr_ratio:.2f}x\n  量比  {r.vol_ratio:.2f}x\n```",
                 "inline": True},
                {"name": "🔬 回測",
                 "value": f"```\n勝率 {r.win_rate:.1f}%\n{wr_bar}\n均報酬 {r.avg_return:+.2f}%\n樣本  {r.trades}次\n技術分 {r.tech_score:.0f}\n```",
                 "inline": True},
                {"name": "💹 基本面",
                 "value": f"```ini\n{fund_text[:200] if fund_text else '資料不足'}\n```",
                 "inline": False},
            ],
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        if news_text:
            embed["fields"].append(
                {"name": "📰 最新新聞", "value": news_text[:500], "inline": False}
            )
        embeds.append(embed)

    if not top5:
        embeds.append({"title": "📉 今日無高分 BUY 標的", "color": 0xff3b6b,
                        "description": "建議等待下一個機會"})

    return {"username": "📊 AI 狙擊手｜收盤戰報", "embeds": embeds[:10]}

def send_discord(payload: dict, webhook_url: str) -> tuple:
    if not webhook_url: return False, "未設定 Webhook"
    try:
        url = webhook_url.replace("discordapp.com", "discord.com").strip()
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code in [200, 204]: return True, "推播成功"
        return False, f"HTTP {r.status_code}: {r.text[:80]}"
    except Exception as e:
        return False, str(e)

# ═══════════════════════════════════════════════════════
# 核心掃描函式（排程器呼叫）
# ═══════════════════════════════════════════════════════
def run_scan(codes: list, params: dict, webhook: str,
             mode: str = "close", fetch_fund: bool = True,
             min_score: float = 0.0) -> list:
    """
    mode: 'morning' | 'intraday' | 'close'
    """
    batches    = [codes[i:i+BATCH_SIZE] for i in range(0, len(codes), BATCH_SIZE)]
    all_results= []
    t0         = time.time()

    for batch in batches:
        raw = fetch_batch(tuple(batch))
        if raw.empty: continue
        for code in batch:
            try:
                r = analyze_one(code, raw, params, fetch_fund=fetch_fund)
                if r and r.total_score >= min_score:
                    all_results.append(r)
            except Exception:
                continue

    all_results.sort(key=lambda x: (0 if x.signal=="BUY" else 1, -x.total_score))

    elapsed = time.time() - t0
    meta = {"total": len(codes), "elapsed": elapsed,
            "buy_count": sum(1 for r in all_results if r.signal=="BUY"),
            "watch_count": sum(1 for r in all_results if r.signal=="WATCH"),
            "time_str": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}

    # 更新 session state（thread-safe 寫入）
    st.session_state.scan_results   = all_results
    st.session_state.scan_meta      = meta
    st.session_state.last_scan_time = datetime.datetime.now()

    # Discord 推播
    if webhook:
        if mode == "morning":
            payload = build_payload_morning(all_results)
        elif mode == "intraday":
            payload = build_payload_intraday(all_results)
        else:
            payload = build_payload_close(all_results, meta)

        ok, msg = send_discord(payload, webhook)
        log_entry = {
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
            "mode": mode, "results": len(all_results),
            "buy": meta["buy_count"], "status": "✅" if ok else f"❌ {msg}"
        }
        st.session_state.sched_log.insert(0, log_entry)
        st.session_state.sched_log = st.session_state.sched_log[:50]

    return all_results

# ═══════════════════════════════════════════════════════
# APScheduler 排程管理
# ═══════════════════════════════════════════════════════
def start_scheduler(codes, params, webhook, fetch_fund, min_score,
                    interval_min, morning_time, close_time,
                    enable_morning, enable_intraday, enable_close):
    """啟動背景排程器"""
    if st.session_state.sched_running:
        return

    scheduler = BackgroundScheduler(timezone="Asia/Taipei")

    # 早盤播報（固定時間）
    if enable_morning:
        h, m = map(int, morning_time.split(":"))
        scheduler.add_job(
            lambda: run_scan(codes, params, webhook, "morning", fetch_fund, min_score),
            CronTrigger(hour=h, minute=m, day_of_week="mon-fri"),
            id="morning", replace_existing=True
        )

    # 盤中定時掃描
    if enable_intraday:
        scheduler.add_job(
            lambda: run_scan(codes, params, webhook, "intraday", False, min_score),
            IntervalTrigger(minutes=interval_min),
            id="intraday", replace_existing=True
        )

    # 收盤完整播報
    if enable_close:
        h2, m2 = map(int, close_time.split(":"))
        scheduler.add_job(
            lambda: run_scan(codes, params, webhook, "close", fetch_fund, min_score),
            CronTrigger(hour=h2, minute=m2, day_of_week="mon-fri"),
            id="close", replace_existing=True
        )

    scheduler.start()
    st.session_state.scheduler     = scheduler
    st.session_state.sched_running = True

def stop_scheduler():
    if st.session_state.scheduler:
        try: st.session_state.scheduler.shutdown(wait=False)
        except Exception: pass
    st.session_state.scheduler     = None
    st.session_state.sched_running = False

def get_next_jobs() -> list:
    if not st.session_state.sched_running or not st.session_state.scheduler:
        return []
    try:
        jobs = st.session_state.scheduler.get_jobs()
        return [(j.id, j.next_run_time.strftime("%H:%M:%S") if j.next_run_time else "—") for j in jobs]
    except Exception:
        return []

# ═══════════════════════════════════════════════════════
# 繪圖
# ═══════════════════════════════════════════════════════
def plot_chart(r: ScanResult) -> go.Figure:
    df  = r.df.tail(120)
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True,
        vertical_spacing=0.015,
        row_heights=[0.52, 0.18, 0.15, 0.15],
        subplot_titles=["", "RSI", "MACD", "Volume"]
    )

    # K 線
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#00ff88", increasing_fillcolor="rgba(0,255,136,0.7)",
        decreasing_line_color="#ff3b6b", decreasing_fillcolor="rgba(255,59,107,0.7)",
        name="K線", line_width=0.8
    ), row=1, col=1)

    # BB
    fig.add_trace(go.Scatter(x=df.index, y=df["Upper"], name="BB上",
        line=dict(color="rgba(255,217,61,0.6)", width=1, dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Lower"], name="BB下",
        line=dict(color="rgba(255,217,61,0.6)", width=1, dash="dot"),
        fill="tonexty", fillcolor="rgba(255,217,61,0.03)"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MA"], name="MA",
        line=dict(color="rgba(77,159,255,0.8)", width=1.2)), row=1, col=1)

    # 停損/目標
    fig.add_hline(y=r.stop,   line_dash="dash", line_color="#ff3b6b", line_width=1,
                  annotation_text=f"  停損 {r.stop}", row=1, col=1)
    fig.add_hline(y=r.target, line_dash="dash", line_color="#00ff88", line_width=1,
                  annotation_text=f"  目標 {r.target}", row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI_S"], name="RSI短",
        line=dict(color="#4d9fff", width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI_L"], name="RSI長",
        line=dict(color="#a855f7", width=1.5)), row=2, col=1)
    for level in [30, 70]:
        fig.add_hline(y=level, line_dash="dot", line_color="rgba(255,255,255,0.15)",
                      line_width=0.8, row=2, col=1)

    # MACD
    hist_colors = ["rgba(0,255,136,0.7)" if v >= 0 else "rgba(255,59,107,0.7)"
                   for v in df["MACD_hist"]]
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"], marker_color=hist_colors,
        name="MACD Hist", showlegend=False), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
        line=dict(color="#4d9fff", width=1)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_sig"], name="Signal",
        line=dict(color="#ff3b6b", width=1)), row=3, col=1)

    # Volume
    vol_colors = ["rgba(0,204,106,0.7)" if c >= o else "rgba(204,34,68,0.7)"
                  for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=vol_colors,
        name="Vol", showlegend=False), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["Vol_MA"], name="Vol MA",
        line=dict(color="#ffd93d", width=1.2)), row=4, col=1)

    fig.update_layout(
        height=650, paper_bgcolor="#060b14", plot_bgcolor="#0a1020",
        font=dict(family="JetBrains Mono", color="#4a6080", size=9),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.01, x=0, font_size=9, bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=15, b=10, l=55, r=90),
    )
    for i in range(1, 5):
        ax = f"yaxis{'' if i==1 else i}"
        xx = f"xaxis{'' if i==1 else i}"
        fig.update_layout(**{
            ax: dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.07)"),
            xx: dict(gridcolor="rgba(255,255,255,0.04)", linecolor="rgba(255,255,255,0.07)")
        })
    return fig

# ═══════════════════════════════════════════════════════
# 側邊欄 UI
# ═══════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:20px 0 12px'>
        <div style='font-size:2.2rem;margin-bottom:4px'>🎯</div>
        <div style='font-weight:900;color:#00ff88;font-size:1rem;letter-spacing:0.06em'>AI SNIPER PRO</div>
        <div style='font-size:0.6rem;color:#4a6080;letter-spacing:0.2em;margin-top:2px'>TAIWAN STOCK · v4.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ── 掃描範圍 ──
    st.markdown("**📡 掃描範圍**")
    scan_mode = st.selectbox("模式", ["全上市櫃 (~1000檔)", "前 300 檔", "前 100 檔（快速）", "自選清單"],
                             label_visibility="collapsed")
    custom_list = ""
    if scan_mode == "自選清單":
        custom_list = st.text_area("代號（逗號分隔）", placeholder="2330, 2317, 2454",
                                   height=70, label_visibility="collapsed")

    st.divider()

    # ── 策略參數 ──
    st.markdown("**⚙️ 技術策略**")
    c1, c2 = st.columns(2)
    with c1:
        bb_period = st.number_input("BB週期", 10, 50, 20, step=1)
        rsi_short = st.number_input("RSI短", 3, 14, 6, step=1)
    with c2:
        bb_std    = st.number_input("BB倍數", 1.0, 3.0, 2.0, step=0.1)
        rsi_long  = st.number_input("RSI長", 10, 30, 12, step=1)

    pct_b_thr = st.slider("%B 超賣門檻", 0.0, 0.5, 0.2, step=0.05)
    vol_mult  = st.slider("爆量倍數", 0.5, 3.0, 1.2, step=0.1)
    grace     = st.slider("訊號緩衝天數", 1, 7, 3)

    st.divider()
    st.markdown("**🔬 回測參數**")
    hold_days      = st.slider("持有天數", 3, 30, 10)
    stop_loss_pct  = st.slider("停損", 0.02, 0.15, 0.05, step=0.01, format="%.2f")
    take_profit_pct= st.slider("停利", 0.05, 0.30, 0.10, step=0.01, format="%.2f")

    st.divider()
    st.markdown("**💹 基本面設定**")
    fetch_fund = st.checkbox("抓取基本面資料", value=True,
                             help="開啟後每檔多約 0.5s，全掃描會較慢")
    min_score  = st.slider("最低綜合評分", 0, 80, 50, step=5,
                            help="0=不篩選，50=只顯示中等以上標的")

    st.divider()

    # ── Discord ──
    st.markdown("**🔔 Discord 推播**")
    webhook = st.text_input("Webhook", type="password",
                             placeholder="https://discord.com/api/webhooks/...",
                             label_visibility="collapsed")

    if st.button("🛠 測試推播", use_container_width=True):
        test_p = {"username": "🎯 AI 狙擊手 Pro MAX",
                  "embeds": [{"title": "✅ 系統連線正常",
                              "description": "台股 AI 狙擊手 Pro MAX v4.0 準備就緒！",
                              "color": 0x00ff88,
                              "timestamp": datetime.datetime.utcnow().isoformat()}]}
        ok, msg = send_discord(test_p, webhook)
        st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")

    st.divider()

    # ── 自動排程 ──
    st.markdown("**⏰ 全自動排程**")

    enable_morning  = st.checkbox("早盤播報", value=True)
    morning_time    = st.text_input("早盤時間", value="08:50", label_visibility="collapsed") if enable_morning else "08:50"

    enable_intraday = st.checkbox("盤中定時掃描", value=True)
    interval_min    = st.slider("掃描間隔(分)", 5, 60, 15) if enable_intraday else 15

    enable_close    = st.checkbox("收盤完整播報", value=True)
    close_time      = st.text_input("收盤時間", value="14:10", label_visibility="collapsed") if enable_close else "14:10"

    st.markdown("")
    col_s, col_p = st.columns(2)
    with col_s:
        if st.button("▶ 啟動排程", use_container_width=True,
                     disabled=st.session_state.sched_running):
            # 決定掃描清單
            if scan_mode == "自選清單":
                sc = [c.strip() for c in custom_list.replace("，",",").split(",")
                      if c.strip().isdigit()]
            elif scan_mode == "前 100 檔（快速）":
                sc = ALL_CODES[:100]
            elif scan_mode == "前 300 檔":
                sc = ALL_CODES[:300]
            else:
                sc = ALL_CODES

            params_snap = {
                "bb_period": bb_period, "bb_std": bb_std,
                "pct_b": pct_b_thr, "grace": grace,
                "rsi_short": rsi_short, "rsi_long": rsi_long,
                "vol_mult": vol_mult, "hold_days": hold_days,
                "stop_loss_pct": stop_loss_pct, "take_profit_pct": take_profit_pct
            }
            st.session_state.scan_codes   = sc
            st.session_state.scan_params  = params_snap
            st.session_state.auto_webhook = webhook

            start_scheduler(sc, params_snap, webhook, fetch_fund, min_score,
                            interval_min, morning_time, close_time,
                            enable_morning, enable_intraday, enable_close)
            st.success("排程已啟動！")
            st.rerun()

    with col_p:
        if st.button("⏹ 停止", use_container_width=True,
                     disabled=not st.session_state.sched_running):
            stop_scheduler()
            st.warning("排程已停止")
            st.rerun()

    # 排程狀態
    if st.session_state.sched_running:
        jobs = get_next_jobs()
        st.markdown(f"""
        <div class="sched-card">
            <div class="sched-row">
                <span class="sched-label">狀態</span>
                <span class="hero-live"><span class="hero-live-dot"></span>運行中</span>
            </div>
        """, unsafe_allow_html=True)
        for jid, nxt in jobs:
            label_map = {"morning": "早盤", "intraday": "盤中", "close": "收盤"}
            st.markdown(f"""
            <div class="sched-row">
                <span class="sched-label">{label_map.get(jid, jid)}</span>
                <span class="sched-val">{nxt}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.caption(f"📦 已載入 **{len(ALL_CODES)}** 檔標的")

# ═══════════════════════════════════════════════════════
# 主畫面
# ═══════════════════════════════════════════════════════
params = {
    "bb_period": bb_period, "bb_std": bb_std,
    "pct_b": pct_b_thr, "grace": grace,
    "rsi_short": rsi_short, "rsi_long": rsi_long,
    "vol_mult": vol_mult, "hold_days": hold_days,
    "stop_loss_pct": stop_loss_pct, "take_profit_pct": take_profit_pct
}

# Hero
sched_badge = (
    '<span class="hero-live"><span class="hero-live-dot"></span>排程運行中</span>'
    if st.session_state.sched_running else
    '<span style="font-family:JetBrains Mono;font-size:0.65rem;color:#4a6080">● 排程未啟動</span>'
)
last_t = (st.session_state.last_scan_time.strftime("%H:%M:%S")
          if st.session_state.last_scan_time else "—")

st.markdown(f"""
<div class="hero-wrap">
    <div style="display:flex;justify-content:space-between;align-items:flex-start">
        <div>
            <div class="hero-title">🎯 台股 AI 狙擊手 Pro MAX</div>
            <div class="hero-sub">MULTI-SIGNAL · FUNDAMENTAL FUSION · AUTO SCHEDULER · DISCORD BROADCAST v4.0</div>
        </div>
        <div style="text-align:right">
            {sched_badge}
            <div style="font-family:JetBrains Mono;font-size:0.65rem;color:#4a6080;margin-top:4px">
                上次掃描 {last_t}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 個股快速查詢 ──
with st.expander("🔍 個股快速查詢（含基本面）", expanded=False):
    qc1, qc2 = st.columns([3, 1])
    with qc1:
        qcode = st.text_input("代號", placeholder="例：2330", label_visibility="collapsed")
    with qc2:
        qbtn  = st.button("查詢", use_container_width=True)

    if qbtn and qcode.strip():
        code = qcode.strip()
        with st.spinner(f"分析 {code} 中..."):
            try:
                df_q = yf.download(f"{code}.TW", period="1y", interval="1d", progress=False)
                if df_q.empty:
                    st.error("查無資料")
                else:
                    df_q = calc_indicators(df_q, params)
                    last_q = df_q.iloc[-1]
                    prev_q = df_q.iloc[-2]
                    price_q = float(last_q["Close"])
                    chg_q   = (price_q / float(prev_q["Close"]) - 1) * 100

                    fund_q = fetch_fundamentals(code) if fetch_fund else Fundamentals()
                    mom_q, yoy_q = fetch_revenue(code)
                    news_q = fetch_news(code, STOCK_DICT.get(code, code))

                    # 評分
                    sig_q = generate_signal_score(df_q, params)
                    t_score = sig_q["tech_score"] if sig_q else 0

                    # Metrics
                    m = st.columns(6)
                    m[0].metric("現價", f"{price_q:.2f}", f"{chg_q:+.2f}%")
                    m[1].metric("量比", f"{float(last_q['Vol_Ratio']):.2f}x")
                    m[2].metric("技術分", f"{t_score:.0f}")
                    m[3].metric("基本分", f"{fund_q.fund_score:.0f}")
                    m[4].metric("PE", f"{fund_q.pe:.1f}" if fund_q.pe else "N/A")
                    m[5].metric("殖利率", f"{fund_q.dividend_yield:.1f}%" if fund_q.dividend_yield else "N/A")

                    # 基本面
                    st.markdown(f"""
                    <div class="fund-grid">
                        <div class="fund-cell"><div class="fund-key">本益比 PE</div>
                            <div class="fund-val">{f"{fund_q.pe:.1f}" if fund_q.pe else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">股淨比 PB</div>
                            <div class="fund-val">{f"{fund_q.pb:.2f}" if fund_q.pb else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">EPS (TTM)</div>
                            <div class="fund-val">{f"{fund_q.eps_ttm:.2f}" if fund_q.eps_ttm else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">EPS 成長率</div>
                            <div class="fund-val">{f"{fund_q.eps_growth:+.1f}%" if fund_q.eps_growth else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">毛利率</div>
                            <div class="fund-val">{f"{fund_q.gross_margin:.1f}%" if fund_q.gross_margin else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">營業利益率</div>
                            <div class="fund-val">{f"{fund_q.op_margin:.1f}%" if fund_q.op_margin else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">殖利率</div>
                            <div class="fund-val">{f"{fund_q.dividend_yield:.1f}%" if fund_q.dividend_yield else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">月增率</div>
                            <div class="fund-val">{f"{mom_q:+.1f}%" if mom_q else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">年增率</div>
                            <div class="fund-val">{f"{yoy_q:+.1f}%" if yoy_q else "—"}</div></div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 新聞
                    if news_q:
                        st.markdown("**📰 最新新聞**")
                        for n in news_q[:5]:
                            cls = n["sentiment"]
                            st.markdown(f"""
                            <div class="news-item {cls}">
                                <div class="news-title"><a href="{n['link']}" target="_blank"
                                    style="color:inherit;text-decoration:none">{n['title']}</a></div>
                                <div class="news-meta">{n['time']}</div>
                            </div>""", unsafe_allow_html=True)

                    # 圖表
                    mock_r = ScanResult(
                        code=code, name=STOCK_DICT.get(code, code),
                        signal=sig_q["signal"] if sig_q else "—",
                        tech_score=t_score, fund_score=fund_q.fund_score,
                        total_score=t_score*0.6+fund_q.fund_score*0.4,
                        price=round(price_q, 2), change_pct=round(chg_q, 2),
                        vol_ratio=round(float(last_q["Vol_Ratio"]), 2),
                        stop=round(float(last_q["Lower"]), 2),
                        target=round(float(last_q["Upper"]), 2),
                        rr_ratio=0, win_rate=0, avg_return=0, trades=0,
                        bb_pos=round(float(last_q["pct_b"]), 3),
                        rsi_s=round(float(last_q["RSI_S"]), 1),
                        rsi_l=round(float(last_q["RSI_L"]), 1),
                        fundamentals=fund_q, df=df_q
                    )
                    st.plotly_chart(plot_chart(mock_r), use_container_width=True)

            except Exception as e:
                st.error(f"錯誤：{e}")

st.divider()

# ── 手動掃描按鈕 ──
scan_btn = st.button("🔥 立即手動掃描", type="primary", use_container_width=True)

if scan_btn:
    if scan_mode == "自選清單":
        target_codes = [c.strip() for c in custom_list.replace("，",",").split(",")
                        if c.strip().isdigit()]
    elif scan_mode == "前 100 檔（快速）":
        target_codes = ALL_CODES[:100]
    elif scan_mode == "前 300 檔":
        target_codes = ALL_CODES[:300]
    else:
        target_codes = ALL_CODES

    if not target_codes:
        st.error("掃描清單為空")
        st.stop()

    t0       = time.time()
    batches  = [target_codes[i:i+BATCH_SIZE] for i in range(0, len(target_codes), BATCH_SIZE)]
    n_bat    = len(batches)
    pbar     = st.progress(0, text="準備中...")
    stat_ph  = st.empty()
    all_res  = []

    for bi, batch in enumerate(batches):
        stat_ph.markdown(
            f"<span style='font-family:JetBrains Mono;font-size:0.75rem;color:#4a6080'>"
            f"⬇ 批次 {bi+1}/{n_bat}　{batch[0]}～{batch[-1]}</span>",
            unsafe_allow_html=True
        )
        raw = fetch_batch(tuple(batch))
        if raw.empty:
            pbar.progress((bi+1)/n_bat)
            continue

        batch_res = []
        for code in batch:
            r = analyze_one(code, raw, params, fetch_fund=fetch_fund)
            if r and r.total_score >= min_score:
                batch_res.append(r)

        all_res.extend(batch_res)
        pct = (bi+1)/n_bat
        stat_ph.markdown(
            f"<span style='font-family:JetBrains Mono;font-size:0.75rem;color:#00ff88'>"
            f"✓ 批次 {bi+1}/{n_bat} 完成　本批訊號 {len(batch_res)} 個</span>",
            unsafe_allow_html=True
        )
        pbar.progress(pct, text=f"掃描 {int(pct*100)}%")

    pbar.progress(1.0, text="✅ 掃描完成！")
    elapsed = time.time() - t0

    all_res.sort(key=lambda x: (0 if x.signal=="BUY" else 1, -x.total_score))
    buy_r = [r for r in all_res if r.signal=="BUY"]

    st.session_state.scan_results   = all_res
    st.session_state.last_scan_time = datetime.datetime.now()
    st.session_state.scan_meta = {
        "total": len(target_codes), "elapsed": elapsed,
        "buy_count": len(buy_r),
        "watch_count": sum(1 for r in all_res if r.signal=="WATCH"),
        "time_str": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    # Discord 推播
    if webhook:
        now_h = datetime.datetime.now().hour
        mode  = "morning" if now_h < 9 else ("close" if now_h >= 14 else "intraday")
        if mode == "morning":   payload = build_payload_morning(all_res)
        elif mode == "intraday":payload = build_payload_intraday(all_res)
        else:                   payload = build_payload_close(all_res, st.session_state.scan_meta)
        ok, msg = send_discord(payload, webhook)
        st.toast("✅ Discord 推播成功！" if ok else f"⚠️ {msg}", icon="🔔" if ok else "⚠️")

# ═══════════════════════════════════════════════════════
# 結果顯示
# ═══════════════════════════════════════════════════════
results = st.session_state.scan_results
meta    = st.session_state.scan_meta

if results or meta:
    buy_r   = [r for r in results if r.signal=="BUY"]
    watch_r = [r for r in results if r.signal=="WATCH"]
    avg_wr  = np.mean([r.win_rate for r in buy_r]) if buy_r else 0
    avg_sc  = np.mean([r.total_score for r in buy_r]) if buy_r else 0

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card b"><div class="kpi-label">掃描標的</div>
            <div class="kpi-val b">{meta.get('total',0)}</div></div>
        <div class="kpi-card g"><div class="kpi-label">BUY 訊號</div>
            <div class="kpi-val g">{meta.get('buy_count',0)}</div></div>
        <div class="kpi-card y"><div class="kpi-label">觀察清單</div>
            <div class="kpi-val y">{meta.get('watch_count',0)}</div></div>
        <div class="kpi-card p"><div class="kpi-label">平均勝率</div>
            <div class="kpi-val">{avg_wr:.1f}%</div></div>
        <div class="kpi-card w"><div class="kpi-label">平均綜合分</div>
            <div class="kpi-val">{avg_sc:.0f}</div></div>
        <div class="kpi-card {'g' if meta.get('elapsed',99)<60 else 'r'}">
            <div class="kpi-label">掃描耗時</div>
            <div class="kpi-val">{meta.get('elapsed',0):.0f}s</div></div>
    </div>
    """, unsafe_allow_html=True)

    if not results:
        st.info("本次掃描無符合標的，可降低「最低綜合評分」或放寬策略參數。")
    else:
        tab_buy, tab_watch, tab_all, tab_log = st.tabs([
            f"💎 BUY ({len(buy_r)})",
            f"👁 觀察 ({len(watch_r)})",
            f"📋 全部 ({len(results)})",
            f"📡 排程日誌"
        ])

        def render_result_list(res_list):
            for r in res_list:
                chg_cls = "style='color:#00ff88'" if r.change_pct >= 0 else "style='color:#ff3b6b'"
                sc_cls  = "score-high" if r.total_score>=70 else ("score-mid" if r.total_score>=50 else "score-low")
                badge   = f'<span class="badge badge-buy">BUY</span>' if r.signal=="BUY" else f'<span class="badge badge-watch">WATCH</span>'
                label   = (
                    f"{badge} &nbsp; <b>{r.code}</b> {r.name} &nbsp;"
                    f"<span style='font-family:JetBrains Mono;font-size:0.85rem' {chg_cls}>"
                    f"{r.price} {'▲' if r.change_pct>=0 else '▼'}{abs(r.change_pct):.2f}%</span>"
                    f"&nbsp; <span style='color:#4a6080;font-size:0.75rem'>綜合 {r.total_score:.0f}分 · 勝率 {r.win_rate:.1f}%</span>"
                )
                with st.expander(label, expanded=False):
                    # Metrics row
                    mc = st.columns(7)
                    mc[0].metric("現價",   f"{r.price}")
                    mc[1].metric("目標",   f"{r.target}", f"+{((r.target/r.price)-1)*100:.1f}%")
                    mc[2].metric("停損",   f"{r.stop}",   f"-{((r.price/r.stop)-1)*100:.1f}%")
                    mc[3].metric("盈虧比", f"{r.rr_ratio:.2f}x")
                    mc[4].metric("技術分", f"{r.tech_score:.0f}")
                    mc[5].metric("基本分", f"{r.fund_score:.0f}")
                    mc[6].metric("勝率",   f"{r.win_rate:.1f}%")

                    # 基本面
                    f = r.fundamentals
                    st.markdown(f"""
                    <div class="fund-grid" style="grid-template-columns:repeat(4,1fr)">
                        <div class="fund-cell"><div class="fund-key">PE</div>
                            <div class="fund-val">{f"{f.pe:.1f}" if f.pe else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">PB</div>
                            <div class="fund-val">{f"{f.pb:.2f}" if f.pb else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">EPS成長</div>
                            <div class="fund-val">{f"{f.eps_growth:+.1f}%" if f.eps_growth else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">毛利率</div>
                            <div class="fund-val">{f"{f.gross_margin:.1f}%" if f.gross_margin else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">營益率</div>
                            <div class="fund-val">{f"{f.op_margin:.1f}%" if f.op_margin else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">殖利率</div>
                            <div class="fund-val">{f"{f.dividend_yield:.1f}%" if f.dividend_yield else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">月增率</div>
                            <div class="fund-val">{f"{f.rev_mom:+.1f}%" if f.rev_mom else "—"}</div></div>
                        <div class="fund-cell"><div class="fund-key">年增率</div>
                            <div class="fund-val">{f"{f.rev_yoy:+.1f}%" if f.rev_yoy else "—"}</div></div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 新聞
                    if f.news:
                        for n in f.news[:4]:
                            cls = n.get("sentiment","neu")
                            st.markdown(f"""
                            <div class="news-item {cls}">
                                <div class="news-title">
                                    <a href="{n['link']}" target="_blank" style="color:inherit;text-decoration:none">
                                    {n['title']}</a></div>
                                <div class="news-meta">{n['time']}</div>
                            </div>""", unsafe_allow_html=True)

                    # 圖表
                    st.plotly_chart(plot_chart(r), use_container_width=True)

        with tab_buy:
            render_result_list(buy_r)

        with tab_watch:
            render_result_list(watch_r)

        with tab_all:
            rows = []
            for r in results:
                f = r.fundamentals
                rows.append({
                    "代號": r.code, "名稱": r.name, "訊號": r.signal,
                    "綜合分": r.total_score, "技術分": r.tech_score, "基本分": r.fund_score,
                    "現價": r.price, "漲跌%": r.change_pct,
                    "目標": r.target, "停損": r.stop, "盈虧比": r.rr_ratio,
                    "量比": r.vol_ratio, "勝率%": r.win_rate,
                    "PE": round(f.pe, 1) if f.pe else None,
                    "殖利率%": round(f.dividend_yield, 1) if f.dividend_yield else None,
                    "月增率%": round(f.rev_mom, 1) if f.rev_mom else None,
                })
            st.dataframe(
                pd.DataFrame(rows), use_container_width=True, hide_index=True,
                column_config={
                    "綜合分": st.column_config.ProgressColumn("綜合分", min_value=0, max_value=100, format="%.0f"),
                    "勝率%":  st.column_config.ProgressColumn("勝率%",  min_value=0, max_value=100, format="%.1f%%"),
                    "漲跌%":  st.column_config.NumberColumn("漲跌%",  format="%.2f%%"),
                    "盈虧比": st.column_config.NumberColumn("盈虧比", format="%.2fx"),
                }
            )

        with tab_log:
            st.markdown("**📡 排程執行日誌**（最新 50 筆）")
            log = st.session_state.sched_log
            if not log:
                st.info("尚無排程執行紀錄，請先啟動排程器。")
            else:
                log_rows = []
                for entry in log:
                    mode_map = {"morning": "🌅 早盤", "intraday": "⚡ 盤中", "close": "📊 收盤"}
                    log_rows.append({
                        "時間": entry["time"],
                        "模式": mode_map.get(entry["mode"], entry["mode"]),
                        "標的數": entry["results"],
                        "BUY": entry["buy"],
                        "狀態": entry["status"]
                    })
                st.dataframe(pd.DataFrame(log_rows), use_container_width=True, hide_index=True)

# ── Footer ──
st.divider()
st.markdown("""
<div style='text-align:center;font-family:JetBrains Mono;font-size:0.6rem;color:#2a3a50;padding:8px 0'>
    台股 AI 狙擊手 Pro MAX v4.0 · 僅供學術研究與技術開發 · 投資有風險，請自行判斷
</div>
""", unsafe_allow_html=True)
