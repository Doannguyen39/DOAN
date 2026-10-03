"""
Tầng đọc ĐA KHUNG cho hệ K23 — gộp nến + trạng thái vòng cung.

Tách riêng khỏi bot QML: bot import dùng, KHÔNG sửa logic bắn kèo.
Nguyên tắc: module này chỉ ĐO và BÀY, không phán, không chặn kèo.

Luật áp dụng (nguồn trong vault K23-Alden):
  - Ranh giới vòng cung = MA nhanh cắt xuống MA chậm (mở) → cắt lên (đóng)   [buổi 15]
  - Điểm cắt mở cung phải NGOÀI dải RSI 40-60, vì trong đó là vùng sideway    [buổi 4 SW1 + Kevin chốt 27/08]
  - Mô hình chỉ tính khi có ĐỘ DỐC + ĐỘ MỞ RỘNG của hai MA                    [buổi 15]
  - Khoảng cách hai MA chính là ĐỘ LỚN CỦA LỰC                                [buổi 4]

Ngưỡng số (spread, slope, 40/60, 80/20) là LƯỢNG HÓA CỦA MÌNH, thầy không nêu số.
Xem note 46 trong vault. Máy có thể đúng cơ chế mà sai hiệu chỉnh — chỗ này nên nghi.
"""

import json
import logging

log = logging.getLogger("k23dk")

# ==================== khung ====================
# Khung sàn MEXC trả trực tiếp
TF_SAN = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]

# Khung phải TỰ GỘP: đích -> (khung nguồn, số nến gộp)
TF_GOP = {
    "10m": ("5m", 2),
    "90m": ("30m", 3),
    "2h":  ("1h", 2),
    "3h":  ("1h", 3),   # b25: cụm mục tiêu H1·H2·H3·H4 — thiếu 3h thì H3 không quét được
    "5h":  ("1h", 5),
    "6h":  ("1h", 6),
    "7h":  ("1h", 7),
    "8h":  ("4h", 2),   # MEXC có Hour8 nhưng bảng map của bot chưa khai
    "12h": ("4h", 3),
    "16h": ("4h", 4),
    "2d":  ("1d", 2),
    "3d":  ("1d", 3),
    "5d":  ("1d", 5),
}

# Độ dài một nến, tính bằng mili giây — dùng để neo mốc gộp
TF_MS = {
    "1m": 60_000, "5m": 300_000, "10m": 600_000, "15m": 900_000, "30m": 1_800_000,
    "90m": 5_400_000, "5h": 18_000_000, "7h": 25_200_000, "16h": 57_600_000,
    "1h": 3_600_000, "2h": 7_200_000, "4h": 14_400_000, "6h": 21_600_000,
    "8h": 28_800_000, "12h": 43_200_000,
    "1d": 86_400_000, "2d": 172_800_000, "3d": 259_200_000, "5d": 432_000_000,
    "1w": 604_800_000,
}

# Nhãn tiếng Việt cho bảng
NHAN = {
    "1m": "M1", "5m": "M5", "10m": "M10", "15m": "M15", "30m": "M30", "90m": "90M",
    "1h": "H1", "2h": "H2", "4h": "H4", "5h": "H5", "6h": "H6", "7h": "H7",
    "8h": "H8", "12h": "H12", "16h": "16H",
    "1d": "D", "2d": "2D", "3d": "3D", "5d": "5D", "1w": "W",
}

# ==================== mốc tham chiếu ====================
# Thầy KHÔNG cho ngưỡng cho độ mở rộng / độ dốc. Buổi 3 (~2:30:03):
#   "độ dốc CÀNG LỚN và độ mở rộng CÀNG LỚN thì xu hướng CÀNG MẠNH"
#   "sideway: hai đường QUẤN VÀO NHAU NHƯ DÂY ĐIỆN, cắt lên cắt xuống,
#    không có độ mở rộng cũng như không có độ dốc"
# -> quan hệ TỶ LỆ, không phải ngưỡng có/không. Thầy so chỗ này với chỗ kia
#    TRÊN CÙNG MỘT CHART, nên ta cũng so tương đối với lịch sử của chính khung đó.
#    (Kevin: "RSI là tâm lý nên chỉ tương đối, áp dụng thuyết tương đối vô cho dễ")
SIDEWAY_DUOI, SIDEWAY_TREN = 40.0, 60.0   # dải cân bằng cung cầu [b4 SW1]


# ==================== gộp nến ====================

