# -*- coding: utf-8 -*-
"""
K23 RULE v7 — module chấm kèo theo ĐÚNG rule vault note 63 v7.
Độc lập: import được mà KHÔNG đụng gì tới bot đang chạy.

Khối cài ở đây (theo sơ đồ khối K0-K10):
  K2   CÔNG TẮC      cụm 1D→1M đồng pha / ngược pha       b7 44:44
  K3   MÔ HÌNH ĐẸP   cung đóng · RSI cú A chạm 70/30      b15 · b7 31:41
  K4   BẬC 1/2/3     lực liên quan + điều chỉnh ≤50%      b8 17:23 · b38 43:54
  K3b  TƯƠNG QUAN    %giá/điểm RSI × volume (tuong_quan)  b3 206 · b10 4252

⭐ CÚ A = đoạn giữa HAI LẦN CẮT MA (b10 40:31). Fibo kéo trên chính đoạn đó,
   và chỉ đo khi đoạn ĐÃ XONG.
🔴 Hồi TỐI ĐA về 0.5 thì còn hiệu lực mạnh; sâu hơn 0.6-0.7 là "đã rất yếu" (b10 40:55).
"""
import k23_dakhung as K
import k23_engine as E
import tuong_quan as T

# ⚙️ 13/09 Kevin chốt: "thuần scalping với QML, chỉ quét từ khung D xuống".
# Cụm GỒNG của b5.1 (4x · 6x) — nằm TRONG dải vận hành nên xài được.
# (Cụm 1d/2d/3d/1w là công tắc của hệ SWING, cách mô hình H1 tới 24x-168x.)
CUM_CONG_TAC = ("1h", "4h", "1d")
KHUNG_MH     = ("1d", "12h", "8h", "6h", "4h", "3h", "2h", "1h", "30m", "15m", "5m")   # DẢI ĐI SĂN MÔ HÌNH — ĐẦY ĐỦ (Kevin chốt 18/09)

# ⭐ 26/09 — BA TẦNG KHUNG, mỗi tầng MỘT nhiệm vụ. Kevin chốt (ghi tay lên sơ đồ):
#   "trên h8 khung lớn xác định LỰC MUA, LỰC BÁN · từ h6 đến h1 là SOI MÔ HÌNH ·
#    m5, m15 ENTRY VÔ LỆNH"
# Thầy b38 00:29:14: "xu hướng là cái sự ĐỒNG THUẬN LỰC ở các khung thời gian khác
# nhau. Muốn hình thành một xu hướng tăng thì tất cả chúng nó phải đồng thuận tăng."
# ⚠️ KHÔNG thay KHUNG_MH: dải săn mô hình giữ đủ 11 khung vì Kevin còn cần mô hình ở
#    m15/m5 cho SCALPING. Ba hằng dưới là VAI TRÒ, không phải cổng chặn.
# ⭐ 27/09 — Kevin chốt THÊM KHUNG TUẦN. Lấy THẲNG từ sàn (MEXC_ITV["1w"]="Week1"),
#    KHÔNG gộp qua TF_GOP: gop_nen() neo theo EPOCH nên nến tuần gộp sẽ bắt đầu thứ
#    NĂM, lệch với TradingView (neo thứ HAI). Sàn trả sẵn nên mốc tuần chuẩn.
#    ⚠️ Việc này ĐẢO memory cũ "hệ ngắn hạn — bỏ Tuần" (M5 và Tuần tách biệt, b13/b10).
#    Kevin chốt lại 27/09: Tuần chỉ nằm ở TẦNG ĐỌC LỰC, KHÔNG lôi vào tầng entry.
KHUNG_LUC    = ("1w", "5d", "3d", "2d", "1d", "12h", "8h")   # ① trên h8 — đọc LỰC
KHUNG_MO_HINH= ("6h", "4h", "3h", "2h", "1h")             # ② h6→h1 — SOI MÔ HÌNH
KHUNG_ENTRY  = ("15m", "5m")                              # ③ ENTRY VÔ LỆNH
#   b25 0:53:41 thầy nói "nếu CHẲNG HẠN anh em phải đi làm 8 tiếng thì nhất quán ĐÂU ĐÓ
#   TỪ H1, H2, H3, H4" — đó là VÍ DỤ cho một hoàn cảnh, KHÔNG phải luật cứng. Dải đầy đủ
#   thầy dạy là D→M5; chọn CỤM nào để trung thành là việc của NGƯỜI, theo quỹ thời gian.
#   b25 0:55 — "khi mình đã xác định cho mình đúng những khung thời gian mà mình muốn vào
#   lệnh, các khung thời gian khác CÓ MÔ HÌNH KHÔNG CÓ MÔ HÌNH — BỎ QUA không cần [quan tâm]"
#   ⚠️ ĐỔI chốt #8 note 70 (trước: 1h·2h·3h·4h). Trần vẫn là 1D (chốt #1: bỏ 2D·3D·W·1M).
# ⭐ SỬA 15/09 — b25 ~00:53:41, thầy chốt thẳng:
#   "chúng ta phải NHẤT QUÁN cho mình trong những khung thời gian đâu đó từ H1, H2,
#    H3, H4… mục tiêu là hôm nay thằng H1 có mô hình hay không, H2 có mô hình hay
#    không, H3 có mô hình hay không, H4 có mô hình hay không?"
# Và thầy cảnh báo ĐÚNG cái bản cũ đang làm: "mở đồ thị ra với sự vô định… thấy
#   anh em bàn M15 mình cũng muốn ăn, bàn 30M cũng muốn ăn… tự nó gây ra áp lực và
#   khiến mình bị vô định, KHÔNG THỂ NÀO LÊN ĐƯỢC KỊCH BẢN."
# Bản cũ ("15m","30m","1h","2h","4h") là note 70 chốt #8 (Kevin 13/09) — ngược thầy.
# ⚠️ Đừng lẫn với CUM_CONG_TAC: H1·H2·H3·H4 là SÁT SƯỜN (1.5–2×, vùng tịnh tiến),
#   còn cụm CHI PHỐI phải cách 3–6× (note 34, b5.1) — đó là H1·H4·1D ở trên.
CHAM_T, CHAM_D = 70.0, 30.0                 # b7 31:41
# ⚠️ BỎ 09/09 — hai ngưỡng dốc≥2.0 / nở≥3.0 là MÌNH TỰ BỊA, không nguồn, mà giết
#    25.5% số giờ (đo 90 ngày BTC: 555/2179). Phễu ra 2 mô hình / 2179 giờ trong khi
#    thầy nói "1 tháng ba bốn lệnh" -> siết sai cỡ 10 lần. Đặt 0 = chỉ đòi MA chậm
#    có nhúc nhích, không đặt mức tuỳ tiện.
# ĐK3 (b15) — NGUỒN: luật của thầy. NGƯỠNG: ĐO ĐƯỢC, không phải của thầy.
#   Thầy chỉ nói "W45 đi ngang thì không phải mô hình", không cho con số.
#   Đo trên 50 lệnh BTC H1→M5 180 ngày (bt_h1_m5.py, 0 vi phạm nhìn trộm):
#     mở rộng < 2 điểm : 5 lệnh, WR 0.0%, -5.99R   <- dải "hai MA quấn", thua sạch
#     dốc    < 0.05    : 9 lệnh, WR 22.2%, -2.48R
#   Lấy đúng mép của dải thua sạch, KHÔNG kéo cao hơn: từ mở rộng>=5 trở lên
#   chiều đảo ngược (cắt mất lệnh thắng), tức là tối ưu quá đà.
#   ⚠️ Ngưỡng này KHÔNG làm hệ có lãi. Nó chỉ ngăn báo mô hình khi chưa có mô hình.
# ── CỔNG "MÔ HÌNH ĐẸP" — đo từ 8 ca Kevin chấm tay 11/09, KHÔNG phải số của thầy ──
# ⚠️ ĐỔI SANG TƯƠNG ĐỐI 12/09 — Kevin duyệt: "okie tương đối rồi mình cân chỉnh lại"
#
# Bản cũ dùng NĂM SỐ TUYỆT ĐỐI. Sai thiết kế: "mở rộng bao nhiêu ĐIỂM RSI" KHÔNG
# so được giữa các coin. Đo 900 nến H1, mở rộng đỉnh LỚN NHẤT từng coin:
#     ENA 17.7 · BTC 16.5 · SOL 15.1 · INJ 15.0 · LINK 14.5
# -> LINK và INJ KHÔNG BAO GIỜ đạt ngưỡng 15, cả nghìn nến cũng không. Coin biến
#    động thấp thành "vĩnh viễn không có mô hình" — vì thước sai đơn vị.
#
# Bằng chứng quyết định: cung ENA 21/08 18:00 -> 23/08 10:00 Kevin nhìn chart gọi
# là MÔ HÌNH. Mở rộng 11.32 -> ngưỡng tuyệt đối 15 GẠT. Nhưng nó nằm PHÂN VỊ 92%
# của chính ENA. 5 ca BTC Kevin duyệt nằm phân vị 97-100%.
#
# Nay: ba số đơn vị "điểm RSI" (mở rộng · hở TB · biên) -> PHÂN VỊ trong lịch sử
# vòng cung của CHÍNH coin+khung đó. Hai số còn lại giữ tuyệt đối vì vốn đã so
# được: độ dài tính bằng NẾN, %40-60 vốn đã là phần trăm.
#
# Nguyên tắc này KHÔNG phải mình nghĩ ra — k23_v3.pine đã ghi từ trước:
#   "Thầy KHÔNG cho ngưỡng 'mở rộng bao nhiêu là đủ' (b15). Thay bằng ĐỘ MẠNH
#    TƯƠNG ĐỐI: |EMA-WMA| hiện tại so với CHÍNH lịch sử khung đó."
# Mình đọc dòng đó rồi vẫn dựng cổng bằng số tuyệt đối. Nay sửa.
# ── CỔNG ĐẸP: chỉ còn ngưỡng TRÍCH ĐƯỢC ──
# XOÁ 12/09: DEP_PHAN_VI 85 · DEP_DAI 28 · DEP_TOI_THIEU_CUNG 15 — ba số tự đặt,
# đo KÍCH THƯỚC cung. Thầy b38: "dù có mở rộng bao nhiêu đi chăng nữa".
CHE_SONG_4060 = 60.0   # % thân cung nằm trong 40-60 -> bậc 3 (b38 43:54, phép che sóng trước)

# ĐK3 (b8 20:43) — "hai đường trung bình mà lại GẦN NHAU, ĐI NGANG -> rõ ràng không có
# xu hướng". Thầy KHÔNG cho số. Hai số dưới là SỐ TỰ ĐẶT, Kevin chỉnh bằng mắt.
# ⚠️ 12/09: ngưỡng cũ (0.05 / 2.0) đo trên LINK H2 loại ĐÚNG 0/27 cung — tức không hề
#    thực thi luật thầy, chỉ trang trí. Siết lên cho nó thật sự cắn.
# ⚠️ HAI SỐ NÀY PHẢI TRÙNG depDoc / depMoRong trong k23_v3.pine — t13 kiểm tự động.
DOC_TOI_THIEU     = 0.0     # GỠ 12/09 — vế 'MA đi ngang' nay nằm trong la_sideway (hở < 3)
MO_RONG_TOI_THIEU = 0.0     # GỠ 12/09 — thay bằng HO_SIDEWAY trong la_sideway
# ↑ CHỐT 12/09 bằng chính con số của THẦY, không phải mình đoán:
#   b8/b12 "bỏ qua 80% nhiễu, chỉ đánh 20% cơ hội rõ ràng" -> lấy 20% làm ĐÍCH.
#
#   ⚠️ 12/09 — nâng mở rộng lên 7.0 là SAI, đã trả lại 6.0. Hai ca tranh nhau:
#     LINK H2  07/09 16:00  hở 6.74 · 12% trong 40-60 · RSI cung 80.5  <- Kevin muốn CÓ MÀU
#     LINK M15 10/09 17:30  hở 6.52 · 52% trong 40-60 · RSI cung 29.0  <- Kevin nói SIDEWAY
#   Hở 6.74 vs 6.52 gần như nhau -> MỞ RỘNG KHÔNG tách được hai ca này.
#   Nhưng 12% vs 52% thời gian trong dải 40-60 thì tách rõ -> siết ở ĐÓ.
#   Đo 1324 vòng cung / 8 coin / H1·H2·H4:
#     hở 6.0 · 40-60 ≤65%  -> 21.1%  (lọt cả hai)
#     hở 7.0 · 40-60 ≤65%  -> 19.7%  (né cả hai — giết luôn ca H2 đúng)
#     hở 6.0 · 40-60 ≤50%  -> 16.8%  (CÓ MÀU ca H2 · né ca M15)   <- CHỌN

# ⚠️ VOLUME TRONG CUNG — luật DUY NHẤT rút từ dữ liệu thật (181 vòng cung BTC 150 ngày).
#    Vòng cung tích lũy là giai đoạn ÊM. Volume cao = có BÁN THẬT, không phải tích lũy.
#      <70%: thắng 64% · 70-100%: 62% · 100-140%: 57% · >140%: 45% (ngược > thuận)
#    Dốc đi một chiều qua 4 ô nên đáng tin hơn bất kỳ ô lẻ nào.
VOL_TRAN = 140.0
QT_T,   QT_D   = 80.0, 20.0                 # b4 GĐ2 -> bậc 1
HOI_TOI_DA     = 50.0   # % — b8 18:12 "không điều chỉnh quá 50% con sóng trước đó" (CHỈ cho TH1)


# ══════════════════ K1 · MÔ HÌNH — BẢN DỰNG LẠI 12/09 ══════════════════
# Kevin đọc lại đủ bốn điều, dựng đúng theo:
#   1. MIN NẾN — mô hình phải kéo dài TỐI THIỂU 4 NGÀY (đo theo khung: H4 = 24 nến)
#   2. ĐỘ BO   — mô hình phải có độ bo, "thể hiện trạng thái THAY ĐỔI TÂM LÝ giao dịch
#                của nhà đầu tư": lực đi một chiều, kiệt, rồi đảo sang chiều kia.
#                => vòng cung = HAI NHÁNH ngược chiều ghép lại, không phải một nhánh thẳng.
#   3. NHIỀU ĐIỂM CẮT ĐƯỢC, nhưng các điểm cắt phải THUẬN TREND (mức tiến đều một chiều
#      trong mỗi nhánh, không lượn tại chỗ).
#   4. SIDEWAY — giai đoạn CẢ BA ĐƯỜNG (RSI · EMA9 · WMA45) đi trong khu vực 40-60,
#      VÀ TRƯỚC ĐÓ CHƯA HÌNH THÀNH MÔ HÌNH. (Nếu đã có mô hình rồi thì việc ba đường
#      vào dải 40-60 KHÔNG biến nó thành sideway.)
# HAI ĐIỀU KIỆN — Kevin chốt 12/09: "đáp ứng đủ CẢ HAI thì mới hình thành mô hình"
#   TRỤC X = thời gian : tối thiểu 4 NGÀY (tự đổi ra nến theo khung)
#   TRỤC Y = biên RSI  : tối thiểu 40 ĐIỂM, đo trên CẢ VÒNG CUNG (ví dụ 30 -> 70)
# ⚠️ Đo trên CẢ CUNG, KHÔNG tách nhánh. Mình từng đo biên từng nhánh -> cung Kevin
#    duyệt (LINK H4 19/08, nhánh yếu 23 điểm) bị loại oan, trong khi cả cung của nó
#    là 52.8 điểm (đáy 35.3 -> đỉnh 88.1).
# ⚙️ HAI BIẾN KEVIN TỰ TINH CHỈNH — Kevin 12/09: "để đó thành biến số để mình tinh chỉnh"
NEN_TOI_THIEU = 28          # TRỤC X — Kevin chỉnh tay trên panel 13/09
BIEN_RSI_TOI_THIEU = 24.0   # TRỤC Y — biên RSI (điểm = %) — Kevin 13/09
NGAY_TOI_THIEU = 4.0        # chỉ để ghi chú, KHÔNG còn dùng để tính
# ĐỘ BO phải THẬT — Kevin 12/09: "3 cái dây dính chụm lại đi ngang bằng vầy cũng tính à".
# Mỗi NHÁNH phải dịch tối thiểu ngần này điểm. Nhánh dịch 0.2 điểm không phải một nhánh,
# đó là ba dây dính nhau ("quấn vào nhau như dây điện" — b3).
# Đo LINK H4: hai cung Kevin khoanh có nhánh nhỏ nhất 0.2 · cung Kevin duyệt 8.8.
# Khoảng trống giữa hai nhóm: 2.8 ↔ 7.8 -> đặt 5.0 vào giữa. SỐ NÀY CHỈNH ĐƯỢC.
BO_TOI_THIEU = 5.0
# MÔ HÌNH CHẾT khi ba đường MỞ RA PHÍA NGƯỢC — Kevin 12/09:
#   "3 đường đang mở ra, giá rơi tự do, đưa tay vô bắt dao rơi à"
# Vòng cung ∪ chuẩn bị TĂNG chỉ còn hiệu lực khi EMA9 CHƯA rơi xuống dưới WMA45.
# Rơi xuống rồi = lực mua bị phủ định = mô hình hết hiệu lực, KHÔNG được báo mua nữa.
# Ca bắt được: LINK H4 12/09 — cung ∪ TĂNG xong 08/09, nhưng EMA9 đang DƯỚI WMA45
# 8.2 điểm và RSI 40.4. Máy vẫn báo chuẩn bị TĂNG -> mời Kevin bắt dao rơi.
DAI_DUOI, DAI_TREN = 40.0, 60.0
# LỰC MUA TẠM NGHỈ (Kevin 12/09) — ba vế, số của Kevin:
TAM_DUOI, TAM_TREN, TAM_SAN = 30.0, 70.0, 40.0


