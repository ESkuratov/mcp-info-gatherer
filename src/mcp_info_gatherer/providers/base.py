"""Абстрактный базовый класс для info-провайдеров."""

from abc import ABC, abstractmethod

from mcp_info_gatherer.models import SearchResponse, TrendItem


class InfoProvider(ABC):
    """Базовый класс провайдера поиска информации.

    Каждый источник (web, Twitter, Telegram) реализует этот интерфейс.
    """

    @abstractmethod
    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск информации по запросу.

        Args:
            query: Поисковый запрос
            max_results: Максимум результатов

        Returns:
            SearchResponse с результатами поиска
        """
        ...

    async def get_trends(self, topic: str, max_results: int = 5) -> list[TrendItem]:
        """Получить тренды по теме (опционально).

        Args:
            topic: Тема для поиска трендов
            max_results: Максимум трендов

        Returns:
            Список TrendItem
        """
        return []
