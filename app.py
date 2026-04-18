import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

# ── 頁面設定 ──────────────────────────────────────────────
st.set_page_config(
    page_title="台股全自動選股系統",
    page_icon="🚀",
    layout="wide",
)

st.title("🚀 台股全自動選股系統")
st.caption("自動獲取全台股清單 · 批次運算防封鎖 · BBand + RSI 雙指標策略")

# ── 1. 自動抓取全台股名稱對照表 (快取24小時) ────────────────
@st.cache_data(ttl=86400)
def get_all_stock_names():
    names = {}
    # 🌟 關鍵破解：加上 headers，偽裝成正常的 Google Chrome 瀏覽器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        # 抓上市清單
        res = requests.get("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", headers=headers, timeout=10)
        if res.status_code == 200:
            for item in res.json():
                if len(item["Code"]) == 4 and item["Code"].isdigit(): 
                    names[item["Code"]] = item["Name"]
                    
        # 抓上櫃清單
        res2 = requests.get("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes", headers=headers, timeout=10)
        if res2.status_code == 200:
            for item in res2.json():
                if len(item["SecuritiesCompanyCode"]) == 4 and item["SecuritiesCompanyCode"].isdigit():
                    names[item["SecuritiesCompanyCode"]] = item["CompanyName"]
                    
    except Exception as e:
        # 🌟 如果還是失敗，直接在網頁上印出真正死掉的原因，不要盲猜
        st.error(f"⚠️ 抓取股票代號失敗，可能是被擋了。錯誤訊息：{e}")
        # 保底提供 10 檔權值股測試用
        names = {"2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2382": "廣達", "2308": "台達電", 
                 "2881": "富邦金", "2882": "國泰金", "2891": "中信金", "2603": "長榮", "1503": "士電"}
    return names

STOCK_NAMES = get_all_stock_names()
ALL_CODES = list(STOCK_NAMES.keys())

# ── 2. 指標計算函式 ──────────────────────────────────────────
def calc_bollinger(closes: np.ndarray, period: int, multiplier: float):
    upper, middle, lower, pct_b = [], [], [], []
    for i in range(len(closes)):
        if i < period - 1:
            upper.append(np.nan); middle.append(np.nan)
            lower.append(np.nan); pct_b.append(np.nan)
            continue
        sl = closes[i - period + 1 : i + 1]
        mean = sl.mean()
        std  = sl.std(ddof=0)
        u = mean + multiplier * std
        l = mean - multiplier * std
        upper.append(u); middle.append(mean); lower.append(l)
        pct_b.append(0.5 if std == 0 else (closes[i] - l) / (u - l))
    return (np.array(upper), np.array(middle),
            np.array(lower), np.array(pct_b))

def calc_rsi(closes: np.ndarray, period: int):
    rsi = np.full(len(closes), np.nan)
    for i in range(period, len(closes)):
        changes = np.diff(closes[i - period : i + 1])
        gains  = changes[changes > 0].sum()
        losses = -changes[changes < 0].sum()
        avg_g  = gains  / period
        avg_l  = losses / period
        rsi[i] = 100 if avg_l == 0 else 100 - 100 / (1 + avg_g / avg_l)
    return rsi

# ── 3. 批次抓取資料 (快取24小時防 Yahoo 封鎖) ────────────────
@st.cache_data(ttl=86400)
def fetch_all_closes(codes: list):
    tickers = [f"{c}.TW" for c in codes]
    # threads=True 讓下載速度變快，progress=False 關閉終端機進度條
    df = yf.download(tickers, period="6mo", interval="1d", auto_adjust=True, threads=True, progress=False)
    return df

