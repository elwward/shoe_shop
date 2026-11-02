from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

from database import load_db_config

DATA_DIR = Path(__file__).resolve().parent.parent / "database"


def import_data():
    conn = psycopg2.connect(**load_db_config())
    cur = conn.cursor()

    try:

        # PVZ
        pvz_df = pd.read_excel(DATA_DIR / 'Пункты выдачи_import.xlsx', header=None)
        pvz_records = [(row[0],) for _, row in pvz_df.iterrows()]
        insert_pvz_query = "INSERT INTO pvz (pvz_address) VALUES %s"
        execute_values(cur, insert_pvz_query, pvz_records)
        conn.commit()

        # Users
        users_df = pd.read_excel(DATA_DIR / 'user_import.xlsx')
        users_df.rename(columns={
            'Роль сотрудника': 'user_role',
            'ФИО': 'user_name',
            'Логин': 'user_login',
            'Пароль': 'user_password'
        }, inplace=True)
        users_records = [
            (row['user_role'], row['user_name'], row['user_login'], row['user_password'])
            for _, row in users_df.iterrows()
        ]
        insert_users_query = """
            INSERT INTO users (user_role, user_name, user_login, user_password)
            VALUES %s ON CONFLICT DO NOTHING
        """
        execute_values(cur, insert_users_query, users_records)
        conn.commit()

        # Products
        products_df = pd.read_excel(DATA_DIR / 'Tovar.xlsx')
        products_df.rename(columns={
            'Артикул': 'product_article',
            'Наименование товара': 'product_name',
            'Единица измерения': 'product_unit',
            'Цена': 'product_cost',
            'Поставщик': 'product_supplier',
            'Производитель': 'product_creator',
            'Категория товара': 'product_category',
            'Действующая скидка': 'product_sale',
            'Кол-во на складе': 'product_count',
            'Описание товара': 'product_information',
            'Фото': 'product_picture'
        }, inplace=True)

        products_df['product_cost'] = pd.to_numeric(products_df['product_cost'], errors='coerce')
        products_df['product_sale'] = pd.to_numeric(products_df['product_sale'], errors='coerce').fillna(0).astype(int)
        products_df['product_count'] = pd.to_numeric(products_df['product_count'], errors='coerce').fillna(0).astype(int)

        products_records = [
            (
                row['product_article'],
                row['product_name'],
                row['product_unit'],
                row['product_cost'],
                row['product_supplier'],
                row['product_creator'],
                row['product_category'],
                row['product_sale'],
                row['product_count'],
                row['product_information'],
                row['product_picture']
            )
            for _, row in products_df.iterrows()
        ]
        insert_products_query = """
            INSERT INTO products (
                product_article, product_name, product_unit, product_cost,
                product_supplier, product_creator, product_category, product_sale,
                product_count, product_information, product_picture
            ) VALUES %s ON CONFLICT DO NOTHING
        """
        execute_values(cur, insert_products_query, products_records)
        conn.commit()

        print("Импорт Orders и Order_Products...")

        cur.execute("SELECT product_article, product_id FROM products;")
        product_id_map = dict(cur.fetchall())


        cur.execute("SELECT pvz_id, pvz_id FROM pvz;")
        pvz_id_map = dict(cur.fetchall())

        orders_df = pd.read_excel(DATA_DIR / 'Заказ_import.xlsx')

        col_mapping = {}
        for col in orders_df.columns:
            if 'Номер заказа' in col or 'номер' in col.lower() and 'заказ' in col.lower():
                col_mapping[col] = 'order_id'
            elif 'Артикул заказа' in col or 'артикул' in col.lower() and 'заказ' in col.lower():
                col_mapping[col] = 'order_article_str'
            elif 'Дата заказа' in col or 'дата' in col.lower() and 'заказ' in col.lower():
                col_mapping[col] = 'order_create_date'
            elif 'Дата доставки' in col or 'дата' in col.lower() and 'доставк' in col.lower():
                col_mapping[col] = 'order_delivery_date'
            elif 'Адрес пункта выдачи' in col or 'адрес' in col.lower() and 'пункт' in col.lower():
                col_mapping[col] = 'order_pvz_id'  # Теперь это ID, а не адрес
            elif 'ФИО авторизованного клиента' in col or 'фио' in col.lower() and 'клиент' in col.lower():
                col_mapping[col] = 'order_user_name'
            elif 'Код для получения' in col or 'код' in col.lower() and 'получ' in col.lower():
                col_mapping[col] = 'order_code'
            elif 'Статус заказа' in col or 'статус' in col.lower() and 'заказ' in col.lower():
                col_mapping[col] = 'order_status'

        # Переименуем столбцы
        orders_df.rename(columns=col_mapping, inplace=True)

        required_cols = ['order_id', 'order_article_str', 'order_create_date', 'order_delivery_date',
                         'order_pvz_id', 'order_user_name', 'order_code', 'order_status']
        missing_cols = [col for col in required_cols if col not in orders_df.columns]
        if missing_cols:
            raise ValueError(f"Не найдены следующие обязательные столбцы: {missing_cols}")

        orders_df['order_create_date'] = pd.to_datetime(orders_df['order_create_date'], format='%d.%m.%Y', errors='coerce').dt.date
        orders_df['order_delivery_date'] = pd.to_datetime(orders_df['order_delivery_date'], format='%d.%m.%Y', errors='coerce').dt.date

        orders_df['order_pvz_id'] = pd.to_numeric(orders_df['order_pvz_id'], errors='coerce').fillna(0).astype(int)

        orders_records = []
        order_products_records = []

        for _, row in orders_df.iterrows():
            if not all([row['order_id'], row['order_create_date'], row['order_delivery_date'],
                       row['order_pvz_id'], row['order_user_name'], row['order_code'], row['order_status']]):
                continue


            pvz_id = int(row['order_pvz_id'])


            if pvz_id not in pvz_id_map:
                print(f"Предупреждение: Не найден PVZ с ID '{pvz_id}' для заказа {row['order_id']}")
                continue


            order_record = (
                int(row['order_id']),
                row['order_article_str'],
                row['order_create_date'],
                row['order_delivery_date'],
                pvz_id,
                row['order_user_name'],
                int(row['order_code']),
                row['order_status']
            )
            orders_records.append(order_record)


            article_str = row['order_article_str']
            if isinstance(article_str, str):
                parts = [part.strip() for part in article_str.split(',')]
                for i in range(0, len(parts), 2):
                    if i + 1 < len(parts):
                        product_article = parts[i]
                        count = int(parts[i + 1])
                        product_id = product_id_map.get(product_article)
                        if product_id is not None:
                            order_products_records.append((int(row['order_id']), product_id, count))
                        else:
                            print(f"Предупреждение: Не найден продукт с артикулом '{product_article}' для заказа {row['order_id']}")

        insert_orders_query = """
            INSERT INTO orders (
                order_id, order_article, order_create_date, order_delivery_date,
                order_pvz_id_fk, order_user_name, order_code, order_status
            ) VALUES %s ON CONFLICT DO NOTHING
        """
        execute_values(cur, insert_orders_query, orders_records)
        conn.commit()

        insert_order_products_query = """
            INSERT INTO order_products (order_id, product_id, count)
            VALUES %s ON CONFLICT DO NOTHING
        """
        execute_values(cur, insert_order_products_query, order_products_records)
        conn.commit()
        print(f"Импортировано {len(order_products_records)} связей заказ-продукт.")

        print("Импорт завершен успешно.")

    except Exception as e:
        print(f"Ошибка при импорте: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    import_data()