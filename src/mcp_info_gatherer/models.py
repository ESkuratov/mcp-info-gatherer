"""Pydantic-схемы для MCP Info Gatherer."""

from pydantic import BaseModel, Field
from typing import Optional


class SearchQuery(BaseModel):
    """Параметры поискового запроса."""
    query: str = Field(description="Поисковый запрос")
    max_results: int = Field(default=10, description="Максимум результатов")
    source: str = Field(default="web", description="Источник: web | twitter | telegram")


class SearchResult(BaseModel):
    """Один результат поиска."""
    title: str = Field(default="", description="Заголовок")
    url: str = Field(default="", description="Ссылка")
    content: str = Field(default="", description="Текст/сниппет")
    source: str = Field(default="web", description="Источник: web | twitter | telegram")
    author: Optional[str] = Field(None, description="Автор (для Twitter/Telegram)")
    date: Optional[str] = Field(None, description="Дата публикации")
    score: Optional[float] = Field(None, description="Релевантность (0-1)")


class SearchResponse(BaseModel):
    """Результаты поиска."""
    results: list[SearchResult] = Field(default_factory=list, description="Результаты поиска")
    total: int = Field(default=0, description="Всего найдено")
    source: str = Field(description="Источник поиска")
    error: Optional[str] = Field(None, description="Ошибка, если поиск не удался")


class TrendQuery(BaseModel):
    """Параметры запроса трендов."""
    topic: str = Field(description="Тема для поиска трендов")
    max_results: int = Field(default=5, description="Максимум трендов")
    source: str = Field(default="web", description="Источник: web | twitter")


class TrendItem(BaseModel):
    """Один тренд."""
    title: str = Field(description="Название тренда")
    description: str = Field(default="", description="Описание")
    url: str = Field(default="", description="Ссылка")
    source: str = Field(description="Источник")
    mentions: Optional[int] = Field(None, description="Количество упоминаний")


class ReleaseItem(BaseModel):
    """Один GitHub релиз."""
    repo: str = Field(description="Репозиторий (owner/repo)")
    tag_name: str = Field(description="Тег релиза (например, v1.0.0)")
    release_name: str = Field(default="", description="Название релиза")
    published_at: str = Field(default="", description="Дата публикации (ISO 8601)")
    body: str = Field(default="", description="Описание релиза (changelog)")
    url: str = Field(default="", description="Ссылка на релиз")
    prerelease: bool = Field(default=False, description="Pre-release?")


class ReleasesResponse(BaseModel):
    """Список релизов из GitHub."""
    releases: list[ReleaseItem] = Field(default_factory=list, description="Релизы")
    total: int = Field(default=0, description="Всего релизов")
    error: Optional[str] = Field(None, description="Ошибка, если запрос не удался")
