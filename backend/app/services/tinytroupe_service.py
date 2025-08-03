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

# Try to import TinyTroupe components
try:
    from tinytroupe.agent import TinyPerson
    from tinytroupe.environment import TinyWorld
    TINYTROUPE_AVAILABLE = True
    logger.info("TinyTroupe successfully imported")
except ImportError as e:
    logger.warning(f"TinyTroupe import failed: {e}")
    TINYTROUPE_AVAILABLE = False


class TinyTroupeService:
    def __init__(self):
        self.tinytroupe_available = TINYTROUPE_AVAILABLE
        self.openai_available = OPENAI_AVAILABLE
        
        if not self.tinytroupe_available:
            logger.warning("TinyTroupe is not available due to import issues.")
        else:
            logger.info("TinyTroupe is available and ready to use.")
        
        # Set OpenAI API key if available
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key:
            logger.info("OpenAI API key found and set")
            if self.openai_available:
                openai.api_key = self.api_key
        else:
            logger.warning("OPENAI_API_KEY not found in environment variables.")
        
        # Log overall service status
        logger.info(f"TinyTroupeService initialized - TinyTroupe: {self.tinytroupe_available}, OpenAI: {self.openai_available}, API Key: {bool(self.api_key)}")
    
    def create_agent_from_character(self, character: Character) -> Optional[Any]:
        """Create a TinyPerson agent from a Character model."""
        if not self.tinytroupe_available:
            logger.warning(f"❌ TinyTroupe not available for {character.name}")
            return None
            
        try:
            logger.info(f"🎭 Creating TinyPerson for '{character.name}'")
            
            # Create TinyPerson with character attributes
            agent = TinyPerson(name=character.name)
            logger.info(f"✅ TinyPerson instance created for {character.name}")
            
            # Define the agent with character traits - using a more comprehensive persona
            persona_definition = f"""
            あなたは{character.name}です。
            
            基本情報:
            - 名前: {character.name}
            - 説明: {character.description}
            - 性格: {character.personality}
            - 背景: {character.background}
            
            あなたは常にこの性格と背景に基づいて行動し、発言してください。
            議論では、あなたの個性と経験を活かした独自の視点を提供してください。
            """
            
            logger.info(f"📝 Defining persona for {character.name}")
            # Fix: define method requires key and value arguments
            agent.define('persona', persona_definition)
            logger.info(f"✅ Persona defined for {character.name}")
            
            # Set agent's personality traits if available
            if hasattr(agent, 'set_personality'):
                logger.info(f"🎭 Setting personality for {character.name}")
                agent.set_personality(character.personality)
                logger.info(f"✅ Personality set for {character.name}")
            
            # Add any additional configuration from tinytroupe_config
            if hasattr(character, 'tinytroupe_config') and character.tinytroupe_config:
                logger.info(f"⚙️ Applying tinytroupe_config for {character.name}")
                for key, value in character.tinytroupe_config.items():
                    if hasattr(agent, key):
                        setattr(agent, key, value)
                        logger.info(f"✅ Set {key} for {character.name}")
            
            logger.info(f"🎉 Successfully created TinyPerson agent for {character.name}")
            return agent
            
        except Exception as e:
            logger.error(f"❌ Error creating TinyPerson for {character.name}: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Full traceback: {traceback.format_exc()}")
            return None
    
    def setup_world_agents(self, world: World, characters: List[Character]) -> Tuple[Optional[Any], List[Any]]:
        """Create a TinyWorld and populate it with TinyPerson agents."""
        if not self.tinytroupe_available:
            logger.warning("❌ TinyTroupe not available")
            return None, []
            
        try:
            logger.info(f"🏗️ Creating TinyWorld for '{world.name}' with {len(characters)} characters")
            
            # Create the world environment
            tiny_world = TinyWorld(
                name=world.name,
                agents=[],  # Initialize with empty agents list
                initial_datetime=datetime.datetime.now()
            )
            
            logger.info(f"✅ TinyWorld '{world.name}' created successfully")
            
            # Set world context/background (remove deprecated method)
            # tiny_world.set_communication_display(True)  # This method may not exist in current version
            
            agents = []
            for i, character in enumerate(characters):
                logger.info(f"🤖 Creating agent {i+1}/{len(characters)}: {character.name}")
                agent = self.create_agent_from_character(character)
                if agent:
                    # Add agent to world
                    tiny_world.add_agent(agent)
                    agents.append(agent)
                    logger.info(f"✅ Added agent {character.name} to TinyWorld")
                else:
                    logger.error(f"❌ Failed to create agent for {character.name}")
            
            logger.info(f"🎯 Final result - TinyWorld: {tiny_world is not None}, Agents: {len(agents)}")
            return tiny_world, agents
            
        except Exception as e:
            logger.error(f"❌ Error setting up world and agents: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Full traceback: {traceback.format_exc()}")
            return None, []
    
    async def run_discussion(self, discussion: Discussion, characters: List[Character], world: World) -> Dict[str, Any]:
        """Run a discussion simulation using TinyTroupe or fallback methods."""
        logger.info(f"=== STARTING DISCUSSION: {discussion.theme} ===")
        logger.info(f"TinyTroupe available: {self.tinytroupe_available}")
        logger.info(f"OpenAI available: {self.openai_available}")
        logger.info(f"API key present: {bool(self.api_key)}")
        logger.info(f"Number of characters: {len(characters)}")
        
        try:
            # First try TinyTroupe if available
            if self.tinytroupe_available and self.api_key:
                logger.info("🚀 USING TINYTROUPE for discussion generation")
                result = await self._create_tinytroupe_discussion_result(discussion, characters, world)
                logger.info("✅ TinyTroupe discussion completed successfully")
                return result
            # Fall back to OpenAI direct if available
            elif self.openai_available and self.api_key:
                logger.warning("⚠️ FALLING BACK to OpenAI direct API (TinyTroupe not available)")
                result = await self._create_ai_discussion_result(discussion, characters, world)
                logger.info("✅ OpenAI direct discussion completed")
                return result
            else:
                # Fall back to mock result
                logger.warning("⚠️ FALLING BACK to mock data (no AI available)")
                result = self._create_mock_discussion_result(discussion, characters, world)
                logger.info("✅ Mock discussion completed")
                return result
                
        except Exception as e:
            logger.error(f"❌ Error in run_discussion: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _create_tinytroupe_discussion_result(self, discussion: Discussion, characters: List[Character], world: World) -> Dict[str, Any]:
        """Create a discussion using actual TinyTroupe library."""
        logger.info("🔧 Starting TinyTroupe discussion creation...")
        try:
            import os
            import asyncio
            
            # Set OpenAI API key for TinyTroupe
            os.environ['OPENAI_API_KEY'] = self.api_key
            logger.info("🔑 OpenAI API key set for TinyTroupe")
            
            # Create TinyWorld and agents
            logger.info("🌍 Creating TinyWorld and agents...")
            logger.info(f"📊 Input data - World: {world.name}, Characters: {[c.name for c in characters]}")
            
            tiny_world, agents = self.setup_world_agents(world, characters)
            
            logger.info(f"🔍 Setup result - TinyWorld: {tiny_world is not None}, Agents count: {len(agents) if agents else 0}")
            
            if not tiny_world:
                logger.error("❌ TinyWorld creation failed")
                return await self._create_ai_discussion_result(discussion, characters, world)
            
            if not agents:
                logger.error("❌ No agents created")
                return await self._create_ai_discussion_result(discussion, characters, world)
            
            logger.info(f"✅ Successfully created TinyWorld with {len(agents)} agents")
            
            messages = [
                {
                    "speaker": "システム",
                    "content": f"TinyTroupeによる議論「{discussion.theme}」を開始します。",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            ]
            
            # Set up the discussion topic in the world
            discussion_prompt = f"""
            議論テーマ: {discussion.theme}
            詳細: {discussion.description}
            
            各エージェントは自分の性格と背景に基づいて、このテーマについて意見を述べてください。
            建設的で多様な視点からの議論を行ってください。
            """
            
            # Have each agent think about and respond to the topic
            logger.info("💭 Starting agent discussions...")
            for i, agent in enumerate(agents):
                try:
                    logger.info(f"🤖 Processing agent {i+1}/{len(agents)}: {agent.name}")
                    
                    # Make the agent think about the topic
                    logger.info(f"🧠 Making {agent.name} think about the topic...")
                    think_result = agent.think(discussion_prompt)
                    logger.info(f"💡 {agent.name} thinking result: {str(think_result)[:100]}...")
                    
                    # Get the agent's response
                    logger.info(f"🗣️ Getting response from {agent.name}...")
                    response = agent.act(f"「{discussion.theme}」について、あなたの意見を2-3文で述べてください。")
                    logger.info(f"📝 {agent.name} response: {str(response)[:100]}...")
                    
                    if response:
                        # Extract the actual content from the response
                        content = response.get('content', str(response)) if isinstance(response, dict) else str(response)
                        
                        messages.append({
                            "speaker": agent.name,
                            "content": content,
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                        logger.info(f"✅ Added message from {agent.name}")
                    else:
                        logger.warning(f"⚠️ No response from {agent.name}")
                    
                    # Small delay to prevent API rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as agent_error:
                    logger.error(f"❌ Error getting response from agent {agent.name}: {agent_error}")
                    # Check if it's an API quota or rate limit error
                    error_str = str(agent_error).lower()
                    if "insufficient_quota" in error_str or "quota" in error_str:
                        logger.warning(f"OpenAI API quota exceeded for {agent.name}, using fallback response")
                        messages.append({
                            "speaker": agent.name,
                            "content": f"{agent.name}として、「{discussion.theme}」について考えています...（APIクォータ不足により詳細な応答ができません）",
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                    elif "rate_limit" in error_str or "429" in error_str:
                        logger.warning(f"OpenAI API rate limit exceeded for {agent.name}, using fallback response")
                        messages.append({
                            "speaker": agent.name,
                            "content": f"{agent.name}として、「{discussion.theme}」について考えています...（API制限により詳細な応答ができません）",
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                    else:
                        # Add a fallback response
                        messages.append({
                            "speaker": agent.name,
                            "content": f"{agent.name}として、「{discussion.theme}」について考えています...",
                            "timestamp": datetime.datetime.now().isoformat()
                        })
            
            # Try to get any additional world interactions
            logger.info("🌍 Running world simulation...")
            try:
                # Run a brief world simulation if possible
                logger.info("⚙️ Executing tiny_world.run(1)...")
                tiny_world.run(1)  # Run for 1 step
                logger.info("✅ World simulation completed")
                
                logger.info("📥 Extracting messages from world...")
                world_messages = self._extract_messages_from_world(tiny_world, agents)
                logger.info(f"📊 Extracted {len(world_messages)} messages from world")
                
                if len(world_messages) > 1:  # More than just the system message
                    messages.extend(world_messages[1:])  # Skip the duplicate system message
                    logger.info(f"➕ Added {len(world_messages)-1} world messages to discussion")
            except Exception as world_error:
                logger.warning(f"⚠️ World simulation step failed: {world_error}")
            
            return {
                "discussion_id": discussion.id,
                "theme": discussion.theme,
                "world": world.name,
                "participants": [char.name for char in characters],
                "messages": messages,
                "status": "completed",
                "note": "Real TinyTroupe discussion with AI agents"
            }
            
        except Exception as e:
            logger.error(f"Error in TinyTroupe discussion generation: {e}")
            # Check if it's an API quota or rate limit error
            error_str = str(e).lower()
            if "insufficient_quota" in error_str or "quota" in error_str:
                logger.warning("OpenAI API quota exceeded in TinyTroupe, falling back to mock discussion")
                return self._create_mock_discussion_result(discussion, characters, world, "TinyTroupe実行中にOpenAI APIクォータ不足が発生したためモックデータを使用")
            elif "rate_limit" in error_str or "429" in error_str:
                logger.warning("OpenAI API rate limit exceeded in TinyTroupe, falling back to mock discussion")
                return self._create_mock_discussion_result(discussion, characters, world, "TinyTroupe実行中にOpenAI API制限が発生したためモックデータを使用")
            else:
                # Fall back to AI discussion
                return await self._create_ai_discussion_result(discussion, characters, world)
    
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
                
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
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
                    
                except openai.RateLimitError as rate_limit_error:
                    logger.error(f"OpenAI API rate limit exceeded for {character.name}: {rate_limit_error}")
                    # Add a fallback response for this character
                    messages.append({
                        "speaker": character.name,
                        "content": f"{character.name}として、「{discussion.theme}」について考えています...（API制限により詳細な応答ができません）",
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                except openai.InsufficientQuotaError as quota_error:
                    logger.error(f"OpenAI API quota exceeded for {character.name}: {quota_error}")
                    # Add a fallback response for this character
                    messages.append({
                        "speaker": character.name,
                        "content": f"{character.name}として、「{discussion.theme}」について考えています...（APIクォータ不足により詳細な応答ができません）",
                        "timestamp": datetime.datetime.now().isoformat()
                    })
                except Exception as api_error:
                    logger.error(f"OpenAI API error for {character.name}: {api_error}")
                    # Add a fallback response for this character
                    messages.append({
                        "speaker": character.name,
                        "content": f"{character.name}として、「{discussion.theme}」について考えています...",
                        "timestamp": datetime.datetime.now().isoformat()
                    })
            
            return {
                "discussion_id": discussion.id,
                "theme": discussion.theme,
                "world": world.name,
                "participants": [char.name for char in characters],
                "messages": messages,
                "status": "completed",
                "note": "AI-powered discussion using OpenAI GPT-4o (with fallback handling)"
            }
            
        except Exception as e:
            logger.error(f"Error in AI discussion generation: {e}")
            # Check if it's a quota or rate limit error
            if "insufficient_quota" in str(e).lower() or "quota" in str(e).lower():
                logger.warning("OpenAI API quota exceeded, falling back to mock discussion")
                return self._create_mock_discussion_result(discussion, characters, world, "OpenAI APIクォータ不足のためモックデータを使用")
            elif "rate_limit" in str(e).lower() or "429" in str(e):
                logger.warning("OpenAI API rate limit exceeded, falling back to mock discussion")
                return self._create_mock_discussion_result(discussion, characters, world, "OpenAI API制限のためモックデータを使用")
            else:
                return self._create_mock_discussion_result(discussion, characters, world, f"AI API エラーのためモックデータを使用: {str(e)}")
    
    def _create_mock_discussion_result(self, discussion: Discussion, characters: List[Character], world: World, reason: str = "Mock result - TinyTroupe not available (Pydantic compatibility issue)") -> Dict[str, Any]:
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
            "note": reason
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
    
    async def run_discussion_with_streaming(self, discussion, characters, world, stream_data):
        """Run discussion with real-time streaming updates to stream_data"""
        logger.info(f"=== STARTING STREAMING DISCUSSION: {discussion.theme} ===")
        
        try:
            # First try TinyTroupe if available
            if self.tinytroupe_available and self.api_key:
                logger.info("🚀 USING TINYTROUPE for streaming discussion generation")
                result = await self._create_tinytroupe_streaming_discussion_result(
                    discussion, characters, world, stream_data
                )
                logger.info("✅ TinyTroupe streaming discussion completed successfully")
                return result
            # Fall back to OpenAI direct if available
            elif self.openai_available and self.api_key:
                logger.warning("⚠️ FALLING BACK to OpenAI direct API with streaming")
                result = await self._create_ai_streaming_discussion_result(
                    discussion, characters, world, stream_data
                )
                logger.info("✅ OpenAI direct streaming discussion completed")
                return result
            else:
                logger.warning("⚠️ FALLING BACK to mock data with streaming")
                result = await self._create_mock_streaming_discussion_result(
                    discussion, characters, world, stream_data
                )
                logger.info("✅ Mock streaming discussion completed")
                return result
                
        except Exception as e:
            logger.error(f"❌ Error in run_discussion_with_streaming: {e}")
            stream_data["error"] = str(e)
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _create_tinytroupe_streaming_discussion_result(self, discussion, characters, world, stream_data):
        """Create a discussion using TinyTroupe with real-time streaming"""
        logger.info("🔧 Starting TinyTroupe streaming discussion creation...")
        
        try:
            import os
            import asyncio
            
            # Set OpenAI API key for TinyTroupe
            os.environ['OPENAI_API_KEY'] = self.api_key
            logger.info("🔑 OpenAI API key set for TinyTroupe")
            
            # Update progress
            stream_data["progress"] = 75
            stream_data["message"] = "TinyTroupeエージェントを作成中..."
            
            # Create TinyWorld and agents
            tiny_world, agents = self.setup_world_agents(world, characters)
            
            if not tiny_world or not agents:
                logger.error("❌ TinyWorld or agents creation failed")
                # Fall back to AI discussion
                return await self._create_ai_streaming_discussion_result(discussion, characters, world, stream_data)
            
            logger.info(f"✅ Successfully created TinyWorld with {len(agents)} agents")
            
            # Initialize messages with system message
            messages = [
                {
                    "speaker": "システム",
                    "content": f"TinyTroupeによる議論「{discussion.theme}」を開始します。",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            ]
            stream_data["messages"] = messages
            
            # Set up the discussion topic
            discussion_prompt = f"""
            議論テーマ: {discussion.theme}
            詳細: {discussion.description}
            
            このテーマについて、あなたの性格と背景に基づいて意見を述べてください。
            建設的で多様な視点からの議論を行ってください。
            """
            
            # Update progress
            stream_data["progress"] = 80
            stream_data["message"] = f"{len(agents)}人のエージェントが議論を開始..."
            
            # Have each agent respond one by one with real-time updates
            logger.info("💭 Starting agent discussions with streaming...")
            for i, agent in enumerate(agents):
                try:
                    logger.info(f"🤖 Processing agent {i+1}/{len(agents)}: {agent.name}")
                    
                    # Update progress for each agent
                    progress = 80 + (15 * (i + 1) / len(agents))  # 80-95%
                    stream_data["progress"] = min(95, int(progress))
                    stream_data["message"] = f"{agent.name}が発言中..."
                    
                    # Make the agent think about the topic
                    logger.info(f"🧠 Making {agent.name} think about the topic...")
                    think_result = agent.think(discussion_prompt)
                    logger.info(f"💡 {agent.name} thinking result: {str(think_result)[:100]}...")
                    
                    # Get the agent's response
                    logger.info(f"🗣️ Getting response from {agent.name}...")
                    response = agent.act(f"「{discussion.theme}」について、あなたの意見を2-3文で述べてください。")
                    logger.info(f"📝 {agent.name} response: {str(response)[:100]}...")
                    
                    # Process the response
                    if response and str(response) != "None":
                        # Extract the actual content from the response
                        content = response.get('content', str(response)) if isinstance(response, dict) else str(response)
                        
                        # Add message immediately to stream
                        new_message = {
                            "speaker": agent.name,
                            "content": content,
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                        messages.append(new_message)
                        stream_data["messages"] = messages.copy()  # Update stream immediately
                        
                        logger.info(f"✅ Added streaming message from {agent.name}")
                    else:
                        logger.warning(f"⚠️ No response from {agent.name}, adding fallback message")
                        # Add a fallback response
                        fallback_message = {
                            "speaker": agent.name,
                            "content": f"{agent.name}として、「{discussion.theme}」について考えています...",
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                        messages.append(fallback_message)
                        stream_data["messages"] = messages.copy()
                    
                    # Small delay between agents
                    await asyncio.sleep(1)
                    
                except Exception as agent_error:
                    logger.error(f"❌ Error getting response from agent {agent.name}: {agent_error}")
                    # Add a fallback response for this agent
                    fallback_message = {
                        "speaker": agent.name,
                        "content": f"{agent.name}として、「{discussion.theme}」について考えています...（エラーが発生しました）",
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    messages.append(fallback_message)
                    stream_data["messages"] = messages.copy()
            
            return {
                "discussion_id": discussion.id,
                "theme": discussion.theme,
                "world": world.name,
                "participants": [char.name for char in characters],
                "messages": messages,
                "status": "completed",
                "note": "Real TinyTroupe streaming discussion with AI agents"
            }
            
        except Exception as e:
            logger.error(f"Error in TinyTroupe streaming discussion generation: {e}")
            error_str = str(e).lower()
            if "insufficient_quota" in error_str or "quota" in error_str:
                logger.warning("OpenAI API quota exceeded in streaming TinyTroupe, falling back to mock discussion")
                return await self._create_mock_streaming_discussion_result(discussion, characters, world, stream_data)
            elif "rate_limit" in error_str or "429" in error_str:
                logger.warning("OpenAI API rate limit exceeded in streaming TinyTroupe, falling back to mock discussion")
                return await self._create_mock_streaming_discussion_result(discussion, characters, world, stream_data)
            else:
                # Fall back to AI discussion
                return await self._create_ai_streaming_discussion_result(discussion, characters, world, stream_data)
    
    async def _create_ai_streaming_discussion_result(self, discussion, characters, world, stream_data):
        """Create an AI-powered discussion with streaming updates"""
        try:
            client = openai.OpenAI(api_key=self.api_key)
            
            messages = [
                {
                    "speaker": "システム",
                    "content": f"議論テーマ「{discussion.theme}」について話し合いを開始します。",
                    "timestamp": datetime.datetime.now().isoformat()
                }
            ]
            stream_data["messages"] = messages
            
            # Generate discussion for each character with streaming
            for i, character in enumerate(characters):
                # Update progress
                progress = 80 + (15 * (i + 1) / len(characters))  # 80-95%
                stream_data["progress"] = min(95, int(progress))
                stream_data["message"] = f"{character.name}が発言中..."
                
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
                
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "あなたは指定されたキャラクターとして自然な議論を行います。"},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=200,
                        temperature=0.8
                    )
                    
                    ai_response = response.choices[0].message.content.strip()
                    
                    new_message = {
                        "speaker": character.name,
                        "content": ai_response,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    messages.append(new_message)
                    stream_data["messages"] = messages.copy()  # Update stream immediately
                    
                except Exception as api_error:
                    logger.error(f"OpenAI API error for {character.name}: {api_error}")
                    # Add a fallback response for this character
                    fallback_message = {
                        "speaker": character.name,
                        "content": f"{character.name}として、「{discussion.theme}」について考えています...",
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    messages.append(fallback_message)
                    stream_data["messages"] = messages.copy()
                
                # Small delay between characters
                await asyncio.sleep(0.5)
            
            return {
                "discussion_id": discussion.id,
                "theme": discussion.theme,
                "world": world.name,
                "participants": [char.name for char in characters],
                "messages": messages,
                "status": "completed",
                "note": "AI-powered streaming discussion using OpenAI GPT-4o-mini"
            }
            
        except Exception as e:
            logger.error(f"Error in AI streaming discussion generation: {e}")
            return await self._create_mock_streaming_discussion_result(discussion, characters, world, stream_data)
    
    async def _create_mock_streaming_discussion_result(self, discussion, characters, world, stream_data):
        """Create a mock discussion with streaming updates"""
        
        messages = [
            {
                "speaker": "システム",
                "content": f"議論テーマ「{discussion.theme}」について話し合いを開始します。",
                "timestamp": datetime.datetime.now().isoformat()
            }
        ]
        stream_data["messages"] = messages
        
        # Generate streaming mock discussion
        for i, character in enumerate(characters):
            # Update progress
            progress = 80 + (15 * (i + 1) / len(characters))  # 80-95%
            stream_data["progress"] = min(95, int(progress))
            stream_data["message"] = f"{character.name}が発言中..."
            
            # Generate mock responses with delay
            discussion_points = [
                f"私は{character.personality}な性格なので、「{discussion.theme}」について{self._generate_mock_opinion(character, discussion.theme)}と思います。",
                f"{character.background}の経験から言うと、この問題は{self._generate_mock_perspective(character, discussion.theme)}",
            ]
            
            for j, point in enumerate(discussion_points):
                if i < 2 or j == 0:  # Limit messages for demo
                    new_message = {
                        "speaker": character.name,
                        "content": point,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    messages.append(new_message)
                    stream_data["messages"] = messages.copy()  # Update stream immediately
                    
                    # Small delay to simulate real conversation
                    await asyncio.sleep(1)
        
        return {
            "discussion_id": discussion.id,
            "theme": discussion.theme,
            "world": world.name,
            "participants": [char.name for char in characters],
            "messages": messages,
            "status": "completed",
            "note": "Mock streaming discussion - TinyTroupe not available or API issues"
        }
    
    def validate_character_config(self, config: Dict[str, Any]) -> bool:
        """Validate character configuration."""
        required_fields = ["name"]
        return all(field in config for field in required_fields)