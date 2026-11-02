-- Скрипт базы данных учебного проекта «Обувной магазин»
-- PostgreSQL 14+

CREATE DATABASE db_for_store;

\c db_for_store

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    user_role VARCHAR(50) NOT NULL,
    user_name VARCHAR(150),
    user_login VARCHAR(100) UNIQUE NOT NULL,
    user_password VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_article VARCHAR(20) UNIQUE NOT NULL,
    product_category VARCHAR(100),
    product_name VARCHAR(200) NOT NULL,
    product_information TEXT,
    product_creator VARCHAR(150),
    product_supplier VARCHAR(150),
    product_cost NUMERIC(12, 2) NOT NULL,
    product_unit VARCHAR(20),
    product_count INTEGER NOT NULL DEFAULT 0,
    product_sale INTEGER,
    product_picture VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS pvz (
    pvz_id SERIAL PRIMARY KEY,
    pvz_address VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    order_article VARCHAR(50) NOT NULL,
    order_status VARCHAR(50),
    order_pvz_id_fk INTEGER REFERENCES pvz(pvz_id),
    order_create_date DATE,
    order_delivery_date DATE
);
