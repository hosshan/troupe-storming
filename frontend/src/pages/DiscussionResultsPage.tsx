import React, { useState, useEffect, useRef } from "react";
import {
  ArrowLeft,
  RefreshCw,
  Loader2,
  AlertCircle,
  Play,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../components/ui/card";
import { Progress } from "../components/ui/progress";
import { Badge } from "../components/ui/badge";
import { Alert, AlertDescription } from "../components/ui/alert";
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

  // メッセージの状態変化を追跡
  useEffect(() => {
    console.log("Messages state changed:", messages.length, "messages");
    if (messages.length > 0) {
      console.log("Latest message:", messages[messages.length - 1]);
    }
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
        console.log("Discussion is pending, ready to start");
        setDiscussionRunning(false);
        setProgress(0);
        setProgressMessage("議論を開始する準備ができています");
        // ユーザーが手動で開始ボタンを押すまで待機
      } else if (discussionData.status === "failed") {
        console.log("Discussion failed, showing error and retry option");
        setDiscussionRunning(false);
        setProgress(0);
        setProgressMessage("議論が失敗しました。再実行できます。");
        // エラーメッセージを設定（resultにエラー情報がある場合）
        if (discussionData.result && discussionData.result.error) {
          setError(`議論が失敗しました: ${discussionData.result.error}`);
        } else {
          setError("議論が失敗しました");
        }
      } else {
        console.log("Unknown discussion status:", discussionData.status);
        setDiscussionRunning(false);
        setError(`不明な議論ステータス: ${discussionData.status}`);
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
      // 議論の現在の状態を再確認
      const currentDiscussion = await discussionsApi.getById(
        parseInt(discussionId!)
      );

      // 既に開始されている場合は、ストリーミングを開始するだけ
      if (currentDiscussion.status === "running") {
        console.log(
          "Discussion is already running, starting streaming updates"
        );
        setDiscussionRunning(true);
        setProgressMessage("議論を実行中です...");
        startListeningForUpdates();
        return;
      }

      // 既に完了している場合は、新しい議論を作成する必要がある
      if (currentDiscussion.status === "completed") {
        console.log(
          "Discussion is completed, cannot restart existing discussion"
        );
        setError(
          "既に完了した議論は再開始できません。新しい議論を作成してください。"
        );
        return;
      }

      // pending状態の場合のみstartを呼び出す
      if (currentDiscussion.status === "pending") {
        setDiscussionRunning(true);
        setProgressMessage("議論を開始しています...");
        setProgress(0);
        setMessages([]);

        const response = await discussionsApi.start(parseInt(discussionId!));
        console.log("Start discussion response:", response);

        // レスポンスのステータスをチェック
        if (response?.status === "completed") {
          console.log("Discussion already completed, refreshing data...");
          setDiscussionRunning(false);
          setProgress(100);
          setProgressMessage("議論は既に完了しています");
          refreshDiscussion();
        } else if (response?.status === "running") {
          console.log("Discussion already running, starting updates...");
          startListeningForUpdates();
        } else {
          console.log("Discussion started successfully, starting updates...");
          startListeningForUpdates();
        }
      } else {
        console.log("Unexpected discussion status:", currentDiscussion.status);
        setError(`予期しない議論状態です: ${currentDiscussion.status}`);
      }
    } catch (error: any) {
      console.error("Failed to start discussion:", error);

      // 400エラーの場合は、既に開始されている可能性がある
      if (error.response?.status === 400) {
        const errorMessage = error.response.data?.detail || error.message;
        if (
          errorMessage.includes("already started") ||
          errorMessage.includes("already completed")
        ) {
          console.log(
            "Discussion already started/completed, starting streaming updates"
          );
          setDiscussionRunning(true);
          setProgressMessage("議論を実行中です...");
          startListeningForUpdates();
          return;
        }
      }

      if (isComponentMountedRef.current) {
        setError(
          "議論の開始に失敗しました: " + (error.message || "不明なエラー")
        );
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
            console.log("Updating messages:", data.messages.length, "messages"); // デバッグログを追加
            console.log("Current messages count:", messages.length); // デバッグログを追加

            // 新しいメッセージが既存のメッセージより多い場合のみ更新
            if (data.messages.length > messages.length) {
              console.log("New messages detected, updating..."); // デバッグログを追加
              setMessages(data.messages);
            } else if (data.messages.length > 0 && messages.length === 0) {
              // 初回のメッセージの場合
              console.log("Initial messages received, setting..."); // デバッグログを追加
              setMessages(data.messages);
            }
          }

          if (data.completed) {
            console.log(
              "Discussion completed, setting discussionRunning to false"
            ); // デバッグログを追加
            console.log("Final progress:", data.progress); // デバッグログを追加
            console.log("Final message:", data.message); // デバッグログを追加
            setDiscussionRunning(false);

            if (data.error) {
              console.error("Discussion completed with error:", data.error); // デバッグログを追加
              setError(data.error);
            } else {
              console.log("Discussion completed successfully"); // デバッグログを追加
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
        return "secondary";
      case "running":
        return "default";
      case "completed":
        return "default";
      case "failed":
        return "destructive";
      default:
        return "secondary";
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
              onClick={() => navigate("/worlds")}
              className="hover:text-foreground transition-colors"
            >
              世界管理
            </button>
          </li>
          <li>/</li>
          <li>
            <button
              onClick={() => navigate(`/discussions/${worldId}`)}
              className="hover:text-foreground transition-colors"
            >
              {world?.name} - 議論管理
            </button>
          </li>
          <li>/</li>
          <li className="text-foreground font-medium">
            議論結果: {discussion?.theme}
          </li>
        </ol>
      </nav>

      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">議論結果</h1>
          <p className="text-muted-foreground">キャラクターたちの議論の結果をリアルタイムで確認できます。</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={refreshDiscussion}
            disabled={discussionRunning}
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            更新
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate(`/discussions/${worldId}`)}
            className="gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            議論一覧に戻る
          </Button>
        </div>
      </div>

      {discussion && (
        <Card className="mb-6">
          <CardHeader>
            <div className="flex justify-between items-start gap-3">
              <div className="flex-1 min-w-0">
                <CardTitle className="text-2xl">{discussion.theme}</CardTitle>
              </div>
              <div className="flex-shrink-0">
                <Badge variant={getStatusColor(discussion.status)} className="whitespace-nowrap">
                  {getStatusText(discussion.status)}
                </Badge>
              </div>
            </div>
            <CardDescription className="mt-2">
              {discussion.description}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              <span className="font-medium">参加キャラクター:</span> {characters.map((c) => c.name).join(", ")}
            </p>

            {discussion.status === "pending" && (
              <Button
                onClick={startDiscussion}
                disabled={loading}
                className="gap-2"
              >
                <Play className="h-4 w-4" />
                {loading ? "議論開始中..." : "議論を開始"}
              </Button>
            )}

            {discussion.status === "failed" && (
              <Button
                onClick={startDiscussion}
                disabled={loading}
                className="gap-2"
              >
                <Play className="h-4 w-4" />
                {loading ? "再実行中..." : "再実行"}
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error}
          </AlertDescription>
        </Alert>
      )}

      {discussionRunning && (
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-4">
              <Loader2 className="h-5 w-5 animate-spin" />
              <h3 className="text-lg font-semibold">議論実行中...</h3>
            </div>
            <Progress value={progress} className="mb-3" />
            <p className="text-sm text-muted-foreground">
              {progressMessage}
            </p>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-xl">議論の流れ</CardTitle>
        </CardHeader>
        <CardContent>
          {messages.length === 0 && !discussionRunning && (
            <div className="text-center py-8 text-muted-foreground">
              まだ議論が開始されていません
            </div>
          )}

          <div className="max-h-[600px] overflow-auto space-y-3">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`p-4 rounded-lg border-l-4 ${
                  message.speaker === "システム"
                    ? "border-l-blue-500 bg-blue-50/50"
                    : "border-l-green-500 bg-green-50/50"
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-semibold text-sm">
                    {message.speaker}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(message.timestamp).toLocaleTimeString("ja-JP")}
                  </span>
                </div>
                <p className="text-sm whitespace-pre-wrap leading-relaxed">
                  {message.content}
                </p>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {discussionRunning && messages.length === 0 && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default DiscussionResultsPage;
