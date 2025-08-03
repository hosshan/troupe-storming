import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Fab,
  Breadcrumbs,
  Link,
  Chip,
} from '@mui/material';
import { Add as AddIcon, PlayArrow as PlayIcon, ArrowBack as ArrowBackIcon, Refresh as RefreshIcon } from '@mui/icons-material';
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
      case 'pending': return 'default';
      case 'running': return 'warning';
      case 'completed': return 'success';
      case 'failed': return 'error';
      default: return 'default';
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
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Box mb={2}>
        <Breadcrumbs>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate('/worlds')}
            sx={{ textDecoration: 'none' }}
          >
            世界管理
          </Link>
          <Typography color="text.primary">
            {world?.name} - 議論管理
          </Typography>
        </Breadcrumbs>
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          議論管理
        </Typography>
        <Box>
          <Button
            startIcon={<RefreshIcon />}
            onClick={loadDiscussions}
            sx={{ mr: 1 }}
          >
            更新
          </Button>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/worlds')}
          >
            世界一覧に戻る
          </Button>
        </Box>
      </Box>

      {world && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              世界: {world.name}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {world.description}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              登録キャラクター数: {characters.length}人
            </Typography>
          </CardContent>
        </Card>
      )}

      {characters.length === 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="body1" color="error">
              この世界にはキャラクターが登録されていません。
              議論を開始するには、まずキャラクターを作成してください。
            </Typography>
            <Button
              variant="contained"
              onClick={() => navigate(`/characters/${worldId}`)}
              sx={{ mt: 2 }}
            >
              キャラクターを作成
            </Button>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={3}>
        {discussions.map((discussion) => (
          <Grid item xs={12} md={6} lg={4} key={discussion.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                  <Typography variant="h6" component="h2">
                    {discussion.theme}
                  </Typography>
                  <Chip
                    label={getStatusText(discussion.status)}
                    color={getStatusColor(discussion.status)}
                    size="small"
                  />
                </Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {discussion.description}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  作成日: {new Date(discussion.created_at).toLocaleDateString('ja-JP')}
                </Typography>
              </CardContent>
              <CardActions>
                {discussion.status === 'pending' && characters.length > 0 && (
                  <Button
                    size="small"
                    startIcon={<PlayIcon />}
                    onClick={() => handleStartDiscussion(discussion.id)}
                    variant="contained"
                  >
                    議論開始
                  </Button>
                )}
                {(discussion.status === 'completed' || discussion.status === 'running') && (
                  <Button
                    size="small"
                    onClick={() => handleViewResult(discussion)}
                  >
                    {discussion.status === 'completed' ? '結果を見る' : '議論を見る'}
                  </Button>
                )}
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Fab
        color="primary"
        aria-label="add"
        onClick={handleOpenDialog}
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        disabled={characters.length === 0}
      >
        <AddIcon />
      </Fab>

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>新しい議論テーマを作成</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="議論テーマ"
            fullWidth
            variant="outlined"
            value={formData.theme}
            onChange={(e) => setFormData({ ...formData, theme: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="詳細説明"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>キャンセル</Button>
          <Button onClick={handleSubmit} variant="contained">
            作成
          </Button>
        </DialogActions>
      </Dialog>

    </Box>
  );
};

export default DiscussionsPage;