def nen_toi_thieu(gio_moi_nen=None):
    """Số NẾN tối thiểu của một mô hình. Kevin chỉnh thẳng NEN_TOI_THIEU.
       (Trước đây suy từ 4 ngày rồi đổi theo khung — nay Kevin chỉnh số nến trực tiếp,
        cùng một con số áp cho mọi khung.)"""
    return NEN_TOI_THIEU


def cac_muc_cat(f, s_):
    """[(chỉ_số, mức)] của mọi điểm cắt EMA9/WMA45. Mức = giá trị hai đường tại đó."""
    return [(i, (f[i] + s_[i]) / 2.0) for i, _ in K._cac_diem_cat(f, s_)
            if f[i] is not None and s_[i] is not None]


def vong_cung(f, s_, gio_moi_nen=4.0, r=None, c=None):
    """VÒNG CUNG = ĐÚNG HAI LẦN CẮT — không có điểm cắt nào Ở GIỮA.

    Kevin 12/09: "hai điểm cắt thôi" · "cái hộp màu đỏ kìa 5 6 lần cắt chứ có phải
    hai lần cắt không". Hộp chứa nhiều hơn 2 lần cắt là SAI.

    TRỤC X = số nến giữa hai lần cắt        >= NEN_TOI_THIEU
    TRỤC Y = max(RSI) - min(RSI) trong đó   >= BIEN_RSI_TOI_THIEU
    Chiều  = EMA9 DƯỚI WMA45 trong cung -> ∪ TĂNG · TRÊN -> ∩ GIẢM (b15 1:37:30).
             ⚠️ KHÔNG đọc từ mức cắt — luật đó sai 502/502 cung (13/09).

    ⛔ CẤM gộp/làm mịn chuỗi điểm cắt. Khung không có thì TỊNH TIẾN LÊN KHUNG.
    """
    can = nen_toi_thieu(gio_moi_nen)
    mc = cac_muc_cat(f, s_)
    ra = []
    for k in range(len(mc) - 1):
        (i0, m0), (i1, m1) = mc[k], mc[k + 1]
        dai = i1 - i0
        if dai < can:                    # TRỤC X chưa đủ, kể cả sau dung sai
            continue
        # ⚠️ SỬA 13/09 — Kevin bắt trên LINK H1: cung "mức 38→46.8" bị gọi ∪ TĂNG
        # trong khi RSI đi 55.8 → đỉnh 69.9 → 41.9, tức hình ∩ rõ ràng.
        # MỨC CẮT chỉ nói cung này NẰM CAO hơn cung trước, KHÔNG nói cung HÌNH GÌ.
        # Hình do EMA9 nằm TRÊN hay DƯỚI WMA45 TRONG cung quyết định:
        #   EMA DƯỚI WMA suốt cung -> ∪  RSI trũng rồi ngoi lên  -> chuẩn bị TĂNG
        #   EMA TRÊN  WMA suốt cung -> ∩  RSI vồng lên rồi rơi   -> chuẩn bị GIẢM
        giua = (i0 + i1) // 2
        if f[giua] is None or s_[giua] is None:
            continue
        chieu = 1 if f[giua] < s_[giua] else -1
        bien_y, i_dinh = None, i0
        if r is not None:
            js = [j for j in range(i0, i1 + 1) if r[j] is not None]
            if not js:
                continue
            bien_y = round(max(r[j] for j in js) - min(r[j] for j in js), 1)
            if bien_y < BIEN_RSI_TOI_THIEU:   # TRỤC Y chưa đủ, kể cả sau dung sai
                continue
            i_dinh = min(js, key=lambda j: r[j] if chieu == 1 else -r[j])
        # ── PHÂN LOẠI CUNG (b15 1:23:25) — tích luỹ nằm trong giai đoạn ĐIỀU CHỈNH.
        # Cung mà GIÁ đã chạy mạnh cùng chiều TRONG hộp là cung SÓNG, không phải
        # cung tích luỹ. Vào ở cung sóng = đuổi (b9 22:22). ENA H4: +96% trong hộp.
        loai, d_gia = None, None
        if c is not None and c[i0]:
            d_gia = round((c[i1] - c[i0]) / c[i0] * 100.0, 1)
            chay = (chieu == 1 and d_gia > 25) or (chieu == -1 and d_gia < -25)
            loai = "song" if chay else "tich_luy"
        ra.append({"chuan_bi": chieu, "loai": loai, "d_gia": d_gia,
                   "i_dau": i0, "i_dinh": i_dinh, "i_cuoi": i1,
                   "muc_dau": round(m0, 1), "muc_dinh": round(m0, 1),
                   "muc_cuoi": round(m1, 1),
                   "mucs": [round(m0, 1), round(m1, 1)],
                   "dai": dai, "dai_nhanh1": i_dinh - i0, "dai_nhanh2": i1 - i_dinh,
                   "bien_y": bien_y, "so_cat": 2})
    return ra


def xung_luc(r, c, mh, f=None, s_=None):
    """XUNG LỰC = (%hồi RSI − %hồi giá) / 100, cắt trần ±1, làm tròn nấc 0.25.

    b3 mục 6: RSI giảm có HAI nguyên nhân khác hẳn — lực mua NGHỈ hay lực bán TĂNG.
    Nhìn RSI một mình KHÔNG phân biệt được, phải so với GIÁ trên CÙNG con sóng.
    Đoạn hồi: từ lúc cung đóng tới khi EMA9 cắt WMA45 (nguồn cũ ghi b15 22:25 — SAI giờ; xem b15 1:23:25).
    Mỗi bên lấy cực trị của CHÍNH NÓ (ENA: đỉnh RSI 21/08, đỉnh giá 23/08 — lệch 2 ngày).

    Trả (giá_trị, chế_độ). 5 chế độ Kevin chốt 13/09 — xem NHAN_XUNG_LUC.
    """
    i0, i1, ch = mh["i_dau"], mh["i_cuoi"], mh["chuan_bi"]
    js = [k for k in range(i0, i1 + 1) if r[k] is not None]
    if not js or i1 >= len(c) - 1:
        return None, None
    # ⭐ SỬA 16/09 — MẪU SỐ. Bản cũ lấy rA = r[i0] (ĐIỂM CẮT, một đầu mút) trong khi
    # vế GIÁ lấy pA = cực trị CẢ CUNG -> hai vế đo trên HAI CỬA SỔ khác nhau, trái b3 mục 6
    # ("so RSI với giá trên CÙNG con sóng"). Hệ quả đo được: mẫu số RSI trung vị chỉ 6.4 điểm,
    # 44% số cung dưới 5 điểm, p5 = 0.00 -> tỷ lệ nổ -> 82% số cung trả KỊCH TRẦN +1.00,
    # thang đo thành hằng số. Nay lấy cực trị trong cung cho CÙNG cửa sổ với giá:
    # mẫu số trung vị 31.4 điểm, không cung nào dưới 5.
    # ⚠️ Đã đo: sửa xong thang KHÔNG có sức dự báo (46-53% ở mọi dải, vào tại C).
    #    Sửa để panel NÓI THẬT, không phải để có edge. Xung lực vẫn là RÂU RIA, cấm làm cổng.
    rA = min(r[k] for k in js) if ch == 1 else max(r[k] for k in js)
    rB = max(r[k] for k in js) if ch == 1 else min(r[k] for k in js)
    pA = min(c[i0:i1 + 1]) if ch == 1 else max(c[i0:i1 + 1])
    pB = max(c[i0:i1 + 1]) if ch == 1 else min(c[i0:i1 + 1])
    if rB == rA or pB == pA:
        return None, None
    het = len(c) - 1
    if f is not None and s_ is not None:
        for j in range(i1 + 1, len(f)):
            if None in (f[j], s_[j], f[j - 1], s_[j - 1]):
                continue
            len_ = f[j - 1] <= s_[j - 1] and f[j] > s_[j]
            xuong = f[j - 1] >= s_[j - 1] and f[j] < s_[j]
            if (ch == 1 and len_) or (ch == -1 and xuong):
                het = j
                break
    seg = [r[k] for k in range(i1, het + 1) if r[k] is not None]
    if not seg:
        return None, None
    rC = min(seg) if ch == 1 else max(seg)
    pC = min(c[i1:het + 1]) if ch == 1 else max(c[i1:het + 1])
    hR = abs(rB - rC) / abs(rB - rA) * 100.0
    hP = abs(pB - pC) / abs(pB - pA) * 100.0
    v = max(-1.0, min(1.0, (hR - hP) / 100.0))
    v = round(v * 4) / 4
    if v >= 0.25:        # phe THUẬN cung áp đảo — phe ngược đốt lực mà không đẩy nổi giá
        che = "LUC_MUA_MANH" if ch == 1 else "LUC_BAN_MANH"
    elif v <= -0.25:     # giá lùi nhiều hơn RSI — phe thuận cung chỉ đang TẠM NGHỈ
        che = "MUA_TAM_NGHI" if ch == 1 else "BAN_TAM_NGHI"
    else:
        che = "CAN_BANG"
    return v, che


NHAN_XUNG_LUC = {
    "LUC_MUA_MANH": "🟢 LỰC MUA MẠNH",
    "LUC_BAN_MANH": "🔴 LỰC BÁN MẠNH",
    "MUA_TAM_NGHI": "🟢 LỰC MUA TẠM NGHỈ",
    "BAN_TAM_NGHI": "🔴 LỰC BÁN TẠM NGHỈ",
    "CAN_BANG":     "⚪ CÂN BẰNG",
}


def tam_nghi(f, s_, r, c, gio_moi_nen=4.0, i=None, bars=None):
    """LỰC MUA TẠM NGHỈ — Kevin chốt 12/09 (vẽ tay trên LINK H8):
       "RSI cắt xuống mà GIÁ KHÔNG GIẢM, SAU CÁI NÀY mới gọi là lực mua tạm nghỉ."
       "Cái này" = MỘT VÒNG CUNG ∪ ĐÃ HOÀN TẤT — con sóng mua đẩy RSI lên vùng cao.

    Ba vế:
      1. TRƯỚC ĐÓ có một VÒNG CUNG ∪ (chuẩn bị TĂNG) đã xong  — mô hình rõ ràng
      2. SAU nó, EMA9 CẮT XUỐNG dưới WMA45                     — "RSI cắt xuống"
      3. GIÁ KHÔNG GIẢM so với lúc cung đó đóng                — "giá không giảm"
    Đủ ba = lực mua đang NGHỈ, KHÔNG phải đảo chiều -> CẤM SHORT.

    ⚠️ Bản trước mình bắt "RSI phải đi từ <=30 lên >=70" — ca Kevin vẽ chỉ xuất phát
       từ ~42 nên trượt. Mô hình rõ ràng là VÒNG CUNG, không phải quãng RSI thô.
    """
    i = (len(f) - 1) if i is None else i
    ds = [m for m in vong_cung(f, s_, gio_moi_nen, r)
          if m["chuan_bi"] == 1 and m["i_cuoi"] <= i]
    if not ds:
        return False, "chưa có vòng cung ∪ nào hoàn tất trước đó"
    mh = ds[-1]
    z = mh["i_cuoi"]
    cat_xuong = [k for k, _ in K._cac_diem_cat(f, s_)
                 if k > z and k <= i and f[k] is not None and s_[k] is not None
                 and f[k] < s_[k]]
    if not cat_xuong:
        if f[i] is not None and s_[i] is not None and f[i] < s_[i]:
            cat_xuong = [i]
        else:
            return False, (f"vòng cung ∪ xong {i - z} nến trước, nhưng RSI CHƯA cắt xuống "
                           f"(EMA9 {f[i]:.1f} vẫn trên WMA45 {s_[i]:.1f})")
    k0 = cat_xuong[0]
    # ⭐ VẾ 3 — SỬA 26/09. Kevin: "tính theo VÙNG đi chứ đừng tính ĐIỂM".
    #   Bản cũ so HAI MÚT: `c[i] < c[z]` — giá lúc này với giá lúc cung đóng.
    #   Một cây râu ở đầu hoặc cuối là lệch, và giá ngoi lên tụt xuống trong đoạn
    #   thì không thấy. Nay đọc VÙNG: cấu trúc giá còn GIỮ hay đã PHÁ (b8 1:24:23,
    #   b26 0:05:36 "đáy sau cao hơn đáy trước").
    #   THỨ TỰ: cau_truc_gia() là THƯỚC CHÍNH. Nó trả True (còn giữ) / False (đã phá)
    #   / None (chưa đủ sóng để đọc). CHỈ khi None mới rơi xuống thước dự phòng —
    #   trả True mà vẫn chạy dự phòng thì dự phòng chặn hết (lỗi 26/09, 7/8 ca).
    _vung_ly_do = None
    _giu = None
    if bars is not None and len(bars) > z + 2:
        try:
            _giu, _moc = cau_truc_gia(bars[:i + 1], 1)
        except Exception:
            _giu = None
    if _giu is False:
        _vung_ly_do = (f"cấu trúc giá ĐÃ PHÁ — đáy sóng gần nhất thấp hơn "
                       f"đáy trước (b8 1:24:23 · b26 0:05:36)")
    elif _giu is None:
        # chưa đọc được cấu trúc -> thước dự phòng, vẫn đọc VÙNG chứ không đọc
        # điểm: lấy đáy THẤP NHẤT của cả đoạn, không phải riêng nến cuối.
        _day_vung = min(x for x in c[z:i + 1] if x is not None)
        if _day_vung < c[z]:
            _vung_ly_do = (f"chưa đọc được cấu trúc, và đáy vùng "
                           f"{100*(_day_vung-c[z])/c[z]:+.2f}% dưới mốc cung ∪ đóng")
    if _vung_ly_do:
        return False, (f"RSI đã cắt xuống, nhưng {_vung_ly_do} — "
                       f"đây là ĐIỀU CHỈNH THẬT, không phải tạm nghỉ")
    return True, (f"LỰC MUA TẠM NGHỈ — vòng cung ∪ {mh['dai']} nến đóng trước đó "
                  f"(mức {mh['muc_dau']}→{mh['muc_cuoi']}), "
                  f"RSI đã cắt xuống, nhưng giá GIỮ ĐƯỢC VÙNG (đáy vùng "
                  f"{100*(min(x for x in c[z:i+1] if x is not None)-c[z])/c[z]:+.2f}%) "
                  f"→ CẤM SHORT")


def ba_duong_trong_dai(r, f, s_, i):
    """Điều 4 — CẢ BA ĐƯỜNG (RSI · EMA9 · WMA45) cùng nằm trong dải 40-60."""
    for v in (r[i], f[i], s_[i]):
        if v is None or not (DAI_DUOI <= v <= DAI_TREN):
            return False
    return True


