# ──────────────────────────────────────────────────────────────────────────────
# Locale: Russian (ru)
# ──────────────────────────────────────────────────────────────────────────────

# ── /start — первый визит ─────────────────────────────────────────────────────

WELCOME_NEW = (
    '<tg-emoji emoji-id="5906995262378741881">👋</tg-emoji> '
    "Привет, <b>{name}</b>!\n\n"
    "<b>v2hub</b> — ваш личный VPN-менеджер.\n\n"
    "Один раз подключите устройство по ссылке-подписке — "
    "и забудьте о ручной настройке навсегда. "
    "Все изменения применяются автоматически на каждом вашем устройстве: "
    "телефоне, ноутбуке, планшете и у членов семьи.\n\n"
    "Мы уже создали ваш персональный токен доступа 👇"
)

# ── /start — повторный визит ──────────────────────────────────────────────────

WELCOME_RETURNING = (
    '<tg-emoji emoji-id="5906995262378741881">👋</tg-emoji> '
    "С возвращением, <b>{name}</b>!\n\n"
    "Всё под контролем — управляйте подключениями через панель."
)

# ── Токен — показывается сразу после приветствия новому пользователю ──────────

TOKEN_FIRST_TIME = (
    '<tg-emoji emoji-id="6005570495603282482">🔑</tg-emoji> '
    "<b>Ваш токен доступа готов!</b>\n\n"
    "<blockquote><code>{token}</code></blockquote>\n\n"
    "Скопируйте токен и вставьте его при первом входе в панель управления — "
    "это нужно сделать один раз.\n\n"
    '<tg-emoji emoji-id="5881702736843511327">⚠️</tg-emoji> '
    "Никому не передавайте токен: он даёт полный доступ к вашему аккаунту."
)

# ── Токен — просмотр через /token ─────────────────────────────────────────────

TOKEN_NONE = (
    '<tg-emoji emoji-id="6005570495603282482">🔑</tg-emoji> <b>Токен доступа</b>\n\n'
    "У вас пока нет токена — без него войти в панель не получится.\n"
    "Нажмите кнопку ниже, чтобы получить его прямо сейчас."
)

TOKEN_INFO = (
    '<tg-emoji emoji-id="6005570495603282482">🔑</tg-emoji> <b>Ваш токен доступа</b>\n\n'
    "<blockquote><code>{token}</code></blockquote>\n\n"
    '<tg-emoji emoji-id="5881702736843511327">⚠️</tg-emoji> '
    "Никому не передавайте токен: он даёт полный доступ к вашему аккаунту."
)

TOKEN_GENERATING = "⏳ Создаём токен…"

TOKEN_CREATED = (
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> '
    "<b>Токен готов!</b>\n\n"
    "<blockquote><code>{token}</code></blockquote>\n\n"
    "Скопируйте его и вставьте при входе в панель управления.\n\n"
    '<tg-emoji emoji-id="5881702736843511327">⚠️</tg-emoji> '
    "Никому не передавайте токен: он даёт полный доступ к вашему аккаунту."
)

TOKEN_REFRESHING = "⏳ Обновляем токен…"

TOKEN_REFRESHED = (
    '<tg-emoji emoji-id="6005843436479975944">🔄</tg-emoji> '
    "<b>Токен обновлён!</b>\n\n"
    "<blockquote><code>{token}</code></blockquote>\n\n"
    "Старый токен деактивирован — вставьте новый в панели управления.\n\n"
    '<tg-emoji emoji-id="5881702736843511327">⚠️</tg-emoji> '
    "Никому не передавайте токен: он даёт полный доступ к вашему аккаунту."
)

TOKEN_NO_ACTIVE = "У вас нет активного токена."

TOKEN_ERROR_GENERATE = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось создать токен:\n<code>{error}</code>\n\n"
    "Попробуйте позже или напишите в поддержку."
)

TOKEN_ERROR_REFRESH = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось обновить токен:\n<code>{error}</code>\n\n"
    "Попробуйте позже или напишите в поддержку."
)

# ── /help ─────────────────────────────────────────────────────────────────────

