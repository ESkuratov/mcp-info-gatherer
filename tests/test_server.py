"""Тесты для MCP Info Gatherer."""

import pytest


class TestModels:
    """Тесты Pydantic-моделей."""

    def test_search_result_model(self):
        from mcp_info_gatherer.models import SearchResult

        r = SearchResult(
            title="Test",
            url="https://example.com",
            content="Test content",
            source="web",
        )
        assert r.title == "Test"
        assert r.source == "web"
        assert r.score is None

    def test_search_response_model(self):
        from mcp_info_gatherer.models import SearchResponse, SearchResult

        resp = SearchResponse(
            results=[
                SearchResult(title="A", url="https://a.com", content="A", source="web"),
            ],
            total=1,
            source="web",
        )
        assert resp.total == 1
        assert len(resp.results) == 1
        assert resp.error is None

    def test_search_response_with_error(self):
        from mcp_info_gatherer.models import SearchResponse

        resp = SearchResponse(
            results=[],
            total=0,
            source="web",
            error="API key not configured",
        )
        assert resp.error is not None

    def test_trend_item_model(self):
        from mcp_info_gatherer.models import TrendItem

        t = TrendItem(
            title="AI Trends",
            description="Latest AI trends",
            url="https://example.com/ai",
            source="web",
        )
        assert t.title == "AI Trends"
        assert t.mentions is None


class TestWebSearchProvider:
    """Тесты WebSearchProvider."""

    def test_provider_no_api_key(self):
        import os
        from mcp_info_gatherer.providers.web_search import WebSearchProvider

        old_key = os.environ.pop("TAVILY_API_KEY", None)

        provider = WebSearchProvider()
        assert provider.api_key == ""

        if old_key is not None:
            os.environ["TAVILY_API_KEY"] = old_key

    @pytest.mark.asyncio
    async def test_search_no_key_returns_error(self):
        from mcp_info_gatherer.providers.web_search import WebSearchProvider

        provider = WebSearchProvider()
        result = await provider.search("test query")
        assert result.total == 0
        assert result.error is not None
        assert "TAVILY_API_KEY" in result.error


class TestTwitterProvider:
    """Тесты TwitterProvider."""

    @pytest.mark.asyncio
    async def test_search_no_key_returns_error(self):
        from mcp_info_gatherer.providers.twitter import TwitterProvider

        provider = TwitterProvider()
        result = await provider.search("test query")
        assert result.total == 0
        assert result.error is not None
        assert "X_BEARER_TOKEN" in result.error


class TestTelegramProvider:
    """Тесты TelegramProvider."""

    @pytest.mark.asyncio
    async def test_search_no_credentials_returns_error(self):
        from mcp_info_gatherer.providers.telegram import TelegramProvider

        provider = TelegramProvider()
        result = await provider.search("test query")
        assert result.total == 0
        assert result.error is not None
        assert "Не настроены" in result.error


class TestGitHubProvider:
    """Тесты GitHubProvider."""

    def test_provider_no_token(self):
        import os
        from mcp_info_gatherer.providers.github import GitHubProvider

        old_token = os.environ.pop("GITHUB_TOKEN", None)

        provider = GitHubProvider()
        assert provider.token == ""

        if old_token is not None:
            os.environ["GITHUB_TOKEN"] = old_token

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_api_error(self):
        from mcp_info_gatherer.providers.github import GitHubProvider

        provider = GitHubProvider()
        result = await provider.search("test query")
        # GitHub API без токена — 60 req/h, может упасть с ошибкой
        # Но структура ответа должна быть валидной
        assert hasattr(result, "results")
        assert hasattr(result, "source")
        assert result.source == "github"

    @pytest.mark.asyncio
    async def test_search_code_returns_valid_structure(self):
        from mcp_info_gatherer.providers.github import GitHubProvider

        provider = GitHubProvider()
        result = await provider.search_code("test lang:python")
        assert hasattr(result, "results")
        assert result.source == "github"

    @pytest.mark.asyncio
    async def test_search_issues_returns_valid_structure(self):
        from mcp_info_gatherer.providers.github import GitHubProvider

        provider = GitHubProvider()
        result = await provider.search_issues("test")
        assert hasattr(result, "results")
        assert result.source == "github"

    @pytest.mark.asyncio
    async def test_get_trends_returns_list(self):
        from mcp_info_gatherer.providers.github import GitHubProvider

        provider = GitHubProvider()
        trends = await provider.get_trends("machine learning", 3)
        assert isinstance(trends, list)


