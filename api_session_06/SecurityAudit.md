# 5 nguy cơ rò rỉ bảo mật
1. Lỗ hổng BOLA (Broken Object Level Authorization - OWASP API1): Khi người dùng xem bài viết riêng tư của người khác bằng cách đổi ID bài viết trên URL nếu hệ thống chỉ kiểm tra đăng nhập mà bỏ qua bước kiểm tra quyền sở hữu bài viết.
2. Lưu trữ Token ở localStorage phía Client: Dễ bị tấn công XSS đánh cắp Token. Đề xuất chuyển sang dùng Cookie HttpOnly, Secure, SameSite hoặc mô hình BFF.
3. Thiếu cơ chế Rate Limiting tại /auth/login: Dễ bị tấn công Credential Stuffing / Brute Force dò mật khẩu liên tục.
4. Đưa thông tin nhạy cảm (PII) vào Payload của JWT: Payload của JWT chỉ được mã hóa Base64URL nên ai có token cũng có thể giải mã và đọc được plaintext (không đặt mật khẩu hay dữ liệu cá nhân vào JWT).
5. Chấp nhận thuật toán alg=none hoặc nhầm lẫn thuật toán (Algorithm Confusion HS ↔ RS): Kẻ tấn công có thể chỉnh sửa payload và bỏ qua kiểm tra chữ ký nếu server không thiết lập allowlist thuật toán mã hóa cố định.