# ShoeShop — система оформления заказов обуви

Учебный проект: десктопное приложение для просмотра каталога обуви
и оформления заказов.

## Возможности

- просмотр каталога моделей обуви с ценой, скидкой и наличием;
- сортировка, фильтрация и поиск товаров;
- оформление заказа авторизованным пользователем;
- управление заказами (менеджер и администратор);
- вход по логину и паролю или режим гостя.

## Требования

- Python 3.10+
- PostgreSQL 14
- библиотеки из файла `requirements.txt`

## Установка и запуск

1. Клонировать репозиторий: `git clone https://github.com/elwward/shoe_shop.git`
2. Создать окружение и установить зависимости:
   `python -m venv venv`, `venv\Scripts\activate`, `pip install -r requirements.txt`
3. Создать базу данных и загрузить скрипт `database/shoe_store.sql`.
4. Скопировать `config.ini.example` в `config.ini` и указать параметры подключения.
5. Запустить приложение: `python main.py`

## Структура репозитория

- `app/` — модули приложения (вход, товары, заказы, работа с БД)
- `resources/` — изображения, логотип, иконка
- `database/` — скрипт базы данных и файлы импорта Excel
- `docker/db-check/` — вспомогательный сервис проверки БД (Dockerfile, check_db.py)
- `docs/` — ER-диаграмма

## Запуск PostgreSQL через Docker Compose

### Предварительные требования

- Docker Desktop с Linux-контейнерами (Docker Engine + Compose v2):
  `docker --version`, `docker compose version`
- Git-репозиторий проекта

### Настройка .env

1. Скопируйте `.env.example` в `.env`:
   `Copy-Item .env.example .env`
2. Замените `POSTGRES_PASSWORD` на собственный локальный пароль.
   Файл `.env` исключён из Git через `.gitignore` — настоящий пароль в
   репозиторий не попадает.

### Команды запуска

```powershell
docker compose config --quiet        # проверка конфигурации
docker compose up --build -d         # запуск сервисов db и db-check
docker compose ps                    # состояние сервисов
docker compose logs --tail=40 db     # журналы PostgreSQL
docker compose run --rm db-check     # одноразовая проверка подключения
```

Сервис `db` (PostgreSQL 14) публикуется на `127.0.0.1:5433` (порт Windows
задаётся переменной `POSTGRES_HOST_PORT`, порт внутри контейнера — 5432).
Сервис `db-check` — одноразовый диагностический контейнер: при успешном
выполнении его статус `Exited (0)` является нормальным, в журнале должна
быть строка вида `OK: база=db_for_store; таблиц=N`.

### Импорт базы данных

SQL-скрипт сам создаёт базу `db_for_store` и переключается в неё
(`CREATE DATABASE` + `\c`). При первом запуске, когда база ещё не создана:

```powershell
docker compose cp database/shoe_store.sql db:/tmp/shoe_store.sql
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U shoe_user -d shoe_store -f /tmp/shoe_store.sql
```

При чистом пересоздании контейнера база `db_for_store` создаётся при
инициализации, поэтому первую команду скрипта (`CREATE DATABASE`)
игнорируют — импорт выполняют без `ON_ERROR_STOP`:

```powershell
docker compose exec -T db psql -U shoe_user -d postgres -f /tmp/shoe_store.sql
```

Заполнение таблиц данными из Excel:

```powershell
python app\import_from_excel.py
```

### Подключение приложения

В `config.ini` укажите:

```ini
[database]
host = localhost
port = 5433
name = db_for_store
user = shoe_user
password = ВАШ_ЛОКАЛЬНЫЙ_ПАРОЛЬ
```

Порт 5433 занят? Измените `POSTGRES_HOST_PORT` в `.env` и перезапустите
Compose, затем обновите порт в `config.ini`.

### Остановка

```powershell
docker compose stop    # остановить сервисы (данные сохраняются)
docker compose start   # запустить снова
```

Не выполняйте `docker compose down -v` без необходимости: именованный
том для данных пока не настроен (планируется в практической работе №13),
поэтому при пересоздании контейнера `db` данные потребуется
импортировать заново.

## Постоянное хранение и сети

### Именованный том

Данные PostgreSQL хранятся в именованном томе `db_data`
(фактическое имя с префиксом проекта — `shoe_shop_db_data`),
подключённом к `/var/lib/postgresql/data` в сервисе `db`. Том
сохраняется при остановке, удалении и пересоздании контейнеров
(`docker compose down`, `up -d --force-recreate db`).

### Резервное копирование и восстановление

```powershell
# Резервная копия (каталог backups/ исключён из Git)
mkdir backups
docker compose exec db pg_dump -U shoe_user -d db_for_store -f /tmp/shoe_store_before_volume.sql
docker compose cp db:/tmp/shoe_store_before_volume.sql ./backups/shoe_store_before_volume.sql

# Восстановление (в пустую базу нового тома)
docker compose cp ./backups/shoe_store_before_volume.sql db:/tmp/restore.sql
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U shoe_user -d db_for_store -f /tmp/restore.sql
```

Восстановление выполняют только в пустую базу. Если таблицы уже
существуют (`relation already exists`), повторный импорт не выполняют,
пока не выяснено состояние тома.

### Сеть

Оба сервиса подключены к пользовательской bridge-сети `shoe-backend`:
внутри неё контейнеры обращаются по именам сервисов (db-check — к
`db:5432`). Порт PostgreSQL опубликован только на локальном интерфейсе:
`127.0.0.1:5433:5432` — приложение Windows подключается к `localhost:5433`.
Публикация `0.0.0.0:5433:5432` для локальной учебной базы не требуется.

```powershell
docker network ls                          # сеть shoe_shop_shoe-backend
docker network inspect shoe_shop_shoe-backend
docker compose port db 5432                # 127.0.0.1:5433
```

### Разница команд остановки

| Команда | Результат |
|---|---|
| `docker compose stop` | Останавливает контейнеры, том сохраняется |
| `docker compose down` | Удаляет контейнеры и сети проекта, именованный том сохраняется |
| `docker compose down -v` | Удаляет также именованные тома — **не выполнять**: приведёт к потере базы (есть резервная копия в `backups/`) |

### Автор

Григорьян С. А., группа ЩПКО-02-23
