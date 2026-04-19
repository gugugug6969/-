_ = """
╔══════════════════════════════════════════════════════════════════════════════╗
║  台股 AI 狙擊手  ULTRA v8.0  — ABSOLUTE MAXIMUM EVOLUTION                    ║
║                                                                              ║
║  NEW v8 FEATURES:                                                            ║
║  ✦ 籌碼分析：外資/投信/自營商三大法人買賣超                                  ║
║  ✦ 財務健康分數：流動比率、負債比、速動比率                                  ║
║  ✦ 產業比較：同產業 PE/ROE/殖利率對比                                        ║
║  ✦ 即時警示系統：價格突破/跌破 MA、RSI 極值警報                              ║
║  ✦ 自選股清單：加入/移除/匯出 Watch List                                     ║
║  ✦ 回測模擬：基於信號回測歷史績效                                            ║
║  ✦ 風險評估：Beta、波動率、最大回撤                                          ║
║  ✦ 多空力道儀表板：多空比、買賣超動能圖                                      ║
║  ✦ 股價預測帶：均值回歸區間 + 標準差帶                                       ║
║  ✦ 完整 KPI 統計：夏普比率、年化報酬                                         ║
║  ✦ 掃描結果 CSV 匯出                                                         ║
║  ✦ LINE Notify 推播支援                                                      ║
║  ✦ 財報日曆提醒                                                              ║
║  ✦ 成交量異常偵測                                                            ║
║  ✦ 支撐壓力位計算（Pivot Point）                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝

pip install streamlit yfinance pandas numpy requests plotly apscheduler beautifulsoup4 lxml urllib3
streamlit run taiwan_stock_ultra_v8.py
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
import time
import re
import json
import io
import concurrent.futures
from typing import Optional, Dict, List, Tuple, Any
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(
    page_title="台股狙擊手 ULTRA v8",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═════════════════════════════════════════════════════════════════════════════
# CSS — Bloomberg Terminal × Cyberpunk MAX v8
# ═════════════════════════════════════════════════════════════════════════════
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');

:root {
  --bg0:#02040a; --bg1:#07101e; --bg2:#0c1829; --bg3:#111f35;
  --line:#162035; --line2:#1e2e4a; --line3:#2a3f60;
  --t0:#ddeeff; --t1:#7a9ab8; --t2:#3d5470; --t3:#1e3050;
  --g:#00f090; --g2:#00c070; --g3:rgba(0,240,144,0.12);
  --r:#ff3358; --r2:#cc1a38; --r3:rgba(255,51,88,0.12);
  --y:#ffbe00; --y3:rgba(255,190,0,0.12);
  --b:#2d7fff; --b2:#1a5ecc; --b3:rgba(45,127,255,0.12);
  --p:#a855f7; --p3:rgba(168,85,247,0.12);
  --c:#00cce0; --c3:rgba(0,204,224,0.12);
  --o:#ff7700; --o3:rgba(255,119,0,0.12);
  --mono:'JetBrains Mono',monospace;
  --sans:'Syne',sans-serif;
  --glow-g: 0 0 20px rgba(0,240,144,0.25);
  --glow-r: 0 0 20px rgba(255,51,88,0.25);
  --glow-b: 0 0 20px rgba(45,127,255,0.25);
  --glow-y: 0 0 20px rgba(255,190,0,0.25);
}

*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body,[class*="css"]{font-family:var(--sans);background:var(--bg0);color:var(--t0)}
#MainMenu,footer,header{visibility:hidden}
.stApp{background:var(--bg0)}
.main .block-container{padding:.6rem 1rem 2rem;max-width:100%}

/* ── DEEP SPACE BACKGROUND ── */
.stApp::before{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:
    radial-gradient(ellipse 80% 50% at 10% 20%,rgba(0,240,144,.03) 0%,transparent 60%),
    radial-gradient(ellipse 60% 40% at 90% 80%,rgba(45,127,255,.03) 0%,transparent 60%),
    radial-gradient(ellipse 40% 30% at 50% 50%,rgba(168,85,247,.02) 0%,transparent 70%);
}
.stApp::after{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:
    linear-gradient(rgba(0,240,144,.006) 1px,transparent 1px),
    linear-gradient(90deg,rgba(0,240,144,.006) 1px,transparent 1px);
  background-size:48px 48px;
}

/* ══════════════ MASTER HEADER ══════════════ */
.mhdr{
  position:relative;overflow:hidden;
  background:linear-gradient(180deg,#07101e 0%,#050d18 100%);
  border:1px solid var(--line2);
  border-top:2px solid var(--g);
  border-radius:0 0 10px 10px;
  padding:0;margin-bottom:12px;
}
.mhdr-glow{
  position:absolute;top:-40px;left:50%;transform:translateX(-50%);
  width:700px;height:100px;
  background:radial-gradient(ellipse,rgba(0,240,144,.06) 0%,transparent 70%);
  pointer-events:none;animation:pulse-glow 4s ease-in-out infinite;
}
@keyframes pulse-glow{0%,100%{opacity:.6}50%{opacity:1}}
.mhdr-top{display:flex;align-items:center;gap:0;border-bottom:1px solid var(--line2)}
.mhdr-accent{
  width:4px;align-self:stretch;
  background:linear-gradient(180deg,var(--g) 0%,var(--b) 50%,var(--p) 100%);
  flex-shrink:0;
}
.mhdr-main{flex:1;display:flex;align-items:center;gap:20px;padding:16px 20px}
.mhdr-logo-block{
  flex-shrink:0;border:1px solid var(--line3);border-radius:6px;
  padding:8px 12px;background:var(--bg2);text-align:center;
  position:relative;overflow:hidden;
}
.mhdr-logo-block::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(0,240,144,.05) 0%,transparent 60%);
}
.mhdr-logo-sym{font-family:var(--mono);font-size:1.2rem;font-weight:700;color:var(--g);line-height:1}
.mhdr-logo-ver{font-family:var(--mono);font-size:.45rem;color:var(--t2);letter-spacing:.15em;text-transform:uppercase;margin-top:3px}
.mhdr-title-block{flex:1}
.mhdr-eyebrow{
  font-family:var(--mono);font-size:.5rem;color:var(--t2);
  letter-spacing:.22em;text-transform:uppercase;margin-bottom:5px;
  display:flex;align-items:center;gap:8px;
}
.mhdr-eyebrow::before{content:'//';color:var(--g);font-weight:700}
.mhdr-title{
  font-size:1.65rem;font-weight:800;letter-spacing:-.04em;line-height:1;
  background:linear-gradient(100deg,#ddeeff 0%,#00f090 40%,#2d7fff 80%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.mhdr-sub{font-family:var(--mono);font-size:.52rem;color:var(--t2);letter-spacing:.1em;text-transform:uppercase;margin-top:4px}
.mhdr-chips{display:flex;gap:6px;align-items:center;margin-top:8px;flex-wrap:wrap}
.chip{
  display:inline-flex;align-items:center;gap:4px;
  font-family:var(--mono);font-size:.5rem;font-weight:600;
  letter-spacing:.1em;text-transform:uppercase;
  padding:3px 8px;border-radius:3px;border:1px solid;
}
.chip-live{color:var(--g);border-color:rgba(0,240,144,.3);background:var(--g3)}
.chip-live-dot{width:5px;height:5px;border-radius:50%;background:var(--g);animation:blink 1.2s step-end infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
.chip-time{color:var(--t2);border-color:var(--line2);background:transparent}
.chip-sched-on{color:var(--g);border-color:rgba(0,240,144,.3);background:var(--g3)}
.chip-sched-off{color:var(--t2);border-color:var(--line2);background:transparent}
.chip-v8{color:var(--p);border-color:rgba(168,85,247,.3);background:var(--p3)}
.chip-warn{color:var(--y);border-color:rgba(255,190,0,.3);background:var(--y3);animation:blink 2s step-end infinite}

.mhdr-stats{display:flex;gap:1px;align-self:stretch;border-left:1px solid var(--line2);flex-shrink:0}
.mhdr-stat{display:flex;flex-direction:column;justify-content:center;padding:0 20px;border-right:1px solid var(--line2)}
.mhdr-stat-n{font-family:var(--mono);font-size:1.1rem;font-weight:700;line-height:1}
.mhdr-stat-l{font-family:var(--mono);font-size:.46rem;color:var(--t2);text-transform:uppercase;letter-spacing:.14em;margin-top:3px}

.mhdr-bottom{
  display:flex;padding:7px 20px;gap:20px;
  font-family:var(--mono);font-size:.52rem;color:var(--t2);align-items:center;
  overflow:hidden;
}
.mhdr-ticker-item{display:flex;gap:6px;align-items:center}
.mhdr-ticker-code{color:var(--t1);font-weight:600}
.mhdr-ticker-chg-p{color:var(--g)}
.mhdr-ticker-chg-n{color:var(--r)}

/* ══════════════ ALERT BANNER ══════════════ */
.alert-banner{
  background:var(--bg1);border:1px solid rgba(255,190,0,.3);
  border-left:3px solid var(--y);border-radius:6px;
  padding:8px 14px;margin-bottom:10px;
  display:flex;align-items:center;gap:10px;
  font-family:var(--mono);font-size:.6rem;
  animation:pulse-border 2s ease-in-out infinite;
}
@keyframes pulse-border{0%,100%{border-left-color:var(--y)}50%{border-left-color:var(--o)}}
.alert-banner-ico{font-size:.8rem;flex-shrink:0}
.alert-banner-items{flex:1;display:flex;gap:16px;flex-wrap:wrap}
.alert-item{display:flex;gap:5px;align-items:center}
.alert-item-code{color:var(--g);font-weight:700}
.alert-item-msg{color:var(--y)}

/* ══════════════ SIDEBAR ══════════════ */
section[data-testid="stSidebar"]{background:var(--bg1)!important;border-right:1px solid var(--line)!important;min-width:270px!important}
section[data-testid="stSidebar"]>div{padding:0!important}
.sb-seg{border-bottom:1px solid var(--line)}
.sb-seg-hdr{
  display:flex;align-items:center;gap:8px;padding:10px 14px;
  font-family:var(--mono);font-size:.5rem;font-weight:700;
  color:var(--t2);text-transform:uppercase;letter-spacing:.18em;
  background:var(--bg2);border-bottom:1px solid var(--line);
}
.sb-seg-hdr-accent{width:6px;height:1px;background:var(--g)}
.sb-seg-body{padding:10px 14px}

/* watchlist row */
.wl-row{
  display:flex;align-items:center;gap:6px;padding:4px 6px;
  border-radius:4px;margin-bottom:2px;
  background:var(--bg2);border:1px solid var(--line);
}
.wl-code{font-family:var(--mono);font-size:.72rem;font-weight:700;color:var(--g);min-width:38px}
.wl-name{font-family:var(--mono);font-size:.6rem;color:var(--t1);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.wl-price{font-family:var(--mono);font-size:.62rem;color:var(--t0)}
.wl-chg-p{color:var(--g);font-size:.58rem}
.wl-chg-n{color:var(--r);font-size:.58rem}

/* search hit row */
.sh-row{
  display:flex;align-items:center;gap:8px;padding:6px 8px;
  border-radius:4px;margin-bottom:3px;
  background:var(--bg2);border:1px solid var(--line);
  transition:border-color .15s,background .15s;
}
.sh-row:hover{border-color:var(--line3);background:var(--bg3)}
.sh-code{font-family:var(--mono);font-size:.78rem;font-weight:700;color:var(--g);min-width:36px}
.sh-name{font-family:var(--mono);font-size:.62rem;color:var(--t1);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}

/* ══════════════ KPI STRIP ══════════════ */
.kpi-strip{display:grid;grid-template-columns:repeat(8,1fr);gap:5px;margin-bottom:10px}
.kpi{
  position:relative;overflow:hidden;
  background:var(--bg1);border:1px solid var(--line);
  border-radius:5px;padding:10px 12px;
  transition:border-color .2s,transform .2s;
}
.kpi:hover{border-color:var(--line3);transform:translateY(-1px)}
.kpi::before{content:'';position:absolute;bottom:0;left:0;right:0;height:1.5px}
.kpi.g::before{background:var(--g)}.kpi.r::before{background:var(--r)}
.kpi.y::before{background:var(--y)}.kpi.b::before{background:var(--b)}
.kpi.p::before{background:var(--p)}.kpi.c::before{background:var(--c)}
.kpi.o::before{background:var(--o)}.kpi.w::before{background:var(--t1)}
.kpi-l{font-family:var(--mono);font-size:.46rem;color:var(--t2);text-transform:uppercase;letter-spacing:.15em;margin-bottom:4px}
.kpi-v{font-family:var(--mono);font-size:1.25rem;font-weight:700;line-height:1;color:var(--t0)}
.kpi-v.g{color:var(--g)}.kpi-v.r{color:var(--r)}.kpi-v.y{color:var(--y)}
.kpi-v.b{color:var(--b)}.kpi-v.p{color:var(--p)}.kpi-v.c{color:var(--c)}.kpi-v.o{color:var(--o)}
.kpi-d{font-family:var(--mono);font-size:.48rem;color:var(--t2);margin-top:2px}

/* ══════════════ STOCK CARD ══════════════ */
.scard{background:var(--bg1);border:1px solid var(--line2);border-radius:8px;overflow:hidden;margin-bottom:10px}
.scard-top{display:grid;grid-template-columns:auto 1fr auto auto;gap:0;align-items:stretch;border-bottom:1px solid var(--line)}
.scard-accent{width:3px;background:linear-gradient(180deg,var(--g),var(--b),var(--p));flex-shrink:0}
.scard-id{padding:14px 18px;border-right:1px solid var(--line)}
.scard-code{font-family:var(--mono);font-size:1.4rem;font-weight:700;color:var(--t0);line-height:1}
.scard-suffix{font-size:.6rem;color:var(--t2);margin-left:5px}
.scard-name{font-family:var(--mono);font-size:.65rem;color:var(--t1);margin-top:3px}
.scard-mkt{font-family:var(--mono);font-size:.5rem;color:var(--t2);margin-top:1px}
.scard-price-block{padding:14px 18px;display:flex;flex-direction:column;justify-content:center;flex:1}
.scard-price{font-family:var(--mono);font-size:2rem;font-weight:700;line-height:1;color:var(--t0)}
.scard-price-unit{font-size:.7rem;color:var(--t2);margin-left:4px}
.scard-chg{font-family:var(--mono);font-size:.8rem;font-weight:600;margin-top:3px}
.scard-chg.pos{color:var(--g)}.scard-chg.neg{color:var(--r)}
.scard-signals{display:flex;flex-direction:column;justify-content:center;gap:6px;padding:14px 18px;border-left:1px solid var(--line)}
.scard-score-wrap{display:flex;align-items:center;gap:10px}
.score-hex{
  width:50px;height:50px;display:flex;align-items:center;justify-content:center;
  font-family:var(--mono);font-size:.88rem;font-weight:700;
  border-radius:8px;border:2px solid;
}
.sh-g{border-color:var(--g);color:var(--g);background:var(--g3);box-shadow:var(--glow-g)}
.sh-y{border-color:var(--y);color:var(--y);background:var(--y3)}
.sh-r{border-color:var(--r);color:var(--r);background:var(--r3);box-shadow:var(--glow-r)}

.sig{
  display:inline-flex;align-items:center;gap:5px;
  font-family:var(--mono);font-size:.6rem;font-weight:700;
  letter-spacing:.08em;padding:4px 10px;border-radius:3px;border:1px solid;
}
.sig-BUY{color:var(--g);border-color:rgba(0,240,144,.35);background:var(--g3)}
.sig-WATCH{color:var(--y);border-color:rgba(255,190,0,.35);background:var(--y3)}
.sig-HOLD{color:var(--t1);border-color:var(--line3);background:var(--bg3)}
.sig-AVOID{color:var(--r);border-color:rgba(255,51,88,.35);background:var(--r3)}

/* ── FUND GRID ── */
.fgrid{display:grid;grid-template-columns:repeat(6,1fr);gap:5px;margin:10px 0}
.fcell{background:var(--bg2);border:1px solid var(--line);border-radius:4px;padding:8px 10px;transition:border-color .15s,background .15s}
.fcell:hover{border-color:var(--line3);background:var(--bg3)}
.fcell-k{font-family:var(--mono);font-size:.44rem;color:var(--t2);text-transform:uppercase;letter-spacing:.12em;margin-bottom:3px}
.fcell-v{font-family:var(--mono);font-size:.8rem;font-weight:700;color:var(--t0)}
.fcell-v.pos{color:var(--g)}.fcell-v.neg{color:var(--r)}.fcell-v.warn{color:var(--y)}.fcell-v.neu{color:var(--b)}

/* ── TECH ROW ── */
.trow{display:grid;grid-template-columns:repeat(8,1fr);gap:5px;margin-top:5px}
.tcell{background:var(--bg2);border:1px solid var(--line);border-radius:4px;padding:7px 9px}
.tcell-k{font-family:var(--mono);font-size:.42rem;color:var(--t2);text-transform:uppercase;letter-spacing:.1em;margin-bottom:2px}
.tcell-v{font-family:var(--mono);font-size:.72rem;font-weight:700;color:var(--t0)}

/* ── RISK METER ── */
.risk-panel{background:var(--bg2);border:1px solid var(--line2);border-radius:6px;padding:12px 14px;margin-bottom:8px}
.risk-panel-lbl{font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.14em;margin-bottom:10px}
.risk-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.risk-cell{background:var(--bg3);border-radius:4px;padding:8px}
.risk-cell-k{font-family:var(--mono);font-size:.42rem;color:var(--t2);text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px}
.risk-cell-v{font-family:var(--mono);font-size:.85rem;font-weight:700}
.risk-meter{height:4px;background:var(--line);border-radius:2px;margin-top:4px;overflow:hidden}
.risk-meter-fill{height:100%;border-radius:2px}

/* ── INSTITUTION FLOW ── */
.inst-panel{background:var(--bg2);border:1px solid var(--line2);border-radius:6px;padding:12px 14px;margin-bottom:8px}
.inst-panel-lbl{font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.14em;margin-bottom:10px}
.inst-row{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--line)}
.inst-row:last-child{border-bottom:none}
.inst-name{font-family:var(--mono);font-size:.55rem;color:var(--t1);width:52px;flex-shrink:0}
.inst-bar-wrap{flex:1;height:6px;background:var(--line);border-radius:3px;overflow:visible;position:relative}
.inst-bar{height:100%;border-radius:3px;position:absolute;top:0}
.inst-bar.buy{background:linear-gradient(90deg,var(--g2),var(--g));left:50%}
.inst-bar.sell{background:linear-gradient(90deg,var(--r),var(--r2));right:50%}
.inst-val{font-family:var(--mono);font-size:.6rem;font-weight:700;width:60px;text-align:right}

/* ── PIVOT TABLE ── */
.pivot-panel{background:var(--bg2);border:1px solid var(--line2);border-radius:6px;padding:12px 14px;margin-bottom:8px}
.pivot-panel-lbl{font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.14em;margin-bottom:10px}
.pivot-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:5px}
.pivot-cell{background:var(--bg3);border-radius:4px;padding:7px;text-align:center}
.pivot-cell-k{font-family:var(--mono);font-size:.42rem;color:var(--t2);text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px}
.pivot-cell-v{font-family:var(--mono);font-size:.78rem;font-weight:700}
.pivot-cell.resist .pivot-cell-v{color:var(--r)}
.pivot-cell.pivot-p .pivot-cell-v{color:var(--y)}
.pivot-cell.support .pivot-cell-v{color:var(--g)}

/* ── TARGET PRICE ── */
.tpmaster{
  background:var(--bg2);border:1px solid var(--line2);border-radius:6px;padding:14px 16px;margin-bottom:8px;
  position:relative;overflow:hidden;
}
.tpmaster::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse 80% 60% at 50% 0%,rgba(0,240,144,.04) 0%,transparent 70%);
  pointer-events:none;
}
.tpmaster-lbl{font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.15em;margin-bottom:12px}
.tp-prices-row{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:10px}
.tp-price-item{text-align:center}
.tp-price-lbl{font-family:var(--mono);font-size:.44rem;color:var(--t2);text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px}
.tp-price-val{font-family:var(--mono);font-size:.9rem;font-weight:700}
.tp-price-val.cur{color:var(--t0)}.tp-price-val.tp{color:var(--g);font-size:1.1rem}
.tp-price-val.lo{color:var(--b)}.tp-price-val.hi{color:var(--p)}
.tp-upside-big{font-family:var(--mono);font-size:1.6rem;font-weight:700;line-height:1}
.tp-upside-big.pos{color:var(--g);text-shadow:var(--glow-g)}.tp-upside-big.neg{color:var(--r)}
.tp-track{position:relative;height:8px;background:var(--bg3);border-radius:4px;margin:10px 0 20px}
.tp-zone{position:absolute;height:100%;border-radius:4px;background:rgba(45,127,255,.25);border:1px solid rgba(45,127,255,.4)}
.tp-cur-line{position:absolute;top:-5px;width:2px;height:18px;background:#fff;border-radius:1px;transform:translateX(-50%);box-shadow:0 0 8px rgba(255,255,255,.7)}
.tp-tp-line{position:absolute;top:-5px;width:2px;height:18px;border-radius:1px;transform:translateX(-50%)}
.tp-label{position:absolute;font-family:var(--mono);font-size:.44rem;white-space:nowrap;transform:translateX(-50%)}
.tp-footnote{font-family:var(--mono);font-size:.48rem;color:var(--t2);margin-top:6px;line-height:1.6}

/* ── SCORE BARS ── */
.sbars{background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:12px 14px;margin-bottom:8px}
.sbars-lbl{font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.14em;margin-bottom:10px}
.sbar{display:flex;align-items:center;gap:8px;margin:6px 0}
.sbar-k{font-family:var(--mono);font-size:.55rem;color:var(--t1);width:52px;flex-shrink:0}
.sbar-track{flex:1;height:5px;background:var(--line);border-radius:2.5px;overflow:hidden}
.sbar-fill{height:100%;border-radius:2.5px;transition:width .5s ease}
.sbar-fill.g{background:linear-gradient(90deg,var(--g2),var(--g))}
.sbar-fill.y{background:linear-gradient(90deg,#cc9600,var(--y))}
.sbar-fill.r{background:linear-gradient(90deg,var(--r2),var(--r))}
.sbar-n{font-family:var(--mono);font-size:.55rem;color:var(--t1);width:40px;text-align:right;flex-shrink:0}

/* ── CHECKLIST ── */
.chklist{background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:12px 14px}
.chklist-lbl{font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.14em;margin-bottom:8px}
.chk-item{display:flex;align-items:center;gap:6px;padding:4px 0;border-bottom:1px solid var(--line)}
.chk-item:last-child{border-bottom:none}
.chk-icon{font-family:var(--mono);font-size:.6rem;font-weight:700;width:14px;flex-shrink:0}
.chk-lbl{font-family:var(--mono);font-size:.57rem}
.chk-ok .chk-icon{color:var(--g)}.chk-ok .chk-lbl{color:var(--t1)}
.chk-no .chk-icon{color:var(--t3)}.chk-no .chk-lbl{color:var(--t2)}

/* ── SIGNAL CARD ── */
.sigcard{border-radius:6px;padding:14px;margin-bottom:8px;border:1px solid;border-left:3px solid}
.sigcard.BUY{border-color:rgba(0,240,144,.25);border-left-color:var(--g);background:rgba(0,240,144,.04)}
.sigcard.WATCH{border-color:rgba(255,190,0,.25);border-left-color:var(--y);background:rgba(255,190,0,.04)}
.sigcard.HOLD{border-color:var(--line2);border-left-color:var(--t2);background:var(--bg2)}
.sigcard.AVOID{border-color:rgba(255,51,88,.25);border-left-color:var(--r);background:rgba(255,51,88,.04)}
.sigcard-title{font-family:var(--mono);font-size:.72rem;font-weight:700;margin-bottom:6px}
.sigcard-body{font-size:.7rem;color:var(--t1);line-height:1.65}

/* ── BACKTEST PANEL ── */
.bt-panel{background:var(--bg2);border:1px solid var(--line2);border-radius:6px;padding:12px 14px;margin-bottom:8px}
.bt-panel-lbl{font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.14em;margin-bottom:10px}
.bt-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}
.bt-stat{background:var(--bg3);border-radius:4px;padding:7px;text-align:center}
.bt-stat-k{font-family:var(--mono);font-size:.42rem;color:var(--t2);text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px}
.bt-stat-v{font-family:var(--mono);font-size:.82rem;font-weight:700}

/* ── INDUSTRY COMPARE ── */
.ind-panel{background:var(--bg2);border:1px solid var(--line2);border-radius:6px;padding:12px 14px;margin-bottom:8px}
.ind-panel-lbl{font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.14em;margin-bottom:10px}
.ind-row{display:grid;grid-template-columns:1fr repeat(4,auto);gap:10px;align-items:center;padding:5px 0;border-bottom:1px solid var(--line)}
.ind-row:last-child{border-bottom:none}
.ind-name{font-family:var(--mono);font-size:.55rem;color:var(--t1)}
.ind-val{font-family:var(--mono);font-size:.6rem;font-weight:700;text-align:right}
.ind-val.this{color:var(--g)}.ind-val.avg{color:var(--t2)}

/* ── VOLUME ANOMALY ── */
.vol-badge{
  display:inline-flex;align-items:center;gap:4px;
  font-family:var(--mono);font-size:.52rem;font-weight:700;
  padding:3px 8px;border-radius:3px;border:1px solid;
}
.vol-badge.high{color:var(--y);border-color:rgba(255,190,0,.35);background:var(--y3)}
.vol-badge.extreme{color:var(--r);border-color:rgba(255,51,88,.35);background:var(--r3);animation:blink 1s step-end infinite}
.vol-badge.normal{color:var(--t2);border-color:var(--line);background:transparent}

/* ── RESULT TABLE ── */
.rtw{overflow-x:auto;border:1px solid var(--line2);border-radius:7px}
.rt{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:.68rem}
.rt th{
  background:var(--bg2);color:var(--t2);text-transform:uppercase;
  letter-spacing:.1em;font-size:.48rem;font-weight:700;
  padding:9px 11px;text-align:left;border-bottom:1px solid var(--line2);
  white-space:nowrap;position:sticky;top:0;z-index:5;
}
.rt th:first-child{border-left:3px solid transparent}
.rt td{padding:8px 11px;border-bottom:1px solid var(--bg2);vertical-align:middle;white-space:nowrap}
.rt tr:last-child td{border-bottom:none}
.rt tr:hover td{background:var(--bg2)}
.rt tr.BUY   td:first-child{border-left:3px solid var(--g)}
.rt tr.WATCH td:first-child{border-left:3px solid var(--y)}
.rt tr.AVOID td:first-child{border-left:3px solid var(--r)}
.rt tr.HOLD  td:first-child{border-left:3px solid var(--line3)}
.rt td.pri{color:var(--t0);font-weight:700}
.rt td.tp{color:var(--b);font-weight:600}
.rt td.upp{color:var(--g);font-weight:700}
.rt td.upn{color:var(--r);font-weight:700}
.rt td.dim{color:var(--t2)}
.rt td.pos{color:var(--g)}.rt td.neg{color:var(--r)}.rt td.warn{color:var(--y)}

/* ── NEWS ── */
.nwrap{padding:2px 0}
.ni{display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid var(--bg2)}
.ni:last-child{border-bottom:none}
.ni-ic{flex-shrink:0;width:22px;height:22px;border-radius:3px;display:flex;align-items:center;justify-content:center;font-size:.6rem;font-weight:700}
.ni-ic.pos{background:var(--g3);color:var(--g)}.ni-ic.neg{background:var(--r3);color:var(--r)}.ni-ic.neu{background:var(--bg3);color:var(--t2)}
.ni-body{flex:1;min-width:0}
.ni-t{font-size:.77rem;color:var(--t1);margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ni-m{font-family:var(--mono);font-size:.54rem;color:var(--t2)}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"]{background:var(--bg1)!important;border-bottom:1px solid var(--line)!important;gap:0!important;padding:0!important}
.stTabs [data-baseweb="tab"]{
  font-family:var(--mono)!important;font-size:.6rem!important;font-weight:700!important;
  letter-spacing:.1em!important;color:var(--t2)!important;text-transform:uppercase!important;
  border-radius:0!important;padding:10px 20px!important;border-bottom:2px solid transparent!important;
}
.stTabs [aria-selected="true"]{color:var(--g)!important;border-bottom-color:var(--g)!important;background:rgba(0,240,144,.04)!important}

/* ── BUTTONS ── */
.stButton>button{
  font-family:var(--mono)!important;font-size:.65rem!important;font-weight:700!important;
  letter-spacing:.08em!important;border-radius:4px!important;text-transform:uppercase!important;transition:all .15s!important;
}
.stButton>button[kind="primary"]{background:var(--g)!important;color:#02040a!important;border:none!important}
.stButton>button[kind="primary"]:hover{box-shadow:var(--glow-g)!important;transform:translateY(-1px)!important}
.stButton>button:not([kind="primary"]){background:var(--bg2)!important;color:var(--t1)!important;border:1px solid var(--line2)!important}
.stButton>button:not([kind="primary"]):hover{border-color:var(--line3)!important;color:var(--t0)!important}

/* ── INPUTS ── */
.stTextInput>div>div>input,.stTextArea>div>div>textarea{
  background:var(--bg2)!important;border:1px solid var(--line2)!important;
  color:var(--t0)!important;border-radius:4px!important;
  font-family:var(--mono)!important;font-size:.72rem!important;
}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{
  border-color:var(--g)!important;box-shadow:0 0 0 1px rgba(0,240,144,.2)!important;
}
.stSlider>div>div>div>div{background:var(--g)!important}
.stProgress>div>div>div{background:var(--g)!important}
.stRadio>div{gap:6px!important}
label[data-baseweb="radio"]>div:first-child{background:var(--bg2)!important;border-color:var(--line2)!important}
label[data-baseweb="radio"][aria-checked="true"]>div:first-child{background:var(--g)!important;border-color:var(--g)!important}
.streamlit-expanderHeader{
  background:var(--bg1)!important;border:1px solid var(--line)!important;
  border-radius:5px!important;font-family:var(--mono)!important;
  font-size:.62rem!important;font-weight:700!important;color:var(--t1)!important;letter-spacing:.06em!important;
}
hr{border-color:var(--line)!important;margin:6px 0!important}
.empty-state{text-align:center;padding:50px 0}
.empty-state-ico{font-size:2.4rem;margin-bottom:12px}
.empty-state-txt{font-family:var(--mono);font-size:.72rem;color:var(--t2);line-height:1.8}

/* ── LOG ── */
.logwrap{background:var(--bg1);border:1px solid var(--line);border-radius:6px;padding:12px 16px;font-family:var(--mono)}
.ll{font-size:.62rem;padding:2px 0;line-height:1.5}
.ll.ok{color:var(--g)}.ll.err{color:var(--r)}.ll.inf{color:var(--b)}.ll.dim{color:var(--t2)}

/* ── FINANCIAL HEALTH ── */
.fh-panel{background:var(--bg2);border:1px solid var(--line2);border-radius:6px;padding:12px 14px;margin-bottom:8px}
.fh-panel-lbl{font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.14em;margin-bottom:10px}
.fh-score-ring{
  width:64px;height:64px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;flex-direction:column;
  border:3px solid;flex-shrink:0;
}
.fh-score-ring.A{border-color:var(--g);background:rgba(0,240,144,.08)}
.fh-score-ring.B{border-color:var(--b);background:rgba(45,127,255,.08)}
.fh-score-ring.C{border-color:var(--y);background:rgba(255,190,0,.08)}
.fh-score-ring.D{border-color:var(--r);background:rgba(255,51,88,.08)}
.fh-score-grade{font-family:var(--mono);font-size:1.2rem;font-weight:700;line-height:1}
.fh-score-lbl{font-family:var(--mono);font-size:.38rem;color:var(--t2);text-transform:uppercase;letter-spacing:.1em;margin-top:1px}
.fh-top{display:flex;gap:12px;align-items:center;margin-bottom:10px}
.fh-metrics{flex:1;display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.fh-metric{background:var(--bg3);border-radius:4px;padding:6px 8px}
.fh-metric-k{font-family:var(--mono);font-size:.4rem;color:var(--t2);text-transform:uppercase;margin-bottom:2px}
.fh-metric-v{font-family:var(--mono);font-size:.75rem;font-weight:700}

/* ── BULL BEAR GAUGE ── */
.bb-panel{background:var(--bg2);border:1px solid var(--line2);border-radius:6px;padding:12px 14px;margin-bottom:8px}
.bb-panel-lbl{font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.14em;margin-bottom:8px}
.bb-gauge{height:10px;border-radius:5px;overflow:hidden;position:relative;background:var(--line);margin-bottom:6px}
.bb-fill{position:absolute;top:0;height:100%;border-radius:5px;transition:width .8s ease}
.bb-fill.bull{background:linear-gradient(90deg,rgba(0,240,144,.5),var(--g));left:0}
.bb-fill.bear{background:linear-gradient(90deg,var(--r),rgba(255,51,88,.5));right:0}
.bb-labels{display:flex;justify-content:space-between;font-family:var(--mono);font-size:.48rem}

/* Selectbox */
.stSelectbox>div>div{background:var(--bg2)!important;border:1px solid var(--line2)!important;border-radius:4px!important}
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ═════════════════════════════════════════════════════════════════════════════
_DEF = {
    "scan_results":[], "scheduler":None, "sched_running":False,
    "sched_log":[], "last_scan_time":None, "auto_webhook":"",
    "scan_params":{}, "scan_codes":[], "selected_stock":None,
    "detail_cache":{}, "watchlist":[], "alerts":[],
    "alert_config":{},  # code -> {rsi_high, rsi_low, price_above, price_below}
    "line_token":"",
}
for k,v in _DEF.items():
    if k not in st.session_state: st.session_state[k]=v

# ═════════════════════════════════════════════════════════════════════════════
# STOCK NAMES
# ═════════════════════════════════════════════════════════════════════════════
_BUILTIN: Dict[str,str] = {
    "2330":"台積電","2317":"鴻海","2454":"聯發科","2308":"台達電","2382":"廣達",
    "2357":"華碩","2412":"中華電","3008":"大立光","2395":"研華","2303":"聯電",
    "2881":"富邦金","2882":"國泰金","2886":"兆豐金","2884":"玉山金","2885":"元大金",
    "2891":"中信金","2883":"開發金","2887":"台新金","2890":"永豐金","2892":"第一金",
    "1301":"台塑","1303":"南亞","1326":"台化","6505":"台塑化","2002":"中鋼",
    "2207":"和泰車","2912":"統一超","5871":"中租-KY","3711":"日月光投控",
    "2301":"光寶科","2354":"鴻準","2324":"仁寶","2347":"聯強","2327":"國巨",
    "3045":"台灣大","4904":"遠傳","2409":"友達","2408":"南亞科","2376":"技嘉",
    "2379":"瑞昱","6415":"矽力-KY","3034":"聯詠","3037":"欣興","2344":"華邦電",
    "2498":"宏達電","6669":"緯穎","2823":"中壽","2615":"萬海","2603":"長榮",
    "2609":"陽明","2610":"華航","2618":"長榮航","5876":"上海商銀","8046":"南電",
    "3481":"群創","2356":"英業達","2337":"旺宏","2449":"京元電子","3231":"緯創",
    "2352":"佳世達","5274":"信驊","4938":"和碩","2474":"可成","2360":"致茂",
    "3443":"創意","2385":"群光","6285":"啟碁","4919":"新唐","2059":"川湖",
    "2049":"上銀","1590":"亞德客-KY","2105":"正新","2201":"裕隆","2204":"中華",
    "1216":"統一","1102":"亞泥","1101":"台泥","2542":"興富發","5880":"合庫金",
    "2634":"漢翔","6770":"力積電","3529":"力旺","3661":"世芯-KY","6510":"精測",
    "8299":"群聯","2388":"威盛","3532":"台勝科","6472":"保瑞","3035":"智原",
    "4966":"譜瑞-KY","6278":"台表科","3260":"威剛","2404":"漢唐","6582":"申豐",
    "3714":"富采","6488":"環球晶","3013":"映泰","2233":"宏致","2206":"三陽工業",
    "9910":"豐泰","2014":"中鴻","6116":"彩晶","2368":"金像電","3149":"正達",
    "2478":"大毅","6271":"同欣電","2397":"友通","3227":"原相","4961":"天鈺",
    "5234":"達興材料","6269":"台郡","6451":"訊芯-KY","3016":"嘉晶","2227":"裕日車",
    "2383":"台光電","4958":"臻鼎-KY","2347":"聯強","3006":"晶豪科","6547":"高端疫苗",
}

# 產業分類
_INDUSTRY: Dict[str,str] = {
    "2330":"半導體","2317":"電子製造","2454":"半導體","2382":"電子製造",
    "2881":"金融","2882":"金融","2886":"金融","2884":"金融","2885":"金融",
    "2891":"金融","2892":"金融","1301":"塑化","1303":"塑化","6505":"塑化",
    "2002":"鋼鐵","2603":"航運","2609":"航運","2615":"航運",
    "2412":"電信","3045":"電信","4904":"電信",
    "2308":"電子零件","2395":"電腦設備","3008":"光學","2303":"半導體",
    "6669":"伺服器","2357":"電腦設備","5871":"金融租賃","3711":"封測",
}

@st.cache_data(ttl=3600, show_spinner=False)
def load_names() -> Dict[str,str]:
    names = dict(_BUILTIN)
    hdr = {"User-Agent":"Mozilla/5.0"}
    for url, code_key, name_key in [
        ("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL","Code","Name"),
        ("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes","SecuritiesCompanyCode","CompanyName"),
    ]:
        try:
            r = requests.get(url, headers=hdr, timeout=12, verify=False)
            if r.status_code == 200:
                for it in r.json():
                    c = it.get(code_key,"").strip(); n = it.get(name_key,"").strip()
                    if len(c)==4 and c.isdigit() and n: names[c]=n
        except: pass
    return names

def search(q:str, names:Dict[str,str], limit:int=10) -> List[Tuple[str,str]]:
    if not q.strip(): return []
    qu = q.strip().upper(); ql = q.strip().lower()
    t1,t2,t3 = [],[],[]
    for code,name in names.items():
        if code==qu:                 t1.append((code,name))
        elif code.startswith(qu):    t2.append((code,name))
        elif ql in name.lower() or ql in code.lower(): t3.append((code,name))
    seen,out = set(),[]
    for item in t1+t2+t3:
        if item[0] not in seen: seen.add(item[0]); out.append(item)
    return out[:limit]

# ═════════════════════════════════════════════════════════════════════════════
# TICKER RESOLUTION
# ═════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=86400, show_spinner=False)
def resolve_suffix(code:str) -> str:
    for sfx in [".TW",".TWO"]:
        try:
            p = getattr(yf.Ticker(code+sfx).fast_info,"last_price",None)
            if p and float(p)>0: return sfx
        except: pass
    return ".TW"

# ═════════════════════════════════════════════════════════════════════════════
# TECHNICALS
# ═════════════════════════════════════════════════════════════════════════════
def _rsi(s:pd.Series,n:int=14)->pd.Series:
    d=s.diff(); g=d.clip(lower=0).ewm(com=n-1,min_periods=n).mean()
    l=(-d).clip(lower=0).ewm(com=n-1,min_periods=n).mean()
    return 100-100/(1+g/l)

def _macd(s:pd.Series):
    m=s.ewm(span=12,adjust=False).mean()-s.ewm(span=26,adjust=False).mean()
    return m,m.ewm(span=9,adjust=False).mean()

def _bb(s:pd.Series,n:int=20):
    m=s.rolling(n).mean(); std=s.rolling(n).std()
    return m+2*std,m,m-2*std

def _atr(h:pd.Series,l:pd.Series,c:pd.Series,n:int=14)->pd.Series:
    tr=pd.concat([h-l,(h-c.shift()).abs(),(l-c.shift()).abs()],axis=1).max(axis=1)
    return tr.rolling(n).mean()

def _pivot_points(h:float,l:float,c:float)->Dict[str,float]:
    p=(h+l+c)/3
    return {
        "PP":round(p,2),"R1":round(2*p-l,2),"R2":round(p+(h-l),2),"R3":round(h+2*(p-l),2),
        "S1":round(2*p-h,2),"S2":round(p-(h-l),2),"S3":round(l-2*(h-p),2)
    }

def _sharpe(returns:pd.Series)->float:
    if len(returns)<10: return 0.0
    mean_r=returns.mean()*252; std_r=returns.std()*np.sqrt(252)
    return round(mean_r/std_r,2) if std_r>0 else 0.0

def _max_drawdown(prices:pd.Series)->float:
    roll_max=prices.expanding().max()
    drawdown=(prices-roll_max)/roll_max
    return round(float(drawdown.min())*100,1)

def _beta(stock_returns:pd.Series,mkt_returns:pd.Series)->float:
    if len(stock_returns)<30: return 1.0
    cov=np.cov(stock_returns.dropna(),mkt_returns.dropna())
    return round(cov[0,1]/cov[1,1],2) if cov[1,1]>0 else 1.0

def _volume_anomaly(vol:pd.Series)->Tuple[float,str]:
    """回傳(倍率, 狀態) 與20日均量比"""
    if len(vol)<20: return 1.0,"normal"
    avg=vol.rolling(20).mean().iloc[-1]
    last=vol.iloc[-1]
    ratio=last/avg if avg>0 else 1.0
    if ratio>=3:   return ratio,"extreme"
    elif ratio>=2: return ratio,"high"
    return ratio,"normal"

# ═════════════════════════════════════════════════════════════════════════════
# TARGET PRICE — 12個月估算，永遠 > 現價
# ═════════════════════════════════════════════════════════════════════════════
def estimate_target(price, pe, eps, pb, roe, div_yield,
                    analyst_mean, analyst_low, analyst_high, n_analysts,
                    rsi=None, macd=None, macd_signal=None,
                    revenue_growth=None) -> Tuple[Optional[float],Optional[float],Optional[float]]:
    if not price or price <= 0:
        return None, None, None

    upside_rate = 0.0
    upside_rate += 0.08  # 基礎溢價

    if roe and roe > 0:
        r = roe * 100
        if r >= 25:    upside_rate += 0.08
        elif r >= 18:  upside_rate += 0.05
        elif r >= 12:  upside_rate += 0.03
        elif r >= 8:   upside_rate += 0.01

    if div_yield and div_yield > 0:
        y = div_yield * 100
        if y >= 6:    upside_rate += 0.04
        elif y >= 4:  upside_rate += 0.02
        elif y >= 2:  upside_rate += 0.01

    if revenue_growth and revenue_growth > 0:
        g = revenue_growth * 100
        if g >= 30:   upside_rate += 0.06
        elif g >= 15: upside_rate += 0.03
        elif g >= 5:  upside_rate += 0.01

    if pe and 0 < pe <= 15:
        upside_rate += 0.03

    if rsi and 35 <= rsi <= 60:
        upside_rate += 0.02
    if macd is not None and macd_signal is not None and macd > macd_signal:
        upside_rate += 0.02

    model_target = price * (1 + upside_rate)
    final_target = model_target

    if analyst_mean and analyst_mean > price and n_analysts and n_analysts >= 3:
        w_analyst = min(0.6, 0.2 + n_analysts * 0.04)
        w_model = 1 - w_analyst
        final_target = analyst_mean * w_analyst + model_target * w_model

    final_target = max(final_target, price * 1.05)
    final_target = round(final_target, 1)

    if analyst_low and analyst_low > price:
        tl = round(max(analyst_low, price * 1.03), 1)
    else:
        tl = round(price * (1 + upside_rate * 0.6), 1)

    if analyst_high and analyst_high > price:
        th = round(analyst_high, 1)
    else:
        th = round(price * (1 + upside_rate * 1.6), 1)

    tl = min(tl, final_target * 0.97)
    th = max(th, final_target * 1.08)

    return final_target, round(tl,1), round(th,1)

# ═════════════════════════════════════════════════════════════════════════════
# COMPOSITE SCORE (v8 升級版 — 加入風險、量能維度)
# ═════════════════════════════════════════════════════════════════════════════
def composite_score(d:dict)->Tuple[int,Dict[str,int],str]:
    total,det=0,{}
    px=d.get("price",0); ma5=d.get("ma5"); ma20=d.get("ma20"); ma60=d.get("ma60")
    rsi=d.get("rsi"); macd=d.get("macd"); macd_s=d.get("macd_signal")
    bb_u=d.get("bb_upper"); bb_l=d.get("bb_lower")
    pe=d.get("pe"); pb=d.get("pb"); roe=d.get("roe")
    dy=d.get("dividend_yield"); pm=d.get("profit_margin"); rg=d.get("revenue_growth")
    beta=d.get("beta"); vol_ratio=d.get("volume_ratio",1.0)
    current_ratio=d.get("current_ratio"); debt_ratio=d.get("debt_to_equity")

    # 技術 35
    tech=0
    if px and ma5 and ma20:
        if px>ma5>ma20:   tech+=10
        elif px>ma20:     tech+=6
        if ma60 and ma20>ma60: tech+=2
    if rsi is not None:
        if 40<=rsi<=60:   tech+=10
        elif 30<=rsi<40:  tech+=7
        elif 60<rsi<=70:  tech+=5
        elif rsi<30:      tech+=6
    if macd is not None and macd_s is not None:
        if macd>macd_s:   tech+=(9 if macd>0 else 4)
    if bb_u and bb_l and px:
        bw=bb_u-bb_l
        if bw>0:
            pos=(px-bb_l)/bw
            if .2<=pos<=.55: tech+=6
            elif pos<.2:     tech+=4
    det["技術"]=min(tech,35); total+=det["技術"]

    # 基本面 30
    fund=0
    if pe:
        if 6<=pe<=14:    fund+=10
        elif 14<pe<=20:  fund+=7
        elif pe<6:       fund+=4
    if pb:
        if .5<=pb<=2:    fund+=7
        elif 2<pb<=3:    fund+=3
    if roe:
        r=roe*100
        if r>=20:   fund+=9
        elif r>=12: fund+=6
        elif r>=8:  fund+=3
    if dy:
        y=dy*100
        if y>=5:   fund+=4
        elif y>=3: fund+=2
    det["基本面"]=min(fund,30); total+=det["基本面"]

    # 動能 20
    mom=0
    up=d.get("upside")
    if up is not None:
        if up>=25:   mom+=10
        elif up>=15: mom+=7
        elif up>=8:  mom+=5
        elif up>=3:  mom+=2
    if rg:
        r=rg*100
        if r>=20:   mom+=8
        elif r>=10: mom+=5
        elif r>=3:  mom+=2
    det["動能"]=max(min(mom,20),0); total+=det["動能"]

    # 財務健康 10（新增）
    health=0
    if current_ratio:
        if current_ratio>=2:  health+=5
        elif current_ratio>=1.5: health+=3
        elif current_ratio>=1:   health+=1
    if debt_ratio is not None:
        if debt_ratio<=0.5:  health+=5
        elif debt_ratio<=1:  health+=3
        elif debt_ratio<=2:  health+=1
    det["財務健康"]=min(health,10); total+=det["財務健康"]

    # 量能加分 5（新增）
    vol_pts=0
    if vol_ratio and 1.5<=vol_ratio<=4: vol_pts+=3
    if vol_ratio and vol_ratio>4:       vol_pts+=2  # 量太大也不加滿
    if pm and pm>0.15:                  vol_pts+=2
    det["量能"]=min(vol_pts,5); total+=det["量能"]

    total=max(min(total,100),0)
    sig="BUY" if total>=70 else ("WATCH" if total>=53 else ("HOLD" if total>=36 else "AVOID"))
    return total,det,sig

# ═════════════════════════════════════════════════════════════════════════════
# FINANCIAL HEALTH GRADE
# ═════════════════════════════════════════════════════════════════════════════
def financial_health_grade(d:dict)->Tuple[str,int]:
    score=0
    cr=d.get("current_ratio")
    de=d.get("debt_to_equity")
    pm=d.get("profit_margin")
    roe=d.get("roe")
    rg=d.get("revenue_growth")

    if cr:
        if cr>=2:    score+=25
        elif cr>=1.5: score+=18
        elif cr>=1:   score+=10
    if de is not None:
        if de<=0.5:  score+=25
        elif de<=1:  score+=18
        elif de<=2:  score+=10
    if pm:
        if pm>=0.2:  score+=20
        elif pm>=0.1: score+=14
        elif pm>=0.05: score+=8
    if roe:
        r=roe*100
        if r>=20:   score+=15
        elif r>=12: score+=10
        elif r>=8:  score+=5
    if rg:
        if rg>=0.2:  score+=15
        elif rg>=0.1: score+=10
        elif rg>=0:   score+=5

    grade="A" if score>=75 else ("B" if score>=55 else ("C" if score>=35 else "D"))
    return grade,score

# ═════════════════════════════════════════════════════════════════════════════
# BACKTEST — 簡易歷史信號回測
# ═════════════════════════════════════════════════════════════════════════════
def simple_backtest(hist:pd.DataFrame)->Dict[str,Any]:
    """基於 MA5>MA20 作為買進信號，計算歷史報酬"""
    if hist is None or len(hist)<40:
        return {}
    c=hist["Close"]
    ma5=c.rolling(5).mean()
    ma20=c.rolling(20).mean()
    # 信號：ma5剛超過ma20 = 買入
    signal=(ma5>ma20).astype(int)
    signal_prev=signal.shift(1).fillna(0)
    buy_signal=(signal==1)&(signal_prev==0)

    trades=[]
    in_trade=False; buy_price=0.0
    for i in range(len(hist)):
        if buy_signal.iloc[i] and not in_trade:
            buy_price=float(c.iloc[i]); in_trade=True
        elif in_trade and (signal.iloc[i]==0 or i==len(hist)-1):
            sell_price=float(c.iloc[i])
            ret=(sell_price-buy_price)/buy_price*100
            trades.append(ret); in_trade=False

    if not trades:
        return {}

    win_trades=[t for t in trades if t>0]
    ret_arr=pd.Series(c).pct_change().dropna()
    ann_vol=float(ret_arr.std()*np.sqrt(252)*100)
    mdd=_max_drawdown(c)

    return {
        "trades":len(trades),
        "win_rate":round(len(win_trades)/len(trades)*100,1),
        "avg_return":round(np.mean(trades),1),
        "max_win":round(max(trades),1),
        "max_loss":round(min(trades),1),
        "ann_vol":round(ann_vol,1),
        "max_drawdown":mdd,
    }

# ═════════════════════════════════════════════════════════════════════════════
# FETCH STOCK (v8 — 完整增強版)
# ═════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=180, show_spinner=False)
def fetch_stock(code:str)->dict:
    D={
        "code":code,"name":code,"suffix":".TW","error":None,
        "price":None,"prev_close":None,"open":None,"high":None,"low":None,
        "volume":None,"avg_volume":None,"market_cap":None,
        "pe":None,"pb":None,"eps":None,"roe":None,
        "dividend_yield":None,"profit_margin":None,"revenue_growth":None,
        "current_ratio":None,"quick_ratio":None,"debt_to_equity":None,
        "target_price":None,"target_low":None,"target_high":None,"upside":None,
        "analyst_count":0,"ma5":None,"ma20":None,"ma60":None,"ma120":None,
        "rsi":None,"rsi_fast":None,"macd":None,"macd_signal":None,
        "bb_upper":None,"bb_lower":None,"bb_mid":None,"atr":None,
        "beta":None,"volume_ratio":1.0,"volume_status":"normal",
        "pivot":{},"backtest":{},"sharpe":0.0,"max_drawdown":0.0,
        "hist":None,"score":0,"score_detail":{},"signal":"HOLD",
        "industry":None,"fin_health_grade":"C","fin_health_score":0,
        # 三大法人（台灣無法從yfinance取得，用估算模擬）
        "foreign_net":None,"trust_net":None,"dealer_net":None,
    }
    try:
        sfx=resolve_suffix(code); D["suffix"]=sfx
        tk=yf.Ticker(code+sfx); info=tk.info
        D["name"]=(info.get("longName") or info.get("shortName") or code).strip()
        D["industry"]=_INDUSTRY.get(code, info.get("sector","—"))

        # ── 價格 ──
        D["price"]=info.get("currentPrice") or info.get("regularMarketPrice")
        D["prev_close"]=info.get("previousClose") or info.get("regularMarketPreviousClose")
        D["open"]=info.get("open") or info.get("regularMarketOpen")
        D["high"]=info.get("dayHigh") or info.get("regularMarketDayHigh")
        D["low"]=info.get("dayLow") or info.get("regularMarketDayLow")
        D["volume"]=info.get("volume") or info.get("regularMarketVolume")
        D["avg_volume"]=info.get("averageVolume") or info.get("averageVolume10days")
        D["market_cap"]=info.get("marketCap")

        if not D["price"]:
            fi=tk.fast_info
            D["price"]=getattr(fi,"last_price",None)
            D["prev_close"]=getattr(fi,"previous_close",None)

        # ── 基本面 ──
        D["pe"]=info.get("trailingPE") or info.get("forwardPE")
        D["pb"]=info.get("priceToBook")
        D["eps"]=info.get("trailingEps") or info.get("forwardEps")
        D["roe"]=info.get("returnOnEquity")
        D["dividend_yield"]=info.get("dividendYield")
        D["profit_margin"]=info.get("profitMargins")
        D["revenue_growth"]=info.get("revenueGrowth")
        D["analyst_count"]=info.get("numberOfAnalystOpinions") or 0

        # ── 財務健康（v8新增）──
        D["current_ratio"]=info.get("currentRatio")
        D["quick_ratio"]=info.get("quickRatio")
        D["debt_to_equity"]=info.get("debtToEquity")
        if D["debt_to_equity"]: D["debt_to_equity"]=D["debt_to_equity"]/100  # 轉成比率

        # Beta
        D["beta"]=info.get("beta")

        # ── 歷史 & 技術指標 ──
        hist=tk.history(period="1y",auto_adjust=True)
        if hist is not None and not hist.empty and len(hist)>=20:
            D["hist"]=hist; c=hist["Close"]

            # 均線
            D["ma5"] =float(c.rolling(5).mean().iloc[-1])
            D["ma20"]=float(c.rolling(20).mean().iloc[-1])
            if len(c)>=60:  D["ma60"] =float(c.rolling(60).mean().iloc[-1])
            if len(c)>=120: D["ma120"]=float(c.rolling(120).mean().iloc[-1])

            # RSI
            D["rsi"]     =float(_rsi(c,14).iloc[-1])
            D["rsi_fast"]=float(_rsi(c,6).iloc[-1])

            # MACD
            ml,sl=_macd(c); D["macd"]=float(ml.iloc[-1]); D["macd_signal"]=float(sl.iloc[-1])

            # 布林
            bu,bm,bl=_bb(c)
            D["bb_upper"]=float(bu.iloc[-1]); D["bb_mid"]=float(bm.iloc[-1]); D["bb_lower"]=float(bl.iloc[-1])

            # ATR
            if len(hist)>=15:
                D["atr"]=float(_atr(hist["High"],hist["Low"],hist["Close"],14).iloc[-1])

            # Pivot Points（用最近一日高低收）
            if len(hist)>=2:
                y=hist.iloc[-2]
                D["pivot"]=_pivot_points(float(y["High"]),float(y["Low"]),float(y["Close"]))

            # 量能異常
            if "Volume" in hist.columns and len(hist["Volume"])>=21:
                ratio,status=_volume_anomaly(hist["Volume"])
                D["volume_ratio"]=round(ratio,2); D["volume_status"]=status

            # 風險指標
            returns=c.pct_change().dropna()
            D["sharpe"]=_sharpe(returns)
            D["max_drawdown"]=_max_drawdown(c)

            # 三大法人（估算：基於價量關係推算機構行為）
            # 台灣yfinance沒有直接三大法人資料，用技術推估買賣方向
            if len(hist)>=5:
                # 以近5日大額成交推估外資動向（價漲+量增 -> 買超；價跌+量增 -> 賣超）
                recent=hist.tail(5)
                price_trend=float(recent["Close"].iloc[-1]-recent["Close"].iloc[0])/float(recent["Close"].iloc[0])
                vol_trend=float(recent["Volume"].mean())
                avg_vol_long=float(hist["Volume"].mean())
                vol_mult=vol_trend/avg_vol_long if avg_vol_long>0 else 1
                est_flow=price_trend*vol_mult*D["market_cap"]/1e8 if D["market_cap"] else None
                if est_flow is not None:
                    D["foreign_net"]=round(est_flow*0.6,1)       # 外資估約60%
                    D["trust_net"]=round(est_flow*0.25,1)          # 投信25%
                    D["dealer_net"]=round(est_flow*0.15,1)          # 自營商15%

            # 回測
            D["backtest"]=simple_backtest(hist)

        # ── 目標價 ──
        tp,tl,th=estimate_target(
            D["price"],D["pe"],D["eps"],D["pb"],D["roe"],D["dividend_yield"],
            info.get("targetMeanPrice"),info.get("targetLowPrice"),info.get("targetHighPrice"),
            D["analyst_count"],D["rsi"],D["macd"],D["macd_signal"],D["revenue_growth"],
        )
        D["target_price"]=tp; D["target_low"]=tl; D["target_high"]=th
        if D["price"] and tp: D["upside"]=(tp-D["price"])/D["price"]*100

        # ── 評分 ──
        D["score"],D["score_detail"],D["signal"]=composite_score(D)

        # ── 財務健康評級 ──
        D["fin_health_grade"],D["fin_health_score"]=financial_health_grade(D)

    except Exception as e:
        D["error"]=str(e)
    return D

# ═════════════════════════════════════════════════════════════════════════════
# BATCH SCAN — 16 線程並行
# ═════════════════════════════════════════════════════════════════════════════
def scan_batch(codes:List[str],min_score:int=55,min_upside:float=5.0,
               max_pe:float=50.0,signal_filter:str="全部",
               progress_cb=None,max_workers:int=16)->List[dict]:
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs={ex.submit(fetch_stock,c):c for c in codes}
        done=0
        for fut in concurrent.futures.as_completed(futs):
            done+=1
            if progress_cb: progress_cb(done,len(codes),futs[fut])
            try:
                d=fut.result()
                if not d.get("price"): continue
                if d.get("score",0)<min_score: continue
                up=d.get("upside")
                if up is not None and up<min_upside: continue
                pe=d.get("pe")
                if pe is not None and pe>max_pe: continue
                if signal_filter!="全部" and d.get("signal")!=signal_filter: continue
                results.append(d)
            except: pass
    results.sort(key=lambda x:x.get("score",0),reverse=True)
    return results

# ═════════════════════════════════════════════════════════════════════════════
# WATCHLIST PRICES (輕量版)
# ═════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def fetch_watchlist_prices(codes_tuple:tuple)->Dict[str,dict]:
    res={}
    def _fetch(code):
        try:
            sfx=resolve_suffix(code); tk=yf.Ticker(code+sfx)
            fi=tk.fast_info
            px=getattr(fi,"last_price",None)
            pc=getattr(fi,"previous_close",None)
            if px and pc:
                chg=(px-pc)/pc*100
                res[code]={"price":px,"chg":chg}
        except: pass
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(_fetch, codes_tuple))
    return res

# ═════════════════════════════════════════════════════════════════════════════
# ALERTS CHECK
# ═════════════════════════════════════════════════════════════════════════════
def check_alerts(d:dict)->List[str]:
    code=d.get("code"); alerts=[]
    cfg=st.session_state.alert_config.get(code,{})
    px=d.get("price"); rsi=d.get("rsi"); ma20=d.get("ma20")

    if rsi and rsi>75: alerts.append(f"{code} RSI={rsi:.0f} 超買")
    if rsi and rsi<25: alerts.append(f"{code} RSI={rsi:.0f} 超賣")
    if px and ma20 and abs(px-ma20)/ma20<0.005: alerts.append(f"{code} 接近MA20支撐/壓力")
    if d.get("volume_status")=="extreme": alerts.append(f"{code} 爆量異常 {d.get('volume_ratio',1):.1f}x")

    # 自訂警示
    if cfg.get("price_above") and px and px>=cfg["price_above"]:
        alerts.append(f"{code} 突破設定價 {cfg['price_above']}")
    if cfg.get("price_below") and px and px<=cfg["price_below"]:
        alerts.append(f"{code} 跌破設定價 {cfg['price_below']}")
    return alerts

# ═════════════════════════════════════════════════════════════════════════════
# NEWS
# ═════════════════════════════════════════════════════════════════════════════
_POS=["上漲","漲停","創高","突破","強勢","獲利","配息","利多","成長","亮眼","超越","優於","買進","增加","新高","大漲"]
_NEG=["下跌","跌停","創低","破底","虧損","利空","衰退","慘澹","低於","警示","賣出","停損","減少","崩跌","大跌"]

def _sent(t:str)->str:
    s=sum(1 for w in _POS if w in t)-sum(1 for w in _NEG if w in t)
    return "pos" if s>0 else ("neg" if s<0 else "neu")

@st.cache_data(ttl=600,show_spinner=False)
def fetch_news(code:str,name:str)->List[dict]:
    news=[]; hdr={"User-Agent":"Mozilla/5.0"}
    for url,sel in [
        (f"https://tw.stock.yahoo.com/quote/{code}.TW/news","h3 a"),
        (f"https://news.cnyes.com/news/cat/twstock?code={code}","a[href*='/news/id/']"),
    ]:
        if news: break
        try:
            soup=BeautifulSoup(requests.get(url,headers=hdr,timeout=8,verify=False).text,"lxml")
            for a in soup.select(sel)[:12]:
                t=a.get_text(strip=True)
                if len(t)<8: continue
                src="Yahoo Finance" if "yahoo" in url else "鉅亨網"
                news.append({"t":t,"url":a.get("href",""),"s":_sent(t),"src":src})
        except: pass
    return news[:10]

# ═════════════════════════════════════════════════════════════════════════════
# PUSH — Discord + LINE Notify
# ═════════════════════════════════════════════════════════════════════════════
def push_discord(url:str,results:List[dict])->bool:
    if not url or not results: return False
    try:
        now=datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        fields=[]
        for d in results[:10]:
            p,tp,up=d.get("price"),d.get("target_price"),d.get("upside")
            em={"BUY":"🟢","WATCH":"🟡","HOLD":"⚪","AVOID":"🔴"}.get(d.get("signal",""),"⚪")
            fhg=d.get("fin_health_grade","—")
            v=f"`現價 {p:.1f}` ➜ `目標 {tp:.1f}` (**{up:+.1f}%**) · 財健 {fhg}" if (p and tp and up is not None) else "—"
            fields.append({"name":f"{em} {d['code']} {d.get('name','')} · {d.get('score',0)}分","value":v,"inline":False})
        r=requests.post(url,json={"embeds":[{
            "title":f"⚡ 台股狙擊手 ULTRA v8 · {now}",
            "color":0x00f090,
            "fields":fields,
            "footer":{"text":"台股AI狙擊手 · 僅供參考，投資有風險"}
        }]},timeout=8)
        return r.status_code in(200,204)
    except: return False

def push_line(token:str,results:List[dict])->bool:
    if not token or not results: return False
    try:
        now=datetime.datetime.now().strftime("%m/%d %H:%M")
        msg=f"\n⚡ 台股狙擊手 v8 · {now}\n"+"─"*25+"\n"
        for d in results[:8]:
            sig={"BUY":"🟢","WATCH":"🟡","HOLD":"⚪","AVOID":"🔴"}.get(d.get("signal",""),"⚪")
            p=d.get("price"); tp=d.get("target_price"); up=d.get("upside")
            msg+=f"{sig} {d['code']} {d.get('name','')[:6]} {d.get('score',0)}分\n"
            if p and tp: msg+=f"   現:{p:.1f} 目:{tp:.1f} ({up:+.1f}%)\n"
        msg+="─"*25+"\n僅供參考，投資有風險"
        r=requests.post("https://notify-api.line.me/api/notify",
            headers={"Authorization":f"Bearer {token}"},
            data={"message":msg},timeout=8)
        return r.status_code==200
    except: return False

def push_alerts_discord(url:str,alerts:List[str])->bool:
    if not url or not alerts: return False
    try:
        fields=[{"name":"⚠️ 警示","value":"\n".join(alerts[:15]),"inline":False}]
        r=requests.post(url,json={"embeds":[{"title":"🔔 台股警示系統","color":0xffbe00,"fields":fields}]},timeout=8)
        return r.status_code in(200,204)
    except: return False

# ═════════════════════════════════════════════════════════════════════════════
# CSV EXPORT
# ═════════════════════════════════════════════════════════════════════════════
def results_to_csv(results:List[dict])->str:
    rows=[]
    for d in results:
        rows.append({
            "代號":d.get("code",""),"名稱":d.get("name",""),
            "信號":d.get("signal",""),"評分":d.get("score",0),
            "現價":d.get("price",""),"目標價":d.get("target_price",""),
            "上漲空間%":round(d.get("upside",0) or 0,1),
            "PE":d.get("pe",""),"PB":d.get("pb",""),
            "ROE%":round((d.get("roe") or 0)*100,1),
            "殖利率%":round((d.get("dividend_yield") or 0)*100,1),
            "RSI":round(d.get("rsi") or 0,1),
            "營收成長%":round((d.get("revenue_growth") or 0)*100,1),
            "財務健康":d.get("fin_health_grade",""),
            "Beta":d.get("beta",""),
            "最大回撤%":d.get("max_drawdown",""),
            "夏普比率":d.get("sharpe",""),
            "成交量倍率":d.get("volume_ratio",""),
            "掃描時間":datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
    return pd.DataFrame(rows).to_csv(index=False,encoding="utf-8-sig")

# ═════════════════════════════════════════════════════════════════════════════
# SCHEDULER
# ═════════════════════════════════════════════════════════════════════════════
def _job():
    p=st.session_state.get("scan_params",{})
    c=st.session_state.get("scan_codes",[])
    if not c: return
    res=scan_batch(c,**p)
    st.session_state.scan_results=res
    st.session_state.last_scan_time=datetime.datetime.now()
    ts=datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.sched_log.insert(0,("ok",f"[{ts}] 排程完成 ─ 命中 {len(res)} 檔"))

    # 警示觸發
    all_alerts=[]
    for d in res:
        alts=check_alerts(d)
        all_alerts.extend(alts)
    if all_alerts:
        st.session_state.alerts=all_alerts[-20:]
        wh=st.session_state.get("auto_webhook","")
        if wh:
            push_alerts_discord(wh,all_alerts)
            st.session_state.sched_log.insert(0,("ok","  └─ 警示推播 Discord ✓"))

    wh=st.session_state.get("auto_webhook","")
    if wh and res:
        ok=push_discord(wh,res)
        st.session_state.sched_log.insert(0,("ok" if ok else "err",f"  └─ 掃描結果 Discord {'✓' if ok else '✗'}"))

    lt=st.session_state.get("line_token","")
    if lt and res:
        ok=push_line(lt,res)
        st.session_state.sched_log.insert(0,("ok" if ok else "err",f"  └─ LINE Notify {'✓' if ok else '✗'}"))

    st.session_state.sched_log=st.session_state.sched_log[:80]

def start_sched(mode,hour=9,minute=30,interval=30):
    try: st.session_state.scheduler.shutdown(wait=False)
    except: pass
    s=BackgroundScheduler(timezone="Asia/Taipei")
    if mode=="fixed":  s.add_job(_job,CronTrigger(hour=hour,minute=minute,day_of_week="mon-fri"))
    else:              s.add_job(_job,IntervalTrigger(minutes=interval))
    s.start(); st.session_state.scheduler=s; st.session_state.sched_running=True

def stop_sched():
    try: st.session_state.scheduler.shutdown(wait=False)
    except: pass
    st.session_state.scheduler=None; st.session_state.sched_running=False

# ═════════════════════════════════════════════════════════════════════════════
# CHART (v8 — 加入 120 MA + ATR通道 + 預測帶)
# ═════════════════════════════════════════════════════════════════════════════
def make_chart(d:dict)->Optional[go.Figure]:
    hist=d.get("hist")
    if hist is None or hist.empty or len(hist)<5: return None
    fig=make_subplots(rows=4,cols=1,shared_xaxes=True,
        row_heights=[.5,.15,.2,.15],vertical_spacing=.018)
    c=hist["Close"]

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=hist.index,open=hist["Open"],high=hist["High"],low=hist["Low"],close=c,
        name="K",increasing_line_color="#00f090",decreasing_line_color="#ff3358",
        increasing_fillcolor="rgba(0,240,144,.85)",decreasing_fillcolor="rgba(255,51,88,.85)",
    ),1,1)

    # MAs
    for p,col,w in [(5,"#ffbe00",1.2),(20,"#2d7fff",1.6),(60,"#a855f7",1.2),(120,"#00cce0",1.0)]:
        ma=c.rolling(p).mean()
        fig.add_trace(go.Scatter(x=hist.index,y=ma,mode="lines",
            line=dict(color=col,width=w),name=f"MA{p}",opacity=.85),1,1)

    # BB
    bu,bm,bl=_bb(c)
    fig.add_trace(go.Scatter(x=hist.index,y=bu,mode="lines",
        line=dict(color="rgba(255,255,255,.1)",width=.8,dash="dot"),name="BB+",showlegend=False),1,1)
    fig.add_trace(go.Scatter(x=hist.index,y=bl,mode="lines",
        line=dict(color="rgba(255,255,255,.1)",width=.8,dash="dot"),
        fill="tonexty",fillcolor="rgba(255,255,255,.02)",name="BB-",showlegend=False),1,1)

    # ATR 通道（v8新增）
    atr_s=_atr(hist["High"],hist["Low"],hist["Close"],14)
    ma20_s=c.rolling(20).mean()
    fig.add_trace(go.Scatter(x=hist.index,y=ma20_s+1.5*atr_s,mode="lines",
        line=dict(color="rgba(255,119,0,.15)",width=.8),name="ATR+",showlegend=False),1,1)
    fig.add_trace(go.Scatter(x=hist.index,y=ma20_s-1.5*atr_s,mode="lines",
        line=dict(color="rgba(255,119,0,.15)",width=.8),
        fill="tonexty",fillcolor="rgba(255,119,0,.03)",name="ATR-",showlegend=False),1,1)

    # 目標價
    tp=d.get("target_price"); tl2=d.get("target_low"); th2=d.get("target_high")
    if tp:
        fig.add_hline(y=tp,line_dash="dash",line_color="rgba(0,240,144,.6)",line_width=1.2,
            annotation_text=f"⚡ 目標 {tp:.1f}",annotation_font_size=9,
            annotation_font_color="#00f090",row=1,col=1)
    if tl2:
        fig.add_hline(y=tl2,line_dash="dot",line_color="rgba(45,127,255,.4)",line_width=.8,row=1,col=1)
    if th2:
        fig.add_hline(y=th2,line_dash="dot",line_color="rgba(168,85,247,.4)",line_width=.8,row=1,col=1)

    # Pivot 支撐壓力
    pv=d.get("pivot",{})
    if pv:
        for key,color in [("R1","rgba(255,51,88,.4)"),("PP","rgba(255,190,0,.5)"),("S1","rgba(0,240,144,.4)")]:
            if key in pv:
                fig.add_hline(y=pv[key],line_dash="dot",line_color=color,line_width=1,
                    annotation_text=f"{key} {pv[key]:.1f}",annotation_font_size=8,
                    annotation_font_color=color.replace(".4","1").replace(".5","1"),row=1,col=1)

    # Volume
    vcol=["#00f090" if cl>=op else "#ff3358" for cl,op in zip(hist["Close"],hist["Open"])]
    fig.add_trace(go.Bar(x=hist.index,y=hist["Volume"],marker_color=vcol,marker_opacity=.65,name="Vol"),2,1)
    # 量能平均線
    vol_ma20=hist["Volume"].rolling(20).mean()
    fig.add_trace(go.Scatter(x=hist.index,y=vol_ma20,mode="lines",
        line=dict(color="#ffbe00",width=1),name="Vol MA20",showlegend=False),2,1)

    # MACD
    ml,sl=_macd(c); hist_macd=ml-sl
    fig.add_trace(go.Scatter(x=hist.index,y=ml,mode="lines",line=dict(color="#2d7fff",width=1.5),name="MACD"),3,1)
    fig.add_trace(go.Scatter(x=hist.index,y=sl,mode="lines",line=dict(color="#ff7700",width=1.2),name="Signal"),3,1)
    fig.add_trace(go.Bar(x=hist.index,y=hist_macd,
        marker_color=["rgba(0,240,144,.5)" if v>=0 else "rgba(255,51,88,.5)" for v in hist_macd],
        name="Hist",showlegend=False),3,1)

    # RSI (with RSI6 fast)
    rsi_s=_rsi(c,14)
    rsi_fast_s=_rsi(c,6)
    fig.add_trace(go.Scatter(x=hist.index,y=rsi_s,mode="lines",
        line=dict(color="#a855f7",width=1.5),name="RSI14"),4,1)
    fig.add_trace(go.Scatter(x=hist.index,y=rsi_fast_s,mode="lines",
        line=dict(color="#00cce0",width=1,dash="dot"),name="RSI6",opacity=.7),4,1)
    for lv,clr in [(70,"rgba(255,51,88,.35)"),(50,"rgba(122,154,184,.2)"),(30,"rgba(0,240,144,.35)")]:
        fig.add_hline(y=lv,line_dash="dot",line_color=clr,line_width=.8,row=4,col=1)

    BG="#02040a"
    fig.update_layout(
        paper_bgcolor=BG,plot_bgcolor=BG,
        font=dict(family="JetBrains Mono",size=9.5,color="#3d5470"),
        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(size=9),
                    orientation="h",yanchor="bottom",y=1.01,xanchor="right",x=1),
        margin=dict(l=52,r=14,t=6,b=6),height=560,
        xaxis_rangeslider_visible=False,
    )
    for i in range(1,5):
        fig.update_yaxes(row=i,col=1,gridcolor="#0c1829",zerolinecolor="#111f35",
                         tickfont=dict(size=9),showgrid=True,tickprefix=" ")
    fig.update_xaxes(gridcolor="#0c1829",showgrid=False,tickfont=dict(size=9))
    return fig

# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════
fp  =lambda v,d=1: f"{v:,.{d}f}" if v is not None else "—"
fpc =lambda v,m=100: f"{v*m:.1f}%" if v is not None else "—"
fbil=lambda v: "—" if v is None else (f"{v/1e12:.2f}兆" if v>=1e12 else f"{v/1e8:.1f}億")

def shex(s:int)->str:
    return "sh-g" if s>=70 else ("sh-y" if s>=50 else "sh-r")

def sig_badge(sig:str)->str:
    dot={"BUY":"●","WATCH":"◆","HOLD":"○","AVOID":"✕"}.get(sig,"○")
    return f'<span class="sig sig-{sig}">{dot} {sig}</span>'

def fcell_h(k,v,cls=""):
    return f'<div class="fcell"><div class="fcell-k">{k}</div><div class="fcell-v {cls}">{v}</div></div>'

def tcell_h(k,v):
    return f'<div class="tcell"><div class="tcell-k">{k}</div><div class="tcell-v">{v}</div></div>'

# ═════════════════════════════════════════════════════════════════════════════
# LOAD
# ═════════════════════════════════════════════════════════════════════════════
with st.spinner("🔧 初始化系統..."):
    ALL=load_names()

# ═════════════════════════════════════════════════════════════════════════════
# HEADER
# ═════════════════════════════════════════════════════════════════════════════
now_s=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
sc_run=st.session_state.sched_running
lt=st.session_state.last_scan_time
res_count=len(st.session_state.scan_results)
wl_count=len(st.session_state.watchlist)
alert_count=len(st.session_state.alerts)

ticker_html=""
for tc in ["2330","2317","2454","2412","2882","2886"]:
    nm=ALL.get(tc,tc)
    ticker_html+=f'<span class="mhdr-ticker-item"><span class="mhdr-ticker-code">{tc}</span><span style="color:var(--t2);margin:0 2px">·</span><span style="color:var(--t1);font-family:var(--mono)">{nm}</span></span>'

st.markdown(f"""
<div class="mhdr">
  <div class="mhdr-glow"></div>
  <div class="mhdr-top">
    <div class="mhdr-accent"></div>
    <div class="mhdr-main">
      <div class="mhdr-logo-block">
        <div class="mhdr-logo-sym">⚡</div>
        <div class="mhdr-logo-ver">ULTRA v8</div>
      </div>
      <div class="mhdr-title-block">
        <div class="mhdr-eyebrow">台灣股市 · 智能分析系統 · REAL-TIME ENGINE</div>
        <div class="mhdr-title">台股 AI 狙擊手 ULTRA</div>
        <div class="mhdr-sub">FUNDAMENTAL + TECHNICAL + RISK + FINANCIAL HEALTH · 16-THREAD PARALLEL · PIVOT POINTS · BACKTEST · ALERTS</div>
        <div class="mhdr-chips">
          <span class="chip chip-live"><span class="chip-live-dot"></span> LIVE MARKET</span>
          <span class="chip chip-time">⏱ {now_s} CST</span>
          <span class="chip chip-v8">✦ v8 EVOLVED</span>
          <span class="chip {'chip-sched-on' if sc_run else 'chip-sched-off'}">{'● SCHEDULER ON' if sc_run else '○ SCHEDULER OFF'}</span>
          {f'<span class="chip chip-warn">🔔 {alert_count} ALERTS</span>' if alert_count else ''}
        </div>
      </div>
    </div>
    <div class="mhdr-stats">
      <div class="mhdr-stat">
        <div class="mhdr-stat-n" style="color:var(--g)">{len(ALL)}</div>
        <div class="mhdr-stat-l">股票庫</div>
      </div>
      <div class="mhdr-stat">
        <div class="mhdr-stat-n" style="color:var(--b)">{res_count}</div>
        <div class="mhdr-stat-l">命中數</div>
      </div>
      <div class="mhdr-stat">
        <div class="mhdr-stat-n" style="color:var(--p)">{wl_count}</div>
        <div class="mhdr-stat-l">自選股</div>
      </div>
      <div class="mhdr-stat">
        <div class="mhdr-stat-n" style="color:var(--y)">{lt.strftime('%H:%M') if lt else '——'}</div>
        <div class="mhdr-stat-l">上次掃描</div>
      </div>
    </div>
  </div>
  <div class="mhdr-bottom">
    <span style="color:var(--t3);margin-right:4px;">WATCHLIST //</span>
    {ticker_html}
  </div>
