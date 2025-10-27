from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ArtigoCitacao(BaseModel):
    paper_id: str
    title: Optional[str]
    section: Optional[str]
    content: Optional[str]
    created_at: datetime = Field(default_factory=datetime.now)

class Artigo(BaseModel):
    paper_id: str
    title: str | None
    section: str | None
    text: str | None
    created_at: datetime = Field(default_factory=datetime.now)

