import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
import networkx as nx
from database import init_db, DB_NAME

# Auto-initialize database schema and seeds on startup if missing
init_db()

app = Flask(__name__)
CORS(app)


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@app.route("/")
def index():
    return jsonify({
        "status": "online",
        "service": "Fashion.45 REST API, Admin Suite & NetworkX Engine",
        "endpoints": [
            "/api/products",
            "/api/categories",
            "/api/recommendations/<id>",
            "/api/graph-data",
            "/api/analytics/summary",
            "/api/admin/products",
            "/api/admin/orders",
            "/api/order"
        ]
    })


@app.route("/api/categories", methods=["GET"])
def get_categories():
    conn = get_db()
    try:
        rows = conn.execute("SELECT category_id, name FROM categories ORDER BY category_id").fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/products", methods=["GET"])
def get_products():
    category_id = request.args.get("category_id")
    conn = get_db()
    cur = conn.cursor()

    query = """
        SELECT 
            p.product_id, 
            p.name, 
            p.price, 
            p.stock, 
            p.image_url,
            c.name AS category_name, 
            p.category_id
        FROM products p
        JOIN categories c ON p.category_id = c.category_id
    """
    try:
        if category_id:
            query += " WHERE p.category_id = ? ORDER BY p.product_id ASC"
            rows = cur.execute(query, (category_id,)).fetchall()
        else:
            query += " ORDER BY p.product_id ASC"
            rows = cur.execute(query).fetchall()

        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/order", methods=["POST"])
def create_order():
    data = request.json or {}
    cust_name = data.get("customer_name", "Walk-in Customer")
    if isinstance(cust_name, str):
        cust_name = cust_name.strip() or "Walk-in Customer"
    else:
        cust_name = "Walk-in Customer"

    raw_items = data.get("items")
    if raw_items is None and "product_ids" in data:
        counts = {}
        for pid in data["product_ids"]:
            counts[pid] = counts.get(pid, 0) + 1
        raw_items = [{"product_id": pid, "quantity": qty} for pid, qty in counts.items()]

    if not raw_items:
        return jsonify({"error": "Empty cart payload. Items are required."}), 400

    conn = get_db()
    cur = conn.cursor()

    try:
        order_date = datetime.now().strftime("%Y-%m-%d")
        cur.execute(
            "INSERT INTO orders (customer_name, order_date, total_amount) VALUES (?, ?, 0)",
            (cust_name, order_date)
        )
        order_id = cur.lastrowid

        order_total = 0.0

        for item in raw_items:
            pid = int(item["product_id"])
            qty = int(item.get("quantity", 1))

            cur.execute("SELECT name, price, stock FROM products WHERE product_id = ?", (pid,))
            prod = cur.fetchone()

            if not prod:
                raise ValueError(f"Product ID {pid} does not exist.")
            if prod["stock"] < qty:
                raise ValueError(f"Insufficient stock for '{prod['name']}'. In stock: {prod['stock']}")

            unit_price = prod["price"]
            subtotal = unit_price * qty
            order_total += subtotal

            cur.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)",
                (order_id, pid, qty, unit_price)
            )

            cur.execute(
                "UPDATE products SET stock = stock - ? WHERE product_id = ?",
                (qty, pid)
            )

        cur.execute("UPDATE orders SET total_amount = ? WHERE order_id = ?", (round(order_total, 2), order_id))
        conn.commit()

        return jsonify({
            "message": "Order committed successfully",
            "order_id": order_id,
            "total_amount": round(order_total, 2)
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


# ----------------- ADMIN SUITE APIS -----------------

@app.route("/api/admin/products", methods=["POST"])
def admin_add_product():
    """Adds a new product to inventory."""
    data = request.json or {}
    name = str(data.get("name", "")).strip()
    category_id = data.get("category_id")
    price = data.get("price")
    stock = data.get("stock", 0)
    image_url = str(data.get("image_url", "")).strip()

    if not name or category_id is None or price is None:
        return jsonify({"error": "Name, Category, and Price are required fields."}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO products (name, category_id, price, stock, image_url)
            VALUES (?, ?, ?, ?, ?)
        """, (name, int(category_id), float(price), int(stock), image_url))
        conn.commit()
        new_id = cur.lastrowid
        return jsonify({"message": "Product created successfully", "product_id": new_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


@app.route("/api/admin/products/<int:product_id>", methods=["PUT"])
def admin_update_product(product_id):
    """Updates stock count or price of an existing product."""
    data = request.json or {}
    stock = data.get("stock")
    price = data.get("price")

    if stock is None and price is None:
        return jsonify({"error": "Provide at least stock or price to update."}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        if stock is not None and price is not None:
            cur.execute("UPDATE products SET stock = ?, price = ? WHERE product_id = ?", (int(stock), float(price), product_id))
        elif stock is not None:
            cur.execute("UPDATE products SET stock = ? WHERE product_id = ?", (int(stock), product_id))
        elif price is not None:
            cur.execute("UPDATE products SET price = ? WHERE product_id = ?", (float(price), product_id))

        conn.commit()
        return jsonify({"message": f"Product #{product_id} updated successfully."})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


@app.route("/api/admin/products/<int:product_id>", methods=["DELETE"])
def admin_delete_product(product_id):
    """Removes a product from inventory."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM order_items WHERE product_id = ?", (product_id,))
        cur.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()
        return jsonify({"message": f"Product #{product_id} deleted."})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()


@app.route("/api/admin/orders", methods=["GET"])
def admin_get_orders():
    """Returns the last 25 orders with item counts."""
    conn = get_db()
    cur = conn.cursor()
    try:
        rows = cur.execute("""
            SELECT 
                o.order_id, 
                o.customer_name, 
                o.order_date, 
                o.total_amount,
                COUNT(oi.item_id) AS total_items
            FROM orders o
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            GROUP BY o.order_id
            ORDER BY o.order_id DESC
            LIMIT 25
        """).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


# ----------------- NETWORKX GRAPH ENGINE -----------------

@app.route("/api/graph-data", methods=["GET"])
def get_graph_data():
    conn = get_db()
    df = pd.read_sql_query("SELECT order_id, product_id FROM order_items", conn)
    cur = conn.cursor()
    cur.execute("SELECT product_id, name FROM products")
    names_map = {row["product_id"]: row["name"] for row in cur.fetchall()}
    conn.close()

    if df.empty:
        return jsonify({"nodes": [], "edges": []})

    B = nx.Graph()
    for _, row in df.iterrows():
        order_node = f"order_{row['order_id']}"
        product_node = int(row["product_id"])
        B.add_node(order_node, bipartite=0)
        B.add_node(product_node, bipartite=1)
        B.add_edge(order_node, product_node)

    product_nodes = {int(p) for p in df["product_id"].unique()}
    P = nx.bipartite.weighted_projected_graph(B, product_nodes)

    edges = []
    for u, v, d in P.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "source_name": names_map.get(u, f"Item {u}"),
            "target_name": names_map.get(v, f"Item {v}"),
            "weight": d["weight"]
        })

    nodes = [{"id": n, "label": names_map.get(n, f"Item {n}")} for n in P.nodes()]
    return jsonify({"nodes": nodes, "edges": edges})


