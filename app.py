import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# ── 頁面設定 ──────────────────────────────────────────────
st.set_page_config(
    page_title="台股選股系統",
    page_icon="📈",
    layout="wide",
)

st.title("📈 台股選股系統")
st.caption("BBand + RSI 雙指標策略 · 收盤後掃股 · 資料來源：Yahoo Finance (yfinance)")

# ── 股票名稱對照表 ────────────────────────────────────────
STOCK_NAMES = {
    "2301": "光寶科", "2303": "聯電", "2308": "台達電", "2312": "金寶", "2313": "華通",
    "2317": "鴻海", "2323": "中環", "2324": "仁寶", "2327": "國巨", "2330": "台積電",
    "2337": "旺宏", "2344": "華邦電", "2345": "智邦", "2347": "聯強", "2352": "佳世達",
    "2353": "宏碁", "2354": "鴻準", "2356": "英業達", "2357": "華碩", "2360": "致茂",
    "2368": "金像電", "2376": "技嘉", "2377": "微星", "2379": "瑞昱", "2382": "廣達",
    "2383": "台光電", "2385": "群光", "2393": "億光", "2395": "研華", "2404": "漢唐",
    "2408": "南亞科", "2409": "友達", "2412": "中華電", "2439": "美律", "2449": "京元電子",
    "2454": "聯發科", "2455": "全新", "2458": "義隆", "2474": "可成", "2492": "華新科",
    "2498": "宏達電", "3008": "大立光", "3017": "奇鋐", "3034": "聯詠", "3035": "智原",
    "3037": "欣興", "3044": "健鼎", "3045": "台灣大", "3231": "緯創", "3443": "創意",
    "3481": "群創", "3532": "台勝科", "3533": "嘉澤", "3653": "健策", "3661": "世芯-KY",
    "3711": "日月光投控", "4904": "遠傳", "4938": "和碩", "4958": "臻鼎-KY", "5269": "祥碩",
    "5434": "崇越", "6116": "彩晶", "6205": "詮欣", "6239": "力成", "6271": "同欣電",
    "6415": "矽力*-KY", "6456": "GIS-KY", "6669": "緯穎", "6770": "力積電", "6806": "昇佳電子",
    "8046": "南電",
    "1101": "台泥", "1102": "亞泥", "1301": "台塑", "1303": "南亞", "1503": "士電",
    "1513": "中興電", "1514": "亞力", "1519": "華城", "2002": "中鋼", "2207": "和泰車",
    "6505": "台塑化",
    "2801": "彰銀", "2812": "台中銀", "2834": "臺企銀", "2880": "華南金", "2881": "富邦金",
    "2882": "國泰金", "2883": "凱基金", "2884": "玉山金", "2885": "元大金", "2886": "兆豐金",
    "2887": "台新金", "2889": "國票金", "2890": "永豐金", "2891": "中信金", "2892": "第一金",
    "2897": "王道銀", "5871": "中租-KY", "5876": "上海商銀", "5880": "合庫金"
}

# ── 指標計算函式 ──────────────────────────────────────────
def calc_bollinger(closes: np.ndarray, period: int, multiplier: float):
    upper, middle, lower, pct_b = [], [], [], []
    for i in range(len(closes)):
        if i < period - 1:
            upper.append(np.nan); middle.append(np.nan)
            lower.append(np.nan); pct_b.append(np.nan)
            continue
        sl   = closes[i - period + 1 : i + 1]
        mean = sl.mean()
        std  = sl.std(ddof=0)
        u = mean + multiplier * std
        l = mean - multiplier * std
        upper.append(u); middle.append(mean); lower.append(l)
        pct_b.append(0.5 if std == 0 else (closes[i] - l) / (u - l))
    return (np.array(upper), np.array(middle),
            np.array(lower), np.array(pct_b))

def calc_rsi(closes: np.ndarray, period: int) -> np.ndarray:
    """標準 Wilder's RSI（EMA 遞推）"""
    rsi = np.full(len(closes), np.nan)
    if len(closes) <= period:
        return rsi
    changes = np.diff(closes)
    gains   = np.where(changes > 0, changes,  0.0)
    losses  = np.where(changes < 0, -changes, 0.0)
    avg_g = gains[:period].mean()
    avg_l = losses[:period].mean()
    rsi[period] = 100.0 if avg_l == 0 else 100 - 100 / (1 + avg_g / avg_l)
    for i in range(period + 1, len(closes)):
        avg_g = (avg_g * (period - 1) + gains[i - 1])  / period
        avg_l = (avg_l * (period - 1) + losses[i - 1]) / period
        rsi[i] = 100.0 if avg_l == 0 else 100 - 100 / (1 + avg_g / avg_l)
    return rsi

# ── 抓資料 ────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_stock_data(code: str) -> tuple[np.ndarray | None, str]:
    try:
        ticker = yf.Ticker(code + ".TW")
        df = ticker.history(period="6mo", interval="1d", auto_adjust=True)
        if df.empty or len(df) < 30:
            return None, STOCK_NAMES.get(code, code)
        closes = df["Close"].dropna().to_numpy()
        if code in STOCK_NAMES:
            name = STOCK_NAMES[code]
        else:
            try:
                info = ticker.info
                name = info.get("longName") or info.get("shortName") or code
            except Exception:
                name = code
        return closes, name
    except Exception:
        return None, STOCK_NAMES.get(code, code)

# ── 單股分析 ──────────────────────────────────────────────
def analyze(code, closes, name, params):
    bb_period = params["bb_period"]
    bb_std    = params["bb_std"]
    pct_b_thr = params["pct_b"]
    grace     = params["grace"]
    rsi_s_per = params["rsi_short"]
    rsi_l_per = params["rsi_long"]

    min_len = max(bb_period, rsi_l_per) + grace + 5
    if len(closes) < min_len:
        return None

    upper, middle, lower, pct_b = calc_bollinger(closes, bb_period, bb_std)
    rsi_s = calc_rsi(closes, rsi_s_per)
    rsi_l = calc_rsi(closes, rsi_l_per)

    n           = len(closes)
    last_price  = closes[-1]
    last_pct_b  = pct_b[-1]
    last_rsi_s  = rsi_s[-1]
    last_rsi_l  = rsi_l[-1]
    last_upper  = upper[-1]
    last_lower  = lower[-1]
    last_middle = middle[-1]

    if any(np.isnan([last_pct_b, last_rsi_s, last_rsi_l])):
        return None

    pct_b_ok = any(
        (not np.isnan(pct_b[i]) and pct_b[i] < pct_b_thr)
        for i in range(n - grace, n)
    )

    golden = False
    for i in range(max(1, n - 3), n):
        if not any(np.isnan([rsi_s[i], rsi_l[i], rsi_s[i-1], rsi_l[i-1]])):
            if rsi_s[i-1] <= rsi_l[i-1] and rsi_s[i] > rsi_l[i]:
                golden = True; break

    death = False
    if n >= 2 and not any(np.isnan([rsi_s[-1], rsi_l[-1], rsi_s[-2], rsi_l[-2]])):
        death = rsi_s[-2] >= rsi_l[-2] and rsi_s[-1] < rsi_l[-1]

    overbought   = last_price >= last_upper or last_rsi_s > 70
    sell_signal  = overbought and death
    buy_signal   = pct_b_ok and golden and not sell_signal
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
        "code":   code, "name":   name,
        "signal": "BUY" if buy_signal else "WATCH",
        "price":  round(last_price,  2), "pct_b":  round(last_pct_b,  3),
        "rsi_s":  round(last_rsi_s,  1), "rsi_l":  round(last_rsi_l,  1),
        "upper":  round(last_upper,  2), "middle": round(last_middle, 2),
        "lower":  round(last_lower,  2), "stop":   round(last_lower,  2),
        "target": round(last_upper,  2), "rrr":    rrr,
    }

# ── LINE Messaging API 工具函式 ───────────────────────────
def get_channel_access_token(channel_id: str, channel_secret: str) -> str | None:
    """用 Channel ID + Secret 向 LINE 換取 Access Token（有效期 30 天）"""
    try:
        resp = requests.post(
            "https://api.line.me/v2/oauth/accessToken",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type":    "client_credentials",
                "client_id":     channel_id,
                "client_secret": channel_secret,
            },
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
        return None
    except Exception:
        return None