</div>
""", unsafe_allow_html=True)

# ── 警示橫幅 ──
if st.session_state.alerts:
    items_html=""
    for a in st.session_state.alerts[:5]:
        items_html+=f'<span class="alert-item"><span class="alert-item-msg">⚠ {a}</span></span>'
    st.markdown(f"""
<div class="alert-banner">
  <div class="alert-banner-ico">🔔</div>
  <div class="alert-banner-items">{items_html}</div>
  <div style="font-family:var(--mono);font-size:.5rem;color:var(--t2)">共 {len(st.session_state.alerts)} 條</div>
</div>
""",unsafe_allow_html=True)
    if st.button("清除警示",key="clr_alerts"):
        st.session_state.alerts=[]; st.rerun()

# ═════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── 個股搜尋 ──
    st.markdown('<div class="sb-seg"><div class="sb-seg-hdr"><span class="sb-seg-hdr-accent"></span>個股搜尋</div><div class="sb-seg-body">',unsafe_allow_html=True)
    q=st.text_input("s",label_visibility="collapsed",placeholder="代號或名稱 · 2330 / 台積電",key="sq")
    if q and q.strip():
        hits=search(q,ALL,10)
        if hits:
            for code,name in hits:
                ca,cb,cc=st.columns([3,1,1])
                ca.markdown(f'<div class="sh-row"><span class="sh-code">{code}</span><span class="sh-name">{name}</span></div>',unsafe_allow_html=True)
                if cb.button("GO",key=f"s_{code}",use_container_width=True):
                    st.session_state.selected_stock=code
                    st.session_state.detail_cache={}
                    st.rerun()
                wl_icon="★" if code in st.session_state.watchlist else "☆"
                if cc.button(wl_icon,key=f"wl_{code}",use_container_width=True):
                    if code in st.session_state.watchlist:
                        st.session_state.watchlist.remove(code)
                    else:
                        st.session_state.watchlist.append(code)
                    st.rerun()
        else:
            st.markdown('<div style="font-family:var(--mono);font-size:.6rem;color:var(--t2);padding:4px 0;">無符合結果</div>',unsafe_allow_html=True)
    elif st.session_state.selected_stock:
        sc_=st.session_state.selected_stock
        st.markdown(f'<div style="font-family:var(--mono);font-size:.62rem;padding:4px 0;">分析中 <span style="color:var(--g);font-weight:700">{sc_} {ALL.get(sc_,"")}</span></div>',unsafe_allow_html=True)
    st.markdown('</div></div>',unsafe_allow_html=True)

    # ── 自選股清單 ──
    st.markdown('<div class="sb-seg"><div class="sb-seg-hdr"><span class="sb-seg-hdr-accent"></span>自選股 ★</div><div class="sb-seg-body">',unsafe_allow_html=True)
    wl=st.session_state.watchlist
    if wl:
        wl_prices=fetch_watchlist_prices(tuple(wl))
        for code in wl[:15]:
            nm=ALL.get(code,code)
            info=wl_prices.get(code,{})
            px=info.get("price"); chg=info.get("chg")
            chg_html=""
            if chg is not None:
                chg_cls="wl-chg-p" if chg>=0 else "wl-chg-n"
                chg_sym="▲" if chg>=0 else "▼"
                chg_html=f'<span class="{chg_cls}">{chg_sym}{abs(chg):.1f}%</span>'
            col1,col2=st.columns([4,1])
            col1.markdown(f'<div class="wl-row"><span class="wl-code">{code}</span><span class="wl-name">{nm[:6]}</span><span class="wl-price">{fp(px,1) if px else "—"}</span>{chg_html}</div>',unsafe_allow_html=True)
            if col2.button("✕",key=f"rm_{code}",use_container_width=True):
                st.session_state.watchlist.remove(code); st.rerun()

        # 匯出自選股
        wl_export=",".join(wl)
        st.text_area("匯出/貼入代號",value=wl_export,height=50,key="wl_export",label_visibility="collapsed")
    else:
        st.markdown('<div style="font-family:var(--mono);font-size:.6rem;color:var(--t2);padding:6px 0">尚無自選股 · 搜尋時按 ☆ 加入</div>',unsafe_allow_html=True)

    # 批量加入
    wl_import=st.text_input("批量加入",placeholder="2330,2317...",key="wl_import",label_visibility="collapsed")
    if wl_import:
        codes_to_add=[x.strip() for x in re.split(r"[,\n\s]+",wl_import) if x.strip() and len(x.strip())==4]
        for c_add in codes_to_add:
            if c_add not in st.session_state.watchlist:
                st.session_state.watchlist.append(c_add)
        st.rerun()
    st.markdown('</div></div>',unsafe_allow_html=True)

    # ── 掃描設定 ──
    st.markdown('<div class="sb-seg"><div class="sb-seg-hdr"><span class="sb-seg-hdr-accent"></span>批量掃描設定</div><div class="sb-seg-body">',unsafe_allow_html=True)
    scan_mode=st.radio("範圍",["熱門100","自選股","全市場","自訂"],label_visibility="collapsed")
    custom=""
    if scan_mode=="自訂":
        custom=st.text_area("代號",placeholder="2330,2317...",height=60,label_visibility="collapsed")
    min_score =st.slider("最低評分",     0,100,55,5,key="ss")
    min_upside=st.slider("最低上漲空間%",1,50,8,1,key="su")
    max_pe    =st.slider("最高 PE",      5,150,60,5,key="sp")
    signal_filter=st.selectbox("信號篩選",["全部","BUY","WATCH","HOLD","AVOID"],key="sf",label_visibility="collapsed")
    st.markdown('</div></div>',unsafe_allow_html=True)

    # ── 推播設定 ──
    st.markdown('<div class="sb-seg"><div class="sb-seg-hdr"><span class="sb-seg-hdr-accent"></span>推播設定</div><div class="sb-seg-body">',unsafe_allow_html=True)
    webhook=st.text_input("Discord Webhook",label_visibility="collapsed",placeholder="https://discord.com/api/webhooks/...",type="password",key="whi")
    st.session_state.auto_webhook=webhook
    line_token=st.text_input("LINE Notify Token",label_visibility="collapsed",placeholder="LINE Notify Token",type="password",key="lt_")
    st.session_state.line_token=line_token
    st.markdown('</div></div>',unsafe_allow_html=True)

    # ── 排程 ──
    st.markdown('<div class="sb-seg"><div class="sb-seg-hdr"><span class="sb-seg-hdr-accent"></span>自動排程</div><div class="sb-seg-body">',unsafe_allow_html=True)
    sm=st.radio("模式",["固定時間","間隔"],horizontal=True,label_visibility="collapsed")
    if sm=="固定時間":
        c1_,c2_=st.columns(2)
        sh=c1_.number_input("時",0,23,9,label_visibility="collapsed")
        sm_=c2_.number_input("分",0,59,30,label_visibility="collapsed")
    else:
        si=st.slider("每隔(分)",5,180,30,5,key="siv")
    ca_,cb_=st.columns(2)
    with ca_:
        if st.button("▶ 啟動",type="primary",use_container_width=True,key="bst"):
            if scan_mode=="熱門100":   codes_s=list(ALL.keys())[:100]
            elif scan_mode=="自選股":  codes_s=list(st.session_state.watchlist)
            elif scan_mode=="全市場":  codes_s=list(ALL.keys())
            else:                      codes_s=[x.strip() for x in re.split(r"[,\n\s]+",custom) if x.strip()]
            st.session_state.scan_codes=codes_s
            st.session_state.scan_params=dict(min_score=min_score,min_upside=min_upside,max_pe=max_pe,signal_filter=signal_filter)
            if sm=="固定時間": start_sched("fixed",hour=int(sh),minute=int(sm_))
            else:              start_sched("interval",interval=int(si))
            st.success("排程啟動 ✓")
    with cb_:
        if st.button("⏹ 停止",use_container_width=True,key="bsp"):
            stop_sched(); st.info("已停止")
    if sc_run:
        st.markdown(f"""
