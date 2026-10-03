# -*- coding: utf-8 -*-
"""
TƯƠNG QUAN GIÁ ↔ RSI ↔ VOLUME — đọc bản chất phiên đang chạy.

⚠️ BẢN TRƯỚC (07/09) SAI NGƯỢC. Nó chấm MỘT CHIỀU bằng độ nhạy rồi gán
   "nhạy cao = lực RỖNG = thanh khoản mỏng". Đo trên BTC/ETH/XAUT khung H1
   (903 cửa sổ mỗi coin) thì ngược hẳn:
        nhạy CAO  -> volume 128-162% nền   (phiên SÔI ĐỘNG, tiền vào thật)
        nhạy THẤP -> volume  31- 54% nền   (thị trường NGỦ)
   Kevin bắt đúng chỗ: "thanh khoản mỏng" và "không có lực bán" nhìn một chiều thì
   giống hệt nhau. Phải HAI CHIỀU — nhạy + volume — mới tách được.

CÁCH TÍNH
  độ nhạy mỗi nến = |Δ% giá| / |Δ RSI|      -> % giá trên 1 điểm RSI
  (giá quy về % nên BTC 80.000 và BEAT 0,125 so được với nhau)
  nhạy_tỉ_lệ = trung vị 20 nến cuối / trung vị 200 nến trước
  vol_tỉ_lệ  = trung vị volume 20 nến cuối / trung vị volume 200 nến trước
  Trung vị chứ không phải trung bình cộng: một nến RSI đứng mà giá nhảy đủ kéo
  lệch cả nền (BEAT 4h từng ra nền 3.2 trong khi thực tế ~0.3).

MA TRẬN ĐỌC  (Kevin 08/09: ô sôi động phải ghi rõ PHE NÀO áp đảo)
  "Lúc có FOMO theo tin tức: 9 người mua 1 người bán -> LỰC MUA ÁP ĐẢO, và ngược lại"
  -- Kevin 08/09. Đúng định nghĩa RSI của thầy: "RSI là TỈ SỐ lực mua, lực bán" (b3 206).
  Không mượn khái niệm ngoài: "hung hãn" xuất hiện 0/55 buổi, không phải ngôn ngữ hệ này.

                  volume THẤP                    volume CAO
  nhạy CAO   ->   MỎNG    sổ lệnh trống,   |  LỰC MUA/BÁN ÁP ĐẢO
                          giá nhảy         |    tỉ số lực nghiêng hẳn một phe
  nhạy THẤP  ->   NGỦ     không có V ->    |  HẤP THỤ  nhiều tiền mà giá không
                          K0 đứng ngoài    |           nhích: có người đỡ/chặn
  Chiều lấy từ đoạn ngắn: giá LÊN và RSI LÊN -> phe MUA; cùng XUỐNG -> phe BÁN.

🔴 LỆCH CHIỀU = "TẠM NGHỈ", KHÔNG PHẢI TÍN HIỆU ĐẢO (b3 — thầy bắt ghi vào):
   "Sóng điều chỉnh trong một xu hướng tăng mạnh nó là sự TẠM NGHỈ CỦA LỰC MUA,
    chứ không phải sự gia tăng của lực bán."                          b3 1798
   "Xu hướng giảm của RSI KHÔNG đồng nghĩa với xu hướng giảm của giá... đến khi
    nào CÓ SỰ GIA TĂNG CỦA LỰC BÁN thì lúc đấy mới tạo ra sóng giảm."  b3 4499
   "trong giai đoạn CÓ XU HƯỚNG thì tín hiệu PHÂN KỲ đơn giản chỉ là sự tạm nghỉ
    của lực mua, không phải lực bán ĐỂ MÀ CHÚNG TA CÓ THỂ SHORT Ở ĐÓ."  b3 3263
   Phân biệt bằng cách KẾT HỢP VỚI ĐƯỜNG GIÁ (b3 4174):
       RSI xuống + giá KHÔNG xuống -> lực mua TẠM NGHỈ   -> CẤM SHORT
       RSI xuống + giá XUỐNG theo   -> lực bán ĐÃ VÀO    -> mới là sóng giảm thật

Nguồn: b3 206 "RSI là tỉ số lực mua/lực bán" · b10 4252 "giá điều chỉnh xuống sâu
thì RSI PHẢI cắm xuống" · b10 5780 thầy nói volume "mình BỔ TRỢ thôi" · b4 2221
thầy BÁC quy tương quan thành công thức -> chỉ BÀY, KHÔNG dùng làm bộ lọc.
"""

