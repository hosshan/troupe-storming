import json
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import Character, Discussion, World

class TinyTroupeService:
    def __init__(self):
        pass
    
    def create_agent_from_character(self, character: Character) -> Dict[str, Any]:
        agent_config = {
            "name": character.name,
            "description": character.description,
            "personality": character.personality,
            "background": character.background,
        }
        
        if character.tinytroupe_config:
            agent_config.update(character.tinytroupe_config)
        
        return agent_config
    
    def setup_world_agents(self, world: World, characters: List[Character]) -> List[Dict[str, Any]]:
        agents = []
        for character in characters:
            agent_config = self.create_agent_from_character(character)
            agents.append(agent_config)
        
        return agents
    
    async def run_discussion(self, discussion: Discussion, characters: List[Character], world: World) -> Dict[str, Any]:
        try:
            agents = self.setup_world_agents(world, characters)
            
            discussion_prompt = f"""
            世界設定: {world.background}
            
            議論テーマ: {discussion.theme}
            詳細: {discussion.description}
            
            参加者:
            {chr(10).join([f"- {char.name}: {char.description}" for char in characters])}
            
            この設定で議論を開始してください。各キャラクターの個性と背景を活かした議論を展開してください。
            """
            
            result = {
                "discussion_id": discussion.id,
                "theme": discussion.theme,
                "world": world.name,
                "participants": [char.name for char in characters],
                "messages": [
                    {
                        "speaker": "システム",
                        "content": f"議論テーマ「{discussion.theme}」について話し合いを開始します。",
                        "timestamp": "2024-01-01T00:00:00Z"
                    }
                ],
                "status": "completed"
            }
            
            for i, character in enumerate(characters):
                sample_message = f"{character.name}の視点から「{discussion.theme}」について考えると、{character.personality}な性格を活かして議論に参加します。"
                result["messages"].append({
                    "speaker": character.name,
                    "content": sample_message,
                    "timestamp": f"2024-01-01T00:0{i+1}:00Z"
                })
            
            return result
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "failed"
            }
    
    def validate_character_config(self, config: Dict[str, Any]) -> bool:
        required_fields = ["name"]
        return all(field in config for field in required_fields)