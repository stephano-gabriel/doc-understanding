from typing import List, Optional
from pydantic import BaseModel, Field

class DataPoint(BaseModel):
    value: float = Field(description="The numerical value extracted.")
    raw_string_value: str = Field(description="The exact string representation of the extracted numerical value as it appears in the text without modification (e.g., '20.0', '(30)', '$1,000').")
    unit: Optional[str] = Field(description="The unit of measurement for the value (e.g., USD, %, million, kg).")
    description: str = Field(description="Short description of what this number represents.")
    date_ref: Optional[str] = Field(description="Date associated with the data point (format YYYY-MM-DD preferred).")
    quarter_ref: Optional[str] = Field(description="Quarter associated with the data point (e.g., Q1 2024).")
    page_number: Optional[int] = Field(description="The page number where the data was found (0-indexed).")
    location_snippet: str = Field(description="The exact text snippet or surrounding context from the document where this data point was found.")
    table_name: Optional[str] = Field(description="The name of the table if the data was extracted from one.")
    row_label: Optional[str] = Field(description="The row label or header when the value is extracted from a table.")
    section_title: Optional[str] = Field(description="The title of the section or paragraph if the data was found in text.")
    accurate_bbox: Optional[List[float]] = Field(default=None, description="The PyMuPDF-calculated absolute bounding box location [x0, y0, x1, y1] of the data point.")

class ExtractionResult(BaseModel):
    data_points: List[DataPoint] = Field(description="List of all extracted numerical data points from EVERY single row and EVERY section.")