def trang_thai(f, s_, r, gio_moi_nen=4.0):
    """Trạng thái tại nến CUỐI.
       Trả dict: {mo_hinh, sideway, vi_sao}
       · mo_hinh  = vòng cung gần nhất đã hình thành (None nếu chưa có)
       · sideway  = True khi ba đường trong 40-60 VÀ TRƯỚC ĐÓ CHƯA CÓ MÔ HÌNH (điều 4)
    """
    i = len(f) - 1
    ds = vong_cung(f, s_, gio_moi_nen, r)
    truoc = [m for m in ds if m["i_cuoi"] <= i]
    mh = truoc[-1] if truoc else None
    trong_dai = ba_duong_trong_dai(r, f, s_, i)
    # ⚠️ VÁ 12/09 — Kevin: "RSI đi ngang 40 đến 60% mà có [mô hình]... mình nói KHÔNG".
    # Bản trước mình gắn thêm "nếu TRƯỚC ĐÓ đã có mô hình thì vẫn tính" -> ETH H4 ra
    # CÓ mô hình trong khi ba đường đang lình xình giữa dải. Kevin bác.
    # NAY: ba đường đang trong 40-60 = SIDEWAY, HẾT. Mô hình cũ có hay không không cứu được.
    if trong_dai:
        return {"mo_hinh": None, "sideway": True,
                "vi_sao": f"SIDEWAY — ba đường đang đi ngang trong dải "
                          f"{DAI_DUOI:.0f}-{DAI_TREN:.0f} (RSI {r[i]:.1f} · EMA9 {f[i]:.1f} · "
                          f"WMA45 {s_[i]:.1f})"
                          + (f" · cung gần nhất {'∪' if mh['chuan_bi']==1 else '∩'} đã xong "
                             f"{i - mh['i_cuoi']} nến trước, KHÔNG còn hiệu lực" if mh else "")}
    if mh is None and trong_dai:
        return {"mo_hinh": None, "sideway": True,
                "vi_sao": f"SIDEWAY — cả ba đường trong dải {DAI_DUOI:.0f}-{DAI_TREN:.0f} "
                          f"(RSI {r[i]:.1f} · EMA9 {f[i]:.1f} · WMA45 {s_[i]:.1f}) "
                          f"và TRƯỚC ĐÓ CHƯA hình thành mô hình"}
    if mh is None:
        return {"mo_hinh": None, "sideway": False,
                "vi_sao": f"chưa có vòng cung nào đủ {nen_toi_thieu(gio_moi_nen)} nến "
                          f"({NGAY_TOI_THIEU:.0f} ngày)"}
    # ── mô hình còn hiệu lực không: ba đường có mở ra phía NGƯỢC không ──
    tren = f[i] is not None and s_[i] is not None and f[i] > s_[i]
    hop = (tren and mh["chuan_bi"] == 1) or ((not tren) and mh["chuan_bi"] == -1)
    ho = abs(f[i] - s_[i]) if (f[i] is not None and s_[i] is not None) else 0.0
    if not hop and ho >= BO_TOI_THIEU:
        return {"mo_hinh": None, "sideway": False, "chet": True,
                "vi_sao": (f"MÔ HÌNH HẾT HIỆU LỰC — cung {'∪ chuẩn bị TĂNG' if mh['chuan_bi'] == 1 else '∩ chuẩn bị GIẢM'}"
                           f" xong {i - mh['i_cuoi']} nến trước, nhưng EMA9 {f[i]:.1f} đang "
                           f"{'DƯỚI' if not tren else 'TRÊN'} WMA45 {s_[i]:.1f} (hở {ho:.1f}) "
                           f"— ba đường mở ra phía NGƯỢC, đừng bắt dao rơi")}
    mh = dict(mh)
    mh["tuoi"] = i - mh["i_cuoi"]
    mh["con_hieu_luc"] = hop
    return {"mo_hinh": mh, "sideway": False,
            "vi_sao": (f"CÓ MÔ HÌNH · {'∪ chuẩn bị TĂNG' if mh['chuan_bi'] == 1 else '∩ chuẩn bị GIẢM'}"
                       f" · {mh['dai']} nến · {mh['so_cat']} điểm cắt"
                       + (f" · ba đường đang trong 40-60 nhưng ĐÃ có mô hình trước đó"
                          if trong_dai else ""))}


# ══════════════════ K2 · CÔNG TẮC ══════════════════
def neo_cu_a(f, s_, highs, lows, mh):
    """NEO FIBO — đáy/đỉnh giá của CÚ A (con sóng chính), KHÔNG phải của vòng cung.

    ⭐ SỬA 14/09 — LỖI GỐC FIBO. Trước đây cong_vao() neo fibo trên hộp giá của
    CHÍNH VÒNG CUNG, kèm chú thích dẫn b10 2:40 — dẫn đúng nguồn nhưng đọc ngược ý.

    b10 ~2:40:42, thầy cầm tay học viên kéo fibo:
        "RSI bắt đầu xu hướng tăng là TỪ KHU VỰC NÀY NÓ MỞ RA ĐẾN KHU VỰC NÀY NÓ
         KẾT THÚC. Quá trình tăng mở ra thì là CÁI TỪ CÁI ĐÁY NÀY, quá trình kết
         thúc là TỪ CÁI ĐỈNH NÀY, thì em KÉO CHO ANH CÁI FIBO ở đây. Thì đây là
         CON SÓNG CHÍNH của nó. Tối đa con sóng này để nó còn hiệu lực mạnh thì
         tối đa là nó điều chỉnh về cái vùng này. Nếu mà sâu hơn nữa về vùng
         0.6 0.7 thì con sóng này nó ĐÃ RẤT LÀ YẾU RỒI."
    Học viên: "không biết đo điểm nào, nhiều điểm thì nó ra lung tung"
    Thầy:     "thì dựa vào cái việc XÁC ĐỊNH SÓNG Ở TRÊN RSI."

    CON SÓNG CHÍNH = cú A = từ lần cắt TRƯỚC cung → điểm MỞ cung.
    VÒNG CUNG chính là NHỊP ĐIỀU CHỈNH CỦA cú A (b8 17:23) — lấy fibo trên vòng
    cung là đo cái điều chỉnh bằng chính nó.

    Chiều đọc theo THỜI GIAN: cực trị nào tới TRƯỚC là điểm đầu (VÁ 11/09, ca UNI;
    phép kiểm t3_cua_theo_thoi_gian khoá luật này — đừng đổi sang "theo cấu trúc MA").

    Trả (dau_A, dinh_A, chieu_A, i_mo_A) hoặc None nếu không có cú A.
    """
    i_mo_cung = mh["i_dau"]
    truoc = [i for i, _ in cac_muc_cat(f, s_) if i < i_mo_cung]
    if not truoc:
        return None
    i_mo_A = truoc[-1]
    if i_mo_A >= i_mo_cung:
        return None
    i_hi = max(range(i_mo_A, i_mo_cung + 1), key=lambda k: highs[k])
    i_lo = min(range(i_mo_A, i_mo_cung + 1), key=lambda k: lows[k])
    if i_lo < i_hi:
        return lows[i_lo], highs[i_hi], 1, i_mo_A
    return highs[i_hi], lows[i_lo], -1, i_mo_A


# ⭐⭐ ĐIỂM VÀO LÀ MỘT **VÙNG** — Kevin chốt 22/09: "từ 0.5 đến 0.618", SL 0.7.
# Thầy b48 0:46:01: "anh LUÔN LUÔN vào theo MỘT VÙNG chứ KHÔNG BAO GIỜ vào theo
# MỘT ĐIỂM" · b48 1:00:47: "vào khoảng HAI BA LỆNH" trong vùng đó.
VAO_TU  = 0.5      # mép TRÊN vùng vào — bắt đầu được vào
VAO_DEN = 0.618    # mép DƯỚI vùng vào — vào nốt ("0.62" Kevin nói = 0.618 fibo chuẩn)
HONG    = 0.7      # thủng là kèo HỎNG (b2 1:42:39 · b10 2:41) — SL nằm ở đây

def fibo_cu_a(dau_A, dinh_A):
    """Trả BA mốc (f05, f618, f07) — vùng vào là KHOẢNG [f05, f618]."""
    _r = dau_A - dinh_A
    return (dinh_A + _r * VAO_TU,
            dinh_A + _r * VAO_DEN,
            dinh_A + _r * HONG)


NHAN_BAN_CHAT = {
    "MOI":     "🔵 SÓNG MỚI",
    "TIEP":    "🟢 TIẾP DIỄN",
    "SIDEWAY": "⚪ SIDEWAY",
}


def ban_chat_a(a, chieu_cung):
    """A là sóng MỚI hay sóng TIẾP DIỄN — hỏi “RSI ĐANG NẰM Ở ĐÂU”.

    ⭐ 14/09 — TẦNG MÁY CHƯA BAO GIỜ ĐỌC. Kevin: *“mấu chốt là RSI đang nằm ở đâu,
    nó là điểm bắt đầu cho con sóng tăng mới hay là sóng tăng tiếp diễn”*.

    b23 ~00:06:19 — bộ ba nhận SIDEWAY, nguyên văn:
        “đỉnh gần nhất trước đó KHÔNG vượt quá vùng 70 — con sóng trước đó không
         có lực mua tham gia vào mạnh. Và đáy trước đó KHÔNG dưới vùng 30 — cũng
         không có lực bán tham gia vào mạnh… lúc đấy mới xác định là nó đi vào
         khu vực sideway.”
    b4 ~00:21:03 — hình của TIẾP DIỄN: đỉnh 80 → EMA9 cắt xuống → mô hình tích luỹ
         lực mua → cuộn lên → sinh ra con sóng C.
    b12 ~1:27:57 — “đoạn này chưa hề có con sóng gì cả, KHÔNG gọi là ABC nhá.”

    KHÔNG đặt ngưỡng mới: dùng CHAM_T=70 / CHAM_D=30 đã khai sẵn (b7 31:41).

    Trả (ma, mo_ta) — ma ∈ {"MOI","TIEP","SIDEWAY"} hoặc None nếu thiếu dữ liệu.
    """
    if not a:
        return None, "chưa dựng được cú A"
    rc = a.get("rsi_cuc")        # RSI cực của CÚ A
    cc = a.get("cuc_cung")       # RSI cực trong SÓNG B
    if rc is None or cc is None:
        return None, "chưa đo đủ RSI cực của A và B"

    # ── TRỤC 1 · CÓ BÊN NÀO ÁP ĐẢO KHÔNG? — bộ ba b23, phải ĐỦ CẢ HAI VẾ ──
    # "đỉnh gần nhất trước đó KHÔNG vượt quá 70" VÀ "đáy trước đó KHÔNG dưới 30"
    # → cả hai đều không thì mới là sideway. Chỉ một vế thì CHƯA đủ để gọi sideway.
    # Hai cực trị gần nhất chính là cực của A và cực của B.
    dinh_gan, day_gan = max(rc, cc), min(rc, cc)
    if dinh_gan <= CHAM_T and day_gan >= CHAM_D:
        return "SIDEWAY", (f"đỉnh gần nhất {dinh_gan} ≤ {CHAM_T:.0f} và đáy {day_gan} ≥ {CHAM_D:.0f} "
                           f"— không bên nào áp đảo, ĐỨNG NGOÀI (b23 0:06:19)")

    # ── TRỤC 2 · CÓ ÁP ĐẢO RỒI — MỚI hay TIẾP DIỄN? ──
    # A cùng chiều B → B là nhịp điều chỉnh của A → C đi TIẾP xu hướng cũ (b4 0:21:03)
    # A ngược chiều B → B bẻ lại A → lực cũ đã kiệt → C là sóng MỚI
    if a.get("chieu_cu_a") == chieu_cung:
        return "TIEP", (f"A đẩy RSI tới {rc}, B hồi về {cc} — lực đã vào mạnh, "
                        f"C tiếp diễn xu hướng")
    return "MOI", (f"A tới RSI {rc}, B đẩy tới {cc} rồi bo cong — lực cũ đã kiệt, "
                   f"C là sóng MỚI")


def cu_tru(r, i_tu, i_den, ch, moc=None):
    """CƯ TRÚ — % số nến mà RSI GIỮ ĐƯỢC ở bên kia mốc, trong khoảng [i_tu, i_den].

    ⭐ 16/09 — tầng máy CHƯA BAO GIỜ có. Thầy đọc lực bằng CƯ TRÚ, không bằng cú CẮT:
      b26 0:02:52  "lực bán chiếm chủ đạo thì RSI nó CÓ CẮT LÊN CẮT XUỐNG GÌ CHĂNG NỮA
                    thì nó vẫn ở khu vực phía DƯỚI của đồ thị"
      b30 0:51:02  "đừng nhìn MỘT cái đỉnh, HAI cái đỉnh — phải nhìn CẢ MỘT VÙNG…
                    nó CHỌC lên thì KHÔNG gọi là có lực mua. Thế đỉnh nó chết ấy."
      b31 1:29:11  "KHÔNG BAO GIỜ vào khi MỘT cây nến đóng trên vùng 60 —
                    phải DUY TRÌ MỘT CỤM CÂY NẾN ở trên vùng 60"   <- đơn vị đo: CỤM NẾN
      b43 0:10:33  chẩn "sai vị thế": "nó chỉ kéo xuống vùng 40 nó lại GIẬT LÊN… chứ nó
                    có DUY TRÌ được mô hình của 5M ở dưới vùng 40 đâu"
      b11 0:36:55  "RSI vẫn NẰM Ở trong vùng 40-60 -> CHƯA CÓ lực mua… đó là cái BỘ LỌC"
      b43 0:58:50  "đồ thị NẰM HOÀN TOÀN trong khu vực từ vùng 50 trở lên -> có lực mua"

    moc mặc định = TAM_SAN (40) / 100−TAM_SAN (60) — bậc "KHUNG NÀY CÓ LỰC CHƯA".
    Khác bậc 70/30 (mô hình có ý nghĩa, b13 2:28) và 80/20 (áp đảo, b20 1:06:45).
    """
    if moc is None:
        moc = (100.0 - TAM_SAN) if ch == 1 else TAM_SAN
    seg = [x for x in r[i_tu:i_den + 1] if x is not None]
    if not seg:
        return None
    n = sum(1 for x in seg if (x > moc if ch == 1 else x < moc))
    return round(n / len(seg) * 100.0, 1)


def quan_tinh_a(rsi_cuc, chieu_a, muot=None):
    """QUÁN TÍNH của cú A — b20 01:06:45, học viên đọc, thầy xác nhận:
       "quán tính tăng là khi lực mua ÁP ĐẢO lực bán — RSI sẽ có NẾN ĐÓNG ở TRÊN VÙNG 80,
        một nến hoặc nhiều nến. Quán tính giảm thì RSI đóng nến ở DƯỚI 20."

    ⭐ 16/09 — QT_T/QT_D = 80/20 khai từ lâu mà KHÔNG HÀM NÀO GỌI, trong khi "quán tính"
    là khái niệm tần suất hạng 3 cả khoá (1026 + 399 lần).
    """
    if rsi_cuc is None or chieu_a is None:
        return None
    cham = (rsi_cuc >= QT_T) if chieu_a == 1 else (rsi_cuc <= QT_D)
    if not cham:
        return False
    # ⭐ 17/09 — b13 1:22:25, thầy bác một đỉnh giá cao hơn KHÔNG phải là quán tính:
    #   "cái QUÁN TÍNH TĂNG nó phải CÓ ĐỘ MỞ RỘNG và nó THU HẸP DẦN. Còn cái đoạn này nó
    #    là đoạn RẤT NGẮN của RSI, nó KHÔNG ĐỦ cái sự TÍCH LUỸ cho lực tăng lực giảm."
    # Chạm 80/20 là ĐIỀU KIỆN CẦN (b4 0:36:43), chưa đủ. Có đo được độ mượt thì xét thêm.
    if muot is None:
        return True                      # chưa đo được -> giữ nguyên kết luận chạm ngưỡng
    return muot > 0.0                    # cung có ĐOẠN ĐÓNG thật, không cắm ngược một phát


