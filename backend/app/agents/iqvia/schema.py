from pydantic import BaseModel, Field
from typing import List, Optional

class RegionInfo(BaseModel):
    region: str = Field(..., description="Region name such as US, EU, India.")
    sales_value_musd: float = Field(..., description="Sales value in million USD.")
    cagr: float = Field(..., description="Growth rate in percentage.")
    top_competitors: List[str] = Field(..., description="Competitors in this region.")

class IQVIAResponse(BaseModel):
    molecule: str = Field(..., description="The molecule being analyzed.")
    regions: List[RegionInfo] = Field(..., description="List of market data by region.")
    summary: Optional[str] = Field(None, description="Short summary created by the agent.")
