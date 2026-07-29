"""arXiv search provider — поиск научных статей."""

import os
import xml.etree.ElementTree as ET

from mcp_info_gatherer.models import SearchResponse, SearchResult, TrendItem
from mcp_info_gatherer.providers.base import InfoProvider

# Пространство имён Atom для парсинга arXiv XML
ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"


class ArXivProvider(InfoProvider):
    """Поиск научных статей через arXiv API.

    API бесплатный, без ключа.
    Поддерживает категории: cs.AI, cs.LG, stat.ML, cs.CL, etc.
    """

    def __init__(self):
        self.token = os.getenv("ARXIV_TOKEN", "")

    async def search(self, query: str, max_results: int = 10) -> SearchResponse:
        """Поиск статей на arXiv.

        Args:
            query: Поисковый запрос (например, "large language models")
                   или категория (cat:cs.AI)
            max_results: Максимум результатов (1-100)

        Returns:
            SearchResponse с результатами
        """
        try:
            import httpx

            params = {
                "search_query": query,
                "max_results": min(max_results, 100),
                "sortBy": "relevance",
                "sortOrder": "descending",
            }

            headers = {"User-Agent": "MCP-InfoGatherer/0.1 (mail@example.com)"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "http://export.arxiv.org/api/query",
                    headers=headers,
                    params=params,
                )
                resp.raise_for_status()
                xml_data = resp.text

            root = ET.fromstring(xml_data)
            results = []

            for entry in root.findall(f"{{{ATOM_NS}}}entry"):
                title = entry.findtext(f"{{{ATOM_NS}}}title", "").strip().replace("\n", " ")
                summary = entry.findtext(f"{{{ATOM_NS}}}summary", "").strip().replace("\n", " ")[:500]
                published = entry.findtext(f"{{{ATOM_NS}}}published", "")
                link = ""
                for link_el in entry.findall(f"{{{ATOM_NS}}}link"):
                    if link_el.get("rel", "") == "alternate" or not link_el.get("rel"):
                        link = link_el.get("href", "")
                        break

                # Авторы
                authors = []
                for author in entry.findall(f"{{{ATOM_NS}}}author"):
                    name = author.findtext(f"{{{ATOM_NS}}}name", "")
                    if name:
                        authors.append(name)

                # Категории
                categories = []
                for cat in entry.findall(f"{{{ARXIV_NS}}}primary_category"):
                    categories.append(cat.get("term", ""))
                for cat in entry.findall(f"{{{ATOM_NS}}}category"):
                    term = cat.get("term", "")
                    if term and term not in categories:
                        categories.append(term)

                results.append(SearchResult(
                    title=title,
                    url=link,
                    content=(
                        f"Категории: {', '.join(categories[:5])}\n"
                        f"Авторы: {', '.join(authors[:5])}\n"
                        f"{summary[:400]}"
                    ),
                    source="arxiv",
                    author=authors[0] if authors else "",
                    date=published[:10] if published else "",
                ))

            return SearchResponse(
                results=results,
                total=len(results),
                source="arxiv",
            )

        except Exception as e:
            return SearchResponse(
                results=[], total=0, source="arxiv",
                error=f"Ошибка arXiv API: {e}",
            )

    async def get_trends(self, topic: str, max_results: int = 5) -> list[TrendItem]:
        """Последние статьи по теме на arXiv.

        Args:
            topic: Тема или категория (например, "cat:cs.AI")
            max_results: Максимум результатов

        Returns:
            Список TrendItem
        """
        # Для трендов сортируем по дате, а не по релевантности
        try:
            import httpx

            params = {
                "search_query": topic,
                "max_results": min(max_results, 20),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }

            headers = {"User-Agent": "MCP-InfoGatherer/0.1 (mail@example.com)"}

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    "http://export.arxiv.org/api/query",
                    headers=headers,
                    params=params,
                )
                resp.raise_for_status()
                xml_data = resp.text

            root = ET.fromstring(xml_data)
            trends = []

            for entry in root.findall(f"{{{ATOM_NS}}}entry"):
                title = entry.findtext(f"{{{ATOM_NS}}}title", "").strip().replace("\n", " ")
                summary = entry.findtext(f"{{{ATOM_NS}}}summary", "").strip().replace("\n", " ")[:200]
                link = ""
                for link_el in entry.findall(f"{{{ATOM_NS}}}link"):
                    if link_el.get("rel", "") == "alternate" or not link_el.get("rel"):
                        link = link_el.get("href", "")
                        break

                trends.append(TrendItem(
                    title=title,
                    description=summary,
                    url=link,
                    source="arxiv",
                ))

            return trends

        except Exception as e:
            return []
