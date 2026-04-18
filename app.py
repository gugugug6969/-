import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib3
import datetime

# 關閉 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 頁面配置 ---
st.set_page_config(page_title="台股 AI 專業操盤室", page_icon="📈", layout="wide")
st.title("📈 台股 AI 專業操盤室")
st.caption("全自動掃描 | 爆量濾網 | 專業 K 線 | 歷史回測 | 頂級 Discord 戰情卡片")

# --- Discord 工具 (強化錯誤處理) ---
def send_discord_embed(payload, webhook_url):
    if not webhook_url: return False, "未輸入網址"
    try:
        # 強制修正網域，確保連線暢通
        webhook_url = webhook_url.replace("discordapp.com", "discord.com").strip()
        res = requests.post(webhook_url, json=payload, timeout=10)
        if res.status_code in [200, 204]:
            return True, "發送成功"
        else:
            return False, f"Discord 拒絕接收 (代碼: {res.status_code})"
    except Exception as e:
        return False, str(e)

# --- 1. 自動抓取全台股清單 (快取 24 小時) ---
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

# --- 2. 批次抓取歷史股價 (快取 24 小時) ---
@st.cache_data(ttl=86400)
def fetch_all_closes(codes: list):
    tickers = [f"{c}.TW" for c in codes]
    # 使用 threads=True 增加下載速度
    df = yf.download(tickers, period="1y", interval="1d", group_by='ticker', threads=True, progress=False)
    return df

# --- 3. 指標計算與回測引擎 ---
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

def analyze_stock(code, df, params):
    df = calc_indicators(df, params)
    if len(df) < 40: return None
    
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # 訊號邏輯
    pct_b_ok = (df['pct_b'].iloc[-params['grace']:].min() < params['pct_b'])
    golden_cross = (prev['RSI_S'] <= prev['RSI_L'] and last['RSI_S'] > last['RSI_L'])
    vol_ok = (last['Volume'] > last['Vol_MA'] * params['vol_mult'])
    
    buy_signal = pct_b_ok and golden_cross and vol_ok
    
    # 回測勝率計算
    backtest_profit, trades = 0, 0
    for i in range(40, len(df)-10):
        if (df['pct_b'].iloc[i-5:i].min() < params['pct_b']) and (df['RSI_S'].iloc[i-1] <= df['RSI_L'].iloc[i-1] and df['RSI_S'].iloc[i] > df['RSI_L'].iloc[i]):
            backtest_profit += (df['Close'].iloc[i+10] / df['Close'].iloc[i]) - 1
            trades += 1
            
    win_val = (backtest_profit/trades*100) if trades > 0 else 0.0
    
    if buy_signal or (pct_b_ok and not golden_cross):
        return {
            "code": code, "name": STOCK_DICT.get(code, code),
            "signal": "BUY" if buy_signal else "WATCH",
            "price": round(last['Close'], 2),
            "vol_ratio": round(last['Volume']/last['Vol_MA'], 2),
            "stop": round(last['Lower'], 2), "target": round(last['Upper'], 2),
            "win_rate": f"{win_val:.1f}%", "win_val": win_val, "df": df
        }
    return None

# --- 4. 繪圖引擎 ---
def plot_chart(df, name):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], line=dict(color='orange', width=1), name="上軌"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], line=dict(color='orange', width=1), name="下軌"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI_S'], name="RSI短", line=dict(color='blue')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI_L'], name="RSI長", line=dict(color='red')), row=2, col=1)
    fig.update_layout(height=500, xaxis_rangeslider_visible=False, margin=dict(t=30, b=0, l=0, r=0))
    return fig

# --- 5. 側邊欄 ---
with st.sidebar:
    st.header("⚙️ 參數設定")
    vol_mult = st.slider("爆量倍數", 0.5, 3.0, 1.2)
    bb_period = st.number_input("BB 週期", 5, 40, 20)
    pct_b_thr = st.slider("%B 門檻", 0.0, 0.5, 0.2)
    
    st.divider()
    st.header("🔔 Discord 推播")
    webhook = st.text_input("Webhook 網址", type="password", value="https://discord.com/api/webhooks/1495088799875731556/Uyj88sZ2CjVjcPX841vNz_LoNmlcs9uX_22QZdXeQTavmOvm0N60Rl9lVFBaoCeFKGDI")
    
    if st.button("🛠️ 測試發送", use_container_width=True):
        payload = {"username": "AI 狙擊手", "embeds": [{"title": "✅ 測試成功", "color": 3066993}]}
        ok, msg = send_discord_embed(payload, webhook)
        st.success("成功！") if ok else st.error(f"失敗: {msg}")

    st.success(f"已載入 {len(ALL_CODES)} 檔標的")

params = {"bb_period": bb_period, "bb_std": 2.0, "pct_b": pct_b_thr, "grace": 5, "rsi_short": 6, "rsi_long": 12, "vol_mult": vol_mult}

# --- 6. 執行掃描 ---
if st.button("🔥 開始全自動掃描", type="primary", use_container_width=True):
    # 先抓前 100 檔測試效率
    test_codes = ALL_CODES[:100]
    with st.spinner("正在下載數據..."):
        raw_data = fetch_all_closes(test_codes)

    if raw_data.empty:
        st.error("Yahoo Finance 沒抓到資料，請重試！")
        st.stop()

    results = []
    for code in test_codes:
        try:
            df = raw_data[f"{code}.TW"].dropna()
            if df.empty: continue
            res = analyze_stock(code, df, params)
            if res: results.append(res)
        except: continue

    results.sort(key=lambda x: (0 if x["signal"] == "BUY" else 1, -x["win_val"]))

    # 🚀 Discord 高勝率推播
    high_win = [r for r in results if r['signal'] == "BUY" and r['win_val'] >= 60.0]
    if webhook:
        if not high_win:
            send_discord_embed({"username": "AI 狙擊手", "embeds": [{"title": "📉 今日無高勝率標的", "color": 15158332}]}, webhook)
        else:
            fields = []
            for r in high_win[:5]:
                # 🌟 修復關鍵：三引號多行字串，解決 SyntaxError
                val_text = f"""```diff
+ 現價: {r['price']}
+ 目標: {r['target']}
- 停損: {r['stop']}
--- 量比: {r['vol_ratio']}x
```"""
                fields.append({"name": f"💎 {r['code']} {r['name']} (勝率: {r['win_rate']})", "value": val_text, "inline": False})
            
            payload = {
                "username": "AI 狙擊手", 
                "embeds": [{"title": "🚀 高勝率戰報", "color": 5763719, "fields": fields, "timestamp": datetime.datetime.now().isoformat()}]
            }
            send_discord_embed(payload, webhook)
            st.toast("已推播至 Discord！")

    # 📊 顯示結果
    if not results:
        st.info("沒符合的標的。")
    else:
        df_res = pd.DataFrame(results).drop(columns=['df', 'win_val'])
        st.dataframe(df_res, use_container_width=True, hide_index=True)
        for r in results:
            with st.expander(f"{r['code']} {r['name']} | {r['win_rate']}"):
                st.plotly_chart(plot_chart(r['df'], r['name']), use_container_width=True)
