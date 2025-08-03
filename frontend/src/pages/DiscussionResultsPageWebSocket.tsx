import React, { useState, useEffect, useRef } from 'react';
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
  Snackbar,
} from '@mui/material';
import { 
  ArrowBack as ArrowBackIcon, 
  Refresh as RefreshIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon 
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { Discussion, World, Character } from '../types';
import { discussionsApi, worldsApi, charactersApi } from '../services/api';
import { useWebSocketDiscussion } from '../hooks/useWebSocketDiscussion';

interface DiscussionMessage {
  speaker: string;
  content: string;
  timestamp: string;
}

const DiscussionResultsPageWebSocket: React.FC = () => {
  const navigate = useNavigate();
  const { worldId, discussionId } = useParams<{ worldId: string; discussionId: string }>();
  const [world, setWorld] = useState<World | null>(null);
  const [discussion, setDiscussion] = useState<Discussion | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // WebSocket connection for real-time updates
  const {
    isConnected,
    isConnecting,
    progress,
    progressMessage,
    messages,
    error: wsError,
    isCompleted,
    connect,
    disconnect,
    retry,
  } = useWebSocketDiscussion({
    discussionId: parseInt(discussionId!),
    onProgress: (data) => {
      console.log('Progress update:', data);
    },
    onComplete: (finalMessages) => {
      console.log('Discussion completed:', finalMessages);
      setSnackbarMessage('議論が完了しました！');
      setSnackbarOpen(true);
      refreshDiscussion();
    },
    onError: (error) => {
      console.error('WebSocket error:', error);
      setSnackbarMessage(`エラー: ${error}`);
      setSnackbarOpen(true);
    },
    autoConnect: false, // Manual connection after loading data
  });

  useEffect(() => {
    if (worldId && discussionId) {
      loadInitialData();
    }
  }, [worldId, discussionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Connect WebSocket after initial data is loaded
  useEffect(() => {
    if (!loading && discussion) {
      connect();
    }
    
    return () => {
      disconnect();
    };
  }, [loading, discussion, connect, disconnect]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [worldData, discussionData, charactersData] = await Promise.all([
        worldsApi.getById(parseInt(worldId!)),
        discussionsApi.getById(parseInt(discussionId!)),
        charactersApi.getAll(parseInt(worldId!))
      ]);
      
      setWorld(worldData);
      setDiscussion(discussionData);
      setCharacters(charactersData);
      
    } catch (error) {
      console.error('Failed to load data:', error);
      setSnackbarMessage('データの読み込みに失敗しました');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };

  const refreshDiscussion = async () => {
    try {
      const discussionData = await discussionsApi.getById(parseInt(discussionId!));
      setDiscussion(discussionData);
    } catch (error) {
      console.error('Failed to refresh discussion:', error);
    }
  };

  const handleRetry = () => {
    retry();
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
        <CircularProgress />
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
        <Box display="flex" alignItems="center" gap={2}>
          <Typography variant="h4" component="h1">
            議論結果
          </Typography>
          
          {/* Connection status indicator */}
          <Box display="flex" alignItems="center" gap={1}>
            {isConnected ? (
              <WifiIcon color="success" />
            ) : isConnecting ? (
              <CircularProgress size={20} />
            ) : (
              <WifiOffIcon color="disabled" />
            )}
            <Typography variant="caption" color="text.secondary">
              {isConnected ? '接続中' : isConnecting ? '接続中...' : '未接続'}
            </Typography>
          </Box>
        </Box>
        
        <Box>
          {wsError && (
            <Button
              variant="outlined"
              onClick={handleRetry}
              sx={{ mr: 1 }}
            >
              再接続
            </Button>
          )}
          <Button
            startIcon={<RefreshIcon />}
            onClick={refreshDiscussion}
            sx={{ mr: 1 }}
            disabled={isConnecting}
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
          </CardContent>
        </Card>
      )}

      {wsError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {wsError}
        </Alert>
      )}

      {(isConnecting || (!isCompleted && isConnected)) && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <CircularProgress size={24} sx={{ mr: 2 }} />
              <Typography variant="h6">
                議論実行中...
              </Typography>
            </Box>
            <LinearProgress 
              variant="determinate" 
              value={progress} 
              sx={{ mb: 2 }}
            />
            <Typography variant="body2" color="text.secondary">
              {progressMessage}
            </Typography>
          </CardContent>
        </Card>
      )}

      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          議論の流れ
        </Typography>
        
        {messages.length === 0 && !isConnecting && !isConnected && (
          <Typography color="text.secondary" textAlign="center" py={4}>
            WebSocketに接続して議論を開始してください
          </Typography>
        )}
        
        {messages.length === 0 && isConnecting && (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        )}
        
        <List sx={{ maxHeight: '600px', overflow: 'auto' }}>
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
          <div ref={messagesEndRef} />
        </List>
      </Paper>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
};

export default DiscussionResultsPageWebSocket;