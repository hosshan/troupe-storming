import json
import os
import datetime
import logging
import asyncio
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
    
    def _create_system_message(self, discussion) -> dict:
        """議論開始システムメッセージを生成"""
        return {
            "speaker": "システム",
            "content": f"議論テーマ「{discussion.theme}」について話し合いを開始します。",
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def _create_discussion_response(self, discussion, world, characters, messages, note, status="completed") -> dict:
        """共通の議論レスポンス形式を生成"""
        return {
            "discussion_id": discussion.id,
            "theme": discussion.theme,
            "world": world.name,
            "participants": [char.name for char in characters],
            "messages": messages,
            "status": status,
            "note": note
        }
    
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
    
    async def setup_world_agents(self, world: World, characters: List[Character], stream_data=None) -> Tuple[Optional[Any], List[Any]]:
        """Create a TinyWorld and populate it with TinyPerson agents."""
        if not self.tinytroupe_available:
            logger.warning("❌ TinyTroupe not available")
            return None, []
            
        try:
            # Clear global registries to avoid name conflicts
            logger.info("🧹 Clearing TinyTroupe global registries...")
            from tinytroupe.agent import TinyPerson
            from tinytroupe.environment import TinyWorld
            TinyPerson.clear_agents()
            TinyWorld.clear_environments()
            logger.info("✅ TinyTroupe global registries cleared")
            
            logger.info(f"🏗️ Creating TinyWorld for '{world.name}' with {len(characters)} characters")
            
            # Stream progress: Starting world creation
            if stream_data:
                stream_data["progress"] = 20
                stream_data["message"] = f"世界「{world.name}」を作成中..."
                await asyncio.sleep(0.1)  # Allow stream to update
            
            # Create unique world name to avoid conflicts
            import uuid
            unique_world_name = f"{world.name}_{uuid.uuid4().hex[:8]}"
            logger.info(f"🆔 Using unique world name: {unique_world_name}")
            
            # Check existing environments and log them for debugging
            try:
                if hasattr(TinyWorld, '_environments') and TinyWorld._environments:
                    existing_envs = list(TinyWorld._environments.keys())
                    logger.info(f"📋 Existing environments: {existing_envs}")
                    
                    # If the world name already exists, log a warning
                    if world.name in existing_envs:
                        logger.warning(f"⚠️ World '{world.name}' already exists in TinyTroupe registry")
            except Exception as check_error:
                logger.warning(f"⚠️ Could not check existing environments: {check_error}")
            
            # Stream progress: Creating TinyWorld instance
            if stream_data:
                stream_data["progress"] = 30
                stream_data["message"] = f"TinyWorld環境「{unique_world_name}」を初期化中..."
                await asyncio.sleep(0.1)
            
            # Create the world environment
            tiny_world = TinyWorld(
                name=unique_world_name,
                agents=[],  # Initialize with empty agents list
                initial_datetime=datetime.datetime.now()
            )
            
            logger.info(f"✅ TinyWorld '{unique_world_name}' created successfully")
            
            # Set world context/background (remove deprecated method)
            # tiny_world.set_communication_display(True)  # This method may not exist in current version
            
            agents = []
            for i, character in enumerate(characters):
                logger.info(f"🤖 Creating agent {i+1}/{len(characters)}: {character.name}")
                
                # Stream progress: Creating each agent
                if stream_data:
                    progress = 40 + (30 * i / len(characters))  # 40-70%
                    stream_data["progress"] = int(progress)
                    stream_data["message"] = f"AIエージェント「{character.name}」を作成中... ({i+1}/{len(characters)})"
                    await asyncio.sleep(0.2)
                
                agent = self.create_agent_from_character(character)
                if agent:
                    # Add agent to world
                    tiny_world.add_agent(agent)
                    agents.append(agent)
                    logger.info(f"✅ Added agent {character.name} to TinyWorld")
                    
                    # Stream progress: Agent created successfully
                    if stream_data:
                        stream_data["message"] = f"✅ エージェント「{character.name}」が世界に参加しました"
                        await asyncio.sleep(0.3)
                else:
                    logger.error(f"❌ Failed to create agent for {character.name}")
                    if stream_data:
                        stream_data["message"] = f"❌ エージェント「{character.name}」の作成に失敗"
                        await asyncio.sleep(0.2)
            
            logger.info(f"🎯 Final result - TinyWorld: {tiny_world is not None}, Agents: {len(agents)}")
            return tiny_world, agents
            
        except Exception as e:
            logger.error(f"❌ Error setting up world and agents: {e}")
            logger.error(f"🔍 Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"📋 Full traceback: {traceback.format_exc()}")
            
            # Special handling for environment name conflicts
            if "Environment names must be unique" in str(e):
                logger.warning("🔄 Attempting retry with timestamp-based world name...")
                try:
                    import time
                    timestamp_world_name = f"{world.name}_{int(time.time() * 1000)}"
                    logger.info(f"🕐 Using timestamp-based world name: {timestamp_world_name}")
                    
                    tiny_world_retry = TinyWorld(
                        name=timestamp_world_name,
                        agents=[],
                        initial_datetime=datetime.datetime.now()
                    )
                    
                    agents = []
                    for character in characters:
                        agent = self.create_agent_from_character(character)
                        if agent:
                            tiny_world_retry.add_agent(agent)
                            agents.append(agent)
                    
                    logger.info(f"✅ Retry successful with {len(agents)} agents")
                    return tiny_world_retry, agents
                    
                except Exception as retry_error:
                    logger.error(f"❌ Retry also failed: {retry_error}")
            
            return None, []
    
    async def run_discussion(self, discussion: Discussion, characters: List[Character], world: World, stream_data=None, discussion_id=None) -> Dict[str, Any]:
        """Run a discussion simulation using TinyTroupe or fallback methods with optional streaming support."""
        logger.info(f"=== STARTING DISCUSSION: {discussion.theme} ===")
        logger.info(f"TinyTroupe available: {self.tinytroupe_available}")
        logger.info(f"OpenAI available: {self.openai_available}")
        logger.info(f"API key present: {bool(self.api_key)}")
        logger.info(f"Number of characters: {len(characters)}")
        logger.info(f"Streaming mode: {stream_data is not None}")
        
        try:
            # Use unified provider selection logic
            providers = ['tinytroupe', 'openai', 'mock']
            
            for provider in providers:
                try:
                    if provider == 'tinytroupe' and self.tinytroupe_available and self.api_key:
                        logger.info("🚀 USING TINYTROUPE for discussion generation")
                        result = await self._create_discussion_result(
                            'tinytroupe', discussion, characters, world, stream_data, discussion_id
                        )
                        logger.info("✅ TinyTroupe discussion completed successfully")
                        return result
                    elif provider == 'openai' and self.openai_available and self.api_key:
                        logger.warning("⚠️ FALLING BACK to OpenAI direct API")
                        result = await self._create_discussion_result(
                            'openai', discussion, characters, world, stream_data, discussion_id
                        )
                        logger.info("✅ OpenAI direct discussion completed")
                        return result
                    elif provider == 'mock':
                        logger.warning("⚠️ FALLING BACK to mock data (no AI available)")
                        result = await self._create_discussion_result(
                            'mock', discussion, characters, world, stream_data, discussion_id
                        )
                        logger.info("✅ Mock discussion completed")
                        return result
                except Exception as provider_error:
                    logger.warning(f"{provider} provider failed: {provider_error}")
                    continue
            
            # If we get here, all providers failed
            raise Exception("All discussion providers failed")
                
        except Exception as e:
            logger.error(f"❌ Error in run_discussion: {e}")
            if stream_data:
                stream_data["error"] = str(e)
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def _create_discussion_result(self, provider: str, discussion, characters, world, stream_data=None, discussion_id=None):
        """統合された議論生成メソッド（ストリーミング対応）"""
        # 共通処理
        messages = [self._create_system_message(discussion)]
        if stream_data:
            stream_data["messages"] = messages
        
        if provider == 'tinytroupe':
            if stream_data:
                return await self._create_tinytroupe_streaming_discussion_result(
                    discussion, characters, world, stream_data, discussion_id
                )
            else:
                return await self._create_tinytroupe_discussion_result(
                    discussion, characters, world
                )
        elif provider == 'openai':
            if stream_data:
                return await self._create_ai_streaming_discussion_result(
                    discussion, characters, world, stream_data, discussion_id
                )
            else:
                return await self._create_ai_discussion_result(
                    discussion, characters, world
                )
        else:  # mock
            if stream_data:
                return await self._create_mock_streaming_discussion_result(
                    discussion, characters, world, stream_data, discussion_id
                )
            else:
                return self._create_mock_discussion_result(
                    discussion, characters, world
                )
    
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
            
            tiny_world, agents = await self.setup_world_agents(world, characters)
            
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
            discussion_prompt = f"議論テーマ: {discussion.theme}"
            
            # Make all agents accessible to each other for conversation
            try:
                if hasattr(tiny_world, 'make_everyone_accessible'):
                    tiny_world.make_everyone_accessible()
                    logger.info("✅ Made all agents accessible to each other")
            except Exception as e:
                logger.warning(f"⚠️ Could not make agents accessible: {e}")
            
            # Have each agent think about and respond to the topic
            logger.info("💭 Starting agent discussions...")
            for i, agent in enumerate(agents):
                try:
                    logger.info(f"🤖 Processing agent {i+1}/{len(agents)}: {agent.name}")
                    
                    # Make the agent think about the topic
                    logger.info(f"🧠 Making {agent.name} think about the topic...")
                    try:
                        think_result = agent.think(discussion_prompt)
                        logger.info(f"💡 {agent.name} thinking completed")
                    except Exception as think_error:
                        logger.warning(f"⚠️ Thinking failed for {agent.name}: {think_error}")
                        # Continue without thinking step
                    
                    # Get the agent's response using listen_and_act
                    logger.info(f"🗣️ Getting response from {agent.name}...")
                    agent.listen_and_act(f"「{discussion.theme}」について、簡潔に意見を述べてください。")
                    response = agent.pop_actions_and_get_contents_for("TALK", False)
                    logger.info(f"📝 {agent.name} response: {response}...")
                    
                    # Try to extract actual conversation content from agent
                    content = None
                    
                    # First, try to get from the world's communication buffer (most recent)
                    if hasattr(tiny_world, 'communication_buffer'):
                        communications = getattr(tiny_world, 'communication_buffer', [])
                        if communications:
                            # Get the most recent communication from this agent
                            for comm in reversed(communications[-10:]):  # Check last 10 communications
                                if hasattr(comm, 'source') and hasattr(comm, 'content'):
                                    speaker_name = getattr(comm.source, 'name', '')
                                    if speaker_name == agent.name:
                                        comm_content = str(comm.content)
                                        if comm_content and len(comm_content.strip()) > 10:
                                            content = comm_content
                                            logger.info(f"💬 Found recent communication from {agent.name}: {content[:50]}...")
                                            break
                    
                    # If no communication found, try to get from agent's episodic memory
                    if not content and hasattr(agent, 'episodic_memory') and agent.episodic_memory:
                        recent_memories = agent.episodic_memory.retrieve_all()
                        if recent_memories:
                            # Get the most recent memory that contains actual content
                            for memory in reversed(recent_memories[-5:]):  # Check last 5 memories
                                if hasattr(memory, 'content') and memory.content and len(str(memory.content)) > 10:
                                    content = str(memory.content)
                                    logger.info(f"📚 Found content from {agent.name}'s memory: {content[:50]}...")
                                    break
                    
                    # If no memory content, try to get from agent's current state
                    if not content and hasattr(agent, 'current_action'):
                        current_action = getattr(agent, 'current_action', None)
                        if current_action and str(current_action) != "None":
                            content = str(current_action)
                            logger.info(f"🎭 Found content from {agent.name}'s current action: {content[:50]}...")
                    
                    # If still no content, try to get from agent's last communication
                    if not content and hasattr(agent, 'last_communication'):
                        last_comm = getattr(agent, 'last_communication', None)
                        if last_comm and str(last_comm) != "None":
                            content = str(last_comm)
                            logger.info(f"💬 Found content from {agent.name}'s last communication: {content[:50]}...")
                    
                    # If response is not None and has content, use it
                    if response and str(response) != "None":
                        # Extract the actual content from the response
                        response_content = response.get('content', str(response)) if isinstance(response, dict) else str(response)
                        if response_content and len(response_content.strip()) > 5:
                            content = response_content
                            logger.info(f"📝 Using direct response from {agent.name}: {content[:50]}...")
                    
                    if content and len(content.strip()) > 5:
                        messages.append({
                            "speaker": agent.name,
                            "content": content,
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                        logger.info(f"✅ Added message from {agent.name}")
                    else:
                        logger.warning(f"⚠️ No response from {agent.name}, adding fallback message")
                        # Add a fallback response when no response is received
                        messages.append({
                            "speaker": agent.name,
                            "content": f"{agent.name}として、「{discussion.theme}」について考えています...",
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                        logger.info(f"✅ Added fallback message for {agent.name}")
                    
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
                    elif "length" in error_str or "token" in error_str:
                        logger.warning(f"OpenAI API token limit exceeded for {agent.name}, using fallback response")
                        messages.append({
                            "speaker": agent.name,
                            "content": f"{agent.name}として、「{discussion.theme}」について考えています...（トークン制限により詳細な応答ができません）",
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
                logger.info("⚙️ Executing tiny_world.run(3)...")
                tiny_world.run(2)
                logger.info("✅ World simulation completed")
                
                logger.info("📥 Extracting messages from world...")
                # Try to get additional messages from world communications
                if hasattr(tiny_world, 'communication_buffer'):
                    communications = getattr(tiny_world, 'communication_buffer', [])
                    if communications:
                        logger.info(f"📥 Found {len(communications)} communications in world buffer")
                        # Get communications that weren't already captured
                        existing_speakers = {msg.get('speaker') for msg in messages}
                        for comm in communications:
                            if hasattr(comm, 'content') and hasattr(comm, 'source'):
                                speaker_name = getattr(comm.source, 'name', 'Unknown')
                                content = comm.content
                                if content and len(str(content).strip()) > 10:
                                    # Check if this speaker already has a message
                                    if speaker_name not in existing_speakers:
                                        messages.append({
                                            "speaker": speaker_name,
                                            "content": str(content),
                                            "timestamp": datetime.datetime.now().isoformat()
                                        })
                                        logger.info(f"💬 Added additional communication from {speaker_name}: {str(content)[:50]}...")
                                        existing_speakers.add(speaker_name)
                
                # If no additional communications found, try to get from individual agents
                if len(messages) <= len(characters) + 1:  # Only system message + one per character
                    logger.info("🔍 No additional world communications found, trying to extract from individual agents...")
                    for agent in agents:
                        try:
                            # Try to get the most recent action or thought from each agent
                            if hasattr(agent, 'episodic_memory') and agent.episodic_memory:
                                recent_memories = agent.episodic_memory.retrieve_all()
                                if recent_memories:
                                    # Find the most recent meaningful memory
                                    for memory in reversed(recent_memories[-3:]):
                                        if hasattr(memory, 'content') and memory.content and len(str(memory.content)) > 10:
                                            # Check if this memory is not already in messages
                                            memory_content = str(memory.content)
                                            if not any(msg.get('content', '').startswith(memory_content[:20]) for msg in messages if msg.get('speaker') == agent.name):
                                                messages.append({
                                                    "speaker": agent.name,
                                                    "content": memory_content,
                                                    "timestamp": datetime.datetime.now().isoformat()
                                                })
                                                logger.info(f"📚 Added memory content from {agent.name}: {memory_content[:50]}...")
                                                break
                        except Exception as agent_extract_error:
                            logger.warning(f"⚠️ Error extracting from agent {agent.name}: {agent_extract_error}")
                            
            except Exception as world_error:
                logger.warning(f"⚠️ World simulation step failed: {world_error}")
            
            return self._create_discussion_response(
                discussion, world, characters, messages, 
                "Real TinyTroupe discussion with AI agents"
            )
            
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
            
            messages = [self._create_system_message(discussion)]
            
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
            
            return self._create_discussion_response(
                discussion, world, characters, messages,
                "AI-powered discussion using OpenAI GPT-4o (with fallback handling)"
            )
            
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
        
        messages = [self._create_system_message(discussion)]
        
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
        
        return self._create_discussion_response(
            discussion, world, characters, messages, reason
        )
    
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
                logger.info(f"📥 Found {len(communications)} communications in world buffer")
                for comm in communications:
                    if hasattr(comm, 'content') and hasattr(comm, 'source'):
                        speaker_name = getattr(comm.source, 'name', 'Unknown')
                        content = comm.content
                        if content and len(str(content).strip()) > 5:
                            messages.append({
                                "speaker": speaker_name,
                                "content": str(content),
                                "timestamp": datetime.datetime.now().isoformat()
                            })
                            logger.info(f"💬 Added communication from {speaker_name}: {str(content)[:50]}...")
            
            # Try to get from world's conversation history
            if hasattr(tiny_world, 'conversation_history'):
                conv_history = getattr(tiny_world, 'conversation_history', [])
                if conv_history:
                    logger.info(f"📥 Found {len(conv_history)} items in conversation history")
                    for conv in conv_history:
                        if hasattr(conv, 'speaker') and hasattr(conv, 'content'):
                            content = conv.content
                            if content and len(str(content).strip()) > 5:
                                messages.append({
                                    "speaker": conv.speaker,
                                    "content": str(content),
                                    "timestamp": datetime.datetime.now().isoformat()
                                })
                                logger.info(f"💬 Added conversation from {conv.speaker}: {str(content)[:50]}...")
            
            # Try to get from world's recent actions
            if hasattr(tiny_world, 'recent_actions'):
                recent_actions = getattr(tiny_world, 'recent_actions', [])
                if recent_actions:
                    logger.info(f"📥 Found {len(recent_actions)} recent actions")
                    for action in recent_actions:
                        if hasattr(action, 'agent') and hasattr(action, 'content'):
                            agent_name = getattr(action.agent, 'name', 'Unknown')
                            content = action.content
                            if content and len(str(content).strip()) > 5:
                                messages.append({
                                    "speaker": agent_name,
                                    "content": str(content),
                                    "timestamp": datetime.datetime.now().isoformat()
                                })
                                logger.info(f"🎭 Added action from {agent_name}: {str(content)[:50]}...")
            
            # If no communications found, try alternative methods to get agent interactions
            if len(messages) <= 1:  # Only system message
                logger.info("🔍 No world communications found, trying individual agent extraction...")
                for agent in agents:
                    # Get agent's current actions or thoughts
                    if hasattr(agent, 'episodic_memory') and agent.episodic_memory:
                        recent_memories = agent.episodic_memory.retrieve_all()[-3:]  # Get last 3 memories
                        for memory in recent_memories:
                            if hasattr(memory, 'content') and memory.content and len(str(memory.content)) > 10:
                                messages.append({
                                    "speaker": agent.name,
                                    "content": str(memory.content),
                                    "timestamp": datetime.datetime.now().isoformat()
                                })
                                logger.info(f"📚 Added memory from {agent.name}: {str(memory.content)[:50]}...")
                    else:
                        # Fallback: generate a sample response
                        messages.append({
                            "speaker": agent.name,
                            "content": f"{agent.name}として議論に参加しています。",
                            "timestamp": datetime.datetime.now().isoformat()
                        })
                        logger.info(f"📝 Added fallback message for {agent.name}")
                        
        except Exception as e:
            logger.error(f"Error extracting messages: {e}")
            # Fallback: create sample messages based on agents
            for agent in agents:
                messages.append({
                    "speaker": agent.name,
                    "content": f"{agent.name}からの議論への参加です。",
                    "timestamp": datetime.datetime.now().isoformat()
                })
                logger.info(f"📝 Added fallback message for {agent.name} due to extraction error")
        
        return messages
    
    async def run_discussion_with_streaming(self, discussion, characters, world, stream_data, discussion_id=None):
        """Run discussion with real-time streaming updates to stream_data (legacy method - calls unified run_discussion)"""
        return await self.run_discussion(discussion, characters, world, stream_data, discussion_id)
    
    async def _create_tinytroupe_streaming_discussion_result(self, discussion, characters, world, stream_data, discussion_id=None):
        """Create a discussion using TinyTroupe with real-time streaming"""
        logger.info("🔧 Starting TinyTroupe streaming discussion creation...")
        
        try:
            import os
            import asyncio
            
            # Set OpenAI API key for TinyTroupe
            os.environ['OPENAI_API_KEY'] = self.api_key
            logger.info("🔑 OpenAI API key set for TinyTroupe")
            
            # Update progress
            stream_data["progress"] = 10
            stream_data["message"] = "TinyTroupe環境を初期化中..."
            if discussion_id:
                from app.api.discussions import discussion_streams
                discussion_streams[discussion_id] = stream_data

            
            # Create TinyWorld and agents with streaming updates
            tiny_world, agents = await self.setup_world_agents(world, characters, stream_data)
            
            if not tiny_world or not agents:
                logger.error("❌ TinyWorld or agents creation failed")
                # Fall back to AI discussion
                return await self._create_ai_streaming_discussion_result(discussion, characters, world, stream_data, discussion_id)
            
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
            if discussion_id:
                from app.api.discussions import discussion_streams
                discussion_streams[discussion_id] = stream_data
            
            # Set up the discussion topic
            discussion_prompt = f"""
            議論テーマ: {discussion.theme}
            詳細: {discussion.description}
            
            このテーマについて、あなたの性格と背景に基づいて意見を述べてください。
            建設的で多様な視点からの議論を行ってください。
            """
            
            # Make all agents accessible to each other for conversation
            try:
                if hasattr(tiny_world, 'make_everyone_accessible'):
                    tiny_world.make_everyone_accessible()
                    logger.info("✅ Made all agents accessible to each other")
            except Exception as e:
                logger.warning(f"⚠️ Could not make agents accessible: {e}")
            
            # Update progress
            stream_data["progress"] = 75
            stream_data["message"] = f"{len(agents)}人のエージェントが議論を開始..."
            if discussion_id:
                from app.api.discussions import discussion_streams
                discussion_streams[discussion_id] = stream_data
            
            # Have each agent respond one by one with real-time updates
            logger.info("💭 Starting agent discussions with streaming...")
            for i, agent in enumerate(agents):
                try:
                    logger.info(f"🤖 Processing agent {i+1}/{len(agents)}: {agent.name}")
                    
                    # Update progress for each agent
                    progress = 75 + (20 * (i + 1) / len(agents))  # 75-95%
                    stream_data["progress"] = min(95, int(progress))
                    
                    # Stream: Agent thinking
                    stream_data["message"] = f"🧠 {agent.name}が議論テーマについて考えています..."
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
                    await asyncio.sleep(0.5)
                    
                    # Make the agent think about the topic
                    logger.info(f"🧠 Making {agent.name} think about the topic...")
                    stream_data["message"] = f"🧠 {agent.name}が議論テーマについて考えています..."
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
                    try:
                        think_result = agent.think(discussion_prompt)
                        logger.info(f"💡 {agent.name} thinking completed")
                        stream_data["message"] = f"💡 {agent.name}の思考が完了しました"
                        if discussion_id:
                            from app.api.discussions import discussion_streams
                            discussion_streams[discussion_id] = stream_data
                    except Exception as think_error:
                        logger.warning(f"⚠️ Thinking failed for {agent.name}: {think_error}")
                        stream_data["message"] = f"⚠️ {agent.name}の思考処理でエラーが発生しました"
                        if discussion_id:
                            from app.api.discussions import discussion_streams
                            discussion_streams[discussion_id] = stream_data
                        # Continue without thinking step
                    
                    # Stream: Agent preparing response
                    stream_data["message"] = f"💭 {agent.name}が意見をまとめています..."
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
                    await asyncio.sleep(0.5)
                    
                    # Get the agent's response
                    logger.info(f"🗣️ Getting response from {agent.name}...")
                    stream_data["message"] = f"🗣️ {agent.name}が発言中... (AI処理中)"
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
                    
                    agent.listen_and_act(f"「{discussion.theme}」について、簡潔に意見を述べてください。")
                    response = agent.pop_actions_and_get_contents_for("TALK", False)
                    logger.info(f"📝 {agent.name} response: {response}...")
                    
                    # Try to extract actual conversation content from agent
                    content = None
                    if response and str(response) != "None":
                        # Extract the actual content from the response
                        content = response.get('content', str(response)) if isinstance(response, dict) else str(response)
                    else:
                        # Try to get content from agent's recent actions or memory
                        logger.info(f"🔍 Trying to extract content from {agent.name}'s memory or actions...")
                        stream_data["message"] = f"🔍 {agent.name}の記憶や行動から内容を抽出中..."
                        if discussion_id:
                            from app.api.discussions import discussion_streams
                            discussion_streams[discussion_id] = stream_data
                        try:
                            # First, try to get from the world's communication buffer (most recent)
                            if hasattr(tiny_world, 'communication_buffer'):
                                communications = getattr(tiny_world, 'communication_buffer', [])
                                if communications:
                                    # Get the most recent communication from this agent
                                    for comm in reversed(communications[-10:]):  # Check last 10 communications
                                        if hasattr(comm, 'source') and hasattr(comm, 'content'):
                                            speaker_name = getattr(comm.source, 'name', '')
                                            if speaker_name == agent.name:
                                                comm_content = str(comm.content)
                                                if comm_content and len(comm_content.strip()) > 10:
                                                    content = comm_content
                                                    logger.info(f"💬 Found recent communication from {agent.name}: {content[:50]}...")
                                                    stream_data["message"] = f"💬 {agent.name}の最近の通信から内容を発見しました"
                                                    if discussion_id:
                                                        from app.api.discussions import discussion_streams
                                                        discussion_streams[discussion_id] = stream_data
                                                    break
                            
                            # If no communication found, check agent's episodic memory
                            if not content and hasattr(agent, 'episodic_memory') and agent.episodic_memory:
                                recent_memories = agent.episodic_memory.retrieve_all()
                                if recent_memories:
                                    # Get the most recent memory that contains actual content
                                    for memory in reversed(recent_memories[-5:]):  # Check last 5 memories
                                        if hasattr(memory, 'content') and memory.content and len(str(memory.content)) > 10:
                                            content = str(memory.content)
                                            logger.info(f"📚 Found content from {agent.name}'s memory: {content[:50]}...")
                                            stream_data["message"] = f"📚 {agent.name}の記憶から内容を発見しました"
                                            if discussion_id:
                                                from app.api.discussions import discussion_streams
                                                discussion_streams[discussion_id] = stream_data
                                            break
                            
                            # If no memory content, try to get from agent's current state
                            if not content and hasattr(agent, 'current_action'):
                                current_action = getattr(agent, 'current_action', None)
                                if current_action and str(current_action) != "None":
                                    content = str(current_action)
                                    logger.info(f"🎭 Found content from {agent.name}'s current action: {content[:50]}...")
                                    stream_data["message"] = f"🎭 {agent.name}の現在の行動から内容を発見しました"
                                    if discussion_id:
                                        from app.api.discussions import discussion_streams
                                        discussion_streams[discussion_id] = stream_data
                            
                            # If still no content, try to get from agent's last communication
                            if not content and hasattr(agent, 'last_communication'):
                                last_comm = getattr(agent, 'last_communication', None)
                                if last_comm and str(last_comm) != "None":
                                    content = str(last_comm)
                                    logger.info(f"💬 Found content from {agent.name}'s last communication: {content[:50]}...")
                                    stream_data["message"] = f"💬 {agent.name}の最後の通信から内容を発見しました"
                                    if discussion_id:
                                        from app.api.discussions import discussion_streams
                                        discussion_streams[discussion_id] = stream_data
                                    
                        except Exception as extract_error:
                            logger.warning(f"⚠️ Error extracting content from {agent.name}: {extract_error}")
                            stream_data["message"] = f"⚠️ {agent.name}からの内容抽出でエラーが発生しました"
                            if discussion_id:
                                from app.api.discussions import discussion_streams
                                discussion_streams[discussion_id] = stream_data
                    
                    if content and len(content.strip()) > 5:
                        # Stream: Agent completed response
                        stream_data["message"] = f"✅ {agent.name}が発言を完了しました"
                        if discussion_id:
                            from app.api.discussions import discussion_streams
                            discussion_streams[discussion_id] = stream_data
                        await asyncio.sleep(0.2)
                        
                        # Add message immediately to stream
                        new_message = {
                            "speaker": agent.name,
                            "content": content,
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                        messages.append(new_message)
                        stream_data["messages"] = messages.copy()  # Update stream immediately
                        if discussion_id:
                            from app.api.discussions import discussion_streams
                            discussion_streams[discussion_id] = stream_data
                        
                        # Force a small delay to ensure the update is sent
                        await asyncio.sleep(0.1)
                        
                        # Show the actual content in progress message
                        stream_data["message"] = f"💬 {agent.name}: {content[:50]}..." if len(content) > 50 else f"💬 {agent.name}: {content}"
                        if discussion_id:
                            from app.api.discussions import discussion_streams
                            discussion_streams[discussion_id] = stream_data
                        await asyncio.sleep(0.5)  # 短縮
                        
                        logger.info(f"✅ Added streaming message from {agent.name}")
                        logger.debug(f"Stream updated: {len(stream_data['messages'])} messages total")  # デバッグログを追加
                    else:
                        logger.warning(f"⚠️ No response from {agent.name}, adding fallback message")
                        stream_data["message"] = f"⚠️ {agent.name}からの応答を取得できませんでした"
                        if discussion_id:
                            from app.api.discussions import discussion_streams
                            discussion_streams[discussion_id] = stream_data
                        
                        # Stream: Agent had no response
                        stream_data["message"] = f"⚠️ {agent.name}からの応答を取得できませんでした"
                        if discussion_id:
                            from app.api.discussions import discussion_streams
                            discussion_streams[discussion_id] = stream_data
                        await asyncio.sleep(0.3)
                        
                        # Add a fallback response
                        fallback_message = {
                            "speaker": agent.name,
                            "content": f"{agent.name}として、「{discussion.theme}」について考えています...",
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                        messages.append(fallback_message)
                        stream_data["messages"] = messages.copy()
                        if discussion_id:
                            from app.api.discussions import discussion_streams
                            discussion_streams[discussion_id] = stream_data
                        
                        # Force a small delay to ensure the update is sent
                        await asyncio.sleep(0.1)
                    
                    # Small delay between agents
                    await asyncio.sleep(0.5)  # 短縮
                    
                except Exception as agent_error:
                    logger.error(f"❌ Error getting response from agent {agent.name}: {agent_error}")
                    stream_data["message"] = f"❌ {agent.name}からの応答取得でエラーが発生しました"
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
                    # Check if it's a token limit error
                    error_str = str(agent_error).lower()
                    if "length" in error_str or "token" in error_str:
                        logger.warning(f"OpenAI API token limit exceeded for {agent.name}, using fallback response")
                        stream_data["message"] = f"⚠️ {agent.name}: トークン制限により詳細な応答ができません"
                        if discussion_id:
                            from app.api.discussions import discussion_streams
                            discussion_streams[discussion_id] = stream_data
                        fallback_message = {
                            "speaker": agent.name,
                            "content": f"{agent.name}として、「{discussion.theme}」について考えています...（トークン制限により詳細な応答ができません）",
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    else:
                        # Add a fallback response for this agent
                        stream_data["message"] = f"⚠️ {agent.name}: エラーが発生しました"
                        if discussion_id:
                            from app.api.discussions import discussion_streams
                            discussion_streams[discussion_id] = stream_data
                        fallback_message = {
                            "speaker": agent.name,
                            "content": f"{agent.name}として、「{discussion.theme}」について考えています...（エラーが発生しました）",
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    messages.append(fallback_message)
                    stream_data["messages"] = messages.copy()
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
            
            # 完了状態を設定
            stream_data["completed"] = True
            stream_data["progress"] = 100
            stream_data["message"] = "TinyTroupe議論が完了しました"
            if discussion_id:
                from app.api.discussions import discussion_streams
                discussion_streams[discussion_id] = stream_data
            logger.info("✅ TinyTroupe streaming discussion completed")
            
            return self._create_discussion_response(
                discussion, world, characters, messages,
                "Real TinyTroupe streaming discussion with AI agents"
            )
            
        except Exception as e:
            logger.error(f"Error in TinyTroupe streaming discussion generation: {e}")
            error_str = str(e).lower()
            if "insufficient_quota" in error_str or "quota" in error_str:
                logger.warning("OpenAI API quota exceeded in streaming TinyTroupe, falling back to mock discussion")
                return await self._create_mock_streaming_discussion_result(discussion, characters, world, stream_data, discussion_id)
            elif "rate_limit" in error_str or "429" in error_str:
                logger.warning("OpenAI API rate limit exceeded in streaming TinyTroupe, falling back to mock discussion")
                return await self._create_mock_streaming_discussion_result(discussion, characters, world, stream_data, discussion_id)
            else:
                # Fall back to AI discussion
                return await self._create_ai_streaming_discussion_result(discussion, characters, world, stream_data, discussion_id)
    
    async def _create_ai_streaming_discussion_result(self, discussion, characters, world, stream_data, discussion_id=None):
        """Create an AI-powered discussion with streaming updates"""
        try:
            client = openai.OpenAI(api_key=self.api_key)
            
            messages = [self._create_system_message(discussion)]
            stream_data["messages"] = messages
            if discussion_id:
                from app.api.discussions import discussion_streams
                discussion_streams[discussion_id] = stream_data
            
            # Generate discussion for each character with streaming
            for i, character in enumerate(characters):
                # Update progress
                progress = 80 + (15 * (i + 1) / len(characters))  # 80-95%
                stream_data["progress"] = min(95, int(progress))
                stream_data["message"] = f"{character.name}が発言中..."
                if discussion_id:
                    from app.api.discussions import discussion_streams
                    discussion_streams[discussion_id] = stream_data
                
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
                    stream_data["message"] = f"🤖 {character.name}のAI応答を生成中..."
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
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
                    stream_data["message"] = f"✅ {character.name}のAI応答が完了しました"
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
                    
                    new_message = {
                        "speaker": character.name,
                        "content": ai_response,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    messages.append(new_message)
                    stream_data["messages"] = messages.copy()  # Update stream immediately
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
                    
                    # Force a small delay to ensure the update is sent
                    await asyncio.sleep(0.1)
                    
                    logger.debug(f"AI Stream updated: {len(stream_data['messages'])} messages total")  # デバッグログを追加
                    
                except Exception as api_error:
                    logger.error(f"OpenAI API error for {character.name}: {api_error}")
                    stream_data["message"] = f"❌ {character.name}のAI応答生成でエラーが発生しました"
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
                    # Add a fallback response for this character
                    fallback_message = {
                        "speaker": character.name,
                        "content": f"{character.name}として、「{discussion.theme}」について考えています...",
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    messages.append(fallback_message)
                    stream_data["messages"] = messages.copy()
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
                    
                    # Force a small delay to ensure the update is sent
                    await asyncio.sleep(0.1)
                
                # Small delay between characters
                await asyncio.sleep(0.3)  # 短縮
            
            # 完了状態を設定
            stream_data["completed"] = True
            stream_data["progress"] = 100
            stream_data["message"] = "AI議論が完了しました"
            if discussion_id:
                from app.api.discussions import discussion_streams
                discussion_streams[discussion_id] = stream_data
            logger.info("✅ AI streaming discussion completed")
            
            return self._create_discussion_response(
                discussion, world, characters, messages,
                "AI-powered streaming discussion using OpenAI GPT-4o-mini"
            )
            
        except Exception as e:
            logger.error(f"Error in AI streaming discussion generation: {e}")
            return await self._create_mock_streaming_discussion_result(discussion, characters, world, stream_data, discussion_id)
    
    async def _create_mock_streaming_discussion_result(self, discussion, characters, world, stream_data, discussion_id=None):
        """Create a mock discussion with streaming updates"""
        
        messages = [self._create_system_message(discussion)]
        stream_data["messages"] = messages
        if discussion_id:
            from app.api.discussions import discussion_streams
            discussion_streams[discussion_id] = stream_data
        
        # Generate streaming mock discussion
        for i, character in enumerate(characters):
            # Update progress
            progress = 80 + (15 * (i + 1) / len(characters))  # 80-95%
            stream_data["progress"] = min(95, int(progress))
            stream_data["message"] = f"{character.name}が発言中..."
            if discussion_id:
                from app.api.discussions import discussion_streams
                discussion_streams[discussion_id] = stream_data
            
            # Generate mock responses with delay
            discussion_points = [
                f"私は{character.personality}な性格なので、「{discussion.theme}」について{self._generate_mock_opinion(character, discussion.theme)}と思います。",
                f"{character.background}の経験から言うと、この問題は{self._generate_mock_perspective(character, discussion.theme)}",
            ]
            
            for j, point in enumerate(discussion_points):
                if i < 2 or j == 0:  # Limit messages for demo
                    stream_data["message"] = f"🎭 {character.name}のモック応答を生成中... ({j+1}/{len(discussion_points)})"
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
                    
                    new_message = {
                        "speaker": character.name,
                        "content": point,
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    messages.append(new_message)
                    stream_data["messages"] = messages.copy()  # Update stream immediately
                    if discussion_id:
                        from app.api.discussions import discussion_streams
                        discussion_streams[discussion_id] = stream_data
                    
                    # Force a small delay to ensure the update is sent
                    await asyncio.sleep(0.1)
                    
                    logger.debug(f"Mock Stream updated: {len(stream_data['messages'])} messages total")  # デバッグログを追加
                    
                    # Small delay to simulate real conversation
                    await asyncio.sleep(0.5)  # 短縮
        
        # 完了状態を設定
        stream_data["completed"] = True
        stream_data["progress"] = 100
        stream_data["message"] = "モック議論が完了しました"
        if discussion_id:
            from app.api.discussions import discussion_streams
            discussion_streams[discussion_id] = stream_data
        logger.info("✅ Mock streaming discussion completed")
        
        return self._create_discussion_response(
            discussion, world, characters, messages,
            "Mock streaming discussion - TinyTroupe not available or API issues"
        )
    
    def validate_character_config(self, config: Dict[str, Any]) -> bool:
        """Validate character configuration."""
        required_fields = ["name"]
        return all(field in config for field in required_fields)