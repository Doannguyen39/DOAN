import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time
import os

st.set_page_config(page_title="💎 Gem Hunter", page_icon="💎", layout="wide", initial_sidebar_state="collapsed")

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
CG_KEY = os.environ.get("COINGECKO_API_KEY", "")
CG_HEADERS = {"x-cg-demo-api-key": CG_KEY} if CG_KEY else {}
CMC_KEY = os.environ.get("CMC_API_KEY", "")
CMC_HEADERS = {"X-CMC_PRO_API_KEY": CMC_KEY, "Accept": "application/json"}
CMC_BASE = "https://pro-api.coinmarketcap.com/v1"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif;}
.stApp{background:#0d1117;color:#e6edf3;}
#MainMenu,footer,header{visibility:hidden;}
.main-header{background:linear-gradient(135deg,#1a1f2e,#0d1117);border:1px solid #21262d;border-radius:16px;padding:28px;margin-bottom:20px;text-align:center;}
.main-title{font-size:2.2rem;font-weight:700;background:linear-gradient(135deg,#58a6ff,#a371f7,#f78166);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;}
.card{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:18px;text-align:center;}
.flag-green{background:#0d2818;border-left:3px solid #3fb950;color:#7ee787;padding:10px 14px;border-radius:8px;margin-bottom:8px;font-size:0.88rem;}
.flag-red{background:#2d1212;border-left:3px solid #f85149;color:#ff7b72;padding:10px 14px;border-radius:8px;margin-bottom:8px;font-size:0.88rem;}
.flag-yellow{background:#2d2208;border-left:3px solid #d29922;color:#e3b341;padding:10px 14px;border-radius:8px;margin-bottom:8px;font-size:0.88rem;}
.sec{font-size:0.85rem;font-weight:600;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px;padding-bottom:6px;border-bottom:1px solid #21262d;}
.token-hdr{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:20px;margin-bottom:16px;}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.72rem;font-weight:600;}
.badge-blue{background:#0d2137;color:#58a6ff;}
.badge-purple{background:#1e1037;color:#a371f7;}
.badge-green{background:#0d2818;color:#3fb950;}
.badge-red{background:#2d1212;color:#f85149;}
.badge-yellow{background:#2d2208;color:#e3b341;}
.badge-mexc{background:#1a2433;color:#58a6ff;}
.badge-bitmart{background:#2a1e37;color:#a371f7;}
.gem-row{background:#161b22;border:1px solid #21262d;border-radius:8px;padding:12px 16px;margin-bottom:6px;}
.gem-row:hover{border-color:#58a6ff;}
.warning{background:#2d1a00;border:1px solid #d29922;border-radius:10px;padding:12px 16px;font-size:0.82rem;color:#e3b341;margin-top:12px;}
.stTextInput input{background:#161b22!important;border:1px solid #30363d!important;border-radius:10px!important;color:#e6edf3!important;font-size:1rem!important;padding:12px 16px!important;}
.stTextInput input:focus{border-color:#58a6ff!important;}
.stButton button{background:linear-gradient(135deg,#1f6feb,#388bfd)!important;color:white!important;border:none!important;border-radius:10px!important;font-weight:600!important;width:100%;}
</style>
""", unsafe_allow_html=True)

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def fmt_usd(v):
    if not v: return "N/A"
    if v>=1e9: return f"${v/1e9:.2f}B"
    if v>=1e6: return f"${v/1e6:.2f}M"
    if v>=1e3: return f"${v/1e3:.1f}K"
    return f"${v:.4f}"

def fmt_price(v):
    if not v: return "N/A"
    if v>=1: return f"${v:,.4f}"
    if v>=0.001: return f"${v:.6f}"
    return f"${v:.8f}"

def pct_color(v): return "#3fb950" if (v or 0)>=0 else "#f85149"
def pct_str(v): return "N/A" if v is None else f"{'+'if v>=0 else''}{v:.2f}%"

# ─── CG API ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def search_token(q):
    try:
        r = requests.get(f"{COINGECKO_BASE}/search", params={"query":q}, headers=CG_HEADERS, timeout=10)
        if r.status_code==200: return r.json().get("coins",[])
    except: pass
    return []

@st.cache_data(ttl=60)
def get_token_data(cid):
    try:
        r = requests.get(f"{COINGECKO_BASE}/coins/{cid}",
            params={"localization":"false","tickers":"true","market_data":"true","community_data":"true","developer_data":"false"},
            headers=CG_HEADERS, timeout=15)
        if r.status_code==200: return r.json()
        if r.status_code==429: return {"error":"rate_limit"}
    except Exception as e: return {"error":str(e)}
    return None

@st.cache_data(ttl=300)
def get_trending():
    try:
        r = requests.get(f"{COINGECKO_BASE}/search/trending", headers=CG_HEADERS, timeout=10)
        if r.status_code==200: return r.json().get("coins",[])
    except: pass
    return []

@st.cache_data(ttl=120)
def get_microcap():
    try:
        r = requests.get(f"{COINGECKO_BASE}/coins/markets",
            params={"vs_currency":"usd","order":"volume_desc","per_page":250,"page":1,"sparkline":"false","price_change_percentage":"24h"},
            headers=CG_HEADERS, timeout=15)
        if r.status_code==200:
            return [c for c in r.json() if c.get("market_cap") and 100_000<c["market_cap"]<5_000_000 and c.get("total_volume",0)>10_000][:20]
    except: pass
    return []

# ─── CMC API ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def get_top_gainers_cmc():
    if not CMC_KEY: return None, "no_key"
    try:
        r = requests.get(f"{CMC_BASE}/cryptocurrency/listings/latest",
            headers=CMC_HEADERS,
            params={"limit":200,"sort":"percent_change_7d","sort_dir":"desc","market_cap_max":10_000_000,"convert":"USD"},
            timeout=15)
        if r.status_code==200:
            gainers=[]
            for c in r.json().get("data",[]):
                q=c.get("quote",{}).get("USD",{})
                change=q.get("percent_change_7d",0) or 0
                mcap=q.get("market_cap",0) or 0
                vol=q.get("volume_24h",0) or 0
                if change>=30 and 100_000<mcap<5_000_000 and vol>10_000:
                    gainers.append({
                        "name":c.get("name"),"symbol":c.get("symbol"),
                        "tags":c.get("tags",[]),
                        "price":q.get("price",0),"change_24h":q.get("percent_change_24h",0),
                        "change_7d":change,"market_cap":mcap,"volume":vol,
                    })
            return sorted(gainers,key=lambda x:x["change_7d"],reverse=True)[:30], None
        return None, f"API error {r.status_code}"
    except Exception as e: return None, str(e)

@st.cache_data(ttl=1800)
def get_gems_by_tags(search_tags):
    if not CMC_KEY: return []
    try:
        r = requests.get(f"{CMC_BASE}/cryptocurrency/listings/latest",
            headers=CMC_HEADERS,
            params={"limit":500,"sort":"volume_24h","sort_dir":"desc","market_cap_max":1_000_000,"convert":"USD"},
            timeout=15)
        if r.status_code==200:
            gems=[]
            for c in r.json().get("data",[]):
                q=c.get("quote",{}).get("USD",{})
                change_7d=q.get("percent_change_7d",0) or 0
                change_24h=q.get("percent_change_24h",0) or 0
                mcap=q.get("market_cap",0) or 0
                vol=q.get("volume_24h",0) or 0
                if change_7d>80 or change_24h>50: continue
                if mcap<50_000 or vol<5_000: continue
                tags=[t.lower() for t in c.get("tags",[])]
                if any(st_ in " ".join(tags) for st_ in search_tags):
                    gems.append({
                        "name":c.get("name"),"symbol":c.get("symbol"),
                        "tags":c.get("tags",[])[:3],
                        "price":q.get("price",0),"change_24h":change_24h,
                        "change_7d":change_7d,"market_cap":mcap,"volume":vol,
                        "vol_mcap":vol/mcap if mcap>0 else 0,
                    })
            return sorted(gems,key=lambda x:x["vol_mcap"],reverse=True)[:20]
    except: pass
    return []

# ═══════════════════════════════════════════════════════════════════════════════
# RANGE BOT SCANNER — DATA SOURCE: MEXC + BITMART
# ═══════════════════════════════════════════════════════════════════════════════
MEXC_BASE    = "https://api.mexc.com/api/v3"
BITMART_BASE = "https://api-cloud.bitmart.com"

SKIP_COINS = {"USDC","BUSD","USDD","TUSD","FDUSD","DAI","WBTC","WETH","STETH"}

# ─── MEXC ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_mexc_usdt_pairs():
    """Spot pairs USDT trên MEXC. Symbol dạng 'BTCUSDT'."""
    try:
        r = requests.get(f"{MEXC_BASE}/exchangeInfo", timeout=15)
        if r.status_code == 200:
            symbols = r.json().get("symbols", [])
            return [s["symbol"] for s in symbols
                    if s.get("quoteAsset") == "USDT"
                    and s.get("status") == "1"
                    and s.get("isSpotTradingAllowed", True)]
    except:
        pass
    return []

@st.cache_data(ttl=60)
def get_mexc_klines(symbol, interval="60m", limit=72):
    """Nến MEXC. interval dạng '60m' (H1), '15m' (M15). Data: cũ→mới."""
    try:
        r = requests.get(f"{MEXC_BASE}/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=8)
        if r.status_code == 200:
            data = r.json()
            if not data or len(data) < 20:
                return None
            highs   = [float(c[2]) for c in data]
            lows    = [float(c[3]) for c in data]
            closes  = [float(c[4]) for c in data]
            volumes = [float(c[5]) for c in data]
            return {"highs": highs, "lows": lows, "closes": closes, "volumes": volumes}
    except:
        pass
    return None

# ─── BITMART ──────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_bitmart_usdt_pairs():
    """Spot pairs USDT trên BitMart. Symbol dạng 'BTC_USDT'."""
    try:
        r = requests.get(f"{BITMART_BASE}/spot/v1/symbols", timeout=15)
        if r.status_code == 200:
            j = r.json()
            if j.get("code") != 1000:
                return []
            syms = j.get("data", {}).get("symbols", [])
            return [s for s in syms if s.endswith("_USDT")]
    except:
        pass
    return []

@st.cache_data(ttl=60)
def get_bitmart_klines(symbol, step=60, limit=72):
    """
    Nến BitMart spot v3. step = PHÚT (60=H1, 15=M15, 5=M5).
    Response [t,o,h,l,c,v,qv]. BitMart trả ĐẢO (mới→cũ) → sort lại cũ→mới.
    """
    try:
        now = int(time.time())
        params = {
            "symbol": symbol,
            "step": step,
            "after": now - (limit + 1) * step * 60,
            "before": now,
        }
        r = requests.get(f"{BITMART_BASE}/spot/quotation/v3/klines",
                         params=params, timeout=8)
        if r.status_code == 200:
            j = r.json()
            if j.get("code") != 1000:
                return None
            data = j.get("data", [])
            if not data or len(data) < 20:
                return None
            data = sorted(data, key=lambda c: float(c[0]))  # cũ → mới
            highs   = [float(c[2]) for c in data]
            lows    = [float(c[3]) for c in data]
            closes  = [float(c[4]) for c in data]
            volumes = [float(c[5]) for c in data]
            return {"highs": highs, "lows": lows, "closes": closes, "volumes": volumes}
    except:
        pass
    return None

# ─── ANALYZE RANGE BOT v2 (siết logic, loại false positive) ─────────────────────
def analyze_range_bot(kdata, min_osc=4):
    highs   = kdata["highs"]
    lows    = kdata["lows"]
    closes  = kdata["closes"]
    volumes = kdata["volumes"]
    n = len(closes)
    if n < 20:
        return None

    h_max = max(highs)
    l_min = min(lows)
    if l_min <= 0:
        return None
    span = h_max - l_min
    if span <= 0:
        return None

    # 1. Range hẹp (< 25%)
    range_pct = span / l_min * 100
    if range_pct > 25:
        return None

    # 2. TREND FILTER — loại token đang trend (range bot phải đi ngang)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(closes) / n
    cov   = sum((xs[i] - mean_x) * (closes[i] - mean_y) for i in range(n))
    var_x = sum((xs[i] - mean_x) ** 2 for i in range(n))
    slope = cov / var_x if var_x > 0 else 0
    trend_move  = abs(slope) * (n - 1)
    trend_ratio = trend_move / span
    if trend_ratio > 0.4:
        return None

    # 3. OSCILLATION đúng nghĩa — chạm xen kẽ 2 biên
    upper_zone = l_min + span * 0.75
    lower_zone = l_min + span * 0.25
    touches = []
    for i in range(n):
        if highs[i] >= upper_zone:
            if not touches or touches[-1] != 1:
                touches.append(1)
        elif lows[i] <= lower_zone:
            if not touches or touches[-1] != -1:
                touches.append(-1)
    real_osc = len(touches) - 1 if len(touches) > 1 else 0
    if real_osc < min_osc:
        return None

    # 4. VOLUME đều (CV < 0.7)
    vol_mean = sum(volumes) / n if volumes else 0
    if vol_mean == 0:
        return None
    vol_std = (sum((v - vol_mean) ** 2 for v in volumes) / n) ** 0.5
    vol_cv  = vol_std / vol_mean
    if vol_cv > 0.7:
        return None

    # 5. NẾN đều (candle CV < 0.9)
    candle_ranges = [(highs[i] - lows[i]) / lows[i] * 100 for i in range(n) if lows[i] > 0]
    avg_candle = sum(candle_ranges) / len(candle_ranges) if candle_ranges else 0
    candle_std = (sum((c - avg_candle) ** 2 for c in candle_ranges) / len(candle_ranges)) ** 0.5 if candle_ranges else 999
    candle_cv  = candle_std / avg_candle if avg_candle > 0 else 999
    if candle_cv > 0.9:
        return None

    # SCORE
    score = 0
    score += max(0, 30 - range_pct * 1.2)
    score += min(20, real_osc * 2)
    score += max(0, 20 - vol_cv * 25)
    score += max(0, 15 - candle_cv * 12)
    score += max(0, 15 - trend_ratio * 30)

    current_price = closes[-1]
    pos_in_range  = (current_price - l_min) / span * 100

    if pos_in_range <= 30:
        signal, signal_color = "🟢 BUY ZONE", "#3fb950"
    elif pos_in_range >= 70:
        signal, signal_color = "🔴 SELL ZONE", "#f85149"
    else:
        signal, signal_color = "⚪ MID RANGE", "#8b949e"

    return {
        "range_pct": range_pct,
        "range_high": h_max,
        "range_low": l_min,
        "midpoint": (h_max + l_min) / 2,
        "current_price": current_price,
        "pos_in_range": pos_in_range,
        "oscillations": real_osc,
        "vol_cv": vol_cv,
        "candle_cv": candle_cv,
        "trend_ratio": trend_ratio,
        "score": round(score, 1),
        "signal": signal,
        "signal_color": signal_color,
    }

# ─── SCAN MULTI-SÀN (MEXC + BITMART) ────────────────────────────────────────────
@st.cache_data(ttl=300)
def scan_range_bots(max_scan=300, tf_minutes=60, scan_mexc=True, scan_bitmart=True):
    """Quét range bot trên MEXC + BitMart, gộp kết quả. tf_minutes: 60=H1, 15=M15, 5=M5."""
    results = []
    any_pairs = False

    # MEXC interval string theo phút
    mexc_interval = f"{tf_minutes}m" if tf_minutes < 60 else "60m" if tf_minutes == 60 else "4h"

    # ---- MEXC ----
    if scan_mexc:
        pairs = get_mexc_usdt_pairs()
        if pairs:
            any_pairs = True
            pairs = [p for p in pairs if not any(s in p for s in SKIP_COINS)][:max_scan]
            errors = 0
            for symbol in pairs:
                try:
                    kdata = get_mexc_klines(symbol, interval=mexc_interval)
                    if not kdata:
                        continue
                    res = analyze_range_bot(kdata)
                    if res:
                        res["symbol"]   = symbol
                        res["exchange"] = "MEXC"
                        results.append(res)
                    time.sleep(0.05)
                except:
                    errors += 1
                    if errors > 30:
                        break

    # ---- BITMART ----
    if scan_bitmart:
        pairs = get_bitmart_usdt_pairs()
        if pairs:
            any_pairs = True
            pairs = [p for p in pairs if not any(s in p for s in SKIP_COINS)][:max_scan]
            errors = 0
            for symbol in pairs:
                try:
                    kdata = get_bitmart_klines(symbol, step=tf_minutes)
                    if not kdata:
                        continue
                    res = analyze_range_bot(kdata)
                    if res:
                        res["symbol"]   = symbol
                        res["exchange"] = "BitMart"
                        results.append(res)
                    time.sleep(0.3)  # BitMart rate limit thấp
                except:
                    errors += 1
                    if errors > 30:
                        break

    if not any_pairs:
        return [], "Không lấy được danh sách pairs từ sàn nào (kiểm tra mạng/API)."

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:80], None

def analyze_narrative(gainers):
    nmap={"artificial-intelligence":"🤖 AI / Agent","ai":"🤖 AI / Agent","agent":"🤖 AI / Agent",
          "real-world-assets":"🏦 RWA","rwa":"🏦 RWA",
          "depin":"📡 DePIN","decentralized-physical":"📡 DePIN",
          "gaming":"🎮 GameFi","play-to-earn":"🎮 GameFi",
          "defi":"💰 DeFi","decentralized-finance":"💰 DeFi",
          "memes":"🐸 Meme","sports":"⚽ Sports","nft":"🖼️ NFT",
          "layer-2":"⚡ Layer 2","metaverse":"🌐 Metaverse"}
    counts,tokens={},{}
    for t in gainers:
        matched=set()
        for tag in t.get("tags",[]):
            tl=tag.lower().replace(" ","-")
            for k,n in nmap.items():
                if k in tl and n not in matched:
                    matched.add(n)
                    counts[n]=counts.get(n,0)+1
                    tokens.setdefault(n,[]).append(t)
        if not matched:
            counts["🔮 Other"]=counts.get("🔮 Other",0)+1
            tokens.setdefault("🔮 Other",[]).append(t)
    return dict(sorted(counts.items(),key=lambda x:x[1],reverse=True)), tokens

# ─── SCORING ──────────────────────────────────────────────────────────────────
def score_token(data):
    score=0; fg,fr,fy=[],[],[]
    bd={}
    md=data.get("market_data",{})
    mcap=md.get("market_cap",{}).get("usd") or 0
    fdv=md.get("fully_diluted_valuation",{}).get("usd") or 0
    circ=md.get("circulating_supply") or 0
    maxs=md.get("max_supply") or md.get("total_supply") or circ
    vol=md.get("total_volume",{}).get("usd") or 0
    ath_c=md.get("ath_change_percentage",{}).get("usd") or 0
    c24=md.get("price_change_percentage_24h") or 0
    c7=md.get("price_change_percentage_7d") or 0

    if 0<mcap<1e6: s=25;fg.append("🎯 Market cap < $1M — micro-cap, tiềm năng x lớn")
    elif mcap<5e6: s=18;fg.append("✅ Market cap < $5M — low-cap")
    elif mcap<20e6: s=10;fy.append("⚠️ Market cap $5M–$20M")
    elif mcap<100e6: s=4;fy.append("⚠️ Market cap $20M–$100M")
    else: s=0;fr.append("❌ Market cap > $100M — upside hạn chế")
    score+=s;bd["Market Cap"]=s

    ratio=fdv/mcap if fdv>0 and mcap>0 else 0
    if ratio==0: s=10;fy.append("⚠️ Không có data FDV")
    elif ratio<3: s=20;fg.append(f"✅ FDV/Mcap = {ratio:.1f}x — lành mạnh")
    elif ratio<7: s=12;fy.append(f"⚠️ FDV/Mcap = {ratio:.1f}x — dilution trung bình")
    elif ratio<15: s=5;fr.append(f"🚨 FDV/Mcap = {ratio:.1f}x — dilution cao")
    else: s=0;fr.append(f"❌ FDV/Mcap = {ratio:.1f}x — NGUY HIỂM")
    score+=s;bd["FDV/Mcap"]=s

    cp=(circ/maxs*100) if maxs>0 and circ>0 else 0
    if cp==0: s=5;fy.append("⚠️ Không có data supply")
    elif cp<15: s=20;fg.append(f"🚀 Circ supply {cp:.1f}% — rất thấp, dễ pump")
    elif cp<30: s=15;fg.append(f"✅ Circ supply {cp:.1f}%")
    elif cp<60: s=8;fy.append(f"⚠️ Circ supply {cp:.1f}%")
    else: s=3;fy.append(f"⚠️ Circ supply {cp:.1f}% — phần lớn unlocked")
    score+=s;bd["Circ Supply"]=s

    vr=vol/mcap if mcap>0 and vol>0 else 0
    if vr==0: s=0;fr.append("❌ Không có volume")
    elif 0.1<vr<1.0: s=15;fg.append(f"✅ Vol/Mcap = {vr:.2f} — liquidity tốt")
    elif vr>=1.0: s=8;fy.append(f"⚠️ Vol/Mcap = {vr:.2f} — volume rất cao")
    elif vr>0.02: s=8;fy.append(f"⚠️ Vol/Mcap = {vr:.2f} — volume thấp")
    else: s=2;fr.append("❌ Volume gần chết")
    score+=s;bd["Volume/Mcap"]=s

    if ath_c<-90: s=10;fg.append(f"💀 -{abs(ath_c):.0f}% từ ATH — đáy sâu")
    elif ath_c<-75: s=8;fg.append(f"📉 -{abs(ath_c):.0f}% từ ATH")
    elif ath_c<-50: s=5;fy.append(f"⚠️ -{abs(ath_c):.0f}% từ ATH")
    elif ath_c<-20: s=2;fy.append(f"⚠️ -{abs(ath_c):.0f}% từ ATH — gần ATH")
    else: s=0;fr.append("❌ Near ATH — rủi ro cao")
    score+=s;bd["ATH Dist"]=s

    comm=data.get("community_data",{})
    soc=(comm.get("twitter_followers") or 0)+(comm.get("telegram_channel_user_count") or 0)
    if 1000<soc<50000: s=10;fg.append(f"✅ Community nhỏ ({soc:,}) — còn early")
    elif soc<=1000: s=6;fy.append(f"⚠️ Community rất nhỏ ({soc:,})")
    elif soc<200000: s=5;fy.append(f"⚠️ Community trung bình ({soc:,})")
    else: s=2;fy.append(f"⚠️ Community lớn ({soc:,})")
    score+=s;bd["Community"]=s

    if score>=80: g,gc,gl="S","#a371f7","CỰC CAO"
    elif score>=65: g,gc,gl="A","#3fb950","CAO"
    elif score>=50: g,gc,gl="B","#58a6ff","TRUNG BÌNH"
    elif score>=35: g,gc,gl="C","#d29922","THẤP"
    else: g,gc,gl="D","#f85149","RẤT THẤP"
    return {"score":score,"grade":g,"grade_color":gc,"grade_label":gl,
            "fg":fg,"fr":fr,"fy":fy,"bd":bd,
            "mcap":mcap,"fdv":fdv,"ratio":ratio,"cp":cp,"vr":vr,
            "c24":c24,"c7":c7,"ath_c":ath_c}

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <p class="main-title">💎 Gem Hunter</p>
    <p style="color:#8b949e;font-size:0.9rem;margin-top:8px;">Phân tích token micro-cap · Narrative Scanner · Range Bot · Dữ liệu realtime</p>
</div>
""", unsafe_allow_html=True)

ci, cb = st.columns([4,1])
with ci:
    query = st.text_input("", placeholder="🔍  Nhập tên token, symbol... (vd: AIA, LAB, COAI)", key="q", label_visibility="collapsed")
with cb:
    search_btn = st.button("Phân tích", use_container_width=True)

st.markdown("")

# ─── SEARCH RESULT ────────────────────────────────────────────────────────────
if search_btn and query:
    with st.spinner("🔍 Đang tìm..."):
        results = search_token(query)
    if not results:
        st.error("Không tìm thấy token.")
    else:
        coin_id = results[0]["id"]
        with st.spinner("📊 Đang load data..."):
            data = get_token_data(coin_id)

        if not data or data.get("error")=="rate_limit":
            st.warning("⏳ Rate limit. Chờ 60 giây rồi thử lại.")
        elif data.get("error"):
            st.error(f"Lỗi: {data['error']}")
        else:
            r = score_token(data)
            md = data.get("market_data",{})
            price = md.get("current_price",{}).get("usd",0)
            ath = md.get("ath",{}).get("usd",0)
            vol = md.get("total_volume",{}).get("usd",0)
            cats = data.get("categories",[])[:3]
            cat_html = " ".join([f'<span class="badge badge-blue">{c}</span>' for c in cats if c])

            st.markdown(f"""
            <div class="token-hdr">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                    <img src="{data.get('image',{}).get('small','')}" width="44" style="border-radius:50%;">
                    <div>
                        <span style="font-size:1.6rem;font-weight:700;">{data.get('name','')}</span>
                        <span style="background:#21262d;color:#58a6ff;padding:3px 10px;border-radius:6px;font-size:0.82rem;font-weight:600;margin-left:8px;">{data.get('symbol','').upper()}</span>
                    </div>
                </div>
                <div style="display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;">
                    <span style="font-size:2rem;font-weight:700;">{fmt_price(price)}</span>
                    <span style="color:{pct_color(r['c24'])};font-size:1rem;font-weight:600;">{pct_str(r['c24'])} (24h)</span>
                    <span style="color:{pct_color(r['c7'])};font-size:0.9rem;">{pct_str(r['c7'])} (7d)</span>
                </div>
                <div style="margin-top:8px;">{cat_html}</div>
            </div>
            """, unsafe_allow_html=True)

            c1,c2,c3,c4 = st.columns(4)
            with c1: st.markdown(f'<div class="card"><div style="font-size:2.8rem;font-weight:700;color:{r["grade_color"]}">{r["grade"]}</div><div style="font-size:1.3rem;font-weight:600;color:{r["grade_color"]}">{r["score"]}/100</div><div style="color:#8b949e;font-size:0.78rem;margin-top:4px;text-transform:uppercase;">Tiềm năng {r["grade_label"]}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="card"><div style="font-size:1.6rem;font-weight:700;color:#58a6ff">{fmt_usd(r["mcap"])}</div><div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;margin-top:4px;">Market Cap</div><div style="color:#8b949e;font-size:0.78rem;margin-top:6px;">FDV: {fmt_usd(r["fdv"])}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="card"><div style="font-size:1.6rem;font-weight:700;color:#d29922">{r["ratio"]:.1f}x</div><div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;margin-top:4px;">FDV / Mcap</div><div style="color:#8b949e;font-size:0.78rem;margin-top:6px;">Circ: {r["cp"]:.1f}%</div></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="card"><div style="font-size:1.6rem;font-weight:700;color:#f85149">{pct_str(r["ath_c"])}</div><div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;margin-top:4px;">Từ ATH ({fmt_price(ath)})</div><div style="color:#8b949e;font-size:0.78rem;margin-top:6px;">Vol: {fmt_usd(vol)}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            cl, cr = st.columns(2)
            with cl:
                st.markdown('<div class="sec">🚦 Phân tích Tokenomics</div>', unsafe_allow_html=True)
                for f in r["fg"]: st.markdown(f'<div class="flag-green">{f}</div>', unsafe_allow_html=True)
                for f in r["fy"]: st.markdown(f'<div class="flag-yellow">{f}</div>', unsafe_allow_html=True)
                for f in r["fr"]: st.markdown(f'<div class="flag-red">{f}</div>', unsafe_allow_html=True)
            with cr:
                st.markdown('<div class="sec">📊 Score Breakdown</div>', unsafe_allow_html=True)
                max_s={"Market Cap":25,"FDV/Mcap":20,"Circ Supply":20,"Volume/Mcap":15,"ATH Dist":10,"Community":10}
                fig=go.Figure()
                fig.add_trace(go.Bar(y=list(r["bd"].keys()),x=[max_s[k] for k in r["bd"]],orientation='h',marker_color='#21262d'))
                fig.add_trace(go.Bar(y=list(r["bd"].keys()),x=list(r["bd"].values()),orientation='h',
                    marker_color=r["grade_color"],
                    text=[f"{v}/{max_s[k]}" for k,v in r["bd"].items()],textposition='outside',
                    textfont=dict(color='#e6edf3',size=11)))
                fig.update_layout(barmode='overlay',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#8b949e',family='Inter'),showlegend=False,height=250,
                    margin=dict(l=0,r=60,t=0,b=0),
                    xaxis=dict(showgrid=False,showticklabels=False,zeroline=False),
                    yaxis=dict(showgrid=False,tickfont=dict(color='#e6edf3',size=11)))
                st.plotly_chart(fig,use_container_width=True)

            tickers=data.get("tickers",[])[:3]
            if tickers:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="sec">🏦 Đang giao dịch trên</div>', unsafe_allow_html=True)
                ecols=st.columns(3)
                for i,t in enumerate(tickers):
                    with ecols[i]:
                        st.markdown(f'<div class="card" style="text-align:left;"><div style="font-weight:600;">{t.get("market",{}).get("name","")}</div><div style="color:#58a6ff;font-size:0.85rem;">{t.get("base","")}/{t.get("target","")}</div><div style="color:#8b949e;font-size:0.78rem;margin-top:4px;">Vol: {fmt_usd(t.get("converted_volume",{}).get("usd",0))}</div></div>', unsafe_allow_html=True)

            desc=data.get("description",{}).get("en","")
            if desc:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="sec">📝 Mô tả</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="color:#8b949e;font-size:0.85rem;line-height:1.6;">{desc[:400]}{"..."if len(desc)>400 else""}</div>', unsafe_allow_html=True)

            st.markdown('<div class="warning">⚠️ <strong>Disclaimer:</strong> Chỉ hỗ trợ phân tích dữ liệu, KHÔNG phải lời khuyên đầu tư. Luôn verify thủ công trước khi vào lệnh.</div>', unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────
st.markdown("<br><hr style='border-color:#21262d;'><br>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["🔥 Trending", "💎 Micro-cap <$5M", "🔍 Narrative Scanner", "🤖 Range Bot Scanner"])

with tab1:
    trending=get_trending()
    if trending:
        hcols=st.columns([0.4,2,1.2,1.2,1.2,1.5])
        for col,h in zip(hcols,["#","Token","Giá","24h","Mcap","Signal"]):
            col.markdown(f'<div style="color:#8b949e;font-size:0.72rem;text-transform:uppercase;padding-bottom:8px;">{h}</div>',unsafe_allow_html=True)
        for i,item in enumerate(trending[:10]):
            c=item.get("item",{}); d=c.get("data",{})
            pu=d.get("price",0); ch=d.get("price_change_percentage_24h",{}).get("usd",0)
            rank=c.get("market_cap_rank",9999)
            sig="🔥 Early" if rank>500 else "👀 Watch" if rank>200 else "📊 Big"
            cols=st.columns([0.4,2,1.2,1.2,1.2,1.5])
            cols[0].markdown(f'<div style="color:#8b949e;padding-top:10px;">{i+1}</div>',unsafe_allow_html=True)
            cols[1].markdown(f'<div style="display:flex;align-items:center;gap:8px;padding-top:6px;"><img src="{c.get("small","")}" width="22" style="border-radius:50%;"><span style="font-weight:500;">{c.get("name","")}</span> <span style="color:#8b949e;font-size:0.78rem;">{c.get("symbol","")}</span></div>',unsafe_allow_html=True)
            cols[2].markdown(f'<div style="padding-top:10px;">{fmt_price(pu) if pu else "N/A"}</div>',unsafe_allow_html=True)
            cols[3].markdown(f'<div style="color:{pct_color(ch)};padding-top:10px;">{pct_str(ch)}</div>',unsafe_allow_html=True)
            cols[4].markdown(f'<div style="color:#8b949e;padding-top:10px;">{d.get("market_cap","N/A")}</div>',unsafe_allow_html=True)
            cols[5].markdown(f'<div style="padding-top:10px;">{sig}</div>',unsafe_allow_html=True)
    else:
        st.info("Đang tải...")

with tab2:
    st.markdown('<div style="color:#8b949e;font-size:0.82rem;margin-bottom:12px;">Market cap $100K–$5M · Volume đáng chú ý · Refresh mỗi 2 phút</div>',unsafe_allow_html=True)
    lc=get_microcap()
    if lc:
        hcols=st.columns([2,1.2,1.2,1.2,1.2,1.2])
        for col,h in zip(hcols,["Token","Giá","24h","Mcap","Volume","FDV"]):
            col.markdown(f'<div style="color:#8b949e;font-size:0.72rem;text-transform:uppercase;padding-bottom:8px;">{h}</div>',unsafe_allow_html=True)
        for coin in lc:
            ch=coin.get("price_change_percentage_24h",0)
            cols=st.columns([2,1.2,1.2,1.2,1.2,1.2])
            cols[0].markdown(f'<div style="display:flex;align-items:center;gap:8px;padding-top:6px;"><img src="{coin.get("image","")}" width="22" style="border-radius:50%;"><span style="font-weight:500;font-size:0.88rem;">{coin.get("name","")}</span> <span style="color:#8b949e;font-size:0.72rem;">{coin.get("symbol","").upper()}</span></div>',unsafe_allow_html=True)
            cols[1].markdown(f'<div style="padding-top:10px;font-size:0.88rem;">{fmt_price(coin.get("current_price",0))}</div>',unsafe_allow_html=True)
            cols[2].markdown(f'<div style="color:{pct_color(ch)};padding-top:10px;font-size:0.88rem;">{pct_str(ch)}</div>',unsafe_allow_html=True)
            cols[3].markdown(f'<div style="padding-top:10px;font-size:0.88rem;">{fmt_usd(coin.get("market_cap",0))}</div>',unsafe_allow_html=True)
            cols[4].markdown(f'<div style="padding-top:10px;font-size:0.88rem;color:#8b949e;">{fmt_usd(coin.get("total_volume",0))}</div>',unsafe_allow_html=True)
            cols[5].markdown(f'<div style="padding-top:10px;font-size:0.88rem;color:#8b949e;">{fmt_usd(coin.get("fully_diluted_valuation",0))}</div>',unsafe_allow_html=True)
    else:
        st.info("Đang tải...")

with tab3:
    st.markdown("""
    <div style="background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px 18px;margin-bottom:16px;">
        <div style="font-weight:600;color:#e6edf3;">🔍 Narrative Scanner</div>
        <div style="color:#8b949e;font-size:0.82rem;margin-top:4px;">Phát hiện narrative đang pump → tìm gem chưa pump cùng sector · Cache 30 phút</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Refresh / Scan ngay", use_container_width=False):
        st.cache_data.clear()
        st.rerun()

    if not CMC_KEY:
        st.error("⚠️ Chưa cấu hình CMC_API_KEY trong Streamlit Secrets.")
    else:
        with st.spinner("📊 Đang scan top gainers 7 ngày..."):
            gainers, err = get_top_gainers_cmc()

        if err and err != "no_key":
            st.error(f"Lỗi CMC API: {err}")
        elif not gainers:
            st.info("Không tìm thấy token nào +30% trong 7 ngày với market cap < $5M. Thị trường đang sideways.")
        else:
            nc, nt = analyze_narrative(gainers)
            top_narr = list(nc.keys())[0] if nc else ""
            top_count = list(nc.values())[0] if nc else 0

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#1a2e1a,#0d1117);border:1px solid #3fb950;border-radius:12px;padding:18px;margin-bottom:16px;text-align:center;">
                <div style="color:#8b949e;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.1em;">Narrative đang HOT</div>
                <div style="font-size:1.8rem;font-weight:700;color:#3fb950;margin-top:6px;">{top_narr}</div>
                <div style="color:#8b949e;font-size:0.82rem;margin-top:4px;">{top_count} token +30%+ · {len(gainers)} gainers tổng</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="sec">📊 Phân bổ Narrative</div>', unsafe_allow_html=True)
            ncols = st.columns(min(len(nc), 4))
            for i, (narr, cnt) in enumerate(list(nc.items())[:4]):
                with ncols[i]:
                    pct = cnt/len(gainers)*100
                    st.markdown(f"""
                    <div class="card">
                        <div style="font-size:1.4rem;">{narr.split()[0]}</div>
                        <div style="font-size:1.1rem;font-weight:700;color:#58a6ff;margin-top:4px;">{cnt} tokens</div>
                        <div style="color:#8b949e;font-size:0.78rem;">{' '.join(narr.split()[1:])}</div>
                        <div style="color:#3fb950;font-size:0.72rem;margin-top:4px;">{pct:.0f}% gainers</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown(f'<div class="sec">🚀 Top {len(gainers)} token +30%+ (7 ngày) · Mcap < $5M</div>', unsafe_allow_html=True)
            hcols=st.columns([2,1.2,1.2,1.2,1.2,2])
            for col,h in zip(hcols,["Token","Giá","7 ngày","24h","Mcap","Narrative"]):
                col.markdown(f'<div style="color:#8b949e;font-size:0.72rem;text-transform:uppercase;padding-bottom:8px;">{h}</div>',unsafe_allow_html=True)
            for t in gainers:
                cols=st.columns([2,1.2,1.2,1.2,1.2,2])
                cols[0].markdown(f'<div style="padding-top:8px;font-weight:500;">{t["name"]} <span style="color:#8b949e;font-size:0.75rem;">{t["symbol"]}</span></div>',unsafe_allow_html=True)
                cols[1].markdown(f'<div style="padding-top:8px;font-size:0.88rem;">{fmt_price(t["price"])}</div>',unsafe_allow_html=True)
                cols[2].markdown(f'<div style="color:#3fb950;padding-top:8px;font-weight:600;">+{t["change_7d"]:.0f}%</div>',unsafe_allow_html=True)
                cols[3].markdown(f'<div style="color:{pct_color(t["change_24h"])};padding-top:8px;">{pct_str(t["change_24h"])}</div>',unsafe_allow_html=True)
                cols[4].markdown(f'<div style="padding-top:8px;color:#8b949e;font-size:0.88rem;">{fmt_usd(t["market_cap"])}</div>',unsafe_allow_html=True)
                tags_html=" ".join([f'<span class="badge badge-purple">{tg[:12]}</span>' for tg in t["tags"][:2]])
                cols[5].markdown(f'<div style="padding-top:6px;">{tags_html}</div>',unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="sec">💎 Gem chưa pump — cùng narrative đang hot</div>', unsafe_allow_html=True)

            narr_tag_map={
                "ai":["artificial-intelligence","ai","agent","machine-learning"],
                "rwa":["real-world-assets","rwa","asset"],
                "depin":["depin","infrastructure","physical"],
                "gamefi":["gaming","play-to-earn","game","nft-gaming"],
                "defi":["defi","decentralized-finance","yield","dex"],
                "meme":["memes","meme","dog","cat"],
                "sports":["sports","fan-token","football"],
            }
            search_tags=["ai","agent"]
            if top_narr:
                tn=top_narr.lower()
                for k,tags in narr_tag_map.items():
                    if k in tn:
                        search_tags=tags; break

            with st.spinner(f"🔍 Đang tìm gem chưa pump trong {top_narr}..."):
                gems=get_gems_by_tags(search_tags)

            if gems:
                st.markdown(f'<div style="color:#8b949e;font-size:0.82rem;margin-bottom:10px;">{len(gems)} token tiềm năng · Sắp xếp theo Vol/Mcap (tín hiệu accumulation 🔥)</div>',unsafe_allow_html=True)
                hcols=st.columns([2,1.2,1.2,1.2,1.2,1.2])
                for col,h in zip(hcols,["Token","Giá","24h","7 ngày","Mcap","Vol/Mcap"]):
                    col.markdown(f'<div style="color:#8b949e;font-size:0.72rem;text-transform:uppercase;padding-bottom:8px;">{h}</div>',unsafe_allow_html=True)
                for gem in gems:
                    vr=gem["vol_mcap"]
                    sig="🔥" if vr>0.5 else "👀" if vr>0.2 else "📊"
                    cols=st.columns([2,1.2,1.2,1.2,1.2,1.2])
                    cols[0].markdown(f'<div style="padding-top:8px;font-weight:500;">{gem["name"]} <span style="color:#8b949e;font-size:0.75rem;">{gem["symbol"]}</span></div>',unsafe_allow_html=True)
                    cols[1].markdown(f'<div style="padding-top:8px;font-size:0.88rem;">{fmt_price(gem["price"])}</div>',unsafe_allow_html=True)
                    cols[2].markdown(f'<div style="color:{pct_color(gem["change_24h"])};padding-top:8px;">{pct_str(gem["change_24h"])}</div>',unsafe_allow_html=True)
                    cols[3].markdown(f'<div style="color:{pct_color(gem["change_7d"])};padding-top:8px;">{pct_str(gem["change_7d"])}</div>',unsafe_allow_html=True)
                    cols[4].markdown(f'<div style="padding-top:8px;color:#8b949e;font-size:0.88rem;">{fmt_usd(gem["market_cap"])}</div>',unsafe_allow_html=True)
                    cols[5].markdown(f'<div style="padding-top:8px;">{sig} {vr:.2f}x</div>',unsafe_allow_html=True)
            else:
                st.info("Không tìm thấy gem phù hợp trong narrative này.")

with tab4:
    st.markdown("""
    <div style="background:#161b22;border:1px solid #21262d;border-radius:10px;padding:14px 18px;margin-bottom:16px;">
        <div style="font-weight:600;color:#e6edf3;">🤖 Range Bot Scanner</div>
        <div style="color:#8b949e;font-size:0.82rem;margin-top:4px;">
            Phát hiện token bị bot dev chạy liquidity trong range ổn định · MEXC + BitMart Spot · Cache 5 phút
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chọn sàn + khung thời gian
    c_ex1, c_ex2, c_tf = st.columns([1.2, 1.2, 1.6])
    with c_ex1:
        use_mexc = st.checkbox("MEXC", value=True, key="rb_mexc")
    with c_ex2:
        use_bitmart = st.checkbox("BitMart", value=True, key="rb_bitmart")
    with c_tf:
        tf_label = st.selectbox("Khung thời gian", ["M5", "M15", "H1"], index=1, key="rb_tf",
            help="Range bot thấy rõ nhất ở M15")
    tf_map = {"M5": 5, "M15": 15, "H1": 60}
    tf_minutes = tf_map[tf_label]

    # Config filter
    c_cfg1, c_cfg2, c_cfg3 = st.columns(3)
    with c_cfg1:
        max_range_pct = st.slider("Range tối đa (%)", 5, 25, 20, 1,
            help="Token dao động trong range hẹp hơn mức này")
    with c_cfg2:
        min_oscillations = st.slider("Oscillation tối thiểu", 2, 15, 4, 1,
            help="Số lần giá chuyển xen kẽ giữa biên trên và biên dưới")
    with c_cfg3:
        max_scan_pairs = st.slider("Số pairs scan / sàn", 100, 500, 300, 50,
            help="Nhiều hơn = chậm hơn")

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        scan_btn = st.button("🔄 Scan ngay", use_container_width=True, key="range_scan_btn")
    with col_info:
        est = ""
        if use_bitmart:
            est = " · BitMart rate limit thấp nên chậm hơn (~2-3 phút)"
        st.markdown(f'<div style="color:#8b949e;font-size:0.82rem;padding-top:10px;">⏱ Quét theo từng sàn đã chọn · Cache 5 phút{est}</div>', unsafe_allow_html=True)

    if scan_btn:
        st.cache_data.clear()

    if not use_mexc and not use_bitmart:
        st.warning("⚠️ Chọn ít nhất 1 sàn để scan.")
    else:
        ex_txt = " + ".join([x for x, on in [("MEXC", use_mexc), ("BitMart", use_bitmart)] if on])
        with st.spinner(f"🔍 Đang scan {ex_txt} · {tf_label}..."):
            range_results, scan_err = scan_range_bots(
                max_scan=max_scan_pairs, tf_minutes=tf_minutes,
                scan_mexc=use_mexc, scan_bitmart=use_bitmart)

        if scan_err:
            st.error(f"Lỗi: {scan_err}")
        elif not range_results:
            st.info("Không tìm thấy token nào match pattern. Thử tăng Range tối đa hoặc giảm Oscillation tối thiểu.")
        else:
            # Lọc theo config người dùng
            filtered = [r for r in range_results
                        if r["range_pct"] <= max_range_pct
                        and r["oscillations"] >= min_oscillations]

            buy_zone  = [r for r in filtered if "BUY"  in r["signal"]]
            sell_zone = [r for r in filtered if "SELL" in r["signal"]]
            mid_zone  = [r for r in filtered if "MID"  in r["signal"]]

            m1, m2, m3, m4 = st.columns(4)
            m1.markdown(f'<div class="card"><div style="font-size:2rem;font-weight:700;color:#58a6ff">{len(filtered)}</div><div style="color:#8b949e;font-size:0.75rem;margin-top:4px;">TOKEN TÌM THẤY</div></div>', unsafe_allow_html=True)
            m2.markdown(f'<div class="card"><div style="font-size:2rem;font-weight:700;color:#3fb950">{len(buy_zone)}</div><div style="color:#8b949e;font-size:0.75rem;margin-top:4px;">🟢 BUY ZONE</div></div>', unsafe_allow_html=True)
            m3.markdown(f'<div class="card"><div style="font-size:2rem;font-weight:700;color:#f85149">{len(sell_zone)}</div><div style="color:#8b949e;font-size:0.75rem;margin-top:4px;">🔴 SELL ZONE</div></div>', unsafe_allow_html=True)
            m4.markdown(f'<div class="card"><div style="font-size:2rem;font-weight:700;color:#8b949e">{len(mid_zone)}</div><div style="color:#8b949e;font-size:0.75rem;margin-top:4px;">⚪ MID RANGE</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            show_filter = st.radio("Hiển thị:", ["Tất cả", "🟢 Buy Zone", "🔴 Sell Zone"],
                                   horizontal=True, key="rb_filter")

            if show_filter == "🟢 Buy Zone":
                display = buy_zone
            elif show_filter == "🔴 Sell Zone":
                display = sell_zone
            else:
                display = filtered

            if not display:
                st.info("Không có token trong zone này.")
            else:
                st.markdown(f'<div style="color:#8b949e;font-size:0.82rem;margin-bottom:10px;">{len(display)} token · Sắp xếp theo Bot Score cao nhất</div>', unsafe_allow_html=True)

                hcols = st.columns([1, 1.8, 1, 1, 1.2, 1.2, 1.4, 1])
                for col, h in zip(hcols, ["Sàn", "Symbol", "Giá", "Range%", "Low", "High", "Vị trí", "Score"]):
                    col.markdown(f'<div style="color:#8b949e;font-size:0.72rem;text-transform:uppercase;padding-bottom:8px;">{h}</div>', unsafe_allow_html=True)

                def fmt_p(v):
                    return f"${v:.6f}" if v < 0.01 else f"${v:.4f}" if v < 1 else f"${v:.2f}"

                for item in display:
                    cols = st.columns([1, 1.8, 1, 1, 1.2, 1.2, 1.4, 1])
                    ex = item.get("exchange", "")
                    ex_badge = "badge-mexc" if ex == "MEXC" else "badge-bitmart"
                    cols[0].markdown(f'<div style="padding-top:8px;"><span class="badge {ex_badge}">{ex}</span></div>', unsafe_allow_html=True)
                    cols[1].markdown(f'<div style="padding-top:8px;font-weight:600;color:#58a6ff;">{item["symbol"]}</div>', unsafe_allow_html=True)
                    cols[2].markdown(f'<div style="padding-top:8px;font-size:0.85rem;">{fmt_p(item["current_price"])}</div>', unsafe_allow_html=True)
                    cols[3].markdown(f'<div style="padding-top:8px;color:#d29922;font-size:0.85rem;">{item["range_pct"]:.1f}%</div>', unsafe_allow_html=True)
                    cols[4].markdown(f'<div style="padding-top:8px;color:#f85149;font-size:0.8rem;">{fmt_p(item["range_low"])}</div>', unsafe_allow_html=True)
                    cols[5].markdown(f'<div style="padding-top:8px;color:#3fb950;font-size:0.8rem;">{fmt_p(item["range_high"])}</div>', unsafe_allow_html=True)
                    pos = item["pos_in_range"]
                    bar_color = item["signal_color"]
                    cols[6].markdown(f"""
                    <div style="padding-top:10px;">
                        <div style="background:#21262d;border-radius:4px;height:6px;width:100%;">
                            <div style="background:{bar_color};width:{pos:.0f}%;height:6px;border-radius:4px;"></div>
                        </div>
                        <div style="color:{bar_color};font-size:0.7rem;margin-top:3px;">{item["signal"]} · {pos:.0f}%</div>
                    </div>""", unsafe_allow_html=True)
                    score_color = "#3fb950" if item["score"] >= 60 else "#d29922" if item["score"] >= 40 else "#8b949e"
                    cols[7].markdown(f'<div style="padding-top:8px;font-weight:700;color:{score_color};">{item["score"]}</div>', unsafe_allow_html=True)

                st.markdown('<div class="warning">⚠️ Range bot pattern không đảm bảo giá sẽ tiếp tục sideway. Bot có thể dừng bất kỳ lúc nào → giá dump. Luôn đặt SL chặt ngoài range.</div>', unsafe_allow_html=True)

st.markdown('<br><div style="text-align:center;color:#484f58;font-size:0.78rem;padding:16px 0;">💎 Gem Hunter · CoinGecko + CoinMarketCap + MEXC + BitMart · Research only</div>', unsafe_allow_html=True)
