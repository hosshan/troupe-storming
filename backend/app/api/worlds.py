from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database.config import get_db
from app.models import models, schemas

router = APIRouter(prefix="/worlds", tags=["worlds"])

@router.post("/", response_model=schemas.World)
def create_world(world: schemas.WorldCreate, db: Session = Depends(get_db)):
    db_world = models.World(**world.dict())
    db.add(db_world)
    db.commit()
    db.refresh(db_world)
    return db_world

@router.get("/", response_model=List[schemas.World])
def read_worlds(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    worlds = db.query(models.World).offset(skip).limit(limit).all()
    return worlds

@router.get("/{world_id}", response_model=schemas.World)
def read_world(world_id: int, db: Session = Depends(get_db)):
    world = db.query(models.World).filter(models.World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    return world

@router.put("/{world_id}", response_model=schemas.World)
def update_world(world_id: int, world_update: schemas.WorldUpdate, db: Session = Depends(get_db)):
    world = db.query(models.World).filter(models.World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    update_data = world_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(world, field, value)
    
    db.commit()
    db.refresh(world)
    return world

@router.delete("/{world_id}")
def delete_world(world_id: int, db: Session = Depends(get_db)):
    world = db.query(models.World).filter(models.World.id == world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    db.delete(world)
    db.commit()
    return {"message": "World deleted successfully"}