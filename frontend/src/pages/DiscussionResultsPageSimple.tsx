import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Breadcrumbs,
  Link,
  Paper,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, Refresh as RefreshIcon } from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { Discussion, World, Character } from '../types';
import { discussionsApi, worldsApi, charactersApi } from '../services/api';

interface DiscussionMessage {
  speaker: string;
  content: string;
  timestamp: string;
}

const DiscussionResultsPageSimple: React.FC = () => {
  const navigate = useNavigate();
  const { worldId, discussionId } = useParams<{ worldId: string; discussionId: string }>();
  const [world, setWorld] = useState<World | null>(null);
  const [discussion, setDiscussion] = useState<Discussion | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<DiscussionMessage[]>([]);

  useEffect(() => {
    if (worldId && discussionId) {
      loadInitialData();
    }
  }, [worldId, discussionId]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Loading initial data for discussion:', discussionId);
      
      const [worldData, discussionData, charactersData] = await Promise.all([
        worldsApi.getById(parseInt(worldId!)),
        discussionsApi.getById(parseInt(discussionId!)),
        charactersApi.getAll(parseInt(worldId!))
      ]);
      
      console.log('Loaded discussion data:', discussionData);
      
      setWorld(worldData);
      setDiscussion(discussionData);
      setCharacters(charactersData);
      
      // If discussion has results, show them
      if (discussionData.result && discussionData.result.messages) {
        setMessages(discussionData.result.messages);
        console.log('Set messages:', discussionData.result.messages);
      }
      
    } catch (error) {
      console.error('Failed to load data:', error);
      setError('データの読み込みに失敗しました: ' + (error as Error).message);
    } finally {
      setLoading(false);
      console.log('Loading completed');
    }
  };

  const startNewDiscussion = async () => {
    try {
      setLoading(true);
      setError(null);
      setMessages([]);
      
      // Change status to pending first
      await discussionsApi.update(parseInt(discussionId!), { status: 'pending' });
      
      // Start the discussion
      await discussionsApi.start(parseInt(discussionId!));
      
      // Poll for updates
      let pollCount = 0;
      const maxPolls = 60; // 2 minutes max
      
      const pollInterval = setInterval(async () => {
        try {
          pollCount++;
          console.log(`Polling attempt ${pollCount}/${maxPolls}`);
          
          const updatedDiscussion = await discussionsApi.getById(parseInt(discussionId!));
          setDiscussion(updatedDiscussion);
          
          if (updatedDiscussion.status === 'completed' || updatedDiscussion.status === 'failed') {
            clearInterval(pollInterval);
            if (updatedDiscussion.result && updatedDiscussion.result.messages) {
              setMessages(updatedDiscussion.result.messages);
              console.log('Discussion completed with', updatedDiscussion.result.messages.length, 'messages');
            }
            setLoading(false);
          } else if (pollCount >= maxPolls) {
            // Timeout after 2 minutes
            clearInterval(pollInterval);
            setError('議論がタイムアウトしました。バックエンドサーバーを確認してください。');
            setLoading(false);
          }
        } catch (pollError) {
          console.error('Polling error:', pollError);
          if (pollCount >= 3) { // Stop after 3 consecutive errors
            clearInterval(pollInterval);
            setError('議論の監視中にエラーが発生しました: ' + (pollError as Error).message);
            setLoading(false);
          }
        }
      }, 2000); // Poll every 2 seconds
      
      // Stop polling after 2 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        setLoading(false);
      }, 120000);
      
    } catch (error) {
      console.error('Failed to start discussion:', error);
      setError('議論の開始に失敗しました: ' + (error as Error).message);
      setLoading(false);
    }
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
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Box textAlign="center">
          <CircularProgress sx={{ mb: 2 }} />
          <Typography>データを読み込み中...</Typography>
        </Box>
      </Box>
    );
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
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate(`/discussions/${worldId}`)}
            sx={{ textDecoration: 'none' }}
          >
            {world?.name} - 議論管理
          </Link>
          <Typography color="text.primary">
            議論結果: {discussion?.theme}
          </Typography>
        </Breadcrumbs>
      </Box>

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          議論結果
        </Typography>
        <Box>
          <Button
            startIcon={<RefreshIcon />}
            onClick={loadInitialData}
            sx={{ mr: 1 }}
          >
            更新
          </Button>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(`/discussions/${worldId}`)}
          >
            議論一覧に戻る
          </Button>
        </Box>
      </Box>

      {discussion && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h5">
                {discussion.theme}
              </Typography>
              <Chip
                label={getStatusText(discussion.status)}
                color={getStatusColor(discussion.status)}
              />
            </Box>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              {discussion.description}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              参加キャラクター: {characters.map(c => c.name).join(', ')}
            </Typography>
            
            {discussion.status === 'completed' && (
              <Button
                variant="outlined"
                onClick={startNewDiscussion}
                sx={{ mt: 2 }}
              >
                新しい議論を開始
              </Button>
            )}
            
            {discussion.status === 'pending' && (
              <Button
                variant="contained"
                onClick={startNewDiscussion}
                sx={{ mt: 2 }}
                disabled={loading}
              >
                {loading ? '議論開始中...' : '議論を開始'}
              </Button>
            )}
            
            {discussion.status === 'running' && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="primary">
                  議論を実行中です...
                </Typography>
                <LinearProgress sx={{ mt: 1 }} />
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          議論の流れ ({messages.length}件のメッセージ)
        </Typography>
        
        {messages.length === 0 && (
          <Typography color="text.secondary" textAlign="center" py={4}>
            議論メッセージがありません
          </Typography>
        )}
        
        <List>
          {messages.map((message, index) => (
            <ListItem 
              key={index}
              sx={{
                borderLeft: message.speaker === 'システム' ? '4px solid #2196f3' : '4px solid #4caf50',
                mb: 1,
                backgroundColor: message.speaker === 'システム' ? '#f5f5f5' : 'transparent'
              }}
            >
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="subtitle2" component="span" fontWeight="bold">
                      {message.speaker}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" component="span">
                      {new Date(message.timestamp).toLocaleTimeString('ja-JP')}
                    </Typography>
                  </Box>
                }
                secondary={
                  <Typography variant="body2" sx={{ mt: 0.5, whiteSpace: 'pre-wrap' }}>
                    {message.content}
                  </Typography>
                }
              />
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  );
};

export default DiscussionResultsPageSimple;