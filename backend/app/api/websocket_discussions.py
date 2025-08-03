from fastapi import WebSocket, WebSocketDisconnect, Depends
from fastapi import APIRouter
import asyncio
import json
import logging
from sqlalchemy.orm import Session
from app.database.config import get_db
from app.models import models
from app.services.tinytroupe_service import TinyTroupeService
from typing import Dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active WebSocket connections
active_connections: Dict[int, WebSocket] = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, discussion_id: int):
        await websocket.accept()
        self.active_connections[discussion_id] = websocket
        logger.info(f"WebSocket connected for discussion {discussion_id}")

    def disconnect(self, discussion_id: int):
        if discussion_id in self.active_connections:
            del self.active_connections[discussion_id]
            logger.info(f"WebSocket disconnected for discussion {discussion_id}")

    async def send_message(self, discussion_id: int, data: dict):
        if discussion_id in self.active_connections:
            try:
                await self.active_connections[discussion_id].send_text(json.dumps(data))
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                self.disconnect(discussion_id)

manager = ConnectionManager()

@router.websocket("/discussions/{discussion_id}")
async def websocket_discussion_endpoint(
    websocket: WebSocket, 
    discussion_id: int,
    db: Session = Depends(get_db)
):
    await manager.connect(websocket, discussion_id)
    
    try:
        # Get discussion
        discussion = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
        if not discussion:
            await websocket.send_text(json.dumps({
                "error": "Discussion not found",
                "completed": True
            }))
            return

        # If discussion is completed, send existing results
        if discussion.status == "completed" and discussion.result:
            await websocket.send_text(json.dumps({
                "progress": 100,
                "message": "議論が完了しました",
                "completed": True,
                "messages": discussion.result.get("messages", [])
            }))
            return

        # If discussion is pending or running, start/continue it
        if discussion.status == "pending":
            discussion.status = "running"
            db.commit()
            
            # Start discussion with WebSocket streaming
            await run_discussion_with_websocket(discussion_id, db, manager)
        
        # Keep connection alive and listen for client messages
        while True:
            try:
                data = await websocket.receive_text()
                # Handle client messages if needed (e.g., pause, resume, etc.)
                client_data = json.loads(data)
                logger.info(f"Received client message: {client_data}")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for discussion {discussion_id}")
    finally:
        manager.disconnect(discussion_id)

async def run_discussion_with_websocket(discussion_id: int, db: Session, connection_manager: ConnectionManager):
    """Run discussion with WebSocket streaming updates"""
    tinytroupe_service = TinyTroupeService()
    
    try:
        discussion = db.query(models.Discussion).filter(models.Discussion.id == discussion_id).first()
        if not discussion:
            return
        
        world = db.query(models.World).filter(models.World.id == discussion.world_id).first()
        characters = db.query(models.Character).filter(models.Character.world_id == discussion.world_id).all()
        
        if not characters:
            await connection_manager.send_message(discussion_id, {
                "error": "No characters found in this world",
                "completed": True,
                "progress": 100
            })
            discussion.status = "failed"
            discussion.result = {"error": "No characters found in this world"}
            db.commit()
            return
        
        # Create streaming data structure for WebSocket
        class WebSocketStreamData(dict):
            def __init__(self, connection_manager, discussion_id):
                super().__init__()
                self.connection_manager = connection_manager
                self.discussion_id = discussion_id
                self["messages"] = []
                self["progress"] = 0
                self["completed"] = False
                self["error"] = None
                self["message"] = ""
            
            def __setitem__(self, key, value):
                super().__setitem__(key, value)
                # Immediately send update via WebSocket
                asyncio.create_task(self.send_update())
            
            async def send_update(self):
                data = {
                    "progress": self.get("progress", 0),
                    "message": self.get("message", ""),
                    "completed": self.get("completed", False),
                    "messages": self.get("messages", [])
                }
                if self.get("error"):
                    data["error"] = self["error"]
                
                await self.connection_manager.send_message(self.discussion_id, data)
        
        # Create WebSocket stream data
        stream_data = WebSocketStreamData(connection_manager, discussion_id)
        
        # Send initial progress
        stream_data.progress = 10
        stream_data.message = "TinyTroupeサービスを初期化中..."
        await stream_data.send_update()
        await asyncio.sleep(0.5)
        
        # Progress updates
        stream_data.progress = 30
        stream_data.message = f"{len(characters)}人のキャラクターをAIエージェントに変換中..."
        await stream_data.send_update()
        await asyncio.sleep(1)
        
        stream_data.progress = 50
        stream_data.message = f"議論環境「{world.name}」を準備中..."
        await stream_data.send_update()
        await asyncio.sleep(0.5)
        
        stream_data.progress = 70
        stream_data.message = f"議論「{discussion.theme}」を開始..."
        await stream_data.send_update()
        await asyncio.sleep(0.5)
        
        # Run the actual discussion with real-time WebSocket streaming
        result = await tinytroupe_service.run_discussion_with_streaming(
            discussion, characters, world, stream_data
        )
        
        # Send final results
        if "error" not in result:
            stream_data.progress = 100
            stream_data.message = "議論が完了しました"
            stream_data.completed = True
            stream_data.messages = result.get("messages", [])
            discussion.status = "completed"
        else:
            stream_data.error = result.get("error", "Unknown error")
            stream_data.progress = 100
            stream_data.message = "議論でエラーが発生しました"
            stream_data.completed = True
            discussion.status = "failed"
        
        await stream_data.send_update()
        discussion.result = result
        db.commit()
        
    except Exception as e:
        logger.error(f"Error in WebSocket discussion: {e}")
        await connection_manager.send_message(discussion_id, {
            "error": str(e),
            "progress": 100,
            "message": f"エラーが発生しました: {str(e)}",
            "completed": True
        })
        discussion.status = "failed"
        discussion.result = {"error": str(e)}
        db.commit()