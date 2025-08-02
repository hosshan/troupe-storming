from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database.config import get_db
from app.models import models, schemas
from app.services.tinytroupe_service import TinyTroupeService

router = APIRouter(prefix="/discussions", tags=["discussions"])

@router.post("/", response_model=schemas.Discussion)
def create_discussion(discussion: schemas.DiscussionCreate, db: Session = Depends(get_db)):
    world = db.query(models.World).filter(models.World.id == discussion.world_id).first()
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    db_discussion = models.Discussion(**discussion.dict())
    db.add(db_discussion)
    db.commit()
    db.refresh(db_discussion)
    return db_discussion

@router.get("/", response_model=List[schemas.Discussion])
def read_discussions(world_id: int = None, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(models.Discussion)
    if world_id:
        query = query.filter(models.Discussion.world_id == world_id)
    discussions = query.offset(skip).limit(limit).all()
    return discussions

@router.get("/{discussion_id}", response_model=schemas.Discussion)
def read_discussion(discussion_id: int, db: Session = Depends(get_db)):
    discussion = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    return discussion

async def run_discussion_background(discussion_id: int, db: Session):
    tinytroupe_service = TinyTroupeService()
    
    discussion = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
    if not discussion:
        return
    
    world = db.query(models.World).filter(models.World.id == discussion.world_id).first()
    characters = db.query(models.Character).filter(models.Character.world_id == discussion.world_id).all()
    
    if not characters:
        discussion.status = "failed"
        discussion.result = {"error": "No characters found in this world"}
        db.commit()
        return
    
    result = await tinytroupe_service.run_discussion(discussion, characters, world)
    
    discussion.status = "completed" if "error" not in result else "failed"
    discussion.result = result
    db.commit()

@router.post("/{discussion_id}/start")
async def start_discussion(discussion_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    discussion = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    
    if discussion.status != "pending":
        raise HTTPException(status_code=400, detail="Discussion already started or completed")
    
    discussion.status = "running"
    db.commit()
    
    background_tasks.add_task(run_discussion_background, discussion_id, db)
    
    return {"message": "Discussion started", "discussion_id": discussion_id}

@router.put("/{discussion_id}", response_model=schemas.Discussion)
def update_discussion(discussion_id: int, discussion_update: schemas.DiscussionUpdate, db: Session = Depends(get_db)):
    discussion = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    
    update_data = discussion_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(discussion, field, value)
    
    db.commit()
    db.refresh(discussion)
    return discussion