def line_get_user_id(token: str) -> str | None:
    """取得最近加 Bot 為好友的使用者 user_id"""
    try:
        resp = requests.get(
            "https://api.line.me/v2/bot/followers/ids",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        uids = resp.json().get("userIds", [])
        return uids[0] if uids else None
    except Exception:
        return None

def line_push_message(token: str, user_id: str,
                      results: list, rsi_short: int, rsi_long: int) -> tuple[bool, str]:
    """推播掃股結果，超過 4800 字自動切分多則"""
    now   = datetime.now().strftime("%Y/%m/%d %H:%M")
    buys  = [r for r in results if r["signal"] == "BUY"]
    watch = [r for r in results if r["signal"] == "WATCH"]

    def fmt(r):
        rrr_str = f"1:{r['rrr']}" if r["rrr"] else "N/A"
        return (
            f"\n【{r['code']} {r['name']}】\n"
            f"  現價 {r['price']}  %B {r['pct_b']}\n"
            f"  RSI{rsi_short} {r['rsi_s']} / RSI{rsi_long} {r['rsi_l']}\n"
            f"  停損 {r['stop']}  目標 {r['target']}  風報比 {rrr_str}"
        )

    sections = [f"📈 台股選股掃描結果\n🕐 {now}\n{'─'*22}"]
    if buys:
        sections.append(f"\n✅ 買進訊號（{len(buys)} 檔）")
        sections += [fmt(r) for r in buys]
    if watch:
        sections.append(f"\n👀 觀察中（{len(watch)} 檔）")
        sections += [fmt(r) for r in watch]
    if not buys and not watch:
        sections.append("\n本次掃描無符合條件股票。")
    sections.append("\n⚠️ 僅供技術分析參考，非投資建議")

    # 切分成每則 ≤4800 字
    MAX_LEN, messages, current = 4800, [], ""
    for block in sections:
        if len(current) + len(block) > MAX_LEN:
            if current: messages.append(current.strip())
            current = block
        else:
            current += block
    if current.strip():
        messages.append(current.strip())

    all_ok, err_msg = True, ""
    for chunk in [messages[i:i+5] for i in range(0, len(messages), 5)]:
        try:
            resp = requests.post(
                "https://api.line.me/v2/bot/message/push",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"to": user_id, "messages": [{"type": "text", "text": m} for m in chunk]},
                timeout=10,
            )
            if resp.status_code != 200:
                all_ok  = False
                err_msg = resp.json().get("message", f"HTTP {resp.status_code}")
        except Exception as e:
            all_ok, err_msg = False, str(e)

    return all_ok, err_msg

# ── 側邊欄：參數設定 ──────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 參數設定")
    bb_period = st.number_input("BB 週期（天）",  min_value=5,   max_value=50,  value=20)
    bb_std    = st.number_input("BB 標準差倍數",  min_value=1.0, max_value=3.0, value=2.0, step=0.1)
    pct_b_thr = st.number_input("%B 超賣門檻",    min_value=0.0, max_value=0.5, value=0.2, step=0.05)
    grace     = st.number_input("寬容期（天）",    min_value=1,   max_value=14,  value=7)
    rsi_short = st.number_input("RSI 短天期",      min_value=3,   max_value=14,  value=6)
    rsi_long  = st.number_input("RSI 長天期",      min_value=7,   max_value=30,  value=12)

    st.divider()

    # ── LINE 設定區 ───────────────────────────────────────
    st.header("🔔 LINE 推播設定")
    st.caption("[LINE Developers Console](https://developers.line.biz/console/) → Messaging API Channel → Basic settings")

    line_channel_id = st.text_input(
        "Channel ID",
        placeholder="例：2010319445",
    )
    line_channel_secret = st.text_input(
        "Channel Secret",
        type="password",
        placeholder="貼上 Channel Secret",
    )
    line_user_id = st.text_input(
        "你的 LINE User ID",
        placeholder="U 開頭的 33 碼，點下方按鈕自動取得",
    )

    # 自動取得 User ID
    if line_channel_id and line_channel_secret:
        if st.button("🔍 自動取得我的 User ID", use_container_width=True):
            with st.spinner("換取 Token 中..."):
                tmp_token = get_channel_access_token(line_channel_id, line_channel_secret)
            if tmp_token:
                uid = line_get_user_id(tmp_token)
                if uid:
                    st.success(f"取得成功！")
                    st.code(uid)
                    st.info("請複製上方 ID 貼到「你的 LINE User ID」欄位。")
                else:
                    st.error("找不到 User ID。\n請先用 LINE 對你的 Bot 傳任意一則訊息，再重試。")
            else:
                st.error("Token 換取失敗，請確認 Channel ID / Secret 是否正確。")

    # 狀態提示
    if line_channel_id and line_channel_secret and line_user_id:
        st.success("✅ LINE 推播已就緒")
    elif line_channel_id or line_channel_secret:
        st.warning("⚠️ 請填齊所有 LINE 欄位")
    else:
        st.caption("未設定，掃股結果不會推播。")

    st.divider()
    st.caption("策略邏輯")
    st.info("🟢 **買進**：%B < 門檻 + RSI黃金交叉\n\n🔴 **賣出**：價破上軌或RSI>70 + 死亡交叉")

params = {
    "bb_period": bb_period, "bb_std": bb_std,
    "pct_b": pct_b_thr,    "grace": grace,
    "rsi_short": rsi_short, "rsi_long": rsi_long,
}