# ── 4. 單股分析 ──────────────────────────────────────────────
def analyze(code, closes, params):
    bb_period   = params["bb_period"]
    bb_std      = params["bb_std"]
    pct_b_thr   = params["pct_b"]
    grace       = params["grace"]
    rsi_s_per   = params["rsi_short"]
    rsi_l_per   = params["rsi_long"]

    min_len = max(bb_period, rsi_l_per) + grace + 5
    if len(closes) < min_len:
        return None

    upper, middle, lower, pct_b = calc_bollinger(closes, bb_period, bb_std)
    rsi_s = calc_rsi(closes, rsi_s_per)
    rsi_l = calc_rsi(closes, rsi_l_per)

    n = len(closes)
    last_price  = closes[-1]
    last_pct_b  = pct_b[-1]
    last_rsi_s  = rsi_s[-1]
    last_rsi_l  = rsi_l[-1]
    last_upper  = upper[-1]
    last_lower  = lower[-1]
    last_middle = middle[-1]

    if any(np.isnan([last_pct_b, last_rsi_s, last_rsi_l])):
        return None

    # %B 寬容期
    pct_b_ok = any(
        (not np.isnan(pct_b[i]) and pct_b[i] < pct_b_thr)
        for i in range(n - grace, n)
    )

    # RSI 黃金交叉（近3日內）
    golden = False
    for i in range(max(1, n - 3), n):
        if not any(np.isnan([rsi_s[i], rsi_l[i], rsi_s[i-1], rsi_l[i-1]])):
            if rsi_s[i-1] <= rsi_l[i-1] and rsi_s[i] > rsi_l[i]:
                golden = True; break

    # RSI 死亡交叉
    death = (
        not any(np.isnan([rsi_s[-1], rsi_l[-1], rsi_s[-2], rsi_l[-2]]))
        and rsi_s[-2] >= rsi_l[-2] and rsi_s[-1] < rsi_l[-1]
    )

    overbought  = last_price >= last_upper or last_rsi_s > 70
    sell_signal = overbought and death
    buy_signal  = pct_b_ok and golden and not sell_signal
    watch_signal = (
        pct_b_ok and not golden and not sell_signal
        and last_rsi_s < last_rsi_l
        and (last_rsi_l - last_rsi_s) < 5
    )

    if not buy_signal and not watch_signal:
        return None

    risk   = last_price - last_lower
    reward = last_upper  - last_price
    rrr    = round(reward / risk, 2) if risk > 0 else None

    return {
        "code":    code,
        "name":    STOCK_NAMES.get(code, code),
        "signal":  "BUY" if buy_signal else "WATCH",
        "price":   round(last_price,  2),
        "pct_b":   round(last_pct_b,  3),
        "rsi_s":   round(last_rsi_s,  1),
        "rsi_l":   round(last_rsi_l,  1),
        "upper":   round(last_upper,  2),
        "middle":  round(last_middle, 2),
        "lower":   round(last_lower,  2),
        "stop":    round(last_lower,  2),
        "target":  round(last_upper,  2),
        "rrr":     rrr,
    }

# ── 側邊欄：參數設定 ──────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 參數設定")
    bb_period  = st.number_input("BB 週期（天）",     min_value=5,   max_value=50,  value=20)
    bb_std     = st.number_input("BB 標準差倍數",    min_value=1.0, max_value=3.0, value=2.0, step=0.1)
    pct_b_thr  = st.number_input("%B 超賣門檻",      min_value=0.0, max_value=0.5, value=0.2, step=0.05)
    grace      = st.number_input("寬容期（天）",      min_value=1,   max_value=14,  value=7)
    rsi_short  = st.number_input("RSI 短天期",        min_value=3,   max_value=14,  value=6)
    rsi_long   = st.number_input("RSI 長天期",        min_value=7,   max_value=30,  value=12)

    st.divider()
    st.caption("策略邏輯")
    st.info("🟢 **買進**：%B < 門檻 + RSI黃金交叉\n\n🔴 **賣出**：價破上軌或RSI>70 + 死亡交叉")
    st.success(f"📌 系統已自動載入 {len(ALL_CODES)} 檔上市櫃股票")

params = {
    "bb_period": bb_period, "bb_std": bb_std,
    "pct_b": pct_b_thr,    "grace": grace,
    "rsi_short": rsi_short, "rsi_long": rsi_long,
}

