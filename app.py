"""
╔══════════════════════════════════════════════════════════════╗
║         台股 AI 狙擊手 Pro MAX  v3.0                         ║
║  全上市掃描 | 並行加速 | 精準訊號 | 頂級UI | 專業Discord      ║
╚══════════════════════════════════════════════════════════════╝
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib3
import datetime
import concurrent.futures
import time
from dataclasses import dataclass
from typing import Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ══════════════════════════════════════════════
# 頁面配置 & 全域樣式
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="台股 AI 狙擊手 Pro",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&family=JetBrains+Mono:wght@400;700&display=swap');

/* 根字體 */
html, body, [class*="css"] {
    font-family: 'Noto Sans TC', sans-serif;
}

/* 主題色彩系統 */
:root {
    --bg-primary: #0a0e1a;
    --bg-card: #111827;
    --bg-elevated: #1a2235;
    --accent-green: #00ff88;
    --accent-red: #ff3b6b;
    --accent-yellow: #ffd93d;
    --accent-blue: #4d9fff;
    --text-primary: #e8edf5;
    --text-secondary: #8896b0;
    --border: rgba(255,255,255,0.07);
}

/* 強制深色背景 */
.stApp { background: #0a0e1a; }
.main .block-container { padding: 1.5rem 2rem; max-width: 100%; }

/* 標題區 */
.hero-title {
    font-size: 2.4rem;
    font-weight: 900;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #00ff88 0%, #4d9fff 50%, #a855f7 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.hero-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #8896b0;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

/* 統計卡片 */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-bottom: 1.5rem;
}
.stat-card {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 16px 20px;
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.stat-card.green::before { background: linear-gradient(90deg, #00ff88, transparent); }
.stat-card.red::before { background: linear-gradient(90deg, #ff3b6b, transparent); }
.stat-card.yellow::before { background: linear-gradient(90deg, #ffd93d, transparent); }
.stat-card.blue::before { background: linear-gradient(90deg, #4d9fff, transparent); }
.stat-card.purple::before { background: linear-gradient(90deg, #a855f7, transparent); }
.stat-label {
    font-size: 0.68rem;
    color: #8896b0;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 6px;
}
.stat-value {
    font-size: 1.8rem;
    font-weight: 900;
    color: #e8edf5;
    line-height: 1;
}
.stat-card.green .stat-value { color: #00ff88; }
.stat-card.red .stat-value { color: #ff3b6b; }

/* 訊號徽章 */
.badge-buy {
    display: inline-block;
    background: linear-gradient(135deg, #00ff88, #00cc6a);
    color: #0a1a10;
    font-weight: 700;
    font-size: 0.7rem;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.1em;
}
.badge-watch {
    display: inline-block;
    background: linear-gradient(135deg, #ffd93d, #ffaa00);
    color: #1a1000;
    font-weight: 700;
    font-size: 0.7rem;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.1em;
}

/* 結果表格美化 */
.stock-table { width: 100%; border-collapse: collapse; }
.stock-table th {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: #8896b0;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.stock-table td {
    padding: 12px 14px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 0.88rem;
    color: #e8edf5;
}
.stock-table tr:hover td { background: rgba(255,255,255,0.03); }
.price-green { color: #00ff88; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.price-red { color: #ff3b6b; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
.mono { font-family: 'JetBrains Mono', monospace; }

/* 側邊欄 */
section[data-testid="stSidebar"] {
    background: #0d1220 !important;
    border-right: 1px solid rgba(255,255,255,0.07);
}
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stNumberInput label,
section[data-testid="stSidebar"] label {
    color: #8896b0 !important;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-family: 'JetBrains Mono', monospace !important;
}

/* 掃描按鈕 */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00ff88, #00cc6a) !important;
    color: #0a1a10 !important;
    font-weight: 900 !important;
    font-size: 1rem !important;
    letter-spacing: 0.05em !important;
    border: none !important;
    height: 52px !important;
    border-radius: 10px !important;
    transition: all 0.2s !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 25px rgba(0,255,136,0.3) !important;
}

/* 個股查詢按鈕 */
.stButton > button:not([kind="primary"]) {
    background: #1a2235 !important;
    color: #e8edf5 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
}

/* 分隔線 */
hr { border-color: rgba(255,255,255,0.07) !important; }

/* Expander */
.streamlit-expanderHeader {
    background: #111827 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}

/* 進度條 */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #00ff88, #4d9fff) !important;
}

/* Alert/Info */
.stAlert { border-radius: 10px !important; }

/* Metric */
[data-testid="metric-container"] {
    background: #111827;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 16px !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 資料結構
# ══════════════════════════════════════════════
@dataclass
class ScanResult:
    code: str
    name: str
    signal: str          # BUY / WATCH
    price: float
    change_pct: float    # 今日漲跌幅
    vol_ratio: float
    stop: float
    target: float
    rr_ratio: float      # 盈虧比
    win_rate: float      # 回測勝率 (%)
    avg_return: float    # 平均報酬
    trades: int          # 回測次數
    bb_position: float   # %B 值
    rsi_s: float
    rsi_l: float
    df: pd.DataFrame

# ══════════════════════════════════════════════
# 1. 抓取全台股清單
# ══════════════════════════════════════════════
@st.cache_data(ttl=86400)
def get_all_stock_names() -> dict:
    names = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(
            "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
            headers=headers, timeout=15, verify=False
        )
        if r.status_code == 200:
            for item in r.json():
                c = item.get("Code", "")
                if len(c) == 4 and c.isdigit():
                    names[c] = item["Name"]
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
    # fallback
    if not names:
        names = {"2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2308": "台達電", "2382": "廣達"}
    return names

STOCK_DICT = get_all_stock_names()
ALL_CODES = sorted(STOCK_DICT.keys())

# ══════════════════════════════════════════════
# 2. 高效批次下載（分批 + 快取）
# ══════════════════════════════════════════════
BATCH_SIZE = 50   # 每批 50 檔，避免 yfinance 超時

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_batch(codes_tuple: tuple) -> pd.DataFrame:
    """下載一批股票，快取 1 小時"""
    tickers = [f"{c}.TW" for c in codes_tuple]
    try:
        df = yf.download(
            tickers, period="1y", interval="1d",
            group_by="ticker", threads=True,
            progress=False, timeout=30
        )
        return df
    except Exception:
        return pd.DataFrame()

def get_single_df(raw: pd.DataFrame, code: str) -> Optional[pd.DataFrame]:
    """從批次結果中取出單一股票的 OHLCV"""
    ticker = f"{code}.TW"
    try:
        if ticker in raw.columns.get_level_values(0):
            sub = raw[ticker].dropna(subset=["Close"])
            return sub if len(sub) >= 50 else None
        elif "Close" in raw.columns:
            sub = raw.dropna(subset=["Close"])
            return sub if len(sub) >= 50 else None
    except Exception:
        pass
    return None

# ══════════════════════════════════════════════
# 3. 指標計算（向量化，速度最快）
# ══════════════════════════════════════════════
def calc_indicators(df: pd.DataFrame, p: dict) -> pd.DataFrame:
    df = df.copy()
    c = df["Close"].squeeze()

    # Bollinger Bands
    ma = c.rolling(p["bb_period"]).mean()
    std = c.rolling(p["bb_period"]).std(ddof=0)
    df["MA"]    = ma
    df["Upper"] = ma + p["bb_std"] * std
    df["Lower"] = ma - p["bb_std"] * std
    df["pct_b"] = (c - df["Lower"]) / (df["Upper"] - df["Lower"])

    # RSI（向量化）
    def rsi_vec(s, period):
        delta = s.diff()
        up   = delta.clip(lower=0)
        down = (-delta).clip(lower=0)
        gain = up.ewm(com=period-1, adjust=False).mean()
        loss = down.ewm(com=period-1, adjust=False).mean()
        rs   = gain / loss.replace(0, np.nan)
        return 100 - 100 / (1 + rs)

    df["RSI_S"]  = rsi_vec(c, p["rsi_short"])
    df["RSI_L"]  = rsi_vec(c, p["rsi_long"])
    df["MACD_line"], df["MACD_sig"] = _macd(c)
    df["Vol_MA"] = df["Volume"].rolling(20).mean()
    df["ATR"]    = _atr(df, 14)
    return df

def _macd(c, fast=12, slow=26, sig=9):
    ema_f = c.ewm(span=fast, adjust=False).mean()
    ema_s = c.ewm(span=slow, adjust=False).mean()
    line  = ema_f - ema_s
    signal = line.ewm(span=sig, adjust=False).mean()
    return line, signal

def _atr(df, period=14):
    h = df["High"].squeeze()
    l = df["Low"].squeeze()
    c = df["Close"].squeeze()
    tr = pd.concat([h-l, (h-c.shift()).abs(), (l-c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean()

# ══════════════════════════════════════════════
# 4. 精準訊號引擎（多重確認）
# ══════════════════════════════════════════════
def generate_signal(df: pd.DataFrame, p: dict) -> Optional[dict]:
    """
    多重過濾條件：
    1. %B 低位（近 N 日曾觸及超賣）
    2. RSI 黃金交叉（允許 grace 天緩衝）
    3. 成交量放大
    4. MACD 方向確認
    5. 收盤站回 MA（趨勢確認）
    """
    if len(df) < 60:
        return None

    last = df.iloc[-1]
    N    = p["grace"]  # 緩衝天數

    # --- 條件 1：%B 低位（近 N 日最低 %B < 門檻）
    recent_pct_b = df["pct_b"].iloc[-N:].min()
    cond1 = recent_pct_b < p["pct_b"]

    # --- 條件 2：RSI 黃金交叉（近 N 日內發生）
    cross_found = False
    for i in range(-N, 0):
        if (df["RSI_S"].iloc[i-1] <= df["RSI_L"].iloc[i-1] and
                df["RSI_S"].iloc[i] > df["RSI_L"].iloc[i]):
            cross_found = True
            break
    cond2 = cross_found

    # --- 條件 3：量能放大
    vol_ratio = last["Volume"] / last["Vol_MA"] if last["Vol_MA"] > 0 else 0
    cond3 = vol_ratio >= p["vol_mult"]

    # --- 條件 4：MACD 訊號
    macd_ok = last["MACD_line"] > last["MACD_sig"]

    # --- 條件 5：收盤 > MA（趨勢朝上）
    trend_ok = last["Close"] > last["MA"]

    # 評分系統（5 分滿）
    score = sum([cond1, cond2, cond3, macd_ok, trend_ok])

    if score >= 4 and cond1 and cond2:
        return {"signal": "BUY", "score": score}
    elif score >= 2 and cond1:
        return {"signal": "WATCH", "score": score}
    return None

# ══════════════════════════════════════════════
# 5. 回測引擎（含停損機制）
# ══════════════════════════════════════════════
def backtest(df: pd.DataFrame, p: dict) -> dict:
    """
    真實回測：含停損 / 停利，計算勝率、平均報酬、夏普比率
    """
    wins, losses, returns = 0, 0, []
    hold_days = p.get("hold_days", 10)
    stop_pct  = p.get("stop_loss_pct", 0.05)   # 5% 停損
    target_pct = p.get("take_profit_pct", 0.10) # 10% 停利

    for i in range(40, len(df) - hold_days - 1):
        # 觸發條件（同訊號邏輯）
        pb_ok = df["pct_b"].iloc[i-5:i].min() < p["pct_b"]
        rs_cross = (df["RSI_S"].iloc[i-1] <= df["RSI_L"].iloc[i-1] and
                    df["RSI_S"].iloc[i] > df["RSI_L"].iloc[i])
        if not (pb_ok and rs_cross):
            continue

        entry = df["Close"].iloc[i]
        stop  = entry * (1 - stop_pct)
        tp    = entry * (1 + target_pct)
        ret   = None

        for j in range(1, hold_days + 1):
            low  = df["Low"].iloc[i+j]
            high = df["High"].iloc[i+j]
            if low <= stop:
                ret = -stop_pct
                break
            if high >= tp:
                ret = target_pct
                break

        if ret is None:
            ret = (df["Close"].iloc[i+hold_days] / entry) - 1

        returns.append(ret)
        if ret > 0: wins += 1
        else:       losses += 1

    total = len(returns)
    if total == 0:
        return {"win_rate": 0.0, "avg_return": 0.0, "sharpe": 0.0, "trades": 0}

    arr = np.array(returns)
    sharpe = (arr.mean() / (arr.std() + 1e-9)) * np.sqrt(252 / p.get("hold_days", 10))

    return {
        "win_rate":   wins / total * 100,
        "avg_return": arr.mean() * 100,
        "sharpe":     sharpe,
        "trades":     total
    }

# ══════════════════════════════════════════════
# 6. 單一股票分析
# ══════════════════════════════════════════════
def analyze_one(code: str, raw_df: pd.DataFrame, p: dict) -> Optional[ScanResult]:
    df = get_single_df(raw_df, code)
    if df is None:
        return None
    try:
        df = calc_indicators(df, p)
    except Exception:
        return None

    sig = generate_signal(df, p)
    if sig is None:
        return None

    last = df.iloc[-1]
    prev = df.iloc[-2]

    price      = float(last["Close"])
    change_pct = (price / float(prev["Close"]) - 1) * 100
    vol_ratio  = float(last["Volume"] / last["Vol_MA"]) if last["Vol_MA"] > 0 else 0
    stop       = float(last["Lower"])
    target     = float(last["Upper"])
    rr         = (target - price) / (price - stop) if (price - stop) > 0 else 0

    bt = backtest(df, p)

    return ScanResult(
        code=code, name=STOCK_DICT.get(code, code),
        signal=sig["signal"], price=round(price, 2),
        change_pct=round(change_pct, 2),
        vol_ratio=round(vol_ratio, 2),
        stop=round(stop, 2), target=round(target, 2),
        rr_ratio=round(rr, 2),
        win_rate=round(bt["win_rate"], 1),
        avg_return=round(bt["avg_return"], 2),
        trades=bt["trades"],
        bb_position=round(float(last["pct_b"]), 3),
        rsi_s=round(float(last["RSI_S"]), 1),
        rsi_l=round(float(last["RSI_L"]), 1),
        df=df
    )

# ══════════════════════════════════════════════
# 7. 繪圖引擎（專業版）
# ══════════════════════════════════════════════
def plot_chart(r: ScanResult) -> go.Figure:
    df  = r.df.tail(120)
    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.60, 0.22, 0.18],
        subplot_titles=["", "RSI", "Volume"]
    )

    # ── K 線 ──
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#00ff88", increasing_fillcolor="#00cc6a",
        decreasing_line_color="#ff3b6b", decreasing_fillcolor="#cc2244",
        name="K線", line_width=1
    ), row=1, col=1)

    # BB 帶
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Upper"], name="BB上軌",
        line=dict(color="rgba(255,220,100,0.7)", width=1, dash="dot")
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Lower"], name="BB下軌",
        line=dict(color="rgba(255,220,100,0.7)", width=1, dash="dot"),
        fill="tonexty", fillcolor="rgba(255,220,100,0.04)"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["MA"], name="MA",
        line=dict(color="rgba(100,180,255,0.8)", width=1.5)
    ), row=1, col=1)

    # 停損 / 目標線
    fig.add_hline(y=r.stop,   line_dash="dash", line_color="#ff3b6b",
                  annotation_text=f"停損 {r.stop}", annotation_position="right",
                  row=1, col=1)
    fig.add_hline(y=r.target, line_dash="dash", line_color="#00ff88",
                  annotation_text=f"目標 {r.target}", annotation_position="right",
                  row=1, col=1)

    # ── RSI ──
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI_S"], name=f"RSI{6}",
        line=dict(color="#4d9fff", width=1.5)
    ), row=2, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["RSI_L"], name=f"RSI{12}",
        line=dict(color="#a855f7", width=1.5)
    ), row=2, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(255,255,255,0.03)",
                  line_width=0, row=2, col=1)

    # ── 成交量 ──
    colors = ["#00cc6a" if c >= o else "#cc2244"
              for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(
        x=df.index, y=df["Volume"], marker_color=colors,
        name="Volume", opacity=0.7
    ), row=3, col=1)
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Vol_MA"], name="Vol MA",
        line=dict(color="#ffd93d", width=1.5)
    ), row=3, col=1)

    fig.update_layout(
        height=600,
        paper_bgcolor="#0a0e1a",
        plot_bgcolor="#0d1220",
        font=dict(family="JetBrains Mono", color="#8896b0", size=10),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, x=0, font_size=10,
                    bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=20, b=10, l=60, r=80),
    )
    for ax in ["xaxis", "xaxis2", "xaxis3", "yaxis", "yaxis2", "yaxis3"]:
        fig.update_layout(**{ax: dict(
            gridcolor="rgba(255,255,255,0.04)",
            linecolor="rgba(255,255,255,0.07)",
            zerolinecolor="rgba(255,255,255,0.07)"
        )})

    return fig

# ══════════════════════════════════════════════
# 8. Discord 專業推播
# ══════════════════════════════════════════════
def discord_color(signal: str, win_rate: float) -> int:
    if signal == "BUY" and win_rate >= 65:  return 0x00ff88  # 亮綠
    if signal == "BUY":                      return 0x00cc6a  # 綠
    return 0xffd93d                                            # 黃

def build_discord_payload(results: list[ScanResult], scan_time: str) -> dict:
    buy_results   = [r for r in results if r.signal == "BUY"]
    watch_results = [r for r in results if r.signal == "WATCH"]
    top5          = sorted(buy_results, key=lambda x: (-x.win_rate, -x.rr_ratio))[:5]

    embeds = []

    # 總覽 embed
    summary_embed = {
        "title": "🎯 台股 AI 狙擊手｜掃描戰報",
        "description": (
            f"```yaml\n"
            f"掃描時間: {scan_time}\n"
            f"掃描標的: {len(results)} 檔\n"
            f"BUY 訊號: {len(buy_results)} 檔\n"
            f"觀察標的: {len(watch_results)} 檔\n"
            f"```"
        ),
        "color": 0x4d9fff,
        "footer": {"text": "台股 AI 狙擊手 Pro MAX v3.0"}
    }
    embeds.append(summary_embed)

    # 個股 embed（最多 5 張）
    for r in top5:
        trend_icon = "🔺" if r.change_pct >= 0 else "🔻"
        win_bar    = "█" * int(r.win_rate / 10) + "░" * (10 - int(r.win_rate / 10))

        embed = {
            "title": f"{'💎' if r.win_rate >= 65 else '📈'} {r.code} {r.name}",
            "color": discord_color(r.signal, r.win_rate),
            "fields": [
                {
                    "name": "📊 價格資訊",
                    "value": (
                        f"```diff\n"
                        f"+ 現價  {r.price:>10.2f}\n"
                        f"+ 漲跌  {r.change_pct:>+9.2f}%\n"
                        f"+ 目標  {r.target:>10.2f}\n"
                        f"- 停損  {r.stop:>10.2f}\n"
                        f"  盈虧比 {r.rr_ratio:>8.2f}x\n"
                        f"```"
                    ),
                    "inline": True
                },
                {
                    "name": "📈 量能&位置",
                    "value": (
                        f"```ini\n"
                        f"[量比]  {r.vol_ratio:.2f}x\n"
                        f"[%B]   {r.bb_position:.3f}\n"
                        f"[RSI短] {r.rsi_s:.1f}\n"
                        f"[RSI長] {r.rsi_l:.1f}\n"
                        f"```"
                    ),
                    "inline": True
                },
                {
                    "name": "🔬 回測統計",
                    "value": (
                        f"```\n"
                        f"勝率  {r.win_rate:.1f}%\n"
                        f"{win_bar}\n"
                        f"均報酬 {r.avg_return:+.2f}%\n"
                        f"樣本數 {r.trades} 次\n"
                        f"```"
                    ),
                    "inline": False
                }
            ],
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        embeds.append(embed)

    if not top5:
        embeds.append({
            "title": "📉 今日無高勝率 BUY 訊號",
            "description": "建議等待下一個機會",
            "color": 0xff3b6b
        })

    return {
        "username": "🎯 AI 狙擊手 Pro",
        "avatar_url": "https://i.imgur.com/wSTFkRM.png",
        "embeds": embeds[:10]  # Discord 最多 10 個 embed
    }

def send_discord(payload: dict, webhook_url: str) -> tuple[bool, str]:
    if not webhook_url:
        return False, "未設定 Webhook"
    try:
        url = webhook_url.replace("discordapp.com", "discord.com").strip()
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code in [200, 204]:
            return True, "推播成功"
        return False, f"Discord 拒絕 ({r.status_code}): {r.text[:100]}"
    except Exception as e:
        return False, str(e)

# ══════════════════════════════════════════════
# 9. 側邊欄 UI
# ══════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:16px 0 8px'>
        <div style='font-size:2rem'>🎯</div>
        <div style='font-weight:900;color:#00ff88;font-size:1.1rem;letter-spacing:0.05em'>AI 狙擊手 Pro</div>
        <div style='font-size:0.65rem;color:#8896b0;letter-spacing:0.15em'>TAIWAN STOCK SCANNER v3.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("**📡 掃描設定**")

    scan_mode = st.radio(
        "掃描範圍", ["全上市櫃 (~1000檔)", "前 200 檔（快速）", "自選清單"],
        index=0, horizontal=False, label_visibility="collapsed"
    )

    custom_list = ""
    if scan_mode == "自選清單":
        custom_list = st.text_area(
            "輸入股票代號（逗號分隔）",
            placeholder="例：2330, 2317, 2454, 2382",
            height=80
        )

    st.divider()
    st.markdown("**⚙️ 策略參數**")

    col_a, col_b = st.columns(2)
    with col_a:
        bb_period = st.number_input("BB 週期", 10, 50, 20, step=1)
        rsi_short = st.number_input("RSI 短期", 3, 14, 6, step=1)
    with col_b:
        bb_std    = st.number_input("BB 倍數", 1.0, 3.0, 2.0, step=0.1)
        rsi_long  = st.number_input("RSI 長期", 10, 30, 12, step=1)

    pct_b_thr = st.slider("%B 超賣門檻", 0.0, 0.5, 0.2, step=0.05)
    vol_mult  = st.slider("爆量倍數", 0.5, 3.0, 1.2, step=0.1)
    grace     = st.slider("訊號緩衝天數", 1, 7, 3, step=1)

    st.divider()
    st.markdown("**📋 回測設定**")
    hold_days      = st.slider("持有天數", 3, 30, 10, step=1)
    stop_loss_pct  = st.slider("停損 %", 0.02, 0.15, 0.05, step=0.01, format="%.0%%")
    take_profit_pct= st.slider("停利 %", 0.05, 0.30, 0.10, step=0.01, format="%.0%%")
    min_win_rate   = st.slider("最低勝率篩選 %", 0, 80, 0, step=5)

    st.divider()
    st.markdown("**🔔 Discord 推播**")
    webhook = st.text_input("Webhook 網址", type="password",
                             placeholder="https://discord.com/api/webhooks/...")
    auto_push = st.checkbox("掃描完自動推播", value=True)

    if st.button("🛠 測試推播", use_container_width=True):
        test_payload = {
            "username": "🎯 AI 狙擊手 Pro",
            "embeds": [{"title": "✅ 連線測試成功", "description": "台股 AI 狙擊手 Pro MAX v3.0 已就緒！",
                        "color": 0x00ff88}]
        }
        ok, msg = send_discord(test_payload, webhook)
        st.success(f"✅ {msg}") if ok else st.error(f"❌ {msg}")

    st.divider()
    st.caption(f"📦 已載入 **{len(ALL_CODES)}** 檔標的")

# ══════════════════════════════════════════════
# 10. 主畫面
# ══════════════════════════════════════════════
st.markdown('<div class="hero-title">🎯 台股 AI 狙擊手 Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">MULTI-SIGNAL ENGINE · VECTORIZED BACKTEST · REAL-TIME DISCORD PUSH</div>', unsafe_allow_html=True)

# 參數包
params = {
    "bb_period": bb_period, "bb_std": bb_std,
    "pct_b": pct_b_thr, "grace": grace,
    "rsi_short": rsi_short, "rsi_long": rsi_long,
    "vol_mult": vol_mult,
    "hold_days": hold_days,
    "stop_loss_pct": stop_loss_pct,
    "take_profit_pct": take_profit_pct
}

# ── 個股快速查詢 ──
with st.expander("🔍 個股快速查詢", expanded=False):
    q_col1, q_col2 = st.columns([3, 1])
    with q_col1:
        query_code = st.text_input("輸入股票代號", placeholder="例：2330", label_visibility="collapsed")
    with q_col2:
        query_btn = st.button("查詢", use_container_width=True)

    if query_btn and query_code.strip():
        code = query_code.strip()
        with st.spinner(f"正在下載 {code} 資料..."):
            try:
                df_q = yf.download(f"{code}.TW", period="1y", interval="1d", progress=False)
                if df_q.empty:
                    st.error("查無資料，請確認代號是否正確")
                else:
                    df_q = calc_indicators(df_q, params)
                    last_q = df_q.iloc[-1]
                    prev_q = df_q.iloc[-2]
                    price_q = float(last_q["Close"])
                    chg_q   = (price_q / float(prev_q["Close"]) - 1) * 100

                    # 快速 mock result for chart
                    mock_r = ScanResult(
                        code=code, name=STOCK_DICT.get(code, code),
                        signal="—", price=round(price_q, 2),
                        change_pct=round(chg_q, 2),
                        vol_ratio=round(float(last_q["Volume"]/last_q["Vol_MA"]), 2),
                        stop=round(float(last_q["Lower"]), 2),
                        target=round(float(last_q["Upper"]), 2),
                        rr_ratio=0, win_rate=0, avg_return=0, trades=0,
                        bb_position=round(float(last_q["pct_b"]), 3),
                        rsi_s=round(float(last_q["RSI_S"]), 1),
                        rsi_l=round(float(last_q["RSI_L"]), 1),
                        df=df_q
                    )

                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("現價", f"{price_q:.2f}", f"{chg_q:+.2f}%")
                    m2.metric("量比", f"{mock_r.vol_ratio:.2f}x")
                    m3.metric("%B", f"{mock_r.bb_position:.3f}")
                    m4.metric("RSI短", f"{mock_r.rsi_s:.1f}")
                    m5.metric("RSI長", f"{mock_r.rsi_l:.1f}")
                    st.plotly_chart(plot_chart(mock_r), use_container_width=True)
            except Exception as e:
                st.error(f"錯誤：{e}")

st.divider()

# ── 掃描按鈕 ──
scan_btn = st.button("🔥 開始全自動掃描", type="primary", use_container_width=True)

# Session state 保存結果
if "scan_results" not in st.session_state:
    st.session_state.scan_results = []
if "scan_meta" not in st.session_state:
    st.session_state.scan_meta = {}

if scan_btn:
    # 決定掃描清單
    if scan_mode == "自選清單":
        target_codes = [c.strip() for c in custom_list.replace("，", ",").split(",")
                        if c.strip() and c.strip().isdigit()]
    elif scan_mode == "前 200 檔（快速）":
        target_codes = ALL_CODES[:200]
    else:
        target_codes = ALL_CODES

    if not target_codes:
        st.error("清單為空，請確認輸入")
        st.stop()

    t0 = time.time()
    total = len(target_codes)

    # ── 分批下載（顯示進度）──
    batches = [target_codes[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    n_batches = len(batches)

    progress_bar  = st.progress(0, text="準備中...")
    status_txt    = st.empty()
    all_results   = []

    for bi, batch in enumerate(batches):
        status_txt.markdown(
            f"<span style='font-family:JetBrains Mono;font-size:0.8rem;color:#8896b0'>"
            f"⬇️ 下載批次 {bi+1}/{n_batches}（{batch[0]}~{batch[-1]}）...</span>",
            unsafe_allow_html=True
        )
        raw = fetch_batch(tuple(batch))
        if raw.empty:
            progress_bar.progress((bi+1)/n_batches, text=f"批次 {bi+1} 無資料，略過")
            continue

        batch_res = []
        for code in batch:
            r = analyze_one(code, raw, params)
            if r and r.win_rate >= min_win_rate:
                batch_res.append(r)

        all_results.extend(batch_res)
        pct = (bi + 1) / n_batches
        status_txt.markdown(
            f"<span style='font-family:JetBrains Mono;font-size:0.8rem;color:#00ff88'>"
            f"✅ 批次 {bi+1}/{n_batches} 完成，本批 {len(batch_res)} 筆訊號</span>",
            unsafe_allow_html=True
        )
        progress_bar.progress(pct, text=f"掃描進度 {int(pct*100)}%")

    progress_bar.progress(1.0, text="掃描完成！")
    elapsed = time.time() - t0

    # 排序
    all_results.sort(key=lambda x: (0 if x.signal == "BUY" else 1, -x.win_rate, -x.rr_ratio))

    st.session_state.scan_results = all_results
    st.session_state.scan_meta = {
        "total": total, "elapsed": elapsed,
        "time_str": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "buy_count": sum(1 for r in all_results if r.signal == "BUY"),
        "watch_count": sum(1 for r in all_results if r.signal == "WATCH"),
    }

    # Discord 推播
    if auto_push and webhook:
        payload = build_discord_payload(all_results, st.session_state.scan_meta["time_str"])
        ok, msg = send_discord(payload, webhook)
        if ok:
            st.toast("✅ Discord 推播成功！", icon="🔔")
        else:
            st.toast(f"⚠️ Discord 推播失敗：{msg}", icon="⚠️")

# ── 顯示結果 ──
results = st.session_state.scan_results
meta    = st.session_state.scan_meta

if results or meta:
    buy_r   = [r for r in results if r.signal == "BUY"]
    watch_r = [r for r in results if r.signal == "WATCH"]
    avg_wr  = np.mean([r.win_rate for r in buy_r]) if buy_r else 0

    # 統計卡片
    st.markdown(f"""
    <div class="stat-grid">
        <div class="stat-card blue">
            <div class="stat-label">掃描標的</div>
            <div class="stat-value">{meta.get('total', 0)}</div>
        </div>
        <div class="stat-card green">
            <div class="stat-label">BUY 訊號</div>
            <div class="stat-value">{meta.get('buy_count', 0)}</div>
        </div>
        <div class="stat-card yellow">
            <div class="stat-label">觀察標的</div>
            <div class="stat-value">{meta.get('watch_count', 0)}</div>
        </div>
        <div class="stat-card purple">
            <div class="stat-label">平均勝率</div>
            <div class="stat-value">{avg_wr:.1f}%</div>
        </div>
        <div class="stat-card {'green' if meta.get('elapsed', 0) < 60 else 'red'}">
            <div class="stat-label">耗時</div>
            <div class="stat-value">{meta.get('elapsed', 0):.0f}s</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not results:
        st.info("本次掃描未找到符合條件的標的，可以嘗試放寬參數設定。")
    else:
        # Tab 分類顯示
        tab_buy, tab_watch, tab_all = st.tabs(
            [f"💎 BUY 訊號 ({len(buy_r)})", f"👁 觀察清單 ({len(watch_r)})", f"📋 全部結果 ({len(results)})"]
        )

        def render_results(res_list):
            for r in res_list:
                chg_color = "price-green" if r.change_pct >= 0 else "price-red"
                chg_arrow = "▲" if r.change_pct >= 0 else "▼"
                badge     = f'<span class="badge-buy">BUY</span>' if r.signal == "BUY" else f'<span class="badge-watch">WATCH</span>'
                wr_bar    = "█" * int(r.win_rate / 10) + "░" * (10 - int(r.win_rate / 10))

                label = (
                    f"{badge} &nbsp; <b>{r.code}</b> {r.name} &nbsp; "
                    f"<span class='{chg_color} mono'>{r.price} {chg_arrow}{abs(r.change_pct):.2f}%</span> &nbsp; "
                    f"<span class='mono' style='color:#8896b0'>勝率 {r.win_rate:.1f}%</span>"
                )

                with st.expander(label, expanded=False):
                    c1, c2, c3, c4, c5, c6 = st.columns(6)
                    c1.metric("現價",   f"{r.price}")
                    c2.metric("目標",   f"{r.target}", f"+{((r.target/r.price)-1)*100:.1f}%")
                    c3.metric("停損",   f"{r.stop}",   f"-{((r.price/r.stop)-1)*100:.1f}%")
                    c4.metric("盈虧比", f"{r.rr_ratio:.2f}x")
                    c5.metric("量比",   f"{r.vol_ratio:.2f}x")
                    c6.metric("回測勝率", f"{r.win_rate:.1f}%")

                    st.markdown(f"""
                    <div style='font-family:JetBrains Mono;font-size:0.75rem;color:#8896b0;margin:4px 0 12px'>
                        均報酬 <span style='color:#00ff88'>{r.avg_return:+.2f}%</span> ·
                        %B = {r.bb_position:.3f} ·
                        RSI {r.rsi_s:.1f}/{r.rsi_l:.1f} ·
                        樣本 {r.trades} 次 ·
                        {wr_bar}
                    </div>
                    """, unsafe_allow_html=True)
                    st.plotly_chart(plot_chart(r), use_container_width=True)

        with tab_buy:
            render_results(buy_r)
        with tab_watch:
            render_results(watch_r)
        with tab_all:
            # 表格模式
            tbl_data = []
            for r in results:
                tbl_data.append({
                    "代號": r.code, "名稱": r.name, "訊號": r.signal,
                    "現價": r.price, "漲跌%": f"{r.change_pct:+.2f}%",
                    "目標": r.target, "停損": r.stop, "盈虧比": r.rr_ratio,
                    "量比": r.vol_ratio, "勝率%": r.win_rate,
                    "均報酬%": f"{r.avg_return:+.2f}%", "樣本": r.trades
                })
            st.dataframe(
                pd.DataFrame(tbl_data),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "勝率%": st.column_config.ProgressColumn("勝率%", min_value=0, max_value=100, format="%.1f%%"),
                    "盈虧比": st.column_config.NumberColumn("盈虧比", format="%.2fx"),
                }
            )

# 底部資訊
st.divider()
st.markdown("""
<div style='text-align:center;font-family:JetBrains Mono;font-size:0.65rem;color:#4a5568;padding:8px 0'>
    台股 AI 狙擊手 Pro MAX v3.0 · 僅供學術研究與技術開發使用 · 投資有風險，買賣請自行判斷
</div>
""", unsafe_allow_html=True)
