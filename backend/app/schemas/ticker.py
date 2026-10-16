from datetime import datetime, timezone
from typing import Any, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class MarketIndexQuote(BaseModel):
    model_config = ConfigDict(extra="allow")

    symbol: str = Field(..., description="Exchange symbol (e.g. SENSEX, NIFTY BANK, NIFTY IT).")
    name: Optional[str] = Field(None, description="Human-readable index name.")
    last: float = Field(..., description="Last traded points value.")
    change: float = Field(..., description="Absolute points change.")
    pct_change: float = Field(..., description="Percentage change.")
    as_of: str = Field(..., description="ISO timestamp or exchange timestamp string.")
    source: Optional[str] = Field("NSE", description="Origin source (NSE or external/BSE).")
    market_status: Literal["open", "closed", "stale"] = Field(
        "open", description="Market operating status based on trading hours."
    )

    # Frontend compatibility fields
    currentPrice: Optional[float] = Field(None, description="Frontend alias for last.")
    changePoints: Optional[float] = Field(None, description="Frontend alias for change.")
    changePercent: Optional[float] = Field(None, description="Frontend alias for pct_change.")
    isPositive: Optional[bool] = Field(None, description="Frontend boolean indicating positive delta.")
    updatedAt: Optional[str] = Field(None, description="Frontend alias for as_of.")

    @model_validator(mode="before")
    @classmethod
    def harmonize_quote_inputs(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map frontend names to canonical
            if "currentPrice" in data and "last" not in data:
                data["last"] = data["currentPrice"]
            if "changePoints" in data and "change" not in data:
                data["change"] = data["changePoints"]
            if "changePercent" in data and "pct_change" not in data:
                data["pct_change"] = data["changePercent"]
            if "updatedAt" in data and "as_of" not in data:
                data["as_of"] = data["updatedAt"]

            # Map canonical to frontend names
            if "last" in data and "currentPrice" not in data:
                data["currentPrice"] = data["last"]
            if "change" in data and "changePoints" not in data:
                data["changePoints"] = data["change"]
            if "pct_change" in data and "changePercent" not in data:
                data["changePercent"] = data["pct_change"]
            if "as_of" in data and "updatedAt" not in data:
                data["updatedAt"] = data["as_of"]

            if "isPositive" not in data and "change" in data:
                data["isPositive"] = data["change"] >= 0

            if "name" not in data and "symbol" in data:
                data["name"] = data["symbol"]
        return data


class TickerSnapshotPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    timestamp: str = Field(..., description="Snapshot timestamp in ISO format.")
    quotes: List[MarketIndexQuote] = Field(..., description="Current list of tracked index quotes.")


class StreamTicketResponse(BaseModel):
    ticket: str = Field(..., description="Single-use cryptographically secure ticket for SSE streaming.")
    expires_in_seconds: int = Field(default=30, description="Ticket validity window.")