# ── 主頁面：掃描按鈕 ──────────────────────────────────────
st.subheader("一鍵全自動掃描")
st.write("點擊下方按鈕，系統將自動下載全市場歷史股價並套用策略篩選。")

if st.button(f"🔥 開始掃描全台股 ({len(ALL_CODES)} 檔)", type="primary", use_container_width=True):
    results = []
    
    # 步驟 1：批次下載資料
    with st.spinner(f"正在向 Yahoo Finance 打包下載資料，這可能需要 1~2 分鐘，請耐心等候...（每日僅需下載一次）"):
        df_all = fetch_all_closes(ALL_CODES)

    # 步驟 2：本地端高速運算
    prog = st.progress(0, text="準備運算...")
    
    for i, code in enumerate(ALL_CODES):
        # 每 20 檔更新一次進度條，避免畫面卡頓
        if i % 20 == 0:
            prog.progress((i + 1) / len(ALL_CODES), text=f"分析指標中... ({i+1}/{len(ALL_CODES)})")
        
        try:
            # 從批次下載的整包資料中，抽出單一檔股票的收盤價
            ticker_str = f"{code}.TW"
            if "Close" in df_all and ticker_str in df_all["Close"].columns:
                closes = df_all["Close"][ticker_str].dropna().to_numpy()
            else:
                continue

            # 進入原本的分析邏輯
            r = analyze(code, closes, params)
            if r:
                results.append(r)
        except Exception:
            continue

    prog.empty()

    # 排序：BUY > WATCH，再按 RRR 降冪
    results.sort(key=lambda x: (0 if x["signal"] == "BUY" else 1, -(x["rrr"] or 0)))

    # ── 結果顯示 ──────────────────────────────────────────
    st.divider()
    st.metric("✅ 符合條件標的", f"{len(results)} 檔")

    if not results:
        st.info("目前沒有股票符合條件，可嘗試放寬左側參數或等待更好時機。")
    else:
        # 表格總覽
        df = pd.DataFrame(results)
        df_display = df[["code","name","signal","price","pct_b",
                          "rsi_s","rsi_l","stop","target","rrr"]].copy()
        df_display.columns = ["代號","名稱","訊號","現價","%B",
                               f"RSI{rsi_short}",f"RSI{rsi_long}",
                               "停損","目標","風報比"]

        def color_signal(val):
            if val == "BUY":   return "background-color:#1a4a2e; color:#00e5a0; font-weight:bold"
            if val == "WATCH": return "background-color:#3a3000; color:#ffd166; font-weight:bold"
            return ""

        st.dataframe(
            df_display.style.map(color_signal, subset=["訊號"]),
            use_container_width=True,
            hide_index=True,
        )

        # 個股詳細卡片
        st.subheader("個股詳細資訊")
        for r in results:
            is_buy = r["signal"] == "BUY"
            badge  = "✅ 買進訊號" if is_buy else "👀 觀察中"
            
            with st.expander(f"{r['code']} {r['name']}　{badge}", expanded=is_buy):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("現價",        f"{r['price']}")
                c2.metric("%B",          f"{r['pct_b']}", delta="超賣" if r["pct_b"] < pct_b_thr else None)
                c3.metric(f"RSI{rsi_short}", f"{r['rsi_s']}")
                c4.metric(f"RSI{rsi_long}",  f"{r['rsi_l']}")

                st.divider()
                t1, t2, t3, t4 = st.columns(4)
                t1.metric("📌 進場價", f"{r['price']}")
                t2.metric("🛑 停損價", f"{r['stop']}")
                t3.metric("🎯 目標價", f"{r['target']}")
                t4.metric("⚖️ 風報比", f"1 : {r['rrr']}" if r["rrr"] else "N/A")

                st.caption(
                    f"BB 軌道：下軌 {r['lower']} ／ 中軌 {r['middle']} ／ 上軌 {r['upper']}"
                )

# ── 免責聲明 ──────────────────────────────────────────────
st.divider()
st.caption("⚠️ 本工具僅供技術分析參考，不構成投資建議。投資有風險，請自行評估後再做決策。")
