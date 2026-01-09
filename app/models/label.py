from pydantic import BaseModel, Field
from typing import Optional


class Label(BaseModel):
    """Represents a single product label extracted from ZPL"""
    barcode: str = Field(..., min_length=1, description="Barcode value (e.g., GCOI36235)")
    product_name: str = Field(..., description="Product description")
    color: Optional[str] = Field(None, description="Color/variant (e.g., Blanco, Ahumado)")
    sku: str = Field(..., description="SKU code (e.g., DV002)")
    quantity: int = Field(1, ge=1, le=10000, description="Number of copies to print")

    def to_dict(self) -> dict:
        """Convert to dictionary for templating"""
        return self.model_dump()


class ConversionResult(BaseModel):
    """Result of PDF conversion"""
    success: bool
    total_labels: int
    total_copies: int
    pdf_path: Optional[str] = None
    error: Optional[str] = None