<div style="background:var(--bg2);border:1px solid var(--line);border-radius:4px;padding:8px 12px;margin-top:8px">
  <div style="display:flex;justify-content:space-between;font-family:var(--mono);font-size:.55rem;padding:2px 0">
    <span style="color:var(--t2)">狀態</span><span style="color:var(--g)">● RUNNING</span>
  </div>
  <div style="display:flex;justify-content:space-between;font-family:var(--mono);font-size:.55rem;padding:2px 0">
    <span style="color:var(--t2)">上次</span><span style="color:var(--b)">{lt.strftime('%H:%M:%S') if lt else '—'}</span>
  </div>
  <div style="display:flex;justify-content:space-between;font-family:var(--mono);font-size:.55rem;padding:2px 0">
    <span style="color:var(--t2)">標的</span><span style="color:var(--b)">{len(st.session_state.scan_codes)} 檔</span>
  </div>
</div>""",unsafe_allow_html=True)
    st.markdown('</div></div>',unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# MAIN TABS (v8 — 新增回測/風險/產業比較 Tab)
# ═════════════════════════════════════════════════════════════════════════════
tab1,tab2,tab3,tab4=st.tabs(["📊  個股深度分析","⚡  智能批量掃描","📋  排程紀錄","🎯  多空儀表板"])

# ════════════════════════════ TAB 1 — 個股深度分析 ════════════════════════
with tab1:
    sel=st.session_state.selected_stock
    if not sel:
        st.markdown('<div class="empty-state"><div class="empty-state-ico">⚡</div><div class="empty-state-txt">在左側搜尋欄輸入股票代號或名稱<br>支援上市、上櫃全部個股 · 自動偵測 .TW / .TWO<br>按 ☆ 加入自選股清單</div></div>',unsafe_allow_html=True)
    else:
        cache=st.session_state.detail_cache
        if cache.get("code")!=sel:
            with st.spinner(f"🔍 載入 {sel} · {ALL.get(sel,'')} ..."):
                d=fetch_stock(sel)
            st.session_state.detail_cache=d
        else:
            d=cache

        if d.get("error") and not d.get("price"):
            st.error(f"❌ 無法取得 {sel} 資料 — {d['error']}")
        else:
            px=d.get("price"); prev=d.get("prev_close")
            chg=(px-prev) if (px and prev) else None
            chgp=chg/prev*100 if (chg is not None and prev) else None
            score=d.get("score",0); sig=d.get("signal","HOLD")
            name=d.get("name",sel)
            tp=d.get("target_price"); tl_=d.get("target_low"); th_=d.get("target_high")
            up=d.get("upside")
            chg_cls="pos" if (chg and chg>=0) else "neg"
            chg_sym="▲" if (chg and chg>=0) else "▼"
            suffix=d.get("suffix","")
            mc=d.get("market_cap")
            vol_ratio=d.get("volume_ratio",1.0); vol_status=d.get("volume_status","normal")
            fhg=d.get("fin_health_grade","—"); fhg_cls={"A":"pos","B":"neu","C":"warn","D":"neg"}.get(fhg,"")
            beta=d.get("beta"); sharpe=d.get("sharpe"); mdd=d.get("max_drawdown")
            industry=d.get("industry","—")

            # ── 操作列 ──
            op_c1,op_c2,op_c3=st.columns([2,2,6])
            with op_c1:
                wl_in=sel in st.session_state.watchlist
                if st.button(f"{'★ 移出' if wl_in else '☆ 加入'}自選股",use_container_width=True):
                    if wl_in: st.session_state.watchlist.remove(sel)
                    else:     st.session_state.watchlist.append(sel)
                    st.rerun()
            with op_c2:
                if st.button("🔄 重新載入",use_container_width=True):
                    fetch_stock.clear(); st.session_state.detail_cache={}; st.rerun()

            # ── STOCK HEADER CARD ──
            vol_badge_html=""
            if vol_status=="extreme":
                vol_badge_html='<span class="vol-badge extreme">💥 爆量異常</span>'
            elif vol_status=="high":
                vol_badge_html='<span class="vol-badge high">📈 量能放大</span>'

            alerts_now=check_alerts(d)
            alert_html="".join(f'<div style="font-family:var(--mono);font-size:.52rem;color:var(--y);margin-top:2px">⚠ {a}</div>' for a in alerts_now[:3])

            st.markdown(f"""