@app.route("/api/recommendations/<int:product_id>", methods=["GET"])
def get_recommendations(product_id):
    conn = get_db()
    df = pd.read_sql_query("SELECT order_id, product_id FROM order_items", conn)

    if df.empty or product_id not in df["product_id"].values:
        conn.close()
        return jsonify({"target_product_id": product_id, "recommendations": []})

    B = nx.Graph()
    for _, row in df.iterrows():
        order_node = f"order_{row['order_id']}"
        prod_node = int(row["product_id"])
        B.add_node(order_node, bipartite=0)
        B.add_node(prod_node, bipartite=1)
        B.add_edge(order_node, prod_node)

    product_nodes = {int(p) for p in df["product_id"].unique()}
    P = nx.bipartite.weighted_projected_graph(B, product_nodes)

    recommendations = []
    if product_id in P:
        neighbors = P[product_id]
        sorted_neighbors = sorted(neighbors.items(), key=lambda x: x[1]["weight"], reverse=True)

        cur = conn.cursor()
        for rec_id, edge_data in sorted_neighbors[:3]:
            cur.execute("SELECT product_id, name, price, stock, image_url FROM products WHERE product_id = ?", (rec_id,))
            row = cur.fetchone()
            if row:
                rec_dict = dict(row)
                rec_dict["co_purchase_weight"] = edge_data["weight"]
                recommendations.append(rec_dict)

    conn.close()
    return jsonify({
        "target_product_id": product_id,
        "recommendations": recommendations
    })


@app.route("/api/analytics/summary", methods=["GET"])
def get_analytics():
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) AS total_orders, IFNULL(SUM(total_amount), 0) AS gross_revenue FROM orders")
        stats = dict(cur.fetchone())
        cur.execute("SELECT COUNT(DISTINCT customer_name) AS unique_customers FROM orders")
        cust_count = cur.fetchone()["unique_customers"]
        cur.execute("SELECT COUNT(*) AS total_skus, IFNULL(SUM(stock), 0) AS total_inventory FROM products")
        inv_stats = dict(cur.fetchone())

        return jsonify({
            "total_orders": stats["total_orders"],
            "gross_revenue": round(stats["gross_revenue"], 2),
            "unique_customers": cust_count,
            "total_skus": inv_stats["total_skus"],
            "total_inventory": inv_stats["total_inventory"] or 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("[*] Fashion.45 Unified Server listening on http://127.0.0.1:5000")
    app.run(port=5000, debug=True)
