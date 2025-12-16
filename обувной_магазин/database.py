# database.py

import psycopg2
import random
import string

# Настройки подключения (можно вынести в .env позже)
DB_CONFIG = {
    'dbname': 'db_for_store',
    'user': 'postgres',
    'password': 'htpjyfyc',
    'host': 'localhost',
    'port': 5432
}


def generate_product_article():
    """Генерирует артикул в формате: LNNNLN (например, S213E3)"""
    letters = string.ascii_uppercase  # A-Z
    part1 = random.choice(letters)
    part2 = str(random.randint(100, 999))  # 3 цифры
    part3 = random.choice(letters)
    part4 = str(random.randint(0, 9))
    return part1 + part2 + part3 + part4

def article_exists(article):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM products WHERE product_article = %s;", (article,))
    exists = cur.fetchone() is not None
    cur.close()
    conn.close()
    return exists

def generate_unique_product_article():
    while True:
        article = generate_product_article()
        if not article_exists(article):
            return article

def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def authenticate_user(login: str, password: str):
    """
    Возвращает роль пользователя, если логин/пароль верны.
    Иначе — None.
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT user_role FROM users
            WHERE user_login = %s AND user_password = %s;
        """, (login, password))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        # В продакшене — логируйте ошибку, но не показывайте пользователю
        print(f"Ошибка подключения к БД: {e}")
        return None

# database.py
def get_user_full_name(login: str):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_name FROM users WHERE user_login = %s;", (login,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result and result[0] else login  # если ФИО нет — возвращаем логин
    except:
        return login

# --- Товары ---
def get_all_products():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT product_id, product_article, product_category, product_name, product_information,
               product_creator, product_supplier, product_cost, product_unit,
               product_count, product_sale, product_picture
        FROM products
        ORDER BY product_id;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    products = []
    for row in rows:
        products.append({
            "id": row[0],
            "article": row[1],  # <-- Добавлено! Это ключевая строка
            "category": row[2],
            "name": row[3],
            "description": row[4],
            "manufacturer": row[5],
            "supplier": row[6],
            "price": row[7],
            "unit": row[8],
            "stock": row[9],
            "discount": str(row[10]) if row[10] is not None else None,
            "photo_path": row[11] or "picture.png"
        })
    return products

def save_product(product_data):
    conn = get_connection()
    cur = conn.cursor()
    if product_data.get("id") is None:
        # Новый товар
        cur.execute("""
            INSERT INTO products (
                product_article, product_category, product_name, product_information,
                product_creator, product_supplier, product_cost, product_unit,
                product_count, product_sale, product_picture
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING product_id;
        """, (
            product_data["article"],
            product_data["category"],
            product_data["name"],
            product_data["description"],
            product_data["manufacturer"],
            product_data["supplier"],
            product_data["price"],
            product_data["unit"],
            product_data["stock"],
            int(product_data["discount"]) if product_data["discount"] else None,
            product_data["photo_path"]
        ))
        new_id = cur.fetchone()[0]
        product_data["id"] = new_id
        print("INSERT выполнен")
    else:
        # Обновление
        cur.execute("""
            UPDATE products SET
                product_article = %s,
                product_category = %s,
                product_name = %s,
                product_information = %s,
                product_creator = %s,
                product_supplier = %s,
                product_cost = %s,
                product_unit = %s,
                product_count = %s,
                product_sale = %s,
                product_picture = %s
            WHERE product_id = %s;
        """, (
            product_data["article"],
            product_data["category"],
            product_data["name"],
            product_data["description"],
            product_data["manufacturer"],
            product_data["supplier"],
            product_data["price"],
            product_data["unit"],
            product_data["stock"],
            int(product_data["discount"]) if product_data["discount"] else None,
            product_data["photo_path"],
            product_data["id"]
        ))
        print("UPDATE выполнен")
    conn.commit()
    cur.close()
    conn.close()
    return product_data

def delete_product(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE product_id = %s;", (product_id,))
    conn.commit()
    cur.close()
    conn.close()

# --- Заказы ---

def get_all_orders():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT order_id, order_article, order_status, order_pvz_id_fk, order_create_date, order_delivery_date
        FROM orders
        ORDER BY order_id;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    orders = []
    for row in rows:
        orders.append({
            "id": row[0],
            "article": row[1],
            "status": row[2],
            "pickup_address": get_pvz_address(row[3]),  # Связь с таблицей pvz
            "order_date": row[4].strftime("%Y-%m-%d"),
            "delivery_date": row[5].strftime("%Y-%m-%d")
        })
    return orders

def get_pvz_address(pvz_id):
    """Получает адрес пункта выдачи по ID"""
    if pvz_id is None:
        return "Адрес не указан"
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT pvz_address FROM pvz WHERE pvz_id = %s;", (pvz_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else "Адрес не найден"

def save_order(order_data):
    conn = get_connection()
    cur = conn.cursor()
    if order_data.get("id") is None:
        # Новый заказ
        cur.execute("""
            INSERT INTO orders (
                order_article, order_status, order_pvz_id_fk, order_create_date, order_delivery_date
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING order_id;
        """, (
            order_data["article"],
            order_data["status"],
            get_pvz_id_by_address(order_data["pickup_address"]),  # Преобразуем адрес в ID
            order_data["order_date"],
            order_data["delivery_date"]
        ))
        new_id = cur.fetchone()[0]
        order_data["id"] = new_id
    else:
        # Обновление
        cur.execute("""
            UPDATE orders SET
                order_article = %s,
                order_status = %s,
                order_pvz_id_fk = %s,
                order_create_date = %s,
                order_delivery_date = %s
            WHERE order_id = %s;
        """, (
            order_data["article"],
            order_data["status"],
            get_pvz_id_by_address(order_data["pickup_address"]),
            order_data["order_date"],
            order_data["delivery_date"],
            order_data["id"]
        ))
    conn.commit()
    cur.close()
    conn.close()
    return order_data

def get_pvz_id_by_address(address):
    """Находит ID пункта выдачи по адресу, или создает новый, если нет"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT pvz_id FROM pvz WHERE pvz_address = %s;", (address,))
    result = cur.fetchone()
    if result:
        pvz_id = result[0]
    else:
        # Создаем новый пункт выдачи
        cur.execute("INSERT INTO pvz (pvz_address) VALUES (%s) RETURNING pvz_id;", (address,))
        pvz_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return pvz_id

def delete_order(order_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM orders WHERE order_id = %s;", (order_id,))
    conn.commit()
    cur.close()
    conn.close()