"""MCP Info Gatherer — сбор информации из веба, Twitter/X, Telegram,
GitHub, Hugging Face и arXiv.

Предоставляет единый интерфейс для поиска информации
из разных источников.

Запуск:
  uv run mcp-info-gatherer --transport stdio
  uv run mcp-info-gatherer --transport sse --host 127.0.0.1 --port 8003
"""

from mcp.server.fastmcp import FastMCP

from mcp_info_gatherer.models import SearchQuery, SearchResponse
from mcp_info_gatherer.providers import get_provider

# Создаём MCP сервер
mcp = FastMCP("Info Gatherer")


# ============================================================
# TOOLS — WEB
# ============================================================


@mcp.tool()
async def search_web(query: str, max_results: int = 10) -> dict:
    """Поиск информации в интернете.

    Использует Tavily API для поиска по вебу.
    Подходит для: фактчекинг, исследование рынка, поиск статей,
    сбор информации о продуктах и конкурентах.

    Args:
        query: Поисковый запрос (например, "тренды AI 2026")
        max_results: Максимум результатов (1-20)

    Returns:
        SearchResponse: {results: [{title, url, content, source, author, date, score}], total, source, error}
    """
    provider = get_provider("web")
    result = await provider.search(query, max_results)
    return result.model_dump()


# ============================================================
# TOOLS — TWITTER / X
# ============================================================


@mcp.tool()
async def search_twitter(query: str, max_results: int = 10) -> dict:
    """Поиск постов в Twitter/X.

    Использует X API v2 (требуется Bearer Token).
    Подходит для: мониторинг обсуждений, поиск мнений,
    отслеживание трендов в реальном времени.

    Args:
        query: Поисковый запрос (например, "AI news lang:en")
        max_results: Максимум результатов (1-100)

    Returns:
        SearchResponse: {results: [{title, url, content, source, author, date, score}], total, source, error}
    """
    provider = get_provider("twitter")
    result = await provider.search(query, max_results)
    return result.model_dump()


# ============================================================
# TOOLS — TELEGRAM
# ============================================================


@mcp.tool()
async def search_telegram(query: str, max_results: int = 10) -> dict:
    """Поиск по публичным Telegram каналам.

    В MVP — ограничен (Bot API не поддерживает глобальный поиск).
    В V2 — Telethon (MTProto) для полноценного поиска.
    Пока рекомендуется использовать search_web для поиска информации
    о Telegram каналах.

    Args:
        query: Поисковый запрос
        max_results: Максимум результатов

    Returns:
        SearchResponse: {results: [{title, url, content, source, author, date, score}], total, source, error}
    """
    provider = get_provider("telegram")
    result = await provider.search(query, max_results)
    return result.model_dump()


# ============================================================
# TOOLS — GITHUB
# ============================================================


@mcp.tool()
async def search_github(query: str, max_results: int = 10) -> dict:
    """Поиск репозиториев на GitHub.

    Использует GitHub REST API v3. Без токена — 60 req/h,
    с GITHUB_TOKEN — 5000 req/h.
    Подходит для: поиск open-source решений, анализ аналогов,
    мониторинг трендовых проектов.

    Args:
        query: Поисковый запрос (поддерживает qualifiers:
               language:python, stars:>100, topic:ai, etc.)
        max_results: Максимум результатов (1-100)

    Returns:
        SearchResponse: {results: [{title, url, content, source, author, date, score}], total, source, error}
    """
    provider = get_provider("github")
    result = await provider.search(query, max_results)
    return result.model_dump()


@mcp.tool()
async def search_github_code(query: str, max_results: int = 10) -> dict:
    """Поиск кода на GitHub.

    Использует GitHub Code Search API.
    Подходит для: поиск примеров кода, библиотек, утилит.

    Args:
        query: Поисковый запрос (например, "openai client lang:python")
        max_results: Максимум результатов (1-100)

    Returns:
        SearchResponse: {results: [{title, url, content, source, author}], total, source, error}
    """
    from mcp_info_gatherer.providers.github import GitHubProvider
    provider = GitHubProvider()
    result = await provider.search_code(query, max_results)
    return result.model_dump()


@mcp.tool()
async def search_github_issues(query: str, max_results: int = 10) -> dict:
    """Поиск issues и PR на GitHub.

    Использует GitHub Issues API.
    Подходит для: мониторинг багов, обсуждений, фич-реквестов.

    Args:
        query: Поисковый запрос (например, "bug label:bug state:open")
        max_results: Максимум результатов (1-100)

    Returns:
        SearchResponse: {results: [{title, url, content, source, author, date, score}], total, source, error}
    """
    from mcp_info_gatherer.providers.github import GitHubProvider
    provider = GitHubProvider()
    result = await provider.search_issues(query, max_results)
    return result.model_dump()


# ============================================================
# TOOLS — HUGGING FACE
# ============================================================


@mcp.tool()
async def search_huggingface(query: str, max_results: int = 10) -> dict:
    """Поиск моделей на Hugging Face.

    Использует HF Hub API. Бесплатно, без ключа.
    Подходит для: поиск AI-моделей, мониторинг новых релизов,
    анализ трендов в AI.

    Args:
        query: Поисковый запрос (например, "text-to-image")
        max_results: Максимум результатов (1-100)

    Returns:
        SearchResponse: {results: [{title, url, content, source, author, date}], total, source, error}
    """
    provider = get_provider("huggingface")
    result = await provider.search(query, max_results)
    return result.model_dump()


@mcp.tool()
async def search_huggingface_datasets(query: str, max_results: int = 10) -> dict:
    """Поиск датасетов на Hugging Face.

    Использует HF Hub API. Бесплатно, без ключа.
    Подходит для: поиск датасетов для обучения, анализа данных.

    Args:
        query: Поисковый запрос (например, "russian text")
        max_results: Максимум результатов (1-100)

    Returns:
        SearchResponse: {results: [{title, url, content, source, author, date}], total, source, error}
    """
    from mcp_info_gatherer.providers.huggingface import HuggingFaceProvider
    provider = HuggingFaceProvider()
    result = await provider.search_datasets(query, max_results)
    return result.model_dump()


# ============================================================
# TOOLS — ARXIV
# ============================================================


@mcp.tool()
async def search_arxiv(query: str, max_results: int = 10) -> dict:
    """Поиск научных статей на arXiv.

    Использует arXiv API. Бесплатно, без ключа.
    Подходит для: исследование темы, поиск релевантных работ,
    мониторинг новых публикаций.

    Args:
        query: Поисковый запрос (например, "large language models"
               или категория "cat:cs.AI")
        max_results: Максимум результатов (1-100)

    Returns:
        SearchResponse: {results: [{title, url, content, source, author, date}], total, source, error}
    """
    provider = get_provider("arxiv")
    result = await provider.search(query, max_results)
    return result.model_dump()


# ============================================================
# TOOLS — TRENDS
# ============================================================


@mcp.tool()
async def get_trends(topic: str, max_results: int = 5,
                     source: str = "web") -> dict:
    """Получить тренды по теме.

    Анализирует текущие тренды в указанной теме.
    Подходит для: контент-план, исследование аудитории,
    поиск актуальных тем для публикаций.

    Args:
        topic: Тема для поиска трендов (например, "project management")
        max_results: Максимум трендов (1-10)
        source: Источник (web | twitter | github | huggingface | arxiv)

    Returns:
        list[TrendItem]: [{title, description, url, source, mentions}]
    """
    provider = get_provider(source)
    result = await provider.get_trends(topic, max_results)
    return [t.model_dump() for t in result]


# ============================================================
# Entry point
# ============================================================


def main():
    """Точка входа для uv run mcp-info-gatherer."""
    import argparse
    from dotenv import load_dotenv

    load_dotenv()

    parser = argparse.ArgumentParser(description="MCP Info Gatherer")
    parser.add_argument("--transport", choices=["sse", "stdio"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8003)

    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
