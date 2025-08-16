from pydantic import BaseModel, Field, AliasChoices
from typing import List, Optional

class Module(BaseModel):
    name: str
    lessons: List[str] = Field(..., description="3–7 concise lesson titles in logical order")

class Curriculum(BaseModel):
    topic: str
    level: str = "beginner"
    goal: Optional[str] = None
    modules: List[Module]

class Review(BaseModel):
    approved: bool
    issues: List[str] = []
    revision_instructions: str = ""

class DetailedTopic(BaseModel):
    title: str
    subtopics: List[str] = Field(..., validation_alias=AliasChoices("subtopics", "subtopic"))

class DetailedSyllabus(BaseModel):
    topic: str
    outline: List[DetailedTopic]