HELP_TEXT = (
    '<tg-emoji emoji-id="6030848053177486888">❓</tg-emoji> <b>Справка</b>\n\n'
    "<b>v2hub</b> — сервис управления VPN-подключениями. "
    "Настройте устройство один раз, а все обновления будут применяться автоматически.\n\n"
    "<b>Команды:</b>\n"
    "<blockquote>/start — главное меню\n"
    "/token — токен доступа\n"
    "/support — написать в поддержку</blockquote>\n\n"
    "<b>Как начать:</b>\n"
    "1. Получите токен через /token\n"
    "2. Откройте панель и вставьте токен при входе\n"
    "3. Добавьте устройства — изменения будут применяться автоматически\n\n"
    "При обновлении токена старый деактивируется. "
    "Не забудьте вставить новый в панели."
)

# ── /support ──────────────────────────────────────────────────────────────────

SUPPORT_TEXT = (
    '<tg-emoji emoji-id="5936017305585586269">📩</tg-emoji> <b>Поддержка</b>\n\n'
    "Что-то пошло не так или есть вопрос?\n"
    "Мы на связи — напишите нам, и мы разберёмся.\n\n"
    "Чем подробнее опишете ситуацию, тем быстрее поможем."
)

# ── Провайдер: раздел "Стать провайдером" ──────────────────────────────────────

PROVIDER_INTRO = (
    '<tg-emoji emoji-id="6005570495603282482">🏷</tg-emoji> <b>Провайдер</b>\n\n'
    "Провайдер — партнёр v2hub с собственным VPN-сервисом, который может "
    "подключать пользователей и управлять их подписками через API.\n\n"
    "<b>Чтобы стать провайдером, нужно:</b>\n"
    "<blockquote>• иметь действующий VPN-сервис;\n"
    "• либо чётко подтверждённое намерение построить сервис на базе v2hub</blockquote>\n\n"
    "Роль провайдера выдаётся только администратором. "
    "Напишите в поддержку, для получения собственного провайдера."
)

# ── Провайдер: раздел для пользователей с ролью provider ───────────────────────

PROVIDER_INFO = (
    '<tg-emoji emoji-id="6005570495603282482">🏷</tg-emoji> <b>Ваш провайдер</b>\n\n'
    "<b>Название:</b> {provider_name}\n"
    "<b>URL:</b> {provider_url}"
)

PROVIDER_TOKEN_INFO = (
    '<tg-emoji emoji-id="6005570495603282482">🔑</tg-emoji> <b>Токен провайдера</b>\n\n'
    "<blockquote><code>{token}</code></blockquote>\n\n"
    '<tg-emoji emoji-id="5881702736843511327">⚠️</tg-emoji> '
    "Никому не передавайте этот токен: он даёт полный доступ к API вашего провайдера."
)

PROVIDER_TOKEN_REFRESHING = "⏳ Обновляем токен провайдера…"

PROVIDER_TOKEN_REFRESHED = (
    '<tg-emoji emoji-id="6005843436479975944">🔄</tg-emoji> '
    "<b>Токен провайдера обновлён!</b>\n\n"
    "<blockquote><code>{token}</code></blockquote>\n\n"
    "Старый токен деактивирован."
)

PROVIDER_TOKEN_ERROR_REFRESH = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось обновить токен провайдера:\n<code>{error}</code>"
)

PROVIDER_NOT_FOUND_FOR_ROLE = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Ваш провайдерский аккаунт не найден. Обратитесь в поддержку."
)

# ── Провайдер: публичная страница (/start provider_*) ───────────────────────────

PROVIDER_PUBLIC_INFO = (
    '<tg-emoji emoji-id="6005570495603282482">🏷</tg-emoji> <b>{provider_name}</b>\n\n'
    "<b>URL:</b> {provider_url}\n"
    "<b>Статус авторизации:</b> {status}"
)

PROVIDER_STATUS_NONE = "не авторизован"
PROVIDER_STATUS_PENDING = "ожидает подтверждения"
PROVIDER_STATUS_APPROVED = "подключён"
PROVIDER_STATUS_REVOKED = "отключён"

PROVIDER_NOT_FOUND = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Провайдер <code>{provider_name}</code> не найден."
)

# ── Провайдер: подключение по ссылке conn_* ─────────────────────────────────────

PROVIDER_CONNECTION_REQUEST = (
    '<tg-emoji emoji-id="6005570495603282482">🏷</tg-emoji> '
    "<b>Запрос на подключение провайдера</b>\n\n"
    "<b>{provider_name}</b>\n"
    "URL: {provider_url}\n\n"
    "Провайдер запрашивает доступ на добавление подписок.\n\n"
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> '
    "Подключение провайдера <b>не затрагивает</b> ваши личные подписки — "
    "создаются новые рядом с ними.\n\n"
    '<tg-emoji emoji-id="5881702736843511327">🔒</tg-emoji> '
    "Подтвердите или отклоните запрос ниже."
)

