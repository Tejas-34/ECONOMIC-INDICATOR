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
    ALLOW_INSECURE_DEFAULTS: bool = Field(
        default=False,
        description="Permit startup with default or insecure secrets for local development only."
    )
    EVAL_PASSWORD: str = Field(
        default="Analyst@2026",
        description="Plaintext analyst password for seeding from env."
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
    DATA_GOV_GST_URL: str = Field(
        default="https://api.data.gov.in/resource/a49bb4e6-662a-4cd1-83b7-6add74c1b984?api-key=579b464db66ec23bdd000001d42d21bfb519463160b3664bff8100fc&format=json",
        description="data.gov.in GST Tax Collection endpoint."
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


DEFAULT_INSECURE_JWT_SECRET = "c2VjdXJlX2p3dF9zZWNyZXRfa2V5X2Zvcl9lY29ub21pY19pbmRpY2F0b3JfZGFzaGJvYXJkXzIwMjY="
DEFAULT_INSECURE_EVAL_PASSWORD = "Analyst@2026"
DEFAULT_INSECURE_DB_SUBSTRINGS = ["postgres:postgres@", "postgres_secure_password_2026@"]


def validate_startup_secrets(s: Settings) -> None:
    """Enforce startup guard in live data mode (I9)."""
    if s.DATA_MODE != "live":
        return

    if s.ALLOW_INSECURE_DEFAULTS:
        print("[Startup Guard] WARNING: ALLOW_INSECURE_DEFAULTS is enabled. Insecure defaults permitted for development.")
        return

    errors = []
    if not s.JWT_SECRET or s.JWT_SECRET == DEFAULT_INSECURE_JWT_SECRET or len(s.JWT_SECRET) < 32:
        errors.append(
            "Insecure or default JWT_SECRET detected. Must be at least 32 characters and not the committed default."
        )

    if not s.EVAL_PASSWORD or s.EVAL_PASSWORD == DEFAULT_INSECURE_EVAL_PASSWORD:
        errors.append(
            "Default EVAL_PASSWORD ('Analyst@2026') detected. Set a custom EVAL_PASSWORD in .env."
        )

    if any(sub in s.DATABASE_URL for sub in DEFAULT_INSECURE_DB_SUBSTRINGS):
        errors.append(
            "Insecure default password detected in DATABASE_URL. Set a custom password in .env."
        )

    if errors:
        msg = "[Startup Guard] FATAL: Refusing to start in live mode with insecure defaults:\n" + "\n".join(f" - {e}" for e in errors)
        raise RuntimeError(msg)


settings = Settings()

