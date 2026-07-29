"""Telegram search provider — поиск по публичным Telegram каналам."""

import os

from mcp_info_gatherer.models import SearchResponse, SearchResult
from mcp_info_gatherer.providers.base import InfoProvider


class TelegramProvider(InfoProvider):
    """Поиск по публичным Telegram каналам.

    В MVP — поиск через Bot API (ограниченный).
    В V2 — Telethon (MTProto) для полноценного поиска.
    """

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.api_id = os.getenv("TELEGRAM_API_ID", "")
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "")

    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск по публичным Telegram каналам.

        В MVP использует Bot API для поиска сообщений в известных каналах.
        Полноценный поиск по всем каналам — через Telethon (V2).

        Args:
            query: Поисковый запрос
            max_results: Максимум результатов

        Returns:
            SearchResponse с результатами
        """
        if not self.bot_token:
            return SearchResponse(
                results=[],
                total=0,
                source="telegram",
                error=(
                    "TELEGRAM_BOT_TOKEN не настроен. "
                    "Получите токен у @BotFather: https://t.me/BotFather"
                ),
            )

        # MVP: заглушка — Bot API не поддерживает глобальный поиск.
        # В V2: Telethon (MTProto) для поиска по каналам.
        return SearchResponse(
            results=[],
            total=0,
            source="telegram",
            error=(
                "Поиск по Telegram через Bot API недоступен. "
                "В V2 будет реализован через Telethon (MTProto). "
                "Пока используйте web_search для поиска информации о Telegram каналах."
            ),
        )

    async def search_channel(self, channel: str, query: str,
                              max_results: int = 10) -> SearchResponse:
        """Поиск сообщений в конкретном Telegram канале.

        Args:
            channel: @username канала или chat_id
            query: Поисковый запрос
            max_results: Максимум результатов

        Returns:
            SearchResponse с результатами
        """
        if not self.bot_token:
            return SearchResponse(
                results=[],
                total=0,
                source="telegram",
                error="TELEGRAM_BOT_TOKEN не настроен",
            )

        try:
            import httpx

            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params={"timeout": 0})
                resp.raise_for_status()
                data = resp.json()

            if not data.get("ok"):
                return SearchResponse(
                    results=[], total=0, source="telegram",
                    error="Ошибка Telegram Bot API",
                )

            # Bot API не поддерживает прямой поиск по тексту в канале.
            # Это заглушка для демонстрации интерфейса.
            return SearchResponse(
                results=[],
                total=0,
                source="telegram",
                error=(
                    "Поиск по каналу через Bot API ограничен. "
                    "В V2 будет реализован через Telethon."
                ),
            )

        except Exception as e:
            return SearchResponse(
                results=[],
                total=0,
                source="telegram",
                error=f"Ошибка Telegram API: {e}",
            )