PROVIDER_CONNECTION_LINK_INVALID = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Ссылка подключения недействительна или устарела. "
    "Попросите провайдера прислать новую ссылку.\n\n<code>{error}</code>"
)

# ── Провайдер: действия ──────────────────────────────────────────────────────

PROVIDER_APPROVING = "⏳ Подтверждаем подключение…"

PROVIDER_APPROVED = (
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> '
    "Провайдер <b>{provider_name}</b> подключён."
)

PROVIDER_APPROVE_ERROR = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось подтвердить подключение:\n<code>{error}</code>"
)

PROVIDER_LIMIT_ERROR = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Достигнут максимальный лимит подключённых провайдеров.\n"
    "Отключите неиспользуемого провайдера, чтобы подключить новый."
)

PROVIDER_REJECTING = "⏳ Отклоняем запрос…"

PROVIDER_REJECTED = (
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> '
    "Запрос от провайдера <b>{provider_name}</b> отклонён."
)

PROVIDER_REJECT_ERROR = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось отклонить запрос:\n<code>{error}</code>"
)

PROVIDER_DISCONNECTING = "⏳ Отключаем провайдера…"

PROVIDER_DISCONNECTED_DELETED = (
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> '
    "Провайдер <b>{provider_name}</b> отключён и удалён из списка ваших провайдеров."
)

PROVIDER_DISCONNECTED_REVOKED = (
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> '
    "Провайдер <b>{provider_name}</b> отключён. "
)

PROVIDER_DISCONNECT_ERROR = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось отключить провайдера:\n<code>{error}</code>"
)

# ── Провайдер: список моих провайдеров ──────────────────────────────────────────

MY_PROVIDERS_EMPTY = (
    '<tg-emoji emoji-id="6005570495603282482">🏷</tg-emoji> <b>Мои провайдеры</b>\n\n'
    "У вас пока нет подключённых провайдеров."
)

MY_PROVIDERS_TITLE = (
    '<tg-emoji emoji-id="6005570495603282482">🏷</tg-emoji> <b>Мои провайдеры</b>\n\n'
)

DEEP_LINK_INVALID = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> Ссылка повреждена или неполная.'
)

# ── Кнопки провайдера ────────────────────────────────────────────────────────

BTN_PROVIDER = "Провайдер"
BTN_MY_PROVIDERS = "Мои провайдеры"
BTN_PROVIDER_TOKEN = "Токен провайдера"
BTN_PROVIDER_REFRESH_TOKEN = "Обновить токен"
BTN_CONNECT = "Подключить"
BTN_REJECT = "Отклонить"
BTN_DISCONNECT = "Отключить"
BTN_CONTACT_SUPPORT = "Написать администратору"


# ── Расширенный набор кнопок ────────────────────────────────────────────────────────
BTN_EXTENDED_MENU = "Расширенное меню"
BTN_V2HUB_API = "О проекте"
BTN_V2HUB_GITHUB = "Наш GitHub"

# ── Throttle ──────────────────────────────────────────────────────────────────

THROTTLE_WARNING = (
    '<tg-emoji emoji-id="5891211339170326418">⏳</tg-emoji> '
    "Подождите немного перед следующей командой."
)

# ── Кнопки ───────────────────────────────────────────────────────────────────

BTN_OPEN_PANEL = "Открыть панель"
BTN_MY_TOKEN = "Мой токен"
BTN_GET_TOKEN = "Получить токен"
BTN_REFRESH_TOKEN = "Обновить токен"
BTN_HELP = "Помощь"
BTN_SUPPORT = "Поддержка"
BTN_BACK = "Назад"
BTN_MAIN_MENU = "Главное меню"
BTN_WRITE_SUPPORT = "Написать в поддержку"


# ── Кнопки Админа ───────────────────────────────────────────────────────────────────

BTN_ADMIN_PANEL = "Админ-панель"
BTN_ADMIN_PANEL_SETTINGS = "Настройки панели"
BTN_ADMIN_STATS = "Статистика"
BTN_ADMIN_USERS = "Пользователи"
BTN_ADMIN_PROVIDERS = "Провайдеры"
BTN_ADMIN_BROADCAST = "Рассылка"

BTN_ADMIN_STATS_DAY = "День"
BTN_ADMIN_STATS_WEEK = "Неделя"
BTN_ADMIN_STATS_MONTH = "Месяц"
BTN_ADMIN_STATS_ALL = "Все время"
BTN_ADMIN_STATS_OPTIONAL = "Указать дату"


