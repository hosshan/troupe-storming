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
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, ArrowBack as ArrowBackIcon } from '@mui/icons-material';
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
            {world?.name} - キャラクター管理
          </Typography>
        </Breadcrumbs>
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          キャラクター管理
        </Typography>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/worlds')}
        >
          世界一覧に戻る
        </Button>
      </Box>

      {world && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              世界: {world.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {world.description}
            </Typography>
          </CardContent>
        </Card>
      )}

      <Grid container spacing={3}>
        {characters.map((character) => (
          <Grid item xs={12} md={6} lg={4} key={character.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" component="h2" gutterBottom>
                  {character.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {character.description}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  性格: {character.personality}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  背景: {character.background.substring(0, 100)}
                  {character.background.length > 100 ? '...' : ''}
                </Typography>
              </CardContent>
              <CardActions>
                <Button
                  size="small"
                  startIcon={<EditIcon />}
                  onClick={() => handleOpenDialog(character)}
                >
                  編集
                </Button>
                <Button
                  size="small"
                  startIcon={<DeleteIcon />}
                  onClick={() => handleDelete(character.id)}
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
          {editingCharacter ? 'キャラクターを編集' : '新しいキャラクターを作成'}
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="キャラクター名"
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
            label="性格"
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            value={formData.personality}
            onChange={(e) => setFormData({ ...formData, personality: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="背景"
            fullWidth
            multiline
            rows={4}
            variant="outlined"
            value={formData.background}
            onChange={(e) => setFormData({ ...formData, background: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>キャンセル</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingCharacter ? '更新' : '作成'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CharactersPage;