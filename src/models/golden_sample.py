from typing import Optional

from sqlmodel import Field, SQLModel


class GoldenSample(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    input_text: str
    output_json: str
    is_base_case: bool
