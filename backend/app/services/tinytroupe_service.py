import json
import os
import datetime
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.models import Character, Discussion, World

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
    logger.info("OpenAI successfully imported")
except ImportError as e:
    logger.warning(f"OpenAI import failed: {e}")
    OPENAI_AVAILABLE = False

# Disable TinyTroupe for now due to Pydantic compatibility issues
TINYTROUPE_AVAILABLE = False


class TinyTroupeService:
    def __init__(self):
        self.tinytroupe_available = TINYTROUPE_AVAILABLE
        self.openai_available = OPENAI_AVAILABLE
        
        if not self.tinytroupe_available:
            logger.warning("TinyTroupe is not available due to Pydantic compatibility issues.")
        
        # Set OpenAI API key if available
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key:
            logger.info("OpenAI API key found and set")
            if self.openai_available:
                openai.api_key = self.api_key
        else:
            logger.warning("OPENAI_API_KEY not found in environment variables.")
    
    def create_agent_from_character(self, character: Character) -> Optional[Any]:
        """Create a TinyPerson agent from a Character model."""
        if not self.tinytroupe_available:
            return None
            
        try:
            # Create TinyPerson with character attributes
            agent = TinyPerson(name=character.name)
            
            # Define the agent with character traits
            agent.define(
                f"名前: {character.name}\n"
                f"説明: {character.description}\n"
                f"性格: {character.personality}\n"
                f"背景: {character.background}"
            )
            
            # Add any additional configuration from tinytroupe_config
            if character.tinytroupe_config:
                # Apply additional configuration if needed
                for key, value in character.tinytroupe_config.items():
                    if hasattr(agent, key):
                        setattr(agent, key, value)
            
            return agent
            
        except Exception as e:
            logger.error(f"Error creating TinyPerson for {character.name}: {e}")
            return None
    
    def setup_world_agents(self, world: World, characters: List[Character]) -> Tuple[Optional[Any], List[Any]]:
        """Create a TinyWorld and populate it with TinyPerson agents."""
        if not self.tinytroupe_available:
            return None, []
            
        try:
            # Create the world environment
            tiny_world = TinyWorld(
                name=world.name,
                context=f"{world.description}\n\n世界設定: {world.background}"
            )
            
            agents = []
            for character in characters:
                agent = self.create_agent_from_character(character)
                if agent:
                    # Add agent to world
                    tiny_world.add_agent(agent)
                    agents.append(agent)
            
            return tiny_world, agents
            
        except Exception as e:
            logger.error(f"Error setting up world and agents: {e}")
            return None, []
    
    async def run_discussion(self, discussion: Discussion, characters: List[Character], world: World) -> Dict[str, Any]:
        """Run an AI-powered discussion simulation."""
        try:
            # If OpenAI is available and API key is set, use real AI discussion
            if self.openai_available and self.api_key:
                return await self._create_ai_discussion_result(discussion, characters, world)
            else:
                # Fall back to mock result
                return self._create_mock_discussion_result(discussion, characters, world)
                
        except Exception as e:
            logger.error(f"Error in run_discussion: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _create_ai_discussion_result(self, discussion: Discussion, characters: List[Character], world: World) -> Dict[str, Any]:
        """Create an AI-powered discussion using OpenAI API."""
        try:
            client = openai.OpenAI(api_key=self.api_key)
            
            messages = [
                {
                    "speaker": "システム",
                    "content": f"議論テーマ「{discussion.theme}」について話し合いを開始します。",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            ]
            
            # Generate discussion for each character
            for character in characters:
                prompt = f"""
                あなたは{character.name}として振る舞ってください。
                
                キャラクター設定:
                - 名前: {character.name}
                - 説明: {character.description}
                - 性格: {character.personality}
                - 背景: {character.background}
                
                世界設定: {world.background}
                
                議論テーマ: {discussion.theme}
                詳細: {discussion.description}
                
                {character.name}として、このテーマについてあなたの意見を2-3文で述べてください。
                性格と背景を反映した自然な発言をしてください。
                """
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "あなたは指定されたキャラクターとして自然な議論を行います。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.8
                )
                
                ai_response = response.choices[0].message.content.strip()
                
                messages.append({
                    "speaker": character.name,
                    "content": ai_response,
                    "timestamp": datetime.datetime.now().isoformat()
                })
            
            return {
                "discussion_id": discussion.id,
                "theme": discussion.theme,
                "world": world.name,
                "participants": [char.name for char in characters],
                "messages": messages,
                "status": "completed",
                "note": "AI-powered discussion using OpenAI GPT-3.5"
            }
            
        except Exception as e:
            logger.error(f"Error in AI discussion generation: {e}")
            return self._create_mock_discussion_result(discussion, characters, world)
    
    def _create_mock_discussion_result(self, discussion: Discussion, characters: List[Character], world: World) -> Dict[str, Any]:
        """Create a mock discussion result when TinyTroupe is not available."""
        
        messages = [
            {
                "speaker": "システム",
                "content": f"議論テーマ「{discussion.theme}」について話し合いを開始します。",
                "timestamp": datetime.datetime.now().isoformat()
            }
        ]
        
        # Generate more realistic mock discussion
        for i, character in enumerate(characters):
            discussion_points = [
                f"私は{character.personality}な性格なので、「{discussion.theme}」について{self._generate_mock_opinion(character, discussion.theme)}と思います。",
                f"{character.background}の経験から言うと、この問題は{self._generate_mock_perspective(character, discussion.theme)}",
                f"皆さんの意見を聞いて、{character.name}としては{self._generate_mock_response(character, discussion.theme)}"
            ]
            
            for j, point in enumerate(discussion_points):
                if j < 2 or i == 0:  # First character gets all points, others get fewer
                    messages.append({
                        "speaker": character.name,
                        "content": point,
                        "timestamp": datetime.datetime.now().isoformat()
                    })
        
        return {
            "discussion_id": discussion.id,
            "theme": discussion.theme,
            "world": world.name,
            "participants": [char.name for char in characters],
            "messages": messages,
            "status": "completed",
            "note": "Mock result - TinyTroupe not available (Pydantic compatibility issue)"
        }
    
    def _generate_mock_opinion(self, character: Character, theme: str) -> str:
        """Generate a mock opinion based on character traits."""
        opinions = [
            "重要な視点が必要",
            "慎重に検討すべき",
            "積極的に取り組むべき",
            "バランスを考えることが大切",
            "実用的なアプローチが必要"
        ]
        return opinions[hash(character.name + theme) % len(opinions)]
    
    def _generate_mock_perspective(self, character: Character, theme: str) -> str:
        """Generate a mock perspective based on character background."""
        perspectives = [
            "多角的な視点で考える必要があります。",
            "実践的な解決策を見つけることが重要です。",
            "長期的な影響を考慮すべきです。",
            "関係者全員の利益を考える必要があります。",
            "革新的なアイデアが求められています。"
        ]
        return perspectives[hash(character.background + theme) % len(perspectives)]
    
    def _generate_mock_response(self, character: Character, theme: str) -> str:
        """Generate a mock response based on character."""
        responses = [
            "この方向で進めていくのが良いと考えます。",
            "更なる議論が必要だと感じます。",
            "具体的な行動計画を立てるべきです。",
            "みんなで協力して取り組みましょう。",
            "新しい可能性を探ってみませんか。"
        ]
        return responses[hash(character.name + character.personality + theme) % len(responses)]
    
    def _extract_messages_from_world(self, tiny_world: Any, agents: List[Any]) -> List[Dict[str, Any]]:
        """Extract conversation messages from TinyWorld interactions."""
        
        messages = [
            {
                "speaker": "システム",
                "content": "TinyTroupeによる議論を開始しました。",
                "timestamp": datetime.datetime.now().isoformat()
            }
        ]
        
        try:
            # Try to get communications from the world
            communications = getattr(tiny_world, 'communication_buffer', [])
            
            if communications:
                for comm in communications:
                    if hasattr(comm, 'content') and hasattr(comm, 'source'):
                        messages.append({
                            "speaker": getattr(comm.source, 'name', 'Unknown'),
                            "content": comm.content,
                            "timestamp": datetime.datetime.now().isoformat()
                        })
            else:
                # Try alternative methods to get agent interactions
                for agent in agents:
                    # Get agent's current actions or thoughts
                    if hasattr(agent, 'episodic_memory') and agent.episodic_memory:
                        recent_memories = agent.episodic_memory.retrieve_all()[-3:]  # Get last 3 memories
                        for memory in recent_memories:
                            if hasattr(memory, 'content') and memory.content:
                                messages.append({
                                    "speaker": agent.name,
                                    "content": memory.content,
                                    "timestamp": datetime.datetime.now().isoformat()
                                })
                    else:
                        # Fallback: generate a sample response
                        messages.append({
                            "speaker": agent.name,
                            "content": f"{agent.name}として議論に参加しています。",
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                        
        except Exception as e:
            logger.error(f"Error extracting messages: {e}")
            # Fallback: create sample messages based on agents
            for agent in agents:
                messages.append({
                    "speaker": agent.name,
                    "content": f"{agent.name}からの議論への参加です。",
                    "timestamp": datetime.datetime.now().isoformat()
                })
        
        return messages
    
    def validate_character_config(self, config: Dict[str, Any]) -> bool:
        """Validate character configuration."""
        required_fields = ["name"]
        return all(field in config for field in required_fields)