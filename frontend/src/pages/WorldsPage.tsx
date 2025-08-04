import React, { useState, useEffect } from "react";
import {
  Plus,
  Edit,
  Trash2,
  Users,
  MessageCircle,
  Sparkles,
  Loader2,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "../components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../components/ui/dialog";
import { Input } from "../components/ui/input";
import { Textarea } from "../components/ui/textarea";
import { Label } from "../components/ui/label";
import { useNavigate } from "react-router-dom";
import { World, CreateWorldRequest } from "../types";
import { worldsApi } from "../services/api";

const WorldsPage: React.FC = () => {
  const navigate = useNavigate();
  const [worlds, setWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false);
  const [editingWorld, setEditingWorld] = useState<World | null>(null);
  const [formData, setFormData] = useState<CreateWorldRequest>({
    name: "",
    description: "",
    background: "",
  });
  const [generateData, setGenerateData] = useState({
    keywords: "",
    generate_characters: true,
    character_count: 3,
  });
  const [generating, setGenerating] = useState(false);
  const [progressMessage, setProgressMessage] = useState("");

  useEffect(() => {
    loadWorlds();
  }, []);

  const loadWorlds = async () => {
    try {
      const data = await worldsApi.getAll();
      setWorlds(data);
    } catch (error) {
      console.error("Failed to load worlds:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (world?: World) => {
    setEditingWorld(world || null);
    setFormData(
      world
        ? {
            name: world.name,
            description: world.description,
            background: world.background,
          }
        : {
            name: "",
            description: "",
            background: "",
          }
    );
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingWorld(null);
    setFormData({ name: "", description: "", background: "" });
  };

  const handleSubmit = async () => {
    try {
      if (editingWorld) {
        await worldsApi.update(editingWorld.id, formData);
      } else {
        await worldsApi.create(formData);
      }
      handleCloseDialog();
      loadWorlds();
    } catch (error) {
      console.error("Failed to save world:", error);
    }
  };

  const handleDelete = async (worldId: number) => {
    if (window.confirm("この世界を削除しますか？")) {
      try {
        await worldsApi.delete(worldId);
        loadWorlds();
      } catch (error) {
        console.error("Failed to delete world:", error);
      }
    }
  };

  const handleOpenGenerateDialog = () => {
    setGenerateData({
      keywords: "",
      generate_characters: true,
      character_count: 3,
    });
    setGenerateDialogOpen(true);
  };

  const handleCloseGenerateDialog = () => {
    setGenerateDialogOpen(false);
    setGenerateData({
      keywords: "",
      generate_characters: true,
      character_count: 3,
    });
  };

  const handleGenerate = async () => {
    if (!generateData.keywords.trim()) {
      alert("キーワードを入力してください");
      return;
    }

    setGenerating(true);
    setProgressMessage("AIで世界を生成中...");

    try {
      const result = await worldsApi.generate(generateData);

      setGenerating(false);
      handleCloseGenerateDialog();
      loadWorlds();

      if (result.characters.length > 0) {
        alert(
          `世界「${result.world.name}」と${result.characters.length}人のキャラクターを生成しました！`
        );
      } else {
        alert(`世界「${result.world.name}」を生成しました！`);
      }
    } catch (error) {
      setGenerating(false);
      console.error("Failed to generate world:", error);
      alert("世界の生成に失敗しました。もう一度お試しください。");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2 text-lg">Loading...</span>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">世界管理</h1>
          <p className="text-muted-foreground">あなたの創造した世界を管理し、キャラクターや議論を作成できます。</p>
        </div>
        <Button
          variant="outline"
          onClick={handleOpenGenerateDialog}
          className="gap-2"
        >
          <Sparkles className="h-4 w-4" />
          AIで世界を生成
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {worlds.map((world) => (
          <Card key={world.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <CardTitle className="text-xl">{world.name}</CardTitle>
              <CardDescription className="text-sm text-muted-foreground">
                {world.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground leading-relaxed">
                <span className="font-medium">背景:</span> {world.background.substring(0, 100)}
                {world.background.length > 100 ? "..." : ""}
              </p>
            </CardContent>
            <CardFooter className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigate(`/characters/${world.id}`)}
                className="gap-1"
              >
                <Users className="h-3 w-3" />
                キャラクター
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigate(`/discussions/${world.id}`)}
                className="gap-1"
              >
                <MessageCircle className="h-3 w-3" />
                議論
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleOpenDialog(world)}
                className="gap-1"
              >
                <Edit className="h-3 w-3" />
                編集
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleDelete(world.id)}
                className="gap-1 text-destructive hover:text-destructive"
              >
                <Trash2 className="h-3 w-3" />
                削除
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      <Button
        onClick={() => handleOpenDialog()}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg"
        size="icon"
      >
        <Plus className="h-6 w-6" />
      </Button>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[525px]">
          <DialogHeader>
            <DialogTitle>
              {editingWorld ? "世界を編集" : "新しい世界を作成"}
            </DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">世界名</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="世界の名前を入力してください"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="description">説明</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="世界の簡単な説明を入力してください"
                rows={3}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="background">背景設定</Label>
              <Textarea
                id="background"
                value={formData.background}
                onChange={(e) => setFormData({ ...formData, background: e.target.value })}
                placeholder="世界の詳細な背景や設定を入力してください"
                rows={5}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCloseDialog}>
              キャンセル
            </Button>
            <Button onClick={handleSubmit}>
              {editingWorld ? "更新" : "作成"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 世界生成ダイアログ */}
      <Dialog open={generateDialogOpen} onOpenChange={setGenerateDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>AIで世界を生成</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="keywords">キーワード</Label>
              <Input
                id="keywords"
                value={generateData.keywords}
                onChange={(e) => setGenerateData({ ...generateData, keywords: e.target.value })}
                placeholder="例: ドラゴン、魔法学校、宇宙ステーション"
              />
              <p className="text-sm text-muted-foreground">
                世界のテーマやキーワードを入力してください
              </p>
            </div>
            
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="generate-characters"
                checked={generateData.generate_characters}
                onChange={(e) => setGenerateData({ ...generateData, generate_characters: e.target.checked })}
                className="h-4 w-4 rounded border-gray-300"
              />
              <Label htmlFor="generate-characters">キャラクターも一緒に生成する</Label>
            </div>

            {generateData.generate_characters && (
              <div className="grid gap-2">
                <Label>生成するキャラクター数: {generateData.character_count}人</Label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  step="1"
                  value={generateData.character_count}
                  onChange={(e) => setGenerateData({ ...generateData, character_count: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>1</span>
                  <span>2</span>
                  <span>3</span>
                  <span>4</span>
                  <span>5</span>
                </div>
              </div>
            )}

            {generating && (
              <div className="text-center py-4">
                <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">{progressMessage}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  しばらくお待ちください...
                </p>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCloseGenerateDialog} disabled={generating}>
              キャンセル
            </Button>
            <Button
              onClick={handleGenerate}
              disabled={generating || !generateData.keywords.trim()}
              className="gap-2"
            >
              {generating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  生成
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default WorldsPage;
