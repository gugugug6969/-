import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib3
import datetime

# 關閉不安全連線的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="台股 AI 專業操盤室", page_icon="📈", layout="wide")
st.title("📈 台股 AI 專業操盤室 (抓蟲透視版)")

# ── 🌟 修復 1：Discord 強化發送與錯誤捕捉 ──────────────────────
def send_discord_embed(payload, webhook_url):
    if not webhook_url: return False, "未提供網址"
    try:
        # 強制把舊版的 discordapp.com 換成最新的 discord.com (避免被擋)
        webhook_url = webhook_url.replace("discordapp.com", "discord.com")
        res = requests.post(webhook_url, json=payload, timeout=10)
        if res.status_code in [200, 204]:
            return True, "發送成功"
        else:
            return False, f"Discord 拒絕接收。狀態碼: {res.status_code}, 錯誤訊息: {res.text}"
    except Exception as e:
        return False, f"網路連線嚴重異常: {str(e)}"

# ── 1. 自動抓取全台股清單 ────────────────────────
@st.cache_data(ttl=86400)
def get_all_stock_names():
    names = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", headers=headers, timeout=10, verify=False)
        if res.status_code == 200:
            for item in res.json():
                if len(item["Code"]) == 4 and item["Code"].isdigit(): names[item["Code"]] = item["Name"]
        res2 = requests.get("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes", headers=headers, timeout=10, verify=False)
        if res2.status_code == 200:
            for item in res2.json():
                code = item.get("SecuritiesCompanyCode")
                if code and len(code) == 4: names[code] = item.get("CompanyName", code)
    except:
        pass
    return names

STOCK_DICT = get_all_stock_names()
ALL_CODES = list(STOCK_DICT.keys()) if STOCK_DICT else ["2330", "2317", "2454"]

# ── 2. 批次抓取歷史股價 ────────────────────────
@st.cache_data(ttl=86400)
def fetch_all_closes(codes: list):
    tickers = [f"{c}.TW" for c in codes]
    df = yf.download(tickers, period="1y", interval="1d", group_by='ticker', threads=True, progress=False)
    return df

# ── 3. 指標計算邏輯 ──────────────────────────────────────────
def calc_indicators(df, params):
    df = df.copy()
    df['MA'] = df['Close'].rolling(params['bb_period']).mean()
    df['STD'] = df['Close'].rolling(params['bb_period']).std(ddof=0)
    df['Upper'] = df['MA'] + params['bb_std'] * df['STD']
    df['Lower'] = df['MA'] - params['bb_std'] * df['STD']
    df['pct_b'] = (df['Close'] - df['Lower']) / (df['Upper'] - df['Lower'])
    
    def get_rsi(series, p):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(p).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(p).mean()
        return 100 - (100 / (1 + gain/loss))
    
    df['RSI_S'] = get_rsi(df['Close'], params['rsi_short'])
    df['RSI_L'] = get_rsi(df['Close'], params['rsi_long'])
    df['Vol_MA'] = df['Volume'].rolling(20).mean()
    return df

# ── 4. 核心分析與回測引擎 ────────────────────────────────────
def analyze_stock(code, df, params):
    df = calc_indicators(df, params)
    if len(df) < 40: return None
    
    n = -1
    last = df.iloc[n]
    prev = df.iloc[n-1]
    
    pct_b_ok = (df['pct_b'].iloc[n-params['grace']:].min() < params['pct_b'])
    golden_cross = (prev['RSI_S'] <= prev['RSI_L'] and last['RSI_S'] > last['RSI_L'])
    vol_ok = (last['Volume'] > last['Vol_MA'] * params['vol_mult'])
    
    buy_signal = pct_b_ok and golden_cross and vol_ok
    
    backtest_profit = 0
    trades = 0
    for i in range(40, len(df)-10):
        p_pct_b = (df['pct_b'].iloc[i-5:i].min() < params['pct_b'])
        p_cross = (df['RSI_S'].iloc[i-1] <= df['RSI_L'].iloc[i-1] and df['RSI_S'].iloc[i] > df['RSI_L'].iloc[i])
        if p_pct_b and p_cross:
            profit = (df['Close'].iloc[i+10] / df['Close'].iloc[i]) - 1
            backtest_profit += profit
            trades += 1
            
    win_rate_val = (backtest_profit/trades*100) if trades > 0 else 0.0
    win_rate_str = f"{win_rate_val:.1f}%" if trades > 0 else "無買點"

    risk = last['Close'] - last['Lower']
    reward = last['Upper'] - last['Close']
    rrr = round(reward / risk, 2) if risk > 0 else 0

    if buy_signal or (pct_b_ok and not golden_cross):
        return {
            "code": code, "name": STOCK_DICT.get(code, code),
            "signal": "BUY" if buy_signal else "WATCH",
            "price": round(last['Close'], 2),
            "vol_ratio": round(last['Volume']/last['Vol_MA'], 2),
            "stop": round(last['Lower'], 2), "target": round(last['Upper'], 2),
            "rrr": rrr,
            "win_rate": win_rate_str, "win_rate_val": win_rate_val, "df": df
        }
    return None