# ── Статистика ───────────────────────────────────────────────────────────────────
ADMIN_STATS_SELECT = (
    '<tg-emoji emoji-id="5994378914636500516">📊</tg-emoji> '
    "Выберите период, за который хотите получить статистику:"
)

ADMIN_STATS_INFO = (
    '<tg-emoji emoji-id="5994378914636500516">📊</tg-emoji> '
    "Всего пользователей: <code>{total_users}</code>\n\n"
    "Статистика {period}:\n"
    '<tg-emoji emoji-id="5886412370347036129">👤</tg-emoji> '
    "Новых пользователей: <code>{new_users}</code>\n"
    '<tg-emoji emoji-id="6034923938486684992">⭐</tg-emoji> '
    "Новых подписок: <code>{new_subs}</code>"
)

ADMIN_STATS_GET_OPTIONAL_PERIOD = (
    '<tg-emoji emoji-id="5850317551090800862">⏱️</tg-emoji> '
    "Введите период в формате:\n"
    "<code>YYYY-MM-DD : YYYY-MM-DD</code>\n\n"
    "Можно указать только начало или конец периода:\n"
    "<code>YYYY-MM-DD :</code> — с указанной даты\n"
    "<code>: YYYY-MM-DD</code> — до указанной даты"
)

ADMIN_STATS_PERIOD_INVALID = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Неверный формат периода. Попробуйте ещё раз, например:\n"
    "<code>2026-01-01 : 2026-02-01</code>"
)

ADMIN_STATS_PERIOD_LABEL_DAY = "за последние сутки"
ADMIN_STATS_PERIOD_LABEL_WEEK = "за последнюю неделю"
ADMIN_STATS_PERIOD_LABEL_MONTH = "за последний месяц"
ADMIN_STATS_PERIOD_LABEL_ALL = "за всё время"
ADMIN_STATS_PERIOD_LABEL_CUSTOM = "в период с {start_date} по {end_date}"
ADMIN_STATS_PERIOD_LABEL_CUSTOM_START = "запуска"
ADMIN_STATS_PERIOD_LABEL_CUSTOM_END = "сегодняшний день"

ADMIN_STATS_ERROR = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось получить статистику:\n<code>{error}</code>"
)


# ── Админ-панель ─────────────────────────────────────────────────────────────

ADMIN_PANEL_TITLE = (
    '<tg-emoji emoji-id="5926783847453692661">🛠</tg-emoji> <b>Админ-панель</b>\n\nВыберите раздел:'
)


# ── Пользователи ─────────────────────────────────────────────────────────────

BTN_ADMIN_USER_CREATE = "Создать пользователя"

ADMIN_USERS_PROVIDERS_NOT_FOUND = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> У пользователя нет провайдеров.'
)

ADMIN_USERS_PROMPT = (
    '<tg-emoji emoji-id="5886412370347036129">👤</tg-emoji> '
    "Отправьте Telegram ID пользователя, которого хотите найти."
)

ADMIN_USERS_INVALID_ID = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "ID должен быть числом. Попробуйте ещё раз."
)

ADMIN_USERS_NOT_FOUND = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Пользователь с ID <code>{user_id}</code> не найден."
)

ADMIN_USERS_INFO = (
    '<tg-emoji emoji-id="5886412370347036129">👤</tg-emoji> '
    "Информация о пользователе:\n"
    "ID: <code>{user_id}</code>\n"
    "Токен: <tg-spoiler><code>{api_token}</code></tg-spoiler>\n"
    "Провайдер: <code>{provider_name}</code>\n"
    "Дата первого запуска бота: {created_at}\n"
    "Заблокирован в боте: {is_banned}"
)

ADMIN_USERS_UNKNOWN = "неизвестно"

BTN_ADMIN_USER_DELETE = "Удалить пользователя"

ADMIN_USERS_DELETE_CONFIRM = (
    '<tg-emoji emoji-id="6032636795387121097">⚠️</tg-emoji> '
    "Удалить пользователя <code>{user_id}</code>? Это действие необратимо: "
    "будет удалён его аккаунт v2hub и вся связанная с ним информация."
)

ADMIN_USERS_DELETED = (
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> '
    "Пользователь <code>{user_id}</code> удалён."
)

ADMIN_USERS_DELETE_ERROR = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось удалить пользователя:\n<code>{error}</code>"
)


# ── Рассылка ─────────────────────────────────────────────────────────────────

