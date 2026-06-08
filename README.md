# 💎 Hidden Gem Hunter

Web app phân tích tiềm năng token micro-cap crypto.

## Cài đặt

```bash
pip install streamlit requests pandas plotly
```

## Chạy app

```bash
cd gem_hunter
streamlit run app.py
```

Mở trình duyệt: http://localhost:8501

## Tính năng

- 🔍 Tìm kiếm token theo tên/symbol
- 📊 Chấm điểm tiềm năng 0-100 theo 6 tiêu chí:
  - Market Cap (25đ) — ưu tiên < $1M
  - FDV/Mcap Ratio (20đ) — tokenomics dilution risk
  - Circulating Supply % (20đ) — supply thấp = dễ pump
  - Volume/Mcap (15đ) — liquidity & trading activity
  - ATH Distance (10đ) — còn room recover không
  - Community size (10đ) — chưa mainstream = còn early
- 🚦 Tín hiệu xanh/vàng/đỏ chi tiết
- 🔥 Trending coins hôm nay
- 💎 Danh sách micro-cap ($100K–$5M) đáng chú ý

## Grading

| Grade | Score | Ý nghĩa |
|-------|-------|---------|
| S | 80-100 | Tiềm năng CỰC CAO |
| A | 65-79 | Tiềm năng CAO |
| B | 50-64 | Tiềm năng TRUNG BÌNH |
| C | 35-49 | Tiềm năng THẤP |
| D | 0-34 | Nguy hiểm |

## Lưu ý

- Data từ CoinGecko API (free, giới hạn 30 req/phút)
- Nếu bị rate limit: chờ 60s rồi thử lại
- KHÔNG phải lời khuyên đầu tư