# ── 主頁面：股票輸入 ──────────────────────────────────────
st.subheader("輸入股票清單")
raw = st.text_area(
    "台股代號（逗號或換行分隔）",
    value="""2317, 2330, 2454, 2412, 2382, 2308, 3711, 2881, 2882, 2884, 6505, 1301, 1303, 2002, 2886
2301, 2303, 2312, 2313, 2323, 2324, 2327, 2337, 2344, 2345, 2347, 2352, 2353, 2354, 2356,
2357, 2360, 2368, 2376, 2377, 2379, 2383, 2385, 2393, 2395, 2404, 2408, 2409, 2439, 2449,
2455, 2458, 2474, 2492, 2498, 3008, 3017, 3034, 3035, 3037, 3044, 3045, 3231, 3443, 3481,
3532, 3533, 3653, 3661, 4938, 4958, 5269, 5434, 6116, 6205, 6239, 6271, 6415, 6456, 6669,
6770, 8046, 1503, 1513, 1514, 1519, 4904, 6806, 2801, 2812, 2834, 2880, 2883, 2885, 2887,
2889, 2890, 2891, 2892, 2897, 5871, 5876, 5880, 1101, 1102""",
    height=80,
)
codes = [c.strip() for c in raw.replace("\n", ",").split(",") if c.strip()]
st.caption(f"共 {len(codes)} 檔待掃描")

# ── 掃描按鈕 ──────────────────────────────────────────────
line_ready = bool(line_channel_id and line_channel_secret and line_user_id)

if st.button("🔍 開始掃股", type="primary", use_container_width=True):
    results, errors = [], []
    prog = st.progress(0, text="準備中...")

    for i, code in enumerate(codes):
        prog.progress((i + 1) / len(codes), text=f"掃描中... {code} ({i+1}/{len(codes)})")
        closes, name = fetch_stock_data(code)
        if closes is None:
            errors.append(code)
        else:
            r = analyze(code, closes, name, params)
            if r:
                results.append(r)

    prog.empty()
    results.sort(key=lambda x: (0 if x["signal"] == "BUY" else 1, -(x["rrr"] or 0)))

    # ── 自動 LINE 推播 ────────────────────────────────────
    if line_ready:
        with st.spinner("📲 換取 Token 並傳送 LINE 推播中..."):
            token = get_channel_access_token(line_channel_id, line_channel_secret)
            if token:
                ok, err = line_push_message(token, line_user_id, results, rsi_short, rsi_long)
                if ok:
                    st.success("✅ LINE 推播已送出！")
                else:
                    st.error(f"❌ 推播失敗：{err}")
            else:
                st.error("❌ Token 換取失敗，請確認 Channel ID / Secret。")
    else:
        st.info("💡 在左側填入 LINE 設定即可自動推播結果。")

    st.divider()
    col_l, col_r = st.columns(2)
    col_l.metric("✅ 符合條件", f"{len(results)} 檔")
    col_r.metric("❌ 抓取失敗", f"{len(errors)} 檔")

    if errors:
        st.warning(f"以下代號抓取失敗：{', '.join(errors)}")

    if not results:
        st.info("目前沒有股票符合條件，可嘗試放寬參數或等待更好時機。")
    else:
        df = pd.DataFrame(results)
        df_display = df[["code","name","signal","price","pct_b",
                          "rsi_s","rsi_l","stop","target","rrr"]].copy()
        df_display.columns = ["代號","名稱","訊號","現價","%B",
                               f"RSI{rsi_short}",f"RSI{rsi_long}","停損","目標","風報比"]

        def color_signal(val):
            if val == "BUY":   return "background-color:#1a4a2e; color:#00e5a0; font-weight:bold"
            if val == "WATCH": return "background-color:#3a3000; color:#ffd166; font-weight:bold"
            return ""

        st.dataframe(
            df_display.style.map(color_signal, subset=["訊號"]),
            use_container_width=True, hide_index=True,
        )

        st.subheader("個股詳細資訊")
        for r in results:
            is_buy = r["signal"] == "BUY"
            badge  = "✅ 買進訊號" if is_buy else "👀 觀察中"
            with st.expander(f"{r['code']} {r['name']}　{badge}", expanded=is_buy):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("現價",            f"{r['price']}")
                c2.metric("%B",              f"{r['pct_b']}", delta="超賣" if r["pct_b"] < pct_b_thr else None)
                c3.metric(f"RSI{rsi_short}", f"{r['rsi_s']}")
                c4.metric(f"RSI{rsi_long}",  f"{r['rsi_l']}")
                st.divider()
                t1, t2, t3, t4 = st.columns(4)
                t1.metric("📌 進場價", f"{r['price']}")
                t2.metric("🛑 停損價", f"{r['stop']}")
                t3.metric("🎯 目標價", f"{r['target']}")
                t4.metric("⚖️ 風報比", f"1 : {r['rrr']}" if r["rrr"] else "N/A")
                st.caption(f"BB 軌道：下軌 {r['lower']} ／ 中軌 {r['middle']} ／ 上軌 {r['upper']}")

# ── 免責聲明 ──────────────────────────────────────────────
st.divider()
st.caption("⚠️ 本工具僅供技術分析參考，不構成投資建議。投資有風險，請自行評估後再做決策。")
