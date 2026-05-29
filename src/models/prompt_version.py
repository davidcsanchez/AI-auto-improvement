from typing import Optional

from sqlmodel import Field, SQLModel


class PromptVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    parent_prompt_id: Optional[int] = Field(default=None, foreign_key="promptversion.id")
    content: str
    version_number: int
    is_active: bool
    triggering_sample_ids: str
    regression_passed: Optional[bool] = Field(default=None)
    base_passed: Optional[int] = Field(default=None)
    base_total: Optional[int] = Field(default=None)
    failed_cases: str
