"""GitHub search provider — поиск репозиториев, кода и issues."""

import os

from mcp_info_gatherer.models import SearchResponse, SearchResult, TrendItem
from mcp_info_gatherer.providers.base import InfoProvider


class GitHubProvider(InfoProvider):
    """Поиск по GitHub через REST API v3.

    Без токена — 60 req/h (достаточно для разработки).
    С токеном (GITHUB_TOKEN) — 5000 req/h.
    """

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN", "")

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск репозиториев на GitHub.

        Args:
            query: Поисковый запрос (поддерживает GitHub search qualifiers:
                   language:python, stars:>100, topic:ai, etc.)
            max_results: Максимум результатов (1-100)

        Returns:
            SearchResponse с результатами
        """
        return await self._search_repos(query, max_results)

    async def _search_repos(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск репозиториев."""
        try:
            import httpx

            params = {
                "q": query,
                "per_page": min(max_results, 100),
                "sort": "stars",
                "order": "desc",
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://api.github.com/search/repositories",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()

            results = []
            for repo in data.get("items", []):
                results.append(SearchResult(
                    title=repo.get("full_name", ""),
                    url=repo.get("html_url", ""),
                    content=(
                        f"{repo.get('description', '')}\n"
                        f"⭐ {repo.get('stargazers_count', 0)} | "
                        f"🍴 {repo.get('forks_count', 0)} | "
                        f"🐛 {repo.get('open_issues_count', 0)} | "
                        f"📦 {repo.get('language') or 'N/A'}"
                    ),
                    source="github",
                    author=repo.get("owner", {}).get("login", ""),
                    date=repo.get("created_at", ""),
                    score=repo.get("score"),
                ))

            return SearchResponse(
                results=results,
                total=min(data.get("total_count", 0), 1000),
                source="github",
            )

        except Exception as e:
            return SearchResponse(
                results=[], total=0, source="github",
                error=f"Ошибка GitHub API: {e}",
            )

    async def search_code(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск кода на GitHub.

        Args:
            query: Поисковый запрос (например, "openai client lang:python")
            max_results: Максимум результатов (1-100)

        Returns:
            SearchResponse с результатами
        """
        try:
            import httpx

            params = {
                "q": query,
                "per_page": min(max_results, 100),
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://api.github.com/search/code",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()

            results = []
            for item in data.get("items", []):
                repo_name = item.get("repository", {}).get("full_name", "")
                path = item.get("path", "")
                results.append(SearchResult(
                    title=f"{repo_name}: {path}",
                    url=item.get("html_url", ""),
                    content=item.get("name", ""),
                    source="github",
                    author=repo_name.split("/")[0] if "/" in repo_name else "",
                ))

            return SearchResponse(
                results=results,
                total=min(data.get("total_count", 0), 1000),
                source="github",
            )

        except Exception as e:
            return SearchResponse(
                results=[], total=0, source="github",
                error=f"Ошибка GitHub Code Search API: {e}",
            )

    async def search_issues(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск issues и PR на GitHub.

        Args:
            query: Поисковый запрос (например, "bug label:bug state:open")
            max_results: Максимум результатов (1-100)

        Returns:
            SearchResponse с результатами
        """
        try:
            import httpx

            params = {
                "q": query,
                "per_page": min(max_results, 100),
                "sort": "updated",
                "order": "desc",
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://api.github.com/search/issues",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()

            results = []
            for issue in data.get("items", []):
                results.append(SearchResult(
                    title=issue.get("title", ""),
                    url=issue.get("html_url", ""),
                    content=issue.get("body", "")[:500] if issue.get("body") else "",
                    source="github",
                    author=issue.get("user", {}).get("login", ""),
                    date=issue.get("created_at", ""),
                    score=issue.get("score"),
                ))

            return SearchResponse(
                results=results,
                total=min(data.get("total_count", 0), 1000),
                source="github",
            )

        except Exception as e:
            return SearchResponse(
                results=[], total=0, source="github",
                error=f"Ошибка GitHub Issues API: {e}",
            )

    async def get_trends(self, topic: str, max_results: int = 5) -> list[TrendItem]:
        """Трендовые репозитории по теме.

        Args:
            topic: Тема (например, "machine learning")
            max_results: Максимум результатов

        Returns:
            Список TrendItem
        """
        query = f"topic:{topic} stars:>100"
        response = await self._search_repos(query, max_results)

        trends = []
        for r in response.results:
            trends.append(TrendItem(
                title=r.title,
                description=r.content[:200],
                url=r.url,
                source="github",
            ))

        return trends
