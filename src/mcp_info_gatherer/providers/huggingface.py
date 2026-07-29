"""Hugging Face search provider — поиск моделей и датасетов."""

import os

from mcp_info_gatherer.models import SearchResponse, SearchResult, TrendItem
from mcp_info_gatherer.providers.base import InfoProvider


class HuggingFaceProvider(InfoProvider):
    """Поиск по Hugging Face Hub API.

    API бесплатный, без ключа.
    Опционально: HF_TOKEN для расширенного доступа.
    """

    def __init__(self):
        self.token = os.getenv("HF_TOKEN", "")

    def _headers(self) -> dict:
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск моделей на Hugging Face.

        Args:
            query: Поисковый запрос (например, "text-to-image")
            max_results: Максимум результатов (1-100)

        Returns:
            SearchResponse с результатами
        """
        return await self._search_models(query, max_results)

    async def _search_models(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск моделей."""
        try:
            import httpx

            params = {
                "search": query,
                "limit": min(max_results, 100),
                "sort": "downloads",
                "direction": -1,
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://huggingface.co/api/models",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()

            results = []
            for model in data:
                results.append(SearchResult(
                    title=model.get("modelId", model.get("id", "")),
                    url=f"https://huggingface.co/{model.get('modelId', model.get('id', ''))}",
                    content=(
                        f"{model.get('pipeline_tag', 'N/A')} | "
                        f"⬇️ {model.get('downloads', 0):,} | "
                        f"❤️ {model.get('likes', 0)}\n"
                        f"{model.get('description', '')[:300]}"
                    ),
                    source="huggingface",
                    author=model.get("author", model.get("modelId", "")).split("/")[0],
                    date=model.get("createdAt", ""),
                ))

            return SearchResponse(
                results=results,
                total=len(results),
                source="huggingface",
            )

        except Exception as e:
            return SearchResponse(
                results=[], total=0, source="huggingface",
                error=f"Ошибка Hugging Face API: {e}",
            )

    async def search_datasets(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск датасетов на Hugging Face.

        Args:
            query: Поисковый запрос (например, "russian text")
            max_results: Максимум результатов (1-100)

        Returns:
            SearchResponse с результатами
        """
        try:
            import httpx

            params = {
                "search": query,
                "limit": min(max_results, 100),
                "sort": "downloads",
                "direction": -1,
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "https://huggingface.co/api/datasets",
                    headers=self._headers(),
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json()

            results = []
            for ds in data:
                results.append(SearchResult(
                    title=ds.get("id", ""),
                    url=f"https://huggingface.co/datasets/{ds.get('id', '')}",
                    content=(
                        f"⬇️ {ds.get('downloads', 0):,} | "
                        f"❤️ {ds.get('likes', 0)}\n"
                        f"{ds.get('description', '')[:300]}"
                    ),
                    source="huggingface",
                    author=ds.get("id", "").split("/")[0] if "/" in ds.get("id", "") else "",
                    date=ds.get("createdAt", ""),
                ))

            return SearchResponse(
                results=results,
                total=len(results),
                source="huggingface",
            )

        except Exception as e:
            return SearchResponse(
                results=[], total=0, source="huggingface",
                error=f"Ошибка Hugging Face Datasets API: {e}",
            )

    async def get_trends(self, topic: str, max_results: int = 5) -> list[TrendItem]:
        """Новые и популярные модели по теме.

        Args:
            topic: Тема (например, "text-to-image")
            max_results: Максимум результатов

        Returns:
            Список TrendItem
        """
        response = await self._search_models(topic, max_results)

        trends = []
        for r in response.results:
            trends.append(TrendItem(
                title=r.title,
                description=r.content[:200],
                url=r.url,
                source="huggingface",
            ))

        return trends
