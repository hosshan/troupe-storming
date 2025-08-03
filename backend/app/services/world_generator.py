import os
import logging
from typing import Dict, Any, List, Callable, Optional
import json
import random
import asyncio

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class WorldGeneratorService:
    def __init__(self):
        self.openai_available = OPENAI_AVAILABLE
        self.api_key = os.getenv('OPENAI_API_KEY')
        
        if self.api_key and self.openai_available:
            logger.info("OpenAI API key found for world generation")
        else:
            logger.warning("OpenAI API not available for world generation")
    
    async def generate_world_from_keywords(
        self, 
        keywords: str, 
        generate_characters: bool = True, 
        character_count: int = 3,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, Any]:
        """Generate a world and optionally characters from keywords using AI or fallback templates."""
        try:
            if progress_callback:
                progress_callback("🚀 生成を開始しています...", 10)
                await asyncio.sleep(0.5)  # UI更新のための小さな遅延
            
            if self.openai_available and self.api_key:
                if progress_callback:
                    progress_callback("🌍 AIで世界を生成中...", 30)
                world_data = await self._generate_ai_world(keywords, progress_callback)
                
                if generate_characters:
                    if progress_callback:
                        progress_callback("👥 AIでキャラクターを生成中...", 70)
                    characters = await self._generate_ai_characters(keywords, world_data, character_count, progress_callback)
                    world_data["characters"] = characters
                
                if progress_callback:
                    progress_callback("✅ 生成完了！", 100)
                return world_data
            else:
                if progress_callback:
                    progress_callback("📝 テンプレートから世界を生成中...", 40)
                world_data = self._generate_template_world(keywords)
                
                if generate_characters:
                    if progress_callback:
                        progress_callback("👥 テンプレートからキャラクターを生成中...", 80)
                    characters = self._generate_template_characters(keywords, character_count)
                    world_data["characters"] = characters
                
                if progress_callback:
                    progress_callback("✅ 生成完了！", 100)
                return world_data
                
        except Exception as e:
            logger.error(f"Error generating world: {e}")
            if progress_callback:
                progress_callback("⚠️ エラーが発生しました。フォールバックで生成中...", 60)
            
            world_data = self._generate_template_world(keywords)
            if generate_characters:
                characters = self._generate_template_characters(keywords, character_count)
                world_data["characters"] = characters
            
            if progress_callback:
                progress_callback("✅ フォールバック生成完了！", 100)
            return world_data
    
    async def _generate_ai_world(self, keywords: str, progress_callback: Optional[Callable[[str, int], None]] = None) -> Dict[str, Any]:
        """Generate world using OpenAI API."""
        try:
            if progress_callback:
                progress_callback("🤖 OpenAI APIに接続中...", 35)
            client = openai.OpenAI(api_key=self.api_key)
            
            prompt = f"""
            以下のキーワードから創作世界を生成してください: {keywords}

            以下のJSON形式で回答してください:
            {{
                "name": "世界の名前",
                "description": "世界の簡潔な説明（1-2文）",
                "background": "世界の詳細な設定・背景（3-5文で、歴史、文化、特徴を含む）"
            }}

            創造性豊かで興味深い世界を作成してください。
            """
            
            if progress_callback:
                progress_callback("💭 AIが世界を考案中...", 45)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは創造性豊かな世界設定の専門家です。与えられたキーワードから魅力的なファンタジー世界を生成します。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            if progress_callback:
                progress_callback("📝 AI応答を処理中...", 55)
            
            # JSON形式のレスポンスをパース
            try:
                world_data = json.loads(ai_response)
                return {
                    "name": world_data.get("name", f"{keywords}の世界"),
                    "description": world_data.get("description", f"{keywords}をテーマにした世界"),
                    "background": world_data.get("background", f"{keywords}を中心とした独特な世界設定"),
                    "generated_by": "AI (OpenAI GPT-3.5)"
                }
            except json.JSONDecodeError:
                # JSONパースに失敗した場合、テキストから抽出を試行
                lines = ai_response.split('\n')
                name = keywords + "の世界"
                description = f"{keywords}をテーマにした世界"
                background = ai_response.replace('"', '').strip()
                
                return {
                    "name": name,
                    "description": description,
                    "background": background,
                    "generated_by": "AI (OpenAI GPT-3.5)"
                }
                
        except Exception as e:
            logger.error(f"Error in AI world generation: {e}")
            return self._generate_template_world(keywords)
    
    def _generate_template_world(self, keywords: str) -> Dict[str, Any]:
        """Generate world using predefined templates."""
        templates = [
            {
                "name_template": "{keywords}の魔法世界",
                "description_template": "{keywords}が支配する不思議な魔法の世界です。",
                "background_template": "この世界では{keywords}が重要な役割を果たしています。古代から続く魔法の力により、{keywords}を中心とした独特な文明が発達しました。住民たちは{keywords}の力を借りて日々の生活を営んでいます。"
            },
            {
                "name_template": "{keywords}王国",
                "description_template": "{keywords}をテーマにした壮大な王国の物語です。",
                "background_template": "{keywords}王国は数百年の歴史を持つ伝統的な国家です。国民は{keywords}を重んじ、それを基盤とした文化と技術を発展させてきました。王国の平和は{keywords}の加護により保たれています。"
            },
            {
                "name_template": "{keywords}の秘境",
                "description_template": "{keywords}に満ちた神秘的な秘境です。",
                "background_template": "人里離れた秘境には{keywords}にまつわる古い伝説が残されています。この地を訪れる者は{keywords}の真の力と向き合うことになります。自然と{keywords}が調和した美しくも危険な世界です。"
            }
        ]
        
        # キーワードのハッシュ値でテンプレートを選択
        template_index = hash(keywords) % len(templates)
        template = templates[template_index]
        
        return {
            "name": template["name_template"].format(keywords=keywords),
            "description": template["description_template"].format(keywords=keywords),
            "background": template["background_template"].format(keywords=keywords),
            "generated_by": "Template"
        }
    
    async def _generate_ai_characters(self, keywords: str, world_data: Dict[str, Any], character_count: int = 3, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[Dict[str, Any]]:
        """Generate characters using OpenAI API."""
        try:
            if progress_callback:
                progress_callback("👥 キャラクター設計中...", 75)
            client = openai.OpenAI(api_key=self.api_key)
            
            prompt = f"""
            以下の世界設定に合うキャラクターを{character_count}人生成してください:

            世界名: {world_data['name']}
            世界の説明: {world_data['description']}
            世界の背景: {world_data['background']}
            キーワード: {keywords}

            以下のJSON配列形式で回答してください:
            [
                {{
                    "name": "キャラクター名",
                    "description": "キャラクターの簡潔な説明（1-2文）",
                    "personality": "性格の特徴（簡潔に）",
                    "background": "キャラクターの背景・経歴（2-3文）"
                }}
            ]

            各キャラクターは個性的で、世界設定に合致し、議論で異なる視点を提供できるように作成してください。
            """
            
            if progress_callback:
                progress_callback("🎭 AIがキャラクターを作成中...", 85)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "あなたは創造性豊かなキャラクター設定の専門家です。与えられた世界設定に合う魅力的なキャラクターを生成します。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content.strip()
            
            if progress_callback:
                progress_callback("✨ キャラクター情報を整理中...", 90)
            
            try:
                characters_data = json.loads(ai_response)
                return characters_data
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI character response as JSON, using template fallback")
                return self._generate_template_characters(keywords, character_count)
                
        except Exception as e:
            logger.error(f"Error in AI character generation: {e}")
            return self._generate_template_characters(keywords, character_count)
    
    def _generate_template_characters(self, keywords: str, character_count: int = 3) -> List[Dict[str, Any]]:
        """Generate characters using predefined templates."""
        character_templates = [
            {
                "name": "{keywords}の賢者",
                "description": "{keywords}の深い知識を持つ知恵深い人物です。",
                "personality": "知的で慎重、思慮深い",
                "background": "{keywords}について長年研究してきた学者。豊富な知識と経験を持ち、物事を多角的に分析する能力に長けています。"
            },
            {
                "name": "{keywords}の戦士",
                "description": "{keywords}を守るために戦う勇敢な戦士です。",
                "personality": "勇敢で正義感が強い、行動力がある",
                "background": "{keywords}を脅かす敵と戦い続けてきた経験豊富な戦士。実践的な視点から物事を判断し、迅速な行動を好みます。"
            },
            {
                "name": "{keywords}の商人",
                "description": "{keywords}に関わる商売をしている商人です。",
                "personality": "実利的で交渉上手、社交的",
                "background": "{keywords}を扱う商売で成功を収めた商人。経済的な視点と人脈を活かし、現実的な解決策を提案することが得意です。"
            },
            {
                "name": "{keywords}の芸術家",
                "description": "{keywords}をテーマにした作品を創る芸術家です。",
                "personality": "創造的で感性豊か、理想主義的",
                "background": "{keywords}に魅了され、それを表現する芸術作品を創り続けている。美的感覚と創造性から独特な視点を提供します。"
            },
            {
                "name": "{keywords}の探検家",
                "description": "{keywords}の謎を解明しようと冒険する探検家です。",
                "personality": "好奇心旺盛で冒険好き、楽観的",
                "background": "{keywords}にまつわる未知の領域を探検してきた冒険者。新しい発見への情熱と豊富な経験を持っています。"
            }
        ]
        
        # キャラクター数に応じてテンプレートを選択
        selected_templates = random.sample(character_templates, min(character_count, len(character_templates)))
        
        characters = []
        for template in selected_templates:
            character = {
                "name": template["name"].format(keywords=keywords),
                "description": template["description"].format(keywords=keywords),
                "personality": template["personality"],
                "background": template["background"].format(keywords=keywords)
            }
            characters.append(character)
        
        return characters