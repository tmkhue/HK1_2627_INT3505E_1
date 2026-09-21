# 5 endpoint của GitHub REST API
Method, status code, headers, có RESTful không
***
## 1. Liệt kê các project trong tổ chức
*/orgs/{org}/projectsV2*

Liệt kế tất cả project sở hữu bời 1 tổ chức và cấp quyền truy cập cho người dùng được xác thực

| Method | Status code | Headers | RESTful |
| :---: | :---: | :---: | :---: |
| GET | 200, 304, 401, 403 | Accept, X-GitHub-Api-Version | Có |

***
## 2. Lấy 1 project trong tổ chức
*/orgs/{org}/projectsV2/{project_number}*

Lấy 1 project cụ thể được sở hữu bởi tổ chức

| Method | Status code | Headers | RESTful |
| :---: | :---: | :---: | :---: |
| GET | 200, 304, 401, 403 | Accept, Authorization, X-GitHub-Api-Version | Có |

## 3. Liệt kê các project cho user
*/users/{username}/projectsV2*

Liệt kê hết các project sở hữu bởi user được xác thực có quyền truy cập đến

| Method | Status code | Headers | RESTful |
| :---: | :---: | :---: | :---: |
| GET | 200, 304, 401, 403 | Accept, Authorization, X-GitHub-Api-Version | Có |

## 4. Lấy 1 project của 1 user
*/users/{username}/projectsV2/{project_number}*

Lấy 1 project cụ thể được sở hữu bởi 1 user

| Method | Status code | Headers | RESTful |
| :---: | :---: | :---: | :---: |
| GET | 200, 304, 401, 403 | Accept, Authorization, X-GitHub-Api-Version | Có |

## 5. Liệt kê các vấn đề được giao cho user được xác thực
*/issues*

Liệt kê các vấn đề được giao cho user được xác thực qua tất cả các repo được truy cập bao gồm cả cá nhân, nhóm và tổ chức

| Method | Status code | Headers | RESTful |
| :---: | :---: | :---: | :---: |
| GET | 200, 304, 401, 422 | Accept,  X-GitHub-Api-Version | Có |