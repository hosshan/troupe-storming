from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import json
import asyncio
from app.database.config import get_db
from app.models import models, schemas
from app.services.world_generator import WorldGeneratorService

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

@router.post("/generate", response_model=dict)
async def generate_world(request: schemas.WorldGenerateRequest, db: Session = Depends(get_db)):
    """Generate a world and optionally characters from keywords."""
    generator = WorldGeneratorService()
    
    # Generate world and characters
    generated_data = await generator.generate_world_from_keywords(
        keywords=request.keywords,
        generate_characters=request.generate_characters,
        character_count=request.character_count
    )
    
    # Create the world in database
    world_data = {
        "name": generated_data["name"],
        "description": generated_data["description"],
        "background": generated_data["background"]
    }
    db_world = models.World(**world_data)
    db.add(db_world)
    db.commit()
    db.refresh(db_world)
    
    # Create characters if generated
    created_characters = []
    if "characters" in generated_data and request.generate_characters:
        for char_data in generated_data["characters"]:
            character_data = {
                "name": char_data["name"],
                "description": char_data["description"],
                "personality": char_data["personality"],
                "background": char_data["background"],
                "world_id": db_world.id
            }
            db_character = models.Character(**character_data)
            db.add(db_character)
            db.commit()
            db.refresh(db_character)
            created_characters.append({
                "id": db_character.id,
                "name": db_character.name,
                "description": db_character.description,
                "personality": db_character.personality,
                "background": db_character.background,
                "world_id": db_character.world_id,
                "created_at": db_character.created_at
            })
    
    return {
        "world": {
            "id": db_world.id,
            "name": db_world.name,
            "description": db_world.description,
            "background": db_world.background,
            "created_at": db_world.created_at
        },
        "characters": created_characters,
        "generated_by": generated_data.get("generated_by", "Unknown"),
        "keywords": request.keywords
    }

@router.get("/generate-stream")
async def generate_world_stream(
    keywords: str,
    generate_characters: bool = True,
    character_count: int = 3,
    db: Session = Depends(get_db)
):
    """Generate a world with real-time progress updates via Server-Sent Events."""
    
    async def event_generator():
        progress_data = {"current_message": "", "progress": 0, "completed": False, "result": None}
        
        def progress_callback(message: str, progress: int):
            progress_data["current_message"] = message
            progress_data["progress"] = progress
        
        try:
            # Send initial progress
            yield f"data: {json.dumps({'message': '🚀 開始します...', 'progress': 0, 'completed': False})}\n\n"
            await asyncio.sleep(0.1)
            
            generator = WorldGeneratorService()
            
            # Generate world and characters with progress callback
            generated_data = await generator.generate_world_from_keywords(
                keywords=keywords,
                generate_characters=generate_characters,
                character_count=character_count,
                progress_callback=progress_callback
            )
            
            # Send intermediate progress updates
            while progress_data["progress"] < 100:
                yield f"data: {json.dumps({'message': progress_data['current_message'], 'progress': progress_data['progress'], 'completed': False})}\n\n"
                await asyncio.sleep(0.2)
            
            # Create the world in database
            world_data = {
                "name": generated_data["name"],
                "description": generated_data["description"],
                "background": generated_data["background"]
            }
            db_world = models.World(**world_data)
            db.add(db_world)
            db.commit()
            db.refresh(db_world)
            
            # Create characters if generated
            created_characters = []
            if "characters" in generated_data and generate_characters:
                for char_data in generated_data["characters"]:
                    character_data = {
                        "name": char_data["name"],
                        "description": char_data["description"],
                        "personality": char_data["personality"],
                        "background": char_data["background"],
                        "world_id": db_world.id
                    }
                    db_character = models.Character(**character_data)
                    db.add(db_character)
                    db.commit()
                    db.refresh(db_character)
                    created_characters.append({
                        "id": db_character.id,
                        "name": db_character.name,
                        "description": db_character.description,
                        "personality": db_character.personality,
                        "background": db_character.background,
                        "world_id": db_character.world_id,
                        "created_at": db_character.created_at
                    })
            
            # Send final result
            result = {
                "world": {
                    "id": db_world.id,
                    "name": db_world.name,
                    "description": db_world.description,
                    "background": db_world.background,
                    "created_at": db_world.created_at
                },
                "characters": created_characters,
                "generated_by": generated_data.get("generated_by", "Unknown"),
                "keywords": keywords
            }
            
            yield f"data: {json.dumps({'message': '🎉 完了しました！', 'progress': 100, 'completed': True, 'result': result})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'message': f'❌ エラー: {str(e)}', 'progress': 0, 'completed': True, 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )