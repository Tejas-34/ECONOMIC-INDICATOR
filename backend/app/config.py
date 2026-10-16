from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Operational Mode
    DATA_MODE: Literal["mock", "live"] = Field(
        default="mock",
        description="Runtime data mode: 'mock' serves static JSON fixtures with no DB writes; 'live' uses PostgreSQL and upstream collectors."
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/economic_indicators",
        description="PostgreSQL connection string for psycopg3 async pool."
    )
    DB_MIN_SIZE: int = Field(default=2, ge=1, le=20, description="Minimum pool connections.")
    DB_MAX_SIZE: int = Field(default=10, ge=2, le=50, description="Maximum pool connections.")

    # Authentication & Security
    JWT_SECRET: str = Field(
        default="c2VjdXJlX2p3dF9zZWNyZXRfa2V5X2Zvcl9lY29ub21pY19pbmRpY2F0b3JfZGFzaGJvYXJkXzIwMjY=",
        description="HMAC SHA-256 secret key for signing JWT access tokens."
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=5, le=1440, description="Token lifetime in minutes.")
    STREAM_TICKET_EXPIRE_SECONDS: int = Field(default=30, ge=10, le=120, description="Single-use SSE ticket lifetime in seconds.")

    # Seeded Evaluation User
    EVAL_USERNAME: str = Field(
        default="analyst@adityabirla.com",
        description="Default username for evaluation and testing."
    )
    EVAL_PASSWORD_HASH: str = Field(
        default="$2b$12$e6mO7jJ6g5lWkY8g2k.yquMhT6UfO6b5HjCgV4s9R2E1k3m8t2Y1e",
        description="Bcrypt hash of default analyst password ('Analyst@2026')."
    )

    # CORS
    FRONTEND_ORIGIN: str = Field(
        default="http://localhost:5173",
        description="Allowed origin for CORS requests."
    )

    # Collector Network & Resilience Settings
    COLLECTOR_TIMEOUT_CONNECT: float = Field(default=3.0, description="Connection timeout in seconds.")
    COLLECTOR_TIMEOUT_READ: float = Field(default=8.0, description="Read timeout in seconds.")
    COLLECTOR_MAX_RETRIES: int = Field(default=3, description="Maximum retry attempts.")
    COLLECTOR_MIN_INTERVAL_SECONDS: float = Field(default=15.0, description="Minimum delay between requests to same host.")
    COLLECTOR_CIRCUIT_FAILURES: int = Field(default=5, description="Consecutive failures before circuit trips open.")
    COLLECTOR_CIRCUIT_RESET_SECONDS: float = Field(default=300.0, description="Circuit breaker reset backoff in seconds (5 min).")

    # Upstream Endpoints
    NSE_BASE_URL: str = Field(default="https://www.nseindia.com", description="NSE base URL for session warming.")
    NSE_ALL_INDICES_URL: str = Field(default="https://www.nseindia.com/api/allIndices", description="NSE allIndices endpoint.")
    BSE_SENSEX_URL: str = Field(default="https://api.bseindia.com/BseIndiaAPI/api/SensexGraphData/w", description="BSE Sensex endpoint.")
    WORLD_BANK_BASE_URL: str = Field(default="https://api.worldbank.org/v2", description="World Bank API base URL.")
    IMF_DATAMAPPER_BASE_URL: str = Field(default="https://www.imf.org/external/datamapper/api/v1", description="IMF DataMapper base URL.")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