BTN_ADMIN_BROADCAST_MODE_COPY = "Переслать как есть"
BTN_ADMIN_BROADCAST_MODE_COMPOSE = "Собрать сообщение"

ADMIN_BROADCAST_SELECT_MODE = (
    '<tg-emoji emoji-id="5771868281212245617">📢</tg-emoji> '
    "Как вы хотите подготовить рассылку?\n\n"
    "<b>Переслать как есть</b> — отправьте готовое сообщение целиком "
    "(текст, медиа, форматирование, кнопки — если они уже есть), "
    "оно будет скопировано каждому получателю без изменений.\n\n"
    "<b>Собрать сообщение</b> — отправьте текст или медиа, "
    "а затем добавьте кнопки (со ссылкой или действием) отдельно."
)

ADMIN_BROADCAST_PROMPT = (
    '<tg-emoji emoji-id="5771868281212245617">📢</tg-emoji> '
    "Отправьте сообщение, которое хотите разослать пользователям — "
    "оно будет скопировано получателям как есть, вместе с любыми медиа "
    "и уже прикреплённой клавиатурой.\n\n"
    "Поддерживается HTML-разметка Telegram."
)

ADMIN_BROADCAST_CONTENT_PROMPT = (
    '<tg-emoji emoji-id="5771868281212245617">📢</tg-emoji> '
    "Отправьте текст или медиа (с подписью или без) для рассылки. "
    "На следующем шаге вы сможете добавить к нему кнопки.\n\n"
    "Поддерживается HTML-разметка Telegram."
)

ADMIN_BROADCAST_KEYBOARD_BUILDER = (
    '<tg-emoji emoji-id="5771868281212245617">📢</tg-emoji> '
    "<b>Добавление клавиатуры</b>\n\n"
    "Формат кнопки:\n"
    "<code>Текст - callback_data</code>\n\n"
    "Несколько кнопок в ряду:\n"
    "<code>Каталог - catalog | Помощь - help</code>\n\n"
    "Ссылка:\n"
    "<code>Сайт - https://example.com</code>\n\n"
    "Дополнительные параметры:\n"
    "<code>Кнопка - action [style=primary]</code>\n"
    "<code>Кнопка - action [emoji=123456]</code>\n\n"
    "Стили: <code>success</code>, <code>primary</code>, <code>danger</code>.\n\n"
    "Новый ряд — с новой строки.\n\n"
    "Если клавиатура не нужна, нажмите «Пропустить»."
)

ADMIN_BROADCAST_NO_CONTENT = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось получить содержимое рассылки. Попробуйте начать заново."
)

ADMIN_BROADCAST_PREVIEW = (
    '<tg-emoji emoji-id="5771868281212245617">📢</tg-emoji> '
    "Так будет выглядеть рассылка. Получателей: <b>{count}</b>.\n\n"
    "Подтвердить отправку?"
)

ADMIN_BROADCAST_CANCELLED = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> Рассылка отменена.'
)

ADMIN_BROADCAST_STARTED = (
    '<tg-emoji emoji-id="5891211339170326418">⏳</tg-emoji> '
    "Рассылка запущена. Получателей: <b>{count}</b>."
)

ADMIN_BROADCAST_PROGRESS = (
    '<tg-emoji emoji-id="5891211339170326418">⏳</tg-emoji> Рассылка выполняется: {sent}/{total}'
)

ADMIN_BROADCAST_DONE = (
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> '
    "Рассылка завершена.\n"
    "<blockquote>"
    "Всего получателей: {total}\n"
    "Успешно доставлено: {success}\n"
    "Не удалось доставить: {failed}"
    "</blockquote>"
)

BTN_ADMIN_BROADCAST_CONFIRM = "Отправить"
BTN_ADMIN_BROADCAST_CANCEL = "Отменить"
BTN_ADMIN_BROADCAST_NO_KEYBOARD = "Без кнопок"


# ── Провайдеры (админ) ────────────────────────────────────────────────────────

BTN_ADMIN_PROVIDER_CREATE = "Создать провайдера"
BTN_ADMIN_PROVIDER_RENAME = "Переименовать"
BTN_ADMIN_PROVIDER_SET_URL = "Изменить URL"
BTN_ADMIN_PROVIDER_DELETE = "Удалить"
BTN_ADMIN_PROVIDER_SKIP = "Пропустить"
BTN_ADMIN_PROVIDER_CLEAR = "Очистить"

