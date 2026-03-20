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
        "reuters.com,apnews.com,bbc.com,theguardian.com,nytimes.com",
        alias="FIRECRAWL_ALLOWED_DOMAINS",
    )

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    frontend_origin: str = Field(default="http://localhost:3000", alias="FRONTEND_ORIGIN")

    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="no-reply@zia.ai", alias="SMTP_FROM")

    enable_scheduler: bool = Field(default=True, alias="ENABLE_SCHEDULER")
    daily_digest_hour: int = Field(default=8, alias="DAILY_DIGEST_HOUR")
    timezone: str = Field(default="America/Bogota", alias="TZ")


settings = Settings()
