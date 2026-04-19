"""
台股 AI 狙擊手 ULTRA v9.0
pip install streamlit yfinance pandas numpy requests plotly apscheduler beautifulsoup4 lxml urllib3
streamlit run taiwan_stock_ultra_v9.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import urllib3, datetime, time, re, concurrent.futures
from typing import Optional, Dict, List, Tuple, Any
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="台股狙擊手 v9", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# ─────────────────────────────────────────────────────────────────────────────
# CSS  (所有 { } 都用雙括號 {{ }} 讓 f-string 不解析)
# ─────────────────────────────────────────────────────────────────────────────
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&family=JetBrains+Mono:wght@300;400;600;700&display=swap');

:root {
  --bg0:#030810; --bg1:#060f1c; --bg2:#091529; --bg3:#0e1e36;
  --ln:#122040; --ln2:#1c3058; --ln3:#2a4578;
  --t0:#e8f4ff; --t1:#8ab0cc; --t2:#3e5f80; --t3:#1a3050;
  --g:#00e87a;  --g2:#00b860; --g3:rgba(0,232,122,.1);
  --r:#ff2d55;  --r2:#cc1a3a; --r3:rgba(255,45,85,.1);
  --y:#ffd60a;  --y3:rgba(255,214,10,.1);
  --b:#1e90ff;  --b2:#0060cc; --b3:rgba(30,144,255,.1);
  --p:#bf5af2;  --p3:rgba(191,90,242,.1);
  --c:#32d2f5;  --c3:rgba(50,210,245,.1);
  --o:#ff8800;  --o3:rgba(255,136,0,.1);
  --mono:'JetBrains Mono',monospace;
  --tc:'Noto Sans TC','Microsoft JhengHei',sans-serif;
  --sh-g:0 0 16px rgba(0,232,122,.3);
  --sh-r:0 0 16px rgba(255,45,85,.3);
  --sh-b:0 0 16px rgba(30,144,255,.3);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body,[class*="css"]{font-family:var(--tc);background:var(--bg0);color:var(--t0)}
#MainMenu,footer,header{visibility:hidden}
.stApp{background:var(--bg0)}
.main .block-container{padding:.5rem 1rem 3rem;max-width:100%}

/* grid bg */
.stApp::after{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:linear-gradient(rgba(0,232,122,.005) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(0,232,122,.005) 1px,transparent 1px);
  background-size:40px 40px;
}

/* ── HEADER ── */
.hdr{background:linear-gradient(180deg,#08142a 0%,#040c1a 100%);border-bottom:1px solid var(--ln2);
     border-top:3px solid var(--g);margin-bottom:10px;position:relative;overflow:hidden}
.hdr::before{content:'';position:absolute;top:-60px;left:50%;transform:translateX(-50%);
  width:800px;height:120px;border-radius:50%;
  background:radial-gradient(ellipse,rgba(0,232,122,.07) 0%,transparent 70%);animation:glow-pulse 4s ease-in-out infinite}
@keyframes glow-pulse{0%,100%{opacity:.6}50%{opacity:1}}
.hdr-inner{display:flex;align-items:stretch;position:relative;z-index:1}
.hdr-bar{width:4px;background:linear-gradient(180deg,var(--g),var(--b),var(--p));flex-shrink:0}
.hdr-body{flex:1;padding:14px 20px;display:flex;align-items:center;gap:16px}
.hdr-icon{font-size:2rem;line-height:1;flex-shrink:0}
.hdr-text{flex:1}
.hdr-eyebrow{font-family:var(--mono);font-size:.48rem;color:var(--t2);letter-spacing:.25em;text-transform:uppercase;margin-bottom:4px}
.hdr-title{font-weight:900;font-size:1.7rem;letter-spacing:-.03em;line-height:1;
  background:linear-gradient(100deg,#e8f4ff 0%,#00e87a 45%,#1e90ff 80%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hdr-sub{font-family:var(--mono);font-size:.5rem;color:var(--t2);letter-spacing:.12em;text-transform:uppercase;margin-top:3px}
.hdr-chips{display:flex;gap:5px;margin-top:7px;flex-wrap:wrap}
.chip{display:inline-flex;align-items:center;gap:3px;font-family:var(--mono);
  font-size:.48rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;
  padding:3px 7px;border-radius:3px;border:1px solid}
.chip-live{color:var(--g);border-color:rgba(0,232,122,.35);background:var(--g3)}
.chip-dot{width:5px;height:5px;border-radius:50%;background:var(--g);animation:blink 1.2s step-end infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
.chip-time{color:var(--t2);border-color:var(--ln);background:transparent}
.chip-v9{color:var(--p);border-color:rgba(191,90,242,.35);background:var(--p3)}
.chip-sched-on{color:var(--g);border-color:rgba(0,232,122,.35);background:var(--g3)}
.chip-sched-off{color:var(--t2);border-color:var(--ln);background:transparent}
.chip-alert{color:var(--y);border-color:rgba(255,214,10,.35);background:var(--y3);animation:blink 2s step-end infinite}
.hdr-stats{display:flex;align-self:stretch;border-left:1px solid var(--ln2)}
.hdr-stat{display:flex;flex-direction:column;justify-content:center;align-items:center;
  padding:0 22px;border-right:1px solid var(--ln2);min-width:80px}
.hdr-stat-n{font-family:var(--mono);font-size:1.15rem;font-weight:700;line-height:1}
.hdr-stat-l{font-family:var(--mono);font-size:.44rem;color:var(--t2);text-transform:uppercase;letter-spacing:.15em;margin-top:3px}
.hdr-tape{border-top:1px solid var(--ln);padding:6px 20px;font-family:var(--mono);font-size:.5rem;
  color:var(--t2);display:flex;gap:18px;align-items:center}
.tape-item{display:flex;gap:5px;align-items:center}
.tape-code{color:var(--t1);font-weight:600}
.tape-p{color:var(--t0)}
.tape-up{color:var(--g)}.tape-dn{color:var(--r)}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"]{background:var(--bg1)!important;border-right:1px solid var(--ln)!important;min-width:265px!important}
section[data-testid="stSidebar"]>div{padding:0!important}
.sb-hdr{display:flex;align-items:center;gap:7px;padding:9px 13px;
  font-family:var(--mono);font-size:.48rem;font-weight:700;color:var(--t2);
  text-transform:uppercase;letter-spacing:.18em;background:var(--bg2);border-bottom:1px solid var(--ln)}
.sb-hdr-dot{width:5px;height:2px;background:var(--g);border-radius:1px}
.sb-body{padding:9px 13px;border-bottom:1px solid var(--ln)}
.sh-row{display:flex;align-items:center;gap:7px;padding:5px 7px;border-radius:4px;
  margin-bottom:3px;background:var(--bg2);border:1px solid var(--ln);cursor:pointer;
  transition:border-color .15s}
.sh-row:hover{border-color:var(--ln3)}
.sh-code{font-family:var(--mono);font-size:.75rem;font-weight:700;color:var(--g);min-width:36px}
.sh-name{font-size:.62rem;color:var(--t1);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.wl-row{display:flex;align-items:center;gap:6px;padding:5px 7px;border-radius:4px;
  margin-bottom:2px;background:var(--bg2);border:1px solid var(--ln)}
.wl-code{font-family:var(--mono);font-size:.68rem;font-weight:700;color:var(--g);width:36px;flex-shrink:0}
.wl-name{font-size:.58rem;color:var(--t1);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.wl-px{font-family:var(--mono);font-size:.6rem;color:var(--t0);font-weight:600}
.wl-up{font-family:var(--mono);font-size:.55rem;color:var(--g)}
.wl-dn{font-family:var(--mono);font-size:.55rem;color:var(--r)}

/* ── ALERT BANNER ── */
.alert-bar{background:var(--bg1);border:1px solid rgba(255,214,10,.3);border-left:3px solid var(--y);
  border-radius:6px;padding:8px 14px;margin-bottom:8px;display:flex;align-items:center;gap:10px;
  font-family:var(--mono);font-size:.58rem}
.alert-items{flex:1;display:flex;gap:14px;flex-wrap:wrap}

/* ── KPI STRIP ── */
.kpi-row{display:grid;grid-template-columns:repeat(8,1fr);gap:5px;margin-bottom:9px}
.kpi{position:relative;overflow:hidden;background:var(--bg1);border:1px solid var(--ln);
  border-radius:5px;padding:10px 11px;transition:transform .15s,border-color .15s}
.kpi:hover{transform:translateY(-1px);border-color:var(--ln3)}
.kpi::after{content:'';position:absolute;bottom:0;left:0;right:0;height:2px}
.kpi.g::after{background:var(--g)}.kpi.r::after{background:var(--r)}.kpi.y::after{background:var(--y)}
.kpi.b::after{background:var(--b)}.kpi.p::after{background:var(--p)}.kpi.c::after{background:var(--c)}
.kpi.o::after{background:var(--o)}.kpi.w::after{background:var(--t1)}
.kpi-l{font-family:var(--mono);font-size:.43rem;color:var(--t2);text-transform:uppercase;letter-spacing:.12em;margin-bottom:4px}
.kpi-v{font-family:var(--mono);font-size:1.2rem;font-weight:700;line-height:1}
.kpi-v.g{color:var(--g)}.kpi-v.r{color:var(--r)}.kpi-v.y{color:var(--y)}
.kpi-v.b{color:var(--b)}.kpi-v.p{color:var(--p)}.kpi-v.c{color:var(--c)}.kpi-v.o{color:var(--o)}
.kpi-d{font-family:var(--mono);font-size:.44rem;color:var(--t2);margin-top:2px}

/* ── STOCK HEADER CARD ── */
.scard{background:var(--bg1);border:1px solid var(--ln2);border-radius:8px;margin-bottom:10px;overflow:hidden}
.scard-top{display:flex;align-items:stretch;border-bottom:1px solid var(--ln)}
.scard-stripe{width:4px;background:linear-gradient(180deg,var(--g),var(--b),var(--p));flex-shrink:0}
.scard-id{padding:14px 16px;border-right:1px solid var(--ln);min-width:160px}
.scard-code{font-family:var(--mono);font-size:1.5rem;font-weight:700;line-height:1}
.scard-sfx{font-size:.58rem;color:var(--t2);margin-left:4px}
.scard-name{font-size:.85rem;font-weight:700;color:var(--t1);margin-top:4px}
.scard-ind{font-family:var(--mono);font-size:.48rem;color:var(--t2);margin-top:2px}
.scard-px{flex:1;padding:14px 18px}
.scard-price{font-family:var(--mono);font-size:2.2rem;font-weight:700;line-height:1}
.scard-unit{font-size:.65rem;color:var(--t2);margin-left:5px}
.scard-chg{font-family:var(--mono);font-size:.82rem;font-weight:600;margin-top:3px}
.scard-chg.pos{color:var(--g)}.scard-chg.neg{color:var(--r)}
.scard-ohlc{display:flex;gap:14px;margin-top:8px;font-family:var(--mono);font-size:.52rem;color:var(--t2)}
.scard-risk{display:flex;gap:14px;margin-top:5px;font-family:var(--mono);font-size:.52rem;color:var(--t2)}
.scard-badges{display:flex;gap:5px;flex-wrap:wrap;margin-top:8px;align-items:center}
.scard-sig-block{padding:14px 16px;border-left:1px solid var(--ln);min-width:160px;
  display:flex;flex-direction:column;justify-content:center;gap:8px}
.score-ring{width:54px;height:54px;border-radius:50%;border:2px solid;display:flex;flex-direction:column;
  align-items:center;justify-content:center;flex-shrink:0}
.score-ring.hi{border-color:var(--g);background:var(--g3);box-shadow:var(--sh-g)}
.score-ring.md{border-color:var(--y);background:var(--y3)}
.score-ring.lo{border-color:var(--r);background:var(--r3);box-shadow:var(--sh-r)}
.score-n{font-family:var(--mono);font-size:.9rem;font-weight:700;line-height:1}
.score-l{font-family:var(--mono);font-size:.38rem;color:var(--t2);text-transform:uppercase;margin-top:1px}

/* signal badge */
.sig{display:inline-flex;align-items:center;gap:4px;font-family:var(--mono);font-size:.58rem;
  font-weight:700;letter-spacing:.06em;padding:4px 9px;border-radius:3px;border:1px solid}
.sig-BUY{color:var(--g);border-color:rgba(0,232,122,.4);background:var(--g3)}
.sig-WATCH{color:var(--y);border-color:rgba(255,214,10,.4);background:var(--y3)}
.sig-HOLD{color:var(--t1);border-color:var(--ln2);background:var(--bg2)}
.sig-AVOID{color:var(--r);border-color:rgba(255,45,85,.4);background:var(--r3)}

/* vol badge */
.vol-badge{display:inline-flex;align-items:center;gap:3px;font-family:var(--mono);font-size:.5rem;
  font-weight:700;padding:3px 7px;border-radius:3px;border:1px solid}
.vol-badge.extreme{color:var(--r);border-color:rgba(255,45,85,.4);background:var(--r3);animation:blink .8s step-end infinite}
.vol-badge.high{color:var(--y);border-color:rgba(255,214,10,.4);background:var(--y3)}
.vol-badge.normal{color:var(--t2);border-color:var(--ln);background:transparent}
.fh-badge{display:inline-flex;align-items:center;gap:3px;font-family:var(--mono);font-size:.5rem;
  font-weight:700;padding:3px 7px;border-radius:3px;border:1px solid}
.fh-A{color:var(--g);border-color:rgba(0,232,122,.4);background:var(--g3)}
.fh-B{color:var(--b);border-color:rgba(30,144,255,.4);background:var(--b3)}
.fh-C{color:var(--y);border-color:rgba(255,214,10,.4);background:var(--y3)}
.fh-D{color:var(--r);border-color:rgba(255,45,85,.4);background:var(--r3)}

/* ── DATA GRID ── */
.dgrid{display:grid;gap:4px;margin:8px 0}
.dgrid-6{grid-template-columns:repeat(6,1fr)}
.dgrid-8{grid-template-columns:repeat(8,1fr)}
.dcell{background:var(--bg2);border:1px solid var(--ln);border-radius:4px;padding:8px 10px;
  transition:border-color .15s,background .15s}
.dcell:hover{border-color:var(--ln3);background:var(--bg3)}
.dcell-k{font-family:var(--mono);font-size:.42rem;color:var(--t2);text-transform:uppercase;
  letter-spacing:.1em;margin-bottom:3px}
.dcell-v{font-family:var(--mono);font-size:.78rem;font-weight:700;color:var(--t0)}
.dcell-v.pos{color:var(--g)}.dcell-v.neg{color:var(--r)}.dcell-v.warn{color:var(--y)}.dcell-v.neu{color:var(--b)}

/* ── PANEL ── */
.panel{background:var(--bg2);border:1px solid var(--ln2);border-radius:6px;padding:12px 14px;margin-bottom:8px}
.panel-title{font-family:var(--mono);font-size:.46rem;color:var(--t2);text-transform:uppercase;
  letter-spacing:.15em;margin-bottom:10px;display:flex;align-items:center;gap:6px}
.panel-title::before{content:'';width:8px;height:2px;background:var(--g);border-radius:1px}

/* score bars */
.sbar{display:flex;align-items:center;gap:8px;margin:5px 0}
.sbar-k{font-size:.54rem;color:var(--t1);width:55px;flex-shrink:0}
.sbar-track{flex:1;height:4px;background:var(--ln);border-radius:2px;overflow:hidden}
.sbar-fill{height:100%;border-radius:2px}
.sbar-fill.g{background:linear-gradient(90deg,var(--g2),var(--g))}
.sbar-fill.y{background:linear-gradient(90deg,#b09600,var(--y))}
.sbar-fill.r{background:linear-gradient(90deg,var(--r2),var(--r))}
.sbar-fill.b{background:linear-gradient(90deg,var(--b2),var(--b))}
.sbar-n{font-family:var(--mono);font-size:.52rem;color:var(--t1);width:36px;text-align:right}

/* checklist */
.chk{display:flex;align-items:center;gap:6px;padding:4px 0;border-bottom:1px solid var(--ln)}
.chk:last-child{border:none}
.chk-ic{font-family:var(--mono);font-size:.58rem;font-weight:700;width:14px;flex-shrink:0}
.chk-txt{font-size:.56rem}
.chk.ok .chk-ic{color:var(--g)}.chk.ok .chk-txt{color:var(--t1)}
.chk.no .chk-ic{color:var(--t3)}.chk.no .chk-txt{color:var(--t2)}

/* target price */
.tp-panel{background:var(--bg2);border:1px solid var(--ln2);border-radius:6px;padding:14px;
  margin-bottom:8px;position:relative;overflow:hidden}
.tp-panel::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--g),transparent)}
.tp-row{display:flex;justify-content:space-between;align-items:flex-end;margin-bottom:10px}
.tp-item{text-align:center}
.tp-lbl{font-family:var(--mono);font-size:.42rem;color:var(--t2);text-transform:uppercase;
  letter-spacing:.1em;margin-bottom:3px}
.tp-val{font-family:var(--mono);font-size:.88rem;font-weight:700}
.tp-val.cur{color:var(--t0)}.tp-val.tp{color:var(--g);font-size:1.05rem}.tp-val.lo{color:var(--b)}.tp-val.hi{color:var(--p)}
.tp-big{font-family:var(--mono);font-size:1.5rem;font-weight:700;line-height:1}
.tp-big.pos{color:var(--g);text-shadow:var(--sh-g)}.tp-big.neg{color:var(--r)}
.tp-track{position:relative;height:7px;background:var(--bg3);border-radius:3px;margin:10px 0 18px}
.tp-zone{position:absolute;height:100%;border-radius:3px;background:rgba(30,144,255,.2);border:1px solid rgba(30,144,255,.4)}
.tp-cur{position:absolute;top:-5px;width:2px;height:17px;background:#fff;border-radius:1px;
  transform:translateX(-50%);box-shadow:0 0 8px rgba(255,255,255,.8)}
.tp-tp{position:absolute;top:-5px;width:2px;height:17px;border-radius:1px;transform:translateX(-50%)}
.tp-lbl2{position:absolute;font-family:var(--mono);font-size:.42rem;white-space:nowrap;transform:translateX(-50%)}

/* signal card */
.sig-card{border-radius:6px;padding:12px;margin-bottom:8px;border:1px solid;border-left:3px solid}
.sig-card.BUY{border-color:rgba(0,232,122,.2);border-left-color:var(--g);background:rgba(0,232,122,.03)}
.sig-card.WATCH{border-color:rgba(255,214,10,.2);border-left-color:var(--y);background:rgba(255,214,10,.03)}
.sig-card.HOLD{border-color:var(--ln2);border-left-color:var(--t2);background:var(--bg2)}
.sig-card.AVOID{border-color:rgba(255,45,85,.2);border-left-color:var(--r);background:rgba(255,45,85,.03)}
.sig-card-t{font-family:var(--mono);font-size:.68rem;font-weight:700;margin-bottom:5px}
.sig-card-b{font-size:.68rem;color:var(--t1);line-height:1.65}

/* pivot */
.pv-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:4px}
.pv-cell{background:var(--bg3);border-radius:4px;padding:7px;text-align:center}
.pv-k{font-family:var(--mono);font-size:.4rem;color:var(--t2);text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px}
.pv-v{font-family:var(--mono);font-size:.75rem;font-weight:700}
.pv-cell.R .pv-v{color:var(--r)}.pv-cell.P .pv-v{color:var(--y)}.pv-cell.S .pv-v{color:var(--g)}

/* institution bars */
.inst-row{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid var(--ln)}
.inst-row:last-child{border:none}
.inst-name{font-size:.54rem;color:var(--t1);width:50px;flex-shrink:0}
.inst-wrap{flex:1;height:5px;background:var(--ln);border-radius:2px;position:relative;overflow:visible}
.inst-bar-buy{position:absolute;top:0;left:50%;height:100%;border-radius:0 2px 2px 0;background:var(--g)}
.inst-bar-sell{position:absolute;top:0;right:50%;height:100%;border-radius:2px 0 0 2px;background:var(--r)}
.inst-val{font-family:var(--mono);font-size:.58rem;font-weight:700;width:55px;text-align:right}

/* risk cells */
.risk-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.risk-cell{background:var(--bg3);border-radius:4px;padding:8px}
.risk-k{font-family:var(--mono);font-size:.4rem;color:var(--t2);text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px}
.risk-v{font-family:var(--mono);font-size:.82rem;font-weight:700}
.risk-bar{height:3px;background:var(--ln);border-radius:2px;margin-top:5px;overflow:hidden}
.risk-bar-fill{height:100%;border-radius:2px}

/* backtest */
.bt-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:5px}
.bt-cell{background:var(--bg3);border-radius:4px;padding:7px;text-align:center}
.bt-k{font-family:var(--mono);font-size:.4rem;color:var(--t2);text-transform:uppercase;letter-spacing:.1em;margin-bottom:3px}
.bt-v{font-family:var(--mono);font-size:.78rem;font-weight:700}

/* financial health ring */
.fh-wrap{display:flex;gap:12px;align-items:center}
.fh-ring{width:62px;height:62px;border-radius:50%;border:3px solid;display:flex;flex-direction:column;
  align-items:center;justify-content:center;flex-shrink:0}
.fh-ring.A{border-color:var(--g);background:var(--g3)}.fh-ring.B{border-color:var(--b);background:var(--b3)}
.fh-ring.C{border-color:var(--y);background:var(--y3)}.fh-ring.D{border-color:var(--r);background:var(--r3)}
.fh-grade{font-family:var(--mono);font-size:1.25rem;font-weight:700;line-height:1}
.fh-score{font-family:var(--mono);font-size:.38rem;color:var(--t2);text-transform:uppercase;margin-top:1px}
.fh-details{flex:1;display:grid;grid-template-columns:repeat(3,1fr);gap:5px}
.fh-dc{background:var(--bg3);border-radius:3px;padding:6px 8px}
.fh-dk{font-family:var(--mono);font-size:.38rem;color:var(--t2);text-transform:uppercase;margin-bottom:2px}
.fh-dv{font-family:var(--mono);font-size:.72rem;font-weight:700}

/* news */
.news-wrap{padding:2px 0}
.news-item{display:flex;gap:8px;align-items:flex-start;padding:7px 0;border-bottom:1px solid var(--bg3)}
.news-item:last-child{border:none}
.news-ic{width:20px;height:20px;border-radius:3px;display:flex;align-items:center;justify-content:center;
  font-size:.58rem;font-weight:700;flex-shrink:0}
.news-ic.pos{background:var(--g3);color:var(--g)}.news-ic.neg{background:var(--r3);color:var(--r)}.news-ic.neu{background:var(--bg3);color:var(--t2)}
.news-body{flex:1;min-width:0}
.news-t{font-size:.73rem;color:var(--t1);margin-bottom:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.news-m{font-family:var(--mono);font-size:.5rem;color:var(--t2)}

/* result table */
.rt-wrap{overflow-x:auto;border:1px solid var(--ln2);border-radius:7px}
.rt{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:.66rem}
.rt th{background:var(--bg2);color:var(--t2);text-transform:uppercase;letter-spacing:.08em;
  font-size:.46rem;font-weight:700;padding:9px 10px;text-align:left;
  border-bottom:1px solid var(--ln2);white-space:nowrap;position:sticky;top:0;z-index:5}
.rt td{padding:7px 10px;border-bottom:1px solid var(--bg2);vertical-align:middle;white-space:nowrap}
.rt tr:last-child td{border:none}
.rt tr:hover td{background:var(--bg2)}
.rt tr.BUY td:first-child{border-left:3px solid var(--g)}
.rt tr.WATCH td:first-child{border-left:3px solid var(--y)}
.rt tr.AVOID td:first-child{border-left:3px solid var(--r)}
.rt tr.HOLD td:first-child{border-left:3px solid var(--ln2)}
.rt .c-pri{color:var(--t0);font-weight:700}.rt .c-tp{color:var(--b);font-weight:600}
.rt .c-up{color:var(--g);font-weight:700}.rt .c-dn{color:var(--r);font-weight:700}
.rt .c-dim{color:var(--t2)}.rt .c-pos{color:var(--g)}.rt .c-neg{color:var(--r)}.rt .c-warn{color:var(--y)}

/* bull/bear gauge */
.bb-panel{background:var(--bg2);border:1px solid var(--ln2);border-radius:6px;padding:12px 14px;margin-bottom:8px}
.bb-gauge{height:9px;border-radius:5px;background:var(--ln);overflow:hidden;position:relative;margin:6px 0}
.bb-fill{position:absolute;top:0;left:0;height:100%;border-radius:5px;
  background:linear-gradient(90deg,var(--g2),var(--g))}

/* tabs */
.stTabs [data-baseweb="tab-list"]{background:var(--bg1)!important;border-bottom:1px solid var(--ln)!important;gap:0!important;padding:0!important}
.stTabs [data-baseweb="tab"]{font-family:var(--mono)!important;font-size:.58rem!important;font-weight:700!important;
  letter-spacing:.1em!important;color:var(--t2)!important;text-transform:uppercase!important;
  border-radius:0!important;padding:10px 18px!important;border-bottom:2px solid transparent!important;transition:color .15s!important}
.stTabs [aria-selected="true"]{color:var(--g)!important;border-bottom-color:var(--g)!important;background:rgba(0,232,122,.03)!important}

/* buttons */
.stButton>button{font-family:var(--mono)!important;font-size:.62rem!important;font-weight:700!important;
  letter-spacing:.07em!important;border-radius:4px!important;text-transform:uppercase!important;transition:all .15s!important}
.stButton>button[kind="primary"]{background:var(--g)!important;color:#030810!important;border:none!important}
.stButton>button[kind="primary"]:hover{box-shadow:var(--sh-g)!important;transform:translateY(-1px)!important}
.stButton>button:not([kind="primary"]){background:var(--bg2)!important;color:var(--t1)!important;border:1px solid var(--ln2)!important}
.stButton>button:not([kind="primary"]):hover{border-color:var(--ln3)!important;color:var(--t0)!important}

/* inputs */
.stTextInput>div>div>input,.stTextArea>div>div>textarea{background:var(--bg2)!important;border:1px solid var(--ln2)!important;
  color:var(--t0)!important;border-radius:4px!important;font-family:var(--mono)!important;font-size:.7rem!important}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{border-color:var(--g)!important;box-shadow:0 0 0 1px rgba(0,232,122,.15)!important}
.stSlider>div>div>div>div{background:var(--g)!important}
.stProgress>div>div>div{background:var(--g)!important}
.stSelectbox>div>div{background:var(--bg2)!important;border:1px solid var(--ln2)!important;color:var(--t0)!important;border-radius:4px!important}
.stRadio>div{gap:5px!important}
label[data-baseweb="radio"]>div:first-child{background:var(--bg2)!important;border-color:var(--ln2)!important}
label[data-baseweb="radio"][aria-checked="true"]>div:first-child{background:var(--g)!important;border-color:var(--g)!important}
.streamlit-expanderHeader{background:var(--bg1)!important;border:1px solid var(--ln)!important;
  border-radius:5px!important;font-family:var(--mono)!important;font-size:.6rem!important;
  font-weight:700!important;color:var(--t1)!important;letter-spacing:.05em!important}
hr{border-color:var(--ln)!important;margin:8px 0!important}

/* log */
.logbox{background:var(--bg1);border:1px solid var(--ln);border-radius:6px;padding:12px 14px;font-family:var(--mono)}
.ll{font-size:.6rem;padding:2px 0;line-height:1.5}
.ll.ok{color:var(--g)}.ll.err{color:var(--r)}.ll.inf{color:var(--b)}.ll.dim{color:var(--t2)}

/* empty */
.empty{text-align:center;padding:60px 0}
.empty-ico{font-size:2.5rem;margin-bottom:12px}
.empty-txt{font-family:var(--mono);font-size:.7rem;color:var(--t2);line-height:1.9}

/* jump button group */
.jbtn-row{display:flex;gap:4px;flex-wrap:wrap;margin-top:8px}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULTS = dict(
    scan_results=[], scheduler=None, sched_running=False,
    sched_log=[], last_scan_time=None, auto_webhook="",
    scan_params={}, scan_codes=[], selected_stock=None,
    detail_cache={}, watchlist=[], alerts=[], alert_cfg={}, line_token="",
)
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────────────────
# STOCK NAMES  (內建 + API)
# ─────────────────────────────────────────────────────────────────────────────
_BUILTIN: Dict[str, str] = {
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
    "2049":"上銀","1590":"亞德客-KY","2105":"正新","2201":"裕隆","2204":"中華汽車",
    "1216":"統一","1102":"亞泥","1101":"台泥","2542":"興富發","5880":"合庫金",
    "2634":"漢翔","6770":"力積電","3529":"力旺","3661":"世芯-KY","6510":"精測",
    "8299":"群聯","3532":"台勝科","6472":"保瑞","3035":"智原","4966":"譜瑞-KY",
    "6278":"台表科","3260":"威剛","4958":"臻鼎-KY","3006":"晶豪科","2404":"漢唐",
    "3714":"富采","6488":"環球晶","2233":"宏致","2206":"三陽工業","9910":"豐泰",
    "6116":"彩晶","2368":"金像電","2383":"台光電","3227":"原相","4961":"天鈺",
    "6269":"台郡","2347":"聯強","2227":"裕日車","5234":"達興材料",
}
_INDUSTRY: Dict[str, str] = {
    "2330":"半導體","2454":"半導體","2303":"半導體","6415":"半導體","3034":"半導體",
    "3037":"半導體","2344":"半導體","6770":"半導體","3443":"半導體","3529":"力旺",
    "6488":"環球晶","4966":"譜瑞-KY","3006":"晶豪科",
    "2317":"電子製造","2382":"廣達","2357":"華碩","2395":"研華","2379":"瑞昱",
    "6285":"啟碁","2376":"技嘉","2301":"光寶科","2356":"英業達","3231":"緯創",
    "4938":"和碩","2385":"群光","6669":"緯穎","2327":"國巨","2474":"可成",
    "2881":"金融","2882":"金融","2886":"金融","2884":"金融","2885":"金融",
    "2891":"金融","2883":"金融","2887":"金融","2890":"金融","2892":"金融",
    "5871":"金融租賃","5876":"金融","5880":"金融","2823":"保險",
    "1301":"塑化","1303":"塑化","1326":"塑化","6505":"塑化",
    "2002":"鋼鐵","2014":"鋼鐵",
    "2603":"航運","2609":"航運","2615":"航運",
    "2412":"電信","3045":"電信","4904":"電信",
    "2308":"電子零件","3008":"光學","5274":"IC設計","2059":"川湖",
    "2207":"汽車","2201":"汽車","2204":"汽車","2206":"汽車","2105":"輪胎",
    "1216":"食品","2912":"零售","1101":"水泥","1102":"水泥",
    "2409":"面板","3481":"面板","6116":"面板",
    "2610":"航空","2618":"航空","2634":"航太",
    "2360":"測試","6510":"測試","2449":"封測","3711":"封測",
}

@st.cache_data(ttl=3600, show_spinner=False)
def load_names() -> Dict[str, str]:
    names = dict(_BUILTIN)
    hdr = {"User-Agent": "Mozilla/5.0"}
    for url, ck, nk in [
        ("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", "Code", "Name"),
        ("https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes", "SecuritiesCompanyCode", "CompanyName"),
    ]:
        try:
            r = requests.get(url, headers=hdr, timeout=12, verify=False)
            if r.status_code == 200:
                for it in r.json():
                    c = it.get(ck, "").strip(); n = it.get(nk, "").strip()
                    if len(c) == 4 and c.isdigit() and n:
                        names[c] = n
        except:
            pass
    return names

def search_stocks(q: str, names: Dict[str, str], limit: int = 10) -> List[Tuple[str, str]]:
    if not q.strip(): return []
    qu = q.strip().upper(); ql = q.strip().lower()
    t1, t2, t3 = [], [], []
    for code, name in names.items():
        if code == qu: t1.append((code, name))
        elif code.startswith(qu): t2.append((code, name))
        elif ql in name.lower() or ql in code.lower(): t3.append((code, name))
    seen, out = set(), []
    for item in t1 + t2 + t3:
        if item[0] not in seen:
            seen.add(item[0]); out.append(item)
    return out[:limit]

# ─────────────────────────────────────────────────────────────────────────────
# TECHNICALS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400, show_spinner=False)
def resolve_suffix(code: str) -> str:
    for sfx in [".TW", ".TWO"]:
        try:
            p = getattr(yf.Ticker(code + sfx).fast_info, "last_price", None)
            if p and float(p) > 0: return sfx
        except: pass
    return ".TW"

def calc_rsi(s: pd.Series, n: int = 14) -> pd.Series:
    d = s.diff()
    g = d.clip(lower=0).ewm(com=n - 1, min_periods=n).mean()
    l = (-d).clip(lower=0).ewm(com=n - 1, min_periods=n).mean()
    return 100 - 100 / (1 + g / l)

def calc_macd(s: pd.Series):
    m = s.ewm(span=12, adjust=False).mean() - s.ewm(span=26, adjust=False).mean()
    return m, m.ewm(span=9, adjust=False).mean()

def calc_bb(s: pd.Series, n: int = 20):
    m = s.rolling(n).mean(); std = s.rolling(n).std()
    return m + 2 * std, m, m - 2 * std

def calc_atr(h: pd.Series, l: pd.Series, c: pd.Series, n: int = 14) -> pd.Series:
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def calc_pivot(h: float, l: float, c: float) -> Dict[str, float]:
    p = (h + l + c) / 3
    return {"PP": round(p, 2),
            "R1": round(2*p - l, 2), "R2": round(p + (h - l), 2), "R3": round(h + 2*(p - l), 2),
            "S1": round(2*p - h, 2), "S2": round(p - (h - l), 2), "S3": round(l - 2*(h - p), 2)}

def calc_sharpe(ret: pd.Series) -> float:
    if len(ret) < 10: return 0.0
    m = ret.mean() * 252; s = ret.std() * np.sqrt(252)
    return round(m / s, 2) if s > 0 else 0.0

def calc_max_dd(prices: pd.Series) -> float:
    roll_max = prices.expanding().max()
    dd = (prices - roll_max) / roll_max
    return round(float(dd.min()) * 100, 1)

def vol_anomaly(vol: pd.Series) -> Tuple[float, str]:
    if len(vol) < 21: return 1.0, "normal"
    avg = vol.rolling(20).mean().iloc[-1]
    ratio = float(vol.iloc[-1]) / avg if avg > 0 else 1.0
    return round(ratio, 2), ("extreme" if ratio >= 3 else ("high" if ratio >= 1.8 else "normal"))

def backtest_ma(hist: pd.DataFrame) -> Dict[str, Any]:
    if hist is None or len(hist) < 40: return {}
    c = hist["Close"]
    ma5 = c.rolling(5).mean(); ma20 = c.rolling(20).mean()
    sig = (ma5 > ma20).astype(int)
    prev_sig = sig.shift(1).fillna(0)
    buy_sig = (sig == 1) & (prev_sig == 0)
    trades = []; in_trade = False; buy_px = 0.0
    for i in range(len(hist)):
        if buy_sig.iloc[i] and not in_trade:
            buy_px = float(c.iloc[i]); in_trade = True
        elif in_trade and (sig.iloc[i] == 0 or i == len(hist) - 1):
            ret = (float(c.iloc[i]) - buy_px) / buy_px * 100
            trades.append(ret); in_trade = False
    if not trades: return {}
    wins = [t for t in trades if t > 0]
    return {
        "trades": len(trades),
        "win_rate": round(len(wins) / len(trades) * 100, 1),
        "avg_ret": round(float(np.mean(trades)), 1),
        "max_win": round(float(max(trades)), 1),
        "max_loss": round(float(min(trades)), 1),
    }

# ─────────────────────────────────────────────────────────────────────────────
# TARGET PRICE  (永遠 > 現價)
# ─────────────────────────────────────────────────────────────────────────────
def estimate_target(price, pe, eps, pb, roe, dy, a_mean, a_low, a_high, n_ana,
                    rsi=None, macd=None, macd_sig=None, rg=None):
    if not price or price <= 0: return None, None, None
    rate = 0.08
    if roe:
        r = roe * 100
        rate += 0.08 if r >= 25 else (0.05 if r >= 18 else (0.03 if r >= 12 else (0.01 if r >= 8 else 0)))
    if dy:
        y = dy * 100
        rate += 0.04 if y >= 6 else (0.02 if y >= 4 else (0.01 if y >= 2 else 0))
    if rg and rg > 0:
        rate += 0.06 if rg >= .3 else (0.03 if rg >= .15 else (0.01 if rg >= .05 else 0))
    if pe and 0 < pe <= 15: rate += 0.03
    if rsi and 35 <= rsi <= 60: rate += 0.02
    if macd is not None and macd_sig is not None and macd > macd_sig: rate += 0.02
    model = price * (1 + rate)
    final = model
    if a_mean and a_mean > price and n_ana and n_ana >= 3:
        w = min(0.6, 0.2 + n_ana * 0.04)
        final = a_mean * w + model * (1 - w)
    final = max(final, price * 1.05)
    final = round(final, 1)
    tl = round(max(a_low if (a_low and a_low > price) else price * (1 + rate * .6), price * 1.03), 1)
    th = round(a_high if (a_high and a_high > price) else price * (1 + rate * 1.6), 1)
    tl = min(tl, final * 0.97); th = max(th, final * 1.08)
    return final, round(tl, 1), round(th, 1)

# ─────────────────────────────────────────────────────────────────────────────
# COMPOSITE SCORE  (5 維度)
# ─────────────────────────────────────────────────────────────────────────────
def composite_score(d: dict) -> Tuple[int, Dict[str, int], str]:
    total = 0; det = {}
    px = d.get("price", 0) or 0
    ma5 = d.get("ma5"); ma20 = d.get("ma20"); ma60 = d.get("ma60")
    rsi = d.get("rsi"); macd = d.get("macd"); macd_s = d.get("macd_signal")
    bb_u = d.get("bb_upper"); bb_l = d.get("bb_lower")
    pe = d.get("pe"); pb = d.get("pb"); roe = d.get("roe")
    dy = d.get("dividend_yield"); pm = d.get("profit_margin"); rg = d.get("revenue_growth")
    cr = d.get("current_ratio"); de = d.get("debt_to_equity"); vr = d.get("volume_ratio", 1.0)

    # 技術 35
    tech = 0
    if px and ma5 and ma20:
        tech += (10 if px > ma5 > ma20 else (6 if px > ma20 else 0))
        if ma60 and ma20 > ma60: tech += 2
    if rsi is not None:
        tech += (10 if 40 <= rsi <= 60 else (7 if 30 <= rsi < 40 else (5 if 60 < rsi <= 70 else (6 if rsi < 30 else 0))))
    if macd is not None and macd_s is not None:
        tech += (9 if macd > macd_s and macd > 0 else (4 if macd > macd_s else 0))
    if bb_u and bb_l and px:
        bw = bb_u - bb_l
        if bw > 0:
            pos = (px - bb_l) / bw
            tech += (6 if .2 <= pos <= .55 else (4 if pos < .2 else 0))
    det["技術"] = min(tech, 35); total += det["技術"]

    # 基本面 30
    fund = 0
    if pe: fund += (10 if 6 <= pe <= 14 else (7 if 14 < pe <= 20 else (4 if pe < 6 else 0)))
    if pb: fund += (7 if .5 <= pb <= 2 else (3 if 2 < pb <= 3 else 0))
    if roe:
        r = roe * 100
        fund += (9 if r >= 20 else (6 if r >= 12 else (3 if r >= 8 else 0)))
    if dy:
        y = dy * 100
        fund += (4 if y >= 5 else (2 if y >= 3 else 0))
    det["基本面"] = min(fund, 30); total += det["基本面"]

    # 動能 20
    mom = 0
    up = d.get("upside")
    if up is not None:
        mom += (10 if up >= 25 else (7 if up >= 15 else (5 if up >= 8 else (2 if up >= 3 else 0))))
    if rg:
        mom += (8 if rg >= .2 else (5 if rg >= .1 else (2 if rg >= 0 else 0)))
    det["動能"] = min(max(mom, 0), 20); total += det["動能"]

    # 財務健康 10
    fh = 0
    if cr: fh += (5 if cr >= 2 else (3 if cr >= 1.5 else (1 if cr >= 1 else 0)))
    if de is not None: fh += (5 if de <= .5 else (3 if de <= 1 else (1 if de <= 2 else 0)))
    det["財務健康"] = min(fh, 10); total += det["財務健康"]

    # 量能 5
    vp = 0
    if vr and 1.5 <= vr <= 4: vp += 3
    if pm and pm > .15: vp += 2
    det["量能"] = min(vp, 5); total += det["量能"]

    total = max(min(total, 100), 0)
    sig = "BUY" if total >= 70 else ("WATCH" if total >= 53 else ("HOLD" if total >= 36 else "AVOID"))
    return total, det, sig

def financial_health(d: dict) -> Tuple[str, int]:
    s = 0
    cr = d.get("current_ratio"); de = d.get("debt_to_equity")
    pm = d.get("profit_margin"); roe = d.get("roe"); rg = d.get("revenue_growth")
    if cr: s += (25 if cr >= 2 else (18 if cr >= 1.5 else (10 if cr >= 1 else 0)))
    if de is not None: s += (25 if de <= .5 else (18 if de <= 1 else (10 if de <= 2 else 0)))
    if pm: s += (20 if pm >= .2 else (14 if pm >= .1 else (8 if pm >= .05 else 0)))
    if roe: r = roe * 100; s += (15 if r >= 20 else (10 if r >= 12 else (5 if r >= 8 else 0)))
    if rg: s += (15 if rg >= .2 else (10 if rg >= .1 else (5 if rg >= 0 else 0)))
    grade = "A" if s >= 75 else ("B" if s >= 55 else ("C" if s >= 35 else "D"))
    return grade, s

# ─────────────────────────────────────────────────────────────────────────────
# FETCH STOCK
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=180, show_spinner=False)
def fetch_stock(code: str) -> dict:
    D = dict(
        code=code, name=code, suffix=".TW", error=None,
        price=None, prev_close=None, open=None, high=None, low=None,
        volume=None, avg_volume=None, market_cap=None,
        pe=None, pb=None, eps=None, roe=None,
        dividend_yield=None, profit_margin=None, revenue_growth=None,
        current_ratio=None, quick_ratio=None, debt_to_equity=None,
        target_price=None, target_low=None, target_high=None, upside=None,
        analyst_count=0, ma5=None, ma20=None, ma60=None, ma120=None,
        rsi=None, rsi6=None, macd=None, macd_signal=None,
        bb_upper=None, bb_lower=None, bb_mid=None, atr=None,
        beta=None, volume_ratio=1.0, volume_status="normal",
        pivot={}, backtest={}, sharpe=0.0, max_drawdown=0.0,
        hist=None, score=0, score_detail={}, signal="HOLD",
        industry="—", fin_health_grade="C", fin_health_score=0,
        foreign_net=None, trust_net=None, dealer_net=None,
    )
    try:
        sfx = resolve_suffix(code); D["suffix"] = sfx
        tk = yf.Ticker(code + sfx); info = tk.info
        raw_name = info.get("longName") or info.get("shortName") or ""
        # 優先用內建中文名
        D["name"] = _BUILTIN.get(code, raw_name.strip() or code)
        D["industry"] = _INDUSTRY.get(code, info.get("sector") or "—")

        # 價格
        D["price"] = info.get("currentPrice") or info.get("regularMarketPrice")
        D["prev_close"] = info.get("previousClose") or info.get("regularMarketPreviousClose")
        D["open"] = info.get("open") or info.get("regularMarketOpen")
        D["high"] = info.get("dayHigh") or info.get("regularMarketDayHigh")
        D["low"] = info.get("dayLow") or info.get("regularMarketDayLow")
        D["volume"] = info.get("volume") or info.get("regularMarketVolume")
        D["avg_volume"] = info.get("averageVolume")
        D["market_cap"] = info.get("marketCap")
        if not D["price"]:
            fi = tk.fast_info
            D["price"] = getattr(fi, "last_price", None)
            D["prev_close"] = getattr(fi, "previous_close", None)

        # 基本面
        D["pe"] = info.get("trailingPE") or info.get("forwardPE")
        D["pb"] = info.get("priceToBook")
        D["eps"] = info.get("trailingEps") or info.get("forwardEps")
        D["roe"] = info.get("returnOnEquity")
        D["dividend_yield"] = info.get("dividendYield")
        D["profit_margin"] = info.get("profitMargins")
        D["revenue_growth"] = info.get("revenueGrowth")
        D["analyst_count"] = info.get("numberOfAnalystOpinions") or 0
        D["current_ratio"] = info.get("currentRatio")
        D["quick_ratio"] = info.get("quickRatio")
        de_raw = info.get("debtToEquity")
        D["debt_to_equity"] = de_raw / 100 if de_raw else None
        D["beta"] = info.get("beta")

        # 歷史
        hist = tk.history(period="1y", auto_adjust=True)
        if hist is not None and not hist.empty and len(hist) >= 20:
            D["hist"] = hist; c = hist["Close"]
            D["ma5"] = float(c.rolling(5).mean().iloc[-1])
            D["ma20"] = float(c.rolling(20).mean().iloc[-1])
            if len(c) >= 60: D["ma60"] = float(c.rolling(60).mean().iloc[-1])
            if len(c) >= 120: D["ma120"] = float(c.rolling(120).mean().iloc[-1])
            D["rsi"] = float(calc_rsi(c, 14).iloc[-1])
            D["rsi6"] = float(calc_rsi(c, 6).iloc[-1])
            ml, sl = calc_macd(c)
            D["macd"] = float(ml.iloc[-1]); D["macd_signal"] = float(sl.iloc[-1])
            bu, bm, bl = calc_bb(c)
            D["bb_upper"] = float(bu.iloc[-1]); D["bb_mid"] = float(bm.iloc[-1]); D["bb_lower"] = float(bl.iloc[-1])
            if len(hist) >= 15:
                D["atr"] = float(calc_atr(hist["High"], hist["Low"], hist["Close"], 14).iloc[-1])
            if len(hist) >= 2:
                y = hist.iloc[-2]
                D["pivot"] = calc_pivot(float(y["High"]), float(y["Low"]), float(y["Close"]))
            if "Volume" in hist.columns and len(hist["Volume"]) >= 21:
                D["volume_ratio"], D["volume_status"] = vol_anomaly(hist["Volume"])
            ret = c.pct_change().dropna()
            D["sharpe"] = calc_sharpe(ret)
            D["max_drawdown"] = calc_max_dd(c)
            D["backtest"] = backtest_ma(hist)
            # 三大法人估算
            if len(hist) >= 5 and D["market_cap"]:
                recent = hist.tail(5)
                p_trend = (float(recent["Close"].iloc[-1]) - float(recent["Close"].iloc[0])) / float(recent["Close"].iloc[0])
                v_mult = float(recent["Volume"].mean()) / float(hist["Volume"].mean()) if float(hist["Volume"].mean()) > 0 else 1
                est = p_trend * v_mult * D["market_cap"] / 1e8
                D["foreign_net"] = round(est * .6, 1)
                D["trust_net"] = round(est * .25, 1)
                D["dealer_net"] = round(est * .15, 1)

        # 目標價
        tp, tl, th = estimate_target(
            D["price"], D["pe"], D["eps"], D["pb"], D["roe"], D["dividend_yield"],
            info.get("targetMeanPrice"), info.get("targetLowPrice"), info.get("targetHighPrice"),
            D["analyst_count"], D["rsi"], D["macd"], D["macd_signal"], D["revenue_growth"]
        )
        D["target_price"] = tp; D["target_low"] = tl; D["target_high"] = th
        if D["price"] and tp: D["upside"] = (tp - D["price"]) / D["price"] * 100

        # 評分
        D["score"], D["score_detail"], D["signal"] = composite_score(D)
        D["fin_health_grade"], D["fin_health_score"] = financial_health(D)
    except Exception as e:
        D["error"] = str(e)
    return D

# ─────────────────────────────────────────────────────────────────────────────
# BATCH SCAN
# ─────────────────────────────────────────────────────────────────────────────
def scan_batch(codes: List[str], min_score=55, min_upside=5.0, max_pe=60.0,
               signal_filter="全部", progress_cb=None, max_workers=16) -> List[dict]:
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(fetch_stock, c): c for c in codes}
        done = 0
        for fut in concurrent.futures.as_completed(futs):
            done += 1
            if progress_cb: progress_cb(done, len(codes), futs[fut])
            try:
                d = fut.result()
                if not d.get("price"): continue
                if d.get("score", 0) < min_score: continue
                up = d.get("upside")
                if up is not None and up < min_upside: continue
                pe = d.get("pe")
                if pe is not None and pe > max_pe: continue
                if signal_filter != "全部" and d.get("signal") != signal_filter: continue
                results.append(d)
            except: pass
    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results

# ─────────────────────────────────────────────────────────────────────────────
# WATCHLIST PRICES
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def fetch_wl_prices(codes_t: tuple) -> Dict[str, dict]:
    res = {}
    def _f(code):
        try:
            sfx = resolve_suffix(code); tk = yf.Ticker(code + sfx); fi = tk.fast_info
            px = getattr(fi, "last_price", None); pc = getattr(fi, "previous_close", None)
            if px and pc: res[code] = {"price": px, "chg": (px - pc) / pc * 100}
        except: pass
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(_f, codes_t))
    return res

# ─────────────────────────────────────────────────────────────────────────────
# ALERTS
# ─────────────────────────────────────────────────────────────────────────────
def check_alerts(d: dict) -> List[str]:
    code = d.get("code", ""); alerts = []
    px = d.get("price"); rsi = d.get("rsi"); ma20 = d.get("ma20")
    cfg = st.session_state.alert_cfg.get(code, {})
    if rsi and rsi > 76: alerts.append(f"{code} RSI={rsi:.0f} 超買警示")
    if rsi and rsi < 24: alerts.append(f"{code} RSI={rsi:.0f} 超賣警示")
    if px and ma20 and abs(px - ma20) / ma20 < .004: alerts.append(f"{code} 價格逼近MA20")
    if d.get("volume_status") == "extreme": alerts.append(f"{code} 爆量 {d.get('volume_ratio', 1):.1f}x 異常")
    if cfg.get("price_above") and px and px >= cfg["price_above"]:
        alerts.append(f"{code} 突破設定 {cfg['price_above']}")
    if cfg.get("price_below") and px and px <= cfg["price_below"]:
        alerts.append(f"{code} 跌破設定 {cfg['price_below']}")
    return alerts

# ─────────────────────────────────────────────────────────────────────────────
# NEWS
# ─────────────────────────────────────────────────────────────────────────────
_POS = ["上漲","漲停","創高","突破","強勢","獲利","配息","利多","成長","亮眼","超越","買進","新高","大漲","增加"]
_NEG = ["下跌","跌停","創低","破底","虧損","利空","衰退","低於","警示","賣出","停損","大跌","崩跌","減少"]

def sentiment(t: str) -> str:
    s = sum(1 for w in _POS if w in t) - sum(1 for w in _NEG if w in t)
    return "pos" if s > 0 else ("neg" if s < 0 else "neu")

@st.cache_data(ttl=600, show_spinner=False)
def fetch_news(code: str, name: str) -> List[dict]:
    news = []; hdr = {"User-Agent": "Mozilla/5.0"}
    for url, sel in [
        (f"https://tw.stock.yahoo.com/quote/{code}.TW/news", "h3 a"),
        (f"https://news.cnyes.com/news/cat/twstock?code={code}", "a[href*='/news/id/']"),
    ]:
        if news: break
        try:
            soup = BeautifulSoup(requests.get(url, headers=hdr, timeout=8, verify=False).text, "lxml")
            for a in soup.select(sel)[:12]:
                t = a.get_text(strip=True)
                if len(t) < 8: continue
                src = "Yahoo Finance" if "yahoo" in url else "鉅亨網"
                news.append({"t": t, "url": a.get("href", ""), "s": sentiment(t), "src": src})
        except: pass
    return news[:10]

# ─────────────────────────────────────────────────────────────────────────────
# PUSH
# ─────────────────────────────────────────────────────────────────────────────
def push_discord(url: str, results: List[dict]) -> bool:
    if not url or not results: return False
    try:
        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        fields = []
        for d in results[:10]:
            p, tp, up = d.get("price"), d.get("target_price"), d.get("upside")
            em = {"BUY": "🟢", "WATCH": "🟡", "HOLD": "⚪", "AVOID": "🔴"}.get(d.get("signal", ""), "⚪")
            nm = d.get("name", d.get("code", ""))
            v = f"`現價 {p:.1f}` → `目標 {tp:.1f}` (**{up:+.1f}%**)" if (p and tp and up is not None) else "—"
            fields.append({"name": f"{em} {d['code']} {nm} · {d.get('score', 0)}分 · 財健{d.get('fin_health_grade', '—')}", "value": v, "inline": False})
        r = requests.post(url, json={"embeds": [{"title": f"⚡ 台股狙擊手 v9 · {now}", "color": 0x00e87a, "fields": fields, "footer": {"text": "僅供參考，投資有風險"}}]}, timeout=8)
        return r.status_code in (200, 204)
    except: return False

def push_line(token: str, results: List[dict]) -> bool:
    if not token or not results: return False
    try:
        now = datetime.datetime.now().strftime("%m/%d %H:%M")
        msg = f"\n⚡ 台股狙擊手 v9 · {now}\n" + "─" * 22 + "\n"
        for d in results[:8]:
            em = {"BUY": "🟢", "WATCH": "🟡", "HOLD": "⚪", "AVOID": "🔴"}.get(d.get("signal", ""), "⚪")
            nm = d.get("name", d.get("code", ""))
            p = d.get("price"); tp = d.get("target_price"); up = d.get("upside")
            msg += f"{em} {d['code']} {nm} {d.get('score', 0)}分\n"
            if p and tp: msg += f"   現:{p:.1f} 目:{tp:.1f} ({up:+.1f}%)\n"
        msg += "─" * 22 + "\n僅供參考，投資有風險"
        r = requests.post("https://notify-api.line.me/api/notify",
                          headers={"Authorization": f"Bearer {token}"},
                          data={"message": msg}, timeout=8)
        return r.status_code == 200
    except: return False

def results_to_csv(results: List[dict]) -> bytes:
    rows = []
    for d in results:
        rows.append({
            "代號": d.get("code", ""), "名稱": d.get("name", ""), "產業": d.get("industry", ""),
            "信號": d.get("signal", ""), "評分": d.get("score", 0),
            "現價": d.get("price", ""), "目標價": d.get("target_price", ""),
            "上漲空間%": round(d.get("upside") or 0, 1),
            "PE": d.get("pe", ""), "PB": d.get("pb", ""),
            "ROE%": round((d.get("roe") or 0) * 100, 1),
            "殖利率%": round((d.get("dividend_yield") or 0) * 100, 1),
            "RSI": round(d.get("rsi") or 0, 1),
            "營收成長%": round((d.get("revenue_growth") or 0) * 100, 1),
            "財務健康": d.get("fin_health_grade", ""),
            "Beta": d.get("beta", ""), "最大回撤%": d.get("max_drawdown", ""),
            "夏普比率": d.get("sharpe", ""), "量能倍率": d.get("volume_ratio", ""),
            "掃描時間": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
    return pd.DataFrame(rows).to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

# ─────────────────────────────────────────────────────────────────────────────
# SCHEDULER
# ─────────────────────────────────────────────────────────────────────────────
def _job():
    p = st.session_state.get("scan_params", {})
    c = st.session_state.get("scan_codes", [])
    if not c: return
    res = scan_batch(c, **p)
    st.session_state.scan_results = res
    st.session_state.last_scan_time = datetime.datetime.now()
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    st.session_state.sched_log.insert(0, ("ok", f"[{ts}] 排程完成 — 命中 {len(res)} 檔"))
    all_alts = []
    for d in res:
        all_alts.extend(check_alerts(d))
    if all_alts:
        st.session_state.alerts = all_alts[-20:]
    wh = st.session_state.get("auto_webhook", "")
    if wh and res:
        ok = push_discord(wh, res)
        st.session_state.sched_log.insert(0, ("ok" if ok else "err", f"  Discord {'OK' if ok else 'FAIL'}"))
    lt = st.session_state.get("line_token", "")
    if lt and res:
        ok = push_line(lt, res)
        st.session_state.sched_log.insert(0, ("ok" if ok else "err", f"  LINE {'OK' if ok else 'FAIL'}"))
    st.session_state.sched_log = st.session_state.sched_log[:80]

def start_sched(mode, hour=9, minute=30, interval=30):
    try: st.session_state.scheduler.shutdown(wait=False)
    except: pass
    s = BackgroundScheduler(timezone="Asia/Taipei")
    if mode == "fixed": s.add_job(_job, CronTrigger(hour=hour, minute=minute, day_of_week="mon-fri"))
    else: s.add_job(_job, IntervalTrigger(minutes=interval))
    s.start(); st.session_state.scheduler = s; st.session_state.sched_running = True

def stop_sched():
    try: st.session_state.scheduler.shutdown(wait=False)
    except: pass
    st.session_state.scheduler = None; st.session_state.sched_running = False

# ─────────────────────────────────────────────────────────────────────────────
# CHART
# ─────────────────────────────────────────────────────────────────────────────
def make_chart(d: dict) -> Optional[go.Figure]:
    hist = d.get("hist")
    if hist is None or hist.empty or len(hist) < 5: return None
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        row_heights=[.5, .15, .2, .15], vertical_spacing=.016)
    c = hist["Close"]
    # Candles
    fig.add_trace(go.Candlestick(
        x=hist.index, open=hist["Open"], high=hist["High"], low=hist["Low"], close=c,
        name="K", increasing_line_color="#00e87a", decreasing_line_color="#ff2d55",
        increasing_fillcolor="rgba(0,232,122,.85)", decreasing_fillcolor="rgba(255,45,85,.85)"), 1, 1)
    # MAs
    for period, color, width in [(5, "#ffd60a", 1.2), (20, "#1e90ff", 1.6), (60, "#bf5af2", 1.2), (120, "#32d2f5", 1.0)]:
        ma = c.rolling(period).mean()
        fig.add_trace(go.Scatter(x=hist.index, y=ma, mode="lines",
                                 line=dict(color=color, width=width), name=f"MA{period}", opacity=.88), 1, 1)
    # BB
    bu, bm, bl = calc_bb(c)
    fig.add_trace(go.Scatter(x=hist.index, y=bu, mode="lines",
                             line=dict(color="rgba(255,255,255,.08)", width=.8, dash="dot"), showlegend=False), 1, 1)
    fig.add_trace(go.Scatter(x=hist.index, y=bl, mode="lines",
                             line=dict(color="rgba(255,255,255,.08)", width=.8, dash="dot"),
                             fill="tonexty", fillcolor="rgba(255,255,255,.018)", showlegend=False), 1, 1)
    # ATR channel
    atr_s = calc_atr(hist["High"], hist["Low"], hist["Close"], 14)
    fig.add_trace(go.Scatter(x=hist.index, y=bm + 1.5 * atr_s, mode="lines",
                             line=dict(color="rgba(255,136,0,.12)", width=.8), showlegend=False), 1, 1)
    fig.add_trace(go.Scatter(x=hist.index, y=bm - 1.5 * atr_s, mode="lines",
                             line=dict(color="rgba(255,136,0,.12)", width=.8),
                             fill="tonexty", fillcolor="rgba(255,136,0,.025)", showlegend=False), 1, 1)
    # Target / Pivot lines
    tp = d.get("target_price")
    if tp:
        fig.add_hline(y=tp, line_dash="dash", line_color="rgba(0,232,122,.55)", line_width=1.2,
                      annotation_text=f"⚡ 目標 {tp:.1f}",
                      annotation_font=dict(size=9, color="#00e87a"), row=1, col=1)
    pv = d.get("pivot", {})
    for key, col in [("R1", "rgba(255,45,85,.4)"), ("PP", "rgba(255,214,10,.5)"), ("S1", "rgba(0,232,122,.4)")]:
        if key in pv:
            fig.add_hline(y=pv[key], line_dash="dot", line_color=col, line_width=.9,
                          annotation_text=f"{key} {pv[key]:.1f}",
                          annotation_font=dict(size=8, color=col.replace(".4", "1").replace(".5", "1")), row=1, col=1)
    # Volume
    vcol = ["#00e87a" if cl >= op else "#ff2d55" for cl, op in zip(hist["Close"], hist["Open"])]
    fig.add_trace(go.Bar(x=hist.index, y=hist["Volume"], marker_color=vcol, marker_opacity=.6, name="量"), 2, 1)
    fig.add_trace(go.Scatter(x=hist.index, y=hist["Volume"].rolling(20).mean(), mode="lines",
                             line=dict(color="#ffd60a", width=1), showlegend=False), 2, 1)
    # MACD
    ml, sl = calc_macd(c); hm = ml - sl
    fig.add_trace(go.Scatter(x=hist.index, y=ml, mode="lines", line=dict(color="#1e90ff", width=1.5), name="MACD"), 3, 1)
    fig.add_trace(go.Scatter(x=hist.index, y=sl, mode="lines", line=dict(color="#ff8800", width=1.2), name="Signal"), 3, 1)
    fig.add_trace(go.Bar(x=hist.index, y=hm,
                         marker_color=["rgba(0,232,122,.5)" if v >= 0 else "rgba(255,45,85,.5)" for v in hm],
                         showlegend=False), 3, 1)
    # RSI
    rsi14 = calc_rsi(c, 14); rsi6 = calc_rsi(c, 6)
    fig.add_trace(go.Scatter(x=hist.index, y=rsi14, mode="lines",
                             line=dict(color="#bf5af2", width=1.5), name="RSI14"), 4, 1)
    fig.add_trace(go.Scatter(x=hist.index, y=rsi6, mode="lines",
                             line=dict(color="#32d2f5", width=1, dash="dot"), name="RSI6", opacity=.75), 4, 1)
    for lv, col in [(70, "rgba(255,45,85,.3)"), (50, "rgba(255,255,255,.1)"), (30, "rgba(0,232,122,.3)")]:
        fig.add_hline(y=lv, line_dash="dot", line_color=col, line_width=.8, row=4, col=1)

    BG = "#030810"
    fig.update_layout(
        paper_bgcolor=BG, plot_bgcolor=BG,
        font=dict(family="JetBrains Mono", size=9.5, color="#3e5f80"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=9),
                    orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1),
        margin=dict(l=52, r=14, t=4, b=4), height=570,
        xaxis_rangeslider_visible=False,
    )
    for i in range(1, 5):
        fig.update_yaxes(row=i, col=1, gridcolor="#0e1e36", zerolinecolor="#122040",
                         tickfont=dict(size=9), showgrid=True, tickprefix=" ")
    fig.update_xaxes(gridcolor="#0e1e36", showgrid=False, tickfont=dict(size=9))
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# FORMAT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fp(v, d=1): return f"{v:,.{d}f}" if v is not None else "—"
def fpc(v, m=100): return f"{v*m:.1f}%" if v is not None else "—"
def fbil(v): return "—" if v is None else (f"{v/1e12:.2f}兆" if v >= 1e12 else f"{v/1e8:.1f}億")
def shex(s): return "hi" if s >= 70 else ("md" if s >= 50 else "lo")

def sig_badge(sig: str) -> str:
    dot = {"BUY": "●", "WATCH": "◆", "HOLD": "○", "AVOID": "✕"}.get(sig, "○")
    return f'<span class="sig sig-{sig}">{dot} {sig}</span>'

def dcell(k, v, cls=""):
    return f'<div class="dcell"><div class="dcell-k">{k}</div><div class="dcell-v {cls}">{v}</div></div>'

# ─────────────────────────────────────────────────────────────────────────────
# LOAD NAMES
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("初始化系統..."):
    ALL = load_names()

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
now_s = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
sc_run = st.session_state.sched_running
lt = st.session_state.last_scan_time
res_count = len(st.session_state.scan_results)
wl_count = len(st.session_state.watchlist)
alert_count = len(st.session_state.alerts)

tape_codes = ["2330", "2317", "2454", "2412", "2882", "2886", "2603", "6669"]
tape_html = ""
for tc in tape_codes:
    nm = ALL.get(tc, tc)
    tape_html += (
        f'<span class="tape-item">'
        f'<span class="tape-code">{tc}</span>'
        f'<span style="color:var(--t3);margin:0 2px">·</span>'
        f'<span class="tape-p">{nm}</span>'
        f'</span>'
    )

sched_chip = '<span class="chip chip-sched-on">● 排程運行中</span>' if sc_run else '<span class="chip chip-sched-off">○ 排程待機</span>'
alert_chip = f'<span class="chip chip-alert">🔔 {alert_count} 警示</span>' if alert_count else ""

st.markdown(
    f'<div class="hdr">'
    f'<div class="hdr-inner">'
    f'<div class="hdr-bar"></div>'
    f'<div class="hdr-body">'
    f'<div class="hdr-icon">⚡</div>'
    f'<div class="hdr-text">'
    f'<div class="hdr-eyebrow">TAIWAN STOCK · AI ANALYSIS SYSTEM · REAL-TIME ENGINE</div>'
    f'<div class="hdr-title">台股 AI 狙擊手 ULTRA</div>'
    f'<div class="hdr-sub">TECHNICAL + FUNDAMENTAL + RISK + FINANCIAL HEALTH · 16-THREAD PARALLEL · PIVOT · BACKTEST · ALERTS</div>'
    f'<div class="hdr-chips">'
    f'<span class="chip chip-live"><span class="chip-dot"></span> LIVE</span>'
    f'<span class="chip chip-time">⏱ {now_s} CST</span>'
    f'<span class="chip chip-v9">✦ v9 ULTRA</span>'
    f'{sched_chip}{alert_chip}'
    f'</div>'
    f'</div>'
    f'</div>'
    f'<div class="hdr-stats">'
    f'<div class="hdr-stat"><div class="hdr-stat-n" style="color:var(--g)">{len(ALL)}</div><div class="hdr-stat-l">股票庫</div></div>'
    f'<div class="hdr-stat"><div class="hdr-stat-n" style="color:var(--b)">{res_count}</div><div class="hdr-stat-l">命中數</div></div>'
    f'<div class="hdr-stat"><div class="hdr-stat-n" style="color:var(--p)">{wl_count}</div><div class="hdr-stat-l">自選股</div></div>'
    f'<div class="hdr-stat"><div class="hdr-stat-n" style="color:var(--y)">{lt.strftime("%H:%M") if lt else "——"}</div><div class="hdr-stat-l">上次掃描</div></div>'
    f'</div>'
    f'</div>'
    f'<div class="hdr-tape">'
    f'<span style="color:var(--t3);margin-right:4px">WATCHLIST //</span>'
    f'{tape_html}'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True
)

# Alert banner
if st.session_state.alerts:
    items_html = "".join(f'<span style="color:var(--y)">⚠ {a}</span>' for a in st.session_state.alerts[:5])
    st.markdown(
        f'<div class="alert-bar">'
        f'<span style="font-size:.8rem">🔔</span>'
        f'<div class="alert-items">{items_html}</div>'
        f'<span style="font-family:var(--mono);font-size:.48rem;color:var(--t2)">共 {alert_count} 條</span>'
        f'</div>',
        unsafe_allow_html=True
    )
    if st.button("清除警示", key="clr_alerts"):
        st.session_state.alerts = []; st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    # 搜尋
    st.markdown('<div class="sb-hdr"><span class="sb-hdr-dot"></span>個股搜尋</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="sb-body">', unsafe_allow_html=True)
        q = st.text_input("搜尋", label_visibility="collapsed", placeholder="代號或中文名稱  例: 2330 / 台積電", key="sq")
        if q and q.strip():
            hits = search_stocks(q, ALL, 10)
            if hits:
                for code, name in hits:
                    ca, cb, cc = st.columns([3, 1, 1])
                    ca.markdown(
                        f'<div class="sh-row">'
                        f'<span class="sh-code">{code}</span>'
                        f'<span class="sh-name">{name}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    if cb.button("GO", key=f"go_{code}", use_container_width=True):
                        st.session_state.selected_stock = code
                        st.session_state.detail_cache = {}
                        st.rerun()
                    wl_in = code in st.session_state.watchlist
                    if cc.button("★" if wl_in else "☆", key=f"wl_{code}", use_container_width=True):
                        if wl_in: st.session_state.watchlist.remove(code)
                        else: st.session_state.watchlist.append(code)
                        st.rerun()
            else:
                st.markdown('<div style="font-family:var(--mono);font-size:.6rem;color:var(--t2);padding:4px 0">查無結果</div>', unsafe_allow_html=True)
        elif st.session_state.selected_stock:
            sc_ = st.session_state.selected_stock
            nm_ = ALL.get(sc_, sc_)
            st.markdown(
                f'<div style="font-family:var(--mono);font-size:.6rem;padding:4px 0">'
                f'分析中 <span style="color:var(--g);font-weight:700">{sc_} {nm_}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # 自選股
    st.markdown('<div class="sb-hdr"><span class="sb-hdr-dot"></span>自選股清單 ★</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="sb-body">', unsafe_allow_html=True)
        wl = st.session_state.watchlist
        if wl:
            wl_prices = fetch_wl_prices(tuple(wl))
            for code in wl[:15]:
                nm = ALL.get(code, code)
                info = wl_prices.get(code, {})
                px_ = info.get("price"); chg_ = info.get("chg")
                px_str = fp(px_, 1) if px_ else "—"
                chg_str = ""
                if chg_ is not None:
                    cls_ = "wl-up" if chg_ >= 0 else "wl-dn"
                    sym_ = "▲" if chg_ >= 0 else "▼"
                    chg_str = f'<span class="{cls_}">{sym_}{abs(chg_):.1f}%</span>'
                col1, col2 = st.columns([4, 1])
                col1.markdown(
                    f'<div class="wl-row">'
                    f'<span class="wl-code">{code}</span>'
                    f'<span class="wl-name">{nm[:6]}</span>'
                    f'<span class="wl-px">{px_str}</span>'
                    f'{chg_str}'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if col2.button("✕", key=f"rm_{code}", use_container_width=True):
                    st.session_state.watchlist.remove(code); st.rerun()
            st.text_area("匯出", value=",".join(wl), height=46, label_visibility="collapsed", key="wl_export")
        else:
            st.markdown('<div style="font-family:var(--mono);font-size:.58rem;color:var(--t2);padding:4px 0">尚無自選股 · 搜尋時按 ☆ 加入</div>', unsafe_allow_html=True)
        wl_imp = st.text_input("批量加入", placeholder="2330,2317...", key="wl_imp", label_visibility="collapsed")
        if wl_imp:
            for c_add in re.split(r"[,\n\s]+", wl_imp):
                c_add = c_add.strip()
                if len(c_add) == 4 and c_add.isdigit() and c_add not in st.session_state.watchlist:
                    st.session_state.watchlist.append(c_add)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 掃描設定
    st.markdown('<div class="sb-hdr"><span class="sb-hdr-dot"></span>批量掃描設定</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="sb-body">', unsafe_allow_html=True)
        scan_mode = st.radio("範圍", ["熱門100", "自選股", "全市場", "自訂"], label_visibility="collapsed")
        custom_codes = ""
        if scan_mode == "自訂":
            custom_codes = st.text_area("代號", placeholder="2330,2317...", height=56, label_visibility="collapsed")
        min_score = st.slider("最低評分", 0, 100, 55, 5, key="sl_score")
        min_upside = st.slider("最低上漲空間%", 1, 50, 8, 1, key="sl_up")
        max_pe = st.slider("最高 PE", 5, 150, 60, 5, key="sl_pe")
        sig_filter = st.selectbox("信號篩選", ["全部", "BUY", "WATCH", "HOLD", "AVOID"], label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    # 推播
    st.markdown('<div class="sb-hdr"><span class="sb-hdr-dot"></span>推播設定</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="sb-body">', unsafe_allow_html=True)
        webhook = st.text_input("Discord Webhook", placeholder="https://discord.com/api/webhooks/...", type="password", label_visibility="collapsed", key="wh_in")
        st.session_state.auto_webhook = webhook
        line_token = st.text_input("LINE Notify Token", placeholder="LINE Notify Token", type="password", label_visibility="collapsed", key="lt_in")
        st.session_state.line_token = line_token
        st.markdown('</div>', unsafe_allow_html=True)

    # 排程
    st.markdown('<div class="sb-hdr"><span class="sb-hdr-dot"></span>自動排程</div>', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="sb-body">', unsafe_allow_html=True)
        sched_mode = st.radio("排程模式", ["固定時間", "間隔"], horizontal=True, label_visibility="collapsed")
        if sched_mode == "固定時間":
            c1s, c2s = st.columns(2)
            sched_h = c1s.number_input("時", 0, 23, 9, label_visibility="collapsed")
            sched_m = c2s.number_input("分", 0, 59, 30, label_visibility="collapsed")
        else:
            sched_interval = st.slider("每隔(分)", 5, 180, 30, 5, key="sl_int")

        ca, cb = st.columns(2)
        with ca:
            if st.button("▶ 啟動", type="primary", use_container_width=True, key="sched_start"):
                if scan_mode == "熱門100": sc_codes = list(ALL.keys())[:100]
                elif scan_mode == "自選股": sc_codes = list(st.session_state.watchlist)
                elif scan_mode == "全市場": sc_codes = list(ALL.keys())
                else: sc_codes = [x.strip() for x in re.split(r"[,\n\s]+", custom_codes) if x.strip()]
                st.session_state.scan_codes = sc_codes
                st.session_state.scan_params = dict(min_score=min_score, min_upside=min_upside, max_pe=max_pe, signal_filter=sig_filter)
                if sched_mode == "固定時間": start_sched("fixed", hour=int(sched_h), minute=int(sched_m))
                else: start_sched("interval", interval=int(sched_interval))
                st.success("排程已啟動 ✓")
        with cb:
            if st.button("⏹ 停止", use_container_width=True, key="sched_stop"):
                stop_sched(); st.info("已停止")
        if sc_run:
            st.markdown(
                f'<div style="background:var(--bg2);border:1px solid var(--ln);border-radius:4px;'
                f'padding:8px 10px;margin-top:6px;font-family:var(--mono);font-size:.52rem">'
                f'<div style="display:flex;justify-content:space-between;padding:2px 0">'
                f'<span style="color:var(--t2)">狀態</span><span style="color:var(--g)">● RUNNING</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:2px 0">'
                f'<span style="color:var(--t2)">上次</span>'
                f'<span style="color:var(--b)">{lt.strftime("%H:%M:%S") if lt else "—"}</span></div>'
                f'<div style="display:flex;justify-content:space-between;padding:2px 0">'
                f'<span style="color:var(--t2)">標的</span>'
                f'<span style="color:var(--b)">{len(st.session_state.scan_codes)} 檔</span></div>'
                f'</div>',
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT — TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊  個股深度分析", "⚡  智能批量掃描", "🎯  多空儀表板", "📋  排程紀錄"])

# ═══════════════════════ TAB 1 ═══════════════════════
with tab1:
    sel = st.session_state.selected_stock
    if not sel:
        st.markdown(
            '<div class="empty"><div class="empty-ico">⚡</div>'
            '<div class="empty-txt">在左側搜尋欄輸入股票代號或名稱<br>'
            '支援上市、上櫃全部個股 · 自動偵測 .TW / .TWO<br>'
            '按 ☆ 加入自選股清單 · 支援中文搜尋</div></div>',
            unsafe_allow_html=True
        )
    else:
        cache = st.session_state.detail_cache
        if cache.get("code") != sel:
            with st.spinner(f"載入 {sel} {ALL.get(sel, '')} ..."):
                d = fetch_stock(sel)
            st.session_state.detail_cache = d
        else:
            d = cache

        if d.get("error") and not d.get("price"):
            st.error(f"無法取得 {sel} 資料 — {d['error']}")
        else:
            px = d.get("price"); prev = d.get("prev_close")
            chg = (px - prev) if (px and prev) else None
            chgp = chg / prev * 100 if (chg is not None and prev) else None
            score = d.get("score", 0); sig = d.get("signal", "HOLD")
            name = d.get("name", sel); suffix = d.get("suffix", "")
            tp = d.get("target_price"); tl_ = d.get("target_low"); th_ = d.get("target_high")
            up = d.get("upside"); mc = d.get("market_cap"); ind = d.get("industry", "—")
            fhg = d.get("fin_health_grade", "C"); fhs = d.get("fin_health_score", 0)
            beta = d.get("beta"); sharpe = d.get("sharpe"); mdd = d.get("max_drawdown")
            vol_r = d.get("volume_ratio", 1.0); vol_s = d.get("volume_status", "normal")
            chg_cls = "pos" if (chg and chg >= 0) else "neg"
            chg_sym = "▲" if (chg and chg >= 0) else "▼"

            # 操作列
            op1, op2, op3 = st.columns([2, 2, 6])
            wl_in = sel in st.session_state.watchlist
            if op1.button("★ 移出自選股" if wl_in else "☆ 加入自選股", use_container_width=True):
                if wl_in: st.session_state.watchlist.remove(sel)
                else: st.session_state.watchlist.append(sel)
                st.rerun()
            if op2.button("🔄 重新載入", use_container_width=True):
                fetch_stock.clear(); st.session_state.detail_cache = {}; st.rerun()

            # 警示
            alts_now = check_alerts(d)
            alt_html = "".join(
                f'<div style="font-family:var(--mono);font-size:.5rem;color:var(--y);margin-top:2px">⚠ {a}</div>'
                for a in alts_now[:3]
            )

            # vol badge
            if vol_s == "extreme":
                vol_badge = '<span class="vol-badge extreme">💥 爆量</span>'
            elif vol_s == "high":
                vol_badge = '<span class="vol-badge high">📈 放量</span>'
            else:
                vol_badge = ""

            fh_badge = f'<span class="fh-badge fh-{fhg}">財健 {fhg}</span>'

            # STOCK HEADER CARD
            st.markdown(
                f'<div class="scard">'
                f'<div class="scard-top">'
                f'<div class="scard-stripe"></div>'
                f'<div class="scard-id">'
                f'<div class="scard-code">{sel}<span class="scard-sfx">{suffix}</span></div>'
                f'<div class="scard-name">{name}</div>'
                f'<div class="scard-ind">{ind} · 市值 {fbil(mc)}</div>'
                f'<div class="scard-badges" style="margin-top:8px">'
                f'{sig_badge(sig)}{fh_badge}{vol_badge}'
                f'</div>'
                f'{alt_html}'
                f'</div>'
                f'<div class="scard-px">'
                f'<div class="scard-price">{fp(px)}<span class="scard-unit">TWD</span></div>'
                f'<div class="scard-chg {chg_cls}">'
                f'{chg_sym} {f"{abs(chg):.2f}" if chg else "—"}&nbsp;&nbsp;'
                f'({f"{chgp:+.2f}%" if chgp else "—"})'
                f'</div>'
                f'<div class="scard-ohlc">'
                f'<span>開 <span style="color:var(--t1)">{fp(d.get("open"))}</span></span>'
                f'<span>高 <span style="color:var(--g)">{fp(d.get("high"))}</span></span>'
                f'<span>低 <span style="color:var(--r)">{fp(d.get("low"))}</span></span>'
                f'<span>昨 <span style="color:var(--t1)">{fp(prev)}</span></span>'
                f'</div>'
                f'<div class="scard-risk">'
                f'<span>量能 <span style="color:{"var(--r)" if vol_s=="extreme" else ("var(--y)" if vol_s=="high" else "var(--t1)")}">{vol_r:.1f}x</span></span>'
                f'<span>Beta <span style="color:var(--t1)">{fp(beta, 2) if beta else "—"}</span></span>'
                f'<span>夏普 <span style="color:var(--t1)">{fp(sharpe, 2) if sharpe else "—"}</span></span>'
                f'<span>回撤 <span style="color:var(--r)">{f"{mdd:.1f}%" if mdd else "—"}</span></span>'
                f'</div>'
                f'</div>'
                f'<div class="scard-sig-block">'
                f'<div style="display:flex;align-items:center;gap:10px">'
                f'<div class="score-ring {shex(score)}">'
                f'<div class="score-n" style="color:{"var(--g)" if score>=70 else ("var(--y)" if score>=50 else "var(--r)")}">{score}</div>'
                f'<div class="score-l">評分</div>'
                f'</div>'
                f'<div>'
                f'<div style="font-family:var(--mono);font-size:.42rem;color:var(--t2);text-transform:uppercase;letter-spacing:.1em">綜合評分 /100</div>'
                f'<div style="font-family:var(--mono);font-size:.55rem;color:var(--t1);margin-top:3px">{"★"*int(score/20)}{"☆"*(5-int(score/20))}</div>'
                f'</div>'
                f'</div>'
                f'<div style="font-family:var(--mono);font-size:.52rem;color:var(--t2);margin-top:6px">'
                f'目標 <span style="color:var(--g);font-weight:700;font-size:.72rem">{fp(tp)}</span>'
                f'<span style="color:var(--g);margin-left:5px">{f"({up:+.1f}%)" if up is not None else ""}</span>'
                f'</div>'
                f'</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # ── 主佈局
            col_main, col_side = st.columns([5.5, 3])

            with col_main:
                pe = d.get("pe"); pb = d.get("pb"); roe = d.get("roe")
                dy = d.get("dividend_yield"); pm = d.get("profit_margin"); rg = d.get("revenue_growth")
                cr = d.get("current_ratio"); qr = d.get("quick_ratio"); de = d.get("debt_to_equity")
                rsi = d.get("rsi"); ma5v = d.get("ma5"); ma20v = d.get("ma20")
                ma60v = d.get("ma60"); ma120v = d.get("ma120")
                macd_v = d.get("macd"); macd_sv = d.get("macd_signal"); atr_v = d.get("atr")
                ac = d.get("analyst_count", 0)

                # 基本面 + 財務 12格
                cells12 = "".join([
                    dcell("本益比 PE", f"{pe:.1f}×" if pe else "—",
                          "warn" if (pe and pe > 20) else ("pos" if (pe and pe < 15) else "")),
                    dcell("淨值比 PB", f"{pb:.2f}×" if pb else "—"),
                    dcell("ROE", fpc(roe), "pos" if (roe and roe > .12) else ("neg" if (roe and roe < 0) else "")),
                    dcell("殖利率", fpc(dy), "pos" if (dy and dy > .04) else ""),
                    dcell("淨利率", fpc(pm), "pos" if (pm and pm > .1) else ""),
                    dcell("營收成長", fpc(rg), "pos" if (rg and rg > 0) else ("neg" if (rg and rg < -.05) else "")),
                    dcell("流動比率", f"{cr:.2f}" if cr else "—",
                          "pos" if (cr and cr >= 2) else ("warn" if (cr and cr >= 1) else "neg")),
                    dcell("速動比率", f"{qr:.2f}" if qr else "—",
                          "pos" if (qr and qr >= 1) else "warn"),
                    dcell("負債比", f"{de:.2f}" if de else "—",
                          "pos" if (de is not None and de < .5) else ("warn" if (de is not None and de < 1) else "neg")),
                    dcell("RSI 14", f"{rsi:.1f}" if rsi else "—",
                          "neg" if (rsi and rsi > 72) else ("warn" if (rsi and rsi > 60) else ("pos" if (rsi and rsi < 35) else "neu"))),
                    dcell("目標價", fp(tp), "pos"),
                    dcell("上漲空間", f"{up:+.1f}%" if up is not None else "—", "pos"),
                ])
                st.markdown(f'<div class="dgrid dgrid-6" style="margin:8px 0">{cells12}</div>', unsafe_allow_html=True)

                # 技術指標 8格
                macd_ok = bool(macd_v and macd_sv and macd_v > macd_sv)
                cells8 = "".join([
                    dcell("MACD", f"{macd_v:.3f}" if macd_v else "—"),
                    dcell("Signal", f"{macd_sv:.3f}" if macd_sv else "—"),
                    dcell("MACD差", f"{(macd_v-macd_sv):+.3f}" if (macd_v and macd_sv) else "—",
                          "pos" if macd_ok else "neg"),
                    dcell("ATR 14", f"{atr_v:.2f}" if atr_v else "—"),
                    dcell("MA5", fp(ma5v), "pos" if (px and ma5v and px > ma5v) else "neg"),
                    dcell("MA20", fp(ma20v), "pos" if (px and ma20v and px > ma20v) else "neg"),
                    dcell("MA60", fp(ma60v), "pos" if (px and ma60v and px > ma60v) else "neg"),
                    dcell("MA120", fp(ma120v), "pos" if (px and ma120v and px > ma120v) else "neg"),
                ])
                st.markdown(f'<div class="dgrid dgrid-8" style="margin:8px 0">{cells8}</div>', unsafe_allow_html=True)

                # 圖表
                fig = make_chart(d)
                if fig:
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.markdown('<div style="font-family:var(--mono);font-size:.65rem;color:var(--t2);text-align:center;padding:20px">歷史資料不足，無法繪製圖表</div>', unsafe_allow_html=True)

                # 三大法人
                fn = d.get("foreign_net"); tn = d.get("trust_net"); dn = d.get("dealer_net")
                if fn is not None:
                    max_abs = max(abs(fn or 0), abs(tn or 0), abs(dn or 0), 1)
                    def inst_row(name_str, val):
                        if val is None: return ""
                        pct = min(abs(val) / max_abs * 45, 45)
                        is_buy = val >= 0
                        bar_cls = "inst-bar-buy" if is_buy else "inst-bar-sell"
                        val_cls = "pos" if is_buy else "neg"
                        return (
                            f'<div class="inst-row">'
                            f'<div class="inst-name">{name_str}</div>'
                            f'<div class="inst-wrap"><div class="{bar_cls}" style="width:{pct}%"></div></div>'
                            f'<div class="inst-val {val_cls}">{val:+.1f}億</div>'
                            f'</div>'
                        )
                    st.markdown(
                        f'<div class="panel">'
                        f'<div class="panel-title">三大法人動向估算（近5日）</div>'
                        f'{inst_row("外資", fn)}'
                        f'{inst_row("投信", tn)}'
                        f'{inst_row("自營商", dn)}'
                        f'<div style="font-family:var(--mono);font-size:.42rem;color:var(--t2);margin-top:6px">※ 依近期價量關係推估，非官方數據，僅供參考</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                # 回測
                bt = d.get("backtest", {})
                if bt:
                    wr = bt.get("win_rate", 0); ar = bt.get("avg_ret", 0)
                    wr_cls = "pos" if wr >= 55 else ("warn" if wr >= 45 else "neg")
                    ar_cls = "pos" if ar > 0 else "neg"
                    st.markdown(
                        f'<div class="panel">'
                        f'<div class="panel-title">歷史信號回測（MA金叉策略 · 近一年）</div>'
                        f'<div class="bt-grid">'
                        f'<div class="bt-cell"><div class="bt-k">交易次數</div><div class="bt-v">{bt.get("trades", "—")}</div></div>'
                        f'<div class="bt-cell"><div class="bt-k">勝率</div><div class="bt-v {wr_cls}">{wr:.1f}%</div></div>'
                        f'<div class="bt-cell"><div class="bt-k">均報酬</div><div class="bt-v {ar_cls}">{ar:+.1f}%</div></div>'
                        f'<div class="bt-cell"><div class="bt-k">最大獲利</div><div class="bt-v pos">{bt.get("max_win", 0):+.1f}%</div></div>'
                        f'<div class="bt-cell"><div class="bt-k">最大虧損</div><div class="bt-v neg">{bt.get("max_loss", 0):+.1f}%</div></div>'
                        f'<div class="bt-cell"><div class="bt-k">最大回撤</div><div class="bt-v neg">{mdd:.1f}%</div></div>'
                        f'<div class="bt-cell"><div class="bt-k">夏普比率</div><div class="bt-v {"pos" if (sharpe and sharpe>1) else ""}">{fp(sharpe, 2) if sharpe else "—"}</div></div>'
                        f'<div class="bt-cell"><div class="bt-k">Beta</div><div class="bt-v">{fp(beta, 2) if beta else "—"}</div></div>'
                        f'</div>'
                        f'<div style="font-family:var(--mono);font-size:.42rem;color:var(--t2);margin-top:6px">※ 過去績效不代表未來，本策略僅供研究參考</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

            with col_side:
                # 目標價面板
                if px and tp and tl_ and th_:
                    lo_b = min(tl_, px) * .93; hi_b = max(th_, px) * 1.07
                    rng = hi_b - lo_b if hi_b > lo_b else 1
                    def pp(v): return max(0., min(100., (v - lo_b) / rng * 100))
                    p_px = pp(px); p_tp = pp(tp); p_tl = pp(tl_); p_th = pp(th_)
                    bw = p_th - p_tl
                    up_col = "var(--g)" if (up and up >= 0) else "var(--r)"

                    st.markdown(
                        f'<div class="tp-panel">'
                        f'<div class="panel-title">12 個月目標價估算</div>'
                        f'<div class="tp-row">'
                        f'<div class="tp-item"><div class="tp-lbl">目標低</div><div class="tp-val lo">{fp(tl_)}</div></div>'
                        f'<div class="tp-item"><div class="tp-lbl">現價</div><div class="tp-val cur">{fp(px)}</div></div>'
                        f'<div class="tp-item" style="text-align:center">'
                        f'<div class="tp-big {"pos" if (up and up>=0) else "neg"}">{f"{up:+.1f}%" if up is not None else "—"}</div>'
                        f'<div class="tp-lbl" style="margin-top:3px">預期報酬</div>'
                        f'</div>'
                        f'<div class="tp-item"><div class="tp-lbl">目標價</div><div class="tp-val tp">{fp(tp)}</div></div>'
                        f'<div class="tp-item" style="text-align:right"><div class="tp-lbl">目標高</div><div class="tp-val hi">{fp(th_)}</div></div>'
                        f'</div>'
                        f'<div class="tp-track">'
                        f'<div class="tp-zone" style="left:{p_tl:.1f}%;width:{bw:.1f}%"></div>'
                        f'<div class="tp-cur" style="left:{p_px:.1f}%">'
                        f'<div class="tp-lbl2" style="top:-16px;color:#fff;font-size:.42rem">現 {fp(px)}</div>'
                        f'</div>'
                        f'<div class="tp-tp" style="left:{p_tp:.1f}%;background:{up_col};box-shadow:0 0 8px {up_col}88">'
                        f'<div class="tp-lbl2" style="top:14px;color:{up_col};font-size:.42rem">目 {fp(tp)}</div>'
                        f'</div>'
                        f'</div>'
                        f'<div style="font-family:var(--mono);font-size:.44rem;color:var(--t2);line-height:1.7">'
                        f'基礎溢價 + 基本面溢價 + 技術溢價'
                        f'{"+ 分析師共識（" + str(ac) + "人）" if ac >= 3 else ""}<br>'
                        f'區間：{fp(tl_)} – {fp(th_)} · 分析師覆蓋 {ac} 人'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                # 評分明細
                det = d.get("score_detail", {})
                maxes = {"技術": 35, "基本面": 30, "動能": 20, "財務健康": 10, "量能": 5}
                bars_html = ""
                for k, mx in maxes.items():
                    v = det.get(k, 0)
                    pct = int(v / mx * 100)
                    fill_cls = "g" if pct >= 65 else ("y" if pct >= 35 else "r")
                    bars_html += (
                        f'<div class="sbar">'
                        f'<div class="sbar-k">{k}</div>'
                        f'<div class="sbar-track"><div class="sbar-fill {fill_cls}" style="width:{pct}%"></div></div>'
                        f'<div class="sbar-n">{v}/{mx}</div>'
                        f'</div>'
                    )
                st.markdown(
                    f'<div class="panel"><div class="panel-title">評分明細 · 5 維度</div>{bars_html}</div>',
                    unsafe_allow_html=True
                )

                # 財務健康
                fh_colors = {"A": "var(--g)", "B": "var(--b)", "C": "var(--y)", "D": "var(--r)"}
                fh_descs = {"A": "財務體質優良", "B": "財務狀況良好", "C": "一般，需留意", "D": "偏弱，高風險"}
                fhc = fh_colors.get(fhg, "var(--y)")
                fhd = fh_descs.get(fhg, "")
                st.markdown(
                    f'<div class="panel">'
                    f'<div class="panel-title">財務健康評級</div>'
                    f'<div class="fh-wrap">'
                    f'<div class="fh-ring {fhg}">'
                    f'<div class="fh-grade" style="color:{fhc}">{fhg}</div>'
                    f'<div class="fh-score">{fhs}分</div>'
                    f'</div>'
                    f'<div style="flex:1">'
                    f'<div style="font-family:var(--mono);font-size:.58rem;font-weight:700;color:{fhc};margin-bottom:6px">{fhd}</div>'
                    f'<div class="fh-details">'
                    f'<div class="fh-dc"><div class="fh-dk">流動比率</div>'
                    f'<div class="fh-dv" style="color:{"var(--g)" if (cr and cr>=2) else ("var(--y)" if (cr and cr>=1) else "var(--r)")}">{f"{cr:.2f}" if cr else "—"}</div></div>'
                    f'<div class="fh-dc"><div class="fh-dk">速動比率</div>'
                    f'<div class="fh-dv" style="color:{"var(--g)" if (qr and qr>=1) else "var(--y)"}">{f"{qr:.2f}" if qr else "—"}</div></div>'
                    f'<div class="fh-dc"><div class="fh-dk">負債比</div>'
                    f'<div class="fh-dv" style="color:{"var(--g)" if (de is not None and de<.5) else ("var(--y)" if (de is not None and de<1) else "var(--r)")}">{f"{de:.2f}" if de else "—"}</div></div>'
                    f'</div>'
                    f'</div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # 風險
                def risk_bar_html(v, lo, hi, col):
                    if v is None: return ""
                    pct = max(0, min(100, (v - lo) / (hi - lo) * 100))
                    return f'<div class="risk-bar"><div class="risk-bar-fill" style="width:{pct}%;background:{col}"></div></div>'

                beta_cls = "var(--g)" if (beta and beta < 1) else ("var(--y)" if (beta and beta < 1.5) else "var(--r)")
                sha_cls = "var(--g)" if (sharpe and sharpe > 1) else ("var(--y)" if (sharpe and sharpe > 0) else "var(--r)")
                st.markdown(
                    f'<div class="panel">'
                    f'<div class="panel-title">風險指標</div>'
                    f'<div class="risk-grid">'
                    f'<div class="risk-cell"><div class="risk-k">Beta 系統風險</div>'
                    f'<div class="risk-v" style="color:{beta_cls}">{f"{beta:.2f}" if beta else "—"}</div>'
                    f'{risk_bar_html(beta, 0, 2, "var(--b)") if beta else ""}</div>'
                    f'<div class="risk-cell"><div class="risk-k">夏普比率</div>'
                    f'<div class="risk-v" style="color:{sha_cls}">{f"{sharpe:.2f}" if sharpe else "—"}</div>'
                    f'{risk_bar_html(sharpe, -1, 3, "var(--g)") if sharpe else ""}</div>'
                    f'<div class="risk-cell"><div class="risk-k">最大回撤</div>'
                    f'<div class="risk-v" style="color:var(--r)">{f"{mdd:.1f}%" if mdd else "—"}</div>'
                    f'{risk_bar_html(abs(mdd) if mdd else 0, 0, 50, "var(--r)") if mdd else ""}</div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # Pivot Points
                pv = d.get("pivot", {})
                if pv and px:
                    above_pp = px > pv.get("PP", 0)
                    st.markdown(
                        f'<div class="panel">'
                        f'<div class="panel-title">Pivot Point 支撐壓力</div>'
                        f'<div class="pv-grid">'
                        f'<div class="pv-cell R"><div class="pv-k">R3</div><div class="pv-v">{fp(pv.get("R3"))}</div></div>'
                        f'<div class="pv-cell R"><div class="pv-k">R2</div><div class="pv-v">{fp(pv.get("R2"))}</div></div>'
                        f'<div class="pv-cell R"><div class="pv-k">R1</div><div class="pv-v">{fp(pv.get("R1"))}</div></div>'
                        f'<div class="pv-cell P" style="grid-column:span 3">'
                        f'<div class="pv-k">PP 樞紐</div><div class="pv-v">{fp(pv.get("PP"))}</div></div>'
                        f'<div class="pv-cell S"><div class="pv-k">S1</div><div class="pv-v">{fp(pv.get("S1"))}</div></div>'
                        f'<div class="pv-cell S"><div class="pv-k">S2</div><div class="pv-v">{fp(pv.get("S2"))}</div></div>'
                        f'<div class="pv-cell S"><div class="pv-k">S3</div><div class="pv-v">{fp(pv.get("S3"))}</div></div>'
                        f'</div>'
                        f'<div style="font-family:var(--mono);font-size:.44rem;color:var(--t2);margin-top:6px">'
                        f'現價 {fp(px)} · {"位於 PP 上方（壓力區）" if above_pp else "位於 PP 下方（支撐區）"}'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                # 信號解讀
                sig_map = {
                    "BUY": ("強勢買入", "技術多頭排列 + 基本面健康 + 估值合理，三重確認進場信號，建議分批建倉。"),
                    "WATCH": ("觀察等待", "指標逐步到位，尚缺突破確認。建議設定警示價位，等成交量配合再進場。"),
                    "HOLD": ("持有中立", "現階段趨勢不明，持倉者繼續持有，空手者暫緩介入。"),
                    "AVOID": ("暫時迴避", "多項指標偏弱或估值偏高，目前不具進場優勢，等待更好時機。"),
                }
                sig_info = sig_map.get(sig, ("中立", "—"))
                sig_col = {"BUY": "var(--g)", "WATCH": "var(--y)", "HOLD": "var(--t1)", "AVOID": "var(--r)"}.get(sig, "var(--t1)")
                st.markdown(
                    f'<div class="sig-card {sig}">'
                    f'<div class="sig-card-t" style="color:{sig_col}">{sig} · {sig_info[0]}</div>'
                    f'<div class="sig-card-b">{sig_info[1]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                # Checklist
                macd_ok2 = bool(macd_v and macd_sv and macd_v > macd_sv)
                checks = [
                    ("現價 > MA5",   bool(px and ma5v and px > ma5v)),
                    ("現價 > MA20",  bool(px and ma20v and px > ma20v)),
                    ("現價 > MA60",  bool(px and ma60v and px > ma60v)),
                    ("現價 > MA120", bool(px and ma120v and px > ma120v)),
                    ("MACD 金叉",    macd_ok2),
                    ("RSI 健康區",   bool(rsi and 30 <= rsi <= 70)),
                    ("PE 合理 ≤20",  bool(pe and pe <= 20)),
                    ("殖利率 >3%",   bool(dy and dy > .03)),
                    ("ROE >12%",     bool(roe and roe > .12)),
                    ("流動比 ≥1.5", bool(cr and cr >= 1.5)),
                    ("負債比 <1",    bool(de is not None and de < 1)),
                    ("目標上漲",     bool(up and up > 0)),
                    ("成長正向",     bool(rg and rg > 0)),
                    ("財務健康 A/B", fhg in ("A", "B")),
                ]
                ok_n = sum(1 for _, ok in checks if ok)
                chk_html = "".join(
                    f'<div class="chk {"ok" if ok else "no"}">'
                    f'<span class="chk-ic">{"✓" if ok else "✗"}</span>'
                    f'<span class="chk-txt">{lbl}</span>'
                    f'</div>'
                    for lbl, ok in checks
                )
                st.markdown(
                    f'<div class="panel">'
                    f'<div class="panel-title">條件核對 · {ok_n}/{len(checks)} 通過</div>'
                    f'{chk_html}'
                    f'</div>',
                    unsafe_allow_html=True
                )

            # 新聞
            with st.expander("📰  相關新聞 · 情緒分析", expanded=True):
                news = fetch_news(sel, name)
                if news:
                    pos_n = sum(1 for n in news if n.get("s") == "pos")
                    neg_n = sum(1 for n in news if n.get("s") == "neg")
                    sent_txt = "偏多 📈" if pos_n > neg_n else ("偏空 📉" if neg_n > pos_n else "中性 ➡")
                    sent_col = "var(--g)" if pos_n > neg_n else ("var(--r)" if neg_n > pos_n else "var(--t2)")
                    st.markdown(
                        f'<div style="font-family:var(--mono);font-size:.5rem;color:var(--t2);margin-bottom:6px">'
                        f'情緒 <span style="color:{sent_col};font-weight:700">{sent_txt}</span>'
                        f' · 正 {pos_n} · 負 {neg_n}</div>',
                        unsafe_allow_html=True
                    )
                    html = '<div class="news-wrap">'
                    for n in news:
                        s = n.get("s", "neu")
                        ic = {"pos": "↑", "neg": "↓", "neu": "·"}.get(s, "·")
                        html += (
                            f'<div class="news-item">'
                            f'<div class="news-ic {s}">{ic}</div>'
                            f'<div class="news-body">'
                            f'<div class="news-t">{n["t"]}</div>'
                            f'<div class="news-m">{n.get("src", "")}</div>'
                            f'</div>'
                            f'</div>'
                        )
                    html += '</div>'
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="font-family:var(--mono);font-size:.62rem;color:var(--t2);padding:10px 0">暫無新聞資料</div>', unsafe_allow_html=True)

            # 警示設定
            with st.expander("🔔  自訂警示設定", expanded=False):
                cfg = st.session_state.alert_cfg.get(sel, {})
                ac1, ac2 = st.columns(2)
                pa = ac1.number_input("突破價位 (0=停用)", min_value=0.0, value=float(cfg.get("price_above") or 0), step=1.0, key=f"pa_{sel}")
                pb_ = ac2.number_input("跌破價位 (0=停用)", min_value=0.0, value=float(cfg.get("price_below") or 0), step=1.0, key=f"pbb_{sel}")
                if st.button("儲存警示", key=f"save_alt_{sel}"):
                    st.session_state.alert_cfg[sel] = {
                        "price_above": pa if pa > 0 else None,
                        "price_below": pb_ if pb_ > 0 else None,
                    }
                    st.success(f"{sel} 警示已設定 ✓")

# ═══════════════════════ TAB 2 ═══════════════════════
with tab2:
    op1, op2, op3, op4 = st.columns([3, 1.2, 1.2, 1.2])
    with op1:
        if st.button("⚡  立即掃描", type="primary", use_container_width=True, key="scan_now"):
            if scan_mode == "熱門100": c2s = list(ALL.keys())[:100]
            elif scan_mode == "自選股": c2s = list(st.session_state.watchlist)
            elif scan_mode == "全市場": c2s = list(ALL.keys())
            else: c2s = [x.strip() for x in re.split(r"[,\n\s]+", custom_codes) if x.strip()]
            if not c2s:
                st.warning("請設定掃描範圍")
            else:
                ph = st.empty(); txh = st.empty()
                def _prog(done, total, code):
                    ph.progress(done / total)
                    nm_ = ALL.get(code, "")
                    txh.markdown(f'<div class="ll inf">⚡ [{done}/{total}] {code} {nm_}</div>', unsafe_allow_html=True)
                with st.spinner(""):
                    res_new = scan_batch(c2s, min_score=min_score, min_upside=min_upside,
                                         max_pe=max_pe, signal_filter=sig_filter,
                                         progress_cb=_prog, max_workers=16)
                ph.empty(); txh.empty()
                st.session_state.scan_results = res_new
                st.session_state.last_scan_time = datetime.datetime.now()
                all_alts = []
                for d_ in res_new:
                    all_alts.extend(check_alerts(d_))
                if all_alts: st.session_state.alerts = all_alts[-20:]
                st.success(f"✓ 完成 · {len(c2s)} 檔 · 命中 {len(res_new)} 檔 · 警示 {len(all_alts)} 條")
    with op2:
        if st.button("📤 Discord", use_container_width=True, key="push_dc"):
            if not st.session_state.scan_results: st.warning("無掃描結果")
            elif not webhook: st.warning("請填入 Webhook")
            else: st.success("✓") if push_discord(webhook, st.session_state.scan_results) else st.error("✗")
    with op3:
        if st.button("📱 LINE", use_container_width=True, key="push_ln"):
            if not st.session_state.scan_results: st.warning("無掃描結果")
            elif not line_token: st.warning("請填入 LINE Token")
            else: st.success("✓") if push_line(line_token, st.session_state.scan_results) else st.error("✗")
    with op4:
        res_now = st.session_state.scan_results
        if res_now:
            st.download_button(
                "📥 CSV", data=results_to_csv(res_now),
                file_name=f"scan_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv", use_container_width=True, key="dl_csv"
            )

    res = st.session_state.scan_results
    if res:
        buy_n = sum(1 for r in res if r.get("signal") == "BUY")
        wch_n = sum(1 for r in res if r.get("signal") == "WATCH")
        hld_n = sum(1 for r in res if r.get("signal") == "HOLD")
        avd_n = sum(1 for r in res if r.get("signal") == "AVOID")
        avg_sc = int(np.mean([r.get("score", 0) for r in res]))
        top_sc = max(r.get("score", 0) for r in res)
        ups = [r.get("upside") or 0 for r in res]
        avg_up = np.mean(ups); top_up = max(ups)
        fh_a = sum(1 for r in res if r.get("fin_health_grade") == "A")

        st.markdown(
            f'<div class="kpi-row">'
            f'<div class="kpi g"><div class="kpi-l">BUY</div><div class="kpi-v g">{buy_n}</div><div class="kpi-d">強買</div></div>'
            f'<div class="kpi y"><div class="kpi-l">WATCH</div><div class="kpi-v y">{wch_n}</div><div class="kpi-d">觀察</div></div>'
            f'<div class="kpi w"><div class="kpi-l">HOLD</div><div class="kpi-v">{hld_n}</div><div class="kpi-d">持有</div></div>'
            f'<div class="kpi r"><div class="kpi-l">AVOID</div><div class="kpi-v r">{avd_n}</div><div class="kpi-d">迴避</div></div>'
            f'<div class="kpi b"><div class="kpi-l">平均評分</div><div class="kpi-v b">{avg_sc}</div><div class="kpi-d">/100</div></div>'
            f'<div class="kpi p"><div class="kpi-l">平均上漲</div><div class="kpi-v p">{avg_up:+.1f}%</div><div class="kpi-d">預期</div></div>'
            f'<div class="kpi c"><div class="kpi-l">最大上漲</div><div class="kpi-v c">{top_up:+.1f}%</div><div class="kpi-d">單檔</div></div>'
            f'<div class="kpi g"><div class="kpi-l">財健A級</div><div class="kpi-v g">{fh_a}</div><div class="kpi-d">檔</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        rows_html = ""
        for r in res:
            cd = r.get("code", ""); nm = r.get("name", cd)
            pv_ = r.get("price"); tv_ = r.get("target_price"); uv_ = r.get("upside")
            sc_ = r.get("score", 0); sg_ = r.get("signal", "HOLD")
            pev_ = r.get("pe"); rov_ = r.get("roe"); dyv_ = r.get("dividend_yield")
            rsv_ = r.get("rsi"); rgv_ = r.get("revenue_growth")
            macdv_ = r.get("macd"); macdsv_ = r.get("macd_signal")
            ma20v_ = r.get("ma20"); fhg_ = r.get("fin_health_grade", "—")
            volr_ = r.get("volume_ratio", 1.0); vols_ = r.get("volume_status", "normal")
            macd_ok_ = bool(macdv_ and macdsv_ and macdv_ > macdsv_)
            ama_ = bool(pv_ and ma20v_ and pv_ > ma20v_)
            up_td = "c-up" if (uv_ and uv_ >= 0) else "c-dn"
            fhg_cls_ = {"A": "c-pos", "B": "c-neu", "C": "c-warn", "D": "c-neg"}.get(fhg_, "c-dim")
            vol_cls_ = "c-warn" if vols_ == "high" else ("c-neg" if vols_ == "extreme" else "c-dim")
            sc_ring_cls = "hi" if sc_ >= 70 else ("md" if sc_ >= 50 else "lo")
            sc_col = "var(--g)" if sc_ >= 70 else ("var(--y)" if sc_ >= 50 else "var(--r)")

            rows_html += (
                f'<tr class="{sg_}">'
                f'<td>'
                f'<div class="score-ring {sc_ring_cls}" style="width:30px;height:30px;border-width:1.5px">'
                f'<div class="score-n" style="font-size:.62rem;color:{sc_col}">{sc_}</div>'
                f'</div>'
                f'</td>'
                f'<td class="c-pri"><div>{cd}</div><div style="font-size:.5rem;color:var(--t2)">{nm[:8]}</div></td>'
                f'<td>{sig_badge(sg_)}</td>'
                f'<td class="c-pri">{fp(pv_)}</td>'
                f'<td class="c-tp">{fp(tv_)}</td>'
                f'<td class="{up_td}">{f"{uv_:+.1f}%" if uv_ is not None else "—"}</td>'
                f'<td class="c-dim">{f"{pev_:.1f}x" if pev_ else "—"}</td>'
                f'<td class="{"c-pos" if (rov_ and rov_>.12) else "c-dim"}">{fpc(rov_)}</td>'
                f'<td class="{"c-pos" if (dyv_ and dyv_>.04) else "c-dim"}">{fpc(dyv_)}</td>'
                f'<td class="{"c-neg" if (rsv_ and rsv_>70) else ("c-pos" if (rsv_ and rsv_<35) else "c-dim")}">{f"{rsv_:.0f}" if rsv_ else "—"}</td>'
                f'<td class="{"c-pos" if (rgv_ and rgv_>.1) else "c-dim"}">{fpc(rgv_)}</td>'
                f'<td class="{"c-pos" if macd_ok_ else "c-dim"}">{"金叉↑" if macd_ok_ else ("死叉↓" if (macdv_ and macdsv_ and macdv_<macdsv_) else "—")}</td>'
                f'<td class="{"c-pos" if ama_ else "c-neg"}">{"多頭" if ama_ else "空頭"}</td>'
                f'<td class="{fhg_cls_}">{fhg_}</td>'
                f'<td class="{vol_cls_}">{f"{volr_:.1f}x" if volr_ else "—"}</td>'
                f'</tr>'
            )

        st.markdown(
            f'<div class="rt-wrap"><table class="rt"><thead><tr>'
            f'<th>分</th><th>個股</th><th>信號</th>'
            f'<th>現價</th><th>目標</th><th>上漲</th>'
            f'<th>PE</th><th>ROE</th><th>殖利率</th>'
            f'<th>RSI</th><th>營收成長</th><th>MACD</th><th>MA20</th>'
            f'<th>財健</th><th>量能</th>'
            f'</tr></thead><tbody>{rows_html}</tbody></table></div>',
            unsafe_allow_html=True
        )

        # 快速跳轉
        st.markdown('<hr><div style="font-family:var(--mono);font-size:.46rem;color:var(--t2);text-transform:uppercase;letter-spacing:.15em;margin-bottom:6px">// 快速跳轉 TOP 10</div>', unsafe_allow_html=True)
        top10 = res[:10]
        if top10:
            jcols = st.columns(len(top10))
            for jcol, r in zip(jcols, top10):
                nm_short = r.get("name", r["code"])[:4]
                sc_ = r.get("score", 0)
                sc_col_ = "color:var(--g)" if sc_ >= 70 else ("color:var(--y)" if sc_ >= 50 else "color:var(--r)")
                with jcol:
                    if st.button(f"{r['code']}\n{nm_short}\n{sc_}分", use_container_width=True, key=f"jmp_{r['code']}"):
                        st.session_state.selected_stock = r["code"]
                        st.session_state.detail_cache = {}
                        st.rerun()
    else:
        st.markdown(
            '<div class="empty"><div class="empty-ico">🔍</div>'
            '<div class="empty-txt">點擊「立即掃描」開始篩選<br>'
            '16 線程並行引擎 · 速度快 5–10×<br>'
            '財務健康評級 · 風險評估 · 量能異常偵測<br>'
            'CSV 匯出 · LINE Notify · Discord 推播</div></div>',
            unsafe_allow_html=True
        )

# ═══════════════════════ TAB 3 — 多空儀表板 ═══════════════════════
with tab3:
    res_d = st.session_state.scan_results
    if not res_d:
        st.markdown(
            '<div class="empty"><div class="empty-ico">🎯</div>'
            '<div class="empty-txt">請先在「智能批量掃描」執行掃描<br>儀表板將顯示多空分析、評分分布與整體市場情緒</div></div>',
            unsafe_allow_html=True
        )
    else:
        buy_n_ = sum(1 for r in res_d if r.get("signal") == "BUY")
        wch_n_ = sum(1 for r in res_d if r.get("signal") == "WATCH")
        avd_n_ = sum(1 for r in res_d if r.get("signal") == "AVOID")
        total_ = len(res_d)
        bull_pct = int((buy_n_ + wch_n_ * .5) / total_ * 100) if total_ > 0 else 50
        bear_pct = 100 - bull_pct

        st.markdown(
            f'<div class="bb-panel">'
            f'<div class="panel-title">市場多空力道</div>'
            f'<div style="display:flex;justify-content:space-between;font-family:var(--mono);font-size:.5rem;color:var(--t2);margin-bottom:5px">'
            f'<span style="color:var(--g)">多方 {bull_pct}%  BUY {buy_n_} · WATCH {wch_n_}</span>'
            f'<span style="color:var(--r)">空方 {bear_pct}%  AVOID {avd_n_}</span>'
            f'</div>'
            f'<div class="bb-gauge"><div class="bb-fill" style="width:{bull_pct}%"></div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        ch1, ch2 = st.columns(2)
        with ch1:
            scores_ = [r.get("score", 0) for r in res_d]
            sigs_ = [r.get("signal", "HOLD") for r in res_d]
            cm = {"BUY": "#00e87a", "WATCH": "#ffd60a", "HOLD": "#8ab0cc", "AVOID": "#ff2d55"}
            colors_ = [cm.get(s, "#8ab0cc") for s in sigs_]
            codes_ = [r.get("code", "") for r in res_d]
            names_ = [r.get("name", r.get("code", ""))[:5] for r in res_d]
            fig_bar = go.Figure(go.Bar(
                x=[f"{c}<br>{n}" for c, n in zip(codes_, names_)],
                y=scores_, marker_color=colors_, marker_opacity=.85,
                text=[str(s) for s in scores_], textposition="outside",
                textfont=dict(family="JetBrains Mono", size=9, color="#3e5f80"),
            ))
            fig_bar.update_layout(
                paper_bgcolor="#030810", plot_bgcolor="#030810",
                font=dict(family="JetBrains Mono", size=9, color="#3e5f80"),
                margin=dict(l=20, r=10, t=30, b=60), height=280,
                title=dict(text="評分分布", font=dict(size=11, color="#8ab0cc"), x=0),
                xaxis=dict(tickfont=dict(size=7), tickangle=-45, gridcolor="#0e1e36"),
                yaxis=dict(range=[0, 112], gridcolor="#0e1e36", tickfont=dict(size=9)),
                showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

        with ch2:
            ups_ = [r.get("upside") or 0 for r in res_d]
            fig_sc = go.Figure(go.Scatter(
                x=scores_, y=ups_, mode="markers+text",
                text=codes_, textposition="top center",
                textfont=dict(family="JetBrains Mono", size=8, color="#3e5f80"),
                marker=dict(size=[max(7, min(18, s / 10)) for s in scores_],
                            color=colors_, opacity=.85,
                            line=dict(color="#030810", width=1)),
            ))
            fig_sc.add_hline(y=10, line_dash="dot", line_color="rgba(0,232,122,.25)", line_width=1)
            fig_sc.add_vline(x=70, line_dash="dot", line_color="rgba(0,232,122,.25)", line_width=1)
            fig_sc.update_layout(
                paper_bgcolor="#030810", plot_bgcolor="#030810",
                font=dict(family="JetBrains Mono", size=9, color="#3e5f80"),
                margin=dict(l=40, r=10, t=30, b=30), height=280,
                title=dict(text="評分 vs 上漲空間", font=dict(size=11, color="#8ab0cc"), x=0),
                xaxis=dict(title="評分", gridcolor="#0e1e36", tickfont=dict(size=9)),
                yaxis=dict(title="上漲空間%", gridcolor="#0e1e36", tickfont=dict(size=9)),
                showlegend=False,
            )
            st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

        # Top BUY / WATCH
        top_buy_ = [r for r in res_d if r.get("signal") == "BUY"][:8]
        top_wch_ = [r for r in res_d if r.get("signal") == "WATCH"][:8]
        cb1, cb2 = st.columns(2)

        def rank_card(r, border_color, text_color):
            up_ = r.get("upside") or 0
            nm_ = r.get("name", r.get("code", ""))
            sc_ = r.get("score", 0)
            sc_c = "var(--g)" if sc_ >= 70 else ("var(--y)" if sc_ >= 50 else "var(--r)")
            return (
                f'<div style="background:var(--bg1);border:1px solid {border_color};'
                f'border-left:3px solid {text_color};border-radius:5px;'
                f'padding:8px 12px;margin-bottom:5px;display:flex;justify-content:space-between;align-items:center">'
                f'<div>'
                f'<span style="font-family:var(--mono);font-size:.76rem;font-weight:700;color:var(--t0)">{r["code"]}</span>'
                f'<span style="font-size:.6rem;color:var(--t2);margin-left:7px">{nm_[:6]}</span>'
                f'</div>'
                f'<div style="text-align:right">'
                f'<div style="font-family:var(--mono);font-size:.7rem;color:var(--t0)">{fp(r.get("price"))}</div>'
                f'<div style="font-family:var(--mono);font-size:.58rem;color:{text_color}">{up_:+.1f}% → {fp(r.get("target_price"))}</div>'
                f'</div>'
                f'<div style="font-family:var(--mono);font-size:.68rem;font-weight:700;color:{sc_c};'
                f'background:var(--bg2);border:1px solid var(--ln2);border-radius:5px;'
                f'width:28px;height:28px;display:flex;align-items:center;justify-content:center;margin-left:8px">{sc_}</div>'
                f'</div>'
            )

        with cb1:
            st.markdown(f'<div style="font-family:var(--mono);font-size:.5rem;color:var(--g);text-transform:uppercase;letter-spacing:.15em;margin-bottom:7px">🟢 TOP BUY 強買</div>', unsafe_allow_html=True)
            for r in top_buy_:
                st.markdown(rank_card(r, "rgba(0,232,122,.2)", "var(--g)"), unsafe_allow_html=True)
        with cb2:
            st.markdown(f'<div style="font-family:var(--mono);font-size:.5rem;color:var(--y);text-transform:uppercase;letter-spacing:.15em;margin-bottom:7px">🟡 TOP WATCH 觀察</div>', unsafe_allow_html=True)
            for r in top_wch_:
                st.markdown(rank_card(r, "rgba(255,214,10,.2)", "var(--y)"), unsafe_allow_html=True)

        # 財務健康分布
        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<div style="font-family:var(--mono);font-size:.5rem;color:var(--t2);text-transform:uppercase;letter-spacing:.15em;margin-bottom:8px">// 財務健康分布</div>', unsafe_allow_html=True)
        fh_c = {"A": 0, "B": 0, "C": 0, "D": 0}
        for r in res_d:
            g_ = r.get("fin_health_grade", "C")
            if g_ in fh_c: fh_c[g_] += 1
        fh_cols = st.columns(4)
        fh_info = {"A": ("var(--g)", "優良"), "B": ("var(--b)", "良好"), "C": ("var(--y)", "一般"), "D": ("var(--r)", "偏弱")}
        for i, (grade, cnt) in enumerate(fh_c.items()):
            col_, desc_ = fh_info.get(grade, ("var(--t2)", "—"))
            fh_cols[i].markdown(
                f'<div style="background:var(--bg1);border:1px solid var(--ln2);border-radius:6px;padding:14px;text-align:center">'
                f'<div style="font-family:var(--mono);font-size:1.8rem;font-weight:700;color:{col_}">{grade}</div>'
                f'<div style="font-family:var(--mono);font-size:.46rem;color:var(--t2)">{desc_}</div>'
                f'<div style="font-family:var(--mono);font-size:1rem;font-weight:700;color:{col_};margin-top:5px">{cnt}</div>'
                f'<div style="font-family:var(--mono);font-size:.44rem;color:var(--t2)">檔</div>'
                f'</div>',
                unsafe_allow_html=True
            )

# ═══════════════════════ TAB 4 — 排程紀錄 ═══════════════════════
with tab4:
    cc1, cc2 = st.columns([5, 1])
    with cc1:
        st.markdown('<div style="font-family:var(--mono);font-size:.48rem;color:var(--t2);text-transform:uppercase;letter-spacing:.18em;margin-bottom:8px">// SCHEDULER LOG · v9</div>', unsafe_allow_html=True)
    with cc2:
        if st.button("CLR", use_container_width=True, key="clr_log"):
            st.session_state.sched_log = []; st.rerun()
    log = st.session_state.sched_log
    if log:
        log_html = '<div class="logbox">' + "".join(f'<div class="ll {t}">{m}</div>' for t, m in log) + '</div>'
        st.markdown(log_html, unsafe_allow_html=True)
    else:
        st.markdown('<div style="font-family:var(--mono);font-size:.62rem;color:var(--t2);padding:20px 0">尚無排程紀錄 · 啟動排程後此處顯示執行紀錄</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# AUTO REFRESH
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.sched_running:
    time.sleep(1); st.rerun()
