# V2Hub Telegram Bot

Telegram-бот для управления VPN-подключениями через сервис **V2Hub**.
Основной интерфейс — Mini App (панель управления), доступная прямо из бота.

## Что умеет бот

- При первом запуске **автоматически создаёт токен** — пользователю не нужно нажимать лишних кнопок
- Позволяет обновить токен (старый деактивируется, Mini App переключается автоматически)

## Структура

```
├── main.py                  # точка входа, регистрация роутеров
├── config.py                # настройки через .env (pydantic-settings)
├── locales/
│   └── ru.py                # все тексты и подписи кнопок на русском
├── db/
│   ├── engine.py            # async SQLAlchemy engine + init_db
│   ├── models.py            # ORM-модели
│   └── crud.py              # CRUD-хелперы
├── handlers/
│   ├── start.py             # /start: главное меню + автосоздание токена
│   ├── token.py             # /token: просмотр/обновление токена
│   ├── support.py           # /support
│   └── help.py              # /help
├── services/
│   ├── v2hub.py             # фасад над v2hub-admin (AsyncAdminClient)
│   └── keyboards.py         # фабрики inline-клавиатур + передача токена в Mini App
├── middlewares/
│   └── throttle.py          # rate-limit по user_id
├── Dockerfile
└── docker-compose.yml
```

## Быстрый старт

```bash
cp .env.example .env
# заполните .env своими значениями
docker compose up -d
```

### Без Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Команды бота

| Команда    | Описание                                     |
| ---------- | -------------------------------------------- |
| `/start`   | Главное меню (токен создаётся автоматически) |
| `/token`   | Просмотр и обновление токена                 |
| `/support` | Написать в поддержку                         |
| `/help`    | Справка                                      |