def do_muot(f, s_, i_dau, i_cuoi):
    """ĐỘ MƯỢT của một vòng cung — b5 0:26:57, thầy bắt ghi nguyên văn:
       "SỰ DI CHUYỂN CỦA ĐỒ THỊ PHẢI TẠO RA ĐƯỢC ĐỘ MƯỢT CHO ĐƯỜNG TRUNG BÌNH"

    b5.1 0:03:38  cơ chế: "RSI phải ĐI DẦN VÀO để nó KÉO DẦN KHOẢNG CÁCH CỦA HAI ĐƯỜNG
                  TRUNG BÌNH VÀO. Khi nào nó kéo được đường trung bình NHANH cắt LÊN TRÊN
                  đường trung bình CHẬM thì khi đấy nó THÀNH CÔNG."
    b5.1 0:02:42  ngược lại: "RSI tăng lên đây MỘT PHÁT thì nó KHÔNG tạo ra được độ mượt...
                  KHÔNG CÓ một hình thái nào mà đường trung bình nhanh CẮM NGƯỢC LÊN mà nó
                  đi tăng lên được — KHÔNG BAO GIỜ CÓ CHUYỆN ĐÓ."
    b5.1 0:12:51  vì sao quan trọng: "cái ĐỘ MƯỢT đấy nó mới CHÍNH LÀ TÍCH LUỸ của TÂM LÝ
                  thị trường... của LỰC MUA và LỰC BÁN cho một xu hướng thực sự BỀN VỮNG."
    b5.1 0:13:44  "nếu nó KHÔNG CÓ ĐỘ MƯỢT thì nó KHÔNG CÓ BỀN."
    b5.1 0:23:53  "GIẢM GIA TỐC cũng là một yếu tố để tạo ra độ mượt... phải giảm gia tốc
                  để DỪNG cái ĐOÀN TÀU này lại đã."

    Cung nằm giữa HAI lần cắt nên khoảng hở ~0 ở cả hai đầu, phình ở giữa. Phần đáng đo là
    ĐOẠN ĐÓNG — từ chỗ hở RỘNG NHẤT tới lần cắt kết thúc. Kéo dần vào (mượt) thì đoạn này
    DÀI; cắm ngược một phát thì nó NGẮN.

    ⛔ KHÔNG ĐẶT NGƯỠNG. b5.1 0:15:02 — học viên hỏi thẳng "tích luỹ BAO NHIÊU CÂY NẾN thì
       tạo ra độ mượt?", thầy: "CÁI NÀY LÀ TÙY GIAI ĐOẠN nhá". Nên đây là trường BÀY.

    Trả (ti_le_doan_dong, ho_rong_nhat) — None nếu không đo được.
    """
    js = [j for j in range(i_dau, i_cuoi + 1)
          if f[j] is not None and s_[j] is not None]
    if len(js) < 4:
        return None, None
    ho = {j: abs(f[j] - s_[j]) for j in js}
    j_max = max(js, key=lambda j: ho[j])
    dai = js[-1] - js[0]
    if dai <= 0:
        return None, None
    return round((js[-1] - j_max) / dai, 3), round(ho[j_max], 2)


def day_dinh_song(bars, chieu, rsi_len=14):
    """ĐỈNH / ĐÁY **ỨNG VỚI MỘT CON SÓNG** của chính khung này.

    b26 0:10:52 — thầy trả lời học viên hỏi về dịch SL theo đỉnh đáy:
      "Đỉnh đáy LUÔN LUÔN nó tương ứng với MỘT CON SÓNG. Nếu nó KHÔNG tương ứng với con
       sóng thì NÓ KHÔNG PHẢI LÀ ĐỈNH ĐÁY của cái khung thời gian đó — có thể nó là đỉnh
       đáy của KHUNG NHỎ HƠN. Có những đoạn cái RÂU nó tụt xuống phát rồi nó lên — thì
       mình KHÔNG THỂ gọi nó là ĐÁY của khung thời gian này được."
    b13 0:31:46 — "cái đáy này chỉ là một cái việc nó CẮT XUỐNG xong tiếp tục cái đoạn
       NHIỄU lên thôi. Đây có phải đáy của khung 12 giờ không? KHÔNG. Đây là đáy của khung
       H4... cái đáy này nó TƯƠNG ỨNG VỚI QUÁ TRÌNH NÀY. CẢ CÁI CỤM này là hỗ trợ khung H4."

    Con sóng = khoảng giữa HAI LẦN CẮT LIÊN TIẾP của EMA9/WMA45 — b11 1:11:37:
      "từ đây lên đến đây là MỘT con sóng, bởi vì RSI vẫn nằm trong quá trình tăng VÀ
       đường trung bình nhanh vẫn nằm TRÊN đường trung bình chậm."

    ⛔ KHÔNG đặt thêm ngưỡng độ dài — b5.1 0:15:02, học viên hỏi "tích luỹ bao nhiêu cây
       nến?", thầy trả lời "CÁI NÀY LÀ TÙY GIAI ĐOẠN nhá".

    Trả list [(i_dau, i_cuoi, gia)] theo thời gian; phần tử CUỐI là con sóng ĐANG CHẠY.
    """
    if not bars or len(bars) < rsi_len * 3:
        return []
    cl = [x[4] for x in bars]
    r = K.rsi(cl, rsi_len)
    f = K._ema(r, 9)
    s_ = K._wma(r, 45)
    mc = [i for i, _ in cac_muc_cat(f, s_)]
    if not mc:
        return []
    bien = mc + [len(bars) - 1]          # gồm cả con sóng CHƯA đóng

    # ── GỘP NHIỄU: cắt rồi cắt lại trong 1-2 nến KHÔNG phải một con sóng.
    # b11 1:11:43 — "cái SÓNG HỒI của anh nó là MỘT CON SÓNG chứ KHÔNG PHẢI LÀ
    #                MỘT HAI CÂY NẾN về nó gọi là hồi"
    # b4  0:42:21 — "cái đoạn này nó cắt xuống NÓ KHÔNG THỂ HIỆN ĐIỀU GÌ đâu, đôi khi
    #                nó chỉ là ĐOẠN NHIỄU thôi"
    # Ngưỡng "một hai cây nến" là CHỮ CỦA THẦY, không phải số mình đặt.
    sach = [bien[0]]
    for x in bien[1:]:
        if x - sach[-1] <= 2 and x != bien[-1]:
            continue                      # nuốt cú cắt nhiễu, kéo dài sóng trước
        sach.append(x)
    bien = sach

    ra = []
    for k in range(len(bien) - 1):
        i0, i1 = bien[k], bien[k + 1]
        if i1 <= i0:
            continue
        if chieu == 1:
            gia = min(bars[j][3] for j in range(i0, i1 + 1))
        else:
            gia = max(bars[j][2] for j in range(i0, i1 + 1))
        ra.append((i0, i1, gia))
    return ra


def cau_truc_gia(bars, chieu, rsi_len=14):
    """CẤU TRÚC GIÁ — đỉnh sau cao hơn đỉnh trước, đáy sau cao hơn đáy trước.

    b26 0:05:36  "phải thấy những CẤU TRÚC TĂNG rõ ràng: các ĐỈNH SAU CAO HƠN ĐỈNH TRƯỚC,
                  ĐÁY SAU CAO HƠN ĐÁY TRƯỚC"
    b11 0:28:04  "khung nhỏ có DẤU HIỆU DỪNG giảm và nó có ĐỈNH ĐÁY CAO DẦN"
    b17 2:07:20  ngược lại: "KHÁNG CỰ vẫn THẤP DẦN thì LỰC MUA CHƯA CÓ"

    ⚠️ SỬA 17/09 — bản cũ đọc bằng **pivot 3 nến** (`xs[i] == min(w)`), tức bắt cả RÂU
    NHỌN làm đỉnh đáy. b26 0:10:52 nói thẳng **râu KHÔNG phải đáy**. Nay đọc trên
    `day_dinh_song()` — đỉnh đáy **ứng một con sóng** của chính khung đó.

    ⚠️ Đọc trên ĐỒ THỊ GIÁ, không đọc trên RSI (b12 1:43:00: "anh có NỐI ĐỈNH ĐÁY CỦA RSI
       bao giờ đâu?").
    ⚠️ KHÁC bộ lọc xu hướng HH/HL đã bị BÁC (note 49): ở đây cấu trúc dùng để ĐẶT SL ·
       KÍCH HOẠT THOÁT · CHO PHÉP DỊCH SL, không dùng để phán "đang trend".

    Trả (giu, moc) — giu=True nếu đáy/đỉnh SÓNG gần nhất còn cao/thấp dần.
    """
    ds = day_dinh_song(bars, chieu, rsi_len)
    if len(ds) < 2:
        return None, (ds[-1][2] if ds else None)
    truoc, nay = ds[-2][2], ds[-1][2]
    giu = (nay > truoc) if chieu == 1 else (nay < truoc)
    return giu, nay

def fail_quan_tinh(r, i_cuoi, chieu_a, co_quan_tinh, rsi_dinh_cu=None):
    """FAIL QUÁN TÍNH — **HAI CHẾ ĐỘ**, đều của thầy, không cái nào là "MA cắt ngược".

    ⛔ 17/09 — BẢN CŨ SAI TỪ ĐỊNH NGHĨA. Nó nổ khi EMA9 cắt ngược WMA45 sau i_cuoi.
       b4 0:42:21 thầy cấm thẳng cách đó:
         "anh em ĐỪNG CÓ CĂN cái việc nó CẮT LÊN CẮT XUỐNG nhá. Cái đoạn này nó cắt xuống
          NÓ KHÔNG THỂ HIỆN ĐIỀU GÌ ĐÂU. Đôi khi nó chỉ là ĐOẠN NHIỄU thôi. Chúng ta đây
          nó là một QUÁ TRÌNH VÒNG CUNG, bởi vì NÓ KHÔNG PHẢI LÀ 1 + 1 = 2."
       Và cú cắt đó chính là **GIAI ĐOẠN 3 — ĐIỀU CHỈNH**, một bước BÌNH THƯỜNG của vòng
       lặp bốn giai đoạn (b4 0:39:58), không phải dấu hiệu hết lực.
       b9 4:23:18 — thầy sửa học viên mua theo cú cắt: "đấy là SAI RỒI".

    ── CHẾ ĐỘ ①: ĐỈNH MỚI KHÔNG TẠO NỔI QUÁN TÍNH ──────────────────────────────
    b4 0:44:30  "Nếu tiếp tục ĐỈNH MỚI lại tạo ra quán tính tăng, có nghĩa là RSI ở giai
                 đoạn này nó LẠI LÊN 80 TIẾP."
    b4 0:45:05  "...lặp lại quy trình bốn bước CHO ĐẾN KHI NÀO ĐỈNH MỚI NỮA KHÔNG TẠO RA
                 QUÁN TÍNH TĂNG."
    b4 0:46:04  "cái ĐỈNH SAU... nó KHÔNG TẠO RA quán tính tăng nữa. RSI nó CHỚM VÙNG 70
                 THÔI. Đoạn này HẾT LỰC của khung tuần."
    b27 0:41:19 cùng hiện tượng, tên khác — "mô hình SUY YẾU": "trước đó là những ĐỈNH CAO
                 DẦN, sau đó nó tạo ĐỈNH THẤP DẦN... nó KHÔNG VƯỢT ĐƯỢC, nó còn THẤP HƠN."

    ── CHẾ ĐỘ ②: ĐIỀU CHỈNH XUỐNG SÂU ─────────────────────────────────────────
    b20 1:09:03 học viên trả bài, thầy xác nhận: "đặc điểm của FAIL: RSI từ vùng 80, khi
                 vào giai đoạn điều chỉnh thì nó ĐI XUỐNG SÂU — có thể XUỐNG DƯỚI 40 HOẶC 30."
    b42 0:06:36  "vùng để còn giữ được HIỆU LỰC cho quán tính tăng phải là VÙNG 40 TRỞ LÊN.
                 Khi RSI TỤT XUỐNG DƯỚI VÙNG 40 = CÓ LỰC BÁN THAM GIA rồi -> quán tính tăng
                 rõ ràng là BỊ TRIỆT TIÊU."

    ── CHẾ ĐỘ ③ (chỉ BÀY, chưa làm cổng) ──────────────────────────────────────
    b20 1:09:23  "hoặc THỜI GIAN ĐIỀU CHỈNH QUÁ DÀI... tâm lý thị trường thay đổi, người ta
                 THÍCH NGHI được, do đó có tham gia của LỰC BÁN -> quán tính tăng nó fail."
       -> thầy KHÔNG cho mốc "bao lâu là quá dài" (giống b5.1 0:15:02 "tuỳ giai đoạn"),
          nên chế độ này CHƯA cài thành cổng. Xem `lau_bao_nhieu()`.

    ⛔ CỬA CHẶN — b23 0:23:33: "hiện tại nó CÓ SÓNG KHÔNG để mà fail" -> chưa có quán tính
       thì KHÔNG có gì để fail.

    `rsi_dinh_cu` = RSI cực của cú A trước đó, để so chế độ ①.
    Trả True/False/None (None = chưa xét được).
    """
    if not co_quan_tinh:
        return None                      # b23 0:23:33
    sau = [r[j] for j in range(i_cuoi + 1, len(r)) if r[j] is not None]
    if not sau:
        return False

    # ② điều chỉnh xuống SÂU — b20 1:09:11 · b42 0:06:36
    if chieu_a == 1 and min(sau) < TAM_SAN:
        return True
    if chieu_a == -1 and max(sau) > (100.0 - TAM_SAN):
        return True

    # ① đỉnh MỚI không lên nổi vùng quán tính — b4 0:44:30 · 0:46:04
    if rsi_dinh_cu is not None:
        cuc_moi = max(sau) if chieu_a == 1 else min(sau)
        het_qt = (cuc_moi < QT_T) if chieu_a == 1 else (cuc_moi > QT_D)
        # chỉ kết luận khi đỉnh mới ĐÃ HÌNH THÀNH (đã quay đầu), không phán giữa đường
        da_quay = (sau[-1] < cuc_moi - 5) if chieu_a == 1 else (sau[-1] > cuc_moi + 5)
        if het_qt and da_quay:
            return True
    return False


def quan_tinh_manh_yeu(bars, a, rsi_len=14):
    """QUÁN TÍNH MẠNH / YẾU — b37, anh Hậu hỏi "reset lực mua lực bán", thầy vẽ bốn kịch bản
    (ảnh video Kevin chụp 27/09, mốc 50:46 → 51:22 · note 84 §4f):

    (mốc ~ lấy từ ảnh video; câu YẾU nằm NGAY TRƯỚC hình 50:46 — file 37.txt không có giờ)
    b37 ~50:48  "con sóng lên đây nó có quán tính tăng này, nó điều chỉnh xong nó PHÁ ĐỈNH
                 như này thì đây được gọi là quán tính tăng MẠNH… nó kéo tiếp khung lớn"
    b37 ~51:00  "nếu nó đi lên quán tính tăng ở đây mà nó hoàn thành quán tính tăng nó chỉ
                 PHỌT PHẸT khu vực này thôi, xong nó điều chỉnh và nó KHÔNG tạo ra quán tính
                 tăng mới thì là nó RESET"
    b37 ~50:35  "hoàn thành quán tính… nhưng nó lại KHÔNG PHÁ ĐƯỢC cái đỉnh quán tính tăng
                 hoặc cái đáy quán tính giảm đấy thì chúng ta cho rằng là nó YẾU"
    b41 1:28:43 "nó phá đỉnh mà KHÔNG tạo ra 80 mới nó vẫn là HOÀN THÀNH"

    Sóng có quán tính = CÚ A · điều chỉnh = vòng cung · sóng sau = từ lúc cung đóng.
    "Phá đỉnh" đọc bằng GIÁ ĐÓNG NẾN (b4 0:37:03 "chưa đóng nến là KHÔNG TÍNH").
    "Hoàn thành" đọc bằng fail_quan_tinh() đã có — KHÔNG dựng thước thứ hai (LUẬT 6).
    KHÔNG có số mới: chỉ so giá với đỉnh cú A và RSI với QT_T/QT_D (80/20) đã khai.

    ⛔ CHỈ BÀY — lõi là mô hình (note 88 ⑦). Không làm cổng, không vào Telegram.
    Trả (nhan, mo_ta): nhan ∈ "MANH" · "YEU" · "CHUA_RO" · None (cú A không có quán tính).
    """
    if not a or not a.get("quan_tinh"):
        return None, "cú A không có quán tính — không có gì để đo mạnh/yếu (b23 0:23:33)"
    ch = a.get("chieu_cu_a") or a.get("chieu")
    dinh, tuoi = a.get("dinh"), a.get("tuoi_cung")
    if ch not in (1, -1) or dinh is None or tuoi is None or not bars:
        return None, "thiếu mốc cú A"
    c = [x[4] for x in bars]
    i_dong = len(c) - 1 - tuoi                       # nến cung ĐÓNG (xem cu_a)
    if i_dong < 0:
        return None, "thiếu mốc cung"
    sau_c = c[i_dong + 1:]
    if not sau_c:
        return "CHUA_RO", "cung vừa đóng — sóng sau chưa chạy"
    r = K.rsi(c, rsi_len)
    sau_r = [x for x in r[i_dong + 1:] if x is not None]
    ten = "đỉnh" if ch == 1 else "đáy"
    vuot = (max(sau_c) > dinh) if ch == 1 else (min(sau_c) < dinh)
    qt_moi = bool(sau_r) and ((max(sau_r) >= QT_T) if ch == 1 else (min(sau_r) <= QT_D))
    het = fail_quan_tinh(r, i_dong, ch, True, a.get("rsi_cuc"))
    if vuot:
        if qt_moi:
            return "MANH", (f"phá {ten} cú A {dinh:.6g} + RSI tạo quán tính MỚI — "
                            f"lặp vòng (b37 50:48 · b4 0:44:30)")
        if het:
            return "MANH", (f"phá {ten} cú A {dinh:.6g} nhưng KHÔNG tạo quán tính mới — "
                            f"quán tính ĐÃ HOÀN THÀNH (b41 1:28:43)")
        return "MANH", f"phá {ten} cú A {dinh:.6g} — chờ xem có tạo quán tính mới (b37 50:48)"
    if het:
        # fail_quan_tinh() có HAI chế độ — nói đúng chế độ nào nổ, đừng gộp một câu.
        # Dùng lại TAM_SAN=40 đã khai trong fail_quan_tinh (b42 0:06:36), không số mới.
        sau_sau = bool(sau_r) and ((min(sau_r) < TAM_SAN) if ch == 1
                                   else (max(sau_r) > 100.0 - TAM_SAN))
        if sau_sau:
            return "YEU", (f"không phá được {ten} cú A {dinh:.6g}, điều chỉnh SÂU — RSI thủng "
                           f"{TAM_SAN:g}: lực {'bán' if ch == 1 else 'mua'} đã tham gia, "
                           f"quán tính bị triệt tiêu (b42 0:06:36)")
        return "YEU", (f"KHÔNG phá được {ten} cú A {dinh:.6g}, đã quay đầu — "
                       f"hoàn thành “phọt phẹt” (b37 51:00)")
    return "CHUA_RO", f"sóng sau chưa phá {ten} cú A {dinh:.6g}, chưa quay đầu"


