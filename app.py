import streamlit as st
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
import os

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="💎 Hidden Gem Hunter",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
CG_KEY = os.environ.get("COINGECKO_API_KEY", "")
CG_HEADERS = {"x-cg-demo-api-key": CG_KEY} if CG_KEY else {}
CMC_KEY = os.environ.get("CMC_API_KEY", "")
CMC_HEADERS = {"X-CMC_PRO_API_KEY": CMC_KEY, "Accept": "application/json"}

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0d1117; color: #e6edf3; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}

.main-header {
    background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
    border: 1px solid #21262d; border-radius: 16px;
    padding: 32px; margin-bottom: 24px; text-align: center;
}
.main-title {
    font-size: 2.4rem; font-weight: 700;
    background: linear-gradient(135deg, #58a6ff, #a371f7, #f78166);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;
}
.score-card {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 12px; padding: 20px; text-align: center; height: 100%;
}
.score-number { font-size: 3rem; font-weight: 700; line-height: 1; }
.score-label { color: #8b949e; font-size: 0.8rem; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-card { background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 16px 20px; margin-bottom: 12px; }
.flag-item { padding: 10px 14px; border-radius: 8px; margin-bottom: 8px; font-size: 0.88rem; }
.flag-green { background: #0d2818; border-left: 3px solid #3fb950; color: #7ee787; }
.flag-red   { background: #2d1212; border-left: 3px solid #f85149; color: #ff7b72; }
.flag-yellow{ background: #2d2208; border-left: 3px solid #d29922; color: #e3b341; }
.section-title {
    font-size: 1rem; font-weight: 600; color: #8b949e;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin-bottom: 14px; padding-bottom: 8px; border-bottom: 1px solid #21262d;
}
.token-header { background: #161b22; border: 1px solid #21262d; border-radius: 12px; padding: 24px; margin-bottom: 20px; }
.token-name { font-size: 1.8rem; font-weight: 700; color: #e6edf3; }
.token-symbol { background: #21262d; color: #58a6ff; padding: 3px 10px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; display: inline-block; margin-left: 10px; vertical-align: middle; }
.price-big { font-size: 2.2rem; font-weight: 700; color: #e6edf3; }

.ta-signal-box {
    background: #161b22; border: 1px solid #21262d;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 10px;
}
.ta-signal-bull { border-left: 4px solid #3fb950; }
.ta-signal-bear { border-left: 4px solid #f85149; }
.ta-signal-neut { border-left: 4px solid #d29922; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600; }
.badge-green { background: #0d2818; color: #3fb950; }
.badge-red   { background: #2d1212; color: #f85149; }
.badge-blue  { background: #0d2137; color: #58a6ff; }
.badge-purple{ background: #1e1037; color: #a371f7; }
.badge-yellow{ background: #2d2208; color: #e3b341; }

.warning-box { background: #2d1a00; border: 1px solid #d29922; border-radius: 10px; padding: 14px 18px; font-size: 0.85rem; color: #e3b341; margin-top: 16px; }

.stTextInput input { background: #161b22 !important; border: 1px solid #30363d !important; border-radius: 10px !important; color: #e6edf3 !important; font-size: 1rem !important; padding: 12px 16px !important; }
.stTextInput input:focus { border-color: #58a6ff !important; box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important; }
.stButton button { background: linear-gradient(135deg, #1f6feb, #388bfd) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; padding: 12px 28px !important; font-size: 1rem !important; width: 100%; }
</style>
""", unsafe_allow_html=True)

# ─── API HELPERS ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def search_token(query):
    try:
        r = requests.get(f"{COINGECKO_BASE}/search", params={"query": query}, headers=CG_HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("coins", [])
    except: pass
    return []

@st.cache_data(ttl=60)
def get_token_data(coin_id):
    try:
        r = requests.get(f"{COINGECKO_BASE}/coins/{coin_id}",
            params={"localization":"false","tickers":"true","market_data":"true","community_data":"true","developer_data":"false"},
            headers=CG_HEADERS, timeout=15)
        if r.status_code == 200: return r.json()
        if r.status_code == 429: return {"error": "rate_limit"}
    except Exception as e: return {"error": str(e)}
    return None

@st.cache_data(ttl=300)
def get_ohlcv_h4(coin_id):
    """Lấy OHLCV data từ CoinGecko, fallback market_chart nếu ohlc fail"""
    try:
        # Try OHLC endpoint first
        r = requests.get(f"{COINGECKO_BASE}/coins/{coin_id}/ohlc",
            params={"vs_currency": "usd", "days": "90"},
            headers=CG_HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if len(data) >= 10:
                df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                return df.set_index("timestamp")
    except: pass
    try:
        # Fallback: market_chart
        r2 = requests.get(f"{COINGECKO_BASE}/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": "90", "interval": "daily"},
            headers=CG_HEADERS, timeout=15)
        if r2.status_code == 200:
            prices = r2.json().get("prices", [])
            if len(prices) >= 10:
                df = pd.DataFrame(prices, columns=["timestamp", "close"])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
                df = df.set_index("timestamp")
                df["open"] = df["close"].shift(1).fillna(df["close"])
                df["high"] = df[["open","close"]].max(axis=1) * (1 + abs(df["close"].pct_change().fillna(0)) * 0.5)
                df["low"]  = df[["open","close"]].min(axis=1) * (1 - abs(df["close"].pct_change().fillna(0)) * 0.5)
                return df
    except: pass
    return None

@st.cache_data(ttl=300)
def get_volume_data(coin_id):
    """Lấy volume history"""
    try:
        r = requests.get(f"{COINGECKO_BASE}/coins/{coin_id}/market_chart",
            params={"vs_currency": "usd", "days": "90", "interval": "daily"},
            headers=CG_HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            volumes = data.get("total_volumes", [])
            df = pd.DataFrame(volumes, columns=["timestamp", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df.set_index("timestamp")
            return df
    except: pass
    return None

@st.cache_data(ttl=300)
def get_trending():
    try:
        r = requests.get(f"{COINGECKO_BASE}/search/trending", headers=CG_HEADERS, timeout=10)
        if r.status_code == 200: return r.json().get("coins", [])
    except: pass
    return []

@st.cache_data(ttl=120)
def get_new_listings():
    try:
        r = requests.get(f"{COINGECKO_BASE}/coins/markets",
            params={"vs_currency":"usd","order":"volume_desc","per_page":250,"page":1,"sparkline":"false","price_change_percentage":"24h"},
            headers=CG_HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return [c for c in data if c.get("market_cap") and 100_000 < c["market_cap"] < 5_000_000 and c.get("total_volume",0) > 10_000][:20]
    except: pass
    return []

# ─── TECHNICAL ANALYSIS ───────────────────────────────────────────────────────
def calc_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_bb(close, period=20, std=2):
    ma = close.rolling(period).mean()
    sigma = close.rolling(period).std()
    return ma + std*sigma, ma, ma - std*sigma

def detect_sr_levels(df, lookback=20, tolerance=0.02):
    """Detect Support/Resistance từ swing highs/lows"""
    highs = df["high"].rolling(lookback, center=True).max()
    lows = df["low"].rolling(lookback, center=True).min()
    resistance = df[df["high"] == highs]["high"].dropna()
    support = df[df["low"] == lows]["low"].dropna()
    current_price = df["close"].iloc[-1]
    res_levels = sorted([v for v in resistance.unique() if v > current_price * (1 - tolerance)])[:3]
    sup_levels = sorted([v for v in support.unique() if v < current_price * (1 + tolerance)], reverse=True)[:3]
    return res_levels, sup_levels

def detect_rsi_divergence(df, rsi):
    """Phát hiện RSI divergence đơn giản"""
    if len(df) < 20: return None
    recent = 20
    price_last = df["close"].iloc[-recent:]
    rsi_last = rsi.iloc[-recent:]
    price_min_idx = price_last.idxmin()
    rsi_min_idx = rsi_last.idxmin()
    price_max_idx = price_last.idxmax()
    rsi_max_idx = rsi_last.idxmax()
    div = None
    if (price_last.iloc[-1] < price_last.iloc[0]) and (rsi_last.iloc[-1] > rsi_last.iloc[0]):
        div = "bullish"
    elif (price_last.iloc[-1] > price_last.iloc[0]) and (rsi_last.iloc[-1] < rsi_last.iloc[0]):
        div = "bearish"
    return div

def detect_volume_spike(vol_df, threshold=2.5):
    """Phát hiện volume spike"""
    if vol_df is None or len(vol_df) < 20: return False, 0
    avg_vol = vol_df["volume"].rolling(20).mean().iloc[-1]
    last_vol = vol_df["volume"].iloc[-1]
    ratio = last_vol / avg_vol if avg_vol > 0 else 0
    return ratio >= threshold, ratio

def analyze_technicals(coin_id):
    """Chạy full TA analysis"""
    df = get_ohlcv_h4(coin_id)
    vol_df = get_volume_data(coin_id)
    if df is None or len(df) < 30:
        return None

    # Merge volume
    if vol_df is not None:
        df = df.join(vol_df, how="left")
        df["volume"] = df["volume"].fillna(0)
    else:
        df["volume"] = 0

    close = df["close"]
    signals = []
    ta_score = 0

    # ── RSI ──
    rsi = calc_rsi(close)
    rsi_val = rsi.iloc[-1]
    if rsi_val < 30:
        signals.append({"type": "bull", "icon": "🟢", "label": "RSI Oversold", "detail": f"RSI = {rsi_val:.1f} — vùng quá bán, tiềm năng hồi phục"})
        ta_score += 2
    elif rsi_val > 70:
        signals.append({"type": "bear", "icon": "🔴", "label": "RSI Overbought", "detail": f"RSI = {rsi_val:.1f} — vùng quá mua, cẩn thận đảo chiều"})
        ta_score -= 1
    else:
        signals.append({"type": "neut", "icon": "🟡", "label": "RSI Neutral", "detail": f"RSI = {rsi_val:.1f} — vùng trung tính"})

    # ── RSI Divergence ──
    div = detect_rsi_divergence(df, rsi)
    if div == "bullish":
        signals.append({"type": "bull", "icon": "📈", "label": "RSI Bullish Divergence", "detail": "Giá giảm nhưng RSI tăng — tín hiệu đảo chiều tăng tiềm năng"})
        ta_score += 3
    elif div == "bearish":
        signals.append({"type": "bear", "icon": "📉", "label": "RSI Bearish Divergence", "detail": "Giá tăng nhưng RSI giảm — cảnh báo đảo chiều giảm"})
        ta_score -= 2

    # ── Bollinger Bands ──
    bb_upper, bb_mid, bb_lower = calc_bb(close)
    last_close = close.iloc[-1]
    bb_width = (bb_upper.iloc[-1] - bb_lower.iloc[-1]) / bb_mid.iloc[-1]
    bb_width_avg = ((bb_upper - bb_lower) / bb_mid).rolling(20).mean().iloc[-1]

    if bb_width < bb_width_avg * 0.7:
        signals.append({"type": "bull", "icon": "🔥", "label": "BB Squeeze", "detail": f"Bollinger Bands đang thu hẹp — sắp có breakout mạnh"})
        ta_score += 2
    if last_close <= bb_lower.iloc[-1]:
        signals.append({"type": "bull", "icon": "🎯", "label": "BB Lower Touch", "detail": f"Giá chạm BB dưới — vùng hỗ trợ mạnh, tiềm năng bounce"})
        ta_score += 2
    elif last_close >= bb_upper.iloc[-1]:
        signals.append({"type": "bear", "icon": "⚠️", "label": "BB Upper Touch", "detail": f"Giá chạm BB trên — vùng kháng cự, cẩn thận điều chỉnh"})
        ta_score -= 1

    # ── Volume Spike ──
    spike, vol_ratio = detect_volume_spike(vol_df)
    if spike:
        signals.append({"type": "bull", "icon": "🚀", "label": "Volume Spike", "detail": f"Volume tăng {vol_ratio:.1f}x so với trung bình 20 ngày — có dòng tiền lớn vào"})
        ta_score += 3
    elif vol_ratio > 0:
        signals.append({"type": "neut", "icon": "📊", "label": "Volume Normal", "detail": f"Volume ở mức bình thường ({vol_ratio:.1f}x avg)"})

    # ── Support/Resistance ──
    res_levels, sup_levels = detect_sr_levels(df)
    if sup_levels:
        nearest_sup = sup_levels[0]
        dist_sup = (last_close - nearest_sup) / last_close * 100
        if dist_sup < 5:
            signals.append({"type": "bull", "icon": "🛡️", "label": "Gần Support mạnh", "detail": f"Giá cách support {dist_sup:.1f}% — vùng mua tiềm năng"})
            ta_score += 2
    if res_levels:
        nearest_res = res_levels[0]
        dist_res = (nearest_res - last_close) / last_close * 100
        if dist_res < 10:
            signals.append({"type": "bear", "icon": "🧱", "label": "Gần Resistance", "detail": f"Kháng cự chỉ cách {dist_res:.1f}% — upside ngắn hạn bị giới hạn"})
            ta_score -= 1

    # ── Overall TA Grade ──
    if ta_score >= 6:
        ta_verdict = ("BULLISH MẠNH", "#3fb950", "bull")
    elif ta_score >= 3:
        ta_verdict = ("BULLISH", "#58a6ff", "bull")
    elif ta_score >= 0:
        ta_verdict = ("TRUNG TÍNH", "#d29922", "neut")
    elif ta_score >= -3:
        ta_verdict = ("BEARISH", "#f85149", "bear")
    else:
        ta_verdict = ("BEARISH MẠNH", "#f85149", "bear")

    return {
        "df": df,
        "rsi": rsi,
        "bb_upper": bb_upper,
        "bb_mid": bb_mid,
        "bb_lower": bb_lower,
        "signals": signals,
        "ta_score": ta_score,
        "ta_verdict": ta_verdict,
        "res_levels": res_levels,
        "sup_levels": sup_levels,
        "rsi_val": rsi_val,
    }

def render_ta_chart(ta, coin_name):
    """Render candlestick + BB + RSI + Volume chart"""
    df = ta["df"]
    rsi = ta["rsi"]

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.55, 0.25, 0.20],
        subplot_titles=[f"{coin_name} — Price H4 (90 ngày)", "RSI (14)", "Volume"]
    )

    # ── Candlestick ──
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name="Price",
        increasing_fillcolor="#3fb950", increasing_line_color="#3fb950",
        decreasing_fillcolor="#f85149", decreasing_line_color="#f85149",
    ), row=1, col=1)

    # ── Bollinger Bands ──
    fig.add_trace(go.Scatter(x=df.index, y=ta["bb_upper"], name="BB Upper",
        line=dict(color="#58a6ff", width=1, dash="dot"), opacity=0.7), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ta["bb_mid"], name="BB Mid",
        line=dict(color="#8b949e", width=1, dash="dash"), opacity=0.5), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=ta["bb_lower"], name="BB Lower",
        line=dict(color="#58a6ff", width=1, dash="dot"), opacity=0.7,
        fill="tonexty", fillcolor="rgba(88,166,255,0.05)"), row=1, col=1)

    # ── S/R Levels ──
    for r in ta["res_levels"][:2]:
        fig.add_hline(y=r, line_dash="dot", line_color="#f85149", line_width=1, opacity=0.6, row=1, col=1)
    for s in ta["sup_levels"][:2]:
        fig.add_hline(y=s, line_dash="dot", line_color="#3fb950", line_width=1, opacity=0.6, row=1, col=1)

    # ── RSI ──
    rsi_colors = ["#f85149" if v > 70 else "#3fb950" if v < 30 else "#58a6ff" for v in rsi]
    fig.add_trace(go.Scatter(x=rsi.index, y=rsi, name="RSI",
        line=dict(color="#a371f7", width=2)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dot", line_color="#f85149", line_width=1, opacity=0.5, row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#3fb950", line_width=1, opacity=0.5, row=2, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(88,166,255,0.03)", line_width=0, row=2, col=1)

    # ── Volume ──
    if "volume" in df.columns and df["volume"].sum() > 0:
        avg_vol = df["volume"].rolling(20).mean()
        vol_colors = ["#3fb950" if df["close"].iloc[i] >= df["open"].iloc[i] else "#f85149" for i in range(len(df))]
        fig.add_trace(go.Bar(x=df.index, y=df["volume"], name="Volume",
            marker_color=vol_colors, opacity=0.7), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=avg_vol, name="Vol MA20",
            line=dict(color="#d29922", width=1.5, dash="dot")), row=3, col=1)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0d1117",
        font=dict(color="#8b949e", family="Inter"),
        showlegend=False,
        height=680,
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis_rangeslider_visible=False,
    )
    for i in range(1, 4):
        fig.update_xaxes(showgrid=True, gridcolor="#21262d", row=i, col=1)
        fig.update_yaxes(showgrid=True, gridcolor="#21262d", row=i, col=1)

    return fig

# ─── SCORING ──────────────────────────────────────────────────────────────────
def score_token(data):
    score = 0
    flags_green, flags_red, flags_yellow = [], [], []
    breakdown = {}
    md = data.get("market_data", {})
    market_cap = md.get("market_cap", {}).get("usd") or 0
    fdv = md.get("fully_diluted_valuation", {}).get("usd") or 0
    circ_supply = md.get("circulating_supply") or 0
    max_supply = md.get("max_supply") or md.get("total_supply") or circ_supply
    volume_24h = md.get("total_volume", {}).get("usd") or 0
    ath_change = md.get("ath_change_percentage", {}).get("usd") or 0
    change_24h = md.get("price_change_percentage_24h") or 0
    change_7d = md.get("price_change_percentage_7d") or 0

    # Market Cap
    if 0 < market_cap < 1_000_000: s=25; flags_green.append("🎯 Market cap < $1M — vùng micro-cap, tiềm năng x lớn")
    elif market_cap < 5_000_000: s=18; flags_green.append("✅ Market cap < $5M — low-cap, còn room tăng tốt")
    elif market_cap < 20_000_000: s=10; flags_yellow.append("⚠️ Market cap $5M–$20M — small-cap")
    elif market_cap < 100_000_000: s=4; flags_yellow.append("⚠️ Market cap $20M–$100M — mid-cap")
    else: s=0; flags_red.append("❌ Market cap > $100M — upside hạn chế")
    score+=s; breakdown["Market Cap"]=s

    # FDV ratio
    ratio = fdv/market_cap if fdv>0 and market_cap>0 else 0
    if ratio == 0: s=10; flags_yellow.append("⚠️ Không có data FDV")
    elif ratio < 3: s=20; flags_green.append(f"✅ FDV/Mcap = {ratio:.1f}x — tokenomics lành mạnh")
    elif ratio < 7: s=12; flags_yellow.append(f"⚠️ FDV/Mcap = {ratio:.1f}x — dilution trung bình")
    elif ratio < 15: s=5; flags_red.append(f"🚨 FDV/Mcap = {ratio:.1f}x — dilution cao")
    else: s=0; flags_red.append(f"❌ FDV/Mcap = {ratio:.1f}x — NGUY HIỂM")
    score+=s; breakdown["FDV/Mcap Ratio"]=s

    # Circ Supply
    circ_pct = (circ_supply/max_supply*100) if max_supply>0 and circ_supply>0 else 0
    if circ_pct == 0: s=5; flags_yellow.append("⚠️ Không có data supply")
    elif circ_pct < 15: s=20; flags_green.append(f"🚀 Circ supply chỉ {circ_pct:.1f}% — supply thấp, dễ pump")
    elif circ_pct < 30: s=15; flags_green.append(f"✅ Circ supply {circ_pct:.1f}% — còn thấp")
    elif circ_pct < 60: s=8; flags_yellow.append(f"⚠️ Circ supply {circ_pct:.1f}%")
    else: s=3; flags_yellow.append(f"⚠️ Circ supply {circ_pct:.1f}% — phần lớn đã unlock")
    score+=s; breakdown["Circ Supply %"]=s

    # Volume/Mcap
    vol_ratio = volume_24h/market_cap if market_cap>0 and volume_24h>0 else 0
    if vol_ratio == 0: s=0; flags_red.append("❌ Không có volume")
    elif 0.1 < vol_ratio < 1.0: s=15; flags_green.append(f"✅ Volume/Mcap = {vol_ratio:.2f} — liquidity tốt")
    elif vol_ratio >= 1.0: s=8; flags_yellow.append(f"⚠️ Volume/Mcap = {vol_ratio:.2f} — volume rất cao, có thể pump")
    elif vol_ratio > 0.02: s=8; flags_yellow.append(f"⚠️ Volume/Mcap = {vol_ratio:.2f} — volume thấp")
    else: s=2; flags_red.append(f"❌ Volume gần chết — exit rất khó")
    score+=s; breakdown["Volume/Mcap"]=s

    # ATH Distance
    if ath_change < -90: s=10; flags_green.append(f"💀 -99%+ từ ATH — đang ở đáy sâu")
    elif ath_change < -75: s=8; flags_green.append(f"📉 -{abs(ath_change):.0f}% từ ATH — vùng thấp")
    elif ath_change < -50: s=5; flags_yellow.append(f"⚠️ -{abs(ath_change):.0f}% từ ATH")
    elif ath_change < -20: s=2; flags_yellow.append(f"⚠️ -{abs(ath_change):.0f}% từ ATH — gần ATH")
    else: s=0; flags_red.append(f"❌ Near ATH — rủi ro cao")
    score+=s; breakdown["ATH Distance"]=s

    # Community
    comm = data.get("community_data", {})
    total_social = (comm.get("twitter_followers") or 0) + (comm.get("telegram_channel_user_count") or 0)
    if 1000 < total_social < 50000: s=10; flags_green.append(f"✅ Community nhỏ ({total_social:,}) — còn early")
    elif total_social <= 1000: s=6; flags_yellow.append(f"⚠️ Community rất nhỏ ({total_social:,})")
    elif total_social < 200000: s=5; flags_yellow.append(f"⚠️ Community trung bình ({total_social:,})")
    else: s=2; flags_yellow.append(f"⚠️ Community lớn ({total_social:,})")
    score+=s; breakdown["Community"]=s

    if score>=80: grade,gc,gl="S","#a371f7","Tiềm năng CỰC CAO"
    elif score>=65: grade,gc,gl="A","#3fb950","Tiềm năng CAO"
    elif score>=50: grade,gc,gl="B","#58a6ff","Tiềm năng TRUNG BÌNH"
    elif score>=35: grade,gc,gl="C","#d29922","Tiềm năng THẤP"
    else: grade,gc,gl="D","#f85149","Tiềm năng RẤT THẤP"

    return {"score":score,"grade":grade,"grade_color":gc,"grade_label":gl,
            "flags_green":flags_green,"flags_red":flags_red,"flags_yellow":flags_yellow,
            "breakdown":breakdown,"market_cap":market_cap,"fdv":fdv,"fdv_ratio":ratio,
            "circ_pct":circ_pct,"vol_ratio":vol_ratio,"change_24h":change_24h,
            "change_7d":change_7d,"ath_change":ath_change}

# ─── FORMAT HELPERS ───────────────────────────────────────────────────────────
def fmt_usd(val):
    if not val: return "N/A"
    if val>=1e9: return f"${val/1e9:.2f}B"
    if val>=1e6: return f"${val/1e6:.2f}M"
    if val>=1e3: return f"${val/1e3:.1f}K"
    return f"${val:.4f}"

def fmt_price(val):
    if not val: return "N/A"
    if val>=1: return f"${val:,.4f}"
    if val>=0.001: return f"${val:.6f}"
    return f"${val:.8f}"

def pct_color(val): return "#3fb950" if (val or 0)>=0 else "#f85149"
def pct_str(val): return "N/A" if val is None else f"{'+'if val>=0 else''}{val:.2f}%"


CMC_BASE = "https://pro-api.coinmarketcap.com/v1"

@st.cache_data(ttl=1800)
def get_top_gainers_cmc():
    """Lấy top 30 token x2+ trong 3 ngày, market cap < $5M"""
    if not CMC_KEY:
        return None, "Chưa cấu hình CMC API key"
    try:
        r = requests.get(
            f"{CMC_BASE}/cryptocurrency/listings/latest",
            headers=CMC_HEADERS,
            params={
                "limit": 200,
                "sort": "percent_change_7d",
                "sort_dir": "desc",
                "market_cap_max": 10_000_000,
                "convert": "USD"
            },
            timeout=15
        )
        if r.status_code == 200:
            coins = r.json().get("data", [])
            gainers = []
            for c in coins:
                q = c.get("quote", {}).get("USD", {})
                change_3d = q.get("percent_change_72h", 0) or 0
                mcap = q.get("market_cap", 0) or 0
                volume = q.get("volume_24h", 0) or 0
                if change_3d >= 100 and 100_000 < mcap < 5_000_000 and volume > 10_000:
                    gainers.append({
                        "id": c.get("id"),
                        "name": c.get("name"),
                        "symbol": c.get("symbol"),
                        "slug": c.get("slug"),
                        "tags": c.get("tags", []),
                        "price": q.get("price", 0),
                        "change_24h": q.get("percent_change_24h", 0),
                        "change_3d": change_3d,
                        "market_cap": mcap,
                        "volume": volume,
                    })
            return sorted(gainers, key=lambda x: x["change_3d"], reverse=True)[:30], None
        elif r.status_code == 401:
            return None, "API key không hợp lệ"
        else:
            return None, f"Lỗi API: {r.status_code}"
    except Exception as e:
        return None, str(e)

def analyze_narrative(gainers):
    """Phân tích narrative từ danh sách gainers"""
    if not gainers:
        return {}
    tag_count = {}
    tag_tokens = {}
    # Normalize tags
    narrative_map = {
        "artificial-intelligence": "🤖 AI / Machine Learning",
        "ai-big-data": "🤖 AI / Machine Learning",
        "real-world-assets": "🏦 RWA (Real World Assets)",
        "rwa": "🏦 RWA (Real World Assets)",
        "depin": "📡 DePIN",
        "decentralized-physical-infrastructure": "📡 DePIN",
        "gaming": "🎮 GameFi",
        "play-to-earn": "🎮 GameFi",
        "decentralized-finance-defi": "💰 DeFi",
        "defi": "💰 DeFi",
        "layer-2": "⚡ Layer 2",
        "ethereum-ecosystem": "⚡ Layer 2",
        "memes": "🐸 Meme",
        "sports": "⚽ Sports",
        "nft": "🖼️ NFT",
        "metaverse": "🌐 Metaverse",
        "social-fi": "👥 SocialFi",
        "agent": "🤖 AI / Machine Learning",
        "ai-agents": "🤖 AI / Machine Learning",
    }
    for token in gainers:
        matched = set()
        for tag in token.get("tags", []):
            tag_lower = tag.lower().replace(" ", "-")
            for key, narrative in narrative_map.items():
                if key in tag_lower and narrative not in matched:
                    matched.add(narrative)
                    tag_count[narrative] = tag_count.get(narrative, 0) + 1
                    if narrative not in tag_tokens:
                        tag_tokens[narrative] = []
                    tag_tokens[narrative].append(token)
        if not matched:
            other = "🔮 Other"
            tag_count[other] = tag_count.get(other, 0) + 1
            if other not in tag_tokens:
                tag_tokens[other] = []
            tag_tokens[other].append(token)
    return dict(sorted(tag_count.items(), key=lambda x: x[1], reverse=True)), tag_tokens

@st.cache_data(ttl=1800)
def get_hidden_gems_by_narrative(narrative_tags):
    """Tìm token chưa pump cùng narrative"""
    if not CMC_KEY:
        return []
    try:
        r = requests.get(
            f"{CMC_BASE}/cryptocurrency/listings/latest",
            headers=CMC_HEADERS,
            params={
                "limit": 500,
                "sort": "volume_24h",
                "sort_dir": "desc",
                "market_cap_max": 1_000_000,
                "convert": "USD"
            },
            timeout=15
        )
        if r.status_code == 200:
            coins = r.json().get("data", [])
            gems = []
            for c in coins:
                q = c.get("quote", {}).get("USD", {})
                change_3d = q.get("percent_change_72h", 0) or 0
                change_24h = q.get("percent_change_24h", 0) or 0
                mcap = q.get("market_cap", 0) or 0
                volume = q.get("volume_24h", 0) or 0
                # Chưa pump mạnh
                if change_3d > 50 or change_24h > 30:
                    continue
                if mcap < 50_000 or volume < 5_000:
                    continue
                # Check narrative match
                tags = [t.lower() for t in c.get("tags", [])]
                match = any(nt in " ".join(tags) for nt in narrative_tags)
                if match:
                    vol_mcap = volume / mcap if mcap > 0 else 0
                    gems.append({
                        "name": c.get("name"),
                        "symbol": c.get("symbol"),
                        "tags": c.get("tags", [])[:3],
                        "price": q.get("price", 0),
                        "change_24h": change_24h,
                        "change_3d": change_3d,
                        "market_cap": mcap,
                        "volume": volume,
                        "vol_mcap": vol_mcap,
                    })
            # Sort by volume/mcap ratio (accumulation signal)
            return sorted(gems, key=lambda x: x["vol_mcap"], reverse=True)[:20]
    except:
        pass
    return []

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <p class="main-title">💎 Hidden Gem Hunter</p>
    <p style="color:#8b949e;font-size:0.95rem;margin-top:8px;">Phân tích tiềm năng token micro-cap · Kỹ thuật H4 · Dữ liệu realtime</p>
</div>
""", unsafe_allow_html=True)

col_input, col_btn = st.columns([4,1])
with col_input:
    query = st.text_input("", placeholder="🔍  Nhập tên token, symbol... (vd: AIA, LAB, COAI, BTC)", key="search_input", label_visibility="collapsed")
with col_btn:
    search_btn = st.button("Phân tích", use_container_width=True)

st.markdown("")

# ─── SEARCH ───────────────────────────────────────────────────────────────────
if search_btn and query:
    with st.spinner("🔍 Đang tìm kiếm..."):
        results = search_token(query)
    if not results:
        st.error("Không tìm thấy token.")
    else:
        coin = results[0]
        coin_id = coin["id"]
        with st.spinner(f"📊 Đang load data..."):
            data = get_token_data(coin_id)
            time.sleep(0.3)

        if not data or data.get("error") == "rate_limit":
            st.warning("⏳ Rate limit. Chờ 60 giây rồi thử lại.")
        elif data.get("error"):
            st.error(f"Lỗi: {data['error']}")
        else:
            result = score_token(data)
            md = data.get("market_data", {})
            price = md.get("current_price", {}).get("usd", 0)
            ath = md.get("ath", {}).get("usd", 0)
            volume = md.get("total_volume", {}).get("usd", 0)
            categories = data.get("categories", [])[:3]
            cat_badges = " ".join([f'<span class="badge badge-blue">{c}</span>' for c in categories if c])

            # Token header
            st.markdown(f"""
            <div class="token-header">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                    <img src="{data.get('image',{}).get('small','')}" width="48" style="border-radius:50%;">
                    <div>
                        <span class="token-name">{data.get('name','')}</span>
                        <span class="token-symbol">{data.get('symbol','').upper()}</span>
                    </div>
                </div>
                <div style="display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;">
                    <span class="price-big">{fmt_price(price)}</span>
                    <span style="color:{pct_color(result['change_24h'])};font-size:1.1rem;font-weight:600;">{pct_str(result['change_24h'])} (24h)</span>
                    <span style="color:{pct_color(result['change_7d'])};font-size:0.95rem;">{pct_str(result['change_7d'])} (7d)</span>
                </div>
                <div style="margin-top:10px;">{cat_badges}</div>
            </div>
            """, unsafe_allow_html=True)

            # Score cards
            c1,c2,c3,c4 = st.columns(4)
            with c1:
                st.markdown(f'<div class="score-card"><div class="score-number" style="color:{result["grade_color"]}">{result["grade"]}</div><div style="font-size:1.4rem;font-weight:600;color:{result["grade_color"]};margin-top:4px;">{result["score"]}/100</div><div class="score-label">{result["grade_label"]}</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="score-card"><div class="score-number" style="color:#58a6ff;font-size:1.8rem;">{fmt_usd(result["market_cap"])}</div><div class="score-label">Market Cap</div><div style="margin-top:8px;color:#8b949e;font-size:0.8rem;">FDV: {fmt_usd(result["fdv"])}</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="score-card"><div class="score-number" style="color:#d29922;font-size:1.8rem;">{result["fdv_ratio"]:.1f}x</div><div class="score-label">FDV / Market Cap</div><div style="margin-top:8px;color:#8b949e;font-size:0.8rem;">Circ: {result["circ_pct"]:.1f}%</div></div>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="score-card"><div class="score-number" style="color:#f85149;font-size:1.8rem;">{pct_str(result["ath_change"])}</div><div class="score-label">Từ ATH ({fmt_price(ath)})</div><div style="margin-top:8px;color:#8b949e;font-size:0.8rem;">Vol: {fmt_usd(volume)}</div></div>', unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Scoring flags
            col_left, col_right = st.columns([1,1])
            with col_left:
                st.markdown('<div class="section-title">📊 Phân tích Tokenomics</div>', unsafe_allow_html=True)
                for f in result["flags_green"]: st.markdown(f'<div class="flag-item flag-green">{f}</div>', unsafe_allow_html=True)
                for f in result["flags_yellow"]: st.markdown(f'<div class="flag-item flag-yellow">{f}</div>', unsafe_allow_html=True)
                for f in result["flags_red"]: st.markdown(f'<div class="flag-item flag-red">{f}</div>', unsafe_allow_html=True)
            with col_right:
                st.markdown('<div class="section-title">🔑 Score Breakdown</div>', unsafe_allow_html=True)
                max_scores = {"Market Cap":25,"FDV/Mcap Ratio":20,"Circ Supply %":20,"Volume/Mcap":15,"ATH Distance":10,"Community":10}
                breakdown = result["breakdown"]
                fig_score = go.Figure()
                fig_score.add_trace(go.Bar(y=list(breakdown.keys()), x=[max_scores[k] for k in breakdown], orientation='h', marker_color='#21262d'))
                fig_score.add_trace(go.Bar(y=list(breakdown.keys()), x=list(breakdown.values()), orientation='h',
                    marker_color=result["grade_color"],
                    text=[f"{s}/{max_scores[k]}" for k,s in breakdown.items()], textposition='outside',
                    textfont=dict(color='#e6edf3', size=11)))
                fig_score.update_layout(barmode='overlay', paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#8b949e',family='Inter'), showlegend=False, height=260,
                    margin=dict(l=0,r=60,t=0,b=0),
                    xaxis=dict(showgrid=False,showticklabels=False,zeroline=False),
                    yaxis=dict(showgrid=False,tickfont=dict(color='#e6edf3',size=11)))
                st.plotly_chart(fig_score, use_container_width=True)

            # ── TECHNICAL ANALYSIS SECTION ──
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">📈 Phân tích Kỹ thuật H4</div>', unsafe_allow_html=True)

            with st.spinner("⚙️ Đang tính toán indicators..."):
                ta = analyze_technicals(coin_id)

            if ta is None:
                st.info("Không đủ data OHLCV để phân tích kỹ thuật.")
            else:
                verdict_text, verdict_color, verdict_type = ta["ta_verdict"]
                verdict_class = f"ta-signal-{'bull' if verdict_type=='bull' else 'bear' if verdict_type=='bear' else 'neut'}"

                # Verdict banner
                st.markdown(f"""
                <div class="ta-signal-box {verdict_class}" style="margin-bottom:20px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <span style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;">Tổng hợp kỹ thuật H4</span>
                            <div style="font-size:1.4rem;font-weight:700;color:{verdict_color};margin-top:4px;">{verdict_text}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="color:#8b949e;font-size:0.8rem;">RSI (14)</div>
                            <div style="font-size:1.6rem;font-weight:700;color:{'#f85149' if ta['rsi_val']>70 else '#3fb950' if ta['rsi_val']<30 else '#58a6ff'}">{ta['rsi_val']:.1f}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Signal cards
                sig_cols = st.columns(2)
                for i, sig in enumerate(ta["signals"]):
                    css_class = f"ta-signal-{'bull' if sig['type']=='bull' else 'bear' if sig['type']=='bear' else 'neut'}"
                    with sig_cols[i % 2]:
                        st.markdown(f"""
                        <div class="ta-signal-box {css_class}">
                            <div style="font-weight:600;font-size:0.9rem;">{sig['icon']} {sig['label']}</div>
                            <div style="color:#8b949e;font-size:0.82rem;margin-top:4px;">{sig['detail']}</div>
                        </div>
                        """, unsafe_allow_html=True)

                # S/R Levels
                sr_col1, sr_col2 = st.columns(2)
                with sr_col1:
                    if ta["res_levels"]:
                        st.markdown('<div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;margin-bottom:8px;">🧱 Kháng cự</div>', unsafe_allow_html=True)
                        for r in ta["res_levels"][:3]:
                            st.markdown(f'<div class="ta-signal-box ta-signal-bear" style="padding:8px 14px;margin-bottom:6px;"><span style="font-weight:600;">{fmt_price(r)}</span></div>', unsafe_allow_html=True)
                with sr_col2:
                    if ta["sup_levels"]:
                        st.markdown('<div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;margin-bottom:8px;">🛡️ Hỗ trợ</div>', unsafe_allow_html=True)
                        for s in ta["sup_levels"][:3]:
                            st.markdown(f'<div class="ta-signal-box ta-signal-bull" style="padding:8px 14px;margin-bottom:6px;"><span style="font-weight:600;">{fmt_price(s)}</span></div>', unsafe_allow_html=True)

                # Chart
                st.markdown("<br>", unsafe_allow_html=True)
                fig_ta = render_ta_chart(ta, data.get("name",""))
                st.plotly_chart(fig_ta, use_container_width=True)

            # Description
            desc = data.get("description", {}).get("en", "")
            if desc:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="section-title">📝 Mô tả dự án</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="color:#8b949e;font-size:0.88rem;line-height:1.6;">{desc[:400]}{"..." if len(desc)>400 else ""}</div>', unsafe_allow_html=True)

            st.markdown('<div class="warning-box">⚠️ <strong>Disclaimer:</strong> Công cụ này chỉ hỗ trợ phân tích dữ liệu, KHÔNG phải lời khuyên đầu tư. Luôn verify thủ công trước khi vào lệnh.</div>', unsafe_allow_html=True)

# ─── TRENDING & MICROCAP TABS ─────────────────────────────────────────────────
st.markdown("<br><hr style='border-color:#21262d;'><br>", unsafe_allow_html=True)
tab1, tab2, tab3 = st.tabs(["🔥 Trending hôm nay", "💎 Micro-cap đáng chú ý (<$5M)", "🔍 Narrative Scanner"])

with tab1:
    trending = get_trending()
    if trending:
        cols_h = st.columns([0.4,2,1.2,1.2,1.2,1.5])
        for col,h in zip(cols_h,["#","Token","Giá","24h","Market Cap","Score"]):
            col.markdown(f'<div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;padding-bottom:8px;">{h}</div>', unsafe_allow_html=True)
        for i,item in enumerate(trending[:10]):
            c = item.get("item",{})
            d = c.get("data",{})
            price_usd = d.get("price",0)
            change_24h = d.get("price_change_percentage_24h",{}).get("usd",0)
            mcap = d.get("market_cap","")
            rank = c.get("market_cap_rank",9999)
            qs = "🔥 Early" if rank>500 else "👀 Watch" if rank>200 else "📊 Established"
            cols = st.columns([0.4,2,1.2,1.2,1.2,1.5])
            cols[0].markdown(f'<div style="color:#8b949e;padding-top:10px;">{i+1}</div>', unsafe_allow_html=True)
            cols[1].markdown(f'<div style="display:flex;align-items:center;gap:8px;padding-top:6px;"><img src="{c.get("small","")}" width="24" style="border-radius:50%;"><span style="font-weight:500;">{c.get("name","")}</span><span style="color:#8b949e;font-size:0.8rem;">{c.get("symbol","")}</span></div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div style="padding-top:10px;">{fmt_price(price_usd) if price_usd else "N/A"}</div>', unsafe_allow_html=True)
            cols[3].markdown(f'<div style="color:{pct_color(change_24h)};padding-top:10px;">{pct_str(change_24h)}</div>', unsafe_allow_html=True)
            cols[4].markdown(f'<div style="color:#8b949e;padding-top:10px;">{mcap or "N/A"}</div>', unsafe_allow_html=True)
            cols[5].markdown(f'<div style="padding-top:10px;">{qs}</div>', unsafe_allow_html=True)
    else:
        st.info("Đang tải trending...")

with tab2:
    st.markdown('<div style="color:#8b949e;font-size:0.85rem;margin-bottom:16px;">Market cap $100K–$5M · Volume đáng chú ý · Cập nhật mỗi 2 phút</div>', unsafe_allow_html=True)
    low_caps = get_new_listings()
    if low_caps:
        cols_h = st.columns([2,1.2,1.2,1.2,1.2,1.2])
        for col,h in zip(cols_h,["Token","Giá","24h","Market Cap","Volume","FDV"]):
            col.markdown(f'<div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;padding-bottom:8px;">{h}</div>', unsafe_allow_html=True)
        for coin in low_caps:
            change = coin.get("price_change_percentage_24h",0)
            cols = st.columns([2,1.2,1.2,1.2,1.2,1.2])
            cols[0].markdown(f'<div style="display:flex;align-items:center;gap:8px;padding-top:6px;"><img src="{coin.get("image","")}" width="22" style="border-radius:50%;"><span style="font-weight:500;font-size:0.9rem;">{coin.get("name","")}</span><span style="color:#8b949e;font-size:0.75rem;">{coin.get("symbol","").upper()}</span></div>', unsafe_allow_html=True)
            cols[1].markdown(f'<div style="padding-top:10px;font-size:0.9rem;">{fmt_price(coin.get("current_price",0))}</div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div style="color:{pct_color(change)};padding-top:10px;font-size:0.9rem;">{pct_str(change)}</div>', unsafe_allow_html=True)
            cols[3].markdown(f'<div style="padding-top:10px;font-size:0.9rem;">{fmt_usd(coin.get("market_cap",0))}</div>', unsafe_allow_html=True)
            cols[4].markdown(f'<div style="padding-top:10px;font-size:0.9rem;color:#8b949e;">{fmt_usd(coin.get("total_volume",0))}</div>', unsafe_allow_html=True)
            cols[5].markdown(f'<div style="padding-top:10px;font-size:0.9rem;color:#8b949e;">{fmt_usd(coin.get("fully_diluted_valuation",0))}</div>', unsafe_allow_html=True)
    else:
        st.info("Đang tải micro-cap data...")


with tab3:
    st.markdown("""
    <div style="background:#161b22;border:1px solid #21262d;border-radius:10px;padding:16px 20px;margin-bottom:20px;">
        <div style="font-size:0.9rem;color:#e6edf3;font-weight:600;">🔍 Narrative Scanner</div>
        <div style="color:#8b949e;font-size:0.82rem;margin-top:6px;">
            Tự động phát hiện narrative đang pump → tìm gem chưa pump cùng sector · Cập nhật mỗi 30 phút
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not CMC_KEY:
        st.error("⚠️ Chưa cấu hình CMC_API_KEY trong Streamlit Secrets.")
    else:
        with st.spinner("📊 Đang phân tích top gainers 3 ngày..."):
            gainers, err = get_top_gainers_cmc()

        if err:
            st.error(f"Lỗi: {err}")
        elif not gainers:
            st.info("Không tìm thấy token nào x2+ trong 3 ngày với market cap < $5M.")
        else:
            # Narrative analysis
            narrative_counts, narrative_tokens = analyze_narrative(gainers)

            # Top narrative banner
            if narrative_counts:
                top_narrative = list(narrative_counts.keys())[0]
                top_count = list(narrative_counts.values())[0]
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#1a2e1a,#0d1117);border:1px solid #3fb950;border-radius:12px;padding:20px;margin-bottom:20px;text-align:center;">
                    <div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.1em;">Narrative đang HOT nhất</div>
                    <div style="font-size:2rem;font-weight:700;color:#3fb950;margin-top:8px;">{top_narrative}</div>
                    <div style="color:#8b949e;font-size:0.85rem;margin-top:4px;">{top_count} token x2+ trong 3 ngày · {len(gainers)} gainers tổng</div>
                </div>
                """, unsafe_allow_html=True)

            # Narrative breakdown
            st.markdown('<div class="section-title">📊 Phân bổ Narrative trong top gainers</div>', unsafe_allow_html=True)
            narr_cols = st.columns(min(len(narrative_counts), 4))
            for i, (narr, count) in enumerate(list(narrative_counts.items())[:4]):
                pct = count / len(gainers) * 100
                with narr_cols[i]:
                    st.markdown(f"""
                    <div class="score-card">
                        <div style="font-size:1.5rem;">{narr.split()[0]}</div>
                        <div style="font-size:1.2rem;font-weight:700;color:#58a6ff;margin-top:4px;">{count} tokens</div>
                        <div style="color:#8b949e;font-size:0.8rem;">{narr.split(' ',1)[1] if ' ' in narr else narr}</div>
                        <div style="color:#3fb950;font-size:0.75rem;margin-top:4px;">{pct:.0f}% gainers</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Top gainers table
            st.markdown('<div class="section-title">🚀 Top 30 token x2+ (3 ngày) · Market cap < $5M</div>', unsafe_allow_html=True)
            cols_h = st.columns([2, 1.2, 1.2, 1.2, 1.2, 2])
            for col, h in zip(cols_h, ["Token", "Giá", "3 ngày", "24h", "Market Cap", "Narrative"]):
                col.markdown(f'<div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;padding-bottom:8px;">{h}</div>', unsafe_allow_html=True)

            for token in gainers:
                cols = st.columns([2, 1.2, 1.2, 1.2, 1.2, 2])
                cols[0].markdown(f'<div style="padding-top:8px;font-weight:500;">{token["name"]} <span style="color:#8b949e;font-size:0.75rem;">{token["symbol"]}</span></div>', unsafe_allow_html=True)
                cols[1].markdown(f'<div style="padding-top:8px;font-size:0.9rem;">{fmt_price(token["price"])}</div>', unsafe_allow_html=True)
                cols[2].markdown(f'<div style="color:#3fb950;padding-top:8px;font-weight:600;">+{token["change_3d"]:.0f}%</div>', unsafe_allow_html=True)
                cols[3].markdown(f'<div style="color:{pct_color(token["change_24h"])};padding-top:8px;">{pct_str(token["change_24h"])}</div>', unsafe_allow_html=True)
                cols[4].markdown(f'<div style="padding-top:8px;color:#8b949e;font-size:0.9rem;">{fmt_usd(token["market_cap"])}</div>', unsafe_allow_html=True)
                tags_html = " ".join([f'<span class="badge badge-purple">{t[:12]}</span>' for t in token["tags"][:2]])
                cols[5].markdown(f'<div style="padding-top:6px;">{tags_html}</div>', unsafe_allow_html=True)

            # Hidden gems section
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">💎 Gem chưa pump — cùng narrative đang hot</div>', unsafe_allow_html=True)

            # Get top narrative tags for searching
            if narrative_counts:
                top_narr = list(narrative_counts.keys())[0].lower()
                narr_tag_map = {
                    "ai": ["artificial-intelligence", "ai", "agent"],
                    "rwa": ["real-world-assets", "rwa"],
                    "depin": ["depin", "infrastructure"],
                    "gamefi": ["gaming", "play-to-earn", "game"],
                    "defi": ["defi", "decentralized-finance"],
                    "meme": ["memes", "meme"],
                    "sports": ["sports", "fan-token"],
                }
                search_tags = ["ai", "agent"]  # default
                for key, tags in narr_tag_map.items():
                    if key in top_narr:
                        search_tags = tags
                        break

                with st.spinner(f"🔍 Đang scan gem chưa pump trong narrative {list(narrative_counts.keys())[0]}..."):
                    gems = get_hidden_gems_by_narrative(search_tags)

                if gems:
                    st.markdown(f'<div style="color:#8b949e;font-size:0.82rem;margin-bottom:12px;">Tìm thấy {len(gems)} token tiềm năng · Sắp xếp theo Volume/Mcap ratio (tín hiệu accumulation)</div>', unsafe_allow_html=True)
                    cols_h2 = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1.2])
                    for col, h in zip(cols_h2, ["Token", "Giá", "24h", "3 ngày", "Market Cap", "Vol/Mcap"]):
                        col.markdown(f'<div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;padding-bottom:8px;">{h}</div>', unsafe_allow_html=True)

                    for gem in gems:
                        vol_ratio = gem["vol_mcap"]
                        vol_signal = "🔥" if vol_ratio > 0.5 else "👀" if vol_ratio > 0.2 else "📊"
                        cols = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1.2])
                        cols[0].markdown(f'<div style="padding-top:8px;font-weight:500;">{gem["name"]} <span style="color:#8b949e;font-size:0.75rem;">{gem["symbol"]}</span></div>', unsafe_allow_html=True)
                        cols[1].markdown(f'<div style="padding-top:8px;font-size:0.9rem;">{fmt_price(gem["price"])}</div>', unsafe_allow_html=True)
                        cols[2].markdown(f'<div style="color:{pct_color(gem["change_24h"])};padding-top:8px;">{pct_str(gem["change_24h"])}</div>', unsafe_allow_html=True)
                        cols[3].markdown(f'<div style="color:{pct_color(gem["change_3d"])};padding-top:8px;">{pct_str(gem["change_3d"])}</div>', unsafe_allow_html=True)
                        cols[4].markdown(f'<div style="padding-top:8px;color:#8b949e;font-size:0.9rem;">{fmt_usd(gem["market_cap"])}</div>', unsafe_allow_html=True)
                        cols[5].markdown(f'<div style="padding-top:8px;">{vol_signal} {vol_ratio:.2f}x</div>', unsafe_allow_html=True)
                else:
                    st.info("Không tìm thấy gem phù hợp. Thử lại sau.")


st.markdown('<br><div style="text-align:center;color:#484f58;font-size:0.8rem;padding:20px 0;">💎 Hidden Gem Hunter · H4 TA · CoinGecko API · Research only</div>', unsafe_allow_html=True)
