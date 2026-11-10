import connexion
import os

# Định vị chính xác thư mục chứa file products.yaml
current_dir = os.path.dirname(os.path.abspath(__file__))
openapi_dir = os.path.join(current_dir, '../openapi')

app = connexion.App(__name__, specification_dir=openapi_dir)
app.add_api('products.yaml')

# Đảm bảo tên hàm viết thường, trùng khớp hoàn toàn với operationId
def get_products():
    return [
        {"productId": "1", "name": "Sản phẩm A", "price": 10.0},
        {"productId": "2", "name": "Sản phẩm B", "price": 20.0},
    ], 200

def create_products(body):
    new_product = {
        "productId": str(len(get_products()[0]) + 1),
        "name": body.get("name"),
        "price": body.get("price"),
    }
    return new_product, 201

def get_product_by_id(productId):
    products = get_products()[0]
    for product in products:
        if product["productId"] == productId:
            return product, 200
    return {"message": "Product not found"}, 404

if __name__ == '__main__':
    app.run(port=8080)
