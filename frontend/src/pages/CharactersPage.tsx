import React, { useState, useEffect } from 'react';
import {
  Plus,
  Edit,
  Trash2,
  ArrowLeft,
  Loader2,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { useNavigate, useParams } from 'react-router-dom';
import { Character, World, CreateCharacterRequest } from '../types';
import { charactersApi, worldsApi } from '../services/api';

const CharactersPage: React.FC = () => {
  const navigate = useNavigate();
  const { worldId } = useParams<{ worldId: string }>();
  const [world, setWorld] = useState<World | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCharacter, setEditingCharacter] = useState<Character | null>(null);
  const [formData, setFormData] = useState<CreateCharacterRequest>({
    name: '',
    description: '',
    personality: '',
    background: '',
    world_id: parseInt(worldId || '0'),
  });

  useEffect(() => {
    if (worldId) {
      loadWorld();
      loadCharacters();
    }
  }, [worldId]);

  const loadWorld = async () => {
    try {
      const worldData = await worldsApi.getById(parseInt(worldId!));
      setWorld(worldData);
    } catch (error) {
      console.error('Failed to load world:', error);
    }
  };

  const loadCharacters = async () => {
    try {
      const data = await charactersApi.getAll(parseInt(worldId!));
      setCharacters(data);
    } catch (error) {
      console.error('Failed to load characters:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (character?: Character) => {
    setEditingCharacter(character || null);
    setFormData(character ? {
      name: character.name,
      description: character.description,
      personality: character.personality,
      background: character.background,
      world_id: character.world_id,
    } : {
      name: '',
      description: '',
      personality: '',
      background: '',
      world_id: parseInt(worldId || '0'),
    });
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingCharacter(null);
    setFormData({
      name: '',
      description: '',
      personality: '',
      background: '',
      world_id: parseInt(worldId || '0'),
    });
  };

  const handleSubmit = async () => {
    try {
      if (editingCharacter) {
        await charactersApi.update(editingCharacter.id, formData);
      } else {
        await charactersApi.create(formData);
      }
      handleCloseDialog();
      loadCharacters();
    } catch (error) {
      console.error('Failed to save character:', error);
    }
  };

  const handleDelete = async (characterId: number) => {
    if (window.confirm('このキャラクターを削除しますか？')) {
      try {
        await charactersApi.delete(characterId);
        loadCharacters();
      } catch (error) {
        console.error('Failed to delete character:', error);
      }
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
      <nav className="mb-6">
        <ol className="flex items-center space-x-2 text-sm text-muted-foreground">
          <li>
            <button
              onClick={() => navigate('/worlds')}
              className="hover:text-foreground transition-colors"
            >
              世界管理
            </button>
          </li>
          <li>/</li>
          <li className="text-foreground font-medium">
            {world?.name} - キャラクター管理
          </li>
        </ol>
      </nav>

      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">キャラクター管理</h1>
          {world && (
            <p className="text-muted-foreground">{world.name}の世界に登露されたキャラクターを管理できます。</p>
          )}
        </div>
        <Button
          variant="outline"
          onClick={() => navigate('/worlds')}
          className="gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          世界一覧に戻る
        </Button>
      </div>

      {world && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-xl">世界: {world.name}</CardTitle>
            <CardDescription>{world.description}</CardDescription>
          </CardHeader>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {characters.map((character) => (
          <Card key={character.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <CardTitle className="text-xl">{character.name}</CardTitle>
              <CardDescription className="text-sm text-muted-foreground">
                {character.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <p>
                  <span className="font-medium text-foreground">性格:</span>
                  <span className="text-muted-foreground ml-1">{character.personality}</span>
                </p>
                <p>
                  <span className="font-medium text-foreground">背景:</span>
                  <span className="text-muted-foreground ml-1">
                    {character.background.substring(0, 100)}
                    {character.background.length > 100 ? '...' : ''}
                  </span>
                </p>
              </div>
            </CardContent>
            <CardFooter className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleOpenDialog(character)}
                className="gap-1"
              >
                <Edit className="h-3 w-3" />
                編集
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleDelete(character.id)}
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
              {editingCharacter ? 'キャラクターを編集' : '新しいキャラクターを作成'}
            </DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">キャラクター名</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="キャラクターの名前を入力してください"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="description">説明</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="キャラクターの簡単な説明を入力してください"
                rows={3}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="personality">性格</Label>
              <Textarea
                id="personality"
                value={formData.personality}
                onChange={(e) => setFormData({ ...formData, personality: e.target.value })}
                placeholder="キャラクターの性格や特徴を入力してください"
                rows={3}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="background">背景</Label>
              <Textarea
                id="background"
                value={formData.background}
                onChange={(e) => setFormData({ ...formData, background: e.target.value })}
                placeholder="キャラクターの背景や経歴を入力してください"
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCloseDialog}>
              キャンセル
            </Button>
            <Button onClick={handleSubmit}>
              {editingCharacter ? '更新' : '作成'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CharactersPage;