def gop_nen(bars, n):
    """
    Gộp n nến liền nhau thành 1. bars = [[t_ms, open, high, low, close, vol], ...] tăng dần.

    Neo mốc theo EPOCH: nến gộp bắt đầu tại mốc chia hết cho (n x độ dài nến nguồn).
    Cách này nhất quán và tái lập được; có thể lệch với cách TradingView neo 2D/3D,
    nên đừng dùng số ở đây để đối chiếu từng cây nến với chart.
    """
    if not bars or n <= 1:
        return list(bars)

    buoc = (bars[1][0] - bars[0][0]) if len(bars) > 1 else 0
    if buoc <= 0:
        return list(bars)
    khoi = buoc * n

    ra = []
    cum = None
    for b in bars:
        moc = (b[0] // khoi) * khoi
        if cum is None or cum[0] != moc:
            if cum is not None:
                ra.append(cum)
            cum = [moc, b[1], b[2], b[3], b[4], b[5] if len(b) > 5 else 0]
        else:
            cum[2] = max(cum[2], b[2])          # high
            cum[3] = min(cum[3], b[3])          # low
            cum[4] = b[4]                        # close = nến cuối
            if len(b) > 5:
                cum[5] += b[5]
    if cum is not None:
        ra.append(cum)
    return ra


def nen_cho_khung(lay_nen, symbol, tf, so_nen, kho=None):
    """
    Trả nến cho MỌI khung, kể cả khung sàn không có.
    `lay_nen(symbol, tf_san, limit)` là hàm fetch của bot.

    `kho` là dict cache dùng chung khi đọc nhiều khung của cùng một coin: 17 khung
    chỉ cần gọi sàn 5 lần (5m · 30m · 1h · 4h · 1d), phần còn lại gộp từ đó.
    """
    kho = kho if kho is not None else {}

    def tho_cua(tf_nguon, can):
        cu = kho.get(tf_nguon)
        if cu is None or len(cu) < can:
            kho[tf_nguon] = lay_nen(symbol, tf_nguon, max(can, 600))
        return kho[tf_nguon]

    if tf in TF_GOP:
        nguon, n = TF_GOP[tf]
        return gop_nen(tho_cua(nguon, so_nen * n + n), n)
    return tho_cua(tf, so_nen)


# ==================== chỉ báo ====================

def _ema(xs, n):
    ra = [None] * len(xs)
    k = 2.0 / (n + 1)
    tr = None
    for i, x in enumerate(xs):
        if x is None:
            continue
        tr = x if tr is None else (x - tr) * k + tr
        ra[i] = tr
    return ra


def _wma(xs, n):
    ra = [None] * len(xs)
    ts = n * (n + 1) / 2.0
    for i in range(len(xs)):
        if i + 1 < n:
            continue
        cua = xs[i - n + 1:i + 1]
        if any(v is None for v in cua):
            continue
        ra[i] = sum(v * (j + 1) for j, v in enumerate(cua)) / ts
    return ra


def rsi(closes, n=14):
    ra = [None] * len(closes)
    if len(closes) <= n:
        return ra
    tang = giam = 0.0
    for i in range(1, n + 1):
        d = closes[i] - closes[i - 1]
        tang += max(d, 0.0)
        giam += max(-d, 0.0)
    tang /= n
    giam /= n
    ra[n] = 100.0 if giam == 0 else 100 - 100 / (1 + tang / giam)
    for i in range(n + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        tang = (tang * (n - 1) + max(d, 0.0)) / n
        giam = (giam * (n - 1) + max(-d, 0.0)) / n
        ra[i] = 100.0 if giam == 0 else 100 - 100 / (1 + tang / giam)
    return ra


# ==================== vòng cung ====================

def _cac_diem_cat(f, s):
    """Trả [(chỉ_số, 'xuong'|'len'), ...] theo thứ tự thời gian."""
    ra = []
    truoc = None
    for i in range(len(f)):
        if f[i] is None or s[i] is None:
            continue
        dau = 1 if f[i] > s[i] else (-1 if f[i] < s[i] else 0)
        if dau == 0:
            continue
        if truoc is not None and dau != truoc:
            ra.append((i, "xuong" if dau < 0 else "len"))
        truoc = dau
    return ra


def _da_thoat_vung(r, tu_i, chieu, den_i=None):
    """
    Sau điểm cắt, RSI đã thoát khỏi dải 40-60 ĐÚNG CHIỀU của cung chưa?

    Cung tích lũy lực MUA sinh ra từ đợt bán -> RSI phải chìm xuống DƯỚI 40.
    Cung tích lũy lực BÁN sinh ra từ đợt mua -> RSI phải vọt lên TRÊN 60.
    Thoát sai chiều không tính: đó chỉ là nhiễu quanh vùng cân bằng.
    (Kevin chốt 27/08 — siết lại phương án (b) sau khi thấy nó nhận hết mọi khung.)
    """
    den_i = len(r) if den_i is None else den_i + 1
    for i in range(tu_i, min(den_i, len(r))):
        if r[i] is None:
            continue
        if chieu == "mua" and r[i] < SIDEWAY_DUOI:
            return True
        if chieu == "ban" and r[i] > SIDEWAY_TREN:
            return True
    return False


def trang_thai_cung(r, f, s):
    """
    Vòng cung tích lũy đã tạo thành chưa?

    Luật: cung mở tại điểm MA nhanh cắt MA chậm [buổi 15]. Điểm cắt nằm trong dải 40-60
    (vùng sideway) thì CHƯA tính — trừ khi sau đó RSI đã thoát ra ngoài dải, nghĩa là lực
    thật sự đã sinh ra [Kevin chốt 27/08, phương án (b)].

    Trả dict:
      trang_thai : 'chua_co' | 'trong_sideway' | 'dang_chay' | 'da_hoan_thanh'
      rsi_mo     : RSI tại điểm cắt mở cung
      so_nen     : số nến kể từ lúc mở cung
      chuan_bi   : 'tang' (cung ∪, mở bằng cắt xuống) | 'giam' (cung ∩, mở bằng cắt lên)

    CÁCH GỌI: dùng KẾT QUẢ TRÊN GIÁ, không dùng "tích lũy lực mua/bán".
    Buổi 3 thầy bắt ghi: "mô hình tích lũy lực BÁN của RSI chính là sóng TĂNG trên giá,
    và ngược lại" - ngược trực giác, rất dễ hiểu nhầm. Buổi 4 thầy BỎ cách gọi đó,
    đổi thành "quá trình chuẩn bị vào sóng tăng/giảm". Ta theo cách gọi mới.
      mo_trong_vung : cung mở trong 40-60 nhưng đã thoát ra — để bày cho người đọc tự cân
    """
    kq = {"trang_thai": "chua_co", "rsi_mo": None, "rsi_dong": None, "so_nen": 0,
          "tuoi": None, "chuan_bi": None, "mo_trong_vung": False}
    cat = _cac_diem_cat(f, s)
    if not cat:
        return kq

    def hop_le(i_cat, loai_cat, i_den=None):
        """Điểm cắt này có mở được cung không, và có phải mở trong vùng mờ không."""
        rv = r[i_cat] if i_cat < len(r) else None
        if rv is None:
            return False, False
        chieu = "mua" if loai_cat == "xuong" else "ban"   # chiều để dò thoát vùng
        if rv < SIDEWAY_DUOI or rv > SIDEWAY_TREN:
            return True, False                                  # cắt ngoài vùng → hợp lệ luôn
        return _da_thoat_vung(r, i_cat, chieu, i_den), True      # cắt trong vùng → phải thoát ĐÚNG CHIỀU

    # cặp cắt cuối: mở (cat[-2]) → đóng (cat[-1])
    if len(cat) >= 2:
        i_mo, loai_mo = cat[-2]
        i_dong, loai_dong = cat[-1]
        ok, trong_vung = hop_le(i_mo, loai_mo, i_dong)
        if ok and loai_mo != loai_dong:
            kq.update(trang_thai="da_hoan_thanh", rsi_mo=round(r[i_mo], 1),
                      rsi_dong=round(r[i_dong], 1) if r[i_dong] is not None else None,
                      so_nen=i_dong - i_mo,          # CHIỀU DÀI cung (mở → đóng)
                      tuoi=len(f) - 1 - i_dong,      # TUỔI: bao nhiêu nến KỂ TỪ LÚC ĐÓNG
                      mo_trong_vung=trong_vung,
                      chuan_bi="tang" if loai_mo == "xuong" else "giam")
            return kq

    # chưa đóng: xét lần cắt cuối như điểm mở
    i_cuoi, loai_cuoi = cat[-1]
    if i_cuoi >= len(r) or r[i_cuoi] is None:
        return kq
    ok, trong_vung = hop_le(i_cuoi, loai_cuoi)
    if ok:
        kq.update(trang_thai="dang_chay", rsi_mo=round(r[i_cuoi], 1),
                  so_nen=len(f) - 1 - i_cuoi, mo_trong_vung=trong_vung,
                  chuan_bi="tang" if loai_cuoi == "xuong" else "giam")
    else:
        kq.update(trang_thai="trong_sideway", rsi_mo=round(r[i_cuoi], 1),
                  so_nen=len(f) - 1 - i_cuoi, mo_trong_vung=True)
    return kq


# ==================== đọc một khung ====================

def doc_khung(closes, rsi_len=14, ema_len=9, wma_len=45):
    """
    Đọc đầy đủ một khung. Trả dict đủ để bày ra bảng — không phán, không lọc.
    """
    r = rsi(closes, rsi_len)
    f = _ema(r, ema_len)
    s = _wma(r, wma_len)

    r_cuoi = next((r[i] for i in range(len(r) - 1, -1, -1) if r[i] is not None), None)
    if r_cuoi is None or f[-1] is None or s[-1] is None:
        return None

    spread = f[-1] - s[-1]
    slope = None
    if len(f) > 4 and f[-4] is not None:
        slope = (f[-1] - f[-4]) / 3.0

    # ĐỘ MẠNH = độ mở rộng hiện tại đứng ở đâu so với chính lịch sử khung này.
    # 100% = rộng nhất từng thấy (thầy: "mở rất là rộng")
    #   0% = dính nhau      (thầy: "quấn vào nhau như dây điện")
    lich_su = [abs(f[i] - s[i]) for i in range(len(f))
               if f[i] is not None and s[i] is not None]
    manh = None
    if len(lich_su) >= 20:
        dinh = sorted(lich_su)[int(len(lich_su) * 0.95)]      # mốc "rộng nhất", bỏ nhiễu 5%
        if dinh > 0:
            manh = round(min(100.0, abs(spread) / dinh * 100), 1)

    # ⭐ ĐANG MỞ RA hay ĐANG KHÉP LẠI — buổi 4 ~2:34, thầy xác nhận "Chính xác":
    #   cắt lên rồi "mở mở dần ra"  -> LỰC MUA tích lũy tăng dần
    #   rộng nhất                    -> hai lực GẦN CÂN BẰNG (điểm chuyển)
    #   "thu hẹp dần"                -> LỰC BÁN tích lũy tăng dần
    #   cắt vào nhau                 -> xác nhận đảo
    # Thiếu cái này thì máy chỉ biết cung RỘNG bao nhiêu, không biết đang ở NỬA NÀO.
    no_rong = None
    if len(f) > 6 and f[-6] is not None and s[-6] is not None:
        truoc = abs(f[-6] - s[-6])
        no_rong = abs(spread) - truoc          # >0 mở ra, <0 khép lại

    if no_rong is None:
        pha = None
    elif no_rong > 0:
        pha = "mo_ra"       # lực đang thắng thế mạnh dần
    elif no_rong < 0:
        pha = "khep_lai"    # lực ngược đang tích lũy
    else:
        pha = "dung"

    # Hướng: đường nhanh nằm trên hay dưới đường chậm. Dốc phải cùng chiều thì mới
    # là xu hướng thật (b15: thiếu dốc thì không phải mô hình).
    huong = 0
    if slope is not None:
        if spread > 0 and slope > 0:
            huong = 1
        elif spread < 0 and slope < 0:
            huong = -1

    return {
        "rsi": round(r_cuoi, 1),
        "ema": round(f[-1], 1),
        "wma": round(s[-1], 1),
        "spread": round(spread, 2),
        "slope": round(slope, 3) if slope is not None else None,
        "manh": manh,          # 0-100: mở toác hay quấn dây điện
        "no_rong": round(no_rong, 3) if no_rong is not None else None,
        "pha": pha,            # mo_ra / khep_lai — đang ở nửa nào của vòng cung
        "trend": huong,        # -1/0/1: chiều, khi dốc và mở rộng cùng hướng
        "cung": trang_thai_cung(r, f, s),
    }


# ==================== XĂNG (dư địa tới ngưỡng quán tính) ====================
# Mốc 80/20 = quán tính [buổi 4/5]. Độ sâu 30/70 là lượng hóa của mình — xem note 46.
INERT_UP, INERT_DN = 80.0, 20.0
DEPTH_LONG, DEPTH_SHORT = 30.0, 70.0


def xang(chieu, rsi_val, rsi_xuat_phat=None):
    """
    Xăng = sóng đang ở ĐẦU hay CUỐI chu kỳ. Không phải đo lực mạnh yếu (đó là độ mở rộng).

    Mốc XUẤT PHÁT = RSI tại điểm KẾT THÚC vòng cung tích lũy — lúc chuyển trạng thái,
    tức lúc con sóng bắt đầu chạy. Thầy (b5.1 ~17:39): "khi RSI 1D bắt đầu nó CẮT LÊN,
    nó mở toác, thì bình nhiên liệu tăng còn nhiều hay ít? - Rõ ràng là nhiều...
    xu hướng tăng này nó MỚI BẮT ĐẦU thôi, nó CHƯA ĐI XA đâu."

    Đích = mốc quán tính 80 (lên) / 20 (xuống)  [b4-b5].

        xăng = (80 - RSI hiện tại) / (80 - RSI lúc chuyển trạng thái)      chiều lên
        xăng = (RSI hiện tại - 20) / (RSI lúc chuyển trạng thái - 20)      chiều xuống

    Không dùng số nến để đo — thầy (b5.1 ~15:30): "bao nhiêu cây nến thì tích lũy xong?
    Cái này là TÙY GIAI ĐOẠN."

    Chưa xác định được điểm chuyển trạng thái -> trả None, không đoán.
    """
    if chieu == 0 or rsi_val is None or rsi_xuat_phat is None:
        return None
    if chieu == 1:
        tong = INERT_UP - rsi_xuat_phat
        con = INERT_UP - rsi_val
    else:
        tong = rsi_xuat_phat - INERT_DN
        con = rsi_val - INERT_DN
    if tong <= 0:
        return None
    # ⚠️ GỠ CAP 11/09 — `min(100.0, …)` che mất trường hợp SÓNG ĐÃ CHẠY NGƯỢC.
    #   Đo trên 320 lệnh: 103 lệnh (≈⅓) hiện "xăng 100%" nhưng thô >100%,
    #   trung vị 122%, max 408% — tức RSI đã đi ngược kể từ lúc cung đóng,
    #   mà panel vẫn báo "còn đầy". Hai trạng thái NGƯỢC NHAU đọc ra một số.
    #   Nay trả THẬT. >100% nghĩa là sóng chưa tiêu gì, thậm chí đang lùi.
    #   Chỗ hiển thị dùng xang_chu() để in cho người đọc.
    return round(max(0.0, con / tong * 100), 1)


def xang_chu(x):
    """Đổi số xăng thành chữ cho người đọc. >100% = sóng đang LÙI, chưa tiêu gì."""
    if x is None:
        return "—"
    if x > 100.0:
        return f"100%↩{x - 100:.0f}"     # đầy bình, mà còn lùi thêm x-100%
    return f"{x:.0f}%"


# ==================== BA LÝ THUYẾT ĐA KHUNG ====================
#
# 1. CỤM KHUNG (buổi 5.1) — nhìn LÊN, khoảng cách 3-6x
#    Khung X muốn chạy phải được HAI khung lớn hơn trong cụm đồng thuận.
#    <2x = sát sườn (không xung đột) · 3-6x = chi phối · >6x = không liên quan.
#
# 2. BẢN CHẤT SÓNG (buổi 7) — nhìn XUỐNG, các khung nhỏ hơn liền kề
#    "Sóng khung X muốn đi lên thì bản chất phải có quán tính tăng của các khung
#     nhỏ hơn liền kề." 1W muốn lên -> 1D/2D/3D phải có lực; bật xuống H4 mà không
#     có lực thì 1W không quyết định được thị trường, rồi tụt.
#
# 3. TỊNH TIẾN SÓNG (buổi 7) — khung SÁT SƯỜN 1.5-2x
#    Khung có mô hình nhưng lực không đủ -> NHƯỜNG QUYẾT ĐỊNH cho khung sát sườn.
#    CHỈ xảy ra trong downtrend/sideway. Uptrend mạnh thì không có hiện tượng này.
#    Khi tịnh tiến, bộ khung tham chiếu GIỮ NGUYÊN.

# 3-6x: chi phối nhau, cần đồng thuận
CUM = {
    "5m":  ["5m", "15m", "1h"],
    "15m": ["15m", "1h", "4h"],
    "1h":  ["1h", "4h", "1d"],
    "1d":  ["1d", "3d", "5d"],   # bỏ Tuần (hệ ngắn hạn) — 3x và 5x vẫn trong dải 3-6x của thầy
}

# ══════════════════════════════════════════════════════════════════════════════
# CHUỖI BÁNH RĂNG — lực truyền TỪNG MẮT, cấm nhảy cóc
#
# Kevin 15/09 11:01: "nếu làm nguyên lý bánh răng thì phải thêm luôn h4 h6 h8 h12 d
#                     nữa đó bạn, KHÔNG THỂ NÀO H4 KÉO ĐC KHUNG D"
#
# Thầy b11 00:03:37 đọc đúng chuỗi này, gọi đích danh H6/H8/H12/1D:
#   "khung nhỏ nó lại KÉO LUÔN KHUNG LỚN như thằng H6, H8 vào quá trình điều chỉnh
#    luôn" -> "kéo cái RSI của thằng H12 xuống, nhưng vẫn giữ được RSI của thằng 1D"
# Chiều kéo LÊN, b11 01:01:27: "khung nhỏ nó kéo lên thì nó có quán tính tăng để
#   KÉO TIẾP KHUNG LỚN lên hay không?"
#
# ĐO 15/09 (6 coin, 12 phép, hai chiều): số lần cắt MA 1H:4H:1D = 110:24:1
#   (ổn định 98-116). RSI 1D không thủng 30 lần nào trong 81 ngày khi 1H thủng 14-22.
#   -> bánh kế bên đứng yên thì bánh này đang quay TRƯỢT.
# ❌ Bị bác bằng số: "bánh nhỏ dẫn 3 ngày" chỉ đúng 2/5 coin — KHÔNG dùng.
BANH_RANG = ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"]


def mat_ke(tf, len_tren=True):
    """Mắt răng kế tiếp trong chuỗi. Lực chỉ truyền sang mắt KỀ, không nhảy cóc."""
    if tf not in BANH_RANG:
        return None
    i = BANH_RANG.index(tf) + (1 if len_tren else -1)
    return BANH_RANG[i] if 0 <= i < len(BANH_RANG) else None


# 1.5-2x: gần như MỘT khung, nhường quyết định cho nhau (tịnh tiến)
SAT_SUON = [
    ["10m", "15m", "30m"],                   # thầy: M10 ↔ M15 ↔ M30
    ["1h", "90m", "2h"],                     # thầy: H1 ↔ 90M ↔ H2 (1 nến 90M = 1,5 nến H1)
    ["4h", "5h", "6h", "7h", "8h"],          # thầy: "H5 chỉ hơn H4 một tí thôi"
    ["12h", "16h"],                          # thầy: 12H ↔ 16H
    ["1d", "2d"],                            # suy ra theo cùng tỷ lệ 1.5-2x
]

# các khung NHỎ HƠN liền kề — dùng cho bản chất sóng
# Khung nhỏ hơn liền kề — mỗi dòng có nguồn transcript, xếp từ NHỎ tới LỚN.
NHO_HON = {
    "5m":  [],                              # SÀN của dải — dưới M5 không xét (Kevin 13/09)
    "15m": ["5m"],                          # suy ra theo cùng tỷ lệ
    "30m": ["5m", "15m"],                   # b6 18:25 cùng lối: khung lớn cần M5·M15 đỡ
    "1h":  ["5m", "15m"],                   # b6 18:25 "sóng tăng của H1 phải từ cấu trúc tăng của M15 và M5"
    "2h":  ["5m", "15m", "30m"],            # b10 2:03:42 "khung nhỏ hơn của H2… ví dụ thằng 5m"
    "3h":  ["30m", "1h", "2h"],             # suy ra theo cùng tỷ lệ với 4h
    "4h":  ["15m", "30m", "1h"],            # suy ra
    "6h":  ["1h", "2h", "4h"],              # b11 0:03:37 thầy đọc H6 bị khung nhỏ kéo
    "8h":  ["2h", "4h", "6h"],              # b11 0:03:37 "như thằng H6, H8"
    "12h": ["4h", "6h", "8h"],              # b11 0:03:50 "kéo RSI của thằng H12 xuống"
    "1d":  ["1h", "4h", "8h", "12h"],       # b13 2:41:22 "phải xem H4… thử bật H1 đi xem nào"
                                            # + b11 0:03:55 1D giữ được khi H12 đã bị kéo
    "2d":  ["12h", "1d"],                   # suy ra cùng tỷ lệ 1.5-2x (b7)
    "3d":  ["1d", "2d"],                    # suy ra
    "5d":  ["2d", "3d"],                    # suy ra
    "1w":  ["12h", "1d", "2d", "3d"],       # b7 40:16 "1D 2D 3D" · b13 1:59:04 "12 giờ, 1D còn lực kéo 1W"
}

# Dải khung đầy đủ: mỗi khung có vai trò riêng, không phải để so với nhau.
MOI_KHUNG = ["5m", "10m", "15m", "30m", "1h", "90m", "2h", "4h", "5h", "6h", "7h",
             "8h", "12h", "16h", "1d", "2d", "3d", "5d"]

# ⚠️ KIỂM 11/09: XANG_CAN · PIVOT_TRAI/PHAI · TEST_SAI_SO đều là SỐ MÌNH TỰ ĐẶT,
#   CHƯA ĐO trên kết quả lệnh lần nào. Đã rà: cả ba chỉ nằm ở đường BÀY
#   (du_luc/con_xang/cac_muc) — KHÔNG nằm ở đường ra quyết định của máy
#   (cong_mo_hinh -> cu_a -> mo_hinh_dep). Nên tạm chấp nhận được, NHƯNG:
#   cấm dùng chúng để lọc lệnh, và cấm tune chúng để cứu một kết quả xấu.
XANG_CAN = 25.0     # lượng hóa của mình — note 46


def doc_moi_khung(lay_nen, symbol, khung=None, so_nen=200):
    """Đọc các khung -> {tf: dict}. Khung nào lỗi/thiếu nến thì bỏ qua."""
    khung = khung or MOI_KHUNG
    bang = {}
    kho = {}                      # cache nến thô, dùng chung cho mọi khung của coin này
    for tf in khung:
        try:
            bars = nen_cho_khung(lay_nen, symbol, tf, so_nen, kho)
            d = doc_khung([b[4] for b in bars])
            if d:
                c = d["cung"]
                # Cung ĐÃ ĐÓNG -> sóng đã bắt đầu chạy, tính xăng từ điểm chuyển trạng thái.
                # Cung ĐANG CHẠY -> vẫn đang tích lũy, sóng mới chưa khởi động -> chưa có xăng để đo.
                ch = d["trend"] or (1 if c["chuan_bi"] == "tang" else -1 if c["chuan_bi"] == "giam" else 0)
                d["xang"] = xang(ch, d["rsi"], c.get("rsi_dong"))
                d["tf"] = tf
                d["nhan"] = NHAN[tf]
                # Lưu CẢ HAI mốc: luật chốt cần mốc theo chiều LỆNH đang gồng,
                # không phải theo chiều khung này đang đi.
                d["ho_tro"] = pha_ho_tro(bars, 1)     # đáy gần nhất — lệnh mua nhìn mốc này
                d["khang_cu"] = pha_ho_tro(bars, -1)  # đỉnh gần nhất — lệnh bán nhìn mốc này
                bang[tf] = d
        except Exception as e:
            log.warning("doc %s %s loi: %s", symbol, tf, e)
    return bang


# ==================== HỖ TRỢ / KHÁNG CỰ TRÊN GIÁ ====================
# Buổi 13 ~2:42: thầy chỉ vùng hỗ trợ bằng mắt — "nó có rất nhiều râu nó test cái
# vùng này thì nó đang tạo một cái vùng hỗ trợ". Thầy không cho công thức, nên ở đây
# máy chỉ BÀY: mức pivot gần nhất + đã bị test mấy lần. Số 2/2 dưới đây là của mình.

PIVOT_TRAI = PIVOT_PHAI = 2      # số của mình — fractal 2 bên
TEST_SAI_SO = 0.003              # số của mình — râu chạm trong 0.3% coi như test cùng vùng


def lam_tron_gia(x, n=6):
    """Làm tròn GIÁ theo CHỮ SỐ CÓ NGHĨA, không theo số thập phân.
    ⚠️ 03/10 mục L: `round(muc, 6)` biến PEPE 4.3e-06 thành 4e-06 ⇒ sai hỗ trợ/kháng
    cự, C5 `sat_moc_ngang` mù. Cách làm giống `dong_bo_sheet._so` (6 chữ số nghĩa)."""
    if x is None:
        return None
    return float(f"{float(x):.{n}g}")


def _pivot_gan_nhat(bars, chieu, trai=PIVOT_TRAI, phai=PIVOT_PHAI):
    """
    chieu = 1 (đang tăng) -> tìm ĐÁY gần nhất đã xác nhận = hỗ trợ.
    chieu = -1 (đang giảm) -> tìm ĐỈNH gần nhất = kháng cự.
    Trả (index, giá) hoặc None. Pivot phải đủ `phai` nến bên phải mới tính là xác nhận.
    """
    if len(bars) < trai + phai + 1:
        return None
    cot = 3 if chieu == 1 else 2                       # low hoặc high
    for i in range(len(bars) - phai - 1, trai - 1, -1):
        gia = bars[i][cot]
        trai_ok = all((bars[j][cot] > gia) if chieu == 1 else (bars[j][cot] < gia)
                      for j in range(i - trai, i))
        phai_ok = all((bars[j][cot] > gia) if chieu == 1 else (bars[j][cot] < gia)
                      for j in range(i + 1, i + phai + 1))
        if trai_ok and phai_ok:
            return i, gia
    return None


def pha_ho_tro(bars, chieu):
    """
    Khung này đã PHÁ hỗ trợ (nếu đang gồng long) / kháng cự (nếu đang gồng short) chưa?
    Đây là điều kiện thứ hai của luật chốt — b13 1:59:44.
    """
    pv = _pivot_gan_nhat(bars, chieu)
    if not pv:
        return None
    i, muc = pv
    dong = bars[-1][4]
    cot = 3 if chieu == 1 else 2

    # Đếm số lần râu về test lại vùng đó — thầy: "rất nhiều râu nó test cái vùng này"
    lan_test = sum(1 for b in bars[i:] if abs(b[cot] - muc) / muc <= TEST_SAI_SO)

    da_pha = dong < muc if chieu == 1 else dong > muc
    khoang = (dong - muc) / muc * 100
    return {
        "muc": lam_tron_gia(muc),
        "gia": lam_tron_gia(dong),
        "cach": round(khoang, 2),        # % giá đang cách mức đó (âm = đã xuyên xuống)
        "lan_test": lan_test,
        "da_pha": da_pha,
        "ten": "hỗ trợ" if chieu == 1 else "kháng cự",
    }


def cac_muc(bars, chieu_lenh, trai=PIVOT_TRAI, phai=PIVOT_PHAI):
    """MỌI mức ngang đã xác nhận theo hướng LỆNH (không chỉ mức gần nhất).
    chieu_lenh=1 (long)  -> các ĐỈNH pivot NẰM TRÊN giá  = kháng cự
    chieu_lenh=-1 (short)-> các ĐÁY  pivot NẰM DƯỚI giá  = hỗ trợ
    Vì sao cần: _pivot_gan_nhat chỉ trả mức GẦN NHẤT -> đo ra R:R trung vị 0.99,
    trong khi D2 nói cơ chế target-khung-lớn đẻ ra 1:5-1:7. 'Gần nhất' là chữ mình
    tự thêm, luật (Kevin chốt 08/09) chỉ đòi mức NGANG có lan_test >= 1.
    Trả list dict đã lọc lan_test>=1, sắp theo khoảng cách tăng dần."""
    if len(bars) < trai + phai + 1:
        return []
    cot = 2 if chieu_lenh == 1 else 3
    dong = bars[-1][4]
    ra = []
    for i in range(trai, len(bars) - phai):
        gia = bars[i][cot]
        if chieu_lenh == 1:
            ok = (all(bars[j][cot] < gia for j in range(i - trai, i)) and
                  all(bars[j][cot] < gia for j in range(i + 1, i + phai + 1)))
            if not ok or gia <= dong:
                continue
        else:
            ok = (all(bars[j][cot] > gia for j in range(i - trai, i)) and
                  all(bars[j][cot] > gia for j in range(i + 1, i + phai + 1)))
            if not ok or gia >= dong:
                continue
        lan = sum(1 for b in bars[i:] if abs(b[cot] - gia) / gia <= TEST_SAI_SO)
        if lan >= 1:
            ra.append({"muc": lam_tron_gia(gia), "lan_test": lan,
                       "cach": round((gia - dong) / dong * 100, 2)})
    ra.sort(key=lambda x: abs(x["cach"]))
    return ra


def gan_moc(d, bars, tf=None):
    """Gắn HAI mốc KC/HT (kèm lan_test) vào dict khung.
    Bug 09/09: k23_v7.cham / quet_lenh_rsi / backtest tự dựng bang bằng doc_khung()
    (chỉ nhận mảng CLOSE) nên bang KHÔNG BAO GIỜ có 'khang_cu'/'ho_tro'
    -> muc_tieu_theo_khung luôn None -> hệ RSI đánh mà KHÔNG có đích (D2),
    mất đúng cơ chế đẻ ra R:R 1:5-1:7. Mọi chỗ dựng bang phải gọi hàm này."""
    if d is None:
        return d
    d["ho_tro"]   = pha_ho_tro(bars, 1)
    d["khang_cu"] = pha_ho_tro(bars, -1)
    if tf:                                   # muc_tieu_theo_khung còn đọc 'nhan'/'tf'
        d["tf"] = tf
        d["nhan"] = NHAN.get(tf, tf)
    # XĂNG — trước đây chỉ doc_moi_khung mới tính, nên mọi bảng dựng qua gan_moc
    # đều in cột xăng RỖNG. Mà xăng là thước "đi xa hay chưa" của thầy (b6 · b11),
    # thiếu nó thì không kiểm được luật xăng trên khung đánh. Nối vào đây 10/09.
    if d.get("xang") is None:
        c = d.get("cung") or {}
        ch = d.get("trend") or (1 if c.get("chuan_bi") == "tang"
                                else -1 if c.get("chuan_bi") == "giam" else 0)
        try:
            d["xang"] = xang(ch, d.get("rsi"), c.get("rsi_dong")) if ch else None
        except Exception:
            d["xang"] = None
    return d


def nen_chot(bang, tf, chieu):
    """
    LUẬT CHỐT — buổi 13 ~1:59:25:
      "chúng ta sẽ giữ lệnh khi mà các khung thời gian nhỏ hơn của 12 giờ nếu nó còn
       quán tính tăng... Nhưng nếu nó hoàn thành hết quán tính tăng và không còn quán
       tính tăng nào của những khung nhỏ hơn nữa thì lúc đấy mình phải xem xét để mà
       chốt — khi mà các khung nhỏ nó PHÁ HỖ TRỢ thì lúc đấy mình chốt nó ra."

    HAI điều kiện, không phải một. Hết xăng thôi chưa chốt.
    chieu = 1 nếu đang gồng lệnh mua, -1 nếu gồng lệnh bán.

    ⚠️ CHỈ BÀY CHO MẮT — ĐỪNG NỐI VÀO BOT.
    Backtest 27/08/2026, 526 lệnh QM thật, 45 ngày, 21 coin:
        gốc  (TP/SL của bot)  WR 48% · +122.20R · PF 1.48
        tầng H1 (M5/M15)      WR 40% ·  +30.63R · PF 1.24   -91.6R
        tầng H4 (M15/M30/H1)  WR 38% ·   +0.15R · PF 1.00  -122.1R
    Lý do: bot đã có TP cứng R:R 3:1. Luật này là cơ chế thoát THỨ HAI, gần như luôn
    bắn trước TP nên nó THAY THẾ chứ không bổ trợ -> ăn non toàn bộ. Thầy dạy luật này
    cho gồng lệnh khung 12H/1W, nơi KHÔNG có TP cứng và nó là cơ chế thoát duy nhất.
    Đừng tune XANG_CAN/pivot để cứu — đó là đi tìm số đẹp. Xem note 53 mục 7.
    """
    duoi = [t for t in NHO_HON.get(tf, []) if t in bang]
    if not duoi:
        return None

    # (1) còn khung nhỏ nào giữ quán tính cùng chiều không
    con_qt = [bang[t]["nhan"] for t in duoi
              if bang[t]["trend"] == chieu
              and bang[t]["xang"] is not None and bang[t]["xang"] >= XANG_CAN]
    het_qt = not con_qt

    # (2) khung nhỏ nào đã phá hỗ trợ/kháng cự chưa
    da_pha, chua_pha = [], []
    for t in duoi:
        hk = bang[t].get("ho_tro" if chieu == 1 else "khang_cu")
        if not hk:
            continue
        (da_pha if hk["da_pha"] else chua_pha).append(f"{bang[t]['nhan']} {hk['muc']}")

    if het_qt and da_pha:
        trang_thai, ket = "CHOT", f"CHỐT — bên dưới cạn quán tính VÀ {', '.join(da_pha)} đã phá"
    elif het_qt:
        trang_thai = "CANH"
        ket = ("CANH CHỐT — bên dưới đã cạn quán tính nhưng CHƯA phá "
               + (chua_pha[0].split()[1] if chua_pha else "mốc nào") + ", thầy dạy đợi phá mới ra")
    elif da_pha:
        trang_thai = "CANH"
        ket = f"CANH — {', '.join(da_pha)} đã phá nhưng {', '.join(con_qt)} vẫn còn quán tính"
    else:
        trang_thai, ket = "GIU", f"GIỮ — {', '.join(con_qt)} còn quán tính, chưa phá mốc nào"

    return {"tf": tf, "chieu": chieu, "trang_thai": trang_thai,
            "con_quan_tinh": con_qt, "da_pha": da_pha, "ket_luan": ket}


def doc_cum(bang, tf_muc_tieu):
    """CỤM KHUNG — khung mục tiêu có được hai khung lớn hơn gật đầu không."""
    cum = CUM.get(tf_muc_tieu)
    if not cum:
        return None
    mt = bang.get(cum[0])
    tren = [bang[t] for t in cum[1:] if t in bang]
    if not mt or len(tren) < 2:
        return None

    h = mt["trend"]
    ghi = [d["nhan"] for d in tren if d["trend"] != 0 and h != 0 and d["trend"] != h]
    thuan = [d["nhan"] for d in tren if d["trend"] != 0 and h != 0 and d["trend"] == h]
    cai_nhau = tren[0]["trend"] != 0 and tren[1]["trend"] != 0 and tren[0]["trend"] != tren[1]["trend"]

    if h == 0:
        ket = f"{mt['nhan']} chưa rõ hướng"
    elif len(thuan) == 2:
        ket = f"{mt['nhan']} {'lên' if h == 1 else 'xuống'} · cụm ĐỒNG THUẬN"
    elif ghi:
        ket = f"{mt['nhan']} {'lên' if h == 1 else 'xuống'} nhưng bị {', '.join(ghi)} GHÌ → thành sideway"
    else:
        ket = f"{mt['nhan']} {'lên' if h == 1 else 'xuống'} · khung trên chưa xác nhận"
    if cai_nhau:
        ket += f" · {tren[0]['nhan']} và {tren[1]['nhan']} ngược pha"

    return {"cum": cum, "muc_tieu": mt, "dong_thuan": h != 0 and len(thuan) == 2,
            "ghi": ghi, "cai_nhau": cai_nhau, "ket_luan": ket}


def ban_chat_song(bang, tf):
    """
    BẢN CHẤT SÓNG — khung tf có được các khung NHỎ HƠN liền kề đỡ không?
    Không có lực bên dưới thì tf không quyết định được thị trường, đẩy lên rồi tụt.
    """
    duoi = [bang[t] for t in NHO_HON.get(tf, []) if t in bang]
    mt = bang.get(tf)
    if not mt or not duoi:
        return None
    h = mt["trend"]

    # BẮC CẦU (b13 2:41:30): "Bật thằng H1 mà nó không có thì chắc chắn là thằng H4
    # nó không có, bởi vì thằng H4 nó là thằng lớn hơn." Khung nhỏ nhất im lìm thì
    # các khung trung gian không thể có lực — quán tính khung lớn dựng từ khung nhỏ.
    nho_nhat = duoi[0]
    if h != 0 and nho_nhat["trend"] != h:
        bac_cau = (f"{nho_nhat['nhan']} (nhỏ nhất) không có quán tính "
                   f"{'tăng' if h == 1 else 'giảm'} → các khung trên nó cũng khó có")
    else:
        bac_cau = None
    do = [d["nhan"] for d in duoi if h != 0 and d["trend"] == h]
    nguoc = [d["nhan"] for d in duoi if h != 0 and d["trend"] != 0 and d["trend"] != h]
    con_xang = [d["nhan"] for d in duoi if d["xang"] is not None and d["xang"] >= XANG_CAN]

    if h == 0:
        ket = f"{mt['nhan']} chưa rõ hướng"
    elif do:
        ket = f"{mt['nhan']} được {', '.join(do)} đỡ"
        ket += f" · còn xăng: {', '.join(con_xang)}" if con_xang else " · nhưng bên dưới ĐÃ CẠN"
    else:
        ket = f"{mt['nhan']} {'lên' if h == 1 else 'xuống'} nhưng bên dưới KHÔNG có lực → khó kéo nổi"
    if nguoc:
        ket += f" · {', '.join(nguoc)} đang đi ngược"

    if bac_cau:
        ket += f" · {bac_cau}"

    return {"tf": tf, "do": do, "nguoc": nguoc, "con_xang": con_xang, "bac_cau": bac_cau,
            "du_luc": bool(do) and bool(con_xang) and not bac_cau, "ket_luan": ket}


def tinh_tien(bang, tf):
    """
    TỊNH TIẾN SÓNG — khung tf yếu thì khung SÁT SƯỜN nào đang cầm quyết định?
    Chỉ áp dụng khi tf KHÔNG phải uptrend mạnh (thầy: uptrend mạnh không có hiện tượng này).
    """
    nhom = next((n for n in SAT_SUON if tf in n), None)
    mt = bang.get(tf)
    if not nhom or not mt:
        return None
    # Thầy: tịnh tiến "hầu hết chỉ áp dụng trong giai đoạn downtrend và sideway".
    # Uptrend thì "dòng tiền ào ạt, cứ có mô hình là nó chạy" -> không nhường quyết định.
    # Dùng đúng dấu xu hướng, KHÔNG đặt thêm ngưỡng "mạnh bao nhiêu" (thầy không cho số).
    if mt["trend"] == 1:
        return {"tf": tf, "nhuong_cho": None,
                "ket_luan": f"{mt['nhan']} đang uptrend — thầy: uptrend không có tịnh tiến"}

    # ⛔ 18/09 — chỉ tịnh tiến TRONG DẢI đang dùng. Kevin 13/09 bỏ hẳn 2D·3D·W·1M
    # (hệ ngắn hạn). Trước đó máy báo "D yếu → quyết định nằm ở 2D" — nhường quyền
    # cho khung đã bị loại khỏi hệ, vô nghĩa.
    trong_dai = set(BANH_RANG)
    ke = [bang[t] for t in nhom
          if t != tf and t in bang and t in trong_dai and bang[t]["trend"] != 0]
    if not ke:
        return {"tf": tf, "nhuong_cho": None,
                "ket_luan": f"{mt['nhan']} và khung sát sườn đều chưa rõ"}
    manh = max(ke, key=lambda d: d["manh"] or 0)
    if mt["trend"] == 0 or (manh["manh"] or 0) > (mt["manh"] or 0):
        return {"tf": tf, "nhuong_cho": manh["nhan"],
                "ket_luan": f"{mt['nhan']} yếu → quyết định đang nằm ở {manh['nhan']} "
                            f"{'▲' if manh['trend'] == 1 else '▼'} (sát sườn)"}
    return {"tf": tf, "nhuong_cho": None,
            "ket_luan": f"{mt['nhan']} vẫn tự cầm quyết định"}


def doc_lenh_m5(bang):
    """
    Đọc cho một kèo QML M5 — ba lý thuyết, ba câu hỏi khác nhau.
    Chỉ bày, không phán. Quyết định là của người.
    """
    ra = {"ket_luan": []}
    c = doc_cum(bang, "5m")
    if c:
        ra["vao"] = c
        ra["ket_luan"].append("VÀO (cụm M5·M15·H1): " + c["ket_luan"])

    c1 = doc_cum(bang, "1h")
    b1 = ban_chat_song(bang, "4h")
    if c1:
        ra["gong_cum"] = c1
        t = "GỒNG (cụm H1·H4·1D): " + c1["ket_luan"]
        if c1["ghi"]:
            t += " → không gồng xa, chốt sớm"
        ra["ket_luan"].append(t)
    if b1:
        ra["gong_ban_chat"] = b1
        ra["ket_luan"].append("BẢN CHẤT (H4 có được M15/M30/H1 đỡ): " + b1["ket_luan"])

    tt = tinh_tien(bang, "1h")
    if tt and tt["nhuong_cho"]:
        ra["tinh_tien"] = tt
        ra["ket_luan"].append("TỊNH TIẾN: " + tt["ket_luan"])
    return ra


# ==================== QUY LUẬT VÀO LỆNH (buổi 8 · 9 · 17) ====================
# Máy đo trước đây chỉ trả lời "khung này mạnh yếu ra sao". Nó KHÔNG trả lời được
# câu quan trọng nhất của thầy: "khung này CÓ MÔ HÌNH hay không".

def co_mo_hinh(d):
    """
    QUY LUẬT 1 (b8 33:23): "Có mô hình thì vào, không có mô hình thì thôi."
    Mô hình cần ĐỦ BA điều kiện — thiếu một là không tính:
      1. ranh giới = hai lần cắt MA          (b15 1:36)
      2. điểm mở cung NGOÀI dải 40-60         (Kevin chốt, dựa b4)
      3. có độ dốc + độ mở rộng               (b3 2:38 · b15)
    Trả (bool, lý do) — nêu rõ thiếu điều kiện nào để mắt kiểm lại được.
    """
    c = d.get("cung") or {}
    if c.get("trang_thai") != "da_hoan_thanh":
        return False, "cung chưa đóng — chớm cắt là sóng giả (b15 1:39)"
    mo = c.get("rsi_mo")
    if mo is None:
        return False, "không xác định được điểm mở cung"
    if SIDEWAY_DUOI <= mo <= SIDEWAY_TREN:
        return False, f"cung mở tại RSI {mo:.0f} — trong dải 40-60, cắt vô nghĩa"
    if d.get("trend") == 0:
        return False, "hai đường quấn nhau, không có độ dốc (b3 2:38)"
    return True, f"cung mở {mo:.0f} → đóng {c.get('rsi_dong')} · đủ 3 điều kiện"


def diem_a_pham(d, so_nen_moi=6):
    """
    A' (b2 1:23:02) = điểm KẾT THÚC vòng cung — lúc giá "dừng giảm và bắt đầu tăng dần".
    Thầy: mua ở A', KHÔNG mua ở A (lúc còn đang rơi).
    Cung vừa đóng trong `so_nen_moi` nến gần đây thì coi là A' còn tươi.
    """
    c = d.get("cung") or {}
    if c.get("trang_thai") != "da_hoan_thanh":
        return None
    # ⚠️ TRƯỚC 07/09/2026 chỗ này đọc nhầm c["so_nen"] — với cung đã đóng đó là
    #    CHIỀU DÀI cung, không phải tuổi. Nên nó lọc "cung NGẮN" chứ không phải
    #    "cung VỪA ĐÓNG" → A' chưa bao giờ được đo đúng.
    tuoi = c.get("tuoi")
    if tuoi is None or tuoi > so_nen_moi:
        return None
    return {"chieu": 1 if c.get("chuan_bi") == "tang" else -1,
            "rsi_dong": c.get("rsi_dong"), "cach_day": tuoi}


def nguoc_pha_sat_suon(bang, tf):
    """
    CẤM (b17 49:37): mô hình ngược pha với khung SÁT SƯỜN thì bỏ qua.
      "H1 đi xuống có mô hình ngược pha với H2 thì thôi bỏ qua. Không thể nào
       short theo target của H1 được."
    Có mô hình VẪN CHƯA ĐỦ — nó còn phải không bị khung sát sườn ghì ngược.
    """
    d = bang.get(tf)
    if not d or d["trend"] == 0:
        return None
    ke = []
    for cum in SAT_SUON:
        if tf in cum:
            ke = [t for t in cum if t != tf and t in bang]
            break
    if not ke:
        return None
    nguoc = [bang[t] for t in ke if bang[t]["trend"] != 0 and bang[t]["trend"] != d["trend"]]
    if not nguoc:
        return {"bo": False, "ket_luan": f"{d['nhan']} không bị khung sát sườn ghì"}
    ten = ", ".join(x["nhan"] for x in nguoc)
    return {"bo": True, "nguoc": [x["tf"] for x in nguoc],
            "ket_luan": f"BỎ — {d['nhan']} {'lên' if d['trend']==1 else 'xuống'} nhưng "
                        f"ngược pha {ten} → sẽ vướng lực ngược của khung sát sườn (b17)"}


def muc_tieu_theo_khung(bang, tf, chieu):
    """
    QUY LUẬT 2 (b8 42:29): "Sóng của khung nào sẽ tìm về kháng cự hỗ trợ CỦA KHUNG ĐÓ."
    Ăn sóng khung nào thì target mốc của chính khung đó — không lấy mốc khung khác.
    """
    d = bang.get(tf)
    if not d:
        return None
    moc = d.get("khang_cu") if chieu == 1 else d.get("ho_tro")
    if not moc:
        return None
    return {"tf": tf, "muc": moc["muc"], "cach": moc["cach"], "test": moc["lan_test"],
            "ket_luan": f"ăn sóng {d['nhan']} → target {moc['muc']} "
                        f"({moc['cach']:+.2f}%, {moc['lan_test']} lần test)"}


def soi_kheo(bang, tf):
    """
    Gộp quy trình b9 cho MỘT khung: có mô hình chưa · A' còn tươi không ·
    có bị khung sát sườn ghì không · target ở đâu. Chỉ BÀY, mắt quyết.
    """
    d = bang.get(tf)
    if not d:
        return None
    ok, vi_sao = co_mo_hinh(d)
    ap = diem_a_pham(d)
    ng = nguoc_pha_sat_suon(bang, tf)
    chieu = d["trend"] or (ap or {}).get("chieu", 0)
    mt = muc_tieu_theo_khung(bang, tf, chieu) if chieu else None

    dong = [f"{d['nhan']} · {'CÓ MÔ HÌNH' if ok else 'KHÔNG có mô hình'} — {vi_sao}"]
    if ap:
        dong.append(f"A' {'tăng' if ap['chieu']==1 else 'giảm'} cách đây {ap['cach_day']} nến "
                    f"(cung đóng ở RSI {ap['rsi_dong']})")
    if ng:
        dong.append(ng["ket_luan"])
    if mt:
        dong.append(mt["ket_luan"])
    return {"tf": tf, "co_mo_hinh": ok, "vi_sao": vi_sao, "a_pham": ap,
            "nguoc_pha": ng, "muc_tieu": mt,
            "vao_duoc": bool(ok and ap and not (ng or {}).get("bo")),
            "ket_luan": " · ".join(dong)}


# ==================== CHỤP ẢNH ĐA KHUNG (ghi vào nhật ký) ====================
# Chụp TẠI THỜI ĐIỂM kèo bắn / lệnh khớp, không phải đọc panel live sau này.
# Panel live ≠ nến entry: xem lại lệnh cũ mà đọc panel hôm nay là đọc nhầm thị trường khác.

NHOM_HIEN = [("NGẮN", ["5m", "15m", "30m", "1h"]),
             ("TRUNG", ["2h", "4h", "6h", "8h"]),
             ("DÀI", ["12h", "1d", "2d", "3d"])]


def _gon_mot_khung(d):
    """M5 81▲ m100 ▲mở x—   ->  rsi · hướng · độ mạnh · nở · xăng"""
    h = {1: "▲", -1: "▼", 0: "—"}[d["trend"]]
    no = "—" if not d.get("pha") else ("mở" if d["pha"] == "mo_ra" else "khép")
    xg = xang_chu(d["xang"])
    return f"{d['nhan']} {d['rsi']:.0f}{h} m{(d['manh'] or 0):.0f} {no} x{xg}"


def _tom_tat(bang):
    """Khung nào đang cầm quyết định, chế độ gì — tính 1 lần lúc chụp cho web khỏi tính lại."""
    # ⭐ KHUNG NẮM QUYỀN = khung có LỰC RÕ NHẤT, KHÔNG phải khung to nhất.
    # Kevin chốt 26/08/2026 (note 52): cách cũ duyệt 1D->H4->H1 lấy khung LỚN NHẤT còn trend
    # là SAI. Căn cứ b15: mô hình chỉ tính khi có ĐỘ DỐC + ĐỘ MỞ RỘNG; khung nào lộn xộn,
    # không rõ tín hiệu thì dời sang khung lân cận mà quan sát.
    # Đo "lực rõ": độ mạnh (mở rộng so với chính lịch sử khung đó) + đang NỞ RA thêm.
    ung_vien = []
    for t, d in bang.items():
        if d["trend"] == 0 or d["manh"] is None:
            continue
        nr = d["no_rong"] or 0.0
        # đang mở rộng thì lực còn tăng; đang khép thì lực đang mất -> hạ bậc
        diem = d["manh"] + (min(nr, 15.0) * 2.0 if nr > 0 else nr * 2.0)
        ung_vien.append((diem, d["manh"], nr, t, d["trend"]))
    dan, huong = None, 0
    if ung_vien:
        ung_vien.sort(reverse=True)
        dan, huong = ung_vien[0][3], ung_vien[0][4]
    xep_hang = [(t, round(dm, 1), m, nr) for dm, m, nr, t, _ in ung_vien[:5]]
    # chế độ theo cụm D/H4/H1
    len_ = sum(1 for t in ("1d", "4h", "1h") if bang.get(t, {}).get("trend") == 1)
    xuong = sum(1 for t in ("1d", "4h", "1h") if bang.get(t, {}).get("trend") == -1)
    if len_ and xuong:
        che_do = "SIDEWAY nguoc pha"
    elif len_ >= 2:
        che_do = "TREND tang"
    elif xuong >= 2:
        che_do = "TREND giam"
    else:
        che_do = "SIDEWAY chua ro"
    mo = sum(1 for t in ("1d", "2d", "3d") if (bang.get(t, {}).get("no_rong") or 0) > 0)
    khep = sum(1 for t in ("1d", "2d", "3d") if (bang.get(t, {}).get("no_rong") or 0) < 0)
    # ⭐ GIÁ ĐANG ĐỨNG Ở ĐÂU — hỏi TRƯỚC khi đọc RSI.
    # Kevin sửa 28/08/2026: "vô bừa theo RSI mà không chịu nhìn giá đang nằm ở khu vực nào".
    # Kèo XAUT LONG 28/08 thắng vì giá nằm NGAY HỖ TRỢ cục bộ — M5 hướng lên từ đó là bật
    # lên đúng nền. RSI đa khung không thấy được điều này; nó chỉ đo lực, không đo VỊ TRÍ.
    vi_tri = []
    for tf in ("5m", "15m", "1h", "4h", "1d"):
        d = bang.get(tf)
        if not d:
            continue
        h, k = d.get("ho_tro"), d.get("khang_cu")
        if h and abs(h["cach"]) <= 1.0:          # trong 1% -> coi là ĐANG ĐỨNG TRÊN nền
            vi_tri.append((abs(h["cach"]), tf, "ho_tro", h["muc"], h["cach"], h["lan_test"]))
        if k and abs(k["cach"]) <= 1.0:
            vi_tri.append((abs(k["cach"]), tf, "khang_cu", k["muc"], k["cach"], k["lan_test"]))
    vi_tri.sort()
    vi_tri = [{"tf": t, "loai": l, "muc": m, "cach": c, "test": n}
              for _, t, l, m, c, n in vi_tri[:4]]

    return {"dan": dan, "huong": huong, "che_do": che_do, "xep_hang": xep_hang,
            "vi_tri": vi_tri,
            "pha_lon": "mo_ra" if mo >= 2 else "khep_lai" if khep >= 2 else "chua_ro",
            "bc": (ban_chat_song(bang, dan) or {}).get("ket_luan") if dan else None}


def _feature_qm(bars_m5, nhin_lai=20):
    """
    3 feature của QM QUALITY SCORE (note 50, validated OOS 3 chiều):
      m5os  = 50 - RSI(M5) tại ĐÁY  -> cao là tốt (oversold sâu, spring mạnh)
      bostr = RSI(M5) hiện tại - RSI đáy -> THẤP là tốt (bo nhẹ/sớm, bật mạnh = trễ = đu)
    xang lấy từ RSI H1 ở chỗ gọi. Đáy = RSI thấp nhất trong `nhin_lai` nến gần nhất.

    ⚠ ĐÂY LÀ XẤP XỈ, chỉ dùng để dò nhanh. Đo lại 27/08 cho gradient ĐẢO (Q1 56% > Q4 45%)
    trong khi bản đúng (head_idx của setup) cho gradient PHẲNG. Hai thang khác nhau —
    đừng ghép số của hàm này với bộ chuẩn hóa trong web.
    """
    try:
        r = rsi([b[4] for b in bars_m5], 14)
        gan = [x for x in r[-nhin_lai:] if x is not None]
        if len(gan) < 5 or r[-1] is None:
            return None, None
        day = min(gan)
        return round(50.0 - day, 2), round(r[-1] - day, 2)
    except Exception:
        return None, None


def chup_da_khung(lay_nen, symbol, khung=None, so_nen=200, f_ngoai=None):
    """
    Trả (text, nen) để ghi vào 2 cột nhật ký:
      text — người đọc: 3 dòng NGẮN / TRUNG / DÀI
      nen  — máy đọc: {"5m": [rsi, manh, trend, xang, no_rong], ...} để phân tích sau

    Mọi lỗi đều nuốt và trả ("", "") — chụp ảnh KHÔNG được phép làm hỏng việc ghi lệnh.
    """
    try:
        bang = doc_moi_khung(lay_nen, symbol, khung, so_nen)
        if not bang:
            return "", ""
        dong = []
        for ten, ds in NHOM_HIEN:
            cot = [_gon_mot_khung(bang[t]) for t in ds if t in bang]
            if cot:
                dong.append(f"{ten}: " + " · ".join(cot))
        nen = {t: [round(d["rsi"], 1), round(d["manh"] or 0, 1), d["trend"],
                   None if d["xang"] is None else round(d["xang"], 1),
                   d.get("no_rong")]
               for t, d in bang.items()}
        tt = _tom_tat(bang)
        # 3 feature — note 50. `xang` ở đây là feature riêng, KHÁC cột "xăng" đa khung.
        # m5os/bostr PHẢI do bot tính (RSI tại head_idx + RSI lúc đặt lệnh). Không có thì
        # để trống: xấp xỉ bằng "min 20 nến" khác thang với bộ chuẩn hóa -> số σ sai.
        r_h1 = bang.get("1h", {}).get("rsi")
        sh = bool(f_ngoai and f_ngoai.get("short"))
        xang = None if r_h1 is None else round((r_h1 - 60.0) if sh else (60.0 - r_h1), 2)
        tt["f"] = {"m5os": (f_ngoai or {}).get("m5os"),
                   "bostr": (f_ngoai or {}).get("bostr"),
                   "xang": xang}
        nen["_"] = tt
        return "\n".join(dong), json.dumps(nen, separators=(",", ":"), ensure_ascii=False)
    except Exception as e:
        log.warning("chup_da_khung %s loi: %s", symbol, e)
        return "", ""
