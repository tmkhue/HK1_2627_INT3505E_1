# Kết quả chạy Week 1
## Bài 1: Hello API
![alt text](image/image.png)

## Bài 2:
![alt text](image/image-1.png)

## Bài 3:
![alt text](image/image-2.png)

## Bài 4:
C:\Users\Minh Khuê>curl -i http://127.0.0.1:5000/students/1
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.14.2
Date: Fri, 11 Sep 2026 18:16:32 GMT
Content-Type: application/json
Content-Length: 55
Connection: close

{
  "gpa": 4.0,
  "id": "1",
  "name": "Tran Minh A"
}

C:\Users\Minh Khuê>curl -i "http://127.0.0.1:5000/students?gpa=3.6&name=a"
HTTP/1.1 200 OK
Server: Werkzeug/3.1.8 Python/3.14.2
Date: Fri, 11 Sep 2026 18:19:57 GMT
Content-Type: application/json
Content-Length: 174
Connection: close

{
  "students": [
    {
      "gpa": 4.0,
      "id": "1",
      "name": "Tran Minh A"
    },
    {
      "gpa": 3.8,
      "id": "4",
      "name": "Pham Van D"
    }
  ]
}