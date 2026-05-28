from typing import Optional

from sqlmodel import Field, SQLModel


class TicketSample(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    input_text: str 
    output_json: str | None
    is_correct: Optional[bool] = Field(default=None)
    for_evaluation: bool = Field(default=False)
    prompt_version_id: int = Field(foreign_key="promptversion.id")