def lau_bao_nhieu(i_dau, i_dinh, i_cuoi):
    """CHẾ ĐỘ ③ — thời gian điều chỉnh so với thời gian đẩy. **BÀY, không làm cổng.**
       b20 1:09:23: "THỜI GIAN ĐIỀU CHỈNH QUÁ DÀI... người ta THÍCH NGHI được".
       ⚠️ Thầy KHÔNG cho mốc "bao lâu là quá dài" -> cấm tự đặt ngưỡng ở đây (LUẬT 3).
       Trả tỉ lệ (nhịp sau / nhịp trước) hoặc None."""
    a1, a2 = i_dinh - i_dau, i_cuoi - i_dinh
    return round(a2 / a1, 2) if a1 > 0 else None

def cong_vao(bars, chieu_muon=None, rsi_len=14):
    """⭐ CỔNG VÀO — NGUỒN SỰ THẬT DUY NHẤT cho cả BOT lẫn PANEL PINE.

    Kevin 13/09: "làm sao cho mình soi trên TradingView nó khớp lệnh với con bot
    RSI báo là được". Muốn khớp thì hai bên phải gọi CÙNG MỘT HÀM — không ai được
    tự dựng cổng riêng. Pine là bản dịch 1-1 của hàm này.

    Trả dict:  co · cung · xung_luc · che_do_xl · loai · hop · fibo · vao · ly_do
    """
    c = [x[4] for x in bars]
    hi = [x[2] for x in bars]
    lo = [x[3] for x in bars]
    r = K.rsi(c, rsi_len)
    f = K._ema(r, 9)
    s_ = K._wma(r, 45)

    ds = vong_cung(f, s_, r=r, c=c)
    if not ds:
        return {"co": False, "vao": False,
                "ly_do": "⚪ KHÔNG có mô hình — quy luật 1: KHÔNG VÀO"}
    mh = ds[-1]
    ch = mh["chuan_bi"]
    i0, i1 = mh["i_dau"], mh["i_cuoi"]
    ph = max(hi[i0:i1 + 1])
    pl = min(lo[i0:i1 + 1])
    xl, che = xung_luc(r, c, mh, f, s_)
    now = c[-1]

    # ⭐ FIBO NEO TRÊN CÚ A (b10 2:40:42) — xem neo_cu_a(). Vòng cung là NHỊP ĐIỀU
    # CHỈNH của cú A, nên KHÔNG được lấy chính nó làm gốc fibo.
    neo = neo_cu_a(f, s_, hi, lo, mh)
    dau_A = dinh_A = chA = None
    f05 = f618 = f70 = None
    if neo is not None:
        dau_A, dinh_A, chA, _i_mo_A = neo
        # 01/10 mục O — cú A ngược chiều cung: KHÔNG dựng vùng (xem cu_a, b12 1:27:51)
        if chA == ch:
            f05, f618, f70 = fibo_cu_a(dau_A, dinh_A)
    # ⚠️ "QUÁ 0.7" đo ĐỘ SÂU NHẤT CỦA NHỊP ĐIỀU CHỈNH, không đo giá lúc này.
    # b10 2:41: "tối đa con sóng này để nó còn hiệu lực mạnh thì tối đa là nó
    # ĐIỀU CHỈNH về cái vùng này. Sâu hơn nữa về vùng 0.6 0.7 thì con sóng này
    # ĐÃ RẤT LÀ YẾU RỒI." Điều chỉnh đã ăn tới 186% rồi thì giá rớt ngược lại vào
    # vùng KHÔNG làm con sóng sống lại. (Ca TAO 4H 13/09: hồi 186% mà cổng vẫn 🟢.)
    # ⚠️ VÁ 14/09 lần 2 — Kevin bắt trên BTC M5: máy báo "CHỜ giá về vùng ≤ 0.5
    # (76895.9)" trong khi giá đang 77783, tức đã vượt xa mốc FAIL 77041.7.
    # Bản vá lần 1 đo trên i0..i1 (chỉ trong vòng cung) -> bắt được ca TAO (hồi sâu
    # rồi rớt lại) nhưng MẤT ca ngược: giá vượt 0.7 SAU KHI cung đã đóng.
    # Nhịp điều chỉnh KHÔNG dừng lúc cung đóng — nó chạy tới tận bây giờ.
    # Nay đo i0..HẾT: bắt được cả hai chiều.
    # C XÁC NHẬN = CHÍNH cú cắt ĐÓNG CUNG (i1).
    # ⭐ 03/10 mục H (Kevin CODE ĐI) — bản cũ đòi thêm MỘT lần cắt cùng chiều NỮA sau i1,
    # tức RSI phải nhúng lại rồi cắt lên lần hai ⇒ trễ một lần cắt; RSI đi thẳng thì C
    # không bao giờ tới (XAUT 30M 28/09 · PEPE 4H 01/10 bị "⏳ chưa có C").
    # Thầy b15 1:23:25→1:24:39 (nguồn cũ ghi "b15 22:25" là SAI giờ): "sau cái quá trình
    # tích lũy RSI của giai đoạn ĐIỀU CHỈNH… đường trung bình nhanh cắt lên trên đường
    # trung bình chậm… RSI kết thúc quá trình điều chỉnh". Vòng cung ∪/∩ CHÍNH LÀ nhịp
    # điều chỉnh của cú A (xem neo_cu_a), nên cú cắt đóng cung là cú cắt kết thúc điều
    # chỉnh — luôn đúng chiều mô hình (∪: EMA9 dưới WMA45 suốt cung ⇒ đóng bằng cắt LÊN).
    # Vế hai "giá quay về đỉnh cũ hoặc cao hơn" KHÔNG làm cổng (giá đã rời vùng 0.5–0.618,
    # vào là đuổi) — đã được BÀY ở quan_tinh_manh_yeu() "phá đỉnh cú A = MẠNH" và cảnh báo
    # D4 "qua đỉnh cú A — tìm entry mới". Pine: cXacNhan = mhCo.
    # ⭐ 22/09 — TÍNH TRƯỚC khối fibo, vì nó là MỐC ĐÓNG của nhịp điều chỉnh.
    cxn = True
    i_cxn = i1

    # ⚠️ "QUÁ 0.7" đo ĐỘ SÂU NHẤT CỦA NHỊP ĐIỀU CHỈNH.
    # ⭐ 22/09 — CHỐT CỬA SỔ ĐO TẠI C XÁC NHẬN, không đo tới tận bây giờ.
    # Kevin 21/09: "nó treo hoài sao ông". Bản cũ `min(lo[i0:])` đo tới HẾT dữ liệu,
    # nên khi sóng C đã chạy thì nó vẫn tính luôn cả C vào "độ sâu điều chỉnh" —
    # thủng 0.7 một lần là thủng VĨNH VIỄN, mô hình chết luôn dù giá đang đi lên.
    # Đo ADA 1h 21/09: 11 nến đủ mô hình + C xác nhận + test 2MA, giá đi từ 0.1926
    # lên 0.2208 mà câu chặn không đổi "đã qua fibo 0.7". Vào 0.1926 -> 0.2440 = +26.7%.
    # Chính thầy chốt đoạn hồi HẾT ở đây: b15 1:23:25 "RSI kết thúc quá trình điều chỉnh".
    # Đo quá mốc đó là đo SÓNG C mà tưởng là sóng B.
    # KHÔNG đụng ngưỡng 0.7 (b2 1:42:39) — chỉ sửa CỬA SỔ ĐO.
    # ⭐ 03/10 H — C = i1 nên cửa sổ này = chính vòng cung; đoạn SAU C do P đo riêng.
    _het = i_cxn + 1
    # `trong` = giá NẰM TRONG VÙNG [0.5, 0.618]: phải hồi ít nhất 0.5 mới vào,
    # sâu hơn 0.618 thì hết vùng (chưa hỏng — hỏng là thủng 0.7).
    if f05 is None:
        trong = qua = False
    elif chA == 1:                      # cú A TĂNG -> điều chỉnh đi XUỐNG
        sau_nhat = min(lo[i0:_het])
        qua = sau_nhat < f70
        trong = f618 <= now <= f05      # f618 thấp hơn f05
    else:                               # cú A GIẢM -> điều chỉnh đi LÊN
        sau_nhat = max(hi[i0:_het])
        qua = sau_nhat > f70
        trong = f05 <= now <= f618      # f618 cao hơn f05
    # ⭐ 03/10 mục P — Kevin chốt: SAU C xác nhận mà giá THỦNG 0.7 ⇒ mô hình CHẾT.
    # Cửa sổ trên (chốt 22/09) dừng ở C nên cú thủng sau C lọt: ENA 1H giá 0.23252 <
    # 0.7 = 0.232571 mà vẫn "⏳ CHỜ về VÙNG VÀO"; GRAM 15M 01/10 chọc 1.484 < SL 1.494.
    # Đo RIÊNG đoạn sau C (bên kia mốc 0.7 theo chiều điều chỉnh). Mục O đã bắt chA == ch
    # nên sóng C chạy đúng chiều không bao giờ làm đoạn này "thủng" — không lặp vết 21/09.
    # Ngưỡng 0.7 giữ nguyên (b2 1:42:39 · b10 2:41 "0.6 0.7 đã rất yếu").
    thung_sau_c = False
    if f05 is not None and i_cxn is not None and i_cxn + 1 < len(lo):
        thung_sau_c = (min(lo[i_cxn + 1:]) < f70) if chA == 1 else (max(hi[i_cxn + 1:]) > f70)

    # ⭐ 14/09 — BẢN CHẤT CỦA A + CỬA ⑤. Cần cú A đầy đủ (có rsi_cuc / cuc_cung)
    # nên gọi cu_a() — nó dùng chung neo_cu_a() với hàm này, không thể lệch cung.
    a_full = cu_a(c, hi, lo, rsi_len)
    bc, bc_vi = ban_chat_a(a_full, ch)

    # CỬA ⑤ — CHỈ ÁP CHO CA TIẾP DIỄN (Kevin 14/09):
    #   "A tiếp diễn xu hướng lực mua tạm nghỉ thì RSI đừng phá 40%,
    #    phá thì theo logic có lực bán tham gia rồi, kèo không đẹp nữa"
    # b13 ~1:51:37: RSI giảm trong điều chỉnh = lực mua TẠM NGHỈ và "CHƯA CÓ LỰC
    #   BÁN THAM GIA VÀO"; b10 ~1:26:30: không có lực bán = "RSI không tụt sâu được nữa".
    # Mốc 40–60 = vùng cân bằng (b3 2:08:50 · b4 1:01:02 · b6 0:01:07 · b23 0:06:19).
    # Thủng 40 (long) / vượt 60 (short) = ra khỏi vùng cân bằng = lực ngược đã vào thật.
    # Dùng TAM_SAN=40 đã khai sẵn — KHÔNG đặt số mới.
    # Ca SÓNG MỚI thì NGƯỢC LẠI: RSI bắt buộc từng ở cực, nên KHÔNG áp cửa này.
    # ⭐ 03/10 mục Q — "thủng 40" đo bằng CƯ TRÚ, không bằng RSI CỰC TRỊ. Ca PEPE 4H
    # 02/10: RSI chọc 36.4 nhưng chỉ 3/44 nến dưới 40 -> bản cũ ❌, giá chạy +5.3%.
    # Thầy SỬA BÀI b43 0:10:20→0:10:45: "RSI nó chỉ kéo xuống vùng 40 nó lại giật lên…
    # chứ nó có DUY TRÌ được… dưới vùng 40 đâu" + b31 1:29:11 "duy trì MỘT CỤM nến".
    # Dùng lại cu_tru() + CT_CU_TRU=25% (note 77) — KHÔNG số mới. Đo trên chính vòng
    # cung i0..i1 (= nhịp B, cùng đoạn với cuc_cung). Pine: `ctB`.
    cc = (a_full or {}).get("cuc_cung")
    tran_b = TAM_SAN if ch == 1 else (100.0 - TAM_SAN)
    ct_b = cu_tru(r, i0, i1, -ch)        # % nến RSI ở PHÍA lực ngược của mốc 40/60
    pha_b = sat_mep = False
    if bc == "TIEP" and ct_b is not None:
        pha_b = ct_b >= CT_CU_TRU
        sat_mep = abs(ct_b - CT_CU_TRU) <= CT_CU_TRU * 0.05   # ±5% — thuyết tương đối

    # ══════════ ⭐ 16/09 · TẦNG LỰC + CẤU TRÚC — CHỈ BÀY, KHÔNG PHẢI CỔNG ══════════
    # Kevin đã chốt: "LÕI = mô hình. Xăng/xung lực/tương quan giá là RÂU RIA, CẤM làm cổng."
    # Nên tất cả những gì dưới đây đi vào dict để MẮT đọc, KHÔNG chen vào chuỗi quyết định.
    # Nguồn từng mục: xem docstring của cu_tru / quan_tinh_a / cau_truc_gia / fail_quan_tinh.
    het_i = len(c) - 1
    # ① lực CỦA CÚ A — cư trú trên chính đoạn A (bậc 60/40)
    ct_a = None if neo is None else cu_tru(r, _i_mo_A, i0, chA)
    # ② lực HIỆN TẠI của khung — 20 nến gần nhất
    ct_nay = cu_tru(r, max(0, het_i - 19), het_i, ch)
    # ⑥ ĐỘ MƯỢT phải tính TRƯỚC — quán tính cần nó (b13 1:22:25)
    muot, ho_max = do_muot(f, s_, i0, i1)
    # ③ quán tính của cú A — 80/20 (b20 1:06:45) + mở rộng→thu hẹp (b13 1:22:25)
    qt_a = quan_tinh_a((a_full or {}).get("rsi_cuc"), chA, muot)
    # ④ fail quán tính — HAI chế độ của thầy, KHÔNG phải "MA cắt ngược" (b4 0:42:21)
    fail_a = fail_quan_tinh(r, i1, chA, qt_a, (a_full or {}).get("rsi_cuc"))
    # ③b nhịp sau / nhịp trước — BÀY, thầy không cho mốc (b20 1:09:23)
    lau = lau_bao_nhieu(mh["i_dau"], mh["i_dinh"], mh["i_cuoi"])
    # ⑤ cấu trúc giá trên khung mô hình — đáy/đỉnh gần nhất là chỗ SL nấp (b8 1:27:15)
    ct_giu, ct_moc = cau_truc_gia(bars, ch, rsi_len)

    d = {"co": True, "cung": mh, "xung_luc": xl, "che_do_xl": che,
         "cu_tru_a": ct_a, "cu_tru_nay": ct_nay,
         "quan_tinh_a": qt_a, "fail_quan_tinh": fail_a,
         "cau_truc_giu": ct_giu, "cau_truc_moc": ct_moc,
         "do_muot": muot, "ho_rong_nhat": ho_max, "lau_dieu_chinh": lau,
         "loai": mh["loai"], "hop": (pl, ph), "fibo": (f05, f618, f70),
         "cu_a": None if neo is None else (dau_A, dinh_A, chA),
         "ban_chat": bc, "ban_chat_vi": bc_vi, "rsi_cuc_b": cc, "cu_tru_b": ct_b,
         "sat_mep": sat_mep,
         "gia": now, "c_xac_nhan": cxn, "thung_sau_c": thung_sau_c, "chieu": ch}

    if chieu_muon is not None and ch != chieu_muon:
        d.update(vao=False, ly_do=f"mô hình {'∪ TĂNG' if ch == 1 else '∩ GIẢM'} NGƯỢC chiều lệnh")
    elif neo is None:
        # Không có lần cắt nào TRƯỚC cung -> không có cú A -> không có gốc fibo.
        # Không đoán bừa một vùng vào: b10 2:41 "không biết đo điểm nào thì nó ra lung tung".
        d.update(vao=False, ly_do="⚠️ không có cú A trước cung — không dựng được vùng vào")
    elif bc == "SIDEWAY":
        # ⭐ 14/09 — THAY khối chặn thô cũ ("cú A không phải sóng sạch").
        # BẢN CŨ chặn MỌI ca A ngược chiều B — đúng với 8/8 ca đo được 14/09 vì
        # cả 8 đều có RSI cực của A trong 41–68, nhưng chặn bằng lý do THÔ:
        # hôm nào A thực sự thủng 30 rồi bo cong lên thì nó chặn NHẦM đúng SÓNG MỚI.
        # Nay dùng đúng bộ ba b23 0:06:19 — xem ban_chat_a().
        d.update(vao=False, ly_do=f"⚪ SIDEWAY — {bc_vi}")
    elif bc is None:
        d.update(vao=False, ly_do=f"⚠️ chưa đọc được bản chất của A — {bc_vi}")
    elif f05 is None:
        # ⭐ 01/10 mục O — cú A NGƯỢC chiều cung: chưa có sóng cùng chiều -> không có
        # B, không có vùng. NÓI ra, không im (note 88 ④). Khớp Pine `cuASach`.
        d.update(vao=False,
                 ly_do=(f"🔵 SÓNG MỚI — cú A ngược chiều cung, chưa có sóng "
                        f"{'tăng' if ch == 1 else 'giảm'} để kéo fibo · chờ sóng 1 chạy "
                        f"rồi hồi (b12 1:27:51 · b10 2:40:33)"))
    elif mh["loai"] == "song":
        d.update(vao=False, ly_do=f"⛔ CUNG SÓNG — giá đã chạy {mh['d_gia']:+.0f}% TRONG hộp · vào là ĐUỔI (b9 22:22)")
    elif qua:
        d.update(vao=False, ly_do="❌ giá đã qua fibo 0.7 — sóng FAIL")
    elif thung_sau_c:
        d.update(vao=False, ly_do=f"❌ SAU C xác nhận giá đã thủng fibo 0.7 ({f70:.6g}) — "
                                  f"sóng FAIL, mô hình CHẾT (Kevin chốt 03/10 · b10 2:41)")
    elif pha_b:
        d.update(vao=False,
                 ly_do=f"❌ A TIẾP DIỄN nhưng B CƯ TRÚ {'dưới' if ch == 1 else 'trên'} "
                        f"{tran_b:.0f} {ct_b:.0f}% số nến (≥{CT_CU_TRU}%, RSI cực {cc}) — lực "
                        f"{'bán' if ch == 1 else 'mua'} đã tham gia, kèo hết đẹp "
                        f"(b13 1:51:37 · b43 0:10:33)")
    elif not trong:
        d.update(vao=False,
                 ly_do=f"⏳ CHỜ giá về VÙNG VÀO {f05:.6g}–{f618:.6g} (fibo 0.5→0.618)")
    else:
        _nh = NHAN_BAN_CHAT.get(bc, "")
        _sm = " · ⚠️ sát mép" if sat_mep else ""
        d.update(vao=True,
                 ly_do=f"🟢 ĐỦ ĐIỀU KIỆN — {_nh} · cung tích luỹ · "
                        f"TRONG VÙNG {f05:.6g}–{f618:.6g} · C xác nhận{_sm}")
    return d


