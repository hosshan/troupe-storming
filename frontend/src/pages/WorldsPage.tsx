import React, { useState, useEffect } from "react";
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
  Switch,
  FormControlLabel,
  Slider,
  CircularProgress,
} from "@mui/material";
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  People as PeopleIcon,
  Chat as ChatIcon,
  AutoFixHigh as GenerateIcon,
} from "@mui/icons-material";
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
    return <Typography>Loading...</Typography>;
  }

  return (
    <Box>
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography variant="h4" component="h1">
          世界管理
        </Typography>
        <Button
          variant="outlined"
          startIcon={<GenerateIcon />}
          onClick={handleOpenGenerateDialog}
        >
          AIで世界を生成
        </Button>
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
                  {world.background.length > 100 ? "..." : ""}
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
        sx={{ position: "fixed", bottom: 16, right: 16 }}
      >
        <AddIcon />
      </Fab>

      <Dialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingWorld ? "世界を編集" : "新しい世界を作成"}
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
            onChange={(e) =>
              setFormData({ ...formData, description: e.target.value })
            }
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
            onChange={(e) =>
              setFormData({ ...formData, background: e.target.value })
            }
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>キャンセル</Button>
          <Button onClick={handleSubmit} variant="contained">
            {editingWorld ? "更新" : "作成"}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 世界生成ダイアログ */}
      <Dialog
        open={generateDialogOpen}
        onClose={handleCloseGenerateDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>AIで世界を生成</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="キーワード"
            placeholder="例: ドラゴン、魔法学校、宇宙ステーション"
            fullWidth
            variant="outlined"
            value={generateData.keywords}
            onChange={(e) =>
              setGenerateData({ ...generateData, keywords: e.target.value })
            }
            sx={{ mb: 3 }}
            helperText="世界のテーマやキーワードを入力してください"
          />

          <FormControlLabel
            control={
              <Switch
                checked={generateData.generate_characters}
                onChange={(e) =>
                  setGenerateData({
                    ...generateData,
                    generate_characters: e.target.checked,
                  })
                }
              />
            }
            label="キャラクターも一緒に生成する"
            sx={{ mb: 2 }}
          />

          {generateData.generate_characters && (
            <Box sx={{ mb: 2 }}>
              <Typography gutterBottom>
                生成するキャラクター数: {generateData.character_count}人
              </Typography>
              <Slider
                value={generateData.character_count}
                onChange={(_, value) =>
                  setGenerateData({
                    ...generateData,
                    character_count: value as number,
                  })
                }
                min={1}
                max={5}
                step={1}
                marks
                valueLabelDisplay="auto"
              />
            </Box>
          )}

          {/* Progress display during generation */}
          {generating && (
            <Box sx={{ mt: 3, mb: 2, textAlign: "center" }}>
              <CircularProgress size={40} sx={{ mb: 2 }} />
              <Typography variant="body2" color="text.secondary">
                {progressMessage}
              </Typography>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ mt: 1, display: "block" }}
              >
                しばらくお待ちください...
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseGenerateDialog} disabled={generating}>
            キャンセル
          </Button>
          <Button
            onClick={handleGenerate}
            variant="contained"
            disabled={generating || !generateData.keywords.trim()}
            startIcon={
              generating ? <CircularProgress size={20} /> : <GenerateIcon />
            }
          >
            {generating ? "生成中..." : "生成"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WorldsPage;
