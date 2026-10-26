# Fashion.45 — Desktop E-Commerce & Graph Recommendation Engine

A standalone desktop e-commerce platform and analytics system built in pure Python. The project uses a normalized SQLite database, a Flask REST API backend, an on-demand NetworkX bipartite graph projection engine for bundle recommendations, and a native CustomTkinter desktop interface with an integrated Admin Management Suite.

---

## 🚀 Features

- **Normalized Relational RDBMS (`database.py`):** 3NF relational schema in SQLite enforcing strict foreign keys (`PRAGMA foreign_keys = ON;`) with deterministic baseline seeding (`seed=42`) and image URL support.
- **RESTful API Backend (`app.py`):** Modular Flask endpoints serving product catalogs, categories, transactional order commits, and graph metrics. Auto-initializes the database on startup.
- **NetworkX Bipartite Graph Engine:** Models transactions as a bipartite graph $B(\text{Orders}, \text{Products})$ and calculates weighted one-mode projections onto products to detect real-time co-purchasing bundles without node collision.
- **Embedded Network Visualizer:** Native Matplotlib canvas rendering the product co-purchasing network graph inside a top-level popup with automatic memory management (`plt.close(fig)`).
- **Native Desktop Client (`desktop_app.py`):** Responsive dark-mode interface built with CustomTkinter featuring live category filtering, cart management, atomic checkout, asynchronous image caching (Pillow), and a complete Admin Suite (real-time KPIs, inventory restock, deletion, and transaction logs).

---

## 📦 Tech Stack

- **GUI Client:** CustomTkinter, Matplotlib (`FigureCanvasTkAgg`), Pillow (PIL)
- **Backend API:** Python 3, Flask, Flask-CORS, Requests
- **Analytics & Graph Theory:** NetworkX, Pandas
- **Database:** SQLite3

---

## 🛠️ Getting Started

### 1. Prerequisites
Ensure you have Python 3.10+ installed on your system.

### 2. Installation
Clone the repository and install all dependencies:
```bash
git clone https://github.com/anandhukrishne/fashion.45
cd fashion.45
pip install -r requirements.txt
```

---

## 🏃 Running the Application

Fashion.45 is a two-tier architecture. Run the backend API server first, followed by the desktop app in separate terminals:

### Terminal 1: Backend Server
```bash
python app.py
```
*The server will automatically initialize and seed `products.db` if missing, and listen on `http://127.0.0.1:5000`.*

### Terminal 2: Desktop Client
```bash
python desktop_app.py
```
*Launches the dark-mode GUI client with customer storefront, bundle recommendations, and the Admin Suite.*

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service health status and registered routes |
| `GET` | `/api/categories` | Retrieve all product categories |
| `GET` | `/api/products` | Retrieve catalog (supports `?category_id=<id>`) |
| `POST` | `/api/order` | Commit atomic customer order with stock deduction |
| `GET` | `/api/recommendations/<id>` | NetworkX bipartite projection bundle suggestions |
| `GET` | `/api/graph-data` | Full co-purchasing graph topology (nodes and weighted edges) |
| `GET` | `/api/analytics/summary` | Admin KPIs (revenue, orders, SKUs, inventory units) |
| `GET` | `/api/admin/orders` | Recent 25 orders with item counts and totals |
| `POST` | `/api/admin/products` | Add new product to inventory |
| `PUT` | `/api/admin/products/<id>` | Update product stock count or unit price |
| `DELETE` | `/api/admin/products/<id>` | Delete product and cascade related order items |

---

## 📁 Repository Structure

```
Fashion.45/
├── assets/           # App icons and 45 stylized logo wordmarks
├── database.py       # SQLite connection, schema definition, and deterministic seeder
├── app.py            # Flask REST API + NetworkX bipartite projection engine
├── desktop_app.py    # CustomTkinter GUI client (Storefront + Admin Suite)
├── products.db       # Relational SQLite database
├── requirements.txt  # Runtime Python dependencies
└── README.md         # Setup and architectural documentation
```
## About author
- **Developer:** AnandhuKrishne, Student at IIITKottayam as a part of ITW III course projekt
- **Imaginary Developer Brand:** 45 STUDioS, not an official brand yet
- **Current Version:** V 1.0.0 (Beta)
