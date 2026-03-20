from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String
from sqlmodel import Field, SQLModel


class Subscription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    category: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(default=True)


class SummaryCache(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(sa_column=Column(String, unique=True, index=True))
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