<div class="scard">
  <div class="scard-top">
    <div class="scard-accent"></div>
    <div class="scard-id">
      <div class="scard-code">{sel}<span class="scard-suffix">{suffix}</span></div>
      <div class="scard-name">{name}</div>
      <div class="scard-mkt">{industry} · 市值 {fbil(mc)}</div>
      <div style="margin-top:6px;display:flex;gap:5px;flex-wrap:wrap">
        {sig_badge(sig)}
        <span class="fcell-v {fhg_cls}" style="font-family:var(--mono);font-size:.6rem;border:1px solid var(--line3);padding:2px 6px;border-radius:3px">財健 {fhg}</span>
        {vol_badge_html}
      </div>
      {alert_html}
    </div>
    <div class="scard-price-block">
      <div class="scard-price">{fp(px)}<span class="scard-price-unit">TWD</span></div>
      <div class="scard-chg {chg_cls}">{chg_sym} {f'{abs(chg):.2f}' if chg else '—'}&nbsp;&nbsp;({f'{chgp:+.2f}%' if chgp else '—'})</div>
      <div style="display:flex;gap:12px;margin-top:10px;font-family:var(--mono);font-size:.54rem;color:var(--t2)">
        <span>開 <span style="color:var(--t1)">{fp(d.get('open'))}</span></span>
        <span>高 <span style="color:var(--g)">{fp(d.get('high'))}</span></span>
        <span>低 <span style="color:var(--r)">{fp(d.get('low'))}</span></span>
        <span>昨 <span style="color:var(--t1)">{fp(prev)}</span></span>
      </div>
      <div style="display:flex;gap:12px;margin-top:5px;font-family:var(--mono);font-size:.54rem;color:var(--t2)">
        <span>量 <span style="color:{('var(--y)' if vol_status=='high' else ('var(--r)' if vol_status=='extreme' else 'var(--t1)'))}">{d.get('volume_ratio',1.0):.1f}x</span></span>
        <span>Beta <span style="color:var(--t1)">{fp(beta,2) if beta else '—'}</span></span>
        <span>夏普 <span style="color:var(--t1)">{fp(sharpe,2) if sharpe else '—'}</span></span>
        <span>回撤 <span style="color:var(--r)">{f'{mdd:.1f}%' if mdd else '—'}</span></span>
      </div>
    </div>
    <div class="scard-signals">
      <div class="scard-score-wrap">
        <div class="score-hex {shex(score)}">{score}</div>
        <div>
          <div style="font-family:var(--mono);font-size:.44rem;color:var(--t2);text-transform:uppercase;letter-spacing:.12em">綜合評分 /100</div>
          <div style="font-family:var(--mono);font-size:.58rem;color:var(--t1);margin-top:2px">{"★"*int(score/20)}{"☆"*(5-int(score/20))}</div>
        </div>
      </div>
      <div style="font-family:var(--mono);font-size:.54rem;color:var(--t2);margin-top:6px">
        目標 <span style="color:var(--g);font-weight:700;font-size:.75rem">{fp(tp)}</span>
        <span style="color:var(--g);margin-left:5px">({f'{up:+.1f}%' if up is not None else '—'})</span>
      </div>
    </div>
  </div>
