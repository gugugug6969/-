import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib3

# 關閉不安全連線的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── 頁面設定 ──────────────────────────────────────────────
st.set_page_config(page_title="台股 AI 專業操盤室", page_icon="📈", layout="wide")

st.title("📈 台股 AI 專業操盤室")
st.caption("全自動掃描 | 爆量濾網 | 專業 K 線 | 歷史回測 | Discord 推播")

# ── Discord 工具 ─────────────────────────────────────────
def send_discord(msg, webhook_url):
    if not webhook_url: return False
    try:
        res = requests.post(webhook_url, json={"content": msg}, timeout=5)
        return res.status_code in [200, 204]
    except:
        return False

# ── 1. 自動抓取全台股清單 (繞過憑證) ────────────────────────
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
        names = {"2330": "台積電", "2317": "鴻海", "2454": "聯發科"}
    return names

STOCK_DICT = get_all_stock_names()
ALL_CODES = list(STOCK_DICT.keys())

# ── 2. 指標計算邏輯 ──────────────────────────────────────────
def calc_indicators(df, params):
    df = df.copy()
    # BBands
    df['MA'] = df['Close'].rolling(params['bb_period']).mean()
    df['STD'] = df['Close'].rolling(params['bb_period']).std(ddof=0)
    df['Upper'] = df['MA'] + params['bb_std'] * df['STD']
    df['Lower'] = df['MA'] - params['bb_std'] * df['STD']
    df['pct_b'] = (df['Close'] - df['Lower']) / (df['Upper'] - df['Lower'])
    
    # RSI
    def get_rsi(series, p):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(p).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(p).mean()
        return 100 - (100 / (1 + gain/loss))
    
    df['RSI_S'] = get_rsi(df['Close'], params['rsi_short'])
    df['RSI_L'] = get_rsi(df['Close'], params['rsi_long'])
    
    # 成交量均線 (20日)
    df['Vol_MA'] = df['Volume'].rolling(20).mean()
    return df

# ── 3. 核心分析與回測引擎 ────────────────────────────────────
def analyze_stock(code, df, params):
    df = calc_indicators(df, params)
    if len(df) < 40: return None
    
    n = -1
    last = df.iloc[n]
    prev = df.iloc[n-1]
    
    # 訊號邏輯
    pct_b_ok = (df['pct_b'].iloc[n-params['grace']:].min() < params['pct_b'])
    golden_cross = (prev['RSI_S'] <= prev['RSI_L'] and last['RSI_S'] > last['RSI_L'])
    # 爆量濾網：今日成交量 > 20日均量 * 倍數
    vol_ok = (last['Volume'] > last['Vol_MA'] * params['vol_mult'])
    
    buy_signal = pct_b_ok and golden_cross and vol_ok
    
    # 回測邏輯：計算過去一年的勝率
    backtest_profit = 0
    trades = 0
    for i in range(40, len(df)-10):
        p_pct_b = (df['pct_b'].iloc[i-5:i].min() < params['pct_b'])
        p_cross = (df['RSI_S'].iloc[i-1] <= df['RSI_L'].iloc[i-1] and df['RSI_S'].iloc[i] > df['RSI_L'].iloc[i])
        if p_pct_b and p_cross:
            profit = (df['Close'].iloc[i+10] / df['Close'].iloc[i]) - 1
            backtest_profit += profit
            trades += 1
    
    win_rate = f"{(backtest_profit/trades*100):.1f}%" if trades > 0 else "無歷史買點"

    if buy_signal or (pct_b_ok and not golden_cross):
        return {
            "code": code, "name": STOCK_DICT.get(code, code),
            "signal": "BUY" if buy_signal else "WATCH",
            "price": round(last['Close'], 2),
            "vol_ratio": round(last['Volume']/last['Vol_MA'], 2),
            "stop": round(last['Lower'], 2), "target": round(last['Upper'], 2),
            "win_rate": win_rate, "df": df
        }
    return None

# ── 4. 專業 K 線繪圖引擎 ────────────────────────────────────
def plot_chart(df, name):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    # K線
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="K線"), row=1, col=1)
    # BBands
    fig.add_trace(go.Scatter(x=df.index, y=df['Upper'], line=dict(color='orange', width=1), name="上軌"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Lower'], line=dict(color='orange', width=1), name="下軌"), row=1, col=1)
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI_S'], name="RSI短", line=dict(color='blue')), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI_L'], name="RSI長", line=dict(color='red')), row=2, col=1)
    
    fig.update_layout(height=500, xaxis_rangeslider_visible=False, margin=dict(t=30, b=0, l=0, r=0))
    return fig

