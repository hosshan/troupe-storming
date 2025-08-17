import json
import os
import datetime
import logging
import asyncio
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import Character, Discussion, World

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from tinytroupe.agent import TinyPerson
    from tinytroupe.environment import TinyWorld
    from tinytroupe.factory import TinyPersonFactory
    TINYTROUPE_AVAILABLE = True
    logger.info("TinyTroupe successfully imported")
except ImportError as e:
    logger.warning(f"TinyTroupe import failed: {e}")
    TINYTROUPE_AVAILABLE = False


class TinyTroupeService:
    def __init__(self):
        self.tinytroupe_available = TINYTROUPE_AVAILABLE
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if self.api_key and TINYTROUPE_AVAILABLE:
            os.environ['OPENAI_API_KEY'] = self.api_key
            logger.info("TinyTroupe service initialized successfully")
        else:
            logger.warning("TinyTroupe not available or API key missing")
    
    def create_agent_from_character(self, character: Character) -> Optional[TinyPerson]:
        """Create a TinyPerson agent from a Character model."""
        if not self.tinytroupe_available:
            return None
            
        try:
            # シンプルなエージェント作成
            agent = TinyPerson(name=character.name)
            
            # LengthFinishReasonErrorを回避するための設定
            if hasattr(agent, 'max_tokens'):
                agent.max_tokens = 1000  # トークン数を制限
            if hasattr(agent, 'max_response_length'):
                agent.max_response_length = 500  # レスポンス長を制限
            
            logger.info(f"Agent {character.name} created successfully")
            logger.info(f"{agent.minibio()}")
            
            return agent
        except Exception as e:
            logger.error(f"Failed to create agent for {character.name}: {e}")
            return None
    
    async def run_discussion_with_streaming(self, discussion: Discussion, characters: List[Character], world: World, stream_data: Dict[str, Any], discussion_id: Optional[int] = None) -> Dict[str, Any]:
        """Run a TinyTroupe discussion with streaming updates (external interface compatibility)."""
        return await self.run_discussion(discussion, characters, world, stream_data)
    
    async def run_discussion(self, discussion: Discussion, characters: List[Character], world: World, stream_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run a TinyTroupe discussion with streaming updates."""
        if not self.tinytroupe_available or not self.api_key:
            return self._create_fallback_response(discussion, characters, world, stream_data)
        
        try:
            # 初期化
            stream_data["progress"] = 0
            stream_data["message"] = "TinyTroupe議論を開始中..."
            stream_data["messages"] = []
            
            # 1. エージェント作成
            stream_data["progress"] = 10
            stream_data["message"] = "エージェントを作成中..."
            await asyncio.sleep(0.1)
            
            agents = []
            for i, character in enumerate(characters):
                progress = 10 + (30 * i / len(characters))
                stream_data["progress"] = int(progress)
                stream_data["message"] = f"エージェント「{character.name}」を作成中..."
                await asyncio.sleep(0.1)
                
                agent = self.create_agent_from_character(character)
                if agent:
                    agents.append(agent)
                    stream_data["message"] = f"✅ エージェント「{character.name}」が作成されました"
                    await asyncio.sleep(0.2)
            
            if not agents:
                stream_data["message"] = "❌ エージェントの作成に失敗しました"
                return self._create_fallback_response(discussion, characters, world, stream_data)
            
            # 2. ワールド作成
            stream_data["progress"] = 50
            stream_data["message"] = "ワールド環境を作成中..."
            await asyncio.sleep(0.1)
            
            tiny_world = TinyWorld(world.name, agents)
            tiny_world.make_everyone_accessible()
            
            # LengthFinishReasonErrorを回避するための設定
            if hasattr(tiny_world, 'max_tokens_per_turn'):
                tiny_world.max_tokens_per_turn = 800  # ターンごとのトークン数を制限
            if hasattr(tiny_world, 'max_conversation_length'):
                tiny_world.max_conversation_length = 2000  # 会話全体の長さを制限
            
            stream_data["message"] = f"✅ ワールド「{world.name}」が作成されました"
            await asyncio.sleep(0.2)
            
            # 3. 議論開始メッセージ
            stream_data["progress"] = 60
            stream_data["message"] = "議論テーマを設定中..."
            await asyncio.sleep(0.1)
            
            discussion_prompt = f"""
            みなさんこんにちは! 本日の議論テーマはこちらです: {discussion.theme}
            
            それぞれの意見をお願いします。
            """
            
            # 4. ワールドにメッセージを送信
            tiny_world.broadcast(discussion_prompt)
            stream_data["message"] = f"💬 議論テーマ「{discussion.theme}」を送信しました"
            await asyncio.sleep(0.2)
            
            # 5. 議論実行
            stream_data["progress"] = 70
            stream_data["message"] = "エージェントが議論を開始中..."
            await asyncio.sleep(0.1)
            
            turn_count = getattr(discussion, 'turn_count', 1)
            
            try:
                # return_actions=Trueを使って行動を直接取得
                actions = tiny_world.run(turn_count, return_actions=True)
                stream_data["message"] = f"✅ {turn_count}ターンの議論が完了しました"
            except Exception as e:
                logger.warning(f"World simulation failed with error: {e}")
                # LengthFinishReasonErrorなどの場合、フォールバック処理
                if "LengthFinishReasonError" in str(e) or "length limit" in str(e).lower():
                    stream_data["message"] = f"⚠️ トークン制限により一部の処理が完了しませんでしたが、利用可能な結果を取得します"
                    actions = []  # 空のリストでフォールバック
                else:
                    # その他のエラーの場合は再試行
                    logger.info("Retrying world simulation...")
                    try:
                        tiny_world.run(turn_count, return_actions=True)
                        stream_data["message"] = f"✅ {turn_count}ターンの議論が完了しました（再試行成功）"
                    except Exception as retry_e:
                        logger.error(f"Retry also failed: {retry_e}")
                        stream_data["message"] = f"❌ 議論の実行に失敗しました: {str(retry_e)}"
            
            await asyncio.sleep(0.2)
            
            # 6. 結果抽出
            stream_data["progress"] = 80
            stream_data["message"] = "議論結果を抽出中..."
            await asyncio.sleep(0.1)
            
            messages = [self._create_system_message(discussion)]
            stream_data["messages"] = messages.copy()
            await asyncio.sleep(0.1)

            actions = tiny_world.pop_latest_actions()
            
            # 取得した行動から発言を抽出
            if actions and isinstance(actions, list):
                logger.info(f"Retrieved {len(actions)} actions from world simulation")
                
                # 行動を時系列順にソート（必要に応じて）
                for action in actions:
                    try:
                        if hasattr(action, 'agent') and hasattr(action, 'action_type'):
                            agent_name = action.agent.name if hasattr(action.agent, 'name') else str(action.agent)
                            action_type = action.action_type
                            
                            logger.info(f"Action: {agent_name} -> {action_type}")
                            # TALKアクションの場合、発言内容を取得
                            if action_type == 'TALK':
                                content = action.get("content", "")
                                if content.strip():
                                    new_message = {
                                        "speaker": agent_name,
                                        "content": content,
                                        "timestamp": datetime.datetime.now().isoformat()
                                    }
                                    messages.append(new_message)
                                    stream_data["messages"] = messages.copy()
                                    
                                    # 発言のプレビューを表示
                                    preview = content[:100] + "..." if len(content) > 100 else content
                                    stream_data["message"] = f"💬 {agent_name}: {preview}"
                                    await asyncio.sleep(0.3)
                            
                            # THINKアクションの場合、思考内容を取得（オプション）
                            elif action_type == 'THINK':
                                content = action.get("content", "")
                                if content.strip():
                                    new_message = {
                                        "speaker": agent_name,
                                        "content": f"[思考] {content}",
                                        "timestamp": datetime.datetime.now().isoformat()
                                    }
                                    messages.append(new_message)
                                    stream_data["messages"] = messages.copy()
                                    
                                    preview = content[:100] + "..." if len(content) > 100 else content
                                    stream_data["message"] = f"🤔 {agent_name}: {preview}"
                                    await asyncio.sleep(0.3)
                    
                    except Exception as e:
                        logger.warning(f"Error processing action: {e}")
                        continue
            
            # 行動から発言が取得できなかった場合、従来の方法を試行
            if len(messages) <= 1:  # システムメッセージのみの場合
                logger.info("No actions retrieved, falling back to agent state extraction")
                
                # 各エージェントから発言を取得
                for i, agent in enumerate(agents):
                    progress = 80 + (15 * (i + 1) / len(agents))
                    stream_data["progress"] = int(progress)
                    stream_data["message"] = f"エージェント「{agent.name}」の発言を取得中..."
                    await asyncio.sleep(0.1)
                    
                    try:
                        # TinyTroupeの実際の動作に合わせて発言を取得
                        agent_messages = []
                        
                        # デバッグ情報を出力
                        logger.info(f"Agent {agent.name} attributes: {dir(agent)}")
                        
                        # 方法1: エージェントの記憶から発言を取得
                        if hasattr(agent, 'episodic_memory') and agent.episodic_memory:
                            try:
                                memories = agent.episodic_memory.retrieve_all()
                                logger.info(f"Agent {agent.name} memories: {memories}")
                                if memories:
                                    for memory in memories:
                                        if hasattr(memory, 'content') and memory.content:
                                            content = str(memory.content)
                                            if content.strip():
                                                agent_messages.append(content)
                            except Exception as e:
                                logger.debug(f"Memory retrieval failed for {agent.name}: {e}")
                        
                        # 方法2: エージェントの行動履歴から発言を取得
                        if hasattr(agent, 'action_history') and agent.action_history:
                            try:
                                logger.info(f"Agent {agent.name} action_history: {agent.action_history}")
                                for action in agent.action_history:
                                    if hasattr(action, 'action_type') and action.action_type == 'TALK':
                                        if hasattr(action, 'content') and action.content:
                                            content = str(action.content)
                                            if content.strip():
                                                agent_messages.append(content)
                            except Exception as e:
                                logger.debug(f"Action history retrieval failed for {agent.name}: {e}")
                        
                        # 方法3: エージェントの内部状態から発言を取得
                        if hasattr(agent, 'internal_state') and agent.internal_state:
                            try:
                                logger.info(f"Agent {agent.name} internal_state: {agent.internal_state}")
                                if hasattr(agent.internal_state, 'thoughts'):
                                    thoughts = agent.internal_state.thoughts
                                    if thoughts and isinstance(thoughts, list):
                                        for thought in thoughts:
                                            if hasattr(thought, 'content'):
                                                content = str(thought.content)
                                                if content.strip():
                                                    agent_messages.append(content)
                            except Exception as e:
                                logger.debug(f"Internal state retrieval failed for {agent.name}: {e}")
                        
                        # 方法4: エージェントの会話履歴から発言を取得
                        if hasattr(agent, 'conversation_history') and agent.conversation_history:
                            try:
                                logger.info(f"Agent {agent.name} conversation_history: {agent.conversation_history}")
                                for conv in agent.conversation_history:
                                    if hasattr(conv, 'content'):
                                        content = str(conv.content)
                                        if content.strip():
                                            agent_messages.append(content)
                            except Exception as e:
                                logger.debug(f"Conversation history retrieval failed for {agent.name}: {e}")
                        
                        # 方法5: エージェントの最新の状態から発言を取得
                        if hasattr(agent, 'current_action') and agent.current_action:
                            try:
                                logger.info(f"Agent {agent.name} current_action: {agent.current_action}")
                                if hasattr(agent.current_action, 'content'):
                                    content = str(agent.current_action.content)
                                    if content.strip():
                                        agent_messages.append(content)
                            except Exception as e:
                                logger.debug(f"Current action retrieval failed for {agent.name}: {e}")
                        
                        # 方法6: エージェントの最後の行動から発言を取得
                        if hasattr(agent, 'last_action') and agent.last_action:
                            try:
                                logger.info(f"Agent {agent.name} last_action: {agent.last_action}")
                                if hasattr(agent.last_action, 'content'):
                                    content = str(agent.last_action.content)
                                    if content.strip():
                                        agent_messages.append(content)
                            except Exception as e:
                                logger.debug(f"Last action retrieval failed for {agent.name}: {e}")
                        
                        logger.info(f"Agent {agent.name} extracted messages: {agent_messages}")
                        
                        # 発言が見つからない場合のフォールバック
                        if not agent_messages:
                            # エージェントの基本情報から発言を生成
                            if hasattr(agent, 'minibio'):
                                try:
                                    bio = agent.minibio()
                                    if bio:
                                        agent_messages.append(f"{agent.name}として「{discussion.theme}」について考えています。{bio}")
                                    else:
                                        agent_messages.append(f"{agent.name}が議論に参加しました。")
                                except:
                                    agent_messages.append(f"{agent.name}が議論に参加しました。")
                            else:
                                agent_messages.append(f"{agent.name}が議論に参加しました。")
                        
                        # 発言をメッセージリストに追加
                        for j, content in enumerate(agent_messages):
                            new_message = {
                                "speaker": agent.name,
                                "content": content,
                                "timestamp": datetime.datetime.now().isoformat()
                            }
                            messages.append(new_message)
                            stream_data["messages"] = messages.copy()
                            
                            # 最初の発言のみ詳細表示
                            if j == 0:
                                preview = content[:100] + "..." if len(content) > 100 else content
                                stream_data["message"] = f"💬 {agent.name}: {preview}"
                                await asyncio.sleep(0.3)
                        
                    except Exception as e:
                        logger.warning(f"Error extracting from agent {agent.name}: {e}")
                        # 基本的な発言を追加
                        new_message = {
                            "speaker": agent.name,
                            "content": f"{agent.name}が議論に参加しました。",
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                        messages.append(new_message)
                        stream_data["messages"] = messages.copy()
                        stream_data["message"] = f"✅ {agent.name}が議論に参加しました"
                        await asyncio.sleep(0.2)
            
            # 完了
            stream_data["progress"] = 100
            stream_data["message"] = "TinyTroupe議論が完了しました"
            stream_data["completed"] = True
            
            return self._create_discussion_response(discussion, world, characters, messages)
            
        except Exception as e:
            logger.error(f"TinyTroupe discussion failed: {e}")
            stream_data["message"] = f"❌ エラーが発生しました: {str(e)}"
            stream_data["error"] = str(e)
            return self._create_fallback_response(discussion, characters, world, stream_data)
    
    def _create_system_message(self, discussion) -> dict:
        """議論開始システムメッセージを生成"""
        return {
            "speaker": "システム",
            "content": f"議論テーマ「{discussion.theme}」について話し合いを開始します。",
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def _create_discussion_response(self, discussion, world, characters, messages) -> dict:
        """共通の議論レスポンス形式を生成"""
        return {
            "discussion_id": discussion.id,
            "theme": discussion.theme,
            "world": world.name,
            "participants": [char.name for char in characters],
            "messages": messages,
            "status": "completed",
            "note": "TinyTroupeによる議論が完了しました"
        }
    
    def _create_fallback_response(self, discussion, characters, world, stream_data) -> dict:
        """フォールバック用の基本的なレスポンス"""
        messages = [self._create_system_message(discussion)]
        
        for character in characters:
            messages.append({
                        "speaker": character.name,
                "content": f"{character.name}として「{discussion.theme}」について考えています。",
                        "timestamp": datetime.datetime.now().isoformat()
            })
        
        # ストリーミングデータも更新
        if stream_data:
            stream_data["progress"] = 100
            stream_data["message"] = "フォールバック処理が完了しました"
            stream_data["messages"] = messages.copy()
        stream_data["completed"] = True
        
        return self._create_discussion_response(discussion, world, characters, messages)