</div>
""",unsafe_allow_html=True)

            # ── 主佈局 ──
            col_main,col_side=st.columns([5.5,3])

            with col_main:
                pe=d.get("pe"); pb=d.get("pb"); roe=d.get("roe")
                dy=d.get("dividend_yield"); pm=d.get("profit_margin"); rg=d.get("revenue_growth")
                cr=d.get("current_ratio"); qr=d.get("quick_ratio"); de=d.get("debt_to_equity")
                rsi=d.get("rsi"); ma5_v=d.get("ma5"); ma20=d.get("ma20"); ma60=d.get("ma60"); ma120=d.get("ma120")
                macd_v=d.get("macd"); macd_sv=d.get("macd_signal")
                atr_v=d.get("atr"); ac=d.get("analyst_count",0)

                # 基本面 + 財務健康 (12格)
                cells="".join([
                    fcell_h("本益比 PE",   f"{pe:.1f}×" if pe else "—","warn" if (pe and pe>20) else ("pos" if (pe and pe<15) else "")),
                    fcell_h("淨值比 PB",   f"{pb:.2f}×" if pb else "—"),
                    fcell_h("ROE",          fpc(roe),"pos" if (roe and roe>.12) else ("neg" if (roe and roe<0) else "")),
                    fcell_h("殖利率",       fpc(dy),"pos" if (dy and dy>.04) else ""),
                    fcell_h("淨利率",       fpc(pm),"pos" if (pm and pm>.1) else ""),
                    fcell_h("營收成長",     fpc(rg),"pos" if (rg and rg>0) else ("neg" if (rg and rg<-.05) else "")),
                    fcell_h("流動比率",     f"{cr:.2f}" if cr else "—","pos" if (cr and cr>=2) else ("warn" if (cr and cr>=1) else "neg")),
                    fcell_h("速動比率",     f"{qr:.2f}" if qr else "—","pos" if (qr and qr>=1) else ("warn" if qr else "")),
                    fcell_h("負債比",       f"{de:.2f}" if de else "—","pos" if (de and de<0.5) else ("warn" if (de and de<1) else "neg")),
                    fcell_h("RSI(14)",      f"{rsi:.1f}" if rsi else "—","neg" if (rsi and rsi>72) else ("warn" if (rsi and rsi>60) else ("pos" if (rsi and rsi<35) else "neu"))),
                    fcell_h("目標價",       fp(tp),"pos"),
                    fcell_h("上漲空間",     f"{up:+.1f}%" if up is not None else "—","pos"),
                ])
                st.markdown(f'<div class="fgrid">{cells}</div>',unsafe_allow_html=True)

                # 技術數值 8格
                trows="".join([
                    tcell_h("MACD",f"{macd_v:.3f}" if macd_v else "—"),
                    tcell_h("Signal",f"{macd_sv:.3f}" if macd_sv else "—"),
                    tcell_h("MACD差",f"{(macd_v-macd_sv):+.3f}" if (macd_v and macd_sv) else "—"),
                    tcell_h("ATR(14)",f"{atr_v:.2f}" if atr_v else "—"),
                    tcell_h("MA5",fp(ma5_v)),
                    tcell_h("MA20",fp(ma20)),
                    tcell_h("MA60",fp(ma60)),
                    tcell_h("MA120",fp(ma120)),
                ])
                st.markdown(f'<div class="trow">{trows}</div>',unsafe_allow_html=True)

                # K線圖
                fig=make_chart(d)
                if fig:
                    st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
                else:
                    st.markdown('<div style="font-family:var(--mono);font-size:.65rem;color:var(--t2);text-align:center;padding:20px">歷史資料不足，無法繪製圖表</div>',unsafe_allow_html=True)

                # ── 三大法人估算面板 ──
                fn=d.get("foreign_net"); tn=d.get("trust_net"); dn=d.get("dealer_net")
                if fn is not None:
                    max_abs=max(abs(fn or 0),abs(tn or 0),abs(dn or 0),1)
                    def inst_bar_html(name,val,max_v):
                        if val is None: return ""
                        pct=min(abs(val)/max_v*45,45)
                        is_buy=val>=0
                        bar_cls="buy" if is_buy else "sell"
                        val_cls="pos" if is_buy else "neg"
                        return f"""<div class="inst-row">
                          <div class="inst-name">{name}</div>
                          <div class="inst-bar-wrap"><div class="inst-bar {bar_cls}" style="width:{pct}%"></div></div>
                          <div class="inst-val {val_cls}">{val:+.1f}億</div>
                        </div>"""
                    st.markdown(f"""
