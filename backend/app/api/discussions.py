from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, AsyncGenerator
import asyncio
import json
import time
from app.database.config import get_db
from app.models import models, schemas
from app.services.tinytroupe_service import TinyTroupeService

router = APIRouter(prefix="/discussions", tags=["discussions"])

# Global dictionary to store discussion streams and active connections
discussion_streams = {}
active_connections = {}

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

async def run_discussion_with_streaming(discussion_id: int, db: Session):
    """Run discussion with streaming updates"""
    tinytroupe_service = TinyTroupeService()
    
    discussion = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
    if not discussion:
        return
    
    world = db.query(models.World).filter(models.World.id == discussion.world_id).first()
    characters = db.query(models.Character).filter(models.Character.world_id == discussion.world_id).all()
    
    # Initialize stream data
    stream_data = {
        "messages": [],
        "progress": 0,
        "completed": False,
        "error": None,
        "start_time": time.time()
    }
    discussion_streams[discussion_id] = stream_data
    
    try:
        if not characters:
            stream_data["error"] = "No characters found in this world"
            stream_data["completed"] = True
            discussion.status = "failed"
            discussion.result = {"error": "No characters found in this world"}
            db.commit()
            return
        
        # Update progress: Starting
        stream_data["progress"] = 10
        stream_data["message"] = "TinyTroupeサービスを初期化中..."
        await asyncio.sleep(0.5)
        
        # Update progress: Creating agents
        stream_data["progress"] = 30
        stream_data["message"] = f"{len(characters)}人のキャラクターをAIエージェントに変換中..."
        await asyncio.sleep(1)
        
        # Update progress: Setting up world
        stream_data["progress"] = 50
        stream_data["message"] = f"議論環境「{world.name}」を準備中..."
        await asyncio.sleep(0.5)
        
        # Update progress: Starting discussion
        stream_data["progress"] = 70
        stream_data["message"] = f"議論「{discussion.theme}」を開始..."
        await asyncio.sleep(0.5)
        
        # Run the actual discussion with streaming updates
        result = await tinytroupe_service.run_discussion_with_streaming(
            discussion, characters, world, stream_data
        )
        
        # Update with final results
        if "error" not in result:
            stream_data["messages"] = result.get("messages", [])
            stream_data["progress"] = 100
            stream_data["message"] = "議論が完了しました"
            discussion.status = "completed"
        else:
            stream_data["error"] = result.get("error", "Unknown error")
            stream_data["progress"] = 100
            stream_data["message"] = "議論でエラーが発生しました"
            discussion.status = "failed"
        
        discussion.result = result
        db.commit()
        
    except Exception as e:
        stream_data["error"] = str(e)
        stream_data["progress"] = 100
        stream_data["message"] = f"エラーが発生しました: {str(e)}"
        discussion.status = "failed"
        discussion.result = {"error": str(e)}
        db.commit()
    
    finally:
        stream_data["completed"] = True
        print(f"Discussion {discussion_id} completed, setting completed=True")  # デバッグログを追加
        # Clean up after a delay to allow final message to be sent
        asyncio.create_task(cleanup_discussion_stream(discussion_id, delay=5))

async def cleanup_discussion_stream(discussion_id: int, delay: int = 5):
    """Clean up discussion stream after delay"""
    await asyncio.sleep(delay)
    if discussion_id in discussion_streams:
        del discussion_streams[discussion_id]
    if discussion_id in active_connections:
        del active_connections[discussion_id]

async def discussion_event_generator(discussion_id: int, request: Request) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events for discussion progress"""
    
    # Track this connection
    active_connections[discussion_id] = True
    
    try:
        # Wait for stream to be initialized with timeout
        max_wait = 30  # 30 seconds timeout
        wait_count = 0
        while discussion_id not in discussion_streams and wait_count < max_wait:
            # Check if client disconnected
            if await request.is_disconnected():
                return
            await asyncio.sleep(1)
            wait_count += 1
        
        if discussion_id not in discussion_streams:
            yield f"data: {json.dumps({'error': 'Discussion stream not found', 'completed': True})}\n\n"
            return
        
        stream_data = discussion_streams[discussion_id]
        last_message_count = 0
        last_progress = -1
        max_duration = 300  # 5 minutes max duration
        
        while not stream_data["completed"]:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            
            # Check for timeout
            if time.time() - stream_data["start_time"] > max_duration:
                stream_data["error"] = "Discussion timeout"
                stream_data["completed"] = True
                break
            
            current_data = {
                "progress": stream_data["progress"],
                "message": stream_data.get("message", ""),
                "completed": stream_data["completed"],
                "messages": stream_data["messages"]
            }
            
            if stream_data["error"]:
                current_data["error"] = stream_data["error"]
            
            # Only send update if there's new data
            if (len(stream_data["messages"]) != last_message_count or 
                stream_data["progress"] != last_progress):
                
                yield f"data: {json.dumps(current_data)}\n\n"
                last_message_count = len(stream_data["messages"])
                last_progress = stream_data["progress"]
            
            await asyncio.sleep(1)  # Check every second
        
        # Send final update
        final_data = {
            "progress": stream_data["progress"],
            "message": stream_data.get("message", ""),
            "completed": True,
            "messages": stream_data["messages"]
        }
        
        if stream_data["error"]:
            final_data["error"] = stream_data["error"]
        
        print(f"Sending final update for discussion {discussion_id}:", final_data)  # デバッグログを追加
        yield f"data: {json.dumps(final_data)}\n\n"
        
    finally:
        # Clean up connection tracking
        if discussion_id in active_connections:
            del active_connections[discussion_id]

@router.get("/{discussion_id}/stream")
async def stream_discussion_progress(discussion_id: int, request: Request, db: Session = Depends(get_db)):
    """Stream discussion progress using Server-Sent Events"""
    discussion = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
    if not discussion:
        raise HTTPException(status_code=404, detail="Discussion not found")
    
    # Handle different discussion states
    if discussion.status == "pending":
        discussion.status = "running"
        db.commit()
        
        # Start background task
        asyncio.create_task(run_discussion_with_streaming(discussion_id, db))
    elif discussion.status == "completed" and discussion.result:
        # For completed discussions, create a mock stream with existing results
        stream_data = {
            "messages": discussion.result.get("messages", []),
            "progress": 100,
            "completed": True,
            "error": None,
            "message": "議論が完了しました",
            "start_time": time.time()
        }
        discussion_streams[discussion_id] = stream_data
    elif discussion.status == "running":
        # Discussion already running, try to reconnect to stream
        if discussion_id not in discussion_streams:
            # Create a fallback stream for running discussions
            stream_data = {
                "messages": [],
                "progress": 50,
                "completed": False,
                "error": None,
                "message": "議論を実行中です...",
                "start_time": time.time()
            }
            discussion_streams[discussion_id] = stream_data
    
    return StreamingResponse(
        discussion_event_generator(discussion_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@router.delete("/{discussion_id}/stream")
async def stop_discussion_stream(discussion_id: int):
    """Stop and cleanup discussion stream"""
    if discussion_id in discussion_streams:
        discussion_streams[discussion_id]["completed"] = True
        discussion_streams[discussion_id]["error"] = "Stream stopped by user"
    
    if discussion_id in active_connections:
        del active_connections[discussion_id]
    
    return {"message": "Discussion stream stopped"}