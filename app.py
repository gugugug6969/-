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

# ── 頁面設定 ──────────────────────────────────────────────
st.set_page_config(page_title="台股 AI 專業操盤室", page_icon="📈", layout="wide")

st.title("📈 台股 AI 專業操盤室")
st.caption("全自動掃描 | 爆量濾網 | 專業 K 線 | 歷史回測 | 頂級 Discord 戰情卡片")

# ── Discord 終極富文本發送工具 ──────────────────────────────
def send_discord_embed(payload, webhook_url):
    """發送高級 Embed 卡片到 Discord"""
    if not webhook_url: return False
    try:
        res = requests.post(webhook_url, json=payload, timeout=5)
        return res.status_code in [200, 204]
    except:
        return False

# ── 1. 自動抓取全台股清單 (繞過憑證，快取 24 小時) ──────────────
@st.cache_data(ttl=86400)
def get_all_stock_names():
    names = {}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get("[https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL](https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL)", headers=headers, timeout=10, verify=False)
        if res.status_code == 200:
            for item in res.json():
                if len(item["Code"]) == 4 and item["Code"].isdigit(): names[item["Code"]] = item["Name"]
        res2 = requests.get("[https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes](https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes)", headers=headers, timeout=10, verify=False)
        if res2.status_code == 200:
            for item in res2.json():
                code = item.get("SecuritiesCompanyCode")
                if code and len(code) == 4: names[code] = item.get("CompanyName", code)
    except:
        names = {"2330": "台積電", "2317": "鴻海", "2454": "聯發科"}
    return names

STOCK_DICT = get_all_stock_names()
ALL_CODES = list(STOCK_DICT.keys())

# ── 2. 批次抓取歷史股價 (快取 24 小時，防 Yahoo 封鎖) ────────
@st.cache_data(ttl=86400)
def fetch_all_closes(codes: list):
    tickers = [f"{c}.TW" for c in codes]
    df = yf.download(tickers, period="1y", interval="1d", group_by='ticker', threads=True, progress=False)
    return df

# ── 3. 指標計算邏輯 ──────────────────────────────────────────
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

# ── 4. 核心分析與回測引擎 ────────────────────────────────────
def analyze_stock(code, df, params):
    df = calc_indicators(df, params)
    if len(df) < 40: return None
    
    n = -1
    last = df.iloc[n]
    prev = df.iloc[n-1]
    
    # 訊號邏輯
    pct_b_ok = (df['pct_b'].iloc[n-params['grace']:].min() < params['pct_b'])
    golden_cross = (prev['RSI_S'] <= prev['RSI_L'] and last['RSI_S'] > last['RSI_L'])
    vol_ok = (last['Volume'] > last['Vol_MA'] * params['vol_mult'])
    
    buy_signal = pct_b_ok and golden_cross and vol_ok
    
    # 回測邏輯：計算過去一年勝率
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
    win_rate_str = f"{win_rate_val:.1f}%" if trades > 0 else "無歷史買點"

    # 風報比計算
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
    webhook = st.text_input("Webhook 網址", type="password", value="[https://discordapp.com/api/webhooks/1495088799875731556/Uyj88sZ2CjVjcPX841vNz_LoNmlcs9uX_22QZdXeQTavmOvm0N60Rl9lVFBaoCeFKGDI](https://discordapp.com/api/webhooks/1495088799875731556/Uyj88sZ2CjVjcPX841vNz_LoNmlcs9uX_22QZdXeQTavmOvm0N60Rl9lVFBaoCeFKGDI)")
    
    if st.button("🛠️ 測試發送 Discord", use_container_width=True):
        if not webhook: st.error("請先輸入網址！")
        else:
            with st.spinner("測試發送中..."):
                payload = {
                    "username": "AI 狙擊手", "avatar_url": "[https://cdn-icons-png.flaticon.com/512/1154/1154448.png](https://cdn-icons-png.flaticon.com/512/1154/1154448.png)",
                    "embeds": [{
                        "title": "✅ 系統連線測試成功", "description": "如果你看到這張卡片，代表高級戰情推播系統已上線！", "color": 3066993
                    }]
                }
                if send_discord_embed(payload, webhook): st.success("連線成功！請檢查你的 Discord。")
                else: st.error("連線失敗！請確認網址是否正確。")
    
    st.divider()
    st.success(f"已載入 {len(ALL_CODES)} 檔標的")

params = {"bb_period": bb_period, "bb_std": 2.0, "pct_b": pct_b_thr, "grace": 5, "rsi_short": 6, "rsi_long": 12, "vol_mult": vol_mult}