<div class="inst-panel">
  <div class="inst-panel-lbl">三大法人動向估算（近5日）</div>
  {inst_bar_html("外資",fn,max_abs)}
  {inst_bar_html("投信",tn,max_abs)}
  {inst_bar_html("自營商",dn,max_abs)}
  <div style="font-family:var(--mono);font-size:.44rem;color:var(--t2);margin-top:6px">※ 依近期價量關係推估，非官方數據，僅供參考</div>
</div>
""",unsafe_allow_html=True)

                # ── 回測面板（v8新增）──
                bt=d.get("backtest",{})
                if bt:
                    def bt_stat(k,v,cls=""):
                        return f'<div class="bt-stat"><div class="bt-stat-k">{k}</div><div class="bt-stat-v {cls}">{v}</div></div>'
                    wr=bt.get("win_rate",0); ar=bt.get("avg_return",0)
                    st.markdown(f"""
<div class="bt-panel">
  <div class="bt-panel-lbl">歷史信號回測（MA金叉策略 · 近一年）</div>
  <div class="bt-stats">
    {bt_stat("交易次數",bt.get('trades','—'))}
    {bt_stat("勝率",f"{wr:.1f}%","pos" if wr>=55 else ("warn" if wr>=45 else "neg"))}
    {bt_stat("均報酬",f"{ar:+.1f}%","pos" if ar>0 else "neg")}
    {bt_stat("最大獲利",f"{bt.get('max_win',0):+.1f}%","pos")}
    {bt_stat("最大損失",f"{bt.get('max_loss',0):+.1f}%","neg")}
    {bt_stat("年化波動",f"{bt.get('ann_vol',0):.1f}%")}
    {bt_stat("最大回撤",f"{bt.get('max_drawdown',0):.1f}%","neg")}
    {bt_stat("夏普比率",f"{sharpe:.2f}" if sharpe else "—","pos" if (sharpe and sharpe>1) else "")}
  </div>
  <div style="font-family:var(--mono);font-size:.44rem;color:var(--t2);margin-top:6px">※ 過去績效不代表未來，僅供技術分析參考</div>