BO_QUA_RSI = 0.30      # ΔRSI nhỏ hơn mức này coi như RSI đứng yên -> bỏ, tránh chia số gần 0
NGAN, DAI  = 20, 200   # cửa sổ hiện tại / cửa sổ nền

# 🟡 SỐ CỦA MÌNH — chưa đo trên kết quả lệnh. Chỉ để phân ô, KHÔNG để lọc.
CAO, THAP = 140.0, 70.0              # mốc độ nhạy
V_CAO, V_THAP = 120.0, 70.0          # mốc volume
FAIL_DUOI, FAIL_TREN = 40.0, 250.0   # ngoài dải này thì không diễn giải


def _med(xs):
    if not xs:
        return None
    v = sorted(xs); n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def _nhay(closes, rsi):
    """(chỉ số nến, % giá trên 1 điểm RSI)."""
    ra = []
    for i in range(1, len(closes)):
        if rsi[i] is None or rsi[i - 1] is None or closes[i - 1] <= 0:
            continue
        dr = abs(rsi[i] - rsi[i - 1])
        if dr < BO_QUA_RSI:
            continue
        ra.append((i, abs(closes[i] - closes[i - 1]) / closes[i - 1] * 100.0 / dr))
    return ra


def _ti_le(v):
    """(hiện tại, nền, tỉ lệ %) — trung vị cửa sổ ngắn so trung vị cửa sổ nền."""
    if len(v) < NGAN + 30:
        return None
    ht = _med(v[-NGAN:])
    nen = _med(v[-(NGAN + DAI):-NGAN] or v[:-NGAN])
    if not ht or not nen or nen <= 0:
        return None
    return ht, nen, ht / nen * 100.0