def cong_tac(bang):
    """Cụm CUM_CONG_TAC (1H·4H·1D — Kevin chốt 13/09, cụm gồng b5.1) đồng pha hay
    ngược pha. Trả (che_do, chi_tiet).
    ⚠️ SỬA 27/09 (B6) — dòng này cũ ghi "Cụm 1D→1M", không khớp hằng số ở dòng 23.

    che_do: "KY_VONG+" (đồng thuận TĂNG) · "KY_VONG-" (đồng thuận GIẢM)
            · "CHUA_RO" · "CAN_TRONG" (ngược pha trong chính cụm)
    ⚠️ SỬA 12/09: bản cũ trả "KY_VONG" cho CẢ HAI chiều, nên chỗ gọi làm
    `dong_pha = che_do == "KY_VONG"` rồi đưa vào cham_bac() như thể "khung lớn đồng pha
    VỚI mô hình". Sai: khung lớn đồng thuận GIẢM mà mô hình ∪ TĂNG vẫn được tính là
    đồng pha. Nay tách chiều, và dùng dong_pha_voi() để so."""
    co = [(t, bang[t]["trend"]) for t in CUM_CONG_TAC if t in bang]
    if not co:
        return None, "thiếu khung lớn"
    up = sum(1 for _, d in co if d == 1)
    dn = sum(1 for _, d in co if d == -1)
    ct = " ".join(f"{t.upper()}{'▲' if d == 1 else '▼' if d == -1 else '—'}" for t, d in co)
    n = len(co)
    # "đồng pha" đòi ĐA SỐ khung có hướng và CÙNG chiều. Một khung có hướng còn ba khung
    # quấn dây điện thì chưa gọi là đồng thuận được — khung lớn vẫn đang sideway.
    du = (up + dn) * 2 >= n
    if up and not dn:
        return ("KY_VONG+" if du else "CHUA_RO"), (f"đồng thuận ▲ ({up}/{n}) · {ct}" if du
                else f"mới {up}/{n} khung có hướng ▲, còn lại sideway · {ct}")
    if dn and not up:
        return ("KY_VONG-" if du else "CHUA_RO"), (f"đồng thuận ▼ ({dn}/{n}) · {ct}" if du
                else f"mới {dn}/{n} khung có hướng ▼, còn lại sideway · {ct}")
    if not up and not dn:
        return "CHUA_RO", f"khung lớn chưa có hướng nào · {ct}"
    return "CAN_TRONG", f"NGƯỢC PHA {up}▲/{dn}▼ · {ct}"


def dong_pha_voi(che_do, chieu_mo_hinh):
    """Khung lớn có đồng pha VỚI mô hình không (b38 44:31 — điều kiện của bậc 2).
    chieu_mo_hinh: 1 = mô hình chuẩn bị TĂNG, -1 = GIẢM.
    Trả True/False/None (None = chưa đọc được khung lớn, KHÔNG suy ra False)."""
    if che_do in (None, "CHUA_RO"):
        return None
    if che_do == "CAN_TRONG":
        return False
    return (che_do == "KY_VONG+") if chieu_mo_hinh == 1 else (che_do == "KY_VONG-")


# ⭐ ① CÔNG TẮC KỲ VỌNG — Kevin chốt 23/09. Bật theo LỰC ở KHUNG LỚN.
CT_NEN     = 45   # số nến gần nhất để đo cụm cư trú — bằng chu kỳ WMA45
CT_CU_TRU  = 25   # % — ngưỡng gọi là "CỤM nến", không phải một cây chọc lên.
                  # Số này lấy từ note 77 (đo 16/09: cư trú >=25% -> 7/7 coin trên nền,
                  # 4/4 khúc thời gian dương). KHÔNG phải số tự đặt.

def cong_tac_ky_vong(nen, tf_lon="1d", rsi_len=14):
    """① CÔNG TẮC KỲ VỌNG — đọc LỰC ở KHUNG LỚN rồi bật chế độ.

    b51 0:21:15  "chúng ta biết là LÚC NÀO chúng ta nên PHÒNG THỦ, lúc nào chúng ta nên
                  TẤN CÔNG, cái đó là một cái cực kỳ quan trọng"
    b52 0:05:12  "có những giai đoạn chúng ta phải TẤN CÔNG, có những giai đoạn chúng ta
                  phải chấp nhận là chúng ta ở cái trạng thái PHÒNG THỦ... giữ được tài
                  khoản hoà hoặc lãi ít một chút NÓ ĐÃ LÀ THÀNH CÔNG LẮM RỒI"

    Đọc lực bằng ĐỦ HAI VẾ — b43 0:59:40 "nó có kéo được RSI lên trên vùng 60, có thể nó
    GIỮ ĐƯỢC một lúc, mà nó tương ứng với HAI ĐƯỜNG TRUNG BÌNH của RSI tạo ra một XU HƯỚNG":
      vế ①  cụm RSI CƯ TRÚ ngoài mốc 60/40 >= CT_CU_TRU%  (b31 1:29:11 "duy trì một CỤM
            CÂY NẾN", b30 0:51:02 "nó CHỌC lên thì KHÔNG gọi là có lực mua")
      vế ②  EMA9 và WMA45 cùng phía  (hai MA tạo xu hướng)

    ⚠️ Đây là công tắc CHẾ ĐỘ, KHÔNG phải cổng vào lệnh. Nó nói "được phép chiều nào",
    không nói "vào chỗ nào" — điểm vào là việc của khung nhỏ (b12, b11 1:30:39).
    Và KHÔNG dùng độ mở rộng làm điều kiện: độ mở đạt cực đại SAU khi giá đã đi, lấy nó
    làm cổng là mua đỉnh (note 77 muc 7).

    Trả (che_do, chieu, vi_sao):
      "TAN_CONG"  chieu= 1  -> chỉ MUA / CHỜ MUA
      "TAN_CONG"  chieu=-1  -> chỉ BÁN / CHỜ BÁN
      "PHONG_THU" chieu= 0  -> sideway: long/short ĂN NGẮN, chốt non, hạ kỳ vọng
      None        chieu= 0  -> thiếu dữ liệu, KHÔNG suy ra phòng thủ
    """
    # ⭐ 26/09 — `tf_lon` nhận CHUỖI (một khung, như cũ) HOẶC DANH SÁCH khung.
    # Với danh sách: đọc lực TỪNG khung rồi tổng hợp theo đúng lời thầy —
    #   b38 00:29:14 "xu hướng là sự ĐỒNG THUẬN LỰC ở các khung thời gian khác nhau"
    #   b4  1:12:08  khung chọi khung = SIDEWAY ĐA KHUNG (SW2) -> phòng thủ
    #   b4  1:00:07  không bên nào có lực = SIDEWAY ĐƠN KHUNG (SW1) -> phòng thủ
    # KHÔNG đặt ngưỡng "bao nhiêu khung là đủ" — chỉ hỏi ĐỒNG THUẬN hay CHỎI.
    if not isinstance(tf_lon, str):
        dai = [t for t in (tf_lon or ()) if (nen or {}).get(t)]
        if not dai:
            return None, 0, "thiếu nến mọi khung lớn %s" % str(tuple(tf_lon or ()))
        ket = [(t,) + tuple(cong_tac_ky_vong(nen, t, rsi_len)) for t in dai]
        co_luc = [(t, chieu) for t, cd, chieu, _ in ket if cd == "TAN_CONG"]
        chieu_co = set(c for _, c in co_luc)
        ten = " · ".join("%s%s" % (t.upper(), "↑" if c == 1 else "↓") for t, c in co_luc)
        if len(chieu_co) == 1:
            c = chieu_co.pop()
            return ("TAN_CONG", c,
                    "LỰC %s ĐỒNG THUẬN khung lớn (%s) — chỉ %s/CHỜ %s · b38 00:29:14"
                    % ("MUA" if c == 1 else "BÁN", ten,
                       "MUA" if c == 1 else "BÁN", "MUA" if c == 1 else "BÁN"))
        if len(chieu_co) > 1:
            return ("PHONG_THU", 0,
                    "KHUNG LỚN CHỎI NHAU (%s) = SIDEWAY ĐA KHUNG SW2 — ăn ngắn, "
                    "chốt non (b4 1:12:08)" % ten)
        return ("PHONG_THU", 0,
                "KHÔNG khung lớn nào có lực (%s) = SIDEWAY ĐƠN KHUNG SW1 — ăn ngắn, "
                "chốt non (b4 1:00:07 · b52 0:05:12)" % " · ".join(t.upper() for t in dai))

    b = (nen or {}).get(tf_lon)
    if not b:
        return None, 0, "thiếu nến khung lớn %s" % str(tf_lon).upper()
    r = K.rsi([x[4] for x in b], rsi_len)
    if not r or r[-1] is None:
        return None, 0, "chưa đọc được RSI khung lớn %s" % str(tf_lon).upper()
    e, w = K._ema(r, 9), K._wma(r, 45)
    if e[-1] is None or w[-1] is None:
        return None, 0, "chưa đủ nến cho EMA9/WMA45 trên %s" % str(tf_lon).upper()
    n = len(r)
    i_tu = max(0, n - CT_NEN)
    ct_mua = cu_tru(r, i_tu, n - 1, 1) or 0.0     # % nến GIỮ trên 60
    ct_ban = cu_tru(r, i_tu, n - 1, -1) or 0.0    # % nến GIỮ dưới 40
    hai_ma_len = e[-1] > w[-1]
    hai_ma_xuong = e[-1] < w[-1]
    nen_ct = "%s cụm %d nến: giữ trên 60 %.0f%% · giữ dưới 40 %.0f%% · EMA9 %.1f %s WMA45 %.1f" % (
        str(tf_lon).upper(), n - i_tu, ct_mua, ct_ban, e[-1],
        ">" if hai_ma_len else "<" if hai_ma_xuong else "=", w[-1])
    if ct_mua >= CT_CU_TRU and hai_ma_len:
        return "TAN_CONG", 1, "LỰC MUA nắm quyền — chỉ MUA/CHỜ MUA · " + nen_ct
    if ct_ban >= CT_CU_TRU and hai_ma_xuong:
        return "TAN_CONG", -1, "LỰC BÁN nắm quyền — chỉ BÁN/CHỜ BÁN · " + nen_ct
    thieu = []
    if ct_mua < CT_CU_TRU and ct_ban < CT_CU_TRU:
        thieu.append("chưa bên nào cư trú đủ %d%%" % CT_CU_TRU)
    if not hai_ma_len and not hai_ma_xuong:
        thieu.append("hai MA chưa tách")
    elif (ct_mua >= CT_CU_TRU) != hai_ma_len:
        thieu.append("cư trú và hai MA chỏi nhau")
    return ("PHONG_THU", 0,
            "SIDEWAY — không bên nào có lực (%s) → ăn ngắn, chốt non, hạ kỳ vọng (b52 0:05:12) · %s"
            % (" · ".join(thieu) or "chưa rõ", nen_ct))


