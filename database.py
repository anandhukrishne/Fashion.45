import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "products.db"


def get_connection():
    """Returns an active SQLite connection enforcing foreign keys."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Initializes tables and seeds initial data if empty."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS categories (\n        category_id INTEGER PRIMARY KEY AUTOINCREMENT,\n        name TEXT NOT NULL UNIQUE\n    );\n\n    CREATE TABLE IF NOT EXISTS products (\n        product_id INTEGER PRIMARY KEY AUTOINCREMENT,\n        name TEXT NOT NULL,\n        category_id INTEGER NOT NULL,\n        price REAL NOT NULL,\n        stock INTEGER NOT NULL,\n        image_url TEXT DEFAULT '',\n        FOREIGN KEY (category_id) REFERENCES categories(category_id)\n    );\n\n    CREATE TABLE IF NOT EXISTS orders (\n        order_id INTEGER PRIMARY KEY AUTOINCREMENT,\n        customer_name TEXT NOT NULL,\n        order_date DATE NOT NULL,\n        total_amount REAL DEFAULT 0\n    );\n\n    CREATE TABLE IF NOT EXISTS order_items (\n        item_id INTEGER PRIMARY KEY AUTOINCREMENT,\n        order_id INTEGER NOT NULL,\n        product_id INTEGER NOT NULL,\n        quantity INTEGER NOT NULL,\n        unit_price REAL NOT NULL,\n        FOREIGN KEY (order_id) REFERENCES orders(order_id),\n        FOREIGN KEY (product_id) REFERENCES products(product_id)\n    );\n    """)
    conn.commit()

    # Migration check: ensure image_url exists on products
    cur.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cur.fetchall()]
    if "image_url" not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN image_url TEXT DEFAULT ''")
        conn.commit()

    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        seed_baseline(conn)
    else:
        # If products exist but image_url is empty, populate curated image URLs
        cur.execute("SELECT product_id, image_url FROM products")
        rows = cur.fetchall()
        curated_images = {
            1: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=300&q=80",
            2: "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=300&q=80",
            3: "https://images.unsplash.com/photo-1542272604-787c3835535d?w=300&q=80",
            4: "https://images.unsplash.com/photo-1603808033192-082d6919d3e1?w=300&q=80",
            5: "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=300&q=80",
            6: "https://images.unsplash.com/photo-1544816155-12df9643f363?w=300&q=80",
            7: "https://images.unsplash.com/photo-1627123424574-724758594e93?w=300&q=80",
            8: "https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=300&q=80",
            9: "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300&q=80",
            10: "https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?w=300&q=80"
        }
        for r in rows:
            if not r["image_url"] and r["product_id"] in curated_images:
                cur.execute("UPDATE products SET image_url = ? WHERE product_id = ?",
                            (curated_images[r["product_id"]], r["product_id"]))
        conn.commit()

    conn.close()


def seed_baseline(conn):
    random.seed(42)
    cur = conn.cursor()

    # 1. Categories
    categories = ['Streetwear', 'Footwear', 'Accessories', 'Stationery']
    for cat in categories:
        cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

    # 2. Products with curated CDN images
    catalog = [
        ('Matiks 50 day streak official Tee-xclusive offer', 1, 899.00, 10,
         'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=300&q=80'),
        ('Matiks 200 day streak official Hoodie', 1, 2499.99, 6,
         'https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=300&q=80'),
        ('Baggy Denim-Being Mallu series', 1, 2499.00, 40,
         'https://images.unsplash.com/photo-1542272604-787c3835535d?w=300&q=80'),
        ('Indian traditional Paduka-Being Indian series', 2, 299.00, 50,
         'https://images.unsplash.com/photo-1603808033192-082d6919d3e1?w=300&q=80'),
        ('#Just_Sandles Sandles', 2, 799.00, 75,
         'https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=300&q=80'),
        ('Indian Unisex Jholla-Being Indian series', 3, 99.00, 120,
         'https://images.unsplash.com/photo-1544816155-12df9643f363?w=300&q=80'),
        ('#Just_Hold_My_Cards Cardholder', 3, 49.00, 150,
         'https://images.unsplash.com/photo-1627123424574-724758594e93?w=300&q=80'),
        ('Keychain.45', 3, 24.99, 200,
         'https://images.unsplash.com/photo-1614064641938-3bbee52942c7?w=300&q=80'),
        ('SPIDERMAN series books.45 A4 10 Notebook set', 4, 299.00, 100,
         'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300&q=80'),
        ('#Just_Write 0.7 BallPoint Pen-set of 10 pens', 4, 99.00, 80,
         'https://images.unsplash.com/photo-1583485088034-697b5bc54ccd?w=300&q=80'),
    ]
    cur.executemany(
        "INSERT INTO products (name, category_id, price, stock, image_url) VALUES (?, ?, ?, ?, ?)",
        catalog
    )

    names = ['Aanvi', 'Divya', 'Rohit', 'Ananya', 'VijayKumar', 'Lino', 'Aadish', 'Maheswarrr']
    base_date = datetime(2026, 1, 1)

    for order_id in range(1, 51):
        cust = random.choice(names)
        order_date = base_date + timedelta(days=random.randint(1, 180))
        cur.execute("INSERT INTO orders (customer_name, order_date, total_amount) VALUES (?, ?, 0)",
                    (cust, order_date.strftime("%Y-%m-%d")))

        picked_ids = random.sample(range(1, len(catalog) + 1), k=random.choice([2, 3]))
        order_total = 0.0

        for pid in picked_ids:
            cur.execute("SELECT price FROM products WHERE product_id = ?", (pid,))
            price = cur.fetchone()[0]
            cur.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, 1, ?)",
                        (order_id, pid, price))
            order_total += price

        cur.execute("UPDATE orders SET total_amount = ? WHERE order_id = ?", (round(order_total, 2), order_id))

    conn.commit()
    print("[+] Database initialized with image support and 50 seeded relational transactions.")


if __name__ == "__main__":
    init_db()
