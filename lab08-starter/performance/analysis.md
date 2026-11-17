# Lab 4 — Phân tích kết quả

| Kịch bản | Users | Spawn rate | Duration | p95 (ms) | Failure rate | RPS |
|---|---:|---:|---:|---:|---:|---:|
| A | 10 | 2 | 30s | 32 | 0% | 4.81 |
| B | 50 | 5 | 60s | 33 | 0.07% | 23.07 |
| C | 200 | 50 | 30s | 110 | 0.07% | 97.28 |

## Trả lời

### 1. Kịch bản có p95 cao nhất

Kịch bản có p95 cao nhất là C vì có 200 users và spawn rate 50 users/giây. 
Flask development server, SQLite và các thao tác ghi từ `POST /books` có thể tạo queueing/contention, khiến p95 tăng phi tuyến sau khi máy bắt đầu bão hòa.

### 2. Failure rate theo số user

Task `search_by_year` có chủ ý đánh dấu khoảng 1% request là failed bằng `response.failure("Injected simulated HTTP 500")`. Đây là lỗi phía Locust để mô phỏng sự cố, không phải HTTP 500 thật do Flask trả về. Khi so sánh A, B, C, chỉ kết luận có lỗi tăng theo tải nếu status code hoặc lỗi thực tế trong HTML/log Flask cũng tăng.

Các nguyên nhân có thể kiểm tra trong code là Flask development server, SQLite contention khi tạo sách và việc các request phải chờ xử lý tuần tự.

### 3. SLO p95 < 300 ms

Tất cả kịch bản đạt SLO nếu p95 đo được trong HTML nhỏ hơn 300 ms. Nên dùng A làm CI gate vì ngắn, nhẹ và lặp lại được. CI có thể fail khi p95 của A >= 300 ms hoặc failure rate vượt ngưỡng đã thống nhất. B và C phù hợp chạy định kỳ, không nên dùng làm gate cho mọi commit.


### 4. Bonus: connection pool giới hạn 5

Khi 200 users đồng thời nhưng pool chỉ có 5 connection, các request vượt quá 5 có thể phải chờ; nếu vượt `pool_timeout`, chúng có thể lỗi timeout. Để xác nhận, so sánh p95/failure rate của C với A, kiểm tra status/error trong HTML và log Flask/SQLAlchemy. Nếu độ trễ và lỗi tăng rõ khi concurrency vượt 5, đó là bằng chứng phù hợp với giả thuyết pool bị nghẽn.