# ══════════════════ K3+K4 · MÔ HÌNH ĐẸP (bậc 1/2/3 — b8/b38) ══════════════════
def cu_a(closes, highs, lows, rsi_len=14, vols=None):
    """CÚ A = đoạn LIỀN TRƯỚC vòng cung (note 63: "CÚ A và MÔ HÌNH là hai đoạn LIỀN NHAU").

    ⚙️ GỘP 13/09 — Kevin: "vòng cung với mô hình là 1 mà".
    MỘT khái niệm = MỘT nguồn sự thật. Vòng cung LẤY DUY NHẤT từ vong_cung()
    (2 lần cắt · TRỤC X · TRỤC Y). Trước đây hàm này tự dò cat[] lần nữa và
    dùng trang_thai_cung() — thành bản cài thứ hai, luật khác, chạy song song.

    cú A     = từ điểm cắt TRƯỚC cung  →  điểm MỞ cung
    vòng cung = i_dau → i_cuoi của vong_cung()
    """
    r = K.rsi(closes, rsi_len)
    f = K._ema(r, 9)
    s = K._wma(r, 45)

    ds = vong_cung(f, s, r=r)                 # NGUỒN DUY NHẤT
    if not ds:
        return None
    mh = ds[-1]
    chuan_bi    = mh["chuan_bi"]
    i_mo_cung   = mh["i_dau"]                 # cung MỞ = cú A KẾT THÚC
    i_dong_cung = mh["i_cuoi"]                # cung ĐÓNG

    mc = cac_muc_cat(f, s)                    # điểm cắt TRƯỚC cung = cú A MỞ
    truoc_cung = [i for i, _ in mc if i < i_mo_cung]
    if not truoc_cung:
        return None
    i_mo_A = truoc_cung[-1]

    seg_r = [x for x in r[i_mo_A:i_mo_cung + 1] if x is not None]
    if not seg_r:
        return None
    # RSI cực của cú A — đo theo CHIỀU THẬT của cú A, xác định bên dưới.
    # (b8 17:23 nói cú A cùng chiều mô hình; nay dùng làm ĐIỀU KIỆN KIỂM, không áp đặt)
    seg_hi_r, seg_lo_r = max(seg_r), min(seg_r)

    # ══════ ĐK3 (b15) — VÁ 11/09, ca UNI H4 Kevin bắt được ══════
    # Bản cũ đo dốc+mở rộng trên đoạn CÚ A (i_mo_A → i_mo_cung). SAI ĐOẠN.
    # Thầy b15 (01:38): "cái điểm bắt đầu của mô hình... ngay điểm đường trung bình
    # nhanh cắt xuống đường trung bình chậm... điểm kết thúc... chỗ đường trung bình
    # nhanh cắt [lên]" -> MÔ HÌNH = CHÍNH VÒNG CUNG. Rồi thầy hỏi đoạn đó có phải
    # mô hình không: "Cái này KHÔNG được gọi là mô hình. Tại vì đường W45 nó ĐI NGANG
    # luôn chứ nó không có ĐỘ DỐC." — "Đúng rồi... nó không có ĐỘ MỞ RỘNG của RSI."
    # Nên dốc và mở rộng phải đo TRÊN VÒNG CUNG, không phải trên cú A.
    #
    # Dốc chuẩn hoá theo ĐỘ DÀI CUNG (điểm RSI / nến) — cung dài thì tổng dịch chuyển
    # lớn là đương nhiên, cái thầy nhìn là đường W45 có NGHIÊNG hay không.
    cung_s = [x for x in s[i_mo_cung:i_dong_cung + 1] if x is not None]
    cung_f = [x for x in f[i_mo_cung:i_dong_cung + 1] if x is not None]
    if len(cung_s) < 3 or len(cung_f) < 3:
        return None
    doc     = abs(cung_s[-1] - cung_s[0]) / max(1, len(cung_s) - 1)   # điểm/nến
    mo_rong = max(abs(a - b) for a, b in zip(cung_f, cung_s))          # đỉnh khoảng hở
    if doc < DOC_TOI_THIEU or mo_rong < MO_RONG_TOI_THIEU:
        return None

    # giữ số đo trên cú A để đối chiếu, KHÔNG dùng làm cổng
    seg_s = [x for x in s[i_mo_A:i_mo_cung + 1] if x is not None]
    seg_f = [x for x in f[i_mo_A:i_mo_cung + 1] if x is not None]
    doc_A     = abs(seg_s[-1] - seg_s[0]) if len(seg_s) >= 2 else 0.0
    mo_rong_A = max((abs(a - b) for a, b in zip(seg_f, seg_s)), default=0.0)

    seg_h = highs[i_mo_A:i_mo_cung + 1]
    seg_l = lows[i_mo_A:i_mo_cung + 1]
    if not seg_h or not seg_l:
        return None
    g_hi, g_lo = max(seg_h), min(seg_l)
    if g_hi - g_lo <= 0:
        return None
    # ⚠️ VÁ 11/09 — LỖI NẶNG NHẤT. Bản cũ gán dau/dinh theo CHIỀU VÒNG CUNG:
    #       dinh_A = g_hi if chuan_bi == 1 else g_lo
    #    tức ép cú A phải cùng chiều mô hình, BỎ QUA thứ tự thời gian.
    #    UNI 4H: đoạn 03/09→06/09 giá đi TỪ 5.85 LÊN 7.05 (+20.5%), thấp nhất 5.63
    #    xảy ra TRƯỚC cao nhất 7.249 — vậy mà code báo "7.249 → 5.63 = -22.3%",
    #    BỊA ra một cú sập chưa từng xảy ra. Kéo theo fibo tính ngược -> mọi
    #    "vùng vào" đều sai.
    #    NAY: đọc theo THỜI GIAN. Cực trị nào xảy ra TRƯỚC là điểm đầu.
    # ⭐ 14/09 — GỌI CHUNG neo_cu_a() với cong_vao(). Trước đây hai hàm tự tính neo
    # riêng: cu_a() neo trên cú A (đúng), cong_vao() neo trên vòng cung (sai) -> một
    # bản tin tự mâu thuẫn ("trong vùng 0.5" ngay cạnh "đã hồi 186%", ca TAO 4H 13/09).
    # Nay MỘT hàm, hai nơi gọi -> không thể lệch. kiem_chung.py có phép kiểm khoá lại.
    # ══════ VIẾT LẠI 12/09 — theo đúng định nghĩa thầy, bỏ thứ mình tự thêm ══════
    # note 63 / b10 40:31: CÚ A = "đoạn EMA9 TRÊN WMA45 và mở rộng, từ lần cắt LÊN đến
    # lần cắt XUỐNG". Tức chiều cú A do CẤU TRÚC MA quyết định, không do mình suy:
    #   cung ∪ (mở bằng cắt XUỐNG) -> trước đó EMA9 nằm TRÊN -> cú A là sóng TĂNG
    #   cung ∩ (mở bằng cắt LÊN)   -> trước đó EMA9 nằm DƯỚI -> cú A là sóng GIẢM
    # 🗑 03/10 — câu cũ "Nên chieu_A LUÔN bằng chuan_bi" là SAI theo số đo (UNI/SOL/DOGE 01/10):
    # chiều cú A đọc theo THỜI GIAN (dưới đây), nên CÓ ca cú A NGƯỢC chiều cung = SÓNG MỚI
    # (mục O · b12 1:27:51) — khi đó `song_sach` False, không dựng fibo/vùng vào.
    #
    # b10 40:31: "quá trình tăng MỞ RA thì là từ cái ĐÁY này, KẾT THÚC là từ cái ĐỈNH
    # này". Sóng tăng phải có ĐÁY TRƯỚC, ĐỈNH SAU. Nếu ngược lại thì đoạn đó KHÔNG phải
    # một con sóng sạch -> đúng mô tả TH2 của b8: "trước đó nó là KHU VỰC SIDEWAY và
    # KHÔNG CÓ MỘT CÁI MÔ HÌNH GÌ CẢ". Lúc đó KHÔNG đo "hồi bao nhiêu %" nữa, vì không
    # có con sóng nào để mà hồi. (Trước đây đo bừa -> ra hồi 132% · 252% · 466%.)
    # chiều cú A đọc theo THỜI GIAN — cực trị nào xảy ra TRƯỚC là điểm đầu.
    # (VÁ 11/09, ca UNI: ép chiều theo cung thì code bịa ra một cú sập chưa từng xảy ra.
    #  Phép kiểm t3_cua_theo_thoi_gian khoá luật này — 12/09 mình thử đổi sang "chiều
    #  theo cấu trúc MA" và t3 bắt được ngay. Đừng đổi lại.)
    _neo = neo_cu_a(f, s, highs, lows, mh)
    if _neo is None:
        return None
    dau_A, dinh_A, chieu_A, _ = _neo
    # ⭐ 01/10 (mục O note 70) — cú A NGƯỢC chiều cung (🔵 SÓNG MỚI) thì KHÔNG phải
    # sóng sạch: không có A cùng chiều thì không có B, không có ABC.
    #   b12 1:27:51 "cái đoạn này nó chưa hề có con sóng gì cả… KHÔNG gọi là ABC nhá"
    #   b10 2:40:33 "chỉ đo Fibo khi nó ĐÃ HÌNH THÀNH con sóng"
    # Pine `cuASach` (k23_v3.pine) đã có luật này; Python mất từ 14/09 khi thay khối
    # chặn thô bằng ban_chat_a() — đổi nhãn mà quên giữ vế "không dựng vùng".
    # Hậu quả đo 01/10: 41 dòng ⏳ "CHỜ giá về vùng" với vùng mua nằm TRÊN giá,
    # SL nằm TRÊN giá mua, giá rơi qua đáy cú A vẫn CHỜ (UNI 1H 8.945 vs vùng 9.93).
    song_sach = (chieu_A == chuan_bi)
    bien = abs(dinh_A - dau_A)
    # ĐỘ ĐIỀU CHỈNH đo TRÊN VÒNG CUNG (b8 17:23: cung = quá trình điều chỉnh của cú A),
    # không đo tới giá hiện tại, và đi TIẾP theo chiều cú A thì không tính là hồi.
    if not song_sach:
        hoi = None                          # không có con sóng nào để mà hồi
    elif chieu_A == 1:
        day_cung = min(lows[i_mo_cung:i_dong_cung + 1])
        hoi = max(0.0, (dinh_A - day_cung) / bien * 100.0) if bien > 0 else None
    else:
        dinh_cung = max(highs[i_mo_cung:i_dong_cung + 1])
        hoi = max(0.0, (dinh_cung - dinh_A) / bien * 100.0) if bien > 0 else None
    # VOLUME trong cung so với 50 nến trước cung (luật rút từ dữ liệu)
    vol_ti = None
    if vols and i_mo_cung >= 50:
        tr = vols[max(0, i_mo_cung-50):i_mo_cung]
        tg = vols[i_mo_cung:i_dong_cung+1]
        if tr and tg and sum(tr) > 0:
            vol_ti = round(sum(tg)/len(tg) / (sum(tr)/len(tr)) * 100, 0)
    # TẠM NGHỈ: trong cung RSI đi ngược mà GIÁ KHÔNG đi theo (b3 1798)
    seg_c = r[i_mo_cung:i_dong_cung+1]
    hop = [x for x in seg_c if x is not None]
    tam_nghi = None
    if hop:
        j = i_mo_cung + seg_c.index(min(hop) if chuan_bi == 1 else max(hop))
        dg = (closes[j]-closes[i_mo_cung])/closes[i_mo_cung]*100
        tam_nghi = (dg >= -0.2) if chuan_bi == 1 else (dg <= 0.2)
    # ══════ VÁ 12/09 — Kevin bắt trên chart LINK H4, cung 08/09 ══════
    # "chạm 70/30" phải đo TRONG VÒNG CUNG, không đo trên cú A.
    # note 62 checklist mục 3: "RSI chạm 70/30 trong quá trình CUNG (80/20 càng tốt)".
    # Thầy b7 30:16: "nếu mô hình đi một QUÁ TRÌNH LÊN ĐẾN VÙNG 70 xong ĐI XUỐNG — có
    # sự gia tăng lực mua không? CÓ. Vì 70." -> đang tả chính con cung.
    # Ca LINK: cung 08/09 RSI lên tới 83.6 trong cung, nhưng cú A chỉ 67.6. Đo nhầm
    # đoạn -> gạt mất con cung Kevin khoanh đỏ.
    seg_cung = [x for x in r[i_mo_cung:i_dong_cung + 1] if x is not None]
    cuc_cung  = (min(seg_cung) if chuan_bi == 1 else max(seg_cung)) if seg_cung else None
    cham_cung = False if cuc_cung is None else (cuc_cung <= CHAM_D if chuan_bi == 1 else cuc_cung >= CHAM_T)
    qt_cung   = False if cuc_cung is None else (cuc_cung <= QT_D   if chuan_bi == 1 else cuc_cung >= QT_T)
    cuc       = seg_hi_r if chieu_A == 1 else seg_lo_r   # RSI cực của cú A
    cham      = (cuc >= CHAM_T) if chieu_A == 1 else (cuc <= CHAM_D)
    quan_tinh = (cuc >= QT_T)   if chieu_A == 1 else (cuc <= QT_D)
    # b13: cú A cùng chiều cung = "có lực liên quan phía trước" (điều chỉnh của quán tính).
    #      Ngược chiều = trường hợp 2, "không có lực liên quan" — phải BÀY RA, không giấu.
    lien_quan = (chieu_A == chuan_bi)
    return {
        "vol_ti": vol_ti, "tam_nghi": tam_nghi, "chieu_cu_a": chieu_A, "lien_quan": lien_quan,
        "chieu": chuan_bi, "rsi_cuc": round(cuc, 1), "cham": cham, "quan_tinh": quan_tinh,
        "cuc_cung": None if cuc_cung is None else round(cuc_cung, 1),
        "cham_cung": cham_cung, "qt_cung": qt_cung,
        "dau": dau_A, "dinh": dinh_A, "song_sach": song_sach,
        "bien_pct": round((dinh_A - dau_A) / dau_A * 100, 2) if dau_A else None,
        "hoi": None if hoi is None else round(hoi, 1),
        "f05":    None if not song_sach else fibo_cu_a(dau_A, dinh_A)[0],
        "f618":   None if not song_sach else fibo_cu_a(dau_A, dinh_A)[1],
        # ⚙️ 13/09 Kevin chốt SL tham khảo = fibo 0.7 (b10 2:41 "0.6-0.7 đã rất yếu")
        "f70":    None if not song_sach else fibo_cu_a(dau_A, dinh_A)[2],
        "so_nen": i_mo_cung - i_mo_A, "tuoi_cung": len(f) - 1 - i_dong_cung,
        "rsi_mo_cung": None if r[i_mo_cung] is None else round(r[i_mo_cung], 1),
        "rsi_dong_cung": None if r[i_dong_cung] is None else round(r[i_dong_cung], 1),
        "doc": round(doc, 3), "mo_rong": round(mo_rong, 2),
        "doc_A": round(doc_A, 2), "mo_rong_A": round(mo_rong_A, 2),
        "dai_cung": len(cung_s) - 1,
    }


# ══════════════════ KHUNG NẮM QUYỀN ══════════════════
# khung NHỎ không bao giờ nắm quyền (b23: M1/M5 chỉ THỂ HIỆN lực, b24: chất xúc tác)
def khung_quyet_dinh(bang, tf_choi, co_mo_hinh):
    """⚠️ HÀM ĐA KHUNG — CHỈ BÀY CHO MẮT, KHÔNG NỐI VÀO ĐƯỜNG RA QUYẾT ĐỊNH.

    Kevin chốt 11/09: "máy thì nên 1 khung h1 thôi, đa khung là do mình —
    ảnh hưởng đến tâm lý". Máy bày 6 khung thì 6 khung nói 6 kiểu, sinh phân vân,
    phân vân là hỏng kỷ luật. Đọc đa khung là việc của MẮT Kevin.
    Cổng quyết định của máy nằm ở k23_quet.cong_mo_hinh() — dùng KHUNG_MAY = ("1h",).

    Ai quyết định con sóng — TƯƠNG ĐỐI với khung mình chọn đánh, không phải
    giải vô địch toàn bảng.

    b10: "nếu em chơi ở khung thời gian nào thì em chỉ cần để ý sự đồng thuận của
          khung LỚN HƠN LIỀN KỀ và sự ủng hộ của những khung NHỎ HƠN."
    b24: "mô hình của khung nào thì nó sẽ quyết định xu hướng bằng khung đấy."
    b3·b20: khung hết lực -> vào sideway -> NHƯỜNG quyền cho khung sát sườn.
    b23: khung nhỏ chỉ THỂ HIỆN lực, không bao giờ quyết định.

    ⚠️ SỬA 09/09 lần 2. Bản trước vẫn max(manh) rồi tuyên bố "X nắm quyền" —
       Kevin: "bốc zô đâu là sai". Bốc theo lực không phải luật của thầy.
    """
    if tf_choi in co_mo_hinh:
        return tf_choi, f"{tf_choi.upper()} tự quyết định — chính nó CÓ mô hình (b24)"
    # khung đó chưa có mô hình -> ai đang cầm? xét SÁT SƯỜN theo b7
    lan_can = LAN_CAN.get(tf_choi, ())
    co = [t for t in lan_can if t in co_mo_hinh]
    if co:
        t = co[0]
        return t, (f"{tf_choi.upper()} chưa có mô hình → quyền đang ở {t.upper()} "
                   f"(sát sườn, b7 tịnh tiến)")
    l = (bang.get(tf_choi) or {}).get("manh") or 0
    return None, (f"{tf_choi.upper()} và khung sát sườn ({', '.join(t.upper() for t in lan_can)}) "
                  f"đều KHÔNG có mô hình → chưa ai cầm quyền, đứng ngoài "
                  f"(nguyên tắc 1) · lực {tf_choi.upper()} {l:.0f}/100")


