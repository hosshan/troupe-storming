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

const DiscussionResultsPage: React.FC = () => {
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
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isComponentMountedRef = useRef(true);

  useEffect(() => {
    isComponentMountedRef.current = true;

    if (worldId && discussionId) {
      loadInitialData();
    }

    return () => {
      isComponentMountedRef.current = false;
      cleanupEventSource();
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [worldId, discussionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // discussionRunningの状態変化を追跡
  useEffect(() => {
    console.log("discussionRunning state changed:", discussionRunning);
  }, [discussionRunning]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const cleanupEventSource = () => {
    if (eventSourceRef.current) {
      console.log("Cleaning up EventSource connection");
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
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

      if (!isComponentMountedRef.current) return;

      setWorld(worldData);
      setDiscussion(discussionData);
      setCharacters(charactersData);

      // If discussion is completed, show results
      if (discussionData.status === "completed" && discussionData.result) {
        console.log(
          "Discussion is completed, setting messages:",
          discussionData.result.messages
        );
        setMessages(discussionData.result.messages || []);
        setProgress(100);
        setProgressMessage("議論が完了しました");
        setDiscussionRunning(false);
        console.log("Set discussionRunning to false for completed discussion"); // デバッグログを追加
      } else if (discussionData.status === "running") {
        console.log("Discussion is running, starting updates");
        // Start listening for real-time updates
        startListeningForUpdates();
      } else if (discussionData.status === "pending") {
        console.log("Discussion is pending, starting discussion");
        // Start the discussion
        startDiscussion();
      } else {
        console.log("Unknown discussion status:", discussionData.status);
      }
    } catch (error) {
      console.error("Failed to load data:", error);
      if (isComponentMountedRef.current) {
        setError("データの読み込みに失敗しました");
      }
    } finally {
      if (isComponentMountedRef.current) {
        setLoading(false);
        console.log("Loading completed");
      }
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
      if (isComponentMountedRef.current) {
        setError("議論の開始に失敗しました");
        setDiscussionRunning(false);
      }
    }
  };

  const startListeningForUpdates = () => {
    cleanupEventSource();

    if (!isComponentMountedRef.current) return;

    setDiscussionRunning(true);

    try {
      eventSourceRef.current = discussionsApi.streamProgress(
        parseInt(discussionId!),
        (data: DiscussionProgress) => {
          if (!isComponentMountedRef.current) return;

          console.log("Received discussion progress:", data); // デバッグログを追加

          setProgress(data.progress);
          setProgressMessage(data.message);

          if (data.messages) {
            setMessages(data.messages);
          }

          if (data.completed) {
            console.log(
              "Discussion completed, setting discussionRunning to false"
            ); // デバッグログを追加
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
          if (!isComponentMountedRef.current) return;

          console.error("EventSource error:", error);
          setDiscussionRunning(false);
          setError(error);

          // Try to reconnect after a delay
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }
          reconnectTimeoutRef.current = setTimeout(() => {
            if (
              isComponentMountedRef.current &&
              discussion?.status === "running"
            ) {
              console.log("Attempting to reconnect to discussion stream...");
              startListeningForUpdates();
            }
          }, 5000);
        }
      );
    } catch (error) {
      console.error("Failed to start EventSource:", error);
      if (isComponentMountedRef.current) {
        setError("リアルタイム更新の開始に失敗しました");
        setDiscussionRunning(false);
      }
    }
  };

  const refreshDiscussion = async () => {
    try {
      console.log("Refreshing discussion data...");
      const discussionData = await discussionsApi.getById(
        parseInt(discussionId!)
      );
      console.log("Refreshed discussion data:", discussionData);

      if (!isComponentMountedRef.current) return;

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

      // 議論が完了している場合は、discussionRunningを確実にfalseにする
      if (discussionData.status === "completed") {
        console.log(
          "Discussion status is completed, ensuring discussionRunning is false"
        );
        setDiscussionRunning(false);
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
            onClick={refreshDiscussion}
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
          議論の流れ
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

export default DiscussionResultsPage;