class TestHuggingFaceProvider:
    """Тесты HuggingFaceProvider."""

    @pytest.mark.asyncio
    async def test_search_returns_valid_structure(self):
        from mcp_info_gatherer.providers.huggingface import HuggingFaceProvider

        provider = HuggingFaceProvider()
        result = await provider.search("text-to-image", 3)
        assert hasattr(result, "results")
        assert result.source == "huggingface"

    @pytest.mark.asyncio
    async def test_search_datasets_returns_valid_structure(self):
        from mcp_info_gatherer.providers.huggingface import HuggingFaceProvider

        provider = HuggingFaceProvider()
        result = await provider.search_datasets("russian", 3)
        assert hasattr(result, "results")
        assert result.source == "huggingface"

    @pytest.mark.asyncio
    async def test_get_trends_returns_list(self):
        from mcp_info_gatherer.providers.huggingface import HuggingFaceProvider

        provider = HuggingFaceProvider()
        trends = await provider.get_trends("text-to-image", 3)
        assert isinstance(trends, list)


class TestArXivProvider:
    """Тесты ArXivProvider."""

    @pytest.mark.asyncio
    async def test_search_returns_valid_structure(self):
        from mcp_info_gatherer.providers.arxiv import ArXivProvider

        provider = ArXivProvider()
        result = await provider.search("large language models", 3)
        assert hasattr(result, "results")
        assert result.source == "arxiv"

    @pytest.mark.asyncio
    async def test_get_trends_returns_list(self):
        from mcp_info_gatherer.providers.arxiv import ArXivProvider

        provider = ArXivProvider()
        trends = await provider.get_trends("cat:cs.AI", 3)
        assert isinstance(trends, list)


class TestProviderRegistry:
    """Тесты реестра провайдеров."""

    def test_get_web_provider(self):
        from mcp_info_gatherer.providers import get_provider
        from mcp_info_gatherer.providers.web_search import WebSearchProvider

        provider = get_provider("web")
        assert isinstance(provider, WebSearchProvider)

    def test_get_twitter_provider(self):
        from mcp_info_gatherer.providers import get_provider
        from mcp_info_gatherer.providers.twitter import TwitterProvider

        provider = get_provider("twitter")
        assert isinstance(provider, TwitterProvider)

    def test_get_telegram_provider(self):
        from mcp_info_gatherer.providers import get_provider
        from mcp_info_gatherer.providers.telegram import TelegramProvider

        provider = get_provider("telegram")
        assert isinstance(provider, TelegramProvider)

    def test_get_github_provider(self):
        from mcp_info_gatherer.providers import get_provider
        from mcp_info_gatherer.providers.github import GitHubProvider

        provider = get_provider("github")
        assert isinstance(provider, GitHubProvider)

    def test_get_huggingface_provider(self):
        from mcp_info_gatherer.providers import get_provider
        from mcp_info_gatherer.providers.huggingface import HuggingFaceProvider

        provider = get_provider("huggingface")
        assert isinstance(provider, HuggingFaceProvider)

    def test_get_arxiv_provider(self):
        from mcp_info_gatherer.providers import get_provider
        from mcp_info_gatherer.providers.arxiv import ArXivProvider

        provider = get_provider("arxiv")
        assert isinstance(provider, ArXivProvider)

    def test_get_unknown_provider(self):
        from mcp_info_gatherer.providers import get_provider

        with pytest.raises(ValueError, match="Unknown source"):
            get_provider("unknown")

    def test_provider_singleton(self):
        from mcp_info_gatherer.providers import get_provider

        p1 = get_provider("web")
        p2 = get_provider("web")
        assert p1 is p2


class TestMCPServer:
    """Тесты MCP сервера."""

    @pytest.mark.asyncio
    async def test_server_creation(self):
        from mcp_info_gatherer.server import mcp

        assert mcp.name == "Info Gatherer"
        tools = mcp._tool_manager._tools
        tool_names = [t.name for t in tools.values()]

        # Web
        assert "search_web" in tool_names
        # Twitter
        assert "search_twitter" in tool_names
        # Telegram
        assert "search_telegram" in tool_names
        assert "search_telegram_channel" in tool_names
        assert "get_telegram_channel_info" in tool_names
        # GitHub
        assert "search_github" in tool_names
        assert "search_github_code" in tool_names
        assert "search_github_issues" in tool_names
        # Hugging Face
        assert "search_huggingface" in tool_names
        assert "search_huggingface_datasets" in tool_names
        # arXiv
        assert "search_arxiv" in tool_names
        # Trends
        assert "get_trends" in tool_names
