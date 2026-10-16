from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


# Common Stat Metric Tile
class StatTileMetric(BaseModel):
    model_config = ConfigDict(extra="allow")

    label: str = Field(..., description="Display label for the stat tile.")
    value: Optional[Union[float, int, str]] = Field(None, description="Current stat value.")
    formattedValue: Optional[str] = Field(None, description="Pre-formatted value string for display.")
    unit: Optional[str] = Field(None, description="Metric unit (e.g., %, US$ B, Rs lakh crore).")
    delta: Optional[float] = Field(None, description="Numerical change/delta.")
    change: Optional[float] = Field(None, description="Alias for delta in percentage points (pp).")
    formattedDelta: Optional[str] = Field(None, description="Pre-formatted delta text with direction/unit.")
    deltaUnit: Optional[str] = Field("pp", description="Delta unit, defaults to 'pp'.")
    change_unit: Optional[str] = Field("pp", description="Alias for deltaUnit.")
    deltaDirection: Optional[Literal["positive", "negative", "neutral"]] = Field(
        "neutral", description="Visual indicator direction."
    )
    sublabel: Optional[str] = Field(None, description="Optional secondary sublabel.")
    iconKey: Optional[str] = Field(None, description="Optional icon or artwork key.")

    @model_validator(mode="before")
    @classmethod
    def sync_change_and_delta(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "change" in data and "delta" not in data:
                data["delta"] = data["change"]
            elif "delta" in data and "change" not in data:
                data["change"] = data["delta"]
            if "change_unit" in data and "deltaUnit" not in data:
                data["deltaUnit"] = data["change_unit"]
            elif "deltaUnit" in data and "change_unit" not in data:
                data["change_unit"] = data["deltaUnit"]
        return data


class TimeSeriesPoint(BaseModel):
    model_config = ConfigDict(extra="allow")

    period: str = Field(..., description="Time period label (e.g. 2021, FY2024-25, 25 Jul).")
    value: Optional[Union[float, int]] = Field(None, description="Observation value.")
    basis: Optional[str] = Field(None, description="Reporting basis (e.g. actual, revised_estimate).")


class TimeSeries(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="Series identifier (e.g. india, world, exports, imports).")
    points: List[TimeSeriesPoint] = Field(default_factory=list, description="Ordered time series observations.")


# Source Provenance
class SourceProvenance(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(..., description="Authoritative publisher or agency name.")
    type: Literal["nse", "NSE", "external", "external-curated"] = Field(
        ..., description="Provenance category."
    )
    url: Optional[str] = Field("", description="Documentation or source data URL.")


# Standard Indicator Envelope
class StandardIndicatorEnvelope(BaseModel):
    model_config = ConfigDict(extra="allow")

    # Identifiers: supports both 'id' and 'indicator'
    id: Optional[str] = Field(None, description="Indicator slug ID.")
    indicator: Optional[str] = Field(None, description="Standard indicator identifier slug.")
    title: str = Field(..., description="Panel title matching design specification.")
    subtitle: Optional[str] = Field(None, description="Optional subtitle.")

    # Attribution & Provenance
    source: Union[SourceProvenance, str] = Field(..., description="Authoritative data source.")
    source_type: Optional[str] = Field(None, description="Source provenance type (NSE or external).")
    as_of: str = Field(..., description="Effective data as-of period or date.")
    fetched_at: Optional[str] = Field(None, description="ISO timestamp when fetched.")
    status: Literal["ok", "stale", "unavailable"] = Field("ok", description="Freshness lifecycle status.")

    # KPI Stat Tiles: supports both 'values' (dict) and 'tiles' (list)
    values: Optional[Dict[str, Any]] = Field(None, description="Dictionary of named stat tiles.")
    tiles: Optional[List[StatTileMetric]] = Field(None, description="List of stat tiles.")

    # Chart Series Points
    series: List[Any] = Field(default_factory=list, description="Array of chart series points.")

    @model_validator(mode="after")
    def harmonize_fields(self) -> "StandardIndicatorEnvelope":
        # Ensure both id and indicator are populated
        if self.id and not self.indicator:
            self.indicator = self.id
        elif self.indicator and not self.id:
            self.id = self.indicator

        # Ensure fetched_at is populated
        if not self.fetched_at:
            self.fetched_at = datetime.now(timezone.utc).isoformat()

        # Synchronize values dict and tiles list
        if self.values and not self.tiles:
            self.tiles = [
                v if isinstance(v, StatTileMetric) else StatTileMetric.model_validate(v)
                for v in self.values.values()
                if isinstance(v, dict)
            ]
        elif self.tiles and not self.values:
            self.values = {
                (tile.label.lower().replace(" ", "_") if tile.label else f"tile_{i}"): tile
                for i, tile in enumerate(self.tiles)
            }

        # Harmonize source_type
        if isinstance(self.source, SourceProvenance):
            self.source_type = self.source.type
        elif self.source and not self.source_type:
            self.source_type = "external"

        return self


# Consolidated Dashboard Response
class DashboardResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    indicators: List[StandardIndicatorEnvelope] = Field(..., description="All indicator panels.")
    as_of: str = Field(..., description="Effective dashboard as-of timestamp.")
    fetched_at: str = Field(..., description="ISO 8601 fetch timestamp.")
