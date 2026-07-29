"""Twitter/X search provider — поиск по Twitter/X API v2."""

import os

from mcp_info_gatherer.models import SearchResponse, SearchResult
from mcp_info_gatherer.providers.base import InfoProvider


class TwitterProvider(InfoProvider):
    """Поиск по Twitter/X через API v2.

    Требуется Bearer Token от X API (Basic/Pro подписка).
    Без токена возвращает заглушку с сообщением о настройке.
    """

    def __init__(self):
        self.bearer_token = os.getenv("X_BEARER_TOKEN", "")

    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск твитов по запросу.

        Args:
            query: Поисковый запрос
            max_results: Максимум результатов (1-100)

        Returns:
            SearchResponse с результатами
        """
        if not self.bearer_token:
            return SearchResponse(
                results=[],
                total=0,
                source="twitter",
                error=(
                    "X_BEARER_TOKEN не настроен. "
                    "Требуется X API (Basic/Pro подписка): https://developer.x.com"
                ),
            )

        try:
            import httpx

            headers = {"Authorization": f"Bearer {self.bearer_token}"}
            params = {
                "query": query,
                "max_results": min(max_results, 100),
                "tweet.fields": "created_at,author_id,public_metrics",
                "expansions": "author_id",
                "user.fields": "username,name",
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://api.twitter.com/2/tweets/search/recent",
                    headers=headers,
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()

            # Строим мапу author_id -> username
            users = {}
            for user in data.get("includes", {}).get("users", []):
                users[user["id"]] = user.get("username", "")

            results = []
            for tweet in data.get("data", []):
                author_id = tweet.get("author_id", "")
                results.append(SearchResult(
                    title=f"@{users.get(author_id, 'unknown')}",
                    url=f"https://x.com/{users.get(author_id, 'unknown')}/status/{tweet['id']}",
                    content=tweet.get("text", ""),
                    source="twitter",
                    author=f"@{users.get(author_id, 'unknown')}",
                    date=tweet.get("created_at", ""),
                ))

            return SearchResponse(
                results=results,
                total=len(results),
                source="twitter",
            )

        except Exception as e:
            return SearchResponse(
                results=[],
                total=0,
                source="twitter",
                error=f"Ошибка Twitter API: {e}",
            )

    async def get_trends(self, topic: str, max_results: int = 5) -> list:
        """Поиск трендов по теме в Twitter.

        Args:
            topic: Тема
            max_results: Максимум результатов

        Returns:
            Список TrendItem
        """
        from mcp_info_gatherer.models import TrendItem

        response = await self.search(topic, max_results)

        trends = []
        for r in response.results:
            trends.append(TrendItem(
                title=r.title,
                description=r.content[:200],
                url=r.url,
                source="twitter",
            ))

        return trends
