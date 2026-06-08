import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time

# ─── CONFIG ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="💎 Hidden Gem Hunter",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: #0d1117;
        color: #e6edf3;
    }

    .main-header {
        background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
        border: 1px solid #21262d;
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 24px;
        text-align: center;
    }

    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #58a6ff, #a371f7, #f78166);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }

    .main-subtitle {
        color: #8b949e;
        font-size: 0.95rem;
        margin-top: 8px;
    }

    .score-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        height: 100%;
    }

    .score-number {
        font-size: 3rem;
        font-weight: 700;
        line-height: 1;
    }

    .score-label {
        color: #8b949e;
        font-size: 0.8rem;
        margin-top: 6px;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .metric-card {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }

    .metric-label {
        color: #8b949e;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .metric-value {
        font-size: 1.2rem;
        font-weight: 600;
        color: #e6edf3;
        margin-top: 4px;
    }

    .flag-item {
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 8px;
        font-size: 0.88rem;
        display: flex;
        align-items: flex-start;
        gap: 8px;
    }

    .flag-green { background: #0d2818; border-left: 3px solid #3fb950; color: #7ee787; }
    .flag-red   { background: #2d1212; border-left: 3px solid #f85149; color: #ff7b72; }
    .flag-yellow{ background: #2d2208; border-left: 3px solid #d29922; color: #e3b341; }

    .section-title {
        font-size: 1rem;
        font-weight: 600;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 14px;
        padding-bottom: 8px;
        border-bottom: 1px solid #21262d;
    }

    .token-header {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
    }

    .token-name {
        font-size: 1.8rem;
        font-weight: 700;
        color: #e6edf3;
    }

    .token-symbol {
        background: #21262d;
        color: #58a6ff;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 10px;
        vertical-align: middle;
    }

    .price-big {
        font-size: 2.2rem;
        font-weight: 700;
        color: #e6edf3;
    }

    .trending-row {
        background: #161b22;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: border-color 0.2s;
    }

    .trending-row:hover {
        border-color: #58a6ff;
    }

    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
    }

    .badge-green { background: #0d2818; color: #3fb950; }
    .badge-red   { background: #2d1212; color: #f85149; }
    .badge-blue  { background: #0d2137; color: #58a6ff; }
    .badge-purple{ background: #1e1037; color: #a371f7; }

    .divider {
        border: none;
        border-top: 1px solid #21262d;
        margin: 20px 0;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Input styling */
    .stTextInput input {
        background: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 10px !important;
        color: #e6edf3 !important;
        font-size: 1rem !important;
        padding: 12px 16px !important;
    }

    .stTextInput input:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 2px rgba(88,166,255,0.15) !important;
    }

    .stButton button {
        background: linear-gradient(135deg, #1f6feb, #388bfd) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 12px 28px !important;
        font-size: 1rem !important;
        width: 100%;
        transition: opacity 0.2s !important;
    }

    .stButton button:hover {
        opacity: 0.85 !important;
    }

    .warning-box {
        background: #2d1a00;
        border: 1px solid #d29922;
        border-radius: 10px;
        padding: 14px 18px;
        font-size: 0.85rem;
        color: #e3b341;
        margin-top: 16px;
    }
</style>
""", unsafe_allow_html=True)


# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def search_token(query: str):
    """Search token by name/symbol"""
    try:
        r = requests.get(f"{COINGECKO_BASE}/search", params={"query": query}, timeout=10)
        if r.status_code == 200:
            return r.json().get("coins", [])
    except:
        pass
    return []

@st.cache_data(ttl=60)
def get_token_data(coin_id: str):
    """Get full token data from CoinGecko"""
    try:
        r = requests.get(
            f"{COINGECKO_BASE}/coins/{coin_id}",
            params={
                "localization": "false",
                "tickers": "true",
                "market_data": "true",
                "community_data": "true",
                "developer_data": "false",
            },
            timeout=15
        )
        if r.status_code == 200:
            return r.json()
        elif r.status_code == 429:
            return {"error": "rate_limit"}
    except Exception as e:
        return {"error": str(e)}
    return None

@st.cache_data(ttl=300)
def get_trending():
    """Get trending coins"""
    try:
        r = requests.get(f"{COINGECKO_BASE}/search/trending", timeout=10)
        if r.status_code == 200:
            return r.json().get("coins", [])
    except:
        pass
    return []

@st.cache_data(ttl=120)
def get_new_listings():
    """Get recently added coins"""
    try:
        r = requests.get(
            f"{COINGECKO_BASE}/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "id_asc",
                "per_page": 50,
                "page": 1,
                "sparkline": "false",
            },
            timeout=10
        )
        # Actually get low market cap tokens
        r2 = requests.get(
            f"{COINGECKO_BASE}/coins/markets",
            params={
                "vs_currency": "usd",
                "order": "market_cap_asc",
                "per_page": 100,
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "24h",
            },
            timeout=10
        )
        if r2.status_code == 200:
            data = r2.json()
            # Filter market cap < $5M and has volume
            filtered = [
                c for c in data
                if c.get("market_cap") and 100_000 < c["market_cap"] < 5_000_000
                and c.get("total_volume", 0) > 10_000
            ]
            return filtered[:20]
    except:
        pass
    return []


def score_token(data: dict) -> dict:
    """
    Score token tiềm năng hidden gem theo framework:
    - Market cap (25đ)
    - FDV/Mcap ratio (20đ)
    - Circ supply % (20đ)
    - Volume/Mcap ratio (15đ)
    - Price from ATH (10đ)
    - Community (10đ)
    """
    score = 0
    flags_green = []
    flags_red = []
    flags_yellow = []
    breakdown = {}

    md = data.get("market_data", {})

    market_cap = md.get("market_cap", {}).get("usd") or 0
    fdv = md.get("fully_diluted_valuation", {}).get("usd") or 0
    circ_supply = md.get("circulating_supply") or 0
    total_supply = md.get("total_supply") or 0
    max_supply = md.get("max_supply") or total_supply or circ_supply
    volume_24h = md.get("total_volume", {}).get("usd") or 0
    price = md.get("current_price", {}).get("usd") or 0
    ath = md.get("ath", {}).get("usd") or 0
    ath_change = md.get("ath_change_percentage", {}).get("usd") or 0
    change_24h = md.get("price_change_percentage_24h") or 0
    change_7d = md.get("price_change_percentage_7d") or 0

    # 1. Market Cap (25đ)
    if 0 < market_cap < 1_000_000:
        s = 25
        flags_green.append("🎯 Market cap < $1M — vùng micro-cap, tiềm năng x lớn")
    elif market_cap < 5_000_000:
        s = 18
        flags_green.append("✅ Market cap < $5M — low-cap, còn room tăng tốt")
    elif market_cap < 20_000_000:
        s = 10
        flags_yellow.append("⚠️ Market cap $5M–$20M — small-cap, upside vẫn còn")
    elif market_cap < 100_000_000:
        s = 4
        flags_yellow.append("⚠️ Market cap $20M–$100M — mid-cap, khó x nhiều")
    else:
        s = 0
        flags_red.append("❌ Market cap > $100M — đã lớn, upside hạn chế")
    score += s
    breakdown["Market Cap"] = s

    # 2. FDV/Mcap Ratio (20đ)
    if fdv > 0 and market_cap > 0:
        ratio = fdv / market_cap
        if ratio < 3:
            s = 20
            flags_green.append(f"✅ FDV/Mcap = {ratio:.1f}x — tokenomics lành mạnh, ít dilution")
        elif ratio < 7:
            s = 12
            flags_yellow.append(f"⚠️ FDV/Mcap = {ratio:.1f}x — dilution trung bình, cần theo dõi vesting")
        elif ratio < 15:
            s = 5
            flags_red.append(f"🚨 FDV/Mcap = {ratio:.1f}x — dilution cao, unlock sẽ tạo selling pressure")
        else:
            s = 0
            flags_red.append(f"❌ FDV/Mcap = {ratio:.1f}x — NGUY HIỂM, phần lớn token chưa unlock")
    else:
        s = 10
        flags_yellow.append("⚠️ Không có data FDV — không đánh giá được tokenomics")
        ratio = 0
    score += s
    breakdown["FDV/Mcap Ratio"] = s

    # 3. Circulating Supply % (20đ)
    if max_supply > 0 and circ_supply > 0:
        circ_pct = (circ_supply / max_supply) * 100
        if circ_pct < 15:
            s = 20
            flags_green.append(f"🚀 Circ supply chỉ {circ_pct:.1f}% — supply thấp, dễ pump")
        elif circ_pct < 30:
            s = 15
            flags_green.append(f"✅ Circ supply {circ_pct:.1f}% — supply còn thấp")
        elif circ_pct < 60:
            s = 8
            flags_yellow.append(f"⚠️ Circ supply {circ_pct:.1f}% — trung bình")
        else:
            s = 3
            flags_yellow.append(f"⚠️ Circ supply {circ_pct:.1f}% — phần lớn đã unlock")
    else:
        s = 5
        circ_pct = 0
        flags_yellow.append("⚠️ Không có data supply")
    score += s
    breakdown["Circ Supply %"] = s

    # 4. Volume/Mcap Ratio (15đ) — liquidity & interest
    if market_cap > 0 and volume_24h > 0:
        vol_ratio = volume_24h / market_cap
        if 0.1 < vol_ratio < 1.0:
            s = 15
            flags_green.append(f"✅ Volume/Mcap = {vol_ratio:.2f} — liquidity tốt, có trading activity")
        elif vol_ratio >= 1.0:
            s = 8
            flags_yellow.append(f"⚠️ Volume/Mcap = {vol_ratio:.2f} — volume rất cao, có thể đang pump")
        elif vol_ratio > 0.02:
            s = 8
            flags_yellow.append(f"⚠️ Volume/Mcap = {vol_ratio:.2f} — volume thấp, liquidity mỏng")
        else:
            s = 2
            flags_red.append(f"❌ Volume/Mcap = {vol_ratio:.4f} — volume gần chết, exit rất khó")
    else:
        s = 0
        vol_ratio = 0
        flags_red.append("❌ Không có volume — không trade được")
    score += s
    breakdown["Volume/Mcap"] = s

    # 5. Distance from ATH (10đ) — còn room không
    if ath_change < -90:
        s = 10
        flags_green.append(f"💀 -99%+ từ ATH — đang ở đáy sâu, nếu recover sẽ x lớn")
    elif ath_change < -75:
        s = 8
        flags_green.append(f"📉 -{abs(ath_change):.0f}% từ ATH — vùng thấp, upside potential cao")
    elif ath_change < -50:
        s = 5
        flags_yellow.append(f"⚠️ -{abs(ath_change):.0f}% từ ATH — đã giảm nhiều")
    elif ath_change < -20:
        s = 2
        flags_yellow.append(f"⚠️ -{abs(ath_change):.0f}% từ ATH — gần ATH, upside hạn chế hơn")
    else:
        s = 0
        flags_red.append(f"❌ Chỉ -{abs(ath_change):.0f}% từ ATH — đang near ATH, rủi ro cao")
    score += s
    breakdown["ATH Distance"] = s

    # 6. Community / Social (10đ)
    comm = data.get("community_data", {})
    twitter = comm.get("twitter_followers") or 0
    telegram = comm.get("telegram_channel_user_count") or 0
    total_social = twitter + telegram

    if 1_000 < total_social < 50_000:
        s = 10
        flags_green.append(f"✅ Community nhỏ ({total_social:,} followers) — chưa mainstream, còn early")
    elif total_social <= 1_000:
        s = 6
        flags_yellow.append(f"⚠️ Community rất nhỏ ({total_social:,}) — cực early hoặc chết")
    elif total_social < 200_000:
        s = 5
        flags_yellow.append(f"⚠️ Community trung bình ({total_social:,}) — đang phát triển")
    else:
        s = 2
        flags_yellow.append(f"⚠️ Community lớn ({total_social:,}) — có thể đã được discover")
    score += s
    breakdown["Community"] = s

    # ─── Grade ───
    if score >= 80:
        grade = "S"
        grade_color = "#a371f7"
        grade_label = "Tiềm năng CỰC CAO"
    elif score >= 65:
        grade = "A"
        grade_color = "#3fb950"
        grade_label = "Tiềm năng CAO"
    elif score >= 50:
        grade = "B"
        grade_color = "#58a6ff"
        grade_label = "Tiềm năng TRUNG BÌNH"
    elif score >= 35:
        grade = "C"
        grade_color = "#d29922"
        grade_label = "Tiềm năng THẤP"
    else:
        grade = "D"
        grade_color = "#f85149"
        grade_label = "Tiềm năng RẤT THẤP / Nguy hiểm"

    return {
        "score": score,
        "grade": grade,
        "grade_color": grade_color,
        "grade_label": grade_label,
        "flags_green": flags_green,
        "flags_red": flags_red,
        "flags_yellow": flags_yellow,
        "breakdown": breakdown,
        "market_cap": market_cap,
        "fdv": fdv,
        "fdv_ratio": ratio if fdv > 0 else 0,
        "circ_pct": circ_pct,
        "vol_ratio": vol_ratio if volume_24h > 0 else 0,
        "change_24h": change_24h,
        "change_7d": change_7d,
        "ath_change": ath_change,
    }


def fmt_usd(val):
    if not val or val == 0:
        return "N/A"
    if val >= 1_000_000_000:
        return f"${val/1_000_000_000:.2f}B"
    if val >= 1_000_000:
        return f"${val/1_000_000:.2f}M"
    if val >= 1_000:
        return f"${val/1_000:.1f}K"
    return f"${val:.4f}"

def fmt_price(val):
    if not val:
        return "N/A"
    if val >= 1:
        return f"${val:,.4f}"
    if val >= 0.001:
        return f"${val:.6f}"
    return f"${val:.8f}"

def pct_color(val):
    if val is None:
        return "#8b949e"
    return "#3fb950" if val >= 0 else "#f85149"

def pct_str(val):
    if val is None:
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.2f}%"


# ─── UI ───────────────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header">
    <p class="main-title">💎 Hidden Gem Hunter</p>
    <p class="main-subtitle">Phân tích tiềm năng token micro-cap · Dữ liệu realtime từ CoinGecko</p>
</div>
""", unsafe_allow_html=True)

# Search bar
col_input, col_btn = st.columns([4, 1])
with col_input:
    query = st.text_input(
        label="",
        placeholder="🔍  Nhập tên token, symbol... (vd: AIA, LAB, COAI, bitcoin)",
        key="search_input",
        label_visibility="collapsed"
    )
with col_btn:
    search_btn = st.button("Phân tích", use_container_width=True)

st.markdown("")

# ─── SEARCH RESULT ────────────────────────────────────────────────────────────
if search_btn and query:
    with st.spinner("🔍 Đang tìm kiếm..."):
        results = search_token(query)

    if not results:
        st.error("Không tìm thấy token. Thử nhập tên khác.")
    else:
        # Pick best match
        coin = results[0]
        coin_id = coin["id"]

        with st.spinner(f"📊 Đang load data cho **{coin['name']}**..."):
            data = get_token_data(coin_id)
            time.sleep(0.5)

        if not data or data.get("error") == "rate_limit":
            st.warning("⏳ CoinGecko rate limit. Vui lòng chờ 60 giây rồi thử lại.")
        elif data.get("error"):
            st.error(f"Lỗi: {data['error']}")
        else:
            result = score_token(data)
            md = data.get("market_data", {})
            price = md.get("current_price", {}).get("usd", 0)
            ath = md.get("ath", {}).get("usd", 0)
            volume = md.get("total_volume", {}).get("usd", 0)

            # ── Token Header ──
            categories = data.get("categories", [])[:3]
            cat_badges = " ".join([f'<span class="badge badge-blue">{c}</span>' for c in categories if c])

            st.markdown(f"""
            <div class="token-header">
                <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
                    <img src="{data.get('image',{}).get('small','')}" width="48" style="border-radius:50%;">
                    <div>
                        <span class="token-name">{data.get('name','')}</span>
                        <span class="token-symbol">{data.get('symbol','').upper()}</span>
                    </div>
                </div>
                <div style="display:flex; align-items:baseline; gap:16px; flex-wrap:wrap;">
                    <span class="price-big">{fmt_price(price)}</span>
                    <span style="color:{pct_color(result['change_24h'])}; font-size:1.1rem; font-weight:600;">
                        {pct_str(result['change_24h'])} (24h)
                    </span>
                    <span style="color:{pct_color(result['change_7d'])}; font-size:0.95rem;">
                        {pct_str(result['change_7d'])} (7d)
                    </span>
                </div>
                <div style="margin-top:10px;">{cat_badges}</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Score + Metrics ──
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score-number" style="color:{result['grade_color']}">{result['grade']}</div>
                    <div style="font-size:1.4rem; font-weight:600; color:{result['grade_color']}; margin-top:4px;">{result['score']}/100</div>
                    <div class="score-label">{result['grade_label']}</div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score-number" style="color:#58a6ff; font-size:1.8rem;">{fmt_usd(result['market_cap'])}</div>
                    <div class="score-label">Market Cap</div>
                    <div style="margin-top:8px; color:#8b949e; font-size:0.8rem;">FDV: {fmt_usd(result['fdv'])}</div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score-number" style="color:#d29922; font-size:1.8rem;">{result['fdv_ratio']:.1f}x</div>
                    <div class="score-label">FDV / Market Cap</div>
                    <div style="margin-top:8px; color:#8b949e; font-size:0.8rem;">Circ Supply: {result['circ_pct']:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="score-card">
                    <div class="score-number" style="color:#f85149; font-size:1.8rem;">{pct_str(result['ath_change'])}</div>
                    <div class="score-label">Từ ATH ({fmt_price(ath)})</div>
                    <div style="margin-top:8px; color:#8b949e; font-size:0.8rem;">Vol 24h: {fmt_usd(volume)}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Score Breakdown Chart + Flags ──
            col_left, col_right = st.columns([1, 1])

            with col_left:
                st.markdown('<div class="section-title">📊 Phân tích điểm chi tiết</div>', unsafe_allow_html=True)

                breakdown = result["breakdown"]
                max_scores = {"Market Cap": 25, "FDV/Mcap Ratio": 20, "Circ Supply %": 20,
                              "Volume/Mcap": 15, "ATH Distance": 10, "Community": 10}

                categories_chart = list(breakdown.keys())
                scores_chart = list(breakdown.values())
                max_chart = [max_scores[k] for k in categories_chart]

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=categories_chart,
                    x=max_chart,
                    name="Max",
                    orientation='h',
                    marker_color='#21262d',
                ))
                fig.add_trace(go.Bar(
                    y=categories_chart,
                    x=scores_chart,
                    name="Score",
                    orientation='h',
                    marker_color=[result['grade_color']] * len(scores_chart),
                    text=[f"{s}/{m}" for s, m in zip(scores_chart, max_chart)],
                    textposition='outside',
                    textfont=dict(color='#e6edf3', size=11),
                ))
                fig.update_layout(
                    barmode='overlay',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#8b949e', family='Inter'),
                    showlegend=False,
                    margin=dict(l=0, r=60, t=0, b=0),
                    height=280,
                    xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
                    yaxis=dict(showgrid=False, tickfont=dict(color='#e6edf3', size=11)),
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_right:
                st.markdown('<div class="section-title">🚦 Tín hiệu phân tích</div>', unsafe_allow_html=True)

                for f in result["flags_green"]:
                    st.markdown(f'<div class="flag-item flag-green">{f}</div>', unsafe_allow_html=True)
                for f in result["flags_yellow"]:
                    st.markdown(f'<div class="flag-item flag-yellow">{f}</div>', unsafe_allow_html=True)
                for f in result["flags_red"]:
                    st.markdown(f'<div class="flag-item flag-red">{f}</div>', unsafe_allow_html=True)

            # ── Exchanges ──
            tickers = data.get("tickers", [])[:6]
            if tickers:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="section-title">🏦 Đang giao dịch trên</div>', unsafe_allow_html=True)
                exchange_cols = st.columns(min(len(tickers), 3))
                for i, ticker in enumerate(tickers[:3]):
                    exchange = ticker.get("market", {}).get("name", "Unknown")
                    pair = f"{ticker.get('base','')}/{ticker.get('target','')}"
                    vol = ticker.get("converted_volume", {}).get("usd", 0)
                    with exchange_cols[i]:
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-label">{exchange}</div>
                            <div class="metric-value">{pair}</div>
                            <div style="color:#8b949e; font-size:0.8rem; margin-top:4px;">Vol: {fmt_usd(vol)}</div>
                        </div>
                        """, unsafe_allow_html=True)

            # ── Description ──
            desc = data.get("description", {}).get("en", "")
            if desc:
                desc_clean = desc[:400].replace("<a href=", "<a target='_blank' href=")
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="section-title">📝 Mô tả dự án</div>', unsafe_allow_html=True)
                st.markdown(f'<div style="color:#8b949e; font-size:0.88rem; line-height:1.6;">{desc_clean}{"..." if len(desc)>400 else ""}</div>', unsafe_allow_html=True)

            # Warning
            st.markdown("""
            <div class="warning-box">
                ⚠️ <strong>Disclaimer:</strong> Công cụ này chỉ hỗ trợ phân tích dữ liệu, KHÔNG phải lời khuyên đầu tư.
                Micro-cap tokens có rủi ro cực cao — chỉ dùng vốn nhàn rỗi, luôn verify thủ công trước khi vào lệnh.
            </div>
            """, unsafe_allow_html=True)


# ─── TRENDING & LOW CAP SECTION ───────────────────────────────────────────────
st.markdown("<br><hr style='border-color:#21262d;'><br>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔥 Trending hôm nay", "💎 Micro-cap đáng chú ý (<$5M)"])

with tab1:
    trending = get_trending()
    if trending:
        cols_header = st.columns([0.4, 2, 1.2, 1.2, 1.2, 1.5])
        headers = ["#", "Token", "Giá", "24h", "Market Cap", "Score Tiềm Năng"]
        for col, h in zip(cols_header, headers):
            col.markdown(f'<div style="color:#8b949e; font-size:0.75rem; text-transform:uppercase; padding-bottom:8px;">{h}</div>', unsafe_allow_html=True)

        for i, item in enumerate(trending[:10]):
            coin_info = item.get("item", {})
            name = coin_info.get("name", "")
            symbol = coin_info.get("symbol", "")
            thumb = coin_info.get("small", "")
            price_btc = coin_info.get("price_btc", 0)
            data_td = coin_info.get("data", {})
            price_usd = data_td.get("price", 0)
            change_24h = data_td.get("price_change_percentage_24h", {}).get("usd", 0)
            mcap = data_td.get("market_cap", "")

            # Quick score based on available data
            mcap_num = coin_info.get("market_cap_rank", 9999)
            if mcap_num > 500:
                quick_score = "🔥 Early"
            elif mcap_num > 200:
                quick_score = "👀 Watch"
            else:
                quick_score = "📊 Established"

            cols = st.columns([0.4, 2, 1.2, 1.2, 1.2, 1.5])
            cols[0].markdown(f'<div style="color:#8b949e; padding-top:10px;">{i+1}</div>', unsafe_allow_html=True)
            cols[1].markdown(f"""
                <div style="display:flex; align-items:center; gap:8px; padding-top:6px;">
                    <img src="{thumb}" width="24" style="border-radius:50%;">
                    <span style="font-weight:500;">{name}</span>
                    <span style="color:#8b949e; font-size:0.8rem;">{symbol}</span>
                </div>
            """, unsafe_allow_html=True)
            cols[2].markdown(f'<div style="padding-top:10px;">{fmt_price(price_usd) if price_usd else "N/A"}</div>', unsafe_allow_html=True)
            cols[3].markdown(f'<div style="color:{pct_color(change_24h)}; padding-top:10px;">{pct_str(change_24h)}</div>', unsafe_allow_html=True)
            cols[4].markdown(f'<div style="color:#8b949e; padding-top:10px;">{mcap or "N/A"}</div>', unsafe_allow_html=True)
            cols[5].markdown(f'<div style="padding-top:10px;">{quick_score}</div>', unsafe_allow_html=True)
    else:
        st.info("Đang tải trending data...")

with tab2:
    st.markdown('<div style="color:#8b949e; font-size:0.85rem; margin-bottom:16px;">Các token market cap $100K–$5M có volume đáng chú ý · Cập nhật mỗi 2 phút</div>', unsafe_allow_html=True)

    low_caps = get_new_listings()
    if low_caps:
        cols_header = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1.2])
        for col, h in zip(cols_header, ["Token", "Giá", "24h", "Market Cap", "Volume", "FDV"]):
            col.markdown(f'<div style="color:#8b949e; font-size:0.75rem; text-transform:uppercase; padding-bottom:8px;">{h}</div>', unsafe_allow_html=True)

        for coin in low_caps:
            change = coin.get("price_change_percentage_24h", 0)
            cols = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1.2])
            cols[0].markdown(f"""
                <div style="display:flex; align-items:center; gap:8px; padding-top:6px;">
                    <img src="{coin.get('image','')}" width="22" style="border-radius:50%;">
                    <span style="font-weight:500; font-size:0.9rem;">{coin.get('name','')}</span>
                    <span style="color:#8b949e; font-size:0.75rem;">{coin.get('symbol','').upper()}</span>
                </div>
            """, unsafe_allow_html=True)
            cols[1].markdown(f'<div style="padding-top:10px; font-size:0.9rem;">{fmt_price(coin.get("current_price",0))}</div>', unsafe_allow_html=True)
            cols[2].markdown(f'<div style="color:{pct_color(change)}; padding-top:10px; font-size:0.9rem;">{pct_str(change)}</div>', unsafe_allow_html=True)
            cols[3].markdown(f'<div style="padding-top:10px; font-size:0.9rem;">{fmt_usd(coin.get("market_cap",0))}</div>', unsafe_allow_html=True)
            cols[4].markdown(f'<div style="padding-top:10px; font-size:0.9rem; color:#8b949e;">{fmt_usd(coin.get("total_volume",0))}</div>', unsafe_allow_html=True)
            cols[5].markdown(f'<div style="padding-top:10px; font-size:0.9rem; color:#8b949e;">{fmt_usd(coin.get("fully_diluted_valuation",0))}</div>', unsafe_allow_html=True)
    else:
        st.info("Đang tải data micro-cap...")

# Footer
st.markdown("""
<br>
<div style="text-align:center; color:#484f58; font-size:0.8rem; padding: 20px 0;">
    💎 Hidden Gem Hunter · Data từ CoinGecko API · Chỉ dùng cho mục đích nghiên cứu
</div>
""", unsafe_allow_html=True)
