import React, { useState, useEffect } from 'react';
import {
  Plus,
  Play,
  ArrowLeft,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { useNavigate, useParams } from 'react-router-dom';
import { Discussion, World, CreateDiscussionRequest, Character } from '../types';
import { discussionsApi, worldsApi, charactersApi } from '../services/api';

const DiscussionsPage: React.FC = () => {
  const navigate = useNavigate();
  const { worldId } = useParams<{ worldId: string }>();
  const [world, setWorld] = useState<World | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [discussions, setDiscussions] = useState<Discussion[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState<CreateDiscussionRequest>({
    theme: '',
    description: '',
    world_id: parseInt(worldId || '0'),
  });

  useEffect(() => {
    if (worldId) {
      loadWorld();
      loadCharacters();
      loadDiscussions();
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
    }
  };

  const loadDiscussions = async () => {
    try {
      const data = await discussionsApi.getAll(parseInt(worldId!));
      setDiscussions(data);
    } catch (error) {
      console.error('Failed to load discussions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = () => {
    setFormData({
      theme: '',
      description: '',
      world_id: parseInt(worldId || '0'),
    });
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setFormData({
      theme: '',
      description: '',
      world_id: parseInt(worldId || '0'),
    });
  };

  const handleSubmit = async () => {
    try {
      await discussionsApi.create(formData);
      handleCloseDialog();
      loadDiscussions();
    } catch (error) {
      console.error('Failed to create discussion:', error);
    }
  };

  const handleStartDiscussion = (discussionId: number) => {
    // Navigate to the discussion results page which will handle starting the discussion
    navigate(`/discussions/${worldId}/results/${discussionId}`);
  };

  const handleViewResult = (discussion: Discussion) => {
    // Navigate to the discussion results page
    navigate(`/discussions/${worldId}/results/${discussion.id}`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'secondary';
      case 'running': return 'default';
      case 'completed': return 'default';
      case 'failed': return 'destructive';
      default: return 'secondary';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return '待機中';
      case 'running': return '実行中';
      case 'completed': return '完了';
      case 'failed': return '失敗';
      default: return status;
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
            {world?.name} - 議論管理
          </li>
        </ol>
      </nav>

      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">議論管理</h1>
          {world && (
            <p className="text-muted-foreground">{world.name}の世界でキャラクターたちが議論を行います。</p>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={loadDiscussions}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            更新
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate('/worlds')}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            世界一覧に戻る
          </Button>
        </div>
      </div>

      {world && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-xl">世界: {world.name}</CardTitle>
            <CardDescription>{world.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              登録キャラクター数: <span className="font-medium">{characters.length}人</span>
            </p>
          </CardContent>
        </Card>
      )}

      {characters.length === 0 && (
        <Card className="mb-6 border-destructive/50 bg-destructive/5">
          <CardContent className="pt-6">
            <p className="text-destructive mb-4">
              この世界にはキャラクターが登録されていません。<br />
              議論を開始するには、まずキャラクターを作成してください。
            </p>
            <Button
              onClick={() => navigate(`/characters/${worldId}`)}
            >
              キャラクターを作成
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {discussions.map((discussion) => (
          <Card key={discussion.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex justify-between items-start gap-3">
                <div className="flex-1 min-w-0">
                  <CardTitle className="text-xl leading-tight">{discussion.theme}</CardTitle>
                </div>
                <div className="flex-shrink-0">
                  <Badge variant={getStatusColor(discussion.status)} className="whitespace-nowrap">
                    {getStatusText(discussion.status)}
                  </Badge>
                </div>
              </div>
              <CardDescription className="text-sm text-muted-foreground mt-2">
                {discussion.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                作成日: {new Date(discussion.created_at).toLocaleDateString('ja-JP')}
              </p>
            </CardContent>
            <CardFooter className="flex gap-2">
              {discussion.status === 'pending' && characters.length > 0 && (
                <Button
                  size="sm"
                  onClick={() => handleStartDiscussion(discussion.id)}
                  className="gap-1"
                >
                  <Play className="h-3 w-3" />
                  議論開始
                </Button>
              )}
              {(discussion.status === 'completed' || discussion.status === 'running') && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleViewResult(discussion)}
                >
                  {discussion.status === 'completed' ? '結果を見る' : '議論を見る'}
                </Button>
              )}
            </CardFooter>
          </Card>
        ))}
      </div>

      <Button
        onClick={handleOpenDialog}
        disabled={characters.length === 0}
        className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg"
        size="icon"
      >
        <Plus className="h-6 w-6" />
      </Button>

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-[525px]">
          <DialogHeader>
            <DialogTitle>新しい議論テーマを作成</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="theme">議論テーマ</Label>
              <Input
                id="theme"
                value={formData.theme}
                onChange={(e) => setFormData({ ...formData, theme: e.target.value })}
                placeholder="議論のテーマを入力してください"
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="description">詳細説明</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="議論の詳細や背景を入力してください"
                rows={4}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={handleCloseDialog}>
              キャンセル
            </Button>
            <Button onClick={handleSubmit}>
              作成
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

    </div>
  );
};

export default DiscussionsPage;