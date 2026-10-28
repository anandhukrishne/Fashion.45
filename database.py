import sqlite3
import random
import requests
from datetime import datetime, timedelta

DB_NAME = "products.db"
FAKESTORE_API_URL = "https://fakestoreapi.com/products"

# Fallback catalog in case offline or API unavailable
FALLBACK_CATALOG = [
    ("Fjallraven - Foldsack No. 1 Backpack, Fits 15 Laptops", 1, 109.95, 45,
     "https://fakestoreapi.com/img/81fPKd-2AYL._AC_SL1500_t.png"),
    ("Mens Casual Premium Slim Fit T-Shirts", 1, 22.30, 60,
     "https://fakestoreapi.com/img/71-3HjGNDUL._AC_SY879._SX._UX._SY._UY_t.png"),
    ("Mens Cotton Jacket", 1, 55.99, 35,
     "https://fakestoreapi.com/img/71li-ujtlUL._AC_UX679_t.png"),
    ("Mens Casual Slim Fit", 1, 15.99, 80,
     "https://fakestoreapi.com/img/71YXzeOuslL._AC_UY879_t.png"),
    ("John Hardy Women's Legends Naga Gold & Silver Dragon Station Chain Bracelet", 2, 695.00, 20,
     "https://fakestoreapi.com/img/71pWzhdJNwL._AC_UL640_QL65_ML3_t.png"),
    ("Solid Gold Petite Micropave", 2, 168.00, 30,
     "https://fakestoreapi.com/img/61sbMiUnoGL._AC_UL640_QL65_ML3_t.png"),
    ("White Gold Plated Princess", 2, 9.99, 90,
     "https://fakestoreapi.com/img/71YAIFU48IL._AC_UL640_QL65_ML3_t.png"),
    ("Pierced Owl Rose Gold Plated Stainless Steel Double", 2, 10.99, 110,
     "https://fakestoreapi.com/img/51UDEzMJVpL._AC_UL640_QL65_ML3_t.png"),
    ("WD 2TB Elements Portable External Hard Drive - USB 3.0", 3, 64.00, 75,
     "https://fakestoreapi.com/img/61IBBVJvSDL._AC_SY879_t.png"),
    ("SanDisk SSD PLUS 1TB Internal SSD - SATA III 6 Gb/s", 3, 109.00, 50,
     "https://fakestoreapi.com/img/61U7T1koQqL._AC_SX679_t.png"),
    ("Silicon Power 256GB SSD 3D NAND A55 SLC Cache Performance Boost SATA III 2.5", 3, 109.00, 65,
     "https://fakestoreapi.com/img/71kWymZ+c+L._AC_SX679_t.png"),
    ("WD 4TB Gaming Drive Works with Playstation 4 Portable External Hard Drive", 3, 114.00, 40,
     "https://fakestoreapi.com/img/61mtL65D4cL._AC_SX679_t.png"),
    ("Acer SB220Q bi 21.5 inches Full HD (1920 x 1080) IPS Ultra-Thin", 3, 599.00, 18,
     "https://fakestoreapi.com/img/81QpkIctqPL._AC_SX679_t.png"),
    ("Samsung 49-Inch CHG90 144Hz Curved Gaming Monitor", 3, 999.99, 12,
     "https://fakestoreapi.com/img/81Zt42ioCgL._AC_SX679_t.png"),
    ("BIYLACLESEN Women's 3-in-1 Snowboard Jacket Winter Coats", 4, 56.99, 45,
     "https://fakestoreapi.com/img/51Y5NI-I5jL._AC_UX679_t.png"),
    ("Lock and Love Women's Removable Hooded Faux Leather Moto Biker Jacket", 4, 29.95, 70,
     "https://fakestoreapi.com/img/81XH0e8fefL._AC_UY879_t.png"),
    ("Rain Jacket Women Windbreaker Striped Climbing Raincoats", 4, 39.99, 55,
     "https://fakestoreapi.com/img/71HblAHs5xL._AC_UY879_-2t.png"),
    ("MBJ Women's Solid Short Sleeve Boat Neck V", 4, 9.85, 95,
     "https://fakestoreapi.com/img/71z3kpMAYUL._AC_UY879_t.png"),
    ("Opna Women's Short Sleeve Moisture", 4, 7.95, 120,
     "https://fakestoreapi.com/img/51eg55uWmdL._AC_UX679_t.png"),
    ("DANVOUY Womens T Shirt Casual Cotton Short", 4, 12.99, 85,
     "https://fakestoreapi.com/img/61pHAEJ4NML._AC_UX679_t.png")
]


def format_category(cat_str):
    """Formats category string cleanly (e.g., men's clothing -> Men's Clothing)."""
    return cat_str.strip().title().replace("'S", "'s")


