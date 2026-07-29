"""Web search provider — поиск в интернете через Tavily."""

import os

from mcp_info_gatherer.models import SearchResponse, SearchResult
from mcp_info_gatherer.providers.base import InfoProvider


class WebSearchProvider(InfoProvider):
    """Поиск в интернете через Tavily API."""

    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY", "")

    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск в интернете через Tavily.

        Args:
            query: Поисковый запрос
            max_results: Максимум результатов (1-20)

        Returns:
            SearchResponse с результатами
        """
        if not self.api_key:
            return SearchResponse(
                results=[],
                total=0,
                source="web",
                error="TAVILY_API_KEY не настроен. Укажите ключ в .env",
            )

        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.api_key)
            response = client.search(
                query=query,
                max_results=min(max_results, 20),
                search_depth="advanced",
                include_answer=False,
            )

            results = []
            for r in response.get("results", []):
                results.append(SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    content=r.get("content", ""),
                    source="web",
                    score=r.get("score"),
                ))

            return SearchResponse(
                results=results,
                total=len(results),
                source="web",
            )

        except Exception as e:
            return SearchResponse(
                results=[],
                total=0,
                source="web",
                error=f"Ошибка Tavily поиска: {e}",
            )

    async def get_trends(self, topic: str, max_results: int = 5) -> list:
        """Поиск трендов по теме через Tavily.

        Args:
            topic: Тема
            max_results: Максимум результатов

        Returns:
            Список TrendItem
        """
        from mcp_info_gatherer.models import TrendItem

        query = f"trends {topic} 2026"
        response = await self.search(query, max_results)

        trends = []
        for r in response.results:
            trends.append(TrendItem(
                title=r.title,
                description=r.content[:200],
                url=r.url,
                source="web",
            ))

        return trends