# b7 tịnh tiến — khung SÁT SƯỜN, xếp theo thứ tự ưu tiên hỏi
LAN_CAN = {"5m": ("15m", "30m"), "15m": ("30m", "1h"), "30m": ("1h", "2h"),
           "1h": ("2h", "4h"), "2h": ("4h", "1h"), "3h": ("4h", "2h"),
           "4h": ("12h", "1d"), "12h": ("1d", "4h"), "1d": ("2d", "12h"),
           "2d": ("3d", "1d"), "3d": ("1w", "2d"), "1w": ("3d",)}
KHUNG_KHONG_QUYEN = ("1m", "5m", "15m")



# ══════════════════ K3 + K4 · MÔ HÌNH ĐẸP + BẬC ══════════════════
def cham_bac(a, khung_lon_dong_pha):
    """BẬC 1/2/3 — chép thẳng b8, buổi thầy dạy riêng về mô hình đẹp/xấu (note 62).

    TRƯỜNG HỢP 1 — CÓ LỰC LIÊN QUAN ("lực bảo hộ"):
      "trước đó thị trường có con sóng tăng và nó TẠO RA QUÁN TÍNH TĂNG. Sau đó quán
       tính tăng này đi vào quá trình điều chỉnh... con sóng trước có quán tính tăng ->
       lực mua rất mạnh và nó liên quan BẢO CHỨNG cho mô hình phía sau -> mô hình xác
       suất khả năng xảy ra RẤT CAO."
      Ngưỡng: "không điều chỉnh quá 50% con sóng trước đó" -> "rất là đẹp".

    BIẾN THỂ 1b — sóng trước KHÔNG quán tính, vẫn đẹp nếu đủ HAI điều:
      "thứ nhất là khung thời gian LỚN HƠN vẫn phải ĐỒNG PHA cho cái xu hướng tăng đó.
       Thứ hai là trong quá trình điều chỉnh, giá không điều chỉnh quá sâu dưới Fibo 0.5
       — thì lúc này cái mô hình nó VẪN ĐẸP."

    TRƯỜNG HỢP 2 — KHÔNG CÓ LỰC LIÊN QUAN:
      "trước đó nó là KHU VỰC SIDEWAY và KHÔNG CÓ MỘT CÁI MÔ HÌNH GÌ CẢ... nếu nó đi
       xuống thì đây nó là một sự tích lũy lực bán ĐƠN THUẦN."
      + b38 43:54 bậc 3: che sóng trước đi mà cung nằm trong 40-60, khung lớn sideway
        -> "mô hình đó mình KHÔNG BAO GIỜ ĐỤNG ĐẾN rồi".

    BẮT BUỘC cho CẢ HAI (b7 30:16 · note 62 mục 3):
      RSI phải CHẠM 70/30 trong QUÁ TRÌNH CUNG — "lên đến 70 là đã có sự gia tăng lực
      mua tốt rồi". Không chạm -> "những mô hình nằm trong khu vực đó nó không hề mạnh".

    ⚠️ 12/09 — GỠ HAI THỨ MÌNH TỰ THÊM, không có trong bài thầy:
      · "cú A cùng chiều mô hình" (lien_quan) — thầy phân TH1/TH2 bằng SÓNG TRƯỚC CÓ
        QUÁN TÍNH HAY KHÔNG, không bằng chiều.
      · "hồi > 100% thì rơi sang TH2" — số mình suy ra, thầy không nói.
    """
    if not a:
        return None, "chưa dựng được cú A"

    # ── BẮT BUỘC: RSI chạm 70/30 TRONG CUNG ──
    if not a.get("cham_cung"):
        return 3, (f"bậc 3 — RSI trong cung chỉ tới {a.get('cuc_cung')}, chưa chạm 70/30: "
                   f'"trong cả quá trình có sự gia tăng lực mua lực bán gì không? KHÔNG CÓ" (b7 30:16)')

    hoi = a.get("hoi")
    sau = hoi is not None and hoi > HOI_TOI_DA

    # ── TH1: sóng trước CÓ QUÁN TÍNH -> có lực bảo hộ ──
    if a.get("quan_tinh"):
        if sau:
            return 3, (f"bậc 3 — sóng trước có quán tính (RSI {a['rsi_cuc']}) nhưng đã điều chỉnh "
                       f"{hoi}% > {HOI_TOI_DA:.0f}% con sóng đó — lực bảo hộ mất (b8 18:12)")
        return 1, (f"BẬC 1 — TH1 có LỰC BẢO HỘ: sóng trước có QUÁN TÍNH (RSI {a['rsi_cuc']}), "
                   f"điều chỉnh {hoi}% ≤ {HOI_TOI_DA:.0f}% — \"rất là đẹp\" (b8 18:12)")

    # ── Biến thể 1b: không quán tính, nhưng khung lớn ĐỒNG PHA và không thủng 0.5 ──
    if khung_lon_dong_pha is True:
        if sau:
            return 3, (f"bậc 3 — sóng trước không quán tính (RSI {a['rsi_cuc']}) VÀ đã điều chỉnh "
                       f"{hoi}% > {HOI_TOI_DA:.0f}% (thủng fibo 0.5) — b8 biến thể 1b đòi cả hai")
        return 2, (f"BẬC 2 — sóng trước không quán tính (RSI {a['rsi_cuc']}) nhưng khung lớn "
                   f"ĐỒNG PHA và điều chỉnh {hoi}% ≤ {HOI_TOI_DA:.0f}% — \"vẫn đẹp\" (b8 44:31)")

    if khung_lon_dong_pha is False:
        return 3, (f"bậc 3 — sóng trước không quán tính (RSI {a['rsi_cuc']}) VÀ khung lớn "
                   f"NGƯỢC PHA: tích lũy lực ĐƠN THUẦN, không có lực bảo hộ (b8 TH2)")

    # chưa biết khung lớn -> KHÔNG suy ra, để mắt Kevin chốt
    if sau:
        return 3, (f"bậc 3 — sóng trước không quán tính (RSI {a['rsi_cuc']}) VÀ điều chỉnh "
                   f"{hoi}% > {HOI_TOI_DA:.0f}% (thủng fibo 0.5) — b8 biến thể 1b đòi cả hai")
    return 2, (f"BẬC 2 tạm — sóng trước không quán tính (RSI {a['rsi_cuc']}), điều chỉnh {hoi}%. "
               f"b8 biến thể 1b đòi KHUNG LỚN ĐỒNG PHA mới đẹp — chưa đọc được khung lớn")


# ══════════════════ K6 · SÓNG HỒI = VÒNG CUNG khung vào ══════════════════
def test_hai_ma(bars, rsi_len=14):
    """RSI ĐÃ TEST LẠI HAI ĐƯỜNG TRUNG BÌNH chưa — vùng vào thứ hai, song song với fibo.

    Thầy nói thẳng "test lại HAI ĐƯỜNG trung bình", nhắc ở BA buổi:
      b15  "RSI giảm và quay lại hai đường trung bình"
      b18  "test lại hai đường trung bình thì lúc đó anh em vào đây thì đánh nó
            CHẮC THẮNG hơn rất nhiều là bọn cứ cố đi tìm v..."
      b43  "test lại hai đường trung bình. Thì đây là cái thời điểm mà chúng ta
            quan sát xem có mua được không"

    ⚠️ KHÔNG đặt ngưỡng "sát bao nhiêu" — thầy không cho số nào. Thước là chính
    DẢI GIỮA hai đường: RSI lọt vào khoảng [min(EMA9,WMA45), max(EMA9,WMA45)]
    thì coi như đã về test. Hết chỗ bịa số.

    Vì sao cần: Kevin 17/09 — "báo có mô hình và chờ hồi về vùng test, thứ nhất là
    RSI test EMA9 hoặc fibo 0.6 đến 0.5 để vào lệnh". Fibo đo trên GIÁ, cái này đo
    trên RSI — hai thước cho cùng một câu "đã hồi đủ chưa", cái nào chạm trước thì báo.

    Trả None nếu thiếu dữ liệu. Dạng BÀY — KHÔNG phải cổng chặn.
    """
    c = [x[4] for x in bars]
    r = K.rsi(c, rsi_len)
    if not r or r[-1] is None:
        return None
    e, w = K._ema(r, 9), K._wma(r, 45)
    if e[-1] is None or w[-1] is None:
        return None
    lo, hi = min(e[-1], w[-1]), max(e[-1], w[-1])
    cham = lo <= r[-1] <= hi
    if cham:
        txt = f"RSI {r[-1]:.1f} ĐÃ về giữa hai MA ({lo:.1f}–{hi:.1f}) — đã test"
    else:
        xa = (r[-1] - hi) if r[-1] > hi else (lo - r[-1])
        txt = (f"RSI {r[-1]:.1f} còn cách dải hai MA ({lo:.1f}–{hi:.1f}) {xa:.1f} điểm"
               f" — CHƯA test lại")
    # `tren_wma` — RSI còn ở PHÍA TRÊN WMA45 hay đã thủng xuống. Cần cho cửa vào
    # thứ hai (Kevin 22/09): "RSI cắt lên một đoạn, sau đó về RETEST TRÊN WMA45".
    return {"cham": cham, "rsi": round(r[-1], 1), "ema": round(e[-1], 1),
            "wma": round(w[-1], 1), "lo": round(lo, 1), "hi": round(hi, 1),
            "tren_wma": r[-1] >= w[-1], "ket_luan": txt}


def song_hoi(bars_entry, chieu_mo_hinh, rsi_len=14):
    """
    Hình b11 1:13:25 — thầy vẽ đường chữ U trên RSI: sóng hồi CÓ HÌNH VÒNG CUNG,
    không đếm nến. "một hai cây nến chạm vào đường trung bình thì KHÔNG gọi là hồi".
    Sóng hồi kết thúc = cung nhỏ ĐÓNG, chiều CÙNG mô hình -> đó là điểm vào (C4 ≡ C2).
    Trả (xong?, mô tả, i_cat) — i_cat = CHỈ SỐ NẾN cung khung vào đóng.

    ⭐ 16/09 — thêm i_cat để CHẶT KHÚC (b9 2:11:19) định danh được từng khúc:
       "đoạn này anh ăn một lệnh, đoạn này anh ăn một lệnh, đoạn này anh ăn một
       lệnh". Mỗi khúc = MỘT lần cắt C riêng trên khung vào. Không có mốc này thì
       bot không phân biệt được "khúc mới" với "vẫn khúc cũ" -> bắn trùng.
    """
    # ⚙️ GỘP 13/09 — cung khung VÀO cũng lấy từ vong_cung(), không dùng bản cài khác.
    # ⚠️ Khung vào chỉ cần CÓ vòng cung CÙNG CHIỀU, KHÔNG cần đủ X/Y (Kevin 13/09:
    #    "M5 chỉ cần có mô hình đồng thuận, không cần giống").
    cl = [x[4] for x in bars_entry]
    r = K.rsi(cl, rsi_len); f = K._ema(r, 9); s_ = K._wma(r, 45)
    mc = cac_muc_cat(f, s_)
    if len(mc) < 2:
        return False, "sóng hồi CHƯA xong — khung vào chưa đủ hai lần cắt", None
    (i0, m0), (i1, m1) = mc[-2], mc[-1]
    # chiều đọc từ EMA so với WMA TRONG cung (b15 1:37:30), KHÔNG từ mức cắt
    giua = (i0 + i1) // 2
    if f[giua] is None or s_[giua] is None:
        return False, "khung vào chưa đủ dữ liệu", None
    ch = 1 if f[giua] < s_[giua] else -1
    if ch != chieu_mo_hinh:
        return False, "cung khung vào NGƯỢC chiều mô hình — chưa phải điểm vào", None
    tuoi = len(f) - 1 - i1
    return True, (f"sóng hồi XONG — cung khung vào đóng {tuoi} nến trước "
                  f"(mức {m0:.1f} → {m1:.1f})"), i1


# ══════════════════ chấm một coin ══════════════════
def cham(lay_nen, symbol, khung=None):
    """
    lay_nen(symbol, interval, n) -> [(ts,o,h,l,c,vol), ...]
    Trả (text, dict).
    """
    khung = khung or (list(CUM_CONG_TAC) + list(KHUNG_MH) + ["5m"])
    kho, bang, nen = {}, {}, {}
    for tf in khung:
        try:
            b = K.nen_cho_khung(lay_nen, symbol, tf, 400, kho)
            d = K.gan_moc(K.doc_khung([x[4] for x in b]), b, tf)   # PHẢI gắn mốc KC/HT
            if d:
                bang[tf] = d
                nen[tf] = b
        except Exception:
            continue
    if not bang:
        return f"{symbol}: không lấy được dữ liệu", {}

    che_do, ct_txt = cong_tac(bang)

    ket = []
    for tf in KHUNG_MH:
        if tf not in nen:
            continue
        b = nen[tf]
        # ⭐ 13/09 — qua CỔNG DUY NHẤT cong_vao(), bỏ cham_bac (bậc 1/2/3 đã xoá).
        cv = cong_vao(b)
        if not cv.get("co"):
            continue
        a = cu_a([x[4] for x in b], [x[2] for x in b], [x[3] for x in b])
        if a is None:
            continue
        bac, mo_ta = 1, cv["ly_do"]
        if True:
            # sóng hồi = C XÁC NHẬN của chính cung này (b15 1:23:25) — lấy từ cong_vao,
            # KHÔNG gọi song_hoi() trên khung 5m nữa (hai nguồn -> mâu thuẫn trong 1 dòng)
            hoi_xong = cv.get("c_xac_nhan", False)
            hoi_txt = ("C xác nhận XONG — cung đã đóng (EMA9 cắt WMA45 kết thúc điều chỉnh)"
                       if hoi_xong else "chưa có C xác nhận")
            ket.append((bac, tf, a, mo_ta, hoi_xong, hoi_txt))
    ket.sort(key=lambda x: (0 if x[4] else 1, x[0], KHUNG_MH.index(x[1])))

    # K3b — tương quan trên khung 5m (khung vào lệnh)
    tq = None
    if "5m" in nen:
        b5 = nen["5m"]
        cl5 = [x[4] for x in b5]
        vo5 = [x[5] if len(x) > 5 else 0 for x in b5]
        tq = T.do_tuong_quan(cl5, K.rsi(cl5, 14), vo5 if any(vo5) else None)

    icon = {"KY_VONG": "🟢", "CAN_TRONG": "🔴", "CHUA_RO": "⚪"}.get(che_do, "⚪")
    d = ["═" * 60, f"  {symbol}  ·  RULE v7", "═" * 60,
         f"⚡ CÔNG TẮC   {icon} {che_do or '—'} · {ct_txt}"]
    if che_do == "KY_VONG":
        d.append("   → chỉ MUA và CHỜ MUA (hoặc bán một chiều) · target khung mô hình")
    elif che_do == "CAN_TRONG":
        d.append("   → KHÔNG ăn lệnh dài · nhặt 3-6% · hai chiều · CHỐT NON")

    if not ket:
        d.append("⚖️ MÔ HÌNH   — chưa khung nào qua bậc 1/2 (quy luật 1: không có thì THÔI)")
    else:
        for bac, tf, a, mo_ta, hoi_xong, hoi_txt in ket[:3]:
            d.append(f"⚖️ MÔ HÌNH   {'①' if bac == 1 else '②'} {tf.upper()} · {mo_ta}")
            d.append(f"   cú A {a['dau']:.6g} → {a['dinh']:.6g} ({a['bien_pct']:+.1f}%)"
                     f" · {a['so_nen']} nến · cung đóng {a['tuoi_cung']} nến trước")
            d.append(f"   VÙNG VÀO {a['f05']:.6g}–{a['f618']:.6g}  ·  SL 0.7 {a['f70']:.6g}"
                     if a.get("f05") is not None else
                     "   🔵 cú A ngược chiều cung — chưa có vùng vào (b12 1:27:51)")
            d.append(f"   {'✅' if hoi_xong else '⏳'} {hoi_txt}")
    if tq:
        d.append(f"📊 {T.dong_bay(tq)}")
    d.append("👁 mắt chốt: nhìn phát có thấy đẹp ngay không? lăn tăn thì BỎ (b8 21:00)")
    return "\n".join(d), {"che_do": che_do, "cong_tac": ct_txt,
                          "mo_hinh": [(b, t, h) for b, t, _, _, h, _ in ket], "tuong_quan": tq}
