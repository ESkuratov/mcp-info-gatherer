"""arXiv search provider — поиск научных статей."""

import asyncio
import os
import xml.etree.ElementTree as ET

from mcp_info_gatherer.models import SearchResponse, SearchResult, TrendItem
from mcp_info_gatherer.providers.base import InfoProvider

# Пространство имён Atom для парсинга arXiv XML
ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"

ARXIV_BASE = "https://export.arxiv.org/api/query"
USER_AGENT = "MCP-InfoGatherer/0.1 (mail@example.com)"


def _parse_entry(entry: ET.Element) -> dict:
    """Разобрать одну entry arXiv XML в словарь."""
    title = entry.findtext(f"{{{ATOM_NS}}}title", "").strip().replace("\n", " ")
    summary = entry.findtext(f"{{{ATOM_NS}}}summary", "").strip().replace("\n", " ")

    link = ""
    for link_el in entry.findall(f"{{{ATOM_NS}}}link"):
        if link_el.get("rel", "") == "alternate" or not link_el.get("rel"):
            link = link_el.get("href", "")
            break

    authors = []
    for author in entry.findall(f"{{{ATOM_NS}}}author"):
        name = author.findtext(f"{{{ATOM_NS}}}name", "")
        if name:
            authors.append(name)

    categories = []
    for cat in entry.findall(f"{{{ARXIV_NS}}}primary_category"):
        categories.append(cat.get("term", ""))
    for cat in entry.findall(f"{{{ATOM_NS}}}category"):
        term = cat.get("term", "")
        if term and term not in categories:
            categories.append(term)

    published = entry.findtext(f"{{{ATOM_NS}}}published", "")
    updated = entry.findtext(f"{{{ATOM_NS}}}updated", "")

    return {
        "title": title,
        "summary": summary,
        "link": link,
        "authors": authors,
        "categories": categories,
        "published": published[:10] if published else "",
        "updated": updated[:10] if updated else "",
    }


async def _arxiv_request(
    client: "httpx.AsyncClient",
    params: dict,
    retries: int = 2,
) -> str:
    """GET-запрос к arXiv API с повторными попытками."""
    import httpx

    for attempt in range(retries + 1):
        try:
            resp = await client.get(ARXIV_BASE, params=params, timeout=30)
            resp.raise_for_status()
            return resp.text
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            if attempt < retries:
                wait = 2 ** attempt
                await asyncio.sleep(wait)
                continue
            raise
        except httpx.HTTPStatusError as e:
            raise


