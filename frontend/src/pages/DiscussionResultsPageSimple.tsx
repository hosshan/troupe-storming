import React, { useState, useEffect, useRef } from "react";
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
} from "@mui/material";
import {
  ArrowBack as ArrowBackIcon,
  Refresh as RefreshIcon,
} from "@mui/icons-material";
import { useNavigate, useParams } from "react-router-dom";
import { Discussion, World, Character } from "../types";
import { discussionsApi, worldsApi, charactersApi } from "../services/api";

interface DiscussionMessage {
  speaker: string;
  content: string;
  timestamp: string;
}

interface DiscussionProgress {
  message: string;
  progress: number;
  completed: boolean;
  error?: string;
  messages?: DiscussionMessage[];
}

const DiscussionResultsPageSimple: React.FC = () => {
  const navigate = useNavigate();
  const { worldId, discussionId } = useParams<{
    worldId: string;
    discussionId: string;
  }>();
  const [world, setWorld] = useState<World | null>(null);
  const [discussion, setDiscussion] = useState<Discussion | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [discussionRunning, setDiscussionRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState("");
  const [messages, setMessages] = useState<DiscussionMessage[]>([]);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (worldId && discussionId) {
      loadInitialData();
    }

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [worldId, discussionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log("Loading initial data for discussion:", discussionId);

      const [worldData, discussionData, charactersData] = await Promise.all([
        worldsApi.getById(parseInt(worldId!)),
        discussionsApi.getById(parseInt(discussionId!)),
        charactersApi.getAll(parseInt(worldId!)),
      ]);

      console.log("Loaded discussion data:", discussionData);
      console.log("Discussion status:", discussionData.status);
      console.log("Discussion result:", discussionData.result);

      setWorld(worldData);
      setDiscussion(discussionData);
      setCharacters(charactersData);

      // Handle different discussion states
      if (
        discussionData.status === "completed" &&
        discussionData.result &&
        discussionData.result.messages
      ) {
        console.log(
          "Discussion is completed, setting messages:",
          discussionData.result.messages
        );
        setMessages(discussionData.result.messages);
        setProgress(100);
        setProgressMessage("議論が完了しました");
        setDiscussionRunning(false);
      } else if (discussionData.status === "running") {
        console.log("Discussion is running, starting streaming updates");
        setDiscussionRunning(true);
        startListeningForUpdates();
      } else if (discussionData.status === "pending") {
        console.log("Discussion is pending, ready to start");
        setDiscussionRunning(false);
      } else if (discussionData.status === "failed") {
        console.log("Discussion failed");
        setError("議論が失敗しました");
        setDiscussionRunning(false);
      } else {
        console.log("Unknown discussion status:", discussionData.status);
        setDiscussionRunning(false);
      }
    } catch (error) {
      console.error("Failed to load data:", error);
      setError("データの読み込みに失敗しました: " + (error as Error).message);
    } finally {
      setLoading(false);
      console.log("Loading completed");
    }
  };

  const startDiscussion = async () => {
    try {
      setDiscussionRunning(true);
      setProgressMessage("議論を開始しています...");
      setProgress(0);
      setMessages([]);

      await discussionsApi.start(parseInt(discussionId!));
      startListeningForUpdates();
    } catch (error) {
      console.error("Failed to start discussion:", error);
      setError("議論の開始に失敗しました");
      setDiscussionRunning(false);
    }
  };

  const startListeningForUpdates = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setDiscussionRunning(true);

    eventSourceRef.current = discussionsApi.streamProgress(
      parseInt(discussionId!),
      (data: DiscussionProgress) => {
        setProgress(data.progress);
        setProgressMessage(data.message);

        if (data.messages) {
          setMessages(data.messages);
        }

        if (data.completed) {
          setDiscussionRunning(false);

          if (data.error) {
            setError(data.error);
          } else {
            setProgressMessage("議論が完了しました");
            // Refresh discussion data to get final results
            refreshDiscussion();
          }
        }
      },
      (error: string) => {
        setDiscussionRunning(false);
        setError(error);
      }
    );
  };

  const refreshDiscussion = async () => {
    try {
      console.log("Refreshing discussion data...");
      const discussionData = await discussionsApi.getById(
        parseInt(discussionId!)
      );
      console.log("Refreshed discussion data:", discussionData);
      setDiscussion(discussionData);

      if (discussionData.result && discussionData.result.messages) {
        console.log(
          "Setting refreshed messages:",
          discussionData.result.messages
        );
        setMessages(discussionData.result.messages);
      } else {
        console.log("No messages in refreshed discussion data");
      }
    } catch (error) {
      console.error("Failed to refresh discussion:", error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending":
        return "default";
      case "running":
        return "warning";
      case "completed":
        return "success";
      case "failed":
        return "error";
      default:
        return "default";
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case "pending":
        return "待機中";
      case "running":
        return "実行中";
      case "completed":
        return "完了";
      case "failed":
        return "失敗";
      default:
        return status;
    }
  };

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="400px"
      >
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
            onClick={() => navigate("/worlds")}
            sx={{ textDecoration: "none" }}
          >
            世界管理
          </Link>
          <Link
            component="button"
            variant="body1"
            onClick={() => navigate(`/discussions/${worldId}`)}
            sx={{ textDecoration: "none" }}
          >
            {world?.name} - 議論管理
          </Link>
          <Typography color="text.primary">
            議論結果: {discussion?.theme}
          </Typography>
        </Breadcrumbs>
      </Box>

      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={3}
      >
        <Typography variant="h4" component="h1">
          議論結果
        </Typography>
        <Box>
          <Button
            startIcon={<RefreshIcon />}
            onClick={loadInitialData}
            sx={{ mr: 1 }}
            disabled={discussionRunning}
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
            <Box
              display="flex"
              justifyContent="space-between"
              alignItems="center"
              mb={2}
            >
              <Typography variant="h5">{discussion.theme}</Typography>
              <Chip
                label={getStatusText(discussion.status)}
                color={getStatusColor(discussion.status)}
              />
            </Box>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              {discussion.description}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              参加キャラクター: {characters.map((c) => c.name).join(", ")}
            </Typography>

            {discussion.status === "completed" && (
              <Button
                variant="outlined"
                onClick={startDiscussion}
                sx={{ mt: 2 }}
              >
                新しい議論を開始
              </Button>
            )}

            {discussion.status === "pending" && (
              <Button
                variant="contained"
                onClick={startDiscussion}
                sx={{ mt: 2 }}
                disabled={loading}
              >
                {loading ? "議論開始中..." : "議論を開始"}
              </Button>
            )}

            {discussion.status === "running" && (
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

      {discussionRunning && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <CircularProgress size={24} sx={{ mr: 2 }} />
              <Typography variant="h6">議論実行中...</Typography>
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
          議論の流れ ({messages.length}件のメッセージ)
        </Typography>

        {(() => {
          console.log(
            "Rendering messages, count:",
            messages.length,
            "messages:",
            messages
          );
          return null;
        })()}

        {messages.length === 0 && !discussionRunning && (
          <Typography color="text.secondary" textAlign="center" py={4}>
            まだ議論が開始されていません
          </Typography>
        )}

        <List sx={{ maxHeight: "600px", overflow: "auto" }}>
          {messages.map((message, index) => (
            <ListItem
              key={index}
              sx={{
                borderLeft:
                  message.speaker === "システム"
                    ? "4px solid #2196f3"
                    : "4px solid #4caf50",
                mb: 1,
                backgroundColor:
                  message.speaker === "システム" ? "#f5f5f5" : "transparent",
              }}
            >
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography
                      variant="subtitle2"
                      component="span"
                      fontWeight="bold"
                    >
                      {message.speaker}
                    </Typography>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      component="span"
                    >
                      {new Date(message.timestamp).toLocaleTimeString("ja-JP")}
                    </Typography>
                  </Box>
                }
                secondary={
                  <Typography
                    variant="body2"
                    sx={{ mt: 0.5, whiteSpace: "pre-wrap" }}
                  >
                    {message.content}
                  </Typography>
                }
              />
            </ListItem>
          ))}
          <div ref={messagesEndRef} />
        </List>

        {discussionRunning && messages.length === 0 && (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default DiscussionResultsPageSimple;
