"""Info providers — реализации поисковых провайдеров."""

from .base import InfoProvider
from .web_search import WebSearchProvider
from .twitter import TwitterProvider
from .telegram import TelegramProvider
from .github import GitHubProvider
from .huggingface import HuggingFaceProvider
from .arxiv import ArXivProvider


_providers: dict[str, InfoProvider] = {}


def get_provider(source: str) -> InfoProvider:
    """Возвращает провайдера для указанного источника.

    Args:
        source: "web" | "twitter" | "telegram" | "github" | "huggingface" | "arxiv"

    Returns:
        Экземпляр InfoProvider для данного источника
    """
    if source not in _providers:
        match source:
            case "web":
                _providers[source] = WebSearchProvider()
            case "twitter":
                _providers[source] = TwitterProvider()
            case "telegram":
                _providers[source] = TelegramProvider()
            case "github":
                _providers[source] = GitHubProvider()
            case "huggingface":
                _providers[source] = HuggingFaceProvider()
            case "arxiv":
                _providers[source] = ArXivProvider()
            case _:
                raise ValueError(f"Unknown source: {source}")
    return _providers[source]
