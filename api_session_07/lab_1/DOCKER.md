# Chạy Product API bằng Docker Compose

## Yêu cầu

- Cài Docker Desktop (Windows/macOS) hoặc Docker Engine và Docker Compose plugin (Linux).
- Chuyển thư mục `lab_1` sang máy cần chạy, giữ nguyên `Dockerfile`, `compose.yaml`, `requirements.txt`, `gunicorn.config.py`, `wsgi.py` và thư mục `src`.

## Khởi chạy

Mở terminal tại thư mục `lab_1`, sau đó chạy:

```bash
docker compose up --build -d
```

Lần đầu Docker sẽ tải Python image, cài thư viện và build image. Các lần sau có thể chạy `docker compose up -d`. Không cần tạo `.env` hay chỉnh file cấu hình.

## Truy cập và quản lý

- Swagger UI: <http://localhost:5000/docs/swagger-ui>
- Health check: <http://localhost:5000/healthz>
- Product API: <http://localhost:5000/api/v1/products/>
- Order API: <http://localhost:5000/api/v1/orders/>

Xem trạng thái bằng `docker compose ps` và log bằng `docker compose logs -f product-api`. Dừng service bằng `docker compose down`. Dữ liệu SQLite được giữ trong Docker volume `product-data` qua các lần dừng và khởi chạy lại. Để xóa cả dữ liệu, dùng `docker compose down -v`.

Compose dùng secret mặc định để chạy ngay cho môi trường học tập/local. Trước khi mở service ra mạng công khai, đặt biến môi trường `SECRET_KEY` thành chuỗi bí mật riêng rồi chạy Compose như bình thường.
