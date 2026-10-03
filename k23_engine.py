# -*- coding: utf-8 -*-
"""
K23 ENGINE — tín hiệu RSI THUẦN THẦY, chạy ĐỘC LẬP song song với QM.
Không phải filter cho QM. Không sáng tạo luật.

QUY TRÌNH (mọi luật đều trích được từ transcript):
  1. Quét khung, tìm khung CÓ MÔ HÌNH        cung đóng · mở ngoài 40-60 · có dốc   b8·b15·b3
  2. Trên khung đó xác định cú A              sóng có quán tính RSI ≥80 / ≤20        b4·b15
  3. Kẻ fibo của A, chờ giá hồi 0.5-0.618     = sóng B (điều chỉnh)                  b15
  4. Chờ C XÁC NHẬN: EMA9 cắt WMA45           giá về đỉnh cũ mà chưa cắt = BẪY       b15:2242
  5. ENTRY tại đó
     SL (a) dưới fibo 0.618  (b) RSI khỏi dải 40-60                          Kevin 07/09
  6. TP = KC/HT của khung CÓ MÔ HÌNH          "sóng khung nào về KC/HT khung đó"     b8
  7. risk 1%                                                                        b8

SỐ CỦA MÌNH (không có trong transcript — khai để kiểm lại được):
  - ngưỡng "RSI ra khỏi dải" = 40/60, đúng dải thầy nói, không thêm mức nào khác
  - KC/HT dò bằng pivot fractal 2 nến mỗi bên (như k23_dakhung.pha_ho_tro)
  - cú A lấy swing gần nhất SAU khi cung đóng, tối đa 200 nến
"""
import bisect

SIDEWAY_DUOI, SIDEWAY_TREN = 40.0, 60.0
QUAN_TINH_TREN, QUAN_TINH_DUOI = 80.0, 20.0     # b4 GĐ2 — quán tính
FIB_GAN, FIB_XA = 0.5, 0.618                     # vùng B
PIVOT = 2                                        # fractal 2 bên


def _pivots(bars, chieu, L=PIVOT):
    """chieu=1 → đáy (low); chieu=-1 → đỉnh (high). Trả [(idx, giá)]."""
    cot = 3 if chieu == 1 else 2
    out = []
    for i in range(L, len(bars) - L):
        v = bars[i][cot]
        if chieu == 1 and all(v <= bars[j][cot] for j in range(i - L, i + L + 1) if j != i):
            out.append((i, v))
        elif chieu == -1 and all(v >= bars[j][cot] for j in range(i - L, i + L + 1) if j != i):
            out.append((i, v))
    return out


def muc_kc_ht(bars, chieu, gia):
    """KC/HT gần nhất theo hướng lệnh, trên chính khung CÓ MÔ HÌNH (b8 quy luật 2).
       chieu=1 (long) → kháng cự ở TRÊN; chieu=-1 (short) → hỗ trợ ở DƯỚI."""
    pv = _pivots(bars, -chieu)
    if chieu == 1:
        tren = [p for _, p in pv if p > gia]
        return min(tren) if tren else None
    duoi = [p for _, p in pv if p < gia]
    return max(duoi) if duoi else None


def tim_cu_A(bars, r, i_dong, chieu, toi_da=200):
    """
    Cú A = sóng có QUÁN TÍNH sau khi cung đóng (b4 GĐ2: RSI đóng nến ≥80 / ≤20).
    Trả (gia_dau, gia_cuoi, i_cuoi) hoặc None nếu sóng chưa đạt quán tính.
    """
    n = len(bars)
    if i_dong >= n - 1:
        return None
    het = min(n, i_dong + toi_da)
    dat_quan_tinh = False
    i_cuc = i_dong
    for i in range(i_dong, het):
        rv = r[i]
        if rv is None:
            continue
        if chieu == 1:
            if rv >= QUAN_TINH_TREN:
                dat_quan_tinh = True
            if bars[i][2] > bars[i_cuc][2]:
                i_cuc = i
        else:
            if rv <= QUAN_TINH_DUOI:
                dat_quan_tinh = True
            if bars[i][3] < bars[i_cuc][3]:
                i_cuc = i
    if not dat_quan_tinh:
        return None                                   # chưa có quán tính → chưa phải A
    gia_dau = bars[i_dong][3] if chieu == 1 else bars[i_dong][2]
    gia_cuoi = bars[i_cuc][2] if chieu == 1 else bars[i_cuc][3]
    if (gia_cuoi - gia_dau) * chieu <= 0:
        return None
    return (gia_dau, gia_cuoi, i_cuc)


def vung_fibo(gia_dau, gia_cuoi):
    """Vùng B = fibo 0.5 → 0.618 của cú A. Trả (mức gần, mức xa) theo giá."""
    bien = gia_cuoi - gia_dau
    return (gia_cuoi - bien * FIB_GAN, gia_cuoi - bien * FIB_XA)


