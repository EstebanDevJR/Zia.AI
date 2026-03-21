from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Zia.AI API"
    database_url: str = Field(default="sqlite:///./data/app.db", alias="DATABASE_URL")

    firecrawl_api_key: str | None = Field(default=None, alias="FIRECRAWL_API_KEY")
    firecrawl_base: str = Field(default="https://api.firecrawl.dev/v2", alias="FIRECRAWL_BASE")
    firecrawl_allowed_domains: str = Field(
        default=
        "theverge.com,wired.com,techcrunch.com,arstechnica.com,technologyreview.com,"
        "reuters.com,apnews.com,bbc.com,theguardian.com,nytimes.com,"
        "nature.com,science.org,arxiv.org,openai.com,deepmind.com,anthropic.com,"
        "huggingface.co,stanford.edu",
        alias="FIRECRAWL_ALLOWED_DOMAINS",
    )

    ddg_base: str = Field(default="https://html.duckduckgo.com/html/", alias="DDG_BASE")
    ddg_user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36",
        alias="DDG_USER_AGENT",
    )
    ddg_accept_language: str = Field(default="es-ES,es;q=0.9,en;q=0.8", alias="DDG_ACCEPT_LANGUAGE")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    frontend_origin: str = Field(default="http://localhost:3000", alias="FRONTEND_ORIGIN")
    public_base_url: str = Field(default="http://localhost:8000", alias="PUBLIC_BASE_URL")

    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="no-reply@zia.ai", alias="SMTP_FROM")

    enable_scheduler: bool = Field(default=True, alias="ENABLE_SCHEDULER")
    daily_digest_hour: int = Field(default=8, alias="DAILY_DIGEST_HOUR")
    timezone: str = Field(default="America/Bogota", alias="TZ")

    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    news_cache_ttl_minutes: int = Field(default=15, alias="NEWS_CACHE_TTL_MINUTES")
    rate_limit_summary_per_hour: int = Field(default=30, alias="RATE_LIMIT_SUMMARY_PER_HOUR")
    rate_limit_send_per_hour: int = Field(default=10, alias="RATE_LIMIT_SEND_PER_HOUR")
    rate_limit_subscribe_per_hour: int = Field(default=5, alias="RATE_LIMIT_SUBSCRIBE_PER_HOUR")

    news_page_size_default: int = Field(default=8, alias="NEWS_PAGE_SIZE_DEFAULT")
    news_page_size_max: int = Field(default=20, alias="NEWS_PAGE_SIZE_MAX")
    news_max_limit: int = Field(default=60, alias="NEWS_MAX_LIMIT")
    article_ttl_hours: int = Field(default=24, alias="ARTICLE_TTL_HOURS")
    news_prefetch_enabled: bool = Field(default=True, alias="NEWS_PREFETCH_ENABLED")
    news_prefetch_interval_minutes: int = Field(default=30, alias="NEWS_PREFETCH_INTERVAL_MINUTES")
    news_prefetch_page_size: int = Field(default=25, alias="NEWS_PREFETCH_PAGE_SIZE")

    validation_enabled: bool = Field(default=True, alias="VALIDATION_ENABLED")
    validation_max: int = Field(default=20, alias="VALIDATION_MAX")
    validation_use_llm: bool = Field(default=False, alias="VALIDATION_USE_LLM")
    context_max_chars: int = Field(default=700, alias="CONTEXT_MAX_CHARS")


settings = Settings()