ADMIN_PROVIDERS_LIST_TITLE = (
    '<tg-emoji emoji-id="5931347928810526429">🏷</tg-emoji> <b>Провайдеры</b>\n\n'
    "Всего: <b>{count}</b>.\n"
    "Выберите провайдера или создайте нового:"
)

ADMIN_PROVIDERS_LIST_EMPTY = (
    '<tg-emoji emoji-id="5931347928810526429">🏷</tg-emoji> <b>Провайдеры</b>\n\n'
    "Провайдеров пока нет."
)

ADMIN_PROVIDER_DETAILS = (
    '<tg-emoji emoji-id="5931347928810526429">🏷</tg-emoji> '
    "Провайдер <b>{provider_name}</b>\n"
    "Hash: <code>{provider_hash}</code>\n"
    "Owner hash: <code>{owner_hash}</code>\n"
    "URL: {provider_url}\n"
    "Токен: <blockquote><tg-spoiler>{api_token}</tg-spoiler></blockquote>\n"
)

ADMIN_PROVIDER_NOT_FOUND = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> Провайдер не найден.'
)

# ── Создание провайдера ────────────────────────────────────────────────────────

ADMIN_PROVIDER_CREATE_PROMPT_OWNER = (
    '<tg-emoji emoji-id="5886412370347036129">👤</tg-emoji> '
    "Отправьте Telegram ID пользователя, который будет владельцем нового провайдера.\n\n"
    "У пользователя уже должен быть аккаунт v2hub — при необходимости он будет создан."
)

ADMIN_PROVIDER_CREATE_PROMPT_NAME = (
    '<tg-emoji emoji-id="5931347928810526429">🏷</tg-emoji> '
    "Отправьте имя нового провайдера (должно быть уникальным)."
)

ADMIN_PROVIDER_CREATE_PROMPT_URL = (
    '<tg-emoji emoji-id="5931347928810526429">🏷</tg-emoji> '
    "Отправьте URL провайдера, либо нажмите «Пропустить»."
)

ADMIN_PROVIDER_CREATE_NAME_INVALID = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Имя не может быть пустым. Попробуйте ещё раз."
)

ADMIN_PROVIDER_CREATE_ERROR = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось создать провайдера:\n<code>{error}</code>"
)

ADMIN_PROVIDER_CREATE_CONFLICT = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Провайдер с именем <b>{provider_name}</b> уже существует."
)

ADMIN_PROVIDER_CREATED = (
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> '
    "Провайдер <b>{provider_name}</b> создан.\n"
    "<blockquote>"
    "Owner: <code>{owner_id}</code>\n"
    "Токен: <code>{api_token}</code>"
    "</blockquote>"
)

# ── Управление провайдером ───────────────────────────────────────────────────

ADMIN_PROVIDER_RENAME_PROMPT = (
    '<tg-emoji emoji-id="5931347928810526429">🏷</tg-emoji> '
    "Отправьте новое имя для провайдера <b>{provider_name}</b>."
)

ADMIN_PROVIDER_RENAMED = (
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> '
    "Провайдер переименован в <b>{provider_name}</b>."
)

ADMIN_PROVIDER_RENAME_CONFLICT = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Имя <b>{provider_name}</b> уже занято. Попробуйте другое."
)

ADMIN_PROVIDER_SET_URL_PROMPT = (
    '<tg-emoji emoji-id="5931347928810526429">🏷</tg-emoji> '
    "Отправьте новый URL для провайдера <b>{provider_name}</b>, "
    "либо нажмите «Очистить», чтобы убрать URL."
)

ADMIN_PROVIDER_URL_UPDATED = (
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> URL провайдера обновлён.'
)

ADMIN_PROVIDER_UPDATE_ERROR = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось обновить провайдера:\n<code>{error}</code>"
)

# ── Удаление провайдера ───────────────────────────────────────────────────────

ADMIN_PROVIDER_DELETE_CONFIRM = (
    '<tg-emoji emoji-id="6032636795387121097">⚠️</tg-emoji> '
    "Удалить провайдера <b>{provider_name}</b>? Это действие необратимо."
)

ADMIN_PROVIDER_DELETED = (
    '<tg-emoji emoji-id="6030445631921721471">✅</tg-emoji> '
    "Провайдер <b>{provider_name}</b> удалён."
)

ADMIN_PROVIDER_DELETE_ERROR = (
    '<tg-emoji emoji-id="6032636795387121097">❌</tg-emoji> '
    "Не удалось удалить провайдера:\n<code>{error}</code>"
)