def fibo_mo_rong(gia_dau, gia_cuoi, muc):
    """TP2 — chốt lời theo fibo (Kevin 07/09). Mức 1.272/1.618 là số CHUẨN PHỔ BIẾN,
       thầy KHÔNG nêu mức cụ thể -> chạy cả hai rồi để data chọn."""
    return gia_cuoi + (gia_cuoi - gia_dau) * (muc - 1.0)


def fibo_co_gia_tri(bars_mh, chieu, fib_gan, fib_xa, sai_so=0.003):
    """
    ⭐ b12 ~1:31:40 — thầy chỉnh thẳng cái lỗi phổ biến nhất:
       "Fibo là cái để ĐO LƯỜNG, không phải DỰ BÁO. Cái 0.5 KHÔNG CÓ GIÁ TRỊ GÌ CẢ
        cho đến khi nó có một vùng đáy hay vùng hỗ trợ ở đó."
    -> vùng fibo phải TRÙNG một đáy/đỉnh thật của khung mô hình mới được vào.
    (sai_so 0.3% = số của mình, lấy cùng ngưỡng TEST_SAI_SO trong k23_dakhung.)
    """
    lo, hi = min(fib_gan, fib_xa), max(fib_gan, fib_xa)
    for _, gia in _pivots(bars_mh, chieu):
        if lo * (1 - sai_so) <= gia <= hi * (1 + sai_so):
            return gia
    return None


def day_gan_nhat(bars, chieu, n=40):
    """b12 ~1:30:22 — "nếu nó phá cái ĐÁY GẦN NHẤT là em chốt luôn, không đợi Fibo 0.5".
       Vào theo khung lớn, THOÁT theo khung nhỏ."""
    pv = _pivots(bars[-n:], chieu)
    if not pv:
        return None
    return pv[-1][1]


def c_xac_nhan(f, s, i, chieu):
    """
    C XÁC NHẬN = EMA9 cắt WMA45 đúng chiều tại nến i (b15:2225).
    ⚠️ BẪY b15:2242 — giá về đỉnh cũ mà CHƯA cắt thì RSI vẫn đang điều chỉnh, chưa phải C.
    """
    if i < 1 or f[i] is None or s[i] is None or f[i-1] is None or s[i-1] is None:
        return False
    if chieu == 1:
        return f[i-1] <= s[i-1] and f[i] > s[i]
    return f[i-1] >= s[i-1] and f[i] < s[i]


def sl_theo_luc(rsi_val, chieu):
    """SL (b) — RSI ra khỏi dải 40-60 theo chiều bất lợi (Kevin 07/09)."""
    if rsi_val is None:
        return False
    return rsi_val < SIDEWAY_DUOI if chieu == 1 else rsi_val > SIDEWAY_TREN