# ── 5. 側邊欄與參數 ──────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 操盤參數")
    vol_mult = st.slider("爆量倍數 (成交量 > 20MA x ?)", 0.5, 3.0, 1.2)
    bb_period = st.number_input("BB 週期", 5, 40, 20)
    pct_b_thr = st.slider("%B 超賣門檻", 0.0, 0.5, 0.2)
    
    st.divider()
    st.header("🔔 Discord 推播與測試")
    webhook = st.text_input("Webhook 網址", type="password", value="https://discordapp.com/api/webhooks/1495088799875731556/Uyj88sZ2CjVjcPX841vNz_LoNmlcs9uX_22QZdXeQTavmOvm0N60Rl9lVFBaoCeFKGDI")
    
    if st.button("🛠️ 測試發送 Discord", use_container_width=True):
        if not webhook:
            st.error("請先輸入網址！")
        else:
            with st.spinner("測試發送中..."):
                success = send_discord("✅ **【台股 AI 操盤室】連線測試成功！**", webhook)
                if success:
                    st.success("連線成功！請檢查你的 Discord。")
                else:
                    st.error("連線失敗！請確認網址是否正確。")
    
    st.divider()
    st.success(f"已載入 {len(ALL_CODES)} 檔標的")

params = {"bb_period": bb_period, "bb_std": 2.0, "pct_b": pct_b_thr, "grace": 5, "rsi_short": 6, "rsi_long": 12, "vol_mult": vol_mult}

# ── 6. 主程式執行 ──────────────────────────────────────────
if st.button(f"🔥 開始全自動掃描 (尋找起漲股)", type="primary", use_container_width=True):
    results = []
    # 預設掃描前 300 檔熱門股
    test_codes = ALL_CODES[:300] 
    
    with st.spinner(f"正在下載 {len(test_codes)} 檔股票大數據 (包含成交量)..."):
        raw_data = yf.download([f"{c}.TW" for c in test_codes], period="1y", interval="1d", group_by='ticker', threads=True, progress=False)

    prog = st.progress(0, text="運算指標中...")
    for i, code in enumerate(test_codes):
        if i % 10 == 0: prog.progress((i+1)/len(test_codes))
        try:
            df = raw_data[f"{code}.TW"].dropna()
            if df.empty: continue
            res = analyze_stock(code, df, params)
            if res: results.append(res)
        except: continue
    prog.empty()

    results.sort(key=lambda x: 0 if x["signal"] == "BUY" else 1)

    # ── 🚀 Discord 實戰推播 (終極防呆版) ────────────────────────
    buys = [r for r in results if r['signal'] == "BUY"]
    if webhook:
        if not buys:
            # 沒股票時，發送空手通知
            send_discord("📉 **【台股 AI 操盤室】今日掃描完成。**\n目前市場無符合「爆量 + 起漲」條件的標的，系統建議空手觀望。", webhook)
            st.info("今日無買進訊號，已發送『空手觀望』通知至 Discord。")
        else:
            # 有股票時，最多只發前 15 檔，避免字數超過 2000 字被 Discord 封殺
            top_buys = buys[:15]
            msg = f"🚀 **【AI 操盤室】發現 {len(buys)} 檔爆量起漲標的！** 🚀\n" 
            if len(buys) > 15:
                msg += "*(⚠️ 訊號過多，為符合版面僅列出前 15 檔最強勢標的)*\n\n"
            else:
                msg += "\n"
                
            msg += "\n".join([f"✅ **{r['code']} {r['name']}** | 價:{r['price']} | 量比:{r['vol_ratio']}x | 勝率:{r['win_rate']}" for r in top_buys])
            
            success = send_discord(msg, webhook)
            if success:
                st.toast("🔔 買進訊號已成功推送到 Discord！")
            else:
                st.error("推播失敗：可能遭遇未知的網路問題。")
    # ─────────────────────────────────────────────────────────

    # 顯示結果
    if not results:
        st.info("今日無符合爆量與指標之標的。")
    else:
        st.subheader(f"✅ 篩選結果 (共 {len(results)} 檔符合)")
        df_res = pd.DataFrame(results).drop(columns=['df'])
        st.dataframe(df_res, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("📊 專業技術分析與歷史回測看板")
        for r in results:
            with st.expander(f"{r['code']} {r['name']} | 訊號: {r['signal']} | 量比: {r['vol_ratio']}x | 歷史回測: {r['win_rate']}", expanded=(r['signal']=="BUY")):
                c1, c2, c3 = st.columns([1,1,2])
                c1.metric("現價", r['price'])
                c2.metric("成交量比 (昨日)", f"{r['vol_ratio']} 倍")
                c3.metric("預估目標價 (上軌)", r['target'])
                
                # 畫圖
                st.plotly_chart(plot_chart(r['df'], r['name']), use_container_width=True)

st.divider()
st.caption("⚠️ 本系統僅供技術分析參考，不構成投資建議。投資有風險，請自行評估後再做決策。")
