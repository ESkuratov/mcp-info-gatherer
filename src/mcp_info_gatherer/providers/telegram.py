"""Telegram search provider — поиск по каналам.

Два режима:
  1. User mode (полноценный поиск) — Telethon + номер телефона
  2. Bot mode (ограниченный) — Bot API, только последние сообщения
"""

import os
import re

from mcp_info_gatherer.models import SearchResponse, SearchResult
from mcp_info_gatherer.providers.base import InfoProvider

_CHANNEL_PATTERN = re.compile(r"@(\w+)")


class TelegramProvider(InfoProvider):
    """Поиск по Telegram каналам.

    Режимы:
      User mode (полный поиск):
        TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
        При первом запуске потребуется код подтверждения из Telegram.

      Bot mode (только последние сообщения из каналов, где бот админ):
        TELEGRAM_BOT_TOKEN
    """

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.api_id = os.getenv("TELEGRAM_API_ID", "")
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "")
        self.phone = os.getenv("TELEGRAM_PHONE", "")
        self._client = None

    # ── Telethon (user mode) ──────────────────────────────────────

    async def _get_telethon_client(self):
        """Создаёт Telethon клиент для пользовательского режима."""
        if self._client is not None:
            return self._client

        from telethon import TelegramClient

        client = TelegramClient(
            session="telegram_user_session",
            api_id=int(self.api_id),
            api_hash=self.api_hash,
        )
        await client.start(phone=self.phone)
        self._client = client
        return client

    async def _search_telethon(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск через Telethon (полнотекстовый, по истории)."""
        client = await self._get_telethon_client()
        results = []

        dialogs = await client.get_dialogs(limit=50)

        for dialog in dialogs:
            if len(results) >= max_results:
                break

            entity = dialog.entity
            if not hasattr(entity, "title"):
                continue

            try:
                messages = await client.get_messages(
                    entity,
                    limit=min(max_results - len(results), 10),
                    search=query,
                )

                for msg in messages:
                    if not msg.text and not msg.message:
                        continue

                    text = msg.text or msg.message or ""
                    channel_username = (
                        f"@{entity.username}"
                        if hasattr(entity, "username") and entity.username
                        else entity.title
                    )
                    channel_link = (
                        f"https://t.me/{entity.username}"
                        if hasattr(entity, "username") and entity.username
                        else ""
                    )
                    message_link = f"{channel_link}/{msg.id}" if channel_link else ""

                    results.append(SearchResult(
                        title=entity.title,
                        url=message_link or channel_link,
                        content=text[:500],
                        source="telegram",
                        author=channel_username,
                        date=str(msg.date)[:19] if msg.date else "",
                    ))

            except Exception:
                continue

        return SearchResponse(results=results, total=len(results), source="telegram")

    async def _search_channel_telethon(self, channel: str, query: str,
                                        max_results: int = 10) -> SearchResponse:
        """Поиск в конкретном канале через Telethon."""
        client = await self._get_telethon_client()

        channel_entity = None
        try:
            channel_entity = await client.get_entity(channel)
        except Exception:
            match = _CHANNEL_PATTERN.search(channel)
            if match:
                try:
                    channel_entity = await client.get_entity(match.group(0))
                except Exception:
                    pass

        if channel_entity is None:
            return SearchResponse(
                results=[], total=0, source="telegram",
                error=f"Канал не найден: {channel}",
            )

        messages = await client.get_messages(
            channel_entity,
            limit=min(max_results, 100),
            search=query,
        )

        channel_username = (
            f"@{channel_entity.username}"
            if hasattr(channel_entity, "username") and channel_entity.username
            else channel
        )
        channel_link = (
            f"https://t.me/{channel_entity.username}"
            if hasattr(channel_entity, "username") and channel_entity.username
            else ""
        )

        results = []
        for msg in messages:
            if not msg.text and not msg.message:
                continue
            text = msg.text or msg.message or ""
            message_link = f"{channel_link}/{msg.id}" if channel_link else ""

            results.append(SearchResult(
                title=channel_username,
                url=message_link or channel_link,
                content=text[:500],
                source="telegram",
                author=channel_username,
                date=str(msg.date)[:19] if msg.date else "",
            ))

        return SearchResponse(results=results, total=len(results), source="telegram")

    # ── Bot API (bot mode) ────────────────────────────────────────

    async def _search_bot_api(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск через Bot API — только последние сообщения из каналов, где бот админ."""
        try:
            import httpx

            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {
                "timeout": 5,
                "limit": min(max_results, 100),
                "allowed_updates": ["channel_post"],
            }

            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            if not data.get("ok"):
                return SearchResponse(
                    results=[], total=0, source="telegram",
                    error="Ошибка Bot API",
                )

            results = []
            for update in data.get("result", []):
                msg = update.get("channel_post", {}) or update.get("message", {})
                text = msg.get("text", "") or msg.get("caption", "")
                chat = msg.get("chat", {})

                if not text:
                    continue

                # Фильтр по поисковому запросу
                if query.lower() not in text.lower():
                    continue

                chat_username = chat.get("username", "")
                chat_title = chat.get("title", "")
                message_id = msg.get("message_id", 0)
                channel_link = (
                    f"https://t.me/{chat_username}/{message_id}"
                    if chat_username else ""
                )

                results.append(SearchResult(
                    title=chat_title or chat_username or "Unknown",
                    url=channel_link,
                    content=text[:500],
                    source="telegram",
                    author=f"@{chat_username}" if chat_username else chat_title,
                    date=str(msg.get("date", "")),
                ))

            return SearchResponse(
                results=results,
                total=len(results),
                source="telegram",
            )

        except Exception as e:
            return SearchResponse(
                results=[], total=0, source="telegram",
                error=f"Ошибка Bot API: {e}",
            )

    async def _search_channel_bot_api(self, channel: str, query: str,
                                       max_results: int = 10) -> SearchResponse:
        """Поиск в канале через Bot API — только последние сообщения."""
        return await self._search_bot_api(query, max_results)

    # ── Public API ────────────────────────────────────────────────

    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск сообщений по каналам.

        User mode (Telethon) — полнотекстовый поиск по истории всех диалогов.
        Bot mode (Bot API) — только последние сообщения из каналов, где бот админ.

        Args:
            query: Поисковый запрос
            max_results: Максимум результатов (1-100)

        Returns:
            SearchResponse с результатами
        """
        # User mode — полный поиск
        if self.api_id and self.api_hash and self.phone:
            try:
                return await self._search_telethon(query, max_results)
            except ImportError:
                return SearchResponse(
                    results=[], total=0, source="telegram",
                    error="Telethon не установлен. Выполните: uv add telethon",
                )
            except Exception as e:
                return SearchResponse(
                    results=[], total=0, source="telegram",
                    error=f"Ошибка Telethon: {e}",
                )

        # Bot mode — ограниченный поиск
        if self.bot_token:
            return await self._search_bot_api(query, max_results)

        # Ничего не настроено
        return SearchResponse(
            results=[], total=0, source="telegram",
            error=(
                "Не настроены учётные данные Telegram.\n"
                "  User mode: TELEGRAM_API_ID + TELEGRAM_API_HASH + TELEGRAM_PHONE\n"
                "  Bot mode:  TELEGRAM_BOT_TOKEN\n"
                "Подробнее: https://my.telegram.org/apps"
            ),
        )

    async def search_channel(self, channel: str, query: str,
                              max_results: int = 10) -> SearchResponse:
        """Поиск сообщений в конкретном Telegram канале.

        Args:
            channel: @username канала, chat_id или invite link
            query: Поисковый запрос
            max_results: Максимум результатов (1-100)

        Returns:
            SearchResponse с результатами
        """
        if self.api_id and self.api_hash and self.phone:
            try:
                return await self._search_channel_telethon(channel, query, max_results)
            except ImportError:
                return SearchResponse(
                    results=[], total=0, source="telegram",
                    error="Telethon не установлен. Выполните: uv add telethon",
                )
            except Exception as e:
                return SearchResponse(
                    results=[], total=0, source="telegram",
                    error=f"Ошибка Telethon: {e}",
                )

        if self.bot_token:
            return await self._search_channel_bot_api(channel, query, max_results)

        return SearchResponse(
            results=[], total=0, source="telegram",
            error="Не настроены учётные данные Telegram",
        )

    async def get_channel_info(self, channel: str) -> dict:
        """Получить информацию о канале.

        Args:
            channel: @username, chat_id или invite link

        Returns:
            dict: {title, username, about, participants_count, link}
        """
        if not self.api_id or not self.api_hash:
            return {"error": "TELEGRAM_API_ID и TELEGRAM_API_HASH не настроены"}

        try:
            from telethon import TelegramClient

            client = TelegramClient(
                session="telegram_info_session",
                api_id=int(self.api_id),
                api_hash=self.api_hash,
            )

            if self.phone:
                await client.start(phone=self.phone)
            elif self.bot_token:
                await client.start(bot_token=self.bot_token)
            else:
                return {"error": "Не настроены учётные данные Telegram"}

            entity = await client.get_entity(channel)

            full = None
            try:
                full = await client.get_full_entity(entity)
            except Exception:
                pass

            info = {
                "title": getattr(entity, "title", ""),
                "username": (
                    f"@{entity.username}"
                    if hasattr(entity, "username") and entity.username
                    else ""
                ),
                "about": getattr(full, "about", "") if full else "",
                "participants_count": (
                    getattr(full, "participants_count", 0)
                    if full and hasattr(full, "participants_count")
                    else 0
                ),
                "link": (
                    f"https://t.me/{entity.username}"
                    if hasattr(entity, "username") and entity.username
                    else ""
                ),
            }
            await client.disconnect()
            return info

        except ImportError:
            return {"error": "Telethon не установлен. Выполните: uv add telethon"}
        except Exception as e:
            return {"error": f"Ошибка Telethon: {e}"}