# ══════════════════════════════════════════════════════════════════════
#  BACKTEST — chạy đúng 6 bước, KHÔNG dùng gì của QM
# ══════════════════════════════════════════════════════════════════════
def quet(bars_mh, bars_e, K, ten_mh="", ten_e="", fib_ext=1.618):
    """
    bars_mh = khung CÓ MÔ HÌNH · bars_e = khung ENTRY (b11: "em cứ quan sát từ M5").
    ENTRY  fibo 0.5-0.618 của cú A, VÀ vùng đó TRÙNG đáy/đỉnh thật (b12), VÀ C xác nhận (b15)
    TP1    đỉnh cũ (b15 "C ít nhất về đỉnh cũ") — chốt 50% (b10 "chốt nửa lệnh")
    TP2    fibo mở rộng — chốt nốt                                        (Kevin 07/09)
    SL     (a) dưới fibo 0.618  (b) RSI khỏi dải 40-60  (c) phá đáy gần nhất khung entry (b12)
    Chỉ dùng dữ liệu <= nến hiện tại.
    """
    cl_mh = [b[4] for b in bars_mh]
    r_mh = K.rsi(cl_mh, 14); f_mh = K._ema(r_mh, 9); s_mh = K._wma(r_mh, 45)
    ci = dung_chi_muc(r_mh, f_mh, s_mh); ci["r"] = r_mh     # tra cung O(log n)
    cl_e = [b[4] for b in bars_e]
    r_e = K.rsi(cl_e, 14); f_e = K._ema(r_e, 9); s_e = K._wma(r_e, 45)
    t_mh = [b[0] for b in bars_mh]

    lenh = []; giu = None; cho = None
    for j in range(60, len(bars_e)):
        bar = bars_e[j]; ts = bar[0]
        if giu:
            d = giu; ch = d["chieu"]; R1 = abs(d["entry"] - d["sl0"])
            gia = bar[4]

            # ── PHẦN 1 (50%) — TP1 = đỉnh cũ. Đây là 8/10 lệnh "chốt non".  b15 · b10
            if not d["p1"] and ((bar[2] >= d["tp1"]) if ch == 1 else (bar[3] <= d["tp1"])):
                d["p1"] = True
                d["r"] += abs(d["tp1"] - d["entry"]) / R1 * 0.50

            # ── PHẦN 2 (25%) — TP2 = fibo mở rộng                          Kevin 07/09
            if d["p1"] and not d["p2"] and ((bar[2] >= d["tp2"]) if ch == 1 else (bar[3] <= d["tp2"])):
                d["p2"] = True
                d["r"] += abs(d["tp2"] - d["entry"]) / R1 * 0.25

            # ── PHẦN 3 (25%) — GỒNG, KHÔNG có TP cứng.
            #    Đây là chỗ sinh ra 2/10 lệnh ăn dài; cắt sớm phần này = giết cả hệ.
            #    Trail theo ĐÁY CAO DẦN của khung nhỏ (b12 ~1:29:55, thầy xác nhận "Đúng rồi").
            if d["p1"]:
                mc = day_gan_nhat(bars_e[:j], ch)
                if mc is not None and (mc - d["sl"]) * ch > 0:
                    d["sl"] = mc                       # chỉ dời theo hướng lợi

            cham_sl = bar[3] <= d["sl"] if ch == 1 else bar[2] >= d["sl"]
            con = 1.0 - (0.50 if d["p1"] else 0) - (0.25 if d["p2"] else 0)
            xong = None
            if cham_sl:
                if not d["p1"]:
                    d["r"] += -1.0; xong = "SL (dưới fibo 0.618)"
                else:
                    d["r"] += (d["sl"] - d["entry"]) * ch / R1 * con
                    xong = "trail đáy cao dần (b12)"
            elif not d["p1"] and sl_theo_luc(r_e[j], ch):
                # SL theo LỰC chỉ áp khi CHƯA chốt phần nào — sau TP1 thì để cấu trúc quản.
                d["r"] += (gia - d["entry"]) * ch / R1; xong = "RSI khỏi dải 40-60"
            elif con <= 0.001:
                xong = "TP2 (fibo mở rộng)"
            if xong:
                d["ly_do"] = xong; d["ts_thoat"] = ts; lenh.append(d); giu = None
            continue

        i = bisect.bisect_right(t_mh, ts) - 1
        if i < 60:
            continue
        # Khoá setup theo ĐIỂM ĐÓNG CUNG, không theo nến hiện tại — nếu khoá theo nến thì
        # mỗi lần khung mô hình sang nến mới, setup bị dựng lại và MẤT cờ "đã chạm vùng B".
        c = cung_tai(ci, i)
        i_dong_ht = (i - (c["tuoi"] or 0)) if c["trang_thai"] == "da_hoan_thanh" else None
        if cho is not None and cho.get("i_dong") != i_dong_ht:
            cho = None                      # đã sang vòng cung KHÁC -> bỏ setup cũ
        if cho is None and i_dong_ht is not None:
            mo = c["rsi_mo"]
            if mo is not None and not (SIDEWAY_DUOI <= mo <= SIDEWAY_TREN):
                ch = 1 if c["chuan_bi"] == "tang" else -1
                A = tim_cu_A(bars_mh[:i+1], r_mh[:i+1], i_dong_ht, ch)
                if A:
                    g0, g1, _ = A
                    fg, fx = vung_fibo(g0, g1)
                    # ⭐ b12: fibo KHÔNG có giá trị nếu chỗ đó không có đáy/đỉnh thật
                    neo = fibo_co_gia_tri(bars_mh[:i+1], ch, fg, fx)
                    if neo is not None:
                        cho = {"i_dong": i_dong_ht, "chieu": ch, "fib_gan": fg,
                               "fib_xa": fx, "dinh_A": g1, "day_A": g0, "neo": neo}
        if not cho:
            continue
        ch = cho["chieu"]
        lo_f, hi_f = min(cho["fib_gan"], cho["fib_xa"]), max(cho["fib_gan"], cho["fib_xa"])
        # B — giá ĐÃ hồi vào vùng fibo (ghi nhớ, không đòi còn nằm trong đó).
        if lo_f <= bar[4] <= hi_f:
            cho["cham_B"] = True
        # mô hình hỏng: hồi SÂU hơn 0.618 -> "con sóng đã rất yếu rồi" (b10 ~2:41)
        if cho.get("cham_B") and (bar[4] < lo_f if ch == 1 else bar[4] > hi_f):
            cho = None
            continue
        if not cho.get("cham_B"):
            continue
        # C — EMA9 cắt WMA45 (b15). Lúc này giá ĐÃ rời vùng hồi đi lên: đó chính là
        # sóng tiếp diễn bắt đầu. Đòi giá còn trong vùng lúc cắt là bắt điều không xảy ra.
        if not c_xac_nhan(f_e, s_e, j, ch):
            continue
        entry = bar[4]
        sl = cho["fib_xa"] - (abs(cho["dinh_A"] - cho["fib_xa"]) * 0.02) * ch
        tp1 = cho["dinh_A"]
        tp2 = fibo_mo_rong(cho["day_A"], cho["dinh_A"], fib_ext)
        if (entry - sl) * ch <= 0 or (tp1 - entry) * ch <= 0:
            continue
        giu = {"ts": ts, "chieu": ch, "entry": entry, "sl": sl, "sl0": sl,
               "tp1": tp1, "tp2": tp2, "r": 0.0, "p1": False, "p2": False,
               "khung_mh": ten_mh, "khung_e": ten_e,
               "rr": abs(tp1 - entry) / abs(entry - sl),
               "rr2": abs(tp2 - entry) / abs(entry - sl)}
        cho = None
    return lenh


# ══════════════════════════════════════════════════════════════════════
#  TĂNG TỐC — kết quả PHẢI y hệt K.trang_thai_cung, chỉ khác cách tính.
#  Bản gốc quét lại toàn bộ điểm cắt ở MỖI nến -> O(n²). Ở đây tính điểm cắt
#  MỘT LẦN rồi tra bằng bisect, và dựng sẵn mảng cộng dồn để hỏi "RSI đã thoát
#  dải 40-60 chưa" trong O(1).
# ══════════════════════════════════════════════════════════════════════
def dung_chi_muc(r, f, s):
    cat = []
    truoc = None
    for i in range(len(f)):
        if f[i] is None or s[i] is None:
            continue
        dau = 1 if f[i] > s[i] else (-1 if f[i] < s[i] else 0)
        if dau == 0:
            continue
        if truoc is not None and dau != truoc:
            cat.append((i, "xuong" if dau < 0 else "len"))
        truoc = dau
    n = len(r)
    duoi = [0] * (n + 1)      # số nến có RSI < 40 tính tới i
    tren = [0] * (n + 1)      # số nến có RSI > 60 tính tới i
    for i in range(n):
        rv = r[i]
        duoi[i+1] = duoi[i] + (1 if rv is not None and rv < SIDEWAY_DUOI else 0)
        tren[i+1] = tren[i] + (1 if rv is not None and rv > SIDEWAY_TREN else 0)
    return {"cat": cat, "idx": [c[0] for c in cat], "duoi": duoi, "tren": tren}


def _thoat(ci, tu_i, chieu, den_i):
    m = ci["duoi"] if chieu == "mua" else ci["tren"]
    het = min(den_i + 1, len(m) - 1)
    return het > tu_i and m[het] - m[tu_i] > 0


def cung_tai(ci, i):
    """Bản O(log n) của K.trang_thai_cung(r[:i+1], f[:i+1], s[:i+1])."""
    k = bisect.bisect_right(ci["idx"], i)
    kq = {"trang_thai": "chua_co", "rsi_mo": None, "rsi_dong": None,
          "so_nen": 0, "tuoi": None, "chuan_bi": None}
    if k == 0:
        return kq
    cat = ci["cat"]
    R = ci["r"]

    def hop_le(i_cat, loai, i_den):
        rv = R[i_cat] if i_cat < len(R) else None
        if rv is None:
            return False
        if rv < SIDEWAY_DUOI or rv > SIDEWAY_TREN:
            return True
        return _thoat(ci, i_cat, "mua" if loai == "xuong" else "ban", i_den)

    if k >= 2:
        i_mo, l_mo = cat[k-2]
        i_dong, l_dong = cat[k-1]
        if l_mo != l_dong and hop_le(i_mo, l_mo, i_dong):
            kq.update(trang_thai="da_hoan_thanh", rsi_mo=round(R[i_mo], 1),
                      rsi_dong=round(R[i_dong], 1) if R[i_dong] is not None else None,
                      so_nen=i_dong - i_mo, tuoi=i - i_dong,
                      chuan_bi="tang" if l_mo == "xuong" else "giam")
            return kq
    i_c, l_c = cat[k-1]
    if i_c >= len(R) or R[i_c] is None:
        return kq
    if hop_le(i_c, l_c, i):
        kq.update(trang_thai="dang_chay", rsi_mo=round(R[i_c], 1), so_nen=i - i_c,
                  chuan_bi="tang" if l_c == "xuong" else "giam")
    else:
        kq.update(trang_thai="trong_sideway", rsi_mo=round(R[i_c], 1), so_nen=i - i_c)
    return kq
