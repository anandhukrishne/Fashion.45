import io
import os
import threading
from datetime import datetime
import requests
from PIL import Image
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
API_BASE = "http://127.0.0.1:5000/api"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class Fashion45DesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Fashion.45 | Desktop Client & Admin Suite")
        self.geometry("1180x760")
        self.minsize(1050, 680)

        # Set Window Icon
        icon_path = os.path.join(ASSETS_DIR, "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        self.cart = {}
        self.categories = []
        self.active_recommendation = None
        self.image_cache = {}

        # Top Navigation Bar
        self.setup_nav_bar()

        # Dynamic Content Container
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Build Both Views
        self.build_storefront_view()
        self.build_admin_view()

        # Initialize Default View & Load Catalog
        self.show_storefront()
        self.load_categories()
        self.load_products()

    # ----------------- TOP NAVIGATION BAR -----------------

    def setup_nav_bar(self):
        nav = ctk.CTkFrame(self, height=50, corner_radius=0, fg_color="#181A1D")
        nav.pack(fill="x", side="top")

        # Brand Header: "FASHION." text + 45 logo image
        brand_frame = ctk.CTkFrame(nav, fg_color="transparent")
        brand_frame.pack(side="left", padx=(18, 12))

        ctk.CTkLabel(
            brand_frame,
            text="FASHION.",
            font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
            text_color="#FB542B"
        ).pack(side="left")

        # Load the 45 logo as-is (white variant for dark mode visibility)
        logo_white_path = os.path.join(ASSETS_DIR, "logo_white.png")
        logo_orig_path = os.path.join(ASSETS_DIR, "logo_orig.png")
        if os.path.exists(logo_white_path):
            logo_light = Image.open(logo_orig_path) if os.path.exists(logo_orig_path) else Image.open(logo_white_path)
            logo_dark = Image.open(logo_white_path)
            self.nav_logo = ctk.CTkImage(light_image=logo_light, dark_image=logo_dark, size=(30, 30))
            ctk.CTkLabel(
                brand_frame,
                text="",
                image=self.nav_logo
            ).pack(side="left", padx=(2, 0))

        self.btn_nav_store = ctk.CTkButton(
            nav,
            text="🛍️ Storefront",
            width=130,
            fg_color="#FB542B",
            hover_color="#D9411E",
            command=self.show_storefront
        )
        self.btn_nav_store.pack(side="left", padx=5, pady=8)

        self.btn_nav_admin = ctk.CTkButton(
            nav,
            text="⚙️ Admin Suite",
            width=130,
            fg_color="#2B2D31",
            hover_color="#3E4249",
            command=self.show_admin
        )
        self.btn_nav_admin.pack(side="left", padx=5, pady=8)

        # App Info / Developer Details Button
        self.btn_info = ctk.CTkButton(
            nav,
            text="ⓘ",
            width=36,
            height=32,
            fg_color="#2B2D31",
            hover_color="#3E4249",
            font=ctk.CTkFont(size=16, weight="bold"),
            command=self.open_info_window
        )
        self.btn_info.pack(side="right", padx=(5, 15))

        self.status_banner = ctk.CTkLabel(
            nav,
            text="Connected: 127.0.0.1:5000",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        )
        self.status_banner.pack(side="right", padx=10)

    def update_status(self, text):
        self.after(0, lambda: self.status_banner.configure(text=text))

    def show_storefront(self):
        self.admin_frame.pack_forget()
        self.storefront_frame.pack(fill="both", expand=True)
        self.btn_nav_store.configure(fg_color="#FB542B")
        self.btn_nav_admin.configure(fg_color="#2B2D31")

    def show_admin(self):
        self.storefront_frame.pack_forget()
        self.admin_frame.pack(fill="both", expand=True)
        self.btn_nav_admin.configure(fg_color="#FB542B")
        self.btn_nav_store.configure(fg_color="#2B2D31")
        self.refresh_admin_data()

    # ----------------- APP INFO / DEVELOPER DETAILS -----------------

    def open_info_window(self):
        info_win = ctk.CTkToplevel(self)
        info_win.title("About Fashion.45 | Developer Details")
        info_win.geometry("450x490")
        info_win.resizable(False, False)
        info_win.attributes("-topmost", True)
        info_win.lift()
        info_win.focus_force()

        card = ctk.CTkFrame(info_win, fg_color="#181A1D", corner_radius=12)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        logo_white_path = os.path.join(ASSETS_DIR, "logo_white.png")
        logo_orig_path = os.path.join(ASSETS_DIR, "logo_orig.png")
        if os.path.exists(logo_white_path):
            about_light = Image.open(logo_orig_path) if os.path.exists(logo_orig_path) else Image.open(logo_white_path)
            about_dark = Image.open(logo_white_path)
            self.about_logo = ctk.CTkImage(light_image=about_light, dark_image=about_dark, size=(72, 72))
            ctk.CTkLabel(card, text="", image=self.about_logo).pack(pady=(18, 6))

        ctk.CTkLabel(
            card,
            text="FASHION.45",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FB542B"
        ).pack()

        ctk.CTkLabel(
            card,
            text="Desktop E-Commerce & Graph Recommendation Engine",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(pady=(2, 12))

        ctk.CTkFrame(card, height=1, fg_color="#2B2D31").pack(fill="x", padx=20, pady=4)

        details_box = ctk.CTkFrame(card, fg_color="#1E2024", corner_radius=8)
        details_box.pack(fill="x", padx=16, pady=10)

        details = [
            ("Developer Studio:", "45 STUDioS"),
            ("Engineering Lead:", "AnandhuKrishne"),
            ("Version:", "1.0.0 (Release Build)"),
            ("Online DBMS Source:", "FakeStore API (Live Cloud DBMS)"),
            ("Architecture:", "Two-tier Client / REST API"),
            ("Backend Stack:", "Flask, SQLite3, NetworkX"),
            ("Frontend Stack:", "CustomTkinter, Matplotlib, Pillow"),
            ("Copyright:", f"© {datetime.now().year} 45 STUDioS")
        ]

        for label, val in details:
            row = ctk.CTkFrame(details_box, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(
                row,
                text=label,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="gray",
                anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=val,
                font=ctk.CTkFont(size=11),
                text_color="#FB542B" if "45" in val else "#E0E0E0",
                anchor="e"
            ).pack(side="right")

        ctk.CTkButton(
            card,
            text="Close",
            width=110,
            height=30,
            fg_color="#2B2D31",
            hover_color="#3E4249",
            command=info_win.destroy
        ).pack(pady=(14, 10))

    # ----------------- STOREFRONT VIEW -----------------

    def build_storefront_view(self):
        self.storefront_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.storefront_frame.grid_columnconfigure(0, weight=0)
        self.storefront_frame.grid_columnconfigure(1, weight=3)
        self.storefront_frame.grid_columnconfigure(2, weight=2)
        self.storefront_frame.grid_rowconfigure(0, weight=1)

        # 1. Left Sidebar
        sidebar = ctk.CTkFrame(self.storefront_frame, width=220)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        ctk.CTkLabel(
            sidebar,
            text="Filter Category",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=15, pady=(15, 2))

        self.cat_dropdown = ctk.CTkOptionMenu(
            sidebar,
            values=["All Categories"],
            command=self.filter_by_category
        )
        self.cat_dropdown.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkButton(
            sidebar,
            text="Refresh Catalog",
            fg_color="#2B2D31",
            hover_color="#3E4249",
            command=self.load_products
        ).pack(fill="x", padx=15, pady=10)

        # Dynamic copyright at bottom of left slider that changes with the current year
        current_year = datetime.now().year
        self.copyright_label = ctk.CTkLabel(
            sidebar,
            text=f"(C) {current_year} 45 STUDioS",
            font=ctk.CTkFont(size=11),
            text_color="#7F8C8D"
        )
        self.copyright_label.pack(side="bottom", pady=15)

        # 2. Center Catalog Panel
        catalog_box = ctk.CTkFrame(self.storefront_frame)
        catalog_box.grid(row=0, column=1, sticky="nsew", padx=10)
        catalog_box.grid_rowconfigure(1, weight=1)
        catalog_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            catalog_box,
            text="Catalog & Inventory",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.catalog_scroll = ctk.CTkScrollableFrame(catalog_box)
        self.catalog_scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.catalog_scroll.grid_columnconfigure(0, weight=1)

        # 3. Right Cart & NetworkX Bundle Panel
        right_panel = ctk.CTkFrame(self.storefront_frame)
        right_panel.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right_panel,
            text="Shopping Cart",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.cart_scroll = ctk.CTkScrollableFrame(right_panel, height=220)
        self.cart_scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 10))
        self.cart_scroll.grid_columnconfigure(0, weight=1)

        # Recommendation Box
        self.rec_box = ctk.CTkFrame(
            right_panel,
            fg_color="#1E2024",
            border_width=1,
            border_color="#33373E"
        )
        self.rec_box.grid(row=2, column=0, sticky="ew", padx=15, pady=10)
        self.rec_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.rec_box,
            text="⚡ NetworkX Co-Purchase Bundle",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FB542B"
        ).grid(row=0, column=0, padx=12, pady=(10, 2), sticky="w")

        self.rec_label_content = ctk.CTkLabel(
            self.rec_box,
            text="Click [Bundle ⚡] on any product to run graph projection.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            wraplength=280,
            justify="left"
        )
        self.rec_label_content.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="w")

        rec_btn_frame = ctk.CTkFrame(self.rec_box, fg_color="transparent")
        rec_btn_frame.grid(row=2, column=0, padx=12, pady=(0, 10), sticky="ew")

        ctk.CTkButton(
            rec_btn_frame,
            text="View Graph 🕸️",
            width=110,
            height=28,
            fg_color="#2B2D31",
            hover_color="#3E4249",
            font=ctk.CTkFont(size=11),
            command=self.open_graph_window
        ).pack(side="left", padx=(0, 6))

        self.btn_add_bundle = ctk.CTkButton(
            rec_btn_frame,
            text="+ Add Bundle",
            width=110,
            height=28,
            fg_color="#FB542B",
            hover_color="#D9411E",
            font=ctk.CTkFont(size=11, weight="bold"),
            state="disabled",
            command=self.add_recommended_bundle_to_cart
        )
        self.btn_add_bundle.pack(side="left")

        # Checkout Area (Customer Name shifted right near the cart)
        summary_frame = ctk.CTkFrame(right_panel, fg_color="transparent")
        summary_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(5, 15))
        summary_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            summary_frame,
            text="Customer Name:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).grid(row=0, column=0, sticky="w", pady=(0, 2))

        self.entry_name = ctk.CTkEntry(
            summary_frame,
            placeholder_text="Customer Name (e.g., Aanvi)",
            height=32
        )
        self.entry_name.insert(0, "Aanvi")
        self.entry_name.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.label_total = ctk.CTkLabel(
            summary_frame,
            text="Total: ₹0.00",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FB542B"
        )
        self.label_total.grid(row=2, column=0, sticky="w", pady=(0, 8))

        ctk.CTkButton(
            summary_frame,
            text="Confirm Order (SQL Commit)",
            fg_color="#FB542B",
            hover_color="#D9411E",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.submit_order
        ).grid(row=3, column=0, sticky="ew")

    # ----------------- ADMIN SUITE VIEW -----------------

    def build_admin_view(self):
        self.admin_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.admin_frame.grid_columnconfigure(0, weight=3)
        self.admin_frame.grid_columnconfigure(1, weight=2)
        self.admin_frame.grid_rowconfigure(1, weight=1)

        # Top KPI Metric Row
        kpi_row = ctk.CTkFrame(self.admin_frame, fg_color="transparent")
        kpi_row.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.kpi_rev = self.create_kpi_card(kpi_row, "GROSS REVENUE", "₹0.00", "#2ECC71")
        self.kpi_orders = self.create_kpi_card(kpi_row, "ORDERS PROCESSED", "0", "#3498DB")
        self.kpi_skus = self.create_kpi_card(kpi_row, "ACTIVE SKUs", "0", "#F39C12")
        self.kpi_stock = self.create_kpi_card(kpi_row, "INVENTORY UNITS", "0", "#9B59B6")

        # Left Column: Inventory Table
        inv_box = ctk.CTkFrame(self.admin_frame)
        inv_box.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        inv_box.grid_rowconfigure(1, weight=1)
        inv_box.grid_columnconfigure(0, weight=1)

        inv_header = ctk.CTkFrame(inv_box, fg_color="transparent")
        inv_header.grid(row=0, column=0, padx=15, pady=10, sticky="ew")
        inv_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            inv_header,
            text="Inventory Controls & Restock",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            inv_header,
            text="🌐 Sync Online DBMS",
            width=150,
            height=28,
            fg_color="#2980B9",
            hover_color="#1F618D",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.admin_sync_online_dbms
        ).grid(row=0, column=1, sticky="e")

        self.admin_inv_scroll = ctk.CTkScrollableFrame(inv_box)
        self.admin_inv_scroll.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0, 15))
        self.admin_inv_scroll.grid_columnconfigure(0, weight=1)

        # Right Column: Add Product & Recent Orders
        right_admin = ctk.CTkFrame(self.admin_frame)
        right_admin.grid(row=1, column=1, sticky="nsew")

        form_box = ctk.CTkFrame(right_admin, fg_color="#1E2024")
        form_box.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(
            form_box,
            text="Add New Product",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FB542B"
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.form_name = ctk.CTkEntry(form_box, placeholder_text="Product Title")
        self.form_name.pack(fill="x", padx=15, pady=4)

        self.form_cat = ctk.CTkOptionMenu(
            form_box,
            values=["Electronics", "Jewelery", "Men's Clothing", "Women's Clothing"]
        )
        self.form_cat.pack(fill="x", padx=15, pady=4)

        num_frame = ctk.CTkFrame(form_box, fg_color="transparent")
        num_frame.pack(fill="x", padx=15, pady=4)

        self.form_price = ctk.CTkEntry(num_frame, placeholder_text="Price (₹)", width=120)
        self.form_price.pack(side="left", padx=(0, 5))

        self.form_stock = ctk.CTkEntry(num_frame, placeholder_text="Stock Units", width=120)
        self.form_stock.pack(side="left")

        self.form_img = ctk.CTkEntry(form_box, placeholder_text="Image URL (https://...)")
        self.form_img.pack(fill="x", padx=15, pady=4)

        ctk.CTkButton(
            form_box,
            text="+ Add to Database",
            fg_color="#FB542B",
            hover_color="#D9411E",
            command=self.admin_add_product
        ).pack(fill="x", padx=15, pady=(8, 12))

        # Recent Transactions
        ctk.CTkLabel(
            right_admin,
            text="Recent Transactions",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=15, pady=(10, 2))

        self.admin_orders_scroll = ctk.CTkScrollableFrame(right_admin, height=220)
        self.admin_orders_scroll.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def create_kpi_card(self, parent, title, initial_value, accent_color):
        card = ctk.CTkFrame(parent, fg_color="#1E2024", border_width=1, border_color="#2B2D31")
        card.pack(side="left", expand=True, fill="both", padx=5)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="gray"
        ).pack(anchor="w", padx=12, pady=(10, 0))

        val_label = ctk.CTkLabel(
            card,
            text=initial_value,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=accent_color
        )
        val_label.pack(anchor="w", padx=12, pady=(2, 10))
        return val_label

    # ----------------- ASYNCHRONOUS IMAGE LOADER -----------------

    def load_image_thumbnail_async(self, url, img_label, size=(60, 60)):
        """Fetches product thumbnail asynchronously and applies to label upon completion."""
        if not url:
            return

        if url in self.image_cache:
            cached_img = self.image_cache[url]
            if cached_img:
                img_label.configure(image=cached_img, text="")
            return

        def worker():
            try:
                res = requests.get(url, timeout=4.0)
                if res.status_code == 200:
                    img = Image.open(io.BytesIO(res.content))
                    # Handle transparency cleanly for FakeStore PNGs
                    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
                        bg.alpha_composite(img.convert("RGBA"))
                        raw_img = bg.convert("RGB")
                    else:
                        raw_img = img.convert("RGB")
                    raw_img = raw_img.resize(size, Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=size)
                    self.image_cache[url] = ctk_img

                    def update_widget():
                        try:
                            if img_label.winfo_exists():
                                img_label.configure(image=ctk_img, text="")
                        except Exception:
                            pass

                    self.after(0, update_widget)
                else:
                    self.image_cache[url] = None
            except Exception:
                self.image_cache[url] = None

        threading.Thread(target=worker, daemon=True).start()

    # ----------------- DATA FETCHING & RENDERING -----------------

    def load_categories(self):
        def worker():
            try:
                res = requests.get(f"{API_BASE}/categories", timeout=5).json()
                if isinstance(res, list):
                    self.categories = res
                    cat_names = ["All Categories"] + [c["name"] for c in self.categories]
                    self.after(0, lambda: self._apply_categories(cat_names))
            except Exception as e:
                self.update_status(f"Category fetch error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def _apply_categories(self, cat_names):
        try:
            self.cat_dropdown.configure(values=cat_names)
            admin_cats = [c["name"] for c in self.categories]
            if admin_cats:
                self.form_cat.configure(values=admin_cats)
        except Exception:
            pass

    def filter_by_category(self, choice):
        if choice == "All Categories":
            self.load_products()
        else:
            cat_id = next((c["category_id"] for c in self.categories if c["name"] == choice), None)
            if cat_id is not None:
                self.load_products(category_id=cat_id)

    def load_products(self, category_id=None):
        def worker():
            try:
                url = f"{API_BASE}/products"
                if category_id is not None:
                    url += f"?category_id={category_id}"
                products = requests.get(url, timeout=5).json()
                self.after(0, lambda: self.render_catalog(products))
            except Exception as e:
                self.update_status(f"API Error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def render_catalog(self, products):
        for widget in self.catalog_scroll.winfo_children():
            widget.destroy()

        if not products or not isinstance(products, list):
            ctk.CTkLabel(
                self.catalog_scroll,
                text="No products found in category.",
                text_color="gray"
            ).pack(pady=20)
            return

        for idx, p in enumerate(products):
            pid = p["product_id"]
            name = p["name"]
            price = float(p["price"])
            stock = int(p["stock"])
            cat_name = p.get("category_name", "")
            img_url = p.get("image_url", "")

            card = ctk.CTkFrame(self.catalog_scroll, fg_color="#1E2024")
            card.grid(row=idx, column=0, sticky="ew", padx=5, pady=6)
            card.grid_columnconfigure(1, weight=1)

            # Thumbnail placeholder (updated asynchronously)
            img_label = ctk.CTkLabel(
                card,
                text="📦",
                width=60,
                height=60,
                fg_color="#181A1D",
                corner_radius=6,
                font=ctk.CTkFont(size=20)
            )
            img_label.grid(row=0, column=0, rowspan=2, padx=10, pady=8)

            if img_url:
                self.load_image_thumbnail_async(img_url, img_label, size=(60, 60))

            # Details
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.grid(row=0, column=1, sticky="w", padx=5, pady=(8, 2))

            ctk.CTkLabel(
                info,
                text=name,
                font=ctk.CTkFont(size=14, weight="bold"),
                anchor="w",
                wraplength=340,
                justify="left"
            ).pack(anchor="w")

            stock_color = "#E74C3C" if stock == 0 else ("#F39C12" if stock <= 5 else "#2ECC71")
            stock_text = "Out of Stock" if stock == 0 else f"{stock} in stock"

            ctk.CTkLabel(
                info,
                text=f"{cat_name}  •  {stock_text}",
                font=ctk.CTkFont(size=11),
                text_color=stock_color
            ).pack(anchor="w", pady=(2, 0))

            # Actions & Price
            act = ctk.CTkFrame(card, fg_color="transparent")
            act.grid(row=0, column=2, rowspan=2, padx=12, pady=8, sticky="e")

            ctk.CTkLabel(
                act,
                text=f"₹{price:,.2f}",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color="#FB542B"
            ).pack(anchor="e", pady=(0, 6))

            btn_box = ctk.CTkFrame(act, fg_color="transparent")
            btn_box.pack(anchor="e")

            ctk.CTkButton(
                btn_box,
                text="Bundle ⚡",
                width=75,
                height=28,
                fg_color="#2B2D31",
                hover_color="#3E4249",
                font=ctk.CTkFont(size=11),
                command=lambda p_id=pid, p_name=name: self.fetch_recommendation(p_id, p_name)
            ).pack(side="left", padx=(0, 6))

            add_btn = ctk.CTkButton(
                btn_box,
                text="Add to Cart",
                width=85,
                height=28,
                fg_color="#FB542B" if stock > 0 else "#555555",
                hover_color="#D9411E" if stock > 0 else "#555555",
                state="normal" if stock > 0 else "disabled",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda p_id=pid, p_name=name, p_price=price, p_stock=stock: self.add_to_cart(p_id, p_name, p_price, p_stock)
            )
            add_btn.pack(side="left")

    # ----------------- ADMIN ACTIONS -----------------

    def refresh_admin_data(self):
        def worker():
            try:
                summary = requests.get(f"{API_BASE}/analytics/summary", timeout=5).json()
                orders = requests.get(f"{API_BASE}/admin/orders", timeout=5).json()
                products = requests.get(f"{API_BASE}/products", timeout=5).json()
                self.after(0, lambda: self.update_admin_ui(summary, orders, products))
            except Exception as e:
                self.update_status(f"Admin error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def update_admin_ui(self, summary, orders, products):
        if isinstance(summary, dict):
            self.kpi_rev.configure(text=f"₹{summary.get('gross_revenue', 0):,.2f}")
            self.kpi_orders.configure(text=str(summary.get("total_orders", 0)))
            self.kpi_skus.configure(text=str(summary.get("total_skus", 0)))
            self.kpi_stock.configure(text=str(summary.get("total_inventory", 0)))

        for widget in self.admin_inv_scroll.winfo_children():
            widget.destroy()

        if isinstance(products, list):
            for p in products:
                pid = p["product_id"]
                row = ctk.CTkFrame(self.admin_inv_scroll, fg_color="#181A1D")
                row.pack(fill="x", padx=2, pady=4)

                short_title = (p["name"][:26] + "..") if len(p["name"]) > 26 else p["name"]
                ctk.CTkLabel(
                    row,
                    text=f"#{pid} {short_title}",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    width=180,
                    anchor="w"
                ).pack(side="left", padx=8)

                ctk.CTkLabel(
                    row,
                    text=f"Stock: {p['stock']}",
                    font=ctk.CTkFont(size=12),
                    text_color="#FB542B",
                    width=80
                ).pack(side="left")

                ctk.CTkButton(
                    row,
                    text="+10 Stock",
                    width=70,
                    height=26,
                    fg_color="#2ECC71",
                    hover_color="#27AE60",
                    command=lambda p_id=pid, cur=p["stock"]: self.admin_update_stock(p_id, cur + 10)
                ).pack(side="right", padx=4)

                ctk.CTkButton(
                    row,
                    text="Delete",
                    width=55,
                    height=26,
                    fg_color="#E74C3C",
                    hover_color="#C0392B",
                    command=lambda p_id=pid: self.admin_delete_product(p_id)
                ).pack(side="right", padx=4)

        for widget in self.admin_orders_scroll.winfo_children():
            widget.destroy()

        if isinstance(orders, list):
            for o in orders:
                orow = ctk.CTkFrame(self.admin_orders_scroll, fg_color="#1E2024")
                orow.pack(fill="x", padx=2, pady=3)

                ctk.CTkLabel(
                    orow,
                    text=f"Order #{o['order_id']} • {o['customer_name']}",
                    font=ctk.CTkFont(size=11, weight="bold")
                ).pack(side="left", padx=8, pady=4)

                ctk.CTkLabel(
                    orow,
                    text=f"₹{o['total_amount']:,.2f}",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color="#FB542B"
                ).pack(side="right", padx=8, pady=4)

    def admin_add_product(self):
        name = self.form_name.get().strip()
        cat_str = self.form_cat.get()
        price_str = self.form_price.get().strip()
        stock_str = self.form_stock.get().strip()
        img = self.form_img.get().strip()

        if not name or not price_str or not stock_str:
            self.update_status("Fill in Name, Price, and Stock!")
            return

        try:
            price_val = float(price_str)
            stock_val = int(stock_str)
        except ValueError:
            self.update_status("Invalid price or stock value.")
            return

        cat_map = {c["name"]: c["category_id"] for c in self.categories}
        cat_id = cat_map.get(cat_str, 1)

        payload = {
            "name": name,
            "category_id": cat_id,
            "price": price_val,
            "stock": stock_val,
            "image_url": img
        }

        def worker():
            try:
                res = requests.post(f"{API_BASE}/admin/products", json=payload, timeout=5)
                if res.status_code == 201:
                    def on_success():
                        self.form_name.delete(0, "end")
                        self.form_price.delete(0, "end")
                        self.form_stock.delete(0, "end")
                        self.form_img.delete(0, "end")
                        self.update_status("New product added to inventory.")
                        self.refresh_admin_data()
                        self.load_products()
                    self.after(0, on_success)
                else:
                    err_msg = res.json().get("error", "Add failed")
                    self.update_status(f"Error: {err_msg}")
            except Exception as e:
                self.update_status(f"Network error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def admin_update_stock(self, pid, new_stock):
        def worker():
            try:
                requests.put(f"{API_BASE}/admin/products/{pid}", json={"stock": new_stock}, timeout=5)
                self.after(0, lambda: (self.refresh_admin_data(), self.load_products()))
            except Exception as e:
                self.update_status(f"Update error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def admin_delete_product(self, pid):
        def worker():
            try:
                requests.delete(f"{API_BASE}/admin/products/{pid}", timeout=5)
                self.after(0, lambda: (self.refresh_admin_data(), self.load_products()))
            except Exception as e:
                self.update_status(f"Delete error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def admin_sync_online_dbms(self):
        """Fetches live products from online FakeStore API DBMS and refreshes UI."""
        self.update_status("Fetching latest catalog from online FakeStore API DBMS...")

        def worker():
            try:
                res = requests.post(f"{API_BASE}/admin/sync-online", timeout=12)
                if res.status_code == 200:
                    data = res.json()
                    msg = data.get("message", "Synced online DBMS successfully.")
                    def on_sync():
                        self.update_status(f"✓ {msg}")
                        self.refresh_admin_data()
                        self.load_categories()
                        self.load_products()
                    self.after(0, on_sync)
                else:
                    err = res.json().get("message", "Sync failed.")
                    self.update_status(f"Sync error: {err}")
            except Exception as e:
                self.update_status(f"Sync error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    # ----------------- NETWORKX GRAPH & CART -----------------

    def fetch_recommendation(self, prod_id, prod_name):
        def worker():
            try:
                res = requests.get(f"{API_BASE}/recommendations/{prod_id}", timeout=5).json()
                recs = res.get("recommendations", [])

                def apply_rec():
                    if recs:
                        top = recs[0]
                        self.active_recommendation = top
                        text = (
                            f"Selected: {prod_name[:32]}..\n\n"
                            f"Frequently Bought Together:\n"
                            f"→ {top['name']}\n"
                            f"→ Price: ₹{float(top['price']):,.2f}\n"
                            f"→ Co-Purchase Weight: {top['co_purchase_weight']} orders"
                        )
                        self.btn_add_bundle.configure(state="normal")
                    else:
                        self.active_recommendation = None
                        self.btn_add_bundle.configure(state="disabled")
                        text = "No strong co-purchase links established for this SKU."

                    self.rec_label_content.configure(text=text)

                self.after(0, apply_rec)
            except Exception as e:
                self.update_status(f"Graph error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def add_recommended_bundle_to_cart(self):
        if not self.active_recommendation:
            return
        rec = self.active_recommendation
        self.add_to_cart(rec["product_id"], rec["name"], rec["price"], rec["stock"])

    def open_graph_window(self):
        def worker():
            try:
                res = requests.get(f"{API_BASE}/graph-data", timeout=5).json()
                nodes = res.get("nodes", [])
                edges = res.get("edges", [])

                def render_graph_popup():
                    if not nodes or not edges:
                        self.update_status("No graph data available.")
                        return

                    G = nx.Graph()
                    for n in nodes:
                        lbl = n.get("label", "")
                        short_lbl = (lbl[:14] + "..") if len(lbl) > 14 else lbl
                        G.add_node(n["id"], label=short_lbl)
                    for e in edges:
                        G.add_edge(e["source"], e["target"], weight=e.get("weight", 1))

                    win = ctk.CTkToplevel(self)
                    win.title("Fashion.45 | Complete Co-Purchase Affinity Network")
                    win.geometry("850x600")
                    win.attributes("-topmost", True)
                    win.lift()
                    win.focus_force()

                    fig, ax = plt.subplots(figsize=(8.5, 5.5), facecolor="#181A1D")
                    ax.set_facecolor("#181A1D")

                    pos = nx.spring_layout(G, k=0.85, seed=42)
                    weights = [G[u][v]["weight"] * 1.5 for u, v in G.edges()]
                    labels = nx.get_node_attributes(G, "label")

                    nx.draw_networkx_nodes(G, pos, node_size=1500, node_color="#FB542B", alpha=0.9, ax=ax)
                    nx.draw_networkx_edges(G, pos, width=weights, edge_color="#7F8C8D", alpha=0.6, ax=ax)
                    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_color="#FFFFFF", font_weight="bold", ax=ax)

                    edge_labels = {(u, v): f"w={d['weight']}" for u, v, d in G.edges(data=True)}
                    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7, font_color="#E0E0E0", ax=ax)

                    ax.set_title("Fashion.45: Bipartite Projected Co-Purchasing Graph", color="#FFFFFF", fontsize=12, fontweight="bold", pad=12)
                    ax.axis("off")
                    fig.tight_layout()

                    canvas = FigureCanvasTkAgg(fig, master=win)
                    canvas.draw()
                    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

                    def on_close():
                        plt.close(fig)
                        win.destroy()

                    win.protocol("WM_DELETE_WINDOW", on_close)

                self.after(0, render_graph_popup)

            except Exception as e:
                self.update_status(f"Graph error: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def add_to_cart(self, prod_id, name, price, stock):
        cur_qty = self.cart.get(prod_id, {}).get("qty", 0)
        if cur_qty + 1 > stock:
            self.update_status(f"Only {stock} units left in stock!")
            return

        if prod_id in self.cart:
            self.cart[prod_id]["qty"] += 1
        else:
            self.cart[prod_id] = {"name": name, "price": float(price), "qty": 1}

        self.render_cart()

    def render_cart(self):
        for widget in self.cart_scroll.winfo_children():
            widget.destroy()

        if not self.cart:
            ctk.CTkLabel(self.cart_scroll, text="Shopping bag is empty.", text_color="gray").pack(pady=30)
            self.label_total.configure(text="Total: ₹0.00")
            return

        total = 0.0
        for pid, item in self.cart.items():
            subtotal = item["price"] * item["qty"]
            total += subtotal

            row = ctk.CTkFrame(self.cart_scroll, fg_color="#181A1D")
            row.pack(fill="x", padx=2, pady=3)

            short = (item["name"][:22] + "..") if len(item["name"]) > 22 else item["name"]
            ctk.CTkLabel(row, text=f"{short} (x{item['qty']})", font=ctk.CTkFont(size=12)).pack(side="left", padx=8, pady=4)
            ctk.CTkLabel(row, text=f"₹{subtotal:,.2f}", font=ctk.CTkFont(size=12, weight="bold"), text_color="#FB542B").pack(side="right", padx=8, pady=4)

        self.label_total.configure(text=f"Total: ₹{total:,.2f}")

    def submit_order(self):
        if not self.cart:
            self.update_status("Cart is empty!")
            return

        # Prompt user to confirm or update customer name before placing order
        current_name = self.entry_name.get().strip() or "Aanvi"
        dialog = ctk.CTkInputDialog(
            text=f"Confirm customer name for this order:\n(Current: {current_name})",
            title="Push Order - Customer Name"
        )
        try:
            dialog.attributes("-topmost", True)
        except Exception:
            pass

        entered_name = dialog.get_input()
        if entered_name is None:
            self.update_status("Order cancelled by user.")
            return

        cust = entered_name.strip() if entered_name.strip() else current_name
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, cust)

        items = [{"product_id": pid, "quantity": it["qty"]} for pid, it in self.cart.items()]

        def worker():
            try:
                res = requests.post(f"{API_BASE}/order", json={"customer_name": cust, "items": items}, timeout=5)
                if res.status_code == 201:
                    data = res.json()
                    def on_success():
                        self.cart.clear()
                        self.render_cart()
                        self.load_products()
                        self.update_status(f"Order #{data.get('order_id')} committed to SQLite for {cust}!")
                    self.after(0, on_success)
                else:
                    err_msg = res.json().get("error", "Transaction failed")
                    self.update_status(f"Order failed: {err_msg}")
            except Exception as e:
                self.update_status(f"Order error: {e}")

        threading.Thread(target=worker, daemon=True).start()


if __name__ == "__main__":
    app = Fashion45DesktopApp()
    app.mainloop()