def do_tuong_quan(closes, rsi, vols=None):
    """
    vols = volume từng nến (bar[5]). Thiếu volume thì KHÔNG dán nhãn ô — vì một
    chiều không tách được MỎNG với HẤP THỤ, đúng chỗ Kevin bắt lỗi 08/09.
    """
    nh = _nhay(closes, rsi)
    kq_n = _ti_le([x[1] for x in nh])
    if not kq_n:
        return None
    n_ht, n_nen, n_ti = kq_n

    i0 = nh[-NGAN][0]
    d_gia = (closes[-1] - closes[i0]) / closes[i0] * 100.0 if closes[i0] > 0 else 0.0
    d_rsi = (rsi[-1] - rsi[i0]) if (rsi[-1] is not None and rsi[i0] is not None) else 0.0

    out = {"nhay": round(n_ht, 5), "nhay_nen": round(n_nen, 5), "nhay_ti": round(n_ti),
           "vol_ti": None, "d_gia": round(d_gia, 2), "d_rsi": round(d_rsi, 1),
           "nhan": None, "y_nghia": ""}

    if n_ti < FAIL_DUOI or n_ti > FAIL_TREN:
        out["nhan"], out["y_nghia"] = "FAIL", "số liệu bất thường — không đọc"
        return out

    if vols is None:
        out["nhan"] = "THIẾU VOL"
        out["y_nghia"] = "chưa có volume — một chiều không tách được mỏng / hấp thụ"
        return out

    kq_v = _ti_le([vols[i] for i, _ in nh if i < len(vols) and vols[i] > 0])
    if not kq_v:
        out["nhan"], out["y_nghia"] = "THIẾU VOL", "volume rỗng hoặc bằng 0"
        return out
    out["vol_ti"] = round(kq_v[2])

    nhay_cao, nhay_thap = n_ti >= CAO, n_ti <= THAP
    vol_cao, vol_thap = kq_v[2] >= V_CAO, kq_v[2] <= V_THAP

    # CHIỀU của đoạn ngắn: giá và RSI cùng đi lên -> phe MUA đang thắng, và ngược lại
    ben = "MUA" if (d_gia > 0 and d_rsi > 0) else "BÁN" if (d_gia < 0 and d_rsi < 0) else None

    if nhay_cao and vol_thap:
        out["nhan"], out["y_nghia"] = "MỎNG", "sổ lệnh trống, giá nhảy — coi chừng bị quét"
    elif nhay_cao and vol_cao:
        if ben:
            out["nhan"] = f"LỰC {ben} ÁP ĐẢO"
            out["y_nghia"] = (f"tỉ số lực nghiêng hẳn về phe {ben.lower()} — "
                              f"giá chạy xa hơn nền {round(n_ti)}% với volume {round(kq_v[2])}%")
        else:
            # Giá và RSI LỆCH CHIỀU = PHÂN KỲ, không phải trạng thái trung tính.
            # b10 4252: "giá điều chỉnh xuống sâu thì RSI PHẢI cắm xuống" -> không
            # đồng nhịp là bất thường, và đây là tín hiệu mạnh nhất trong hệ.
            # 🔴 b3 1798 (thầy bắt GHI VÀO): "Sóng điều chỉnh trong một xu hướng tăng
            #    mạnh nó là sự TẠM NGHỈ CỦA LỰC MUA, chứ không phải sự gia tăng của lực bán."
            #    b3 4499: "Xu hướng giảm của RSI KHÔNG đồng nghĩa với xu hướng giảm của giá...
            #    đến khi nào CÓ SỰ GIA TĂNG CỦA LỰC BÁN thì lúc đấy mới tạo ra sóng giảm."
            #    b3 3263: "trong giai đoạn CÓ XU HƯỚNG thì tín hiệu PHÂN KỲ đơn giản nó chỉ
            #    là sự tạm nghỉ của lực mua, KHÔNG PHẢI sự tham gia của lực bán ĐỂ MÀ CHÚNG
            #    TA CÓ THỂ SHORT Ở ĐÓ."
            #    b3 4174 — cách phân biệt: "phân biệt được khi KẾT HỢP VỚI ĐƯỜNG GIÁ".
            #    -> RSI xuống mà GIÁ KHÔNG XUỐNG = lực mua NGHỈ, KHÔNG phải lực bán vào.
            if d_gia >= 0 > d_rsi:
                out["nhan"] = "LỰC MUA TẠM NGHỈ"
                out["y_nghia"] = (f"RSI {d_rsi:+.1f} điểm mà giá vẫn {d_gia:+.1f}% — "
                                  "lực mua nghỉ, KHÔNG có lực bán vào. ⛔ CẤM SHORT ở đây")
            elif d_gia <= 0 < d_rsi:
                out["nhan"] = "LỰC BÁN TẠM NGHỈ"
                out["y_nghia"] = (f"RSI {d_rsi:+.1f} điểm mà giá vẫn {d_gia:+.1f}% — "
                                  "lực bán nghỉ, chưa có lực mua vào. ⛔ CẤM LONG ở đây")
            else:
                out["nhan"], out["y_nghia"] = "GIẰNG CO", "giá hoặc RSI gần như đứng yên"
    elif nhay_thap and vol_thap:
        out["nhan"], out["y_nghia"] = "NGỦ", "không có V — đây là lúc đứng ngoài (K0)"
    elif nhay_thap and vol_cao:
        out["nhan"], out["y_nghia"] = "HẤP THỤ", "nhiều tiền mà giá không nhích — có người đỡ/chặn"
    else:
        out["nhan"], out["y_nghia"] = "THƯỜNG", "giá, lực và tiền đi cùng nhịp"
    return out


def dong_bay(tq):
    """Một dòng cho panel / alert."""
    if not tq:
        return "TƯƠNG QUAN  — chưa đủ nến"
    if tq["nhan"] in ("FAIL", "THIẾU VOL"):
        return f"TƯƠNG QUAN nhạy {tq['nhay_ti']}%  →  ⛔ {tq['nhan']} — {tq['y_nghia']}"
    return (f"TƯƠNG QUAN nhạy {tq['nhay_ti']}% · vol {tq['vol_ti']}%"
            f"  →  {tq['nhan']} — {tq['y_nghia']}")