# ── 7. 主程式執行 ──────────────────────────────────────────
if st.button(f"🔥 開始全自動掃描 (尋找高勝率起漲股)", type="primary", use_container_width=True):
    results = []
    test_codes = ALL_CODES[:300] 
    
    with st.spinner(f"正在向資料庫撈取 {len(test_codes)} 檔大數據 (若有快取將秒速完成)..."):
        raw_data = fetch_all_closes(test_codes)

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

    results.sort(key=lambda x: (0 if x["signal"] == "BUY" else 1, -x["win_rate_val"]))

    # ── 🚀 Discord 頂尖勝率推播 ────────────────────────
    high_win_buys = [r for r in results if r['signal'] == "BUY" and r['win_rate_val'] >= 60.0]
    
    if webhook:
        if not high_win_buys:
            payload = {
                "username": "AI 狙擊手", "avatar_url": "[https://cdn-icons-png.flaticon.com/512/1154/1154448.png](https://cdn-icons-png.flaticon.com/512/1154/1154448.png)",
                "embeds": [{
                    "title": "📉 今日大盤雷達：無高勝率標的",
                    "description": "市場目前缺乏「爆量 + 勝率 > 60%」的絕佳買點。\nAI 建議：**保護資金，空手觀望。**",
                    "color": 15158332,
                    "timestamp": datetime.datetime.now().isoformat()
                }]
            }
            send_discord_embed(payload, webhook)
            st.info("今日無高勝率買進訊號，已發送『空手觀望』卡片至 Discord。")
        else:
            top_5_buys = high_win_buys[:5]
            fields = []
            for r in top_5_buys:
                # 🌟 修復關鍵：使用括號自動連接字串，避免斷行引發 SyntaxError
                diff_text = (
                    "```diff\n"
                    f"+ 現價進場: {r['price']}\n"
                    f"+ 預估目標: {r['target']}\n"
                    f"- 跌破停損: {r['stop']}\n"
                    f"--- 爆量倍數: {r['vol_ratio']}x\n"
                    "```"
                )
                fields.append({
                    "name": f"💎 {r['code']} {r['name']} ── 勝率: {r['win_rate']}",
                    "value": diff_text,
                    "inline": False
                })
                
            payload = {
                "username": "AI 狙擊手", 
                "avatar_url": "[https://cdn-icons-png.flaticon.com/512/1154/1154448.png](https://cdn-icons-png.flaticon.com/512/1154/1154448.png)",
                "embeds": [{
                    "title": "🚀 【頂級勝率】台股爆量起漲雷達",
                    "description": f"系統已從全市場嚴選出 **{len(high_win_buys)}** 檔高勝率標的。\n以下為勝率最高的前 5 檔精銳部隊：",
                    "color": 5763719,
                    "fields": fields,
                    "footer": {"text": "台股 AI 專業操盤室自動運算"},
                    "timestamp": datetime.datetime.now().isoformat()
                }]
            }
            
            success = send_discord_embed(payload, webhook)
            if success: st.toast("🔔 高勝率戰情卡片已成功推送到 Discord！")

    # ── 📊 網頁結果顯示 ──────────────────────────────────────────
    if not results:
        st.info("今日無符合條件之標的。")
    else:
        st.subheader(f"✅ 篩選結果 (共 {len(results)} 檔符合)")
        
        df_res = pd.DataFrame(results).drop(columns=['df', 'win_rate_val'])
        df_display = df_res[["code","name","signal","price","vol_ratio","stop","target","rrr","win_rate"]].copy()
        df_display.columns = ["代號","名稱","訊號","現價","量比","停損","目標","風報比","歷史勝率"]

        def color_signal(val):
            if val == "BUY":   return "background-color:#1a4a2e; color:#00e5a0; font-weight:bold"
            if val == "WATCH": return "background-color:#3a3000; color:#ffd166; font-weight:bold"
            return ""

        st.dataframe(
            df_display.style.map(color_signal, subset=["訊號"]),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        st.subheader("📊 專業技術分析與歷史回測看板")
        for r in results:
            with st.expander(f"{r['code']} {r['name']} | 訊號: {r['signal']} | 量比: {r['vol_ratio']}x | 勝率: {r['win_rate']}", expanded=(r['signal']=="BUY")):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("現價", r['price'])
                c2.metric("成交量比", f"{r['vol_ratio']} 倍")
                c3.metric("預估目標價", r['target'])
                c4.metric("風報比", f"1 : {r['rrr']}" if r['rrr'] else "N/A")
                st.plotly_chart(plot_chart(r['df'], r['name']), use_container_width=True)

st.divider()
st.caption("⚠️ 本系統僅供技術分析參考，不構成投資建議。投資有風險，請自行評估後再做決策。")
