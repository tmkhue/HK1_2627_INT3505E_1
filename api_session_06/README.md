# BTVN Week 6
## API social-network
Chạy thử endpoint đăng nhập
Đăng nhập và lấy token
![alt text](image.png)
Lấy post bằng access token vừa nhận
![alt text](image-1.png)
Gửi JSON sai cú pháp
![alt text](image-2.png)
Gọi bài viết mà không gửi token
![alt text](image-3.png)
Bài viết không tồn tại
![alt text](image-4.png)
## Các scope, lỗi, status code trong endpoint
| Endpoint | Scope | Lỗi có thể xảy ra | Status Code |
| --- | --- | --- | --- |
| POST /auth/login | Không cần Scope (security: [] - Public Endpoint) | - Cú pháp JSON hỏng - Sai thông tin đăng nhập - Đăng nhập quá nhiều lần | - 200 OK: Thành công - 400 Bad Request: Lỗi cú pháp JSON - 401 Unauthorized: Sai thông tin - 422 Unprocessable: Lỗi validation dữ liệu - 429 Too Many Requests: Bị chặn do rate limit - 500 Internal Error: Lỗi hệ thống |
| POST /auth/refresh | Cần Refresh Token hợp lệ | - Thiếu hoặc gửi Token sai định dạng - Refresh Token đã hết hạn hoặc bị thu hồi (đã logout) | - 200 OK: Cấp Access Token mới thành công - 401 Unauthorized: Token hết hạn/sai chữ ký - 403 Forbidden: Token bị thu hồi - 500 Internal Error: Lỗi máy chủ |
| GET /posts/{id} | Yêu cầu Scope: posts:read trong Access Token | - Thiếu Header Authorization hoặc Access Token hết hạn - Token không chứa scope posts:read - Bài viết chế độ riêng tư và người dùng không có quyền xem (BOLA / API1) - Bài viết không tồn tại | - 200 OK: Trả về chi tiết bài viết - 401 Unauthorized: Chưa xác thực / token hết hạn - 403 Forbidden: Thiếu scope hoặc bị từ chối do vi phạm BOLA - 404 Not Found: Bài viết không tồn tại - 500 Internal Error: Lỗi máy chủ |