class ArXivProvider(InfoProvider):
    """Поиск научных статей через arXiv API.

    API бесплатный, без ключа.
    Поддерживает категории: cs.AI, cs.LG, stat.ML, cs.CL, etc.
    """

    def __init__(self):
        self.token = os.getenv("ARXIV_TOKEN", "")

    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
    ) -> SearchResponse:
        """Поиск статей на arXiv.

        Args:
            query: Поисковый запрос (например, "large language models")
                   или категория (cat:cs.AI)
            max_results: Максимум результатов (1-100)
            sort_by: Сортировка — "relevance" (по релевантности)
                     или "submittedDate" (по дате, свежие сверху)

        Returns:
            SearchResponse с результатами
        """
        try:
            import httpx

            params = {
                "search_query": query,
                "max_results": min(max_results, 100),
                "sortBy": sort_by,
                "sortOrder": "descending",
            }

            headers = {"User-Agent": USER_AGENT}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            async with httpx.AsyncClient() as client:
                xml_data = await _arxiv_request(client, params)

            root = ET.fromstring(xml_data)
            results = []

            for entry in root.findall(f"{{{ATOM_NS}}}entry"):
                parsed = _parse_entry(entry)
                results.append(SearchResult(
                    title=parsed["title"],
                    url=parsed["link"],
                    content=(
                        f"Категории: {', '.join(parsed['categories'][:5])}\n"
                        f"Авторы: {', '.join(parsed['authors'][:5])}\n"
                        f"{parsed['summary'][:400]}"
                    ),
                    source="arxiv",
                    author=parsed["authors"][0] if parsed["authors"] else "",
                    date=parsed["published"],
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

    async def search_recent(
        self,
        query: str,
        days: int = 7,
        max_results: int = 50,
    ) -> SearchResponse:
        """Поиск статей за последние N дней.

        arXiv API с sortBy=submittedDate возвращает только последний
        день (до 100 статей). Чтобы получить больше — делаются
        последовательные запросы с пагинацией (start=0, 100, 200...),
        результаты дедуплицируются и фильтруются по дате.

        Args:
            query: Поисковый запрос (например, "cat:cs.AI" или "ti:agent")
            days: Сколько дней искать (1-30)
            max_results: Максимум результатов (1-200)

        Returns:
            SearchResponse с результатами
        """
        import httpx
        from datetime import datetime, timedelta, timezone

        now = datetime.now(timezone.utc)
        cutoff_date = now.date() - timedelta(days=days)
        seen_urls: set[str] = set()
        all_results: list[SearchResult] = []
        start = 0
        page_size = 100

        async with httpx.AsyncClient() as client:
            while len(all_results) < max_results:
                params = {
                    "search_query": query,
                    "start": start,
                    "max_results": page_size,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                }

                try:
                    xml_data = await _arxiv_request(client, params)
                except Exception as e:
                    import sys
                    print(f"arXiv search_recent error (start={start}): {e}", file=sys.stderr)
                    break

                root = ET.fromstring(xml_data)
                entries = root.findall(f"{{{ATOM_NS}}}entry")
                if not entries:
                    break

                batch_has_recent = False
                for entry in entries:
                    parsed = _parse_entry(entry)
                    pub_date = parsed["published"]

                    # Пропускаем статьи старше cutoff_date
                    if pub_date:
                        try:
                            d = datetime.strptime(pub_date, "%Y-%m-%d").date()
                            if d < cutoff_date:
                                continue
                        except ValueError:
                            pass
                        batch_has_recent = True

                    if parsed["link"] in seen_urls:
                        continue
                    seen_urls.add(parsed["link"])

                    all_results.append(SearchResult(
                        title=parsed["title"],
                        url=parsed["link"],
                        content=(
                            f"Категории: {', '.join(parsed['categories'][:5])}\n"
                            f"Авторы: {', '.join(parsed['authors'][:5])}\n"
                            f"{parsed['summary'][:400]}"
                        ),
                        source="arxiv",
                        author=parsed["authors"][0] if parsed["authors"] else "",
                        date=pub_date,
                    ))

                    if len(all_results) >= max_results:
                        break

                # Если в этой странице нет статей в пределах cutoff — выходим
                if not batch_has_recent:
                    break

                start += page_size
                await asyncio.sleep(0.3)  # rate limit

        # Сортировка: свежие сверху
        all_results.sort(key=lambda r: r.date or "", reverse=True)

        return SearchResponse(
            results=all_results[:max_results],
            total=len(all_results),
            source="arxiv",
        )

    async def get_trends(self, topic: str, max_results: int = 5) -> list[TrendItem]:
        """Последние статьи по теме на arXiv.

        Args:
            topic: Тема или категория (например, "cat:cs.AI")
            max_results: Максимум результатов

        Returns:
            Список TrendItem
        """
        try:
            import httpx

            params = {
                "search_query": topic,
                "max_results": min(max_results, 20),
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }

            headers = {"User-Agent": USER_AGENT}

            async with httpx.AsyncClient() as client:
                xml_data = await _arxiv_request(client, params)

            root = ET.fromstring(xml_data)
            trends = []

            for entry in root.findall(f"{{{ATOM_NS}}}entry"):
                parsed = _parse_entry(entry)
                trends.append(TrendItem(
                    title=parsed["title"],
                    description=parsed["summary"][:200],
                    url=parsed["link"],
                    source="arxiv",
                ))

            return trends

        except Exception as e:
            return []
