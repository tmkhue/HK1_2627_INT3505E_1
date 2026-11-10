from src.factory import create_app
from src.extensions import db
from src.models.products import Product

PRODUCTS = [
    ("ALB-001", "Album Bloom", 1000000, 50, "Special edition album"),
    ("ALB-002", "Album Aurora", 950000, 35, "Photobook included"),
    ("ALB-003", "Album Eclipse", 1100000, 28, "Limited edition"),
    ("ALB-004", "Album Harmony", 890000, 42, "Standard edition"),
    ("ALB-005", "Album Starlight", 1050000, 31, "Poster included"),
    ("MER-001", "Miyeon Photocard Set", 150000, 100, "Set of 5 photocards"),
    ("MER-002", "Miyeon Poster", 120000, 60, "Folded official poster"),
    ("MER-003", "Miyeon Keyring", 180000, 45, "Acrylic keyring"),
    ("MER-004", "Miyeon T-Shirt", 450000, 24, "Cotton fan shirt"),
    ("MER-005", "Miyeon Lightstick", 850000, 18, "Official lightstick"),
    ("ACC-001", "Album Sleeve", 50000, 150, "Protective sleeve"),
    ("ACC-002", "Photocard Binder", 220000, 70, "Holds  binder pages"),
    ("ACC-003", "Photo Frame", 90000, 80, "Clear display frame"),
    ("ACC-004", "Mini Photo Book", 175000, 55, "Pocket-sized photo book"),
    ("ACC-005", "Decorative Sticker Pack", 65000, 90, "Official sticker pack"),
    ("GFT-001", "Fan Gift Box", 320000, 20, "Gift box with mixed items"),
    ("GFT-002", "Concert Slogan", 130000, 40, "Fabric concert slogan"),
    ("GFT-003", "Collectible Badge", 70000, 75, "Enamel badge"),
    ("GFT-004", "Desk Calendar", 260000, 33, "2026 desk calendar"),
    ("GFT-005", "Mini Album Stand", 80000, 65, "Acrylic display stand"),
]

def main():
    app = create_app()
    with app.app_context():
        added = 0
        updated = 0
        for sku, name, price_cents, qty, description in PRODUCTS:
            product = db.session.scalar(
                db.select(Product).where(Product.sku == sku)
            )
            if product is None:
                product = Product(sku=sku)
                db.session.add(product)
                added += 1
            else:
                updated += 1

            product.name = name
            product.price_cents = price_cents
            product.qty_in_stock = qty
            product.description = description
            product.archived = False

        db.session.commit()
        print(f"Added {added} products and updated {updated} products.")


if __name__ == "__main__":
    main()
