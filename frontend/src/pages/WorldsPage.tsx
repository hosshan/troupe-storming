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
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, People as PeopleIcon, Chat as ChatIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { World, CreateWorldRequest } from '../types';
import { worldsApi } from '../services/api';

const WorldsPage: React.FC = () => {
  const navigate = useNavigate();
  const [worlds, setWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingWorld, setEditingWorld] = useState<World | null>(null);
  const [formData, setFormData] = useState<CreateWorldRequest>({
    name: '',
    description: '',
    background: '',
  });

  useEffect(() => {
    loadWorlds();
  }, []);

  const loadWorlds = async () => {
    try {
      const data = await worldsApi.getAll();
      setWorlds(data);
    } catch (error) {
      console.error('Failed to load worlds:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (world?: World) => {
    setEditingWorld(world || null);
    setFormData(world ? {
      name: world.name,
      description: world.description,
      background: world.background,
    } : {
      name: '',
      description: '',
      background: '',
    });
    setDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingWorld(null);
    setFormData({ name: '', description: '', background: '' });
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
      console.error('Failed to save world:', error);
    }
  };

  const handleDelete = async (worldId: number) => {
    if (window.confirm('この世界を削除しますか？')) {
      try {
        await worldsApi.delete(worldId);
        loadWorlds();
      } catch (error) {
        console.error('Failed to delete world:', error);
      }
    }
  };

  if (loading) {
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          世界管理
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {worlds.map((world) => (
          <Grid item xs={12} md={6} lg={4} key={world.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" component="h2" gutterBottom>
                  {world.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {world.description}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  背景: {world.background.substring(0, 100)}
                  {world.background.length > 100 ? '...' : ''}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  startIcon={<PeopleIcon />}
                  onClick={() => navigate(`/characters/${world.id}`)}
                >
                  キャラクター
                </Button>
                <Button
                  size="small"
                  startIcon={<ChatIcon />}
                  onClick={() => navigate(`/discussions/${world.id}`)}
                >
                  議論
                </Button>
                <Button
                  size="small"
                  startIcon={<EditIcon />}
                  onClick={() => handleOpenDialog(world)}
                >
                  編集
                </Button>
                <Button
                  size="small"
                  startIcon={<DeleteIcon />}
                  onClick={() => handleDelete(world.id)}
                  color="error"
                >
                  削除
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Fab
        color="primary"
        aria-label="add"
        onClick={() => handleOpenDialog()}
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
      >
        <AddIcon />
      </Fab>

      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingWorld ? '世界を編集' : '新しい世界を作成'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="世界名"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="説明"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="背景設定"
            fullWidth
            multiline
            rows={5}
            variant="outlined"
            value={formData.background}
            onChange={(e) => setFormData({ ...formData, background: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>キャンセル</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingWorld ? '更新' : '作成'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WorldsPage;