# BTVN Tuần 3:
## Lab 1
1. Xác định các resource trong miền
- 'posts': /users/[id]/posts
- 'comments': /posts/[pid]/comments
- 'tags': /posts/[pid]/tags
- 'profile': /users/[id]/profile
- 'follow': /users/[id]/following

2. Phân loại collection/item/sub-resource
- collection: 
    * /users
    * /posts
- item:
    * /users/[id]
    * /posts/[pid]
    * /comments/[cid]
    * /tags/[tag_name]
- sub-resources:
    * /users/[id]/profile
    * /users/[id]/following
    * /users/[id]/followers
    * /users/[id]/posts
    * /posts/[pid]/tags
    * /posts/[pid]/comments
    * /tags/[tag_name]/posts

3. Vẽ sơ đồ endpoints tree và quyết định version segment
```mermaid
graph TD;
    Users-->Posts;
    Users-->Profile
    Users-->Followers
    Users-->Following
    Posts-->Comments
    Posts-->Tags
```
4. Triển khai Flask routes cho collection /posts
- GET /users
![alt text](image.png)
- POST /users
![alt text](image-1.png)
- GET /posts
![alt text](image-2.png)
- POST /posts
![alt text](image-3.png)
- GET /users/[id]
![alt text](image-4.png)
- PUT /posts/[pid]
![alt text](image-5.png)
- DELETE /users/[id]
![alt text](image-6.png)
- GET /posts/[pid]
![alt text](image-7.png)
- GET /tags/[tag_name]/posts
![alt text](image-8.png)
- POST /users/[id]/following
![alt text](image-9.png)

## Lab 2
- Error handler
    * GET /users/[id] với id không hợp lệ
![alt text](image-10.png)
    * POST /users với content không hợp lệ
![alt text](image-11.png)