def get_connection():
    """Returns an active SQLite connection enforcing foreign keys."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def fetch_fakestore_products():
    """Fetches real e-commerce catalog from online FakeStore API with timeout and error handling."""
    try:
        res = requests.get(FAKESTORE_API_URL, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"[+] Successfully fetched {len(data)} items from online FakeStore API DBMS.")
                return data
    except Exception as e:
        print(f"[!] Warning: FakeStore API unreachable ({e}). Using baseline catalog.")
    return None


def init_db(force_reseed=False):
    """Initializes tables and seeds initial data from online FakeStore API if empty or forced."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS categories (
        category_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL,
        image_url TEXT DEFAULT '',
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        order_date DATE NOT NULL,
        total_amount REAL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS order_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );
    """)
    conn.commit()

    cur.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cur.fetchall()]
    if "image_url" not in columns:
        cur.execute("ALTER TABLE products ADD COLUMN image_url TEXT DEFAULT ''")
        conn.commit()

    cur.execute("SELECT COUNT(*) FROM products")
    prod_count = cur.fetchone()[0]

    if prod_count == 0 or force_reseed:
        seed_baseline(conn)

    conn.close()


def seed_baseline(conn):
    """Seeds database with products fetched from online FakeStore API (or fallback) + 50 orders."""
    random.seed(42)
    cur = conn.cursor()

    # Clear existing data if reseeding
    cur.execute("DELETE FROM order_items")
    cur.execute("DELETE FROM orders")
    cur.execute("DELETE FROM products")
    cur.execute("DELETE FROM categories")
    cur.execute("DELETE FROM sqlite_sequence")
    conn.commit()

    online_data = fetch_fakestore_products()

    if online_data:
        # Group and insert categories
        cat_names = sorted(list(set(format_category(item.get("category", "General")) for item in online_data)))
        for cat in cat_names:
            cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

        cur.execute("SELECT category_id, name FROM categories")
        cat_map = {row["name"]: row["category_id"] for row in cur.fetchall()}

        catalog = []
        for item in online_data:
            c_name = format_category(item.get("category", "General"))
            cat_id = cat_map.get(c_name, 1)
            title = item.get("title", "").strip()
            price = round(float(item.get("price", 10.0)), 2)
            stock = random.randint(25, 120)
            img = item.get("image", "")
            catalog.append((title, cat_id, price, stock, img))

        cur.executemany(
            "INSERT INTO products (name, category_id, price, stock, image_url) VALUES (?, ?, ?, ?, ?)",
            catalog
        )
    else:
        # Fallback seeding
        fallback_cats = ["Men's Clothing", "Jewelery", "Electronics", "Women's Clothing"]
        for cat in fallback_cats:
            cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

        catalog = FALLBACK_CATALOG
        cur.executemany(
            "INSERT INTO products (name, category_id, price, stock, image_url) VALUES (?, ?, ?, ?, ?)",
            catalog
        )

    # 3. Seed 50 relational transactions for NetworkX graph projection
    names = ['Aanvi', 'Divya', 'Rohit', 'Ananya', 'VijayKumar', 'Lino', 'Aadish', 'Maheswarrr']
    base_date = datetime(2026, 1, 1)
    catalog_len = len(catalog)

    for order_id in range(1, 51):
        cust = random.choice(names)
        order_date = base_date + timedelta(days=random.randint(1, 180))
        cur.execute(
            "INSERT INTO orders (customer_name, order_date, total_amount) VALUES (?, ?, 0)",
            (cust, order_date.strftime("%Y-%m-%d"))
        )

        picked_ids = random.sample(range(1, catalog_len + 1), k=random.choice([2, 3, 4]))
        order_total = 0.0

        for pid in picked_ids:
            cur.execute("SELECT price FROM products WHERE product_id = ?", (pid,))
            row = cur.fetchone()
            if row:
                price = row[0]
                cur.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, 1, ?)",
                    (order_id, pid, price)
                )
                order_total += price

        cur.execute("UPDATE orders SET total_amount = ? WHERE order_id = ?", (round(order_total, 2), order_id))

    conn.commit()
    print(f"[+] Database seeded with {catalog_len} online FakeStore products and 50 relational transactions.")


def sync_online_catalog(conn=None):
    """Fetches live products from FakeStore API and updates/adds them to local SQLite database."""
    should_close = False
    if conn is None:
        conn = get_connection()
        should_close = True

    online_data = fetch_fakestore_products()
    if not online_data:
        if should_close:
            conn.close()
        return False, "Could not connect to online FakeStore API DBMS."

    cur = conn.cursor()

    # Sync categories
    for item in online_data:
        c_title = format_category(item.get("category", "General"))
        cur.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (c_title,))

    cur.execute("SELECT category_id, name FROM categories")
    cat_map = {row["name"]: row["category_id"] for row in cur.fetchall()}

    added = 0
    updated = 0

    for item in online_data:
        title = item.get("title", "").strip()
        c_title = format_category(item.get("category", "General"))
        cat_id = cat_map.get(c_title, 1)
        price = round(float(item.get("price", 10.0)), 2)
        img = item.get("image", "")

        cur.execute("SELECT product_id FROM products WHERE name = ?", (title,))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE products
                SET price = ?, category_id = ?, image_url = ?
                WHERE product_id = ?
            """, (price, cat_id, img, existing["product_id"]))
            updated += 1
        else:
            cur.execute("""
                INSERT INTO products (name, category_id, price, stock, image_url)
                VALUES (?, ?, ?, ?, ?)
            """, (title, cat_id, price, random.randint(20, 100), img))
            added += 1

    conn.commit()
    if should_close:
        conn.close()

    msg = f"Synced with FakeStore API: {added} new products added, {updated} updated."
    print(f"[+] {msg}")
    return True, msg


if __name__ == "__main__":
    import sys
    force = "--sync" in sys.argv or "--reset" in sys.argv
    init_db(force_reseed=force)
