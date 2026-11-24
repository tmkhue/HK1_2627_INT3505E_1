import uuid
from datetime import datetime, timezone

def v1_create_order(body):
    account_id = body.get("account_id", "unknown")
    item = body.get("item", "Sản phẩm mẫu")
    quantity = body.get("quantity", 1)
    
    return {
        "order_id": f"ORD-V1-{uuid.uuid4().hex[:6]}",
        "account_id": account_id,
        "item_name": item,
        "qty": quantity,
        "status": "SUCCESS",
        "version": "v1"
    }

def v2_create_order(body):
    account_id = body.get("account_id", "unknown")
    
    items = body.get("items")
    if not items:
        items = [{"name": body.get("item", "Sản phẩm mẫu"), "quantity": body.get("quantity", 1)}]
    
    return {
        "id": f"ORD-V2-{uuid.uuid4().hex[:8]}",
        "account_id": account_id,
        "items": items,
        "currency": body.get("currency", "VND"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "CREATED",
        "version": "v2"
    }