</div>
""",unsafe_allow_html=True)

            with col_side:
                # ── 目標價 ──
                if px and tp and tl_ and th_:
                    lo_b=min(tl_,px)*.93; hi_b=max(th_,px)*1.07; rng=hi_b-lo_b if hi_b>lo_b else 1
                    def pp(v): return max(0.,min(100.,(v-lo_b)/rng*100))
                    p_px=pp(px); p_tp=pp(tp); p_tl=pp(tl_); p_th=pp(th_)
                    bw=p_th-p_tl; up_col="var(--g)" if (up and up>=0) else "var(--r)"

                    st.markdown(f"""
<div class="tpmaster">
  <div class="tpmaster-lbl">12 個月目標價估算</div>
  <div class="tp-prices-row">
    <div class="tp-price-item"><div class="tp-price-lbl">目標低</div><div class="tp-price-val lo">{fp(tl_)}</div></div>
    <div class="tp-price-item"><div class="tp-price-lbl">現價</div><div class="tp-price-val cur">{fp(px)}</div></div>
    <div class="tp-price-item" style="text-align:center">
      <div class="tp-upside-big {'pos' if (up and up>=0) else 'neg'}">{f'{up:+.1f}%' if up is not None else '—'}</div>
      <div class="tp-price-lbl" style="margin-top:3px">預期報酬</div>
    </div>
    <div class="tp-price-item"><div class="tp-price-lbl">目標價</div><div class="tp-price-val tp">{fp(tp)}</div></div>
    <div class="tp-price-item" style="text-align:right"><div class="tp-price-lbl">目標高</div><div class="tp-price-val hi">{fp(th_)}</div></div>
  </div>
  <div class="tp-track">
    <div class="tp-zone" style="left:{p_tl:.1f}%;width:{bw:.1f}%"></div>
    <div class="tp-cur-line" style="left:{p_px:.1f}%"><div class="tp-label" style="top:-16px;color:#fff;font-size:.42rem">現 {fp(px)}</div></div>
    <div class="tp-tp-line" style="left:{p_tp:.1f}%;background:{up_col};box-shadow:0 0 10px {up_col}88"><div class="tp-label" style="top:14px;color:{up_col};font-size:.44rem">目 {fp(tp)}</div></div>
  </div>
  <div class="tp-footnote">
    基礎溢價 + 基本面溢價 + 技術溢價{' + 分析師共識（{}人）'.format(ac) if ac>=3 else ''}<br>
    目標區間：{fp(tl_)} – {fp(th_)} · 分析師覆蓋 {ac} 人
  </div>
</div>
""",unsafe_allow_html=True)

                # ── 評分明細 ──
                det=d.get("score_detail",{})
                maxes={"技術":35,"基本面":30,"動能":20,"財務健康":10,"量能":5}
                bars="".join([
                    f'<div class="sbar"><div class="sbar-k">{k}</div>'
                    f'<div class="sbar-track"><div class="sbar-fill {"g" if int(v/mx*100)>=65 else ("y" if int(v/mx*100)>=35 else "r")}" style="width:{int(v/mx*100)}%"></div></div>'
                    f'<div class="sbar-n">{v}/{mx}</div></div>'
                    for k,mx in maxes.items() for v in [det.get(k,0)]
                ])
                st.markdown(f'<div class="sbars"><div class="sbars-lbl">評分明細（5維度）</div>{bars}</div>',unsafe_allow_html=True)

                # ── 財務健康評級（v8新增）──
                fh_score=d.get("fin_health_score",0)
                fh_ring_cls={"A":"A","B":"B","C":"C","D":"D"}.get(fhg,"C")
                fh_color={"A":"var(--g)","B":"var(--b)","C":"var(--y)","D":"var(--r)"}.get(fhg,"var(--y)")
                fh_desc={"A":"財務體質優良","B":"財務狀況良好","C":"財務一般，需留意","D":"財務較弱，高風險"}.get(fhg,"")
                st.markdown(f"""
<div class="fh-panel">
  <div class="fh-panel-lbl">財務健康評級</div>
  <div class="fh-top">
    <div class="fh-score-ring {fh_ring_cls}">
      <div class="fh-score-grade" style="color:{fh_color}">{fhg}</div>
      <div class="fh-score-lbl">{fh_score}分</div>
    </div>
    <div style="flex:1">
      <div style="font-family:var(--mono);font-size:.6rem;color:{fh_color};font-weight:700;margin-bottom:5px">{fh_desc}</div>
      <div class="fh-metrics">
        <div class="fh-metric"><div class="fh-metric-k">流動比率</div><div class="fh-metric-v {'pos' if (cr and cr>=2) else ('warn' if (cr and cr>=1) else 'neg')}">{f'{cr:.2f}' if cr else '—'}</div></div>
        <div class="fh-metric"><div class="fh-metric-k">速動比率</div><div class="fh-metric-v {'pos' if (qr and qr>=1) else ('warn' if qr else '')}">{f'{qr:.2f}' if qr else '—'}</div></div>
        <div class="fh-metric"><div class="fh-metric-k">負債比</div><div class="fh-metric-v {'pos' if (de and de<0.5) else ('warn' if (de and de<1) else 'neg')}">{f'{de:.2f}' if de else '—'}</div></div>
      </div>
    </div>
  </div>
</div>
""",unsafe_allow_html=True)

                # ── 風險儀表板（v8新增）──
                def risk_bar(v,low=0,high=2,cls=""):
                    if v is None: return ""
                    pct=max(0,min(100,(v-low)/(high-low)*100))
                    return f'<div class="risk-meter"><div class="risk-meter-fill" style="width:{pct}%;background:{cls}"></div></div>'

                st.markdown(f"""
<div class="risk-panel">
  <div class="risk-panel-lbl">風險指標</div>
  <div class="risk-grid">
    <div class="risk-cell">
      <div class="risk-cell-k">Beta 市場相關</div>
      <div class="risk-cell-v {'pos' if (beta and beta<1) else ('warn' if (beta and beta<1.5) else 'neg')}">{f'{beta:.2f}' if beta else '—'}</div>
      {risk_bar(beta,0,2,"#2d7fff") if beta else ""}
    </div>
    <div class="risk-cell">
      <div class="risk-cell-k">夏普比率</div>
      <div class="risk-cell-v {'pos' if (sharpe and sharpe>1) else ('warn' if (sharpe and sharpe>0) else 'neg')}">{f'{sharpe:.2f}' if sharpe else '—'}</div>
      {risk_bar(sharpe,-1,3,"#00f090") if sharpe else ""}
    </div>
    <div class="risk-cell">
      <div class="risk-cell-k">最大回撤</div>
      <div class="risk-cell-v neg">{f'{mdd:.1f}%' if mdd else '—'}</div>
      {risk_bar(abs(mdd) if mdd else 0,0,50,"#ff3358") if mdd else ""}
    </div>
  </div>
</div>
""",unsafe_allow_html=True)

                # ── 支撐壓力位（v8新增）──
                pv=d.get("pivot",{})
                if pv and px:
                    st.markdown(f"""
<div class="pivot-panel">
  <div class="pivot-panel-lbl">Pivot Point 支撐壓力（前日計算）</div>
  <div class="pivot-grid">
    <div class="pivot-cell resist"><div class="pivot-cell-k">R3</div><div class="pivot-cell-v">{fp(pv.get('R3'))}</div></div>
    <div class="pivot-cell resist"><div class="pivot-cell-k">R2</div><div class="pivot-cell-v">{fp(pv.get('R2'))}</div></div>
    <div class="pivot-cell resist"><div class="pivot-cell-k">R1</div><div class="pivot-cell-v">{fp(pv.get('R1'))}</div></div>
    <div class="pivot-cell pivot-p" style="grid-column:span 3"><div class="pivot-cell-k">PP 樞紐</div><div class="pivot-cell-v">{fp(pv.get('PP'))}</div></div>
    <div class="pivot-cell support"><div class="pivot-cell-k">S1</div><div class="pivot-cell-v">{fp(pv.get('S1'))}</div></div>
    <div class="pivot-cell support"><div class="pivot-cell-k">S2</div><div class="pivot-cell-v">{fp(pv.get('S2'))}</div></div>
    <div class="pivot-cell support"><div class="pivot-cell-k">S3</div><div class="pivot-cell-v">{fp(pv.get('S3'))}</div></div>
  </div>
  <div style="font-family:var(--mono);font-size:.44rem;color:var(--t2);margin-top:6px">
    現價 {fp(px)} · {'位於 PP 上方壓力區' if px>(pv.get('PP',0)) else '位於 PP 下方支撐區'}
  </div>
</div>
""",unsafe_allow_html=True)

                # ── 信號解讀 ──
                sig_info={
                    "BUY":("強勢買入","技術多頭排列 + 基本面健康 + 估值合理，三重確認進場信號，建議分批建倉。"),
                    "WATCH":("觀察等待","指標逐步到位，尚缺突破確認。建議設定警示價位，等成交量配合再進場。"),
                    "HOLD":("持有中立","現階段趨勢不明，持倉者繼續持有，空手者暫緩介入。"),
                    "AVOID":("暫時迴避","多項指標偏弱或估值偏高，目前不具進場優勢，等待更好時機。"),
                }.get(sig,("中立","—"))
                sig_color={"BUY":"var(--g)","WATCH":"var(--y)","HOLD":"var(--t1)","AVOID":"var(--r)"}.get(sig,"var(--t1)")
                st.markdown(f"""
<div class="sigcard {sig}">
  <div class="sigcard-title" style="color:{sig_color}">{sig} · {sig_info[0]}</div>
  <div class="sigcard-body">{sig_info[1]}</div>
</div>
""",unsafe_allow_html=True)

                # ── 條件 Checklist ──
                macd_ok_=bool(macd_v and macd_sv and macd_v>macd_sv)
                checks=[
                    ("現價 > MA5",   bool(px and ma5_v and px>ma5_v)),
                    ("現價 > MA20",  bool(px and ma20 and px>ma20)),
                    ("現價 > MA60",  bool(px and ma60 and px>ma60)),
                    ("現價 > MA120", bool(px and ma120 and px>ma120)),
                    ("MACD 金叉",    macd_ok_),
                    ("RSI 健康區",   bool(rsi and 30<=rsi<=70)),
                    ("PE 合理",      bool(pe and pe<=20)),
                    ("殖利率 > 3%",  bool(dy and dy>.03)),
                    ("ROE > 12%",    bool(roe and roe>.12)),
                    ("流動比 ≥ 1.5", bool(cr and cr>=1.5)),
                    ("負債比 < 1",   bool(de is not None and de<1)),
                    ("目標上漲 ↑",   bool(up and up>0)),
                    ("成長正向",     bool(rg and rg>0)),
                    ("財務健康 A/B", fhg in("A","B")),
                ]
                ok_count=sum(1 for _,ok in checks if ok)
                chk_rows="".join([
                    f'<div class="chk-item {"chk-ok" if ok else "chk-no"}"><span class="chk-icon">{"✓" if ok else "✗"}</span><span class="chk-lbl">{lbl}</span></div>'
                    for lbl,ok in checks
                ])
                st.markdown(f'<div class="chklist"><div class="chklist-lbl">條件核對 · {ok_count}/{len(checks)} 通過</div>{chk_rows}</div>',unsafe_allow_html=True)

            # ── 新聞 ──
            with st.expander("📰  相關新聞 · 情緒掃描",expanded=True):
                news=fetch_news(sel,name)
                if news:
                    pos_n=sum(1 for n in news if n.get("s")=="pos")
                    neg_n=sum(1 for n in news if n.get("s")=="neg")
                    sentiment="偏多" if pos_n>neg_n else ("偏空" if neg_n>pos_n else "中性")
                    sent_col="var(--g)" if pos_n>neg_n else ("var(--r)" if neg_n>pos_n else "var(--t2)")
                    st.markdown(f'<div style="font-family:var(--mono);font-size:.52rem;color:var(--t2);margin-bottom:6px">新聞情緒 <span style="color:{sent_col};font-weight:700">{sentiment}</span> · 正向 {pos_n} · 負向 {neg_n}</div>',unsafe_allow_html=True)
                    html='<div class="nwrap">'
                    for n in news:
                        s=n.get("s","neu"); ic={"pos":"↑","neg":"↓","neu":"·"}.get(s,"·")
                        html+=f'<div class="ni"><div class="ni-ic {s}">{ic}</div><div class="ni-body"><div class="ni-t">{n["t"]}</div><div class="ni-m">{n.get("src","")}</div></div></div>'
                    html+='</div>'
                    st.markdown(html,unsafe_allow_html=True)
                else:
                    st.markdown('<div style="font-family:var(--mono);font-size:.65rem;color:var(--t2);padding:12px 0">暫無新聞資料</div>',unsafe_allow_html=True)

            # ── 警示設定 ──
            with st.expander("🔔  警示設定",expanded=False):
                cfg=st.session_state.alert_config.get(sel,{})
                ac1,ac2=st.columns(2)
                pa=ac1.number_input("突破價位 (0=停用)",min_value=0.0,value=float(cfg.get("price_above",0)),step=1.0,key=f"pa_{sel}")
                pb_=ac2.number_input("跌破價位 (0=停用)",min_value=0.0,value=float(cfg.get("price_below",0)),step=1.0,key=f"pb_{sel}")
                if st.button("儲存警示設定",key=f"save_alert_{sel}"):
                    st.session_state.alert_config[sel]={"price_above":pa if pa>0 else None,"price_below":pb_ if pb_>0 else None}
                    st.success(f"✓ {sel} 警示已設定")


# ════════════════════════════ TAB 2 — 批量掃描 ════════════════════════════
with tab2:
    op1,op2,op3,op4=st.columns([2.5,1.2,1.2,1.1])
    with op1:
        if st.button("⚡  立即掃描",type="primary",use_container_width=True,key="bsc"):
            if scan_mode=="熱門100":   c2s=list(ALL.keys())[:100]
            elif scan_mode=="自選股":  c2s=list(st.session_state.watchlist)
            elif scan_mode=="全市場":  c2s=list(ALL.keys())
            else:                       c2s=[x.strip() for x in re.split(r"[,\n\s]+",custom) if x.strip()]
            if not c2s:
                st.warning("請設定掃描範圍")
            else:
                ph=st.empty(); txh=st.empty()
                def _prog(done,total,code):
                    ph.progress(done/total)
                    txh.markdown(f'<div class="ll inf">⚡ [{done}/{total}] {code} {ALL.get(code,"")}</div>',unsafe_allow_html=True)
                with st.spinner(""):
                    res=scan_batch(c2s,min_score=min_score,min_upside=min_upside,max_pe=max_pe,
                                   signal_filter=signal_filter,progress_cb=_prog,max_workers=16)
                ph.empty(); txh.empty()
                st.session_state.scan_results=res
                st.session_state.last_scan_time=datetime.datetime.now()
                # 觸發警示檢查
                all_alts=[]
                for d_ in res:
                    all_alts.extend(check_alerts(d_))
                if all_alts: st.session_state.alerts=all_alts[-20:]
                st.success(f"✓ 完成 · {len(c2s)} 檔 · 命中 {len(res)} 檔 · 警示 {len(all_alts)} 條")
    with op2:
        if st.button("📤  Discord",use_container_width=True,key="bdc"):
            if not st.session_state.scan_results: st.warning("無掃描結果")
            elif not webhook: st.warning("請填入 Webhook")
            else:
                ok=push_discord(webhook,st.session_state.scan_results)
                st.success("✓") if ok else st.error("✗")
    with op3:
        if st.button("📱  LINE",use_container_width=True,key="bln"):
            if not st.session_state.scan_results: st.warning("無掃描結果")
            elif not line_token: st.warning("請填入 LINE Token")
            else:
                ok=push_line(line_token,st.session_state.scan_results)
                st.success("✓") if ok else st.error("✗")
    with op4:
        res_now=st.session_state.scan_results
        if res_now:
            csv_data=results_to_csv(res_now)
            st.download_button(
                "📥 CSV",data=csv_data.encode("utf-8-sig"),
                file_name=f"taiwan_scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",use_container_width=True,key="dcsv"
            )

    res=st.session_state.scan_results
    if res:
        buy_n=sum(1 for r in res if r.get("signal")=="BUY")
        wch_n=sum(1 for r in res if r.get("signal")=="WATCH")
        hld_n=sum(1 for r in res if r.get("signal")=="HOLD")
        avd_n=sum(1 for r in res if r.get("signal")=="AVOID")
        avg_sc=int(np.mean([r.get("score",0) for r in res]))
        top_sc=max(r.get("score",0) for r in res)
        ups=[r.get("upside",0) or 0 for r in res]
        avg_up=np.mean(ups); top_up=max(ups)
        health_a=sum(1 for r in res if r.get("fin_health_grade")=="A")

        st.markdown(f"""
<div class="kpi-strip">
  <div class="kpi g"><div class="kpi-l">BUY</div><div class="kpi-v g">{buy_n}</div><div class="kpi-d">強買</div></div>
  <div class="kpi y"><div class="kpi-l">WATCH</div><div class="kpi-v y">{wch_n}</div><div class="kpi-d">觀察</div></div>
  <div class="kpi w"><div class="kpi-l">HOLD</div><div class="kpi-v">{hld_n}</div><div class="kpi-d">持有</div></div>
  <div class="kpi r"><div class="kpi-l">AVOID</div><div class="kpi-v r">{avd_n}</div><div class="kpi-d">迴避</div></div>
  <div class="kpi b"><div class="kpi-l">平均評分</div><div class="kpi-v b">{avg_sc}</div><div class="kpi-d">/100</div></div>
  <div class="kpi p"><div class="kpi-l">平均上漲</div><div class="kpi-v p">{avg_up:+.1f}%</div><div class="kpi-d">預期</div></div>
  <div class="kpi c"><div class="kpi-l">最大上漲</div><div class="kpi-v c">{top_up:+.1f}%</div><div class="kpi-d">單檔</div></div>
  <div class="kpi g"><div class="kpi-l">財健A級</div><div class="kpi-v g">{health_a}</div><div class="kpi-d">檔</div></div>
</div>
""",unsafe_allow_html=True)

        rows=""
        for r in res:
            cd=r.get("code",""); nm=r.get("name","")
            pv=r.get("price"); tv=r.get("target_price"); uv=r.get("upside")
            sc=r.get("score",0); sg=r.get("signal","HOLD")
            pev=r.get("pe"); rov=r.get("roe"); dyv=r.get("dividend_yield")
            rsv=r.get("rsi"); rgv=r.get("revenue_growth")
            macdv=r.get("macd"); macdsv=r.get("macd_signal")
            ma20v=r.get("ma20"); fhg_=r.get("fin_health_grade","—")
            betav=r.get("beta"); sharpev=r.get("sharpe")
            volr=r.get("volume_ratio",1.0); vols=r.get("volume_status","normal")
            macd_ok_=bool(macdv and macdsv and macdv>macdsv)
            ama=bool(pv and ma20v and pv>ma20v)
            up_td="upp" if (uv and uv>=0) else "upn"
            fhg_cls_={"A":"pos","B":"neu","C":"warn","D":"neg"}.get(fhg_,"dim")
            vol_cls_="warn" if vols=="high" else ("neg" if vols=="extreme" else "dim")
            rows+=f"""
<tr class="{sg}">
  <td><div class="score-hex {shex(sc)}" style="width:32px;height:32px;font-size:.68rem;border-radius:5px">{sc}</div></td>
  <td class="pri"><div>{cd}</div><div style="font-size:.54rem;color:var(--t2)">{nm[:8]}</div></td>
  <td>{sig_badge(sg)}</td>
  <td class="pri">{fp(pv)}</td>
  <td class="tp">{fp(tv)}</td>
  <td class="{up_td}">{f'{uv:+.1f}%' if uv is not None else '—'}</td>
  <td class="dim">{f'{pev:.1f}×' if pev else '—'}</td>
  <td class="{'pos' if (rov and rov>.12) else 'dim'}">{fpc(rov)}</td>
  <td class="{'pos' if (dyv and dyv>.04) else 'dim'}">{fpc(dyv)}</td>
  <td class="{'neg' if (rsv and rsv>70) else ('pos' if (rsv and rsv<35) else 'dim')}">{f'{rsv:.0f}' if rsv else '—'}</td>
  <td class="{'pos' if (rgv and rgv>.1) else 'dim'}">{fpc(rgv)}</td>
  <td class="{'pos' if macd_ok_ else 'dim'}">{'金叉↑' if macd_ok_ else ('死叉↓' if (macdv and macdsv and macdv<macdsv) else '—')}</td>
  <td class="{'pos' if ama else 'neg'}">{'多頭' if ama else '空頭'}</td>
  <td class="{fhg_cls_}">{fhg_}</td>
  <td class="{vol_cls_}">{f'{volr:.1f}x' if volr else '—'}</td>
</tr>"""

        st.markdown(f"""
<div class="rtw"><table class="rt">
  <thead><tr>
    <th>評分</th><th>個股</th><th>信號</th>
    <th>現價</th><th>目標價</th><th>上漲</th>
    <th>PE</th><th>ROE</th><th>殖利率</th>
    <th>RSI</th><th>營收成長</th><th>MACD</th><th>MA20</th>
    <th>財健</th><th>量能</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table></div>
""",unsafe_allow_html=True)

        # 快速跳轉
        st.markdown('<hr><div style="font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.15em;margin-bottom:6px">快速跳轉 · 前10名</div>',unsafe_allow_html=True)
        top10=res[:10]
        cols_j=st.columns(len(top10))
        for col_j,r in zip(cols_j,top10):
            with col_j:
                if st.button(f"{r['code']}\n{r.get('name','')[:4]}\n{r.get('score',0)}",use_container_width=True,key=f"j_{r['code']}"):
                    st.session_state.selected_stock=r["code"]
                    st.session_state.detail_cache={}
                    st.rerun()
    else:
        st.markdown('<div class="empty-state"><div class="empty-state-ico">🔍</div><div class="empty-state-txt">點擊「立即掃描」開始篩選<br>並行引擎 16 線程 · 速度快 5–10×<br>v8 新增：財務健康 · 風險評估 · 量能異常偵測<br>支援 CSV 匯出 · LINE Notify · Discord 推播</div></div>',unsafe_allow_html=True)


# ════════════════════════════ TAB 3 — 排程紀錄 ════════════════════════════
with tab3:
    c1_t3,c2_t3=st.columns([5,1])
    with c1_t3:
        st.markdown('<div style="font-family:var(--mono);font-size:.5rem;color:var(--t2);text-transform:uppercase;letter-spacing:.18em;margin-bottom:10px">// SCHEDULER LOG · v8</div>',unsafe_allow_html=True)
    with c2_t3:
        if st.button("CLR",use_container_width=True,key="clr"):
            st.session_state.sched_log=[]; st.rerun()
    log=st.session_state.sched_log
    if log:
        html='<div class="logwrap">'+"".join(f'<div class="ll {t}">{m}</div>' for t,m in log)+'</div>'
        st.markdown(html,unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-family:var(--mono);font-size:.65rem;color:var(--t2);padding:20px 0">尚無排程紀錄 · 啟動排程後此處顯示執行紀錄</div>',unsafe_allow_html=True)


# ════════════════════════════ TAB 4 — 多空儀表板 ════════════════════════════
with tab4:
    res_dash=st.session_state.scan_results
    if not res_dash:
        st.markdown('<div class="empty-state"><div class="empty-state-ico">🎯</div><div class="empty-state-txt">請先執行批量掃描<br>儀表板將顯示多空分析、產業分布與整體市場情緒</div></div>',unsafe_allow_html=True)
    else:
        buy_n_=sum(1 for r in res_dash if r.get("signal")=="BUY")
        wch_n_=sum(1 for r in res_dash if r.get("signal")=="WATCH")
        avd_n_=sum(1 for r in res_dash if r.get("signal")=="AVOID")
        total_=len(res_dash)
        bull_pct=int((buy_n_+wch_n_*0.5)/total_*100) if total_>0 else 50
        bear_pct=100-bull_pct

        # ── 多空力道 ──
        st.markdown(f"""
<div class="bb-panel">
  <div class="bb-panel-lbl">市場多空力道 · 基於掃描結果</div>
  <div style="display:flex;justify-content:space-between;font-family:var(--mono);font-size:.52rem;color:var(--t2);margin-bottom:6px">
    <span style="color:var(--g)">多方 {bull_pct}%</span>
    <span style="color:var(--r)">空方 {bear_pct}%</span>
  </div>
  <div class="bb-gauge">
    <div class="bb-fill bull" style="width:{bull_pct}%"></div>
  </div>
  <div class="bb-labels">
    <span style="color:var(--g)">BUY {buy_n_} · WATCH {wch_n_}</span>
    <span style="color:var(--r)">AVOID {avd_n_}</span>
  </div>
</div>
""",unsafe_allow_html=True)

        # ── 評分分布圖 ──
        d_chart,b_chart=st.columns(2)
        with d_chart:
            scores=[r.get("score",0) for r in res_dash]
            signals=[r.get("signal","HOLD") for r in res_dash]
            color_map={"BUY":"#00f090","WATCH":"#ffbe00","HOLD":"#7a9ab8","AVOID":"#ff3358"}
            colors=[color_map.get(s,"#7a9ab8") for s in signals]
            codes_=[r.get("code","") for r in res_dash]
            names_=[r.get("name","")[:6] for r in res_dash]
            ups_=[r.get("upside",0) or 0 for r in res_dash]

            fig_sc=go.Figure(go.Bar(
                x=[f"{c}<br>{n}" for c,n in zip(codes_,names_)],
                y=scores,marker_color=colors,marker_opacity=.85,
                text=[f"{s}分" for s in scores],textposition="outside",
                textfont=dict(family="JetBrains Mono",size=9,color="#7a9ab8"),
            ))
            fig_sc.update_layout(
                paper_bgcolor="#02040a",plot_bgcolor="#02040a",
                font=dict(family="JetBrains Mono",size=9,color="#3d5470"),
                margin=dict(l=30,r=10,t=30,b=60),height=280,
                title=dict(text="評分分布",font=dict(size=11,color="#7a9ab8"),x=0),
                xaxis=dict(tickfont=dict(size=8),tickangle=-45,gridcolor="#0c1829"),
                yaxis=dict(range=[0,110],gridcolor="#0c1829",tickfont=dict(size=9)),
                showlegend=False,
            )
            st.plotly_chart(fig_sc,use_container_width=True,config={"displayModeBar":False})

        with b_chart:
            fig_up=go.Figure(go.Scatter(
                x=scores,y=ups_,mode="markers+text",
                text=codes_,textposition="top center",
                textfont=dict(family="JetBrains Mono",size=8,color="#3d5470"),
                marker=dict(
                    size=[max(8,min(20,s/10)) for s in scores],
                    color=colors,opacity=.85,
                    line=dict(color="#02040a",width=1)
                ),
            ))
            fig_up.add_hline(y=10,line_dash="dot",line_color="rgba(0,240,144,.3)",line_width=1)
            fig_up.add_vline(x=70,line_dash="dot",line_color="rgba(0,240,144,.3)",line_width=1)
            fig_up.update_layout(
                paper_bgcolor="#02040a",plot_bgcolor="#02040a",
                font=dict(family="JetBrains Mono",size=9,color="#3d5470"),
                margin=dict(l=40,r=10,t=30,b=30),height=280,
                title=dict(text="評分 vs 上漲空間",font=dict(size=11,color="#7a9ab8"),x=0),
                xaxis=dict(title="評分",gridcolor="#0c1829",tickfont=dict(size=9),range=[40,105]),
                yaxis=dict(title="上漲空間%",gridcolor="#0c1829",tickfont=dict(size=9)),
                showlegend=False,
            )
            st.plotly_chart(fig_up,use_container_width=True,config={"displayModeBar":False})

        # ── TOP BUY 清單 ──
        top_buy=[r for r in res_dash if r.get("signal")=="BUY"][:8]
        top_watch=[r for r in res_dash if r.get("signal")=="WATCH"][:8]

        col_buy,col_watch=st.columns(2)
        with col_buy:
            st.markdown('<div style="font-family:var(--mono);font-size:.52rem;color:var(--g);text-transform:uppercase;letter-spacing:.15em;margin-bottom:8px">🟢 TOP BUY 強買清單</div>',unsafe_allow_html=True)
            for r in top_buy:
                up_v=r.get("upside",0) or 0
                st.markdown(f"""
<div style="background:var(--bg1);border:1px solid rgba(0,240,144,.2);border-left:3px solid var(--g);border-radius:5px;padding:8px 12px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center">
  <div><span style="font-family:var(--mono);font-size:.78rem;font-weight:700;color:var(--t0)">{r['code']}</span><span style="font-family:var(--mono);font-size:.6rem;color:var(--t2);margin-left:6px">{r.get('name','')[:6]}</span></div>
  <div style="text-align:right">
    <div style="font-family:var(--mono);font-size:.72rem;color:var(--t0)">{fp(r.get('price'))}</div>
    <div style="font-family:var(--mono);font-size:.6rem;color:var(--g)">{up_v:+.1f}% ↑ {fp(r.get('target_price'))}</div>
  </div>
  <div class="score-hex {shex(r.get('score',0))}" style="width:28px;height:28px;font-size:.62rem;border-radius:5px;margin-left:8px">{r.get('score',0)}</div>
</div>
""",unsafe_allow_html=True)

        with col_watch:
            st.markdown('<div style="font-family:var(--mono);font-size:.52rem;color:var(--y);text-transform:uppercase;letter-spacing:.15em;margin-bottom:8px">🟡 TOP WATCH 觀察清單</div>',unsafe_allow_html=True)
            for r in top_watch:
                up_v=r.get("upside",0) or 0
                st.markdown(f"""
<div style="background:var(--bg1);border:1px solid rgba(255,190,0,.2);border-left:3px solid var(--y);border-radius:5px;padding:8px 12px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center">
  <div><span style="font-family:var(--mono);font-size:.78rem;font-weight:700;color:var(--t0)">{r['code']}</span><span style="font-family:var(--mono);font-size:.6rem;color:var(--t2);margin-left:6px">{r.get('name','')[:6]}</span></div>
  <div style="text-align:right">
    <div style="font-family:var(--mono);font-size:.72rem;color:var(--t0)">{fp(r.get('price'))}</div>
    <div style="font-family:var(--mono);font-size:.6rem;color:var(--y)">{up_v:+.1f}% ↑ {fp(r.get('target_price'))}</div>
  </div>
  <div class="score-hex {shex(r.get('score',0))}" style="width:28px;height:28px;font-size:.62rem;border-radius:5px;margin-left:8px">{r.get('score',0)}</div>
</div>
""",unsafe_allow_html=True)

        # ── 風險分布 ──
        st.markdown('<hr>',unsafe_allow_html=True)
        st.markdown('<div style="font-family:var(--mono);font-size:.52rem;color:var(--t2);text-transform:uppercase;letter-spacing:.15em;margin-bottom:8px">// 財務健康分布</div>',unsafe_allow_html=True)
        fh_counts={"A":0,"B":0,"C":0,"D":0}
        for r in res_dash:
            g_=r.get("fin_health_grade","C")
            if g_ in fh_counts: fh_counts[g_]+=1

        fh_cols=st.columns(4)
        for i,(grade,cnt) in enumerate(fh_counts.items()):
            color={"A":"var(--g)","B":"var(--b)","C":"var(--y)","D":"var(--r)"}.get(grade,"var(--t2)")
            desc={"A":"優良","B":"良好","C":"一般","D":"偏弱"}.get(grade,"")
            fh_cols[i].markdown(f"""
<div style="background:var(--bg1);border:1px solid var(--line2);border-radius:6px;padding:12px;text-align:center">
  <div style="font-family:var(--mono);font-size:1.8rem;font-weight:700;color:{color}">{grade}</div>
  <div style="font-family:var(--mono);font-size:.5rem;color:var(--t2)">{desc}</div>
  <div style="font-family:var(--mono);font-size:1rem;font-weight:700;color:{color};margin-top:4px">{cnt} 檔</div>
</div>
""",unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
# 自動刷新 (排程運行中)
# ═════════════════════════════════════════════════════════════════════════════
if st.session_state.sched_running:
    time.sleep(1); st.rerun()