# ── 5. 專業 K 線繪圖引擎 ────────────────────────────────────
def plot_chart(df, name):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], line=dict(color='orange', width=1), name="上軌"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], line=dict(color='orange', width=1), name="下軌"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI_S'], name="RSI短", line=dict(color='blue')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI_L'], name="RSI長", line=dict(color='red')), row=2, col=1)
    fig.update_layout(height=500, xaxis_rangeslider_visible=False, margin=dict(t=30, b=0, l=0, r=0))
    return fig

# ── 6. 側邊欄與參數 ──────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 操盤參數")
    vol_mult = st.slider("爆量倍數 (成交量 > 20MA x ?)", 0.5, 3.0, 1.2)
    bb_period = st.number_input("BB 週期", 5, 40, 20)
    pct_b_thr = st.slider("%B 超賣門檻", 0.0, 0.5, 0.2)
    
    st.divider()
    st.header("🔔 Discord 戰情推播")
    webhook = st.text_input("Webhook 網址", type="password", value="https://discord.com/api/webhooks/1495088799875731556/Uyj88sZ2CjVjcPX841vNz_LoNmlcs9uX_22QZdXeQTavmOvm0N60Rl9lVFBaoCeFKGDI")
    
    if st.button("🛠️ 測試發送 Discord", use_container_width=True):
        if not webhook: st.error("請先輸入網址！")
        else:
            with st.spinner("測試連線中..."):
                payload = {
                    "username": "AI 狙擊手", "avatar_url": "https://cdn-icons-png.flaticon.com/512/1154/1154448.png",
                    "embeds": [{"title": "✅ 系統連線測試成功", "description": "戰情推播系統上線！", "color": 3066993}]
                }
                success, msg = send_discord_embed(payload, webhook)
                if success: st.success("連線成功！請檢查 Discord。")
                else: st.error(f"連線失敗！原因：\n{msg}") # 🌟 這裡會印出真正的死因
    
    st.divider()
    st.success(f"已載入 {len(ALL_CODES)} 檔標的")

params = {"bb_period": bb_period, "bb_std": 2.0, "pct_b": pct_b_thr, "grace": 5, "rsi_short": 6, "rsi_long": 12, "vol_mult": vol_mult}

# ── 7. 主程式執行 ──────────────────────────────────────────
if st.button(f"🔥 開始全自動掃描", type="primary", use_container_width=True):
    results = []
    test_codes = ALL_CODES[:30] # 🌟 測試用，先抓 30 檔就好，避免被 Yahoo 鎖
    
    with st.spinner(f"正在向 Yahoo 撈取資料..."):
        raw_data = fetch_all_closes(test_codes)

    # 🌟 修復 2：檢查 Yahoo 是不是根本沒給資料
    if raw_data.empty:
        st.error("🚨 嚴重錯誤：Yahoo Finance 拒絕連線，沒有回傳任何股票資料！可能是被暫時封鎖 IP，請稍等幾分鐘後再試。")
        st.stop() # 停止程式，不要往下跑

    prog = st.progress(0, text="運算指標中...")
    for i, code in enumerate(test_codes):
        prog.progress((i+1)/len(test_codes))
        try:
            df = raw_data[f"{code}.TW"].dropna()
            if df.empty: continue
            res = analyze_stock(code, df, params)
            if res: results.append(res)
        except Exception as e:
            st.warning(f"{code} 運算發生錯誤: {e}") # 印出運算錯誤

    prog.empty()
    results.sort(key=lambda x: (0 if x["signal"] == "BUY" else 1, -x["win_rate_val"]))

    # ── 🚀 Discord 推播 ────────────────────────
    high_win_buys = [r for r in results if r['signal'] == "BUY" and r['win_rate_val'] >= 60.0]
    
    if webhook:
        if not high_win_buys:
            payload = {
                "username": "AI 狙擊手", 
                "embeds": [{"title": "📉 今日無高勝率標的", "description": "建議空手觀望。", "color": 15158332}]
            }
            success, msg = send_discord_embed(payload, webhook)
            if not success: st.error(f"Discord 推播失敗: {msg}")
        else:
            top_5 = high_win_buys[:5]
            fields = []
            for r in top_5:
                diff_text = f"
http://googleusercontent.com/immersive_entry_chip/0

### 兩步診斷：
1. **點擊「🛠️ 測試發送 Discord」**：如果畫面跳出紅字，**請直接把那串紅字貼給我看！** 那是 Discord 官方給的死因。
2. **點擊「🔥 開始全自動掃描」**：如果畫面跳出 `🚨 嚴重錯誤：Yahoo Finance 拒絕連線`，就代表你的雲端主機被 Yahoo 擋住了（這在抓資料時很常見），我們再來針對它換一個不會被擋的抓取套件！

跑完告訴我它吐了什麼錯誤訊息給你！
