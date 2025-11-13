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

class Metadata(BaseModel):
    cord_uid: str
    sha: Optional[str] = None
    source_x: Optional[str] = None
    title: Optional[str] = None
    doi: Optional[str] = None
    pmcid: Optional[str] = None
    pubmed_id: Optional[str] = None
    license: Optional[str] = None
    abstract: Optional[str] = None
    publish_time: Optional[str] = None
    authors: Optional[str] = None
    journal: Optional[str] = None
    mag_id: Optional[str] = None
    who_covidence_id: Optional[str] = None
    arxiv_id: Optional[str] = None
    pdf_json_files: Optional[str] = None
    pmc_json_files: Optional[str] = None
    url: Optional[str] = None
    s2_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

class ArtigoStaging(BaseModel):
    paper_id: str
    file_name: str
    title: str
    body_text: str
    created_at: datetime = Field(default_factory=datetime.now)
