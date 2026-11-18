# Установка и запуск ShoeStore

Комплект поставки содержит Windows-сборку приложения «Магазин обуви»
(ShoeStore.exe), файлы развёртывания PostgreSQL в Docker и образцы
конфигурации. **База данных не входит в EXE**: PostgreSQL запускается
отдельно через Docker Compose.

## Состав комплекта

```
ShoeStore-release/
├── application/ShoeStore/     сборка onedir: ShoeStore.exe + _internal/
├── deployment/
│   ├── compose.yaml           описание сервисов db и db-check
│   ├── .env.example           шаблон переменных окружения
│   └── database/shoe_store.sql   SQL-скрипт создания таблиц
├── config.ini.example         образец настройки подключения
├── README.md                  описание проекта
└── INSTALL.md                 этот файл
```

## Требования

- Windows 10/11, 64-разрядная;
- Docker Desktop с Linux-контейнерами и Docker Compose v2
  (`docker --version`, `docker compose version`);
- свободный порт 5433 (или измените `POSTGRES_HOST_PORT` в `.env`);
- права на запись в каталог комплекта (для `config.ini`).

## 1. Подготовка базы данных

1. Перейдите в каталог `deployment`:
   ```powershell
   cd deployment
   ```
2. Создайте `.env` по образцу и укажите свой локальный пароль:
   ```powershell
   Copy-Item .env.example .env
   ```
   Отредактируйте в `.env` строку `POSTGRES_PASSWORD=...`.
   Пароль не публикуйте и не передавайте вместе с архивом.
3. Запустите инфраструктуру:
   ```powershell
   docker compose up -d
   docker compose ps          # db должен быть healthy
   ```
4. **Только для новой пустой базы** импортируйте SQL-скрипт
   (подробнее — практика №12; база `db_for_store` создаётся скриптом):
   ```powershell
   docker compose cp ./database/shoe_store.sql db:/tmp/shoe_store.sql
   docker compose exec -T db psql -v ON_ERROR_STOP=1 -U shoe_user -d db_for_store -f /tmp/shoe_store.sql
   ```
   Если база уже заполнена, повторный импорт без проверки недопустим —
   в скрипте используется `CREATE DATABASE`, который вернёт ошибку
   `already exists`.
5. Проверьте подключение сервисом db-check:
   ```powershell
   docker compose run --rm db-check
   ```
   Ожидается строка `OK: база=db_for_store; таблиц=N`.
   Состояние `Exited (0)` после проверки — нормальное.

## 2. Настройка приложения

1. В каталоге `application/ShoeStore` (рядом с `ShoeStore.exe`) создайте
   `config.ini` по образцу `config.ini.example` из корня комплекта:
   ```ini
   [database]
   host = 127.0.0.1
   port = 5433
   name = db_for_store
   user = shoe_user
   password = ВАШ_ЛОКАЛЬНЫЙ_ПАРОЛЬ
   ```
2. Файл `config.ini` читается **из каталога, где находится ShoeStore.exe**
   (в упакованном режиме путь определяется через `sys.executable`),
   поэтому его можно менять без пересборки приложения.
   Пароль в `config.ini` — локальный, в репозиторий и архив он не входит.

## 3. Запуск приложения

Откройте `application/ShoeStore/ShoeStore.exe` (двойным щелчком или из
PowerShell). При первом запуске откроется окно авторизации; вход возможен
под учебной учётной записью из базы или в режиме гостя.

> Важно: переносите и запускайте **весь каталог** `ShoeStore` целиком.
> Один EXE без подкаталога `_internal` не работает (режим onedir).

## 4. Проверка

- окно авторизации открывается, логотип отображается (ресурсы включены
  в сборку);
- после входа каталог загружается из PostgreSQL — видны реальные товары,
  цены и остатки;
- при остановленной базе приложение завершается с сообщением об ошибке
  подключения `psycopg2.OperationalError` — это ожидаемое поведение
  без базы; после запуска БД приложение снова работает.

## 5. Остановка

```powershell
cd deployment
docker compose stop
```

`docker compose stop` останавливает контейнеры, данные в томе `db_data`
сохраняются. **Не используйте `docker compose down -v`** без резервной
копии: команда удаляет именованный том и данные базы.

## Типичные проблемы

| Симптом | Причина | Действие |
|---|---|---|
| EXE не запускается | Скопирован только EXE | Скопировать весь каталог onedir `ShoeStore` |
| Нет изображений | Ресурсы не попали в сборку | Использовать полный комплект из `application/ShoeStore` |
| «Не найден файл config.ini» | Файл отсутствует рядом с EXE | Создать `config.ini` по образцу в каталоге с `ShoeStore.exe` |
| Ошибка подключения к БД | Docker остановлен, неверный порт/пароль | `docker compose ps`, сверить `127.0.0.1:5433` в `config.ini` |
| `port is already allocated` | Порт 5433 занят | Изменить `POSTGRES_HOST_PORT` в `.env` и порт в `config.ini` |
| `relation already exists` | Повторный импорт SQL | Не повторять импорт; проверить состояние базы |

## Диагностика

```powershell
docker compose ps                 # состояние сервисов
docker compose logs --tail=40 db  # журналы PostgreSQL
docker compose port db 5432       # опубликованный адрес (127.0.0.1:5433)
docker compose run --rm db-check  # проверка подключения
```
