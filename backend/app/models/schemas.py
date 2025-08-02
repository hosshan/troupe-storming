from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class WorldBase(BaseModel):
    name: str
    description: str
    background: str

class WorldCreate(WorldBase):
    pass

class WorldUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    background: Optional[str] = None

class World(WorldBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class CharacterBase(BaseModel):
    name: str
    description: str
    personality: str
    background: str
    world_id: int
    tinytroupe_config: Optional[Any] = None

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    tinytroupe_config: Optional[Any] = None

class Character(CharacterBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DiscussionBase(BaseModel):
    theme: str
    description: str
    world_id: int

class DiscussionCreate(DiscussionBase):
    pass

class DiscussionUpdate(BaseModel):
    theme: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    result: Optional[Any] = None

class Discussion(DiscussionBase):
    id: int
    status: str
    result: Optional[Any] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True