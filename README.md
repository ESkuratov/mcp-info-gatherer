# MCP Info Gatherer

MCP-сервер для сбора информации из разных источников: веб, Twitter/X, Telegram,
GitHub, Hugging Face и arXiv.
Реализует протокол [MCP (Model Context Protocol)](https://modelcontextprotocol.io/).

## Источники

| Источник | Поиск | Тренды | API | Статус |
|---|---|---|---|---|
| **Web** (Tavily) | ✅ | ✅ | Требуется ключ | Работает |
| **Twitter/X** (API v2) | ✅ | ✅ | Требуется Bearer Token | Работает |
| **Telegram** (Bot API) | 🚧 Заглушка | — | Требуется токен | V2: Telethon |
| **GitHub** (REST API) | ✅ репозитории, код, issues | ✅ | Без ключа (60 req/h) | Работает |
| **Hugging Face** (Hub API) | ✅ модели, датасеты | ✅ | Без ключа | Работает |
| **arXiv** (API) | ✅ статьи | ✅ | Без ключа | Работает |

## Установка

```bash
# Установка через uv
uv sync

# С тестовыми зависимостями
uv sync --group test
```

## Настройка

Скопируйте `.env.example` в `.env` и укажите ключи:

```bash
cp .env.example .env
```

```
# WEB SEARCH — обязательный для search_web
TAVILY_API_KEY="tvly-..."

# TWITTER / X — опционально (требуется подписка X API)
X_BEARER_TOKEN="..."

# TELEGRAM — опционально (для V2)
TELEGRAM_BOT_TOKEN="..."

# GITHUB — опционально (для 5000 req/h вместо 60)
GITHUB_TOKEN="..."

# HUGGING FACE — опционально
HF_TOKEN="..."
```

- **Tavily API ключ** — получить на [tavily.com](https://tavily.com)
- **X Bearer Token** — получить в [developer.x.com](https://developer.x.com) (требуется Basic/Pro подписка)
- **Telegram Bot Token** — получить у [@BotFather](https://t.me/BotFather)
- **GitHub Token** — создать в Settings → Developer settings → Personal access tokens
- **GitHub, Hugging Face, arXiv** — работают без ключа

## Запуск

```bash
# stdio (для интеграции с MCP-хостами — Claude Desktop, Cline, crewAI)
uv run mcp-info-gatherer

# SSE (для отладки и удалённого доступа)
uv run mcp-info-gatherer --transport sse --host 127.0.0.1 --port 8003
```

## Инструменты MCP

### Web

#### `search_web`

Поиск информации в интернете через Tavily API.

**Параметры:**
- `query` (str): Поисковый запрос
- `max_results` (int, optional): Максимум результатов (1-20, по умолчанию 10)

**Ответ:**
```json
{
  "results": [
    {
      "title": "AI Trends 2026",
      "url": "https://example.com/ai-trends",
      "content": "Краткое описание...",
      "source": "web",
      "score": 0.95
    }
  ],
  "total": 5,
  "source": "web",
  "error": null
}
```

### Twitter / X

#### `search_twitter`

Поиск постов в Twitter/X. Требуется `X_BEARER_TOKEN`.

**Параметры:**
- `query` (str): Поисковый запрос (например, `"AI news lang:en"`)
- `max_results` (int, optional): 1-100, по умолчанию 10

### Telegram

#### `search_telegram`

Поиск по публичным Telegram каналам.

> **Примечание:** В MVP — заглушка. Bot API не поддерживает глобальный поиск.
> Полноценная реализация — в V2 через Telethon (MTProto).

### GitHub

#### `search_github`

Поиск репозиториев на GitHub. Поддерживает [qualifiers](https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories):
`language:python`, `stars:>100`, `topic:ai`, `org:openai`, etc.

**Параметры:**
- `query` (str): Поисковый запрос
- `max_results` (int, optional): 1-100, по умолчанию 10

#### `search_github_code`

Поиск кода на GitHub.

**Пример:** `"openai client lang:python"`

#### `search_github_issues`

Поиск issues и PR на GitHub.

**Пример:** `"bug label:bug state:open"`

### Hugging Face

#### `search_huggingface`

Поиск AI-моделей на Hugging Face Hub.

**Параметры:**
- `query` (str): Поисковый запрос (например, `"text-to-image"`)
- `max_results` (int, optional): 1-100, по умолчанию 10

#### `search_huggingface_datasets`

Поиск датасетов на Hugging Face Hub.

**Пример:** `"russian text"`

### arXiv

#### `search_arxiv`

Поиск научных статей на arXiv.

**Параметры:**
- `query` (str): Поисковый запрос или категория (`"cat:cs.AI"`, `"cat:cs.LG"`)
- `max_results` (int, optional): 1-100, по умолчанию 10

### Trends

#### `get_trends`

Получить тренды по теме из указанного источника.

**Параметры:**
- `topic` (str): Тема для поиска трендов
- `max_results` (int, optional): 1-10, по умолчанию 5
- `source` (str, optional): `web` | `twitter` | `github` | `huggingface` | `arxiv`

**Ответ:**
```json
[
  {
    "title": "AI в проектном менеджменте",
    "description": "Описание тренда...",
    "url": "https://example.com",
    "source": "web",
    "mentions": null
  }
]
```

## Тестирование

```bash
# Запуск всех тестов
uv run pytest tests/ -v

# Только unit-тесты
uv run pytest tests/test_server.py -v
```

### Что тестируется

- **Модели** — Pydantic-схемы (SearchResult, SearchResponse, TrendItem)
- **Провайдеры** — Web, Twitter, Telegram, GitHub, Hugging Face, arXiv
- **Реестр провайдеров** — синглтон, неизвестные источники
- **MCP сервер** — регистрация всех 10 инструментов

## Структура проекта

```
mcp-info-gatherer/
├── src/mcp_info_gatherer/
│   ├── server.py          # MCP сервер (10 инструментов)
│   ├── models.py          # Pydantic-схемы
│   └── providers/
│       ├── base.py        # Базовый класс InfoProvider
│       ├── web_search.py  # Tavily API
│       ├── twitter.py     # X API v2
│       ├── telegram.py    # Telegram Bot API / Telethon
│       ├── github.py      # GitHub REST API v3
│       ├── huggingface.py # Hugging Face Hub API
│       └── arxiv.py       # arXiv API
├── tests/
│   └── test_server.py     # 27 тестов
├── .env.example
└── pyproject.toml
```

## Интеграция с crewAI

В `ai-gc-pipeline` нужно будет создать bridge tool (`tools/mcp_info_gatherer_tool.py`),
который будет запускать MCP сервер как subprocess и общаться с ним через JSON-RPC по stdio.

Агенты, которые будут использовать:
- **ux-researcher** — `search_web`, `search_twitter`, `search_github` (исследование аудитории и аналогов)
- **content-strategist** — `search_web`, `search_huggingface`, `get_trends` (контент-план)
- **copywriter** — `search_arxiv`, `search_github` (фактчекинг для технических статей)
- **analyst** — `search_telegram`, `search_github_issues` (мониторинг каналов и обсуждений)

## Разработка

```bash
# Установка с dev-зависимостями
uv sync --group test

# Запуск тестов
uv run pytest

# Проверка типов
uv run